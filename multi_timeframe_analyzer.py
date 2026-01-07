#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多周期分析器
支持多周期FVG和流动性分析，实现周期共振检测
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
import threading

from fvg_signal import FVG, LiquidityZone, TradingSignal
from fvg_strategy import FVGStrategy
from liquidity_analyzer import LiquidityAnalyzer
from parameter_config import get_config, FVGStrategyConfig, LiquidityAnalyzerConfig

logger = logging.getLogger(__name__)


@dataclass
class TimeframeAnalysis:
    """单周期分析结果"""
    timeframe: str                          # 周期（如 '15m', '1h', '4h'）
    bullish_fvgs: List[FVG]                 # 看涨FVG列表
    bearish_fvgs: List[FVG]                 # 看跌FVG列表
    liquidity_zones: List[LiquidityZone]    # 流动性区列表
    trading_signals: List[TradingSignal]    # 交易信号列表
    analysis_time: datetime                 # 分析时间
    is_valid: bool = True                   # 分析是否有效


@dataclass
class MultiTimeframeConfluence:
    """多周期共振分析结果"""
    symbol: str                             # 交易对
    confluence_type: str                    # 共振类型（'BUY'/'SELL'/'NEUTRAL'）
    confluence_score: float                 # 共振评分（0-1）
    timeframe_weighted_score: Dict[str, float]  # 各周期加权评分
    contributing_timeframes: List[str]      # 参与共振的周期
    primary_signal: Optional[TradingSignal]  # 主信号（来自主周期）
    support_signals: List[TradingSignal]    # 辅助信号
    fvg_confluence: Dict[str, List[FVG]]   # FVG共振（周期 -> FVG列表）
    liquidity_confluence: Dict[str, LiquidityZone]  # 流动性共振
    confidence: float                       # 综合置信度
    analysis_time: datetime                 # 分析时间


