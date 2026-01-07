#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FVG和流动性策略 - 信号数据结构
定义FVG缺口、流动性区域和交易信号的数据结构
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, List
from datetime import datetime


class FVGType(Enum):
    """FVG类型"""
    BULLISH = "BULLISH"   # 看涨FVG（向上缺口）
    BEARISH = "BEARISH"   # 看跌FVG（向下缺口）


class LiquidityType(Enum):
    """流动性类型"""
    BUYSIDE = "BUYSIDE"     # 买方流动性（下方）
    SELLSIDE = "SELLSIDE"   # 卖方流动性（上方）


class SignalType(Enum):
    """信号类型"""
    BUY = "BUY"
    SELL = "SELL"


class SignalSource(Enum):
    """信号来源"""
    FVG = "FVG"                           # FVG回补
    LIQUIDITY_SWEEP = "LIQUIDITY_SWEEP"   # 流动性捕取
    CONFLUENCE = "CONFLUENCE"             # FVG + 流动性共振


@dataclass
class FVG:
    """FVG缺口数据结构"""
    gap_type: FVGType           # FVG类型
    high_bound: float           # 缺口上界
    low_bound: float            # 缺口下界
    size: float                 # 缺口大小（绝对值）
    size_percent: float         # 缺口大小（百分比）
    formation_time: int         # 形成时间（时间戳）
    kline_index: int            # K线索引
    is_filled: bool = False     # 是否被填充
    fill_time: Optional[int] = None  # 填充时间

    @property
    def midpoint(self) -> float:
        """缺口中点"""
        return (self.high_bound + self.low_bound) / 2

    def is_active(self, current_time: int, max_age_minutes: int = 60) -> bool:
        """判断FVG是否仍然活跃"""
        if self.is_filled:
            return False

        age_seconds = (current_time - self.formation_time) / 1000
        age_minutes = age_seconds / 60

        return age_minutes < max_age_minutes

    def __repr__(self) -> str:
        return (f"FVG({self.gap_type.value}, "
                f"high={self.high_bound:.2f}, "
                f"low={self.low_bound:.2f}, "
                f"size={self.size_percent:.3f}%)")


@dataclass
class LiquidityZone:
    """流动性区域数据结构"""
    zone_type: LiquidityType     # 流动性类型
    level: float                 # 流动性水平（价格）
    strength: float              # 流动性强度（0-1）
    formation_time: int          # 形成时间
    touched_count: int = 0       # 被触摸次数
    is_swept: bool = False      # 是否被扫过
    sweep_time: Optional[int] = None  # 扫过时间

    def update_strength(self, factor: float = 1.0):
        """更新流动性强度"""
        self.strength = min(1.0, self.strength * factor)

    def increment_touch(self):
        """增加触摸次数，降低强度"""
        self.touched_count += 1
        # 每次触摸后强度降低20%
        self.update_strength(0.8)

    def __repr__(self) -> str:
        return (f"LiquidityZone({self.zone_type.value}, "
                f"level={self.level:.2f}, "
                f"strength={self.strength:.2f}, "
                f"touched={self.touched_count})")


@dataclass
class SwingPoint:
    """摆动点（高低点）"""
    point_type: str              # "HIGH" or "LOW"
    price: float                 # 摆动点价格
    time: int                    # 时间
    index: int                   # K线索引

    def __repr__(self) -> str:
        return (f"SwingPoint({self.point_type}, "
                f"price={self.price:.2f})")


@dataclass
class TimeframeAnalysis:
    """单周期分析结果"""
    timeframe: str               # 周期（如"5m"）
    fvg_list: List[FVG]          # 该周期的FVG列表
    buyside_liquidity: List[LiquidityZone]  # 买方流动性区
    sellside_liquidity: List[LiquidityZone]  # 卖方流动性区
    swing_highs: List[SwingPoint]  # 摆动高点
    swing_lows: List[SwingPoint]   # 摆动低点
    current_price: float          # 当前价格
    analysis_time: int            # 分析时间

    def get_active_fvgs(self, max_age_minutes: int = 60) -> List[FVG]:
        """获取活跃的FVG"""
        return [fvg for fvg in self.fvg_list
                if fvg.is_active(self.analysis_time, max_age_minutes)]

    def get_bullish_fvgs(self) -> List[FVG]:
        """获取看涨FVG"""
        return [fvg for fvg in self.fvg_list if fvg.gap_type == FVGType.BULLISH]

    def get_bearish_fvgs(self) -> List[FVG]:
        """获取看跌FVG"""
        return [fvg for fvg in self.fvg_list if fvg.gap_type == FVGType.BEARISH]


