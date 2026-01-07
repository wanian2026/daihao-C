#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FVG策略核心模块
识别FVG缺口并生成交易信号
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass

from fvg_signal import (
    FVG, FVGType, SignalType, FVGSignal, SignalSource
)
from data_fetcher import DataFetcher, KLine


@dataclass
class FVGStrategyConfig:
    """FVG策略配置"""
    # FVG识别参数
    min_fvg_size_percent: float = 0.0005   # 最小FVG大小（0.05%）
    max_fvg_age_minutes: int = 60          # 最大FVG年龄（分钟）
    fvg_lookback: int = 100                # FVG回溯K线数

    # 入场参数
    entry_tolerance_percent: float = 0.0002  # 入场容差（0.02%）
    require_partial_fill: bool = True      # 要求部分填充后才入场

    # 风险管理
    min_risk_reward: float = 2.0           # 最小盈亏比
    max_risk_per_trade: float = 0.01       # 单笔最大风险（1%）

    # 止损止盈
    sl_atr_ratio: float = 1.5             # 止损 = ATR × 1.5
    tp_rr_ratio: float = 2.5               # 止盈 = 风险 × 2.5


class FVGStrategy:
    """FVG策略"""

    def __init__(self, data_fetcher: DataFetcher, symbol: str, config: Optional[FVGStrategyConfig] = None):
        """
        初始化FVG策略

        Args:
            data_fetcher: 数据获取器
            symbol: 交易对
            config: 策略配置
        """
        self.data_fetcher = data_fetcher
        self.symbol = symbol
        self.config = config or FVGStrategyConfig()

        # 缓存
        self._klines_cache: Optional[List[KLine]] = None
        self._atr_cache: Optional[float] = None

    def identify_fvgs(self, timeframe: str = "5m") -> List[FVG]:
        """
        识别FVG缺口

        Args:
            timeframe: K线周期

        Returns:
            FVG列表
        """
        # 获取K线数据
        klines = self.data_fetcher.get_klines(self.symbol, timeframe, self.config.fvg_lookback)

        if not klines or len(klines) < 3:
            return []

        fvgs = []

        # 遍历K线，识别FVG
        for i in range(1, len(klines) - 1):
            prev_kline = klines[i - 1]
            curr_kline = klines[i]
            next_kline = klines[i + 1]

            # 识别看涨FVG
            # 条件：第2根K线的高点 > 第1根K线的低点
            if next_kline.high > prev_kline.low:
                gap_high = next_kline.high
                gap_low = prev_kline.low
                gap_size = gap_high - gap_low

                # 计算缺口大小百分比
                avg_price = (gap_high + gap_low) / 2
                gap_size_percent = gap_size / avg_price

                # 检查最小大小
                if gap_size_percent >= self.config.min_fvg_size_percent:
                    fvg = FVG(
                        gap_type=FVGType.BULLISH,
                        high_bound=gap_high,
                        low_bound=gap_low,
                        size=gap_size,
                        size_percent=gap_size_percent,
                        formation_time=curr_kline.close_time,
                        kline_index=i
                    )
                    fvgs.append(fvg)

            # 识别看跌FVG
            # 条件：第2根K线的低点 < 第1根K线的高点
            if next_kline.low < prev_kline.high:
                gap_high = prev_kline.high
                gap_low = next_kline.low
                gap_size = gap_high - gap_low

                # 计算缺口大小百分比
                avg_price = (gap_high + gap_low) / 2
                gap_size_percent = gap_size / avg_price

                # 检查最小大小
                if gap_size_percent >= self.config.min_fvg_size_percent:
                    fvg = FVG(
                        gap_type=FVGType.BEARISH,
                        high_bound=gap_high,
                        low_bound=gap_low,
                        size=gap_size,
                        size_percent=gap_size_percent,
                        formation_time=curr_kline.close_time,
                        kline_index=i
                    )
                    fvgs.append(fvg)

        # 更新填充状态
        current_price = klines[-1].close
        for fvg in fvgs:
            self._check_fvg_fill(fvg, current_price, klines[fvg.kline_index:])

        # 过滤已填充的FVG
        fvgs = [fvg for fvg in fvgs if not fvg.is_filled]

        # 按时间倒序排列（最新的在前）
        fvgs.sort(key=lambda x: x.formation_time, reverse=True)

        return fvgs

    def _check_fvg_fill(self, fvg: FVG, current_price: float, klines_after: List[KLine]):
        """
        检查FVG是否被填充

        Args:
            fvg: FVG对象
            current_price: 当前价格
            klines_after: FVG形成后的K线
        """
        # 检查当前价格
        if fvg.gap_type == FVGType.BULLISH:
            # 看涨FVG：价格跌到缺口下方则填充
            if current_price <= fvg.low_bound:
                fvg.is_filled = True
                fvg.fill_time = klines_after[-1].close_time if klines_after else fvg.formation_time
        else:  # BEARISH
            # 看跌FVG：价格涨到缺口上方则填充
            if current_price >= fvg.high_bound:
                fvg.is_filled = True
                fvg.fill_time = klines_after[-1].close_time if klines_after else fvg.formation_time

        # 检查历史K线
        for kline in klines_after:
            if fvg.gap_type == FVGType.BULLISH:
                if kline.low <= fvg.low_bound:
                    fvg.is_filled = True
                    fvg.fill_time = kline.close_time
                    break
            else:  # BEARISH
                if kline.high >= fvg.high_bound:
                    fvg.is_filled = True
                    fvg.fill_time = kline.close_time
                    break

    def validate_fvg(self, fvg: FVG, current_price: float) -> bool:
        """
        验证FVG有效性

        Args:
            fvg: FVG对象
            current_price: 当前价格

        Returns:
            是否有效
        """
        # 检查是否已填充
        if fvg.is_filled:
            return False

        # 检查年龄
        if not fvg.is_active(int(current_price * 1000), self.config.max_fvg_age_minutes):
            return False

        # 检查大小
        if fvg.size_percent < self.config.min_fvg_size_percent:
            return False

        return True

    def generate_fvg_signals(self, timeframe: str = "5m") -> List[FVGSignal]:
        """
        生成FVG交易信号

        Args:
            timeframe: K线周期

        Returns:
            FVG信号列表
        """
        # 获取当前价格
        current_price = self.data_fetcher.get_latest_price(self.symbol)
        if current_price == 0:
            return []

        # 获取ATR
        atr = self.data_fetcher.get_atr(self.symbol, timeframe, 14)
        if atr == 0:
            return []

        # 识别FVG
        fvgs = self.identify_fvgs(timeframe)

        signals = []

        # 为每个FVG生成信号
        for fvg in fvgs:
            # 验证FVG
            if not self.validate_fvg(fvg, current_price):
                continue

            # 生成信号
            if fvg.gap_type == FVGType.BULLISH:
                # 看涨FVG：做多信号
                signal = self._generate_bullish_fvg_signal(fvg, current_price, atr)
            else:
                # 看跌FVG：做空信号
                signal = self._generate_bearish_fvg_signal(fvg, current_price, atr)

            if signal:
                signals.append(signal)

        # 按置信度排序
        signals.sort(key=lambda x: x.confidence, reverse=True)

        return signals

    def _generate_bullish_fvg_signal(self, fvg: FVG, current_price: float, atr: float) -> Optional[FVGSignal]:
        """
        生成看涨FVG信号

        Args:
            fvg: 看涨FVG
            current_price: 当前价格
            atr: ATR值

        Returns:
            FVG信号
        """
        # 入场价格：FVG底部（加上容差）
        entry_price = fvg.low_bound * (1 + self.config.entry_tolerance_percent)

        # 止损价格：FVG底部下方
        stop_loss = fvg.low_bound - (atr * self.config.sl_atr_ratio)

        # 止盈价格：根据盈亏比计算
        risk = entry_price - stop_loss
        take_profit = entry_price + (risk * self.config.tp_rr_ratio)

        # 计算盈亏比
        risk_reward_ratio = (take_profit - entry_price) / risk if risk > 0 else 0

        # 检查最小盈亏比
        if risk_reward_ratio < self.config.min_risk_reward:
            return None

        # 计算置信度
        confidence = self._calculate_fvg_confidence(fvg, current_price, atr, risk_reward_ratio)

        # 生成信号
        signal = FVGSignal(
            signal_type=SignalType.BUY,
            signal_source=SignalSource.FVG,
            symbol=self.symbol,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=confidence,
            timeframe=self.data_fetcher.interval,
            fvg=fvg,
            reason=f"看涨FVG回补 - 缺口大小: {fvg.size_percent:.3f}%",
            timestamp=fvg.formation_time,
            primary_timeframe=self.data_fetcher.interval
        )

        return signal

    def _generate_bearish_fvg_signal(self, fvg: FVG, current_price: float, atr: float) -> Optional[FVGSignal]:
        """
        生成看跌FVG信号

        Args:
            fvg: 看跌FVG
            current_price: 当前价格
            atr: ATR值

        Returns:
            FVG信号
        """
        # 入场价格：FVG顶部（减去容差）
        entry_price = fvg.high_bound * (1 - self.config.entry_tolerance_percent)

        # 止损价格：FVG顶上方
        stop_loss = fvg.high_bound + (atr * self.config.sl_atr_ratio)

        # 止盈价格：根据盈亏比计算
        risk = stop_loss - entry_price
        take_profit = entry_price - (risk * self.config.tp_rr_ratio)

        # 计算盈亏比
        risk_reward_ratio = (entry_price - take_profit) / risk if risk > 0 else 0

        # 检查最小盈亏比
        if risk_reward_ratio < self.config.min_risk_reward:
            return None

        # 计算置信度
        confidence = self._calculate_fvg_confidence(fvg, current_price, atr, risk_reward_ratio)

        # 生成信号
        signal = FVGSignal(
            signal_type=SignalType.SELL,
            signal_source=SignalSource.FVG,
            symbol=self.symbol,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=confidence,
            timeframe=self.data_fetcher.interval,
            fvg=fvg,
            reason=f"看跌FVG回补 - 缺口大小: {fvg.size_percent:.3f}%",
            timestamp=fvg.formation_time,
            primary_timeframe=self.data_fetcher.interval
        )

        return signal

    def _calculate_fvg_confidence(self, fvg: FVG, current_price: float, atr: float, rr_ratio: float) -> float:
        """
        计算FVG信号置信度

        Args:
            fvg: FVG对象
            current_price: 当前价格
            atr: ATR值
            rr_ratio: 盈亏比

        Returns:
            置信度（0-1）
        """
        score = 0.0

        # 1. FVG大小评分（30分）
        # 缺口越大，评分越高
        if fvg.size_percent >= 0.002:  # >= 0.2%
            score += 30
        elif fvg.size_percent >= 0.001:  # >= 0.1%
            score += 20
        elif fvg.size_percent >= 0.0005:  # >= 0.05%
            score += 10

        # 2. FVG新鲜度评分（25分）
        # 越新的FVG，评分越高
        current_time = int(current_price * 1000)  # 近似
        age_minutes = (current_time - fvg.formation_time) / 1000 / 60

        if age_minutes < 10:
            score += 25
        elif age_minutes < 30:
            score += 20
        elif age_minutes < 60:
            score += 15
        elif age_minutes < 120:
            score += 10

        # 3. 价格位置评分（25分）
        # 价格越接近FVG，评分越高
        distance_percent = abs(current_price - fvg.midpoint) / fvg.midpoint

        if distance_percent < 0.0005:  # < 0.05%
            score += 25
        elif distance_percent < 0.001:  # < 0.1%
            score += 20
        elif distance_percent < 0.002:  # < 0.2%
            score += 15
        elif distance_percent < 0.005:  # < 0.5%
            score += 10

        # 4. 盈亏比评分（20分）
        if rr_ratio >= 2.5:
            score += 20
        elif rr_ratio >= 2.0:
            score += 15
        elif rr_ratio >= 1.5:
            score += 10

        # 转换为0-1的置信度
        confidence = score / 100.0

        return min(confidence, 1.0)


# 测试代码
if __name__ == "__main__":
    from binance_api_client import BinanceAPIClient

    print("测试FVG策略...")

    try:
        # 初始化
        client = BinanceAPIClient()
        fetcher = DataFetcher(client)
        fetcher.interval = "5m"

        symbol = "ETHUSDT"
        strategy = FVGStrategy(fetcher, symbol)

        # 识别FVG
        print(f"\n识别 {symbol} 的FVG...")
        fvgs = strategy.identify_fvgs("5m")

        print(f"发现 {len(fvgs)} 个FVG：")
        for i, fvg in enumerate(fvgs[:10]):  # 只显示前10个
            print(f"  {i+1}. {fvg}")

        # 生成信号
        print(f"\n生成FVG信号...")
        signals = strategy.generate_fvg_signals("5m")

        print(f"发现 {len(signals)} 个信号：")
        for i, signal in enumerate(signals[:5]):  # 只显示前5个
            print(f"  {i+1}. {signal}")

    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
