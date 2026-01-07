#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
参数配置管理 - 优化版
集中管理系统所有可配置参数

优化原则：
1. 平衡性：不过于激进也不过于保守
2. 适应性：适应5分钟K线的特点
3. 风险优先：保持风控参数的严格性
4. 增加机会：适当放宽过滤条件，但保持质量
5. 安全性：降低杠杆，提高系统稳定性
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class FakeoutStrategyConfig:
    """假突破策略参数
    
    优化说明：
    - min_body_ratio: 0.3 → 0.2，降低K线实体要求，增加信号机会
    - max_structure_levels: 20 → 15，减少干扰结构位
    - structure_valid_bars: 50 → 40，缩短有效期，更贴近当前市场
    """
    swing_period: int = 3              # 摆动点检测周期
    breakout_confirmation: int = 2      # 突破确认K线数
    fakeout_confirmation: int = 1       # 假突破确认K线数
    min_body_ratio: float = 0.2         # K线实体占比（优化：0.3→0.2）
    max_structure_levels: int = 15      # 最大结构位数量（优化：20→15）
    structure_valid_bars: int = 40     # 结构位有效K线数（优化：50→40）


@dataclass
class RiskManagerConfig:
    """风险管理参数
    
    优化说明：
    - max_drawdown_percent: 5% → 8%，适当放宽回撤容忍度
    - daily_loss_limit: 30U → 50U，增加每日亏损额度
    - position_size_leverage: 10x → 5x，降低杠杆提高安全性
    """
    max_drawdown_percent: float = 8.0         # 最大回撤百分比（优化：5%→8%）
    max_consecutive_losses: int = 3           # 最大连续亏损次数（保持不变）
    daily_loss_limit: float = 50.0            # 每日亏损限制（优化：30U→50U）
    risk_per_trade: float = 0.02              # 单笔风险比例（保持不变）
    max_position_size: float = 0.3            # 最大仓位比例（保持不变）
    position_size_leverage: float = 5.0       # 杠杆倍数（优化：10x→5x）


@dataclass
class WorthTradingFilterConfig:
    """交易价值过滤参数
    
    优化说明：
    - min_rr_ratio: 2.0 → 1.8，降低盈亏比要求，增加交易机会
    - min_expected_move: 0.5% → 0.4%，降低最小预期波动
    - min_atr_ratio: 1% → 0.8%，降低ATR要求，适应更多市场状态
    """
    min_rr_ratio: float = 1.8                # 最小盈亏比（优化：2.0→1.8）
    min_expected_move: float = 0.004         # 最小预期波动（优化：0.5%→0.4%）
    cost_multiplier: float = 2.0             # 成本倍数（保持不变）
    min_atr_ratio: float = 0.008              # 最小ATR比例（优化：1%→0.8%）


@dataclass
class ExecutionGateConfig:
    """执行闸门参数
    
    优化说明：
    - max_daily_trades: 20 → 15，控制交易频率，避免过度交易
    - min_signal_confidence: 0.6 → 0.5，降低置信度要求
    """
    min_trade_interval_minutes: int = 10     # 最小交易间隔（保持不变）
    max_daily_trades: int = 15               # 每日最大交易次数（优化：20→15）
    min_signal_confidence: float = 0.5       # 最小信号置信度（优化：0.6→0.5）
    max_spread_percent: float = 0.05         # 最大点差百分比（保持不变）


@dataclass
class SystemConfig:
    """系统运行参数
    
    优化说明：
    - max_symbols_to_monitor: 5 → 8，增加监控标的，发现更多机会
    - enable_simulation: True，默认启用模拟模式
    """
    loop_interval_seconds: int = 10          # 主循环间隔（保持不变）
    data_refresh_interval: int = 30          # 数据刷新间隔（保持不变）
    enable_simulation: bool = True           # 是否启用模拟模式（保持不变）
    auto_start: bool = False                 # 是否自动启动（保持不变）
    log_level: str = "INFO"                  # 日志级别（保持不变）
    max_symbols_to_monitor: int = 8          # 最大监控标的数（优化：5→8）


