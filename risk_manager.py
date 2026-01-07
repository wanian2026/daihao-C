#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风险管理器和执行闸门
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, timedelta
from enum import Enum


class CircuitBreakerState(Enum):
    """熔断状态"""
    NORMAL = "NORMAL"           # 正常
    PAUSED = "PAUSED"           # 暂停
    TRIGGERED = "TRIGGERED"     # 触发熔断


@dataclass
class RiskMetrics:
    """风险指标"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    max_drawdown: float = 0.0
    consecutive_losses: int = 0
    max_consecutive_losses: int = 0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    _total_win_amount: float = 0.0  # 内部使用：总盈利金额
    _total_loss_amount: float = 0.0  # 内部使用：总亏损金额


class RiskManager:
    """风险管理器"""
    
    def __init__(self, 
                 max_drawdown_percent: float = 5.0,      # 降低从10%到5%
                 max_consecutive_losses: int = 3,
                 daily_loss_limit: float = 30.0):        # 降低从50U到30U
        """
        初始化风险管理器
        
        Args:
            max_drawdown_percent: 最大回撤百分比
            max_consecutive_losses: 最大连续亏损次数
            daily_loss_limit: 每日亏损限制（USDT）
        """
        self.max_drawdown_percent = max_drawdown_percent
        self.max_consecutive_losses = max_consecutive_losses
        self.daily_loss_limit = daily_loss_limit
        
        # 状态
        self.metrics = RiskMetrics()
        self.circuit_breaker_state = CircuitBreakerState.NORMAL
        self.circuit_breaker_time: Optional[datetime] = None
        self.daily_start_time = datetime.now()
        self.daily_pnl = 0.0
        
        # 权益曲线
        self.equity_curve: List[tuple] = []
        self.initial_balance = 0.0
    
    def set_initial_balance(self, balance: float):
        """设置初始余额"""
        self.initial_balance = balance
        self.equity_curve.append((datetime.now(), balance))
    
    def update_pnl(self, pnl: float):
        """
        更新盈亏
        
        Args:
            pnl: 盈亏金额（正为盈利，负为亏损）
        """
        # 更新总盈亏
        self.metrics.total_pnl += pnl
        self.daily_pnl += pnl
        
        # 更新交易统计
        self.metrics.total_trades += 1
        if pnl > 0:
            self.metrics.winning_trades += 1
            self.metrics.consecutive_losses = 0
            self.metrics._total_win_amount += pnl  # 累加盈利金额
        else:
            self.metrics.losing_trades += 1
            self.metrics.consecutive_losses += 1
            if self.metrics.consecutive_losses > self.metrics.max_consecutive_losses:
                self.metrics.max_consecutive_losses = self.metrics.consecutive_losses
            self.metrics._total_loss_amount += abs(pnl)  # 累加亏损金额（取绝对值）
        
        # 更新平均盈亏
        self.metrics.avg_win = self.metrics._total_win_amount / self.metrics.winning_trades if self.metrics.winning_trades > 0 else 0
        self.metrics.avg_loss = self.metrics._total_loss_amount / self.metrics.losing_trades if self.metrics.losing_trades > 0 else 0
        
        # 计算当前余额
        current_balance = self.initial_balance + self.metrics.total_pnl
        
        # 计算最大回撤
        peak = max([b for _, b in self.equity_curve] + [current_balance])
        drawdown = (peak - current_balance) / peak * 100 if peak > 0 else 0
        self.metrics.max_drawdown = max(self.metrics.max_drawdown, drawdown)
        
        # 更新权益曲线
        self.equity_curve.append((datetime.now(), current_balance))
        
        # 检查是否触发熔断
        self._check_circuit_breaker()
    
    def _check_circuit_breaker(self):
        """检查是否触发熔断"""
        current_balance = self.initial_balance + self.metrics.total_pnl
        
        # 检查最大回撤
        if self.metrics.max_drawdown >= self.max_drawdown_percent:
            self._trigger_circuit_breaker(f"最大回撤达到 {self.metrics.max_drawdown:.2f}%")
            return
        
        # 检查连续亏损
        if self.metrics.consecutive_losses >= self.max_consecutive_losses:
            self._trigger_circuit_breaker(f"连续亏损 {self.metrics.consecutive_losses} 次")
            return
        
        # 检查每日亏损
        if self.daily_pnl <= -self.daily_loss_limit:
            self._trigger_circuit_breaker(f"每日亏损达到 {abs(self.daily_pnl):.2f} USDT")
            return
    
    def _trigger_circuit_breaker(self, reason: str):
        """触发熔断"""
        self.circuit_breaker_state = CircuitBreakerState.TRIGGERED
        self.circuit_breaker_time = datetime.now()
        print(f"⚠️ 熔断触发: {reason}")
    
    def reset_circuit_breaker(self):
        """重置熔断"""
        self.circuit_breaker_state = CircuitBreakerState.NORMAL
        self.circuit_breaker_time = None
        self.daily_pnl = 0.0
        self.daily_start_time = datetime.now()
    
    def is_allowed_to_trade(self) -> tuple[bool, str]:
        """
        检查是否允许交易
        
        Returns:
            (是否允许, 原因)
        """
        # 检查熔断状态
        if self.circuit_breaker_state == CircuitBreakerState.TRIGGERED:
            # 检查是否可以恢复（30分钟后）
            if self.circuit_breaker_time and (datetime.now() - self.circuit_breaker_time) > timedelta(minutes=30):
                self.reset_circuit_breaker()
            else:
                remaining = 30 - (datetime.now() - self.circuit_breaker_time).total_seconds() / 60 if self.circuit_breaker_time else 0
                return False, f"熔断状态，剩余 {max(0, remaining):.1f} 分钟"
        
        # 检查每日亏损
        if self.daily_pnl <= -self.daily_loss_limit:
            return False, f"每日亏损已达限制 {self.daily_loss_limit} USDT"
        
        # 检查连续亏损
        if self.metrics.consecutive_losses >= self.max_consecutive_losses:
            return False, f"连续亏损 {self.metrics.consecutive_losses} 次"
        
        return True, "允许交易"
    
    def get_metrics(self) -> dict:
        """获取风险指标"""
        current_balance = self.initial_balance + self.metrics.total_pnl
        win_rate = self.metrics.winning_trades / self.metrics.total_trades if self.metrics.total_trades > 0 else 0
        
        return {
            'total_trades': self.metrics.total_trades,
            'winning_trades': self.metrics.winning_trades,
            'losing_trades': self.metrics.losing_trades,
            'win_rate': win_rate,
            'total_pnl': self.metrics.total_pnl,
            'current_balance': current_balance,
            'max_drawdown': self.metrics.max_drawdown,
            'consecutive_losses': self.metrics.consecutive_losses,
            'max_consecutive_losses': self.metrics.max_consecutive_losses,
            'avg_win': self.metrics.avg_win,
            'avg_loss': self.metrics.avg_loss,
            'daily_pnl': self.daily_pnl,
            'circuit_breaker_state': self.circuit_breaker_state.value
        }


class ExecutionGate:
    """执行闸门 - 多重校验机制"""
    
    def __init__(self):
        """初始化执行闸门"""
        self.last_trade_time: Optional[datetime] = None
        self.min_trade_interval = timedelta(minutes=10)  # 最小交易间隔
        self.max_positions = 3  # 最大持仓数
        self.current_positions = 0  # 保留此字段以兼容旧代码
        
        # 使用持仓管理器
        from position_manager import PositionManager
        self.position_manager = PositionManager(max_positions=self.max_positions)
    
    def check(self, 
              signal,
              klines: List,
              min_stop_loss_distance: float) -> tuple[bool, str]:
        """
        执行前校验
        
        Args:
            signal: 交易信号
            klines: K线数据
            min_stop_loss_distance: 最小止损距离
            
        Returns:
            (是否通过, 原因)
        """
        # 检查交易频率
        if self.last_trade_time and (datetime.now() - self.last_trade_time) < self.min_trade_interval:
            remaining = (self.min_trade_interval - (datetime.now() - self.last_trade_time)).total_seconds()
            return False, f"交易间隔不足，还需 {remaining:.0f} 秒"
        
        # 检查持仓数量（使用持仓管理器）
        if self.position_manager.is_at_capacity():
            return False, f"持仓已达上限 {self.max_positions}"
        
        # 检查K线实体（避免在极小实体的K线交易）
        if klines:
            latest_kline = klines[-1]
            body_ratio = latest_kline.body_size / latest_kline.range_size
            if body_ratio < 0.3:
                return False, "K线实体过小"
        
        # 检查止损距离
        if hasattr(signal, 'stop_loss') and hasattr(signal, 'entry_price'):
            stop_distance = abs(signal.stop_loss - signal.entry_price) / signal.entry_price
            if stop_distance < min_stop_loss_distance:
                return False, f"止损距离过小 {stop_distance*100:.2f}% < {min_stop_loss_distance*100:.2f}%"
        
        return True, "通过所有校验"
    
    def record_trade(self):
        """记录交易（保留此方法以兼容旧代码）"""
        self.last_trade_time = datetime.now()
        # 注意：不再使用 current_positions，而是通过 add_position 管理
    
    def get_position_manager(self):
        """获取持仓管理器"""
        return self.position_manager
    
    def close_position(self, symbol: str, exit_price: float, reason: str = "手动平仓"):
        """
        平仓
        
        Args:
            symbol: 交易对
            exit_price: 平仓价
            reason: 平仓原因
        """
        from position_manager import PositionStatus
        position = self.position_manager.close_position(symbol, exit_price, reason)
        if position:
            # 更新盈亏到风险管理器
            return position.pnl
        return 0.0
    
    def get_position_count(self) -> int:
        """获取当前持仓数量"""
        return self.position_manager.get_position_count()
    
    def get_active_positions(self) -> List:
        """获取所有活跃持仓"""
        return self.position_manager.get_all_positions()