@dataclass
class ConfluenceAnalysis:
    """周期共振分析"""
    symbol: str                  # 交易对
    primary_timeframe: str       # 主周期
    confluence_timeframes: List[str]  # 共振周期列表
    signals: List['FVGSignal']   # 所有周期的信号
    best_signal: Optional['FVGSignal'] = None  # 最佳信号
    confluence_score: float = 0.0   # 共振分数（0-1）


@dataclass
class FVGSignal:
    """FVG交易信号"""
    signal_type: SignalType                  # 信号类型（BUY/SELL）
    signal_source: SignalSource              # 信号来源
    symbol: str                              # 交易对
    entry_price: float                       # 入场价格
    stop_loss: float                         # 止损价格
    take_profit: float                       # 止盈价格
    confidence: float                        # 信号置信度（0-1）
    timeframe: str                           # 交易周期

    # 关联数据
    fvg: Optional[FVG] = None                # 关联的FVG
    liquidity_zone: Optional[LiquidityZone] = None  # 关联的流动性区
    swing_point: Optional[SwingPoint] = None  # 关联的摆动点

    # 多周期信息
    timeframe_confluence: Dict[str, bool] = None  # 多周期共振情况（周期: 是否共振）
    primary_timeframe: str = "5m"            # 主周期

    # 风险回报
    risk_reward_ratio: float = 0.0           # 盈亏比
    risk_amount: float = 0.0                 # 风险金额（绝对值）
    risk_percent: float = 0.0                 # 风险百分比

    # 元数据
    reason: str = ""                         # 信号原因
    timestamp: int = 0                       # 信号时间
    signal_id: str = ""                      # 信号唯一ID

    def __post_init__(self):
        """初始化后处理"""
        if self.timeframe_confluence is None:
            self.timeframe_confluence = {}

        if self.timestamp == 0:
            self.timestamp = int(datetime.now().timestamp() * 1000)

        if self.signal_id == "":
            self.signal_id = f"{self.symbol}_{self.signal_type.value}_{self.timestamp}"

        # 计算风险回报比
        if self.stop_loss > 0 and self.take_profit > 0 and self.entry_price > 0:
            if self.signal_type == SignalType.BUY:
                self.risk_amount = self.entry_price - self.stop_loss
                self.risk_percent = self.risk_amount / self.entry_price
                reward_amount = self.take_profit - self.entry_price
                if self.risk_amount > 0:
                    self.risk_reward_ratio = reward_amount / self.risk_amount
            else:  # SELL
                self.risk_amount = self.stop_loss - self.entry_price
                self.risk_percent = self.risk_amount / self.entry_price
                reward_amount = self.entry_price - self.take_profit
                if self.risk_amount > 0:
                    self.risk_reward_ratio = reward_amount / self.risk_amount


@dataclass
class FakeoutSignal:
    """假突破交易信号（兼容假突破策略）"""
    symbol: str                              # 交易对
    signal_type: SignalType                  # 信号类型（BUY/SELL）
    entry_price: float                       # 入场价格
    stop_loss: float                         # 止损价格
    take_profit: float                       # 止盈价格
    confidence: float                        # 信号置信度（0-1）
    timeframe: str                           # 交易周期
    
    # 假突破特有属性
    structure_level: float                   # 结构水平
    breakout_price: float                    # 突破价格
    fakeout_price: float                     # 假突破价格
    swing_period: int                        # 摆动点周期
    
    # 元数据
    timestamp: int = 0                       # 信号时间
    signal_id: str = ""                      # 信号唯一ID
    reason: str = ""                         # 信号原因
    
    def __post_init__(self):
        """初始化后处理"""
        if self.timestamp == 0:
            self.timestamp = int(datetime.now().timestamp() * 1000)
        
        if self.signal_id == "":
            self.signal_id = f"{self.symbol}_{self.signal_type.value}_{self.timestamp}"


# TradingSignal是FVGSignal的别名，保持向后兼容
TradingSignal = FVGSignal