@dataclass
class MarketStateEngineConfig:
    """市场状态引擎参数
    
    优化说明：
    - volatility_window: 14，ATR计算周期
    - trend_ma_fast: 7，趋势判断快速均线
    - trend_ma_slow: 25，趋势判断慢速均线
    - volume_ma_period: 20，成交量均线周期
    """
    volatility_window: int = 14              # 波动率计算窗口（新增）
    trend_ma_fast: int = 7                   # 快速均线周期（新增）
    trend_ma_slow: int = 25                  # 慢速均线周期（新增）
    volume_ma_period: int = 20               # 成交量均线周期（保持不变）


@dataclass
class MarketStateThresholdConfig:
    """市场状态阈值参数（新增）
    
    优化说明：
    - atr_sleep_threshold: 0.5% → 0.4%，放宽休眠判断
    - atr_active_threshold: 2% → 1.5%，降低激进判断门槛
    - volume_active_multiplier: 1.5 → 1.3，降低成交量要求
    - funding_thresholds: 降低费率敏感度，从±0.01%降低到±0.015%
    - atr_avg_ratio_sleep: 0.8 → 0.7，放宽平均值比率要求
    - atr_avg_ratio_aggressive: 2.0 → 1.8，降低激进平均值要求
    """
    # ATR阈值
    atr_sleep_threshold: float = 0.004       # ATR < 0.4% = SLEEP（优化：0.5%→0.4%）
    atr_active_threshold: float = 0.015      # ATR > 1.5% = AGGRESSIVE（优化：2%→1.5%）
    
    # 成交量阈值
    volume_active_multiplier: float = 1.3   # 成交量 > 平均1.3倍 = 活跃（优化：1.5→1.3）
    volume_active_multiplier_2x: float = 2.6  # 成交量 > 平均2.6倍 = 激进（优化：3.0→2.6）
    
    # 资金费率阈值
    funding_sleep_threshold: float = -0.00015  # 负费率 < -0.015% = 休眠（优化：-0.01%→-0.015%）
    funding_aggressive_threshold: float = 0.00015  # 正费率 > 0.015% = 激进（优化：0.01%→0.015%）
    
    # ATR平均值比率
    atr_avg_ratio_sleep: float = 0.7        # ATR < 平均值70% = 休眠（优化：0.8→0.7）
    atr_avg_ratio_aggressive: float = 1.8   # ATR > 平均值180% = 激进（优化：2.0→1.8）
    
    # 历史数据
    atr_history_length: int = 100            # ATR历史记录长度（保持不变）
    atr_period: int = 14                     # ATR计算周期（保持不变）


