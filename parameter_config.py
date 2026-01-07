#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
参数配置管理
集中管理系统所有可配置参数
"""

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class FakeoutStrategyConfig:
    """假突破策略参数"""
    swing_period: int = 3              # 摆动点检测周期
    breakout_confirmation: int = 2      # 突破确认K线数
    fakeout_confirmation: int = 1       # 假突破确认K线数
    min_body_ratio: float = 0.3        # K线实体占比
    max_structure_levels: int = 20     # 最大结构位数量
    structure_valid_bars: int = 50     # 结构位有效K线数


@dataclass
class RiskManagerConfig:
    """风险管理参数"""
    max_drawdown_percent: float = 5.0         # 最大回撤百分比（与RiskManager默认值一致）
    max_consecutive_losses: int = 3           # 最大连续亏损次数
    daily_loss_limit: float = 30.0            # 每日亏损限制（USDT，与RiskManager默认值一致）
    risk_per_trade: float = 0.02              # 单笔风险比例
    max_position_size: float = 0.3            # 最大仓位比例
    position_size_leverage: float = 10.0      # 杠杆倍数


@dataclass
class WorthTradingFilterConfig:
    """交易价值过滤参数"""
    min_rr_ratio: float = 2.0                # 最小盈亏比
    min_expected_move: float = 0.005         # 最小预期波动（0.5%）
    cost_multiplier: float = 2.0             # 成本倍数
    min_atr_ratio: float = 0.01               # 最小ATR比例


@dataclass
class ExecutionGateConfig:
    """执行闸门参数"""
    min_trade_interval_minutes: int = 10     # 最小交易间隔（分钟）
    max_daily_trades: int = 20               # 每日最大交易次数
    min_signal_confidence: float = 0.6       # 最小信号置信度
    max_spread_percent: float = 0.05         # 最大点差百分比


@dataclass
class SystemConfig:
    """系统运行参数"""
    loop_interval_seconds: int = 10          # 主循环间隔（秒）
    data_refresh_interval: int = 30          # 数据刷新间隔（秒）
    enable_simulation: bool = True           # 是否启用模拟模式
    auto_start: bool = False                 # 是否自动启动
    log_level: str = "INFO"                  # 日志级别
    max_symbols_to_monitor: int = 5          # 最大监控标的数


@dataclass
class MarketStateEngineConfig:
    """市场状态引擎参数"""
    volatility_window: int = 14              # 波动率计算窗口
    trend_ma_fast: int = 7                   # 快速均线周期
    trend_ma_slow: int = 25                  # 慢速均线周期
    volume_ma_period: int = 20               # 成交量均线周期
    enable_market_sleep_filter: bool = True  # 是否启用市场休眠过滤（默认启用）


@dataclass
class FVGStrategyConfig:
    """FVG策略参数"""
    # FVG识别参数
    fvg_detection_lookback: int = 50        # FVG检测回看K线数
    fvg_min_gap_ratio: float = 0.001        # 最小FVG缺口比例（0.1%）
    fvg_max_age_bars: int = 30              # FVG最大有效K线数（新鲜度）
    
    # FVG验证参数
    min_fvg_quality: float = 0.6            # 最小FVG质量分数
    enable_fvg_retest: bool = True         # 是否启用FVG回踩验证
    
    # 多周期参数
    timeframes: list = field(default_factory=lambda: ['5m', '15m', '1h'])  # 支持的周期
    primary_timeframe: str = '5m'           # 主周期
    timeframe_weights: dict = field(default_factory=lambda: {'5m': 1.0, '15m': 2.0, '1h': 3.0})  # 周期权重
    
    # 置信度评分权重
    quality_weight: float = 0.30            # FVG质量权重
    freshness_weight: float = 0.25          # 新鲜度权重
    location_weight: float = 0.25           # 位置权重
    rr_ratio_weight: float = 0.20           # 盈亏比权重
    
    # 交易参数
    min_confidence: float = 0.60            # 最小置信度阈值
    min_rr_ratio: float = 2.0               # 最小盈亏比


@dataclass
class LiquidityAnalyzerConfig:
    """流动性分析参数"""
    # 摆动点识别参数
    swing_period: int = 3                   # 摆动点检测周期
    min_swing_strength: float = 0.005      # 最小摆动点强度（0.5%）
    max_swings: int = 20                    # 最大摆动点数量
    
    # 流动性区参数
    liquidity_zone_size: float = 0.001      # 流动性区大小（0.1%）
    min_liquidity_touches: int = 2          # 最小流动性触碰次数
    
    # 流动性捕取参数
    fakeout_confirmation_bars: int = 2     # 假突破确认K线数
    fakeout_min_body_ratio: float = 0.3    # 假突破K线最小实体比例
    liquidity_catch_window: int = 5        # 流动性捕取检测窗口
    
    # 多周期参数
    liquidity_timeframes: list = field(default_factory=lambda: ['15m', '1h', '4h'])  # 流动性分析周期
    liquidity_weight: float = 0.4           # 流动性信号在总评分中的权重


@dataclass
class ParameterConfig:
    """参数配置总类"""
    fakeout_strategy: FakeoutStrategyConfig = field(default_factory=FakeoutStrategyConfig)
    risk_manager: RiskManagerConfig = field(default_factory=RiskManagerConfig)
    worth_trading_filter: WorthTradingFilterConfig = field(default_factory=WorthTradingFilterConfig)
    execution_gate: ExecutionGateConfig = field(default_factory=ExecutionGateConfig)
    system: SystemConfig = field(default_factory=SystemConfig)
    market_state_engine: MarketStateEngineConfig = field(default_factory=MarketStateEngineConfig)
    fvg_strategy: FVGStrategyConfig = field(default_factory=FVGStrategyConfig)
    liquidity_analyzer: LiquidityAnalyzerConfig = field(default_factory=LiquidityAnalyzerConfig)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'fakeout_strategy': self.fakeout_strategy.__dict__,
            'risk_manager': self.risk_manager.__dict__,
            'worth_trading_filter': self.worth_trading_filter.__dict__,
            'execution_gate': self.execution_gate.__dict__,
            'system': self.system.__dict__,
            'market_state_engine': self.market_state_engine.__dict__,
            'fvg_strategy': self.fvg_strategy.__dict__,
            'liquidity_analyzer': self.liquidity_analyzer.__dict__
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """从字典加载"""
        if 'fakeout_strategy' in data:
            for k, v in data['fakeout_strategy'].items():
                setattr(self.fakeout_strategy, k, v)
        if 'risk_manager' in data:
            for k, v in data['risk_manager'].items():
                setattr(self.risk_manager, k, v)
        if 'worth_trading_filter' in data:
            for k, v in data['worth_trading_filter'].items():
                setattr(self.worth_trading_filter, k, v)
        if 'execution_gate' in data:
            for k, v in data['execution_gate'].items():
                setattr(self.execution_gate, k, v)
        if 'system' in data:
            for k, v in data['system'].items():
                setattr(self.system, k, v)
        if 'market_state_engine' in data:
            for k, v in data['market_state_engine'].items():
                setattr(self.market_state_engine, k, v)
        if 'fvg_strategy' in data:
            for k, v in data['fvg_strategy'].items():
                # 特殊处理列表和字典类型
                if k == 'timeframes' or k == 'liquidity_timeframes':
                    if isinstance(v, list):
                        setattr(self.fvg_strategy, k, v)
                elif k == 'timeframe_weights':
                    if isinstance(v, dict):
                        setattr(self.fvg_strategy, k, v)
                else:
                    setattr(self.fvg_strategy, k, v)
        if 'liquidity_analyzer' in data:
            for k, v in data['liquidity_analyzer'].items():
                # 特殊处理列表类型
                if k == 'liquidity_timeframes':
                    if isinstance(v, list):
                        setattr(self.liquidity_analyzer, k, v)
                else:
                    setattr(self.liquidity_analyzer, k, v)


# 全局配置实例
_global_config = ParameterConfig()


def get_config() -> ParameterConfig:
    """获取全局配置"""
    return _global_config


def update_config(updates: Dict[str, Any]):
    """
    更新配置
    
    Args:
        updates: 更新的配置字典
    """
    _global_config.from_dict(updates)
