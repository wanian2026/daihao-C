#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
假突破策略引擎 - FakeoutStrategy
识别结构极值与失败突破，生成交易信号
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from data_fetcher import DataFetcher, MarketData
from trading_strategy import TradingSignal, SignalType


class PatternType(Enum):
    """形态类型"""
    HIGHER_HIGH = "HIGHER_HIGH"      # 更高的高点
    LOWER_HIGH = "LOWER_HIGH"        # 更低的高点
    HIGHER_LOW = "HIGHER_LOW"        # 更高的低点
    LOWER_LOW = "LOWER_LOW"          # 更低的低点
    SWING_HIGH = "SWING_HIGH"        # 摆动高点
    SWING_LOW = "SWING_LOW"          # 摆动低点


@dataclass
class StructureLevel:
    """结构位"""
    level: float
    type: PatternType
    timestamp: int
    confirmed: bool = False
    tested_count: int = 0


@dataclass
class FakeoutSignal:
    """假突破信号"""
    signal_type: SignalType
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float
    pattern_type: PatternType
    reason: str
    structure_level: float


class FakeoutStrategy:
    """假突破策略"""
    
    def __init__(self, 
                 data_fetcher: DataFetcher,
                 symbol: str = "ETHUSDT",
                 interval: str = "5m"):
        """
        初始化策略
        
        Args:
            data_fetcher: 数据获取器
            symbol: 交易对
            interval: K线周期
        """
        self.data_fetcher = data_fetcher
        self.symbol = symbol
        self.interval = interval
        
        # 参数配置
        self.swing_period = 3  # 摆动点检测周期
        self.breakout_confirmation = 2  # 突破确认K线数
        self.fakeout_confirmation = 1  # 假突破确认K线数
        self.min_body_ratio = 0.3  # K线实体占比（用于确认假突破）
        
        # 历史数据
        self.structure_levels: List[StructureLevel] = []
        self.max_structure_levels = 20
    
    def analyze(self) -> List[FakeoutSignal]:
        """
        分析市场，生成信号
        
        Returns:
            假突破信号列表
        """
        signals = []
        
        # 获取K线数据
        klines = self.data_fetcher.get_klines(self.symbol, self.interval, limit=100)
        if len(klines) < 20:
            return signals
        
        # 识别结构位
        self._identify_structure_levels(klines)
        
        # 检测突破和假突破
        signals = self._detect_fakeout(klines)
        
        return signals
    
    def _identify_structure_levels(self, klines: List[MarketData]):
        """
        识别结构位（摆动高低点）
        
        Args:
            klines: K线数据
        """
        new_levels = []
        
        for i in range(self.swing_period, len(klines) - self.swing_period):
            current = klines[i]
            
            # 检测摆动高点
            is_swing_high = True
            for j in range(i - self.swing_period, i + self.swing_period + 1):
                if j != i and klines[j].high >= current.high:
                    is_swing_high = False
                    break
            
            if is_swing_high:
                new_levels.append(StructureLevel(
                    level=current.high,
                    type=PatternType.SWING_HIGH,
                    timestamp=current.open_time,
                    confirmed=True
                ))
            
            # 检测摆动低点
            is_swing_low = True
            for j in range(i - self.swing_period, i + self.swing_period + 1):
                if j != i and klines[j].low <= current.low:
                    is_swing_low = False
                    break
            
            if is_swing_low:
                new_levels.append(StructureLevel(
                    level=current.low,
                    type=PatternType.SWING_LOW,
                    timestamp=current.open_time,
                    confirmed=True
                ))
        
        # 更新结构位列表（保留最近的N个）
        self.structure_levels = new_levels[-self.max_structure_levels:]
    
    def _detect_fakeout(self, klines: List[MarketData]) -> List[FakeoutSignal]:
        """
        检测假突破
        
        Args:
            klines: K线数据
            
        Returns:
            假突破信号列表
        """
        signals = []
        
        if len(klines) < 10:
            return signals
        
        # 检查最近的结构位
        recent_klines = klines[-10:]
        latest_kline = klines[-1]
        
        for structure in self.structure_levels:
            # 只考虑最近的结构位（最近50根K线内）
            if (latest_kline.open_time - structure.timestamp) > 50 * 300000:  # 50 * 5分钟
                continue
            
            # 检测多头假突破（向上突破阻力位后回落）
            if structure.type == PatternType.SWING_HIGH:
                signal = self._check_bullish_fakeout(recent_klines, structure)
                if signal:
                    signals.append(signal)
            
            # 检测空头假突破（向下突破支撑位后回升）
            elif structure.type == PatternType.SWING_LOW:
                signal = self._check_bearish_fakeout(recent_klines, structure)
                if signal:
                    signals.append(signal)
        
        return signals
    
    def _check_bullish_fakeout(self, 
                               klines: List[MarketData], 
                               structure: StructureLevel) -> Optional[FakeoutSignal]:
        """
        检查多头假突破（做多机会）
        
        Args:
            klines: 最近K线
            structure: 结构位
            
        Returns:
            信号或None
        """
        if len(klines) < 3:
            return None
        
        # 检查是否有突破
        breakout_candles = [k for k in klines if k.close > structure.level]
        if len(breakout_candles) == 0:
            return None
        
        # 找到最新的突破K线
        latest_breakout = max(breakout_candles, key=lambda k: k.open_time)
        
        # 检查突破后的K线是否出现回落（假突破）
        # 获取突破后的K线
        breakout_index = klines.index(latest_breakout)
        if breakout_index >= len(klines) - 1:
            return None
        
        post_breakout_candles = klines[breakout_index + 1:]
        
        # 检查是否有K线收盘价跌破结构位
        for candle in post_breakout_candles:
            if candle.close < structure.level:
                # 计算假突破确认度
                breakout_strength = (latest_breakout.high - structure.level) / structure.level
                rejection_strength = (structure.level - candle.low) / structure.level
                
                if breakout_strength > 0.001 and rejection_strength > 0.001:
                    # 生成做多信号
                    return self._create_bullish_signal(
                        latest_breakout,
                        candle,
                        structure
                    )
        
        return None
    
    def _check_bearish_fakeout(self, 
                               klines: List[MarketData], 
                               structure: StructureLevel) -> Optional[FakeoutSignal]:
        """
        检查空头假突破（做空机会）
        
        Args:
            klines: 最近K线
            structure: 结构位
            
        Returns:
            信号或None
        """
        if len(klines) < 3:
            return None
        
        # 检查是否有突破
        breakdown_candles = [k for k in klines if k.close < structure.level]
        if len(breakdown_candles) == 0:
            return None
        
        # 找到最新的突破K线
        latest_breakdown = min(breakdown_candles, key=lambda k: k.open_time)
        
        # 检查突破后的K线是否出现回升（假突破）
        breakdown_index = klines.index(latest_breakdown)
        if breakdown_index >= len(klines) - 1:
            return None
        
        post_breakdown_candles = klines[breakdown_index + 1:]
        
        # 检查是否有K线收盘价涨回结构位
        for candle in post_breakdown_candles:
            if candle.close > structure.level:
                # 计算假突破确认度
                breakdown_strength = (structure.level - latest_breakdown.low) / structure.level
                rejection_strength = (candle.high - structure.level) / structure.level
                
                if breakdown_strength > 0.001 and rejection_strength > 0.001:
                    # 生成做空信号
                    return self._create_bearish_signal(
                        latest_breakdown,
                        candle,
                        structure
                    )
        
        return None
    
    def _create_bullish_signal(self,
                              breakout_candle: MarketData,
                              rejection_candle: MarketData,
                              structure: StructureLevel) -> FakeoutSignal:
        """
        创建做多信号
        
        Args:
            breakout_candle: 突破K线
            rejection_candle: 回落K线
            structure: 结构位
            
        Returns:
            假突破信号
        """
        entry_price = structure.level
        atr = self.data_fetcher.get_atr(self.symbol, self.interval, 14)
        
        # 止损：结构位下方2倍ATR
        stop_loss = structure.level - atr * 2
        
        # 止盈：结构位上方2倍ATR（盈亏比2:1）
        take_profit = structure.level + atr * 4
        
        # 计算置信度
        confidence = self._calculate_confidence(
            breakout_candle,
            rejection_candle,
            structure,
            True
        )
        
        return FakeoutSignal(
            signal_type=SignalType.BUY,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=confidence,
            pattern_type=PatternType.SWING_HIGH,
            reason=f"多头假突破 - 阻力位{structure.level:.2f}被突破后回落",
            structure_level=structure.level
        )
    
    def _create_bearish_signal(self,
                              breakdown_candle: MarketData,
                              rejection_candle: MarketData,
                              structure: StructureLevel) -> FakeoutSignal:
        """
        创建做空信号
        
        Args:
            breakdown_candle: 突破K线
            rejection_candle: 回升K线
            structure: 结构位
            
        Returns:
            假突破信号
        """
        entry_price = structure.level
        atr = self.data_fetcher.get_atr(self.symbol, self.interval, 14)
        
        # 止损：结构位上方2倍ATR
        stop_loss = structure.level + atr * 2
        
        # 止盈：结构位下方2倍ATR（盈亏比2:1）
        take_profit = structure.level - atr * 4
        
        # 计算置信度
        confidence = self._calculate_confidence(
            breakdown_candle,
            rejection_candle,
            structure,
            False
        )
        
        return FakeoutSignal(
            signal_type=SignalType.SELL,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=confidence,
            pattern_type=PatternType.SWING_LOW,
            reason=f"空头假突破 - 支撑位{structure.level:.2f}被突破后回升",
            structure_level=structure.level
        )
    
    def _calculate_confidence(self,
                            first_candle: MarketData,
                            second_candle: MarketData,
                            structure: StructureLevel,
                            is_bullish: bool) -> float:
        """
        计算信号置信度
        
        Args:
            first_candle: 第一根K线
            second_candle: 第二根K线
            structure: 结构位
            is_bullish: 是否看多
            
        Returns:
            置信度（0-1）
        """
        confidence = 0.5  # 基础置信度
        
        # K线实体大小
        if second_candle.body_size > first_candle.body_size * 0.5:
            confidence += 0.1
        
        # 成交量放大（检查最后一根K线的成交量）
        current_volume = self.data_fetcher.get_klines(
            self.symbol, 
            self.interval, 
            limit=1
        )[0].volume
        volume_ma = self.data_fetcher.get_volume_ma(self.symbol, self.interval, 20)
        
        if current_volume > volume_ma * 1.2:
            confidence += 0.15
        
        # 影线长度
        if is_bullish:
            # 多头假突破：下影线较长
            if second_candle.lower_wick > second_candle.body_size:
                confidence += 0.15
        else:
            # 空头假突破：上影线较长
            if second_candle.upper_wick > second_candle.body_size:
                confidence += 0.15
        
        # ATR是否在合理范围
        atr = self.data_fetcher.get_atr(self.symbol, self.interval, 14)
        current_price = self.data_fetcher.get_latest_price(self.symbol)
        atr_ratio = atr / current_price if current_price > 0 else 0
        
        if 0.005 <= atr_ratio <= 0.02:
            confidence += 0.1
        
        return min(0.95, confidence)  # 最大置信度0.95
    
    def analyze_batch(self, symbols: List[str]) -> Dict[str, List[FakeoutSignal]]:
        """
        批量分析多个标的的假突破
        
        Args:
            symbols: 交易对列表
            
        Returns:
            假突破信号字典 {symbol: List[FakeoutSignal]}
        """
        results = {}
        
        for symbol in symbols:
            try:
                # 创建临时策略实例分析单个标的
                temp_strategy = FakeoutStrategy(
                    self.data_fetcher,
                    symbol=symbol,
                    interval=self.interval
                )
                results[symbol] = temp_strategy.analyze()
            except Exception as e:
                print(f"分析 {symbol} 假突破失败: {str(e)}")
                results[symbol] = []
        
        return results
    
    def get_best_signal(self, symbols: List[str]) -> Optional[Tuple[str, FakeoutSignal]]:
        """
        从多个标的中获取最佳信号（置信度最高）
        
        Args:
            symbols: 交易对列表
            
        Returns:
            (symbol, signal) 或 None
        """
        all_signals = self.analyze_batch(symbols)
        
        best_signal = None
        best_symbol = None
        best_confidence = 0.0
        
        for symbol, signals in all_signals.items():
            if signals:
                # 找到该标的的最佳信号
                symbol_best = max(signals, key=lambda s: s.confidence)
                if symbol_best.confidence > best_confidence:
                    best_confidence = symbol_best.confidence
                    best_signal = symbol_best
                    best_symbol = symbol
        
        if best_signal and best_symbol:
            return (best_symbol, best_signal)
        
        return None


# 测试代码
if __name__ == "__main__":
    print("假突破策略测试")
    
    from data_fetcher import DataFetcher
    from binance_api_client import BinanceAPIClient
    
    client = BinanceAPIClient()
    fetcher = DataFetcher(client)
    strategy = FakeoutStrategy(fetcher, symbol="ETHUSDT", interval="5m")
    
    try:
        print("\n分析假突破信号...")
        signals = strategy.analyze()
        
        print(f"\n找到 {len(signals)} 个假突破信号")
        
        for i, signal in enumerate(signals, 1):
            print(f"\n信号 {i}:")
            print(f"  类型: {signal.signal_type.value}")
            print(f"  入场价: {signal.entry_price:.2f}")
            print(f"  止损: {signal.stop_loss:.2f}")
            print(f"  止盈: {signal.take_profit:.2f}")
            print(f"  置信度: {signal.confidence:.2f}")
            print(f"  原因: {signal.reason}")
            print(f"  结构位: {signal.structure_level:.2f}")
        
        if not signals:
            print("\n当前没有假突破信号")
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        print("注意：此测试需要网络连接到币安API")
