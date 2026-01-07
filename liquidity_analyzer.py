#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流动性分析模块
识别买卖方流动性区域和流动性捕取
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass

from fvg_signal import (
    LiquidityType, SignalType, FVGSignal, SignalSource,
    LiquidityZone, SwingPoint
)
from data_fetcher import DataFetcher, KLine


@dataclass
class LiquidityAnalysisConfig:
    """流动性分析配置"""
    # 摆动点识别
    swing_lookback: int = 20               # 摆动点回溯K线数
    swing_threshold: float = 0.001        # 摆动点阈值（0.1%）

    # 流动性识别
    liquidity_threshold: float = 0.001     # 流动性强度阈值（0.1%）
    min_swings_between: int = 3           # 流动性区间之间的最小摆动点数

    # 流动性捕取
    sweep_threshold_percent: float = 0.0003   # 捕取阈值（0.03%）
    sweep_retreat_percent: float = 0.0005    # 捕取后的回落阈值（0.05%）
    max_sweep_age: int = 10                    # 最大捕取年龄（K线数）

    # 流动性目标
    liquidity_target_atr_ratio: float = 2.0   # 流动性目标 = ATR × 2.0


class LiquidityAnalyzer:
    """流动性分析器"""

    def __init__(self, data_fetcher: DataFetcher, symbol: str, config: Optional[LiquidityAnalysisConfig] = None):
        """
        初始化流动性分析器

        Args:
            data_fetcher: 数据获取器
            symbol: 交易对
            config: 分析配置
        """
        self.data_fetcher = data_fetcher
        self.symbol = symbol
        self.config = config or LiquidityAnalysisConfig()

        # 缓存
        self._swing_points_cache: Optional[List[SwingPoint]] = None

    def identify_swing_points(self, timeframe: str = "5m") -> Tuple[List[SwingPoint], List[SwingPoint]]:
        """
        识别摆动高点和摆动低点

        Args:
            timeframe: K线周期

        Returns:
            (摆动高点列表, 摆动低点列表)
        """
        # 获取K线数据
        klines = self.data_fetcher.get_klines(self.symbol, timeframe, self.config.swing_lookback)

        if not klines or len(klines) < 5:
            return [], []

        swing_highs = []
        swing_lows = []

        # 简单摆动点识别
        for i in range(2, len(klines) - 2):
            current = klines[i]
            prev2 = klines[i - 2]
            prev1 = klines[i - 1]
            next1 = klines[i + 1]
            next2 = klines[i + 2]

            # 摆动高点
            if (current.high > prev1.high and current.high > prev2.high and
                current.high > next1.high and current.high > next2.high):
                swing_high = SwingPoint(
                    point_type="HIGH",
                    price=current.high,
                    time=current.close_time,
                    index=i
                )
                swing_highs.append(swing_high)

            # 摆动低点
            if (current.low < prev1.low and current.low < prev2.low and
                current.low < next1.low and current.low < next2.low):
                swing_low = SwingPoint(
                    point_type="LOW",
                    price=current.low,
                    time=current.close_time,
                    index=i
                )
                swing_lows.append(swing_low)

        # 缓存摆动点
        self._swing_points_cache = swing_highs + swing_lows

        return swing_highs, swing_lows

    def identify_buyside_liquidity(self, timeframe: str = "5m") -> List[LiquidityZone]:
        """
        识别买方流动性区（下方的流动性聚集）

        Args:
            timeframe: K线周期

        Returns:
            买方流动性区列表
        """
        # 获取摆动低点
        swing_lows = self.identify_swing_points(timeframe)[1]

        if not swing_lows:
            return []

        liquidity_zones = []

        # 获取当前价格
        current_price = self.data_fetcher.get_latest_price(self.symbol)

        # 遍历摆动低点，识别流动性区
        for i, swing_low in enumerate(swing_lows):
            # 跳过最近的一个摆动低点（可能是当前的）
            if i >= len(swing_lows) - 2:
                continue

            # 检查摆动低点是否在当前价格下方
            if swing_low.price >= current_price:
                continue

            # 计算流动性强度
            # 越接近的摆动点，强度越高
            distance = current_price - swing_low.price
            strength = 1.0 - min(1.0, distance / (current_price * 0.01))  # 1%范围

            if strength < self.config.liquidity_threshold:
                continue

            # 检查是否已有相似的流动性区
            is_duplicate = False
            for zone in liquidity_zones:
                if abs(zone.level - swing_low.price) < (current_price * 0.001):  # 0.1%范围内
                    # 合并流动性区
                    zone.strength = max(zone.strength, strength)
                    zone.touched_count += 1
                    is_duplicate = True
                    break

            if not is_duplicate:
                zone = LiquidityZone(
                    zone_type=LiquidityType.BUYSIDE,
                    level=swing_low.price,
                    strength=strength,
                    formation_time=swing_low.time
                )
                liquidity_zones.append(zone)

        # 按强度排序
        liquidity_zones.sort(key=lambda x: x.strength, reverse=True)

        return liquidity_zones

    def identify_sellside_liquidity(self, timeframe: str = "5m") -> List[LiquidityZone]:
        """
        识别卖方流动性区（上方的流动性聚集）

        Args:
            timeframe: K线周期

        Returns:
            卖方流动性区列表
        """
        # 获取摆动高点
        swing_highs = self.identify_swing_points(timeframe)[0]

        if not swing_highs:
            return []

        liquidity_zones = []

        # 获取当前价格
        current_price = self.data_fetcher.get_latest_price(self.symbol)

        # 遍历摆动高点，识别流动性区
        for i, swing_high in enumerate(swing_highs):
            # 跳过最近的一个摆动高点（可能是当前的）
            if i >= len(swing_highs) - 2:
                continue

            # 检查摆动高点是否在当前价格上方
            if swing_high.price <= current_price:
                continue

            # 计算流动性强度
            # 越接近的摆动点，强度越高
            distance = swing_high.price - current_price
            strength = 1.0 - min(1.0, distance / (current_price * 0.01))  # 1%范围

            if strength < self.config.liquidity_threshold:
                continue

            # 检查是否已有相似的流动性区
            is_duplicate = False
            for zone in liquidity_zones:
                if abs(zone.level - swing_high.price) < (current_price * 0.001):  # 0.1%范围内
                    # 合并流动性区
                    zone.strength = max(zone.strength, strength)
                    zone.touched_count += 1
                    is_duplicate = True
                    break

            if not is_duplicate:
                zone = LiquidityZone(
                    zone_type=LiquidityType.SELLSIDE,
                    level=swing_high.price,
                    strength=strength,
                    formation_time=swing_high.time
                )
                liquidity_zones.append(zone)

        # 按强度排序
        liquidity_zones.sort(key=lambda x: x.strength, reverse=True)

        return liquidity_zones

    def detect_liquidity_sweep(
        self,
        liquidity_zone: LiquidityZone,
        timeframe: str = "5m"
    ) -> Tuple[bool, Optional[KLine]]:
        """
        检测流动性捕取

        Args:
            liquidity_zone: 流动性区
            timeframe: K线周期

        Returns:
            (是否捕取, 捕取K线)
        """
        # 获取K线数据
        klines = self.data_fetcher.get_klines(self.symbol, timeframe, self.config.max_sweep_age)

        if not klines:
            return False, None

        # 检查最近的K线
        recent_klines = klines[-self.config.max_sweep_age:]

        for kline in reversed(recent_klines):
            if liquidity_zone.zone_type == LiquidityType.BUYSIDE:
                # 检查是否跌破买方流动性区
                if kline.low <= liquidity_zone.level * (1 - self.config.sweep_threshold_percent):
                    # 检查是否快速反弹
                    if kline.close > kline.low * (1 + self.config.sweep_retreat_percent):
                        liquidity_zone.is_swept = True
                        liquidity_zone.sweep_time = kline.close_time
                        return True, kline
            else:  # SELLSIDE
                # 检查是否涨破卖方流动性区
                if kline.high >= liquidity_zone.level * (1 + self.config.sweep_threshold_percent):
                    # 检查是否快速回落
                    if kline.close < kline.high * (1 - self.config.sweep_retreat_percent):
                        liquidity_zone.is_swept = True
                        liquidity_zone.sweep_time = kline.close_time
                        return True, kline

        return False, None

    def calculate_liquidity_target(
        self,
        liquidity_zone: LiquidityZone,
        timeframe: str = "5m"
    ) -> Optional[float]:
        """
        计算流动性目标位

        Args:
            liquidity_zone: 流动性区
            timeframe: K线周期

        Returns:
            目标价格
        """
        # 获取ATR
        atr = self.data_fetcher.get_atr(self.symbol, timeframe, 14)
        if atr == 0:
            return None

        # 计算目标位
        target_distance = atr * self.config.liquidity_target_atr_ratio

        if liquidity_zone.zone_type == LiquidityType.BUYSIDE:
            # 买方流动性被扫后，目标向上
            return liquidity_zone.level + target_distance
        else:  # SELLSIDE
            # 卖方流动性被扫后，目标向下
            return liquidity_zone.level - target_distance

    def generate_liquidity_sweep_signals(self, timeframe: str = "5m") -> List[FVGSignal]:
        """
        生成流动性捕取信号

        Args:
            timeframe: K线周期

        Returns:
            FVG信号列表
        """
        signals = []

        # 获取当前价格
        current_price = self.data_fetcher.get_latest_price(self.symbol)
        if current_price == 0:
            return []

        # 获取ATR
        atr = self.data_fetcher.get_atr(self.symbol, timeframe, 14)
        if atr == 0:
            return []

        # 识别买方流动性区
        buyside_zones = self.identify_buyside_liquidity(timeframe)

        # 识别卖方流动性区
        sellside_zones = self.identify_sellside_liquidity(timeframe)

        # 检测买方流动性捕取
        for zone in buyside_zones:
            swept, kline = self.detect_liquidity_sweep(zone, timeframe)
            if swept and kline:
                signal = self._generate_buyside_sweep_signal(zone, kline, atr, current_price)
                if signal:
                    signals.append(signal)

        # 检测卖方流动性捕取
        for zone in sellside_zones:
            swept, kline = self.detect_liquidity_sweep(zone, timeframe)
            if swept and kline:
                signal = self._generate_sellside_sweep_signal(zone, kline, atr, current_price)
                if signal:
                    signals.append(signal)

        # 按置信度排序
        signals.sort(key=lambda x: x.confidence, reverse=True)

        return signals

    def _generate_buyside_sweep_signal(
        self,
        liquidity_zone: LiquidityZone,
        sweep_kline: KLine,
        atr: float,
        current_price: float
    ) -> Optional[FVGSignal]:
        """
        生成买方流动性捕取信号（做多）

        Args:
            liquidity_zone: 流动性区
            sweep_kline: 捕取K线
            atr: ATR值
            current_price: 当前价格

        Returns:
            FVG信号
        """
        # 入场价格：捕取后的收盘价
        entry_price = sweep_kline.close

        # 止损价格：新低点下方
        stop_loss = liquidity_zone.level - (atr * 1.5)

        # 止盈价格：流动性目标
        take_profit = self.calculate_liquidity_target(liquidity_zone)
        if take_profit is None:
            return None

        # 计算盈亏比
        risk = entry_price - stop_loss
        reward = take_profit - entry_price
        risk_reward_ratio = reward / risk if risk > 0 else 0

        # 计算置信度
        confidence = liquidity_zone.strength * 0.7  # 基础置信度
        if risk_reward_ratio >= 2.0:
            confidence += 0.2
        elif risk_reward_ratio >= 1.5:
            confidence += 0.1

        confidence = min(confidence, 1.0)

        # 生成信号
        signal = FVGSignal(
            signal_type=SignalType.BUY,
            signal_source=SignalSource.LIQUIDITY_SWEEP,
            symbol=self.symbol,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=confidence,
            timeframe=self.data_fetcher.interval,
            liquidity_zone=liquidity_zone,
            reason=f"买方流动性捕取 - 强度: {liquidity_zone.strength:.2f}",
            timestamp=sweep_kline.close_time,
            primary_timeframe=self.data_fetcher.interval
        )

        return signal

    def _generate_sellside_sweep_signal(
        self,
        liquidity_zone: LiquidityZone,
        sweep_kline: KLine,
        atr: float,
        current_price: float
    ) -> Optional[FVGSignal]:
        """
        生成卖方流动性捕取信号（做空）

        Args:
            liquidity_zone: 流动性区
            sweep_kline: 捕取K线
            atr: ATR值
            current_price: 当前价格

        Returns:
            FVG信号
        """
        # 入场价格：捕取后的收盘价
        entry_price = sweep_kline.close

        # 止损价格：新高点上方
        stop_loss = liquidity_zone.level + (atr * 1.5)

        # 止盈价格：流动性目标
        take_profit = self.calculate_liquidity_target(liquidity_zone)
        if take_profit is None:
            return None

        # 计算盈亏比
        risk = stop_loss - entry_price
        reward = entry_price - take_profit
        risk_reward_ratio = reward / risk if risk > 0 else 0

        # 计算置信度
        confidence = liquidity_zone.strength * 0.7  # 基础置信度
        if risk_reward_ratio >= 2.0:
            confidence += 0.2
        elif risk_reward_ratio >= 1.5:
            confidence += 0.1

        confidence = min(confidence, 1.0)

        # 生成信号
        signal = FVGSignal(
            signal_type=SignalType.SELL,
            signal_source=SignalSource.LIQUIDITY_SWEEP,
            symbol=self.symbol,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=confidence,
            timeframe=self.data_fetcher.interval,
            liquidity_zone=liquidity_zone,
            reason=f"卖方流动性捕取 - 强度: {liquidity_zone.strength:.2f}",
            timestamp=sweep_kline.close_time,
            primary_timeframe=self.data_fetcher.interval
        )

        return signal


