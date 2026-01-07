#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETH 5m 假突破策略 - 完整系统
整合所有模块，实现事件驱动 + 永久在线循环
"""

import time
import threading
from typing import Optional, Callable
from datetime import datetime, timedelta
from enum import Enum

from binance_trading_client import BinanceTradingClient
from data_fetcher import DataFetcher
from market_state_engine import MarketStateEngine, MarketState
from worth_trading_filter import WorthTradingFilter
from fakeout_strategy import FakeoutStrategy, FakeoutSignal
from risk_manager import RiskManager, ExecutionGate


class SystemState(Enum):
    """系统状态"""
    INITIALIZING = "INITIALIZING"     # 初始化中
    RUNNING = "RUNNING"               # 运行中
    PAUSED = "PAUSED"                 # 已暂停
    ERROR = "ERROR"                  # 错误状态
    STOPPED = "STOPPED"               # 已停止


class ETHFakeoutStrategySystem:
    """ETH 5m假突破策略系统"""
    
    def __init__(self, trading_client: BinanceTradingClient):
        """
        初始化策略系统
        
        Args:
            trading_client: 交易客户端
        """
        self.trading_client = trading_client
        self.symbol = "ETHUSDT"
        self.interval = "5m"
        
        # 创建各模块
        self.data_fetcher = DataFetcher(trading_client)
        self.market_state_engine = MarketStateEngine(self.data_fetcher, self.symbol, self.interval)
        self.worth_trading_filter = WorthTradingFilter(self.data_fetcher)
        self.fakeout_strategy = FakeoutStrategy(self.data_fetcher, self.symbol, self.interval)
        self.risk_manager = RiskManager()
        self.execution_gate = ExecutionGate()
        
        # 系统状态
        self.state = SystemState.INITIALIZING
        self.thread: Optional[threading.Thread] = None
        self.running = False
        
        # 回调函数
        self.on_signal: Optional[Callable] = None
        self.on_order: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        self.on_status_update: Optional[Callable] = None
        
        # 统计信息
        self.stats = {
            'total_loops': 0,
            'signals_found': 0,
            'trades_executed': 0,
            'skips': {
                'market_sleep': 0,
                'not_worth': 0,
                'execution_gate': 0,
                'risk_manager': 0
            }
        }
        
        # 初始化风险管理器
        account_info = self.trading_client.get_account_info()
        if not account_info.get('error'):
            balance = float(account_info.get('totalWalletBalance', 0))
            self.risk_manager.set_initial_balance(balance)
    
    def start(self):
        """启动系统"""
        if self.state == SystemState.RUNNING:
            return False
        
        self.running = True
        self.state = SystemState.RUNNING
        self.thread = threading.Thread(target=self._main_loop, daemon=True)
        self.thread.start()
        
        self._log("ETH 5m假突破策略系统已启动")
        return True
    
    def stop(self):
        """停止系统"""
        self.running = False
        self.state = SystemState.STOPPED
        if self.thread:
            self.thread.join(timeout=10)
        self._log("系统已停止")
    
    def pause(self):
        """暂停系统"""
        if self.state == SystemState.RUNNING:
            self.state = SystemState.PAUSED
            self._log("系统已暂停")
    
    def resume(self):
        """恢复系统"""
        if self.state == SystemState.PAUSED:
            self.state = SystemState.RUNNING
            self._log("系统已恢复")
    
    def _main_loop(self):
        """主循环"""
        loop_count = 0
        
        while self.running:
            try:
                # 暂停状态
                if self.state == SystemState.PAUSED:
                    time.sleep(5)
                    continue
                
                loop_count += 1
                self.stats['total_loops'] = loop_count
                
                # 每一轮循环完成一次完整的"是否允许交易 → 是否有信号 → 是否执行"的判断
                skip_reason = self._execute_one_cycle()
                
                if skip_reason:
                    self.stats['skips'][skip_reason] = self.stats['skips'].get(skip_reason, 0) + 1
                
                # 短暂休眠
                time.sleep(10)  # 每10秒检查一次
                
            except Exception as e:
                self.state = SystemState.ERROR
                self._log(f"主循环错误: {str(e)}")
                if self.on_error:
                    self.on_error(str(e))
                time.sleep(30)  # 错误后等待30秒
    
    def _execute_one_cycle(self) -> Optional[str]:
        """
        执行一个完整周期
        
        Returns:
            跳过原因，None表示执行了交易
        """
        # 1. 系统健康检查
        if not self._health_check():
            return "health_check"
        
        # 2. 全局熔断检查
        allowed, reason = self.risk_manager.is_allowed_to_trade()
        if not allowed:
            return "risk_manager"
        
        # 3. 市场状态判断（非SLEEP）
        market_state_info = self.market_state_engine.analyze()
        if market_state_info.state == MarketState.SLEEP:
            self._log(f"市场状态: {market_state_info.state.value} - 跳过交易")
            return "market_sleep"
        
        # 4. 交易价值判断（Worth-Trading）
        worth_trading = self.worth_trading_filter.check(self.symbol)
        if not worth_trading.is_worth_trading:
            self._log(f"不值得交易: {worth_trading.reasons}")
            return "not_worth"
        
        # 5. 结构位置过滤 + 假突破识别
        fakeout_signals = self.fakeout_strategy.analyze()
        if not fakeout_signals:
            return None  # 没有信号，正常跳过
        
        self.stats['signals_found'] += len(fakeout_signals)
        
        # 6. 选择最佳信号（置信度最高的）
        best_signal = max(fakeout_signals, key=lambda s: s.confidence)
        
        # 7. 执行条件校验
        klines = self.data_fetcher.get_klines(self.symbol, self.interval, limit=20)
        allowed, reason = self.execution_gate.check(
            best_signal,
            klines,
            min_stop_loss_distance=0.01
        )
        
        if not allowed:
            self._log(f"执行闸门拒绝: {reason}")
            return "execution_gate"
        
        # 8. 下单执行
        self._execute_trade(best_signal)
        
        return None
    
    def _health_check(self) -> bool:
        """
        系统健康检查
        
        Returns:
            是否健康
        """
        # 检查数据新鲜度
        freshness = self.data_fetcher.get_data_freshness(self.symbol)
        if freshness > 60:  # 数据延迟超过60秒
            self._log(f"数据不新鲜: 延迟 {freshness} 秒")
            return False
        
        # 检查连接状态
        if not self.trading_client.ping():
            self._log("API连接失败")
            return False
        
        return True
    
    def _execute_trade(self, signal: FakeoutSignal):
        """
        执行交易
        
        Args:
            signal: 假突破信号
        """
        try:
            # 计算仓位大小
            account_balance = self.risk_manager.initial_balance + self.risk_manager.metrics.total_pnl
            position_size = self.worth_trading_filter.calculate_position_size(
                self.symbol,
                account_balance,
                risk_per_trade=0.02
            )
            
            if position_size <= 0:
                self._log("仓位大小计算为0，跳过交易")
                return
            
            # 下市价单
            side = "BUY" if signal.signal_type.value == "BUY" else "SELL"
            
            self._log(f"执行交易: {side} {self.symbol}")
            self._log(f"  入场价: {signal.entry_price:.2f}")
            self._log(f"  止损: {signal.stop_loss:.2f}")
            self._log(f"  止盈: {signal.take_profit:.2f}")
            self._log(f"  仓位: {position_size:.2f} USDT")
            
            # 实际下单
            result = self.trading_client.place_market_order(
                symbol=self.symbol,
                side=side,
                quantity=position_size / signal.entry_price
            )
            
            if result.get('error'):
                self._log(f"下单失败: {result.get('message')}")
                return
            
            # 记录交易
            self.execution_gate.record_trade()
            self.stats['trades_executed'] += 1
            
            # 触发回调
            if self.on_order:
                self.on_order({
                    'signal': signal,
                    'order_result': result,
                    'position_size': position_size
                })
            
            self._log("订单已提交")
            
        except Exception as e:
            self._log(f"执行交易错误: {str(e)}")
            if self.on_error:
                self.on_error(str(e))
    
    def _log(self, message: str):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        # 触发状态更新回调
        if self.on_status_update:
            self.on_status_update({
                'timestamp': datetime.now(),
                'message': message,
                'state': self.state.value,
                'stats': self.stats,
                'risk_metrics': self.risk_manager.get_metrics()
            })
    
    def get_system_status(self) -> dict:
        """获取系统状态"""
        return {
            'state': self.state.value,
            'symbol': self.symbol,
            'interval': self.interval,
            'stats': self.stats,
            'risk_metrics': self.risk_manager.get_metrics(),
            'market_state': self.market_state_engine.get_state_info()
        }


# 测试代码
if __name__ == "__main__":
    print("ETH 5m假突破策略系统测试")
    print("\n注意：需要真实的API密钥才能运行")
    print("建议先在模拟模式下测试\n")
    
    # 示例：创建策略系统
    # from binance_trading_client import BinanceTradingClient
    
    # # 创建交易客户端（需要真实API密钥）
    # client = BinanceTradingClient("your_api_key", "your_api_secret")
    
    # # 创建策略系统
    # system = ETHFakeoutStrategySystem(client)
    
    # # 设置回调
    # def on_signal(signal):
    #     print(f"收到信号: {signal.signal_type.value}")
    # 
    # def on_order(order_info):
    #     print(f"订单已执行: {order_info}")
    # 
    # def on_error(error):
    #     print(f"错误: {error}")
    # 
    # system.on_signal = on_signal
    # system.on_order = on_order
    # system.on_error = on_error
    # 
    # # 启动系统
    # system.start()
    # 
    # # 运行一段时间
    # try:
    #     while True:
    #         status = system.get_system_status()
    #         print(f"\r系统状态: {status['state']} | 循环次数: {status['stats']['total_loops']} | "
    #               f"信号数: {status['stats']['signals_found']} | 交易数: {status['stats']['trades_executed']}", end="")
    #         time.sleep(10)
    # except KeyboardInterrupt:
    #     print("\n\n停止系统...")
    #     system.stop()
    #     print("系统已停止")
    
    print("\n策略系统框架已就绪，可以集成到GUI中运行")
