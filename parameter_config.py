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
class ParameterConfig:
    """参数配置总类"""
    fakeout_strategy: FakeoutStrategyConfig = field(default_factory=FakeoutStrategyConfig)
    risk_manager: RiskManagerConfig = field(default_factory=RiskManagerConfig)
    worth_trading_filter: WorthTradingFilterConfig = field(default_factory=WorthTradingFilterConfig)
    execution_gate: ExecutionGateConfig = field(default_factory=ExecutionGateConfig)
    system: SystemConfig = field(default_factory=SystemConfig)
    market_state_engine: MarketStateEngineConfig = field(default_factory=MarketStateEngineConfig)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'fakeout_strategy': self.fakeout_strategy.__dict__,
            'risk_manager': self.risk_manager.__dict__,
            'worth_trading_filter': self.worth_trading_filter.__dict__,
            'execution_gate': self.execution_gate.__dict__,
            'system': self.system.__dict__,
            'market_state_engine': self.market_state_engine.__dict__
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