# 测试代码
if __name__ == "__main__":
    from binance_api_client import BinanceAPIClient

    print("测试流动性分析...")

    try:
        # 初始化
        client = BinanceAPIClient()
        fetcher = DataFetcher(client)
        fetcher.interval = "5m"

        symbol = "ETHUSDT"
        analyzer = LiquidityAnalyzer(fetcher, symbol)

        # 识别摆动点
        print(f"\n识别 {symbol} 的摆动点...")
        swing_highs, swing_lows = analyzer.identify_swing_points("5m")

        print(f"摆动高点: {len(swing_highs)} 个")
        for i, swing in enumerate(swing_highs[:5]):
            print(f"  {i+1}. {swing}")

        print(f"\n摆动低点: {len(swing_lows)} 个")
        for i, swing in enumerate(swing_lows[:5]):
            print(f"  {i+1}. {swing}")

        # 识别流动性区
        print(f"\n识别买方流动性区...")
        buyside_zones = analyzer.identify_buyside_liquidity("5m")
        print(f"发现 {len(buyside_zones)} 个买方流动性区")
        for i, zone in enumerate(buyside_zones[:3]):
            print(f"  {i+1}. {zone}")

        print(f"\n识别卖方流动性区...")
        sellside_zones = analyzer.identify_sellside_liquidity("5m")
        print(f"发现 {len(sellside_zones)} 个卖方流动性区")
        for i, zone in enumerate(sellside_zones[:3]):
            print(f"  {i+1}. {zone}")

        # 生成流动性捕取信号
        print(f"\n生成流动性捕取信号...")
        signals = analyzer.generate_liquidity_sweep_signals("5m")
        print(f"发现 {len(signals)} 个信号")
        for i, signal in enumerate(signals[:3]):
            print(f"  {i+1}. {signal}")

    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
