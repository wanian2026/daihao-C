#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持仓管理器 - PositionManager
追踪和管理所有持仓，支持自动止盈止损
"""

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum


class PositionStatus(Enum):
    """持仓状态"""
    ACTIVE = "ACTIVE"           # 活跃中
    CLOSED = "CLOSED"           # 已平仓
    STOPPED = "STOPPED"         # 止损
    PROFIT_TAKEN = "PROFIT_TAKEN"  # 止盈


class PositionSide(Enum):
    """持仓方向"""
    LONG = "LONG"               # 多头
    SHORT = "SHORT"             # 空头


@dataclass
class Position:
    """持仓信息"""
    symbol: str                      # 交易对
    side: PositionSide               # 方向
    entry_price: float               # 入场价
    quantity: float                  # 数量（USDT）
    stop_loss: Optional[float] = None    # 止损价
    take_profit: Optional[float] = None  # 止盈价
    entry_time: datetime = field(default_factory=datetime.now)  # 入场时间
    status: PositionStatus = PositionStatus.ACTIVE  # 状态
    exit_price: Optional[float] = None     # 平仓价
    exit_time: Optional[datetime] = None   # 平仓时间
    pnl: float = 0.0                  # 盈亏（USDT）
    order_id: Optional[str] = None    # 订单ID
    
    def calculate_pnl(self, current_price: float) -> float:
        """
        计算当前盈亏
        
        Args:
            current_price: 当前价格
            
        Returns:
            盈亏（USDT）
        """
        if self.side == PositionSide.LONG:
            # 多头：(当前价 - 入场价) * 数量 / 入场价
            return (current_price - self.entry_price) * self.quantity / self.entry_price
        else:
            # 空头：(入场价 - 当前价) * 数量 / 入场价
            return (self.entry_price - current_price) * self.quantity / self.entry_price
    
    def should_stop_loss(self, current_price: float) -> bool:
        """检查是否应该止损"""
        if not self.stop_loss or self.status != PositionStatus.ACTIVE:
            return False
        
        if self.side == PositionSide.LONG:
            return current_price <= self.stop_loss
        else:
            return current_price >= self.stop_loss
    
    def should_take_profit(self, current_price: float) -> bool:
        """检查是否应该止盈"""
        if not self.take_profit or self.status != PositionStatus.ACTIVE:
            return False
        
        if self.side == PositionSide.LONG:
            return current_price >= self.take_profit
        else:
            return current_price <= self.take_profit


class PositionManager:
    """持仓管理器"""
    
    def __init__(self, max_positions: int = 3):
        """
        初始化持仓管理器
        
        Args:
            max_positions: 最大持仓数
        """
        self.max_positions = max_positions
        self.positions: Dict[str, Position] = {}  # symbol -> Position
        self._position_count = 0  # 活跃持仓计数
        self._lock = threading.Lock()  # 线程锁，保护并发访问
    
    def add_position(self, position: Position) -> bool:
        """
        添加持仓
        
        Args:
            position: 持仓信息
            
        Returns:
            是否添加成功
        """
        with self._lock:
            if self._position_count >= self.max_positions:
                return False
            
            # 检查是否已有该交易对的持仓
            if position.symbol in self.positions:
                return False
            
            self.positions[position.symbol] = position
            self._position_count += 1
            print(f"✓ 开仓成功: {position.symbol} {position.side.value} @ {position.entry_price:.2f}")
            return True
    
    def close_position(self, symbol: str, exit_price: float, reason: str = "手动平仓") -> Optional[Position]:
        """
        平仓

        Args:
            symbol: 交易对
            exit_price: 平仓价
            reason: 平仓原因

        Returns:
            平仓的持仓信息或None
        """
        with self._lock:
            if symbol not in self.positions:
                return None

            position = self.positions[symbol]

            # 计算盈亏
            position.exit_price = exit_price
            position.exit_time = datetime.now()
            position.pnl = position.calculate_pnl(exit_price)

            # 更新状态
            if position.pnl > 0:
                position.status = PositionStatus.PROFIT_TAKEN
            else:
                position.status = PositionStatus.STOPPED

            print(f"✓ 平仓完成: {symbol} @ {exit_price:.2f} | PnL: {position.pnl:+.2f} USDT | {reason}")

            # 从活跃持仓中移除（保留记录）
            del self.positions[symbol]
            self._position_count = max(0, self._position_count - 1)

            return position
    
    def close_position_with_retry(self, symbol: str, exit_price: float, reason: str = "手动平仓", max_retries: int = 3) -> Optional[Position]:
        """
        带重试的平仓（用于API调用失败的情况）

        Args:
            symbol: 交易对
            exit_price: 平仓价
            reason: 平仓原因
            max_retries: 最大重试次数

        Returns:
            平仓的持仓信息或None
        """
        for attempt in range(max_retries):
            result = self.close_position(symbol, exit_price, reason)
            if result is not None:
                return result
            if attempt < max_retries - 1:
                print(f"⚠️ 平仓 {symbol} 失败，重试中... ({attempt + 1}/{max_retries})")
                time.sleep(2)  # 等待2秒后重试
        return None
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """获取指定持仓"""
        with self._lock:
            return self.positions.get(symbol)
    
    def get_all_positions(self) -> List[Position]:
        """获取所有活跃持仓"""
        with self._lock:
            return list(self.positions.values())
    
    def get_position_count(self) -> int:
        """获取活跃持仓数量"""
        with self._lock:
            return self._position_count
    
    def is_at_capacity(self) -> bool:
        """是否已达持仓上限"""
        with self._lock:
            return self._position_count >= self.max_positions
    
    def sync_positions(self, trading_client):
        """
        同步持仓状态，检查并执行止盈止损
        
        Args:
            trading_client: 交易客户端
        """
        with self._lock:
            if self._position_count == 0:
                return
        
        try:
            # 获取所有活跃持仓
            positions = self.get_all_positions()
            
            for position in positions:
                try:
                    # 获取当前价格
                    from binance_api_client import BinanceAPIClient
                    api_client = BinanceAPIClient()
                    ticker = api_client._make_request('/fapi/v1/ticker/price', {'symbol': position.symbol})
                    
                    if isinstance(ticker, dict) and ticker.get('error'):
                        continue
                    
                    current_price = float(ticker.get('price', 0))
                    if current_price == 0:
                        continue
                    
                    # 检查是否应该止盈
                    if position.should_take_profit(current_price):
                        print(f"🎯 触发止盈: {position.symbol}")
                        # 实盘模式下平仓
                        if hasattr(trading_client, 'place_market_order'):
                            side = 'SELL' if position.side == PositionSide.LONG else 'BUY'
                            quantity = position.quantity / position.entry_price
                            
                            result = trading_client.place_market_order(
                                symbol=position.symbol,
                                side=side,
                                quantity=quantity
                            )
                            
                            if not result.get('error'):
                                self.close_position(
                                    position.symbol,
                                    current_price,
                                    reason="止盈"
                                )
                    
                    # 检查是否应该止损
                    elif position.should_stop_loss(current_price):
                        print(f"🛑 触发止损: {position.symbol}")
                        # 实盘模式下平仓
                        if hasattr(trading_client, 'place_market_order'):
                            side = 'SELL' if position.side == PositionSide.LONG else 'BUY'
                            quantity = position.quantity / position.entry_price
                            
                            result = trading_client.place_market_order(
                                symbol=position.symbol,
                                side=side,
                                quantity=quantity
                            )
                            
                            if not result.get('error'):
                                self.close_position(
                                    position.symbol,
                                    current_price,
                                    reason="止损"
                                )
                    
                except Exception as e:
                    print(f"检查持仓 {position.symbol} 失败: {e}")
                    continue
        
        except Exception as e:
            print(f"同步持仓失败: {e}")
    
    def check_positions(self, current_prices: Dict[str, float]) -> List[tuple]:
        """
        检查所有持仓，识别需要平仓的

        Args:
            current_prices: 当前价格字典 {symbol: price}

        Returns:
            需要平仓的列表 [(symbol, reason), ...]
        """
        to_close = []

        # 先复制持仓列表，释放锁后再检查
        with self._lock:
            positions_snapshot = list(self.positions.items())

        for symbol, position in positions_snapshot:
            current_price = current_prices.get(symbol)
            if not current_price:
                continue

            # 检查止损
            if position.should_stop_loss(current_price):
                to_close.append((symbol, "止损"))

            # 检查止盈
            elif position.should_take_profit(current_price):
                to_close.append((symbol, "止盈"))

        return to_close
    
    def get_total_pnl(self, current_prices: Dict[str, float]) -> float:
        """
        获取总盈亏（包括已平仓和未平仓的浮动盈亏）

        Args:
            current_prices: 当前价格字典 {symbol: price}

        Returns:
            总盈亏（USDT）
        """
        total = 0.0
        # 计算活跃持仓的浮动盈亏
        for symbol, position in self.positions.items():
            current_price = current_prices.get(symbol)
            if current_price:
                total += position.calculate_pnl(current_price)
        return total
    
    def clear_all_positions(self):
        """清空所有持仓记录（用于测试）"""
        with self._lock:
            self.positions.clear()
            self._position_count = 0

    def get_position_summary(self) -> dict:
        """获取持仓摘要"""
        with self._lock:
            return {
                'total_positions': self._position_count,
                'max_positions': self.max_positions,
                'symbols': list(self.positions.keys()),
                'long_count': sum(1 for p in self.positions.values() if p.side == PositionSide.LONG),
                'short_count': sum(1 for p in self.positions.values() if p.side == PositionSide.SHORT)
            }


# 测试代码
if __name__ == "__main__":
    print("测试持仓管理器...")
    
    manager = PositionManager(max_positions=3)
    
    # 测试开仓
    pos1 = Position(
        symbol="ETHUSDT",
        side=PositionSide.LONG,
        entry_price=3000.0,
        quantity=100.0,
        stop_loss=2950.0,
        take_profit=3100.0
    )
    
    assert manager.add_position(pos1), "添加持仓失败"
    assert manager.get_position_count() == 1, "持仓数量错误"
    print("✓ 开仓测试通过")
    
    # 测试盈亏计算
    pnl = pos1.calculate_pnl(3050.0)
    print(f"盈亏计算: {pnl:.2f} USDT")
    assert abs(pnl - 1.67) < 0.1, "盈亏计算错误"
    print("✓ 盈亏计算测试通过")
    
    # 测试止损检查
    assert not pos1.should_stop_loss(3000.0), "不应触发止损"
    assert pos1.should_stop_loss(2940.0), "应该触发止损"
    assert pos1.should_take_profit(3110.0), "应该触发止盈"
    print("✓ 止损止盈检查测试通过")
    
    # 测试平仓
    closed = manager.close_position("ETHUSDT", 3100.0, "止盈")
    assert closed is not None, "平仓失败"
    assert closed.status == PositionStatus.PROFIT_TAKEN, "状态错误"
    assert closed.pnl > 0, "应该盈利"
    assert manager.get_position_count() == 0, "持仓数量应为0"
    print("✓ 平仓测试通过")
    
    # 测试容量限制
    manager2 = PositionManager(max_positions=2)
    pos2 = Position(symbol="BTCUSDT", side=PositionSide.LONG, entry_price=50000.0, quantity=100.0)
    pos3 = Position(symbol="ETHUSDT", side=PositionSide.LONG, entry_price=3000.0, quantity=100.0)
    
    assert manager2.add_position(pos2), "添加失败"
    assert manager2.add_position(pos3), "添加失败"
    assert not manager2.is_at_capacity() == False, "应该已满"
    
    pos4 = Position(symbol="BNBUSDT", side=PositionSide.LONG, entry_price=400.0, quantity=100.0)
    assert not manager2.add_position(pos4), "不应该能添加（已达上限）"
    print("✓ 容量限制测试通过")
    
    print("\n所有测试通过！")
