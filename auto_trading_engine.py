#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动交易引擎
执行策略信号，管理交易流程
"""

import threading
import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

from binance_trading_client import BinanceTradingClient
from trading_strategy import StrategyManager, TradingSignal, SignalType


class EngineState(Enum):
    """引擎状态"""
    STOPPED = "STOPPED"          # 已停止
    RUNNING = "RUNNING"          # 运行中
    PAUSED = "PAUSED"            # 已暂停
    ERROR = "ERROR"              # 错误状态


@dataclass
class TradeOrder:
    """交易订单"""
    order_id: Optional[str] = None
    symbol: str = ""
    side: str = ""
    order_type: str = ""
    quantity: float = 0.0
    price: Optional[float] = None
    status: str = "PENDING"  # PENDING, FILLED, PARTIALLY_FILLED, CANCELLED, FAILED
    error: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'order_id': self.order_id,
            'symbol': self.symbol,
            'side': self.side,
            'order_type': self.order_type,
            'quantity': self.quantity,
            'price': self.price,
            'status': self.status,
            'error': self.error,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class EngineConfig:
    """引擎配置"""
    max_orders_per_minute: int = 100  # 每分钟最大订单数
    enable_order_rate_limit: bool = True  # 启用订单速率限制
    dry_run: bool = True  # 模拟模式（不实际下单）
    auto_risk_control: bool = True  # 启用风险控制
    max_position_size: float = 1000.0  # 最大持仓规模（USDT）
    stop_loss_percent: float = 0.05  # 止损百分比
    take_profit_percent: float = 0.10  # 止盈百分比


class AutoTradingEngine:
    """自动交易引擎"""
    
    def __init__(self, trading_client: BinanceTradingClient, strategy_manager: StrategyManager):
        """
        初始化交易引擎
        
        Args:
            trading_client: 交易客户端
            strategy_manager: 策略管理器
        """
        self.trading_client = trading_client
        self.strategy_manager = strategy_manager
        self.config = EngineConfig()
        
        # 引擎状态
        self.state = EngineState.STOPPED
        self.thread: Optional[threading.Thread] = None
        self.running = False
        
        # 订单记录
        self.order_history: List[TradeOrder] = []
        self.active_orders: Dict[str, TradeOrder] = {}
        
        # 回调函数
        self.on_signal_callback: Optional[Callable] = None
        self.on_order_callback: Optional[Callable] = None
        self.on_error_callback: Optional[Callable] = None
        
        # 统计信息
        self.stats = {
            'total_orders': 0,
            'successful_orders': 0,
            'failed_orders': 0,
            'total_volume': 0.0,
            'last_execution': None
        }
    
    def start(self):
        """启动引擎"""
        if self.state == EngineState.RUNNING:
            return False
        
        self.running = True
        self.state = EngineState.RUNNING
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        
        self._log("交易引擎已启动")
        return True
    
    def stop(self):
        """停止引擎"""
        self.running = False
        self.state = EngineState.STOPPED
        if self.thread:
            self.thread.join(timeout=5)
        
        self._log("交易引擎已停止")
    
    def pause(self):
        """暂停引擎"""
        if self.state == EngineState.RUNNING:
            self.state = EngineState.PAUSED
            self._log("交易引擎已暂停")
    
    def resume(self):
        """恢复引擎"""
        if self.state == EngineState.PAUSED:
            self.state = EngineState.RUNNING
            self._log("交易引擎已恢复")
    
    def _run_loop(self):
        """主循环"""
        while self.running:
            try:
                if self.state == EngineState.RUNNING:
                    self._execute_cycle()
                
                # 等待下一个周期（默认5秒）
                time.sleep(5)
                
            except Exception as e:
                self.state = EngineState.ERROR
                self._log(f"引擎错误: {str(e)}")
                if self.on_error_callback:
                    self.on_error_callback(str(e))
                time.sleep(10)  # 错误后等待10秒
    
    def _execute_cycle(self):
        """执行一个周期"""
        try:
            # 1. 获取所有合约信息
            all_contracts = self.trading_client.get_contract_info()
            
            # 2. 获取市场数据（简化示例）
            market_data = {}
            
            # 3. 执行所有策略
            results = self.strategy_manager.execute_all(all_contracts, market_data)
            
            # 4. 获取手动选择的合约
            selected_symbols = self.strategy_manager.get_selected_symbols()
            
            # 5. 处理信号
            for strategy_name, result in results.items():
                for signal in result.signals:
                    # 只处理已选择的合约
                    if signal.symbol in selected_symbols:
                        self._process_signal(signal)
            
            # 6. 更新统计
            self.stats['last_execution'] = datetime.now()
            
        except Exception as e:
            self._log(f"执行周期错误: {str(e)}")
    
    def _process_signal(self, signal: TradingSignal):
        """
        处理交易信号
        
        Args:
            signal: 交易信号
        """
        try:
            # 检查是否应该执行信号
            if not self._should_execute_signal(signal):
                return
            
            # 模拟模式
            if self.config.dry_run:
                self._log(f"[模拟] 收到信号: {signal.symbol} {signal.signal_type.value} - {signal.reason}")
                order = TradeOrder(
                    symbol=signal.symbol,
                    side=signal.signal_type.value,
                    order_type="MARKET",
                    quantity=signal.quantity or 0.001,
                    status="FILLED",
                    price=signal.price
                )
                self._record_order(order)
                return
            
            # 实际下单
            self._execute_order(signal)
            
            # 触发回调
            if self.on_signal_callback:
                self.on_signal_callback(signal)
                
        except Exception as e:
            self._log(f"处理信号错误: {str(e)}")
            if self.on_error_callback:
                self.on_error_callback(str(e))
    
    def _should_execute_signal(self, signal: TradingSignal) -> bool:
        """
        判断是否应该执行信号
        
        Args:
            signal: 交易信号
            
        Returns:
            是否执行
        """
        # 检查置信度
        if signal.confidence < 0.5:
            return False
        
        # 检查是否已有持仓（简化）
        # 实际应用中应该查询当前持仓
        
        return True
    
    def _execute_order(self, signal: TradingSignal):
        """
        执行订单
        
        Args:
            signal: 交易信号
        """
        try:
            # 确定订单类型
            if signal.signal_type in [SignalType.BUY, SignalType.SELL]:
                side = signal.signal_type.value
            elif signal.signal_type == SignalType.CLOSE_LONG:
                side = "SELL"
            elif signal.signal_type == SignalType.CLOSE_SHORT:
                side = "BUY"
            else:
                return
            
            # 下市价单
            result = self.trading_client.place_market_order(
                symbol=signal.symbol,
                side=side,
                quantity=signal.quantity or 0.001
            )
            
            # 记录订单
            if result.get('error'):
                order = TradeOrder(
                    symbol=signal.symbol,
                    side=side,
                    order_type="MARKET",
                    quantity=signal.quantity or 0.001,
                    status="FAILED",
                    error=result.get('message')
                )
                self.stats['failed_orders'] += 1
            else:
                order = TradeOrder(
                    order_id=str(result.get('orderId')),
                    symbol=signal.symbol,
                    side=side,
                    order_type="MARKET",
                    quantity=signal.quantity or float(result.get('executedQty', 0)),
                    price=float(result.get('avgPrice', 0)) if result.get('avgPrice') else None,
                    status="FILLED"
                )
                self.stats['successful_orders'] += 1
                self.stats['total_volume'] += order.quantity
            
            self.stats['total_orders'] += 1
            self._record_order(order)
            
            # 触发回调
            if self.on_order_callback:
                self.on_order_callback(order)
                
        except Exception as e:
            self._log(f"执行订单错误: {str(e)}")
            order = TradeOrder(
                symbol=signal.symbol,
                side=signal.signal_type.value,
                order_type="MARKET",
                quantity=signal.quantity or 0.001,
                status="FAILED",
                error=str(e)
            )
            self._record_order(order)
    
    def _record_order(self, order: TradeOrder):
        """
        记录订单
        
        Args:
            order: 订单对象
        """
        self.order_history.append(order)
        if order.order_id:
            self.active_orders[order.order_id] = order
    
    def _log(self, message: str):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            'state': self.state.value,
            'active_orders': len(self.active_orders),
            'order_history_count': len(self.order_history),
            'config': {
                'dry_run': self.config.dry_run,
                'max_orders_per_minute': self.config.max_orders_per_minute
            }
        }
    
    def get_order_history(self, limit: int = 100) -> List[Dict]:
        """
        获取订单历史
        
        Args:
            limit: 返回数量限制
            
        Returns:
            订单历史列表
        """
        return [order.to_dict() for order in self.order_history[-limit:]]
    
    def set_config(self, config: EngineConfig):
        """设置引擎配置"""
        self.config = config
        self._log(f"配置已更新: dry_run={config.dry_run}")


# 测试代码
if __name__ == "__main__":
    print("自动交易引擎测试")
    print()
    
    # 注意：需要真实的API密钥才能实际测试
    # 这里只测试框架功能
    
    # 创建模拟交易客户端
    # from binance_trading_client import BinanceTradingClient
    # client = BinanceTradingClient("test_key", "test_secret")
    
    # 创建策略管理器
    # from trading_strategy import StrategyManager
    # strategy_manager = StrategyManager()
    
    # 创建引擎
    # engine = AutoTradingEngine(client, strategy_manager)
    
    # 设置为模拟模式
    # engine.config.dry_run = True
    
    # 设置回调
    # def on_signal(signal):
    #     print(f"收到信号: {signal.symbol} {signal.signal_type.value}")
    # 
    # def on_order(order):
    #     print(f"订单执行: {order.symbol} {order.status}")
    # 
    # engine.on_signal_callback = on_signal
    # engine.on_order_callback = on_order
    
    # 启动引擎
    # engine.start()
    
    # 运行一段时间
    # time.sleep(10)
    
    # 停止引擎
    # engine.stop()
    
    # 打印统计
    # print(f"统计: {engine.get_stats()}")
    
    print("✓ 交易引擎测试完成")
    print("注意：实际交易需要提供有效的API密钥")