class MultiTimeframeAnalyzer:
    """多周期分析器"""
    
    def __init__(self, config: Optional[ParameterConfig] = None):
        """
        初始化多周期分析器
        
        Args:
            config: 参数配置，如果不提供则使用全局配置
        """
        self.config = config or get_config()
        self.fvg_config = self.config.fvg_strategy
        self.liquidity_config = self.config.liquidity_analyzer
        
        # 初始化FVG策略和流动性分析器
        self.fvg_strategy = FVGStrategy(self.fvg_config)
        self.liquidity_analyzer = LiquidityAnalyzer(self.liquidity_config)
        
        # 缓存各周期的分析结果
        self._cache: Dict[str, Dict[str, TimeframeAnalysis]] = {}
        self._cache_lock = threading.Lock()
        
        logger.info("多周期分析器初始化完成")
    
    def analyze_timeframe(
        self,
        symbol: str,
        timeframe: str,
        klines: List[Dict[str, Any]]
    ) -> TimeframeAnalysis:
        """
        分析单个周期
        
        Args:
            symbol: 交易对
            timeframe: 周期（如 '15m', '1h', '4h'）
            klines: K线数据列表
            
        Returns:
            TimeframeAnalysis: 单周期分析结果
        """
        try:
            # FVG分析
            bullish_fvgs, bearish_fvgs = self.fvg_strategy.detect_fvgs(klines)
            
            # 验证FVG
            bullish_fvgs = [fvg for fvg in bullish_fvgs 
                           if self.fvg_strategy.validate_fvg(fvg, klines)]
            bearish_fvgs = [fvg for fvg in bearish_fvgs 
                           if self.fvg_strategy.validate_fvg(fvg, klines)]
            
            # 流动性分析 - 识别买方和卖方流动性区
            buyside_zones = self.liquidity_analyzer.identify_buyside_liquidity(timeframe)
            sellside_zones = self.liquidity_analyzer.identify_sellside_liquidity(timeframe)
            liquidity_zones = buyside_zones + sellside_zones

            # 生成交易信号
            trading_signals = self.fvg_strategy.generate_signals(
                symbol, timeframe, klines
            )

            # 添加流动性捕取信号
            liquidity_signals = self.liquidity_analyzer.generate_liquidity_sweep_signals(timeframe)
            trading_signals.extend(liquidity_signals)

            return TimeframeAnalysis(
                timeframe=timeframe,
                bullish_fvgs=bullish_fvgs,
                bearish_fvgs=bearish_fvgs,
                liquidity_zones=liquidity_zones,
                trading_signals=trading_signals,
                analysis_time=datetime.now(),
                is_valid=True
            )
            
        except Exception as e:
            logger.error(f"分析周期 {timeframe} 失败: {e}")
            return TimeframeAnalysis(
                timeframe=timeframe,
                bullish_fvgs=[],
                bearish_fvgs=[],
                liquidity_zones=[],
                trading_signals=[],
                analysis_time=datetime.now(),
                is_valid=False
            )
    
    def analyze_multi_timeframe(
        self,
        symbol: str,
        klines_data: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, TimeframeAnalysis]:
        """
        分析多个周期
        
        Args:
            symbol: 交易对
            klines_data: 各周期K线数据字典 {timeframe: klines}
            
        Returns:
            Dict[str, TimeframeAnalysis]: 各周期分析结果
        """
        results = {}
        
        with self._cache_lock:
            for timeframe, klines in klines_data.items():
                analysis = self.analyze_timeframe(symbol, timeframe, klines)
                results[timeframe] = analysis
                
                # 更新缓存
                if symbol not in self._cache:
                    self._cache[symbol] = {}
                self._cache[symbol][timeframe] = analysis
        
        return results
    
    def detect_confluence(
        self,
        symbol: str,
        timeframe_analyses: Dict[str, TimeframeAnalysis]
    ) -> Optional[MultiTimeframeConfluence]:
        """
        检测多周期共振
        
        Args:
            symbol: 交易对
            timeframe_analyses: 各周期分析结果
            
        Returns:
            MultiTimeframeConfluence: 共振分析结果，如果没有共振则返回None
        """
        # 过滤无效的分析结果
        valid_analyses = {
            tf: analysis 
            for tf, analysis in timeframe_analyses.items() 
            if analysis.is_valid and len(analysis.trading_signals) > 0
        }
        
        if not valid_analyses:
            return None
        
        # 收集所有信号
        all_signals = []
        for tf, analysis in valid_analyses.items():
            for signal in analysis.trading_signals:
                all_signals.append((tf, signal))
        
        # 统计做多和做空信号数量
        buy_signals = [s for tf, s in all_signals if s.direction == 'BUY']
        sell_signals = [s for tf, s in all_signals if s.direction == 'SELL']
        
        # 计算加权评分
        buy_score = self._calculate_weighted_score(buy_signals, valid_analyses)
        sell_score = self._calculate_weighted_score(sell_signals, valid_analyses)
        
        # 确定共振类型
        if buy_score > sell_score and buy_score > 0.3:
            confluence_type = 'BUY'
        elif sell_score > buy_score and sell_score > 0.3:
            confluence_type = 'SELL'
        else:
            return None
        
        # 获取主周期信号
        primary_tf = self.fvg_config.primary_timeframe
        primary_signal = None
        primary_analysis = valid_analyses.get(primary_tf)
        
        if primary_analysis and primary_analysis.trading_signals:
            for signal in primary_analysis.trading_signals:
                if signal.direction == confluence_type:
                    primary_signal = signal
                    break
        
        # 收集辅助信号
        support_signals = []
        for tf, analysis in valid_analyses.items():
            if tf != primary_tf:
                for signal in analysis.trading_signals:
                    if signal.direction == confluence_type:
                        support_signals.append(signal)
        
        # 收集FVG共振
        fvg_confluence = {}
        for tf, analysis in valid_analyses.items():
            if confluence_type == 'BUY':
                fvgs = analysis.bullish_fvgs
            else:
                fvgs = analysis.bearish_fvgs
            
            if fvgs:
                fvg_confluence[tf] = fvgs
        
        # 收集流动性共振
        liquidity_confluence = {}
        for tf, analysis in valid_analyses.items():
            for zone in analysis.liquidity_zones:
                if zone.direction == confluence_type:
                    liquidity_confluence[tf] = zone
                    break
        
        # 计算最终置信度
        confluence_score = max(buy_score, sell_score)
        confidence = min(confluence_score * 1.2, 1.0)  # 共振时置信度提升20%
        
        # 收集参与共振的周期
        contributing_timeframes = [
            tf for tf, s in all_signals 
            if s.direction == confluence_type
        ]
        
        # 计算各周期加权评分
        timeframe_weighted_score = {}
        for tf, analysis in valid_analyses.items():
            tf_signals = [
                s for s in analysis.trading_signals 
                if s.direction == confluence_type
            ]
            if tf_signals:
                avg_confidence = sum(s.confidence for s in tf_signals) / len(tf_signals)
                weight = self.fvg_config.timeframe_weights.get(tf, 1.0)
                timeframe_weighted_score[tf] = avg_confidence * weight
        
        return MultiTimeframeConfluence(
            symbol=symbol,
            confluence_type=confluence_type,
            confluence_score=confluence_score,
            timeframe_weighted_score=timeframe_weighted_score,
            contributing_timeframes=contributing_timeframes,
            primary_signal=primary_signal,
            support_signals=support_signals,
            fvg_confluence=fvg_confluence,
            liquidity_confluence=liquidity_confluence,
            confidence=confidence,
            analysis_time=datetime.now()
        )
    
    def _calculate_weighted_score(
        self,
        signals: List[Tuple[str, TradingSignal]],
        analyses: Dict[str, TimeframeAnalysis]
    ) -> float:
        """
        计算加权评分
        
        Args:
            signals: 信号列表 (timeframe, signal)
            analyses: 各周期分析结果
            
        Returns:
            float: 加权评分
        """
        if not signals:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for tf, signal in signals:
            weight = self.fvg_config.timeframe_weights.get(tf, 1.0)
            score = signal.confidence * weight
            total_score += score
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return total_score / total_weight
    
    def get_best_signals(
        self,
        symbol: str,
        timeframe_analyses: Dict[str, TimeframeAnalysis],
        top_n: int = 3
    ) -> List[TradingSignal]:
        """
        获取最佳信号
        
        Args:
            symbol: 交易对
            timeframe_analyses: 各周期分析结果
            top_n: 返回信号数量
            
        Returns:
            List[TradingSignal]: 最佳信号列表
        """
        all_signals = []
        
        for tf, analysis in timeframe_analyses.items():
            for signal in analysis.trading_signals:
                # 应用周期权重调整置信度
                weight = self.fvg_config.timeframe_weights.get(tf, 1.0)
                adjusted_confidence = min(signal.confidence * weight, 1.0)
                
                # 创建带权重的信号副本
                weighted_signal = TradingSignal(
                    symbol=signal.symbol,
                    timeframe=tf,
                    direction=signal.direction,
                    entry_price=signal.entry_price,
                    stop_loss=signal.stop_loss,
                    take_profit=signal.take_profit,
                    confidence=adjusted_confidence,
                    fvg_reference=signal.fvg_reference,
                    liquidity_zone=signal.liquidity_zone,
                    signal_type=signal.signal_type
                )
                
                all_signals.append(weighted_signal)
        
        # 按置信度排序
        all_signals.sort(key=lambda x: x.confidence, reverse=True)
        
        return all_signals[:top_n]
    
    def get_cached_analysis(
        self,
        symbol: str,
        timeframe: str
    ) -> Optional[TimeframeAnalysis]:
        """
        获取缓存的分析结果
        
        Args:
            symbol: 交易对
            timeframe: 周期
            
        Returns:
            Optional[TimeframeAnalysis]: 缓存的分析结果
        """
        with self._cache_lock:
            if symbol in self._cache and timeframe in self._cache[symbol]:
                return self._cache[symbol][timeframe]
            return None
    
    def clear_cache(self, symbol: Optional[str] = None):
        """
        清空缓存
        
        Args:
            symbol: 交易对，如果为None则清空所有缓存
        """
        with self._cache_lock:
            if symbol:
                if symbol in self._cache:
                    del self._cache[symbol]
            else:
                self._cache.clear()