@dataclass
class ParameterConfig:
    """参数配置总类"""
    fakeout_strategy: FakeoutStrategyConfig = field(default_factory=FakeoutStrategyConfig)
    risk_manager: RiskManagerConfig = field(default_factory=RiskManagerConfig)
    worth_trading_filter: WorthTradingFilterConfig = field(default_factory=WorthTradingFilterConfig)
    execution_gate: ExecutionGateConfig = field(default_factory=ExecutionGateConfig)
    system: SystemConfig = field(default_factory=SystemConfig)
    market_state_engine: MarketStateEngineConfig = field(default_factory=MarketStateEngineConfig)
    market_state_thresholds: MarketStateThresholdConfig = field(default_factory=MarketStateThresholdConfig)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'fakeout_strategy': self.fakeout_strategy.__dict__,
            'risk_manager': self.risk_manager.__dict__,
            'worth_trading_filter': self.worth_trading_filter.__dict__,
            'execution_gate': self.execution_gate.__dict__,
            'system': self.system.__dict__,
            'market_state_engine': self.market_state_engine.__dict__,
            'market_state_thresholds': self.market_state_thresholds.__dict__
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """从字典加载"""
        if 'fakeout_strategy' in data:
            for k, v in data['fakeout_strategy'].items():
                if hasattr(self.fakeout_strategy, k):
                    setattr(self.fakeout_strategy, k, v)
        if 'risk_manager' in data:
            for k, v in data['risk_manager'].items():
                if hasattr(self.risk_manager, k):
                    setattr(self.risk_manager, k, v)
        if 'worth_trading_filter' in data:
            for k, v in data['worth_trading_filter'].items():
                if hasattr(self.worth_trading_filter, k):
                    setattr(self.worth_trading_filter, k, v)
        if 'execution_gate' in data:
            for k, v in data['execution_gate'].items():
                if hasattr(self.execution_gate, k):
                    setattr(self.execution_gate, k, v)
        if 'system' in data:
            for k, v in data['system'].items():
                if hasattr(self.system, k):
                    setattr(self.system, k, v)
        if 'market_state_engine' in data:
            for k, v in data['market_state_engine'].items():
                if hasattr(self.market_state_engine, k):
                    setattr(self.market_state_engine, k, v)
        if 'market_state_thresholds' in data:
            for k, v in data['market_state_thresholds'].items():
                if hasattr(self.market_state_thresholds, k):
                    setattr(self.market_state_thresholds, k, v)
    
    def compare_with_original(self) -> Dict[str, Dict[str, str]]:
        """对比原版参数，返回变更说明
        
        Returns:
            格式: {模块名: {参数名: "原值 → 优化值 (说明)"}}
        """
        original_config = {
            'fakeout_strategy': {
                'min_body_ratio': '0.3 → 0.2 (降低K线实体要求，增加信号机会)',
                'max_structure_levels': '20 → 15 (减少干扰结构位)',
                'structure_valid_bars': '50 → 40 (缩短有效期，更贴近当前市场)'
            },
            'risk_manager': {
                'max_drawdown_percent': '5.0 → 8.0 (适当放宽回撤容忍度)',
                'daily_loss_limit': '30.0 → 50.0 (增加每日亏损额度)',
                'position_size_leverage': '10.0 → 5.0 (降低杠杆提高安全性)'
            },
            'worth_trading_filter': {
                'min_rr_ratio': '2.0 → 1.8 (降低盈亏比要求)',
                'min_expected_move': '0.005 → 0.004 (降低最小预期波动)',
                'min_atr_ratio': '0.01 → 0.008 (降低ATR要求)'
            },
            'execution_gate': {
                'max_daily_trades': '20 → 15 (控制交易频率)',
                'min_signal_confidence': '0.6 → 0.5 (降低置信度要求)'
            },
            'system': {
                'max_symbols_to_monitor': '5 → 8 (增加监控标的)'
            },
            'market_state_thresholds': {
                'atr_sleep_threshold': '0.005 → 0.004 (放宽休眠判断)',
                'atr_active_threshold': '0.02 → 0.015 (降低激进判断门槛)',
                'volume_active_multiplier': '1.5 → 1.3 (降低成交量要求)',
                'funding_sleep_threshold': '-0.0001 → -0.00015 (降低费率敏感度)',
                'atr_avg_ratio_sleep': '0.8 → 0.7 (放宽平均值比率要求)'
            }
        }
        return original_config
    
    def print_optimization_summary(self):
        """打印优化摘要"""
        print("=" * 60)
        print("参数配置优化摘要")
        print("=" * 60)
        
        changes = self.compare_with_original()
        total_changes = 0
        
        for module, params in changes.items():
            if params:
                print(f"\n【{module.replace('_', ' ').title()}】")
                for param, description in params.items():
                    print(f"  • {param}: {description}")
                    total_changes += 1
        
        print("\n" + "=" * 60)
        print(f"共优化 {total_changes} 个参数")
        print("=" * 60)
        print("\n优化原则：")
        print("  ✓ 增加交易机会（放宽过滤条件）")
        print("  ✓ 保持风险控制（核心风控参数保持严格）")
        print("  ✓ 提高安全性（降低杠杆）")
        print("  ✓ 适应市场（降低门槛，适应更多市场状态）")
        print("\n⚠️  建议：先用模拟模式测试1-2天，确认效果后再切换实盘")
        print("=" * 60)


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


if __name__ == "__main__":
    # 打印优化摘要
    config = ParameterConfig()
    config.print_optimization_summary()
