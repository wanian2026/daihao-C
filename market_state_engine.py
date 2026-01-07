#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场状态引擎 - MarketStateEngine
根据ATR、成交量、Funding将市场划分为 SLEEP / ACTIVE / AGGRESSIVE
"""

from enum import Enum
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime
from data_fetcher import DataFetcher


class MarketState(Enum):
    """市场状态枚举"""
    SLEEP = "SLEEP"         # 休眠：市场平静，不适合交易
    ACTIVE = "ACTIVE"       # 活跃：市场有波动，适合正常交易
    AGGRESSIVE = "AGGRESSIVE"  # 激进：市场剧烈波动，适合激进策略


@dataclass
class MarketStateInfo:
    """市场状态信息"""
    state: MarketState
    atr: float
    atr_ratio: float  # ATR相对于平均值的比率
    volume_ratio: float  # 成交量相对于平均值的比率
    funding_rate: Optional[float]
    score: float  # 综合评分（0-100）
    timestamp: datetime
    reasons: list  # 状态原因列表


class MarketStateEngine:
    """市场状态引擎"""
    
    def __init__(self, 
                 data_fetcher: DataFetcher,
                 symbol: str = "ETHUSDT",
                 interval: str = "5m",
                 enable_sleep_filter: bool = True):
        """
        初始化市场状态引擎
        
        Args:
            data_fetcher: 数据获取器
            symbol: 交易对
            interval: K线周期
            enable_sleep_filter: 是否启用市场休眠过滤（默认启用）
        """
        self.data_fetcher = data_fetcher
        self.symbol = symbol
        self.interval = interval
        self.enable_sleep_filter = enable_sleep_filter
        
        # 参数配置
        self.atr_period = 14
        self.volume_ma_period = 20
        self.atr_sleep_threshold = 0.005  # ATR < 0.5% = SLEEP
        self.atr_active_threshold = 0.02   # ATR > 2% = AGGRESSIVE
        self.volume_active_multiplier = 1.5  # 成交量 > 平均1.5倍
        self.funding_sleep_threshold = -0.0001  # 负费率
        self.funding_aggressive_threshold = 0.0001  # 正费率
        
        # 历史数据（用于计算平均值）
        self.atr_history = []
        self.max_history_length = 100
    
    def analyze(self) -> MarketStateInfo:
        """
        分析市场状态
        
        Returns:
            市场状态信息
        """
        # 获取数据
        atr = self.data_fetcher.get_atr(self.symbol, self.interval, self.atr_period)
        volume_ma = self.data_fetcher.get_volume_ma(self.symbol, self.interval, self.volume_ma_period)
        latest_volume = self.data_fetcher.get_klines(self.symbol, self.interval, limit=1)[0].volume
        funding_rate = self.data_fetcher.get_funding_rate(self.symbol)
        current_price = self.data_fetcher.get_latest_price(self.symbol)
        
        # 计算比率
        atr_ratio = atr / current_price if current_price > 0 else 0
        volume_ratio = latest_volume / volume_ma if volume_ma > 0 else 1.0
        
        # 更新ATR历史
        self.atr_history.append(atr)
        if len(self.atr_history) > self.max_history_length:
            self.atr_history.pop(0)
        
        # 计算ATR平均值
        atr_avg = sum(self.atr_history) / len(self.atr_history) if self.atr_history else atr
        atr_avg_ratio = atr / atr_avg if atr_avg > 0 else 1.0
        
        # 判断状态
        state, reasons = self._determine_state(
            atr_ratio, 
            volume_ratio, 
            funding_rate, 
            atr_avg_ratio
        )
        
        # 计算综合评分（0-100）
        score = self._calculate_score(
            state, 
            atr_ratio, 
            volume_ratio, 
            funding_rate
        )
        
        return MarketStateInfo(
            state=state,
            atr=atr,
            atr_ratio=atr_avg_ratio,
            volume_ratio=volume_ratio,
            funding_rate=funding_rate,
            score=score,
            timestamp=datetime.now(),
            reasons=reasons
        )
    
    def _determine_state(self, 
                        atr_ratio: float, 
                        volume_ratio: float, 
                        funding_rate: Optional[float],
                        atr_avg_ratio: float) -> tuple[MarketState, list]:
        """
        确定市场状态
        
        Args:
            atr_ratio: ATR比率
            volume_ratio: 成交量比率
            funding_rate: 资金费率
            atr_avg_ratio: ATR平均值比率
            
        Returns:
            (市场状态, 原因列表)
        """
        reasons = []
        
        # 判断是否为SLEEP状态（仅在启用休眠过滤时）
        is_sleep = False
        if self.enable_sleep_filter:
            is_sleep = (
                atr_ratio < self.atr_sleep_threshold or
                atr_avg_ratio < 0.8 or
                (funding_rate is not None and funding_rate < self.funding_sleep_threshold)
            )
        
        if is_sleep:
            reasons.append("ATR过低")
            if volume_ratio < 1.0:
                reasons.append("成交量低迷")
            if funding_rate and funding_rate < self.funding_sleep_threshold:
                reasons.append("负资金费率")
            return MarketState.SLEEP, reasons
        
        # 判断是否为AGGRESSIVE状态
        is_aggressive = (
            atr_ratio > self.atr_active_threshold or
            atr_avg_ratio > 2.0 or
            volume_ratio > self.volume_active_multiplier * 2 or
            (funding_rate is not None and funding_rate > self.funding_aggressive_threshold)
        )
        
        if is_aggressive:
            reasons.append("高波动率")
            if atr_ratio > self.atr_active_threshold:
                reasons.append("ATR突破")
            if volume_ratio > self.volume_active_multiplier * 2:
                reasons.append("放量")
            if funding_rate and funding_rate > self.funding_aggressive_threshold:
                reasons.append("正资金费率")
            return MarketState.AGGRESSIVE, reasons
        
        # 默认为ACTIVE状态
        reasons.append("正常波动")
        if volume_ratio > self.volume_active_multiplier:
            reasons.append("活跃成交")
        return MarketState.ACTIVE, reasons
    
    def _calculate_score(self, 
                        state: MarketState, 
                        atr_ratio: float, 
                        volume_ratio: float, 
                        funding_rate: Optional[float]) -> float:
        """
        计算市场活跃度评分（0-100）
        
        Args:
            state: 市场状态
            atr_ratio: ATR比率
            volume_ratio: 成交量比率
            funding_rate: 资金费率
            
        Returns:
            评分
        """
        # 基础分
        base_score = {
            MarketState.SLEEP: 10,
            MarketState.ACTIVE: 50,
            MarketState.AGGRESSIVE: 80
        }.get(state, 50)
        
        # ATR加分（0-30）
        atr_score = min(30, atr_ratio * 1000)
        
        # 成交量加分（0-20）
        volume_score = min(20, (volume_ratio - 1) * 20)
        
        # 资金费率加分（0-10）
        funding_score = 0
        if funding_rate is not None:
            if funding_rate > 0:
                funding_score = min(10, funding_rate * 100000)
            else:
                funding_score = -min(5, abs(funding_rate) * 100000)
        
        # 总分
        total_score = base_score + atr_score + volume_score + funding_score
        
        # 限制在0-100范围内
        return max(0, min(100, total_score))
    
    def is_tradeable(self) -> bool:
        """
        判断是否适合交易
        
        Returns:
            是否可交易
        """
        state_info = self.analyze()
        return state_info.state != MarketState.SLEEP
    
    def set_sleep_filter(self, enable: bool):
        """
        设置市场休眠过滤开关
        
        Args:
            enable: True=启用休眠过滤，False=禁用休眠过滤
        """
        self.enable_sleep_filter = enable
    
    def get_sleep_filter_status(self) -> bool:
        """
        获取市场休眠过滤开关状态
        
        Returns:
            是否启用休眠过滤
        """
        return self.enable_sleep_filter
    
    def get_state(self) -> MarketState:
        """
        获取当前市场状态
        
        Returns:
            市场状态
        """
        return self.analyze().state
    
    def get_state_info(self) -> Dict:
        """
        获取市场状态详细信息
        
        Returns:
            状态信息字典
        """
        info = self.analyze()
        return {
            'state': info.state.value,
            'atr': info.atr,
            'atr_ratio': info.atr_ratio,
            'volume_ratio': info.volume_ratio,
            'funding_rate': info.funding_rate,
            'score': info.score,
            'reasons': info.reasons,
            'timestamp': info.timestamp.isoformat()
        }
    
    def analyze_batch(self, symbols: List[str]) -> Dict[str, MarketStateInfo]:
        """
        批量分析多个标的的市场状态
        
        Args:
            symbols: 交易对列表
            
        Returns:
            市场状态信息字典 {symbol: MarketStateInfo}
        """
        results = {}
        
        for symbol in symbols:
            try:
                # 创建临时引擎实例分析单个标的
                temp_engine = MarketStateEngine(
                    self.data_fetcher,
                    symbol=symbol,
                    interval=self.interval
                )
                results[symbol] = temp_engine.analyze()
            except Exception as e:
                print(f"分析 {symbol} 市场状态失败: {str(e)}")
                results[symbol] = MarketStateInfo(
                    state=MarketState.SLEEP,
                    atr=0.0,
                    atr_ratio=0.0,
                    volume_ratio=0.0,
                    funding_rate=None,
                    score=0.0,
                    timestamp=datetime.now(),
                    reasons=['分析失败']
                )
        
        return results
    
    def get_tradeable_symbols(self, symbols: List[str]) -> List[str]:
        """
        获取适合交易的标的列表
        
        Args:
            symbols: 交易对列表
            
        Returns:
            可交易标的列表
        """
        results = []
        state_infos = self.analyze_batch(symbols)
        
        for symbol, state_info in state_infos.items():
            if state_info.state != MarketState.SLEEP:
                results.append(symbol)
        
        return results


# 测试代码
if __name__ == "__main__":
    print("市场状态引擎测试")
    
    # 创建数据获取器
    from data_fetcher import DataFetcher
    from binance_api_client import BinanceAPIClient
    
    client = BinanceAPIClient()
    fetcher = DataFetcher(client)
    engine = MarketStateEngine(fetcher, symbol="ETHUSDT", interval="5m")
    
    try:
        print("\n分析市场状态...")
        state_info = engine.analyze()
        
        print(f"\n市场状态: {state_info.state.value}")
        print(f"ATR: {state_info.atr:.2f}")
        print(f"ATR比率: {state_info.atr_ratio:.2f}")
        print(f"成交量比率: {state_info.volume_ratio:.2f}")
        print(f"资金费率: {state_info.funding_rate}")
        print(f"综合评分: {state_info.score:.1f}/100")
        print(f"原因: {', '.join(state_info.reasons)}")
        
        print(f"\n是否适合交易: {engine.is_tradeable()}")
        
        print("\n状态信息详情:")
        state_dict = engine.get_state_info()
        for key, value in state_dict.items():
            print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        print("注意：此测试需要网络连接到币安API")
