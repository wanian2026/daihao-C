#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多标的假突破策略 - 完整系统
整合所有模块，支持多合约标的筛选与自动交易
"""

import time
import threading
from typing import Optional, Callable, List, Dict
from datetime import datetime, timedelta
from enum import Enum

from binance_trading_client import BinanceTradingClient
from binance_api_client import BinanceAPIClient
from data_fetcher import DataFetcher
from market_state_engine import MarketStateEngine, MarketState
from worth_trading_filter import WorthTradingFilter
from fakeout_strategy import FakeoutStrategy, FakeoutSignal
from risk_manager import RiskManager, ExecutionGate
from symbol_selector import SymbolSelector, SelectionMode


class SystemState(Enum):
    """系统状态"""
    INITIALIZING = "INITIALIZING"     # 初始化中
    RUNNING = "RUNNING"               # 运行中
    PAUSED = "PAUSED"                 # 已暂停
    ERROR = "ERROR"                  # 错误状态
    STOPPED = "STOPPED"               # 已停止


class MultiSymbolFakeoutSystem:
    """多标的假突破策略系统"""
    
    def __init__(self, trading_client: BinanceTradingClient):
        """
        初始化策略系统
        
        Args:
            trading_client: 交易客户端
        """
        self.trading_client = trading_client
        self.interval = "5m"
        
        # 创建各模块
        self.api_client = BinanceAPIClient()
        self.data_fetcher = DataFetcher(self.api_client)
        self.symbol_selector = SymbolSelector(self.api_client)
        self.market_state_engine = MarketStateEngine(self.data_fetcher, "ETHUSDT", self.interval)
        self.worth_trading_filter = WorthTradingFilter(self.data_fetcher)
        self.fakeout_strategy = FakeoutStrategy(self.data_fetcher, "ETHUSDT", self.interval)
        self.risk_manager = RiskManager()
        self.execution_gate = ExecutionGate()
        
        # 多标的状态
        self.selected_symbols: List[str] = []
        self.symbol_market_states: Dict[str, dict] = {}
        self.symbol_signals: Dict[str, List[FakeoutSignal]] = {}
        
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
            'symbols_analyzed': 0,
            'skips': {
                'market_sleep': 0,
                'not_worth': 0,
                'execution_gate': 0,
                'risk_manager': 0,
                'no_symbols': 0
            }
        }
        
        # 初始化风险管理器
        account_info = self.trading_client.get_account_info()
        if not account_info.get('error'):
            balance = float(account_info.get('totalWalletBalance', 0))
            self.risk_manager.set_initial_balance(balance)
        
        # 初始化合约选择器
        self._initialize_symbols()
        
        # 启动持仓同步任务
        threading.Thread(target=self._sync_positions_loop, daemon=True).start()
    
    def _initialize_symbols(self):
        """初始化合约选择器"""
        try:
            self._log("正在获取USDT永续合约列表...")
            self.symbol_selector.update_symbol_list(force_update=True)
            self.selected_symbols = self.symbol_selector.get_selected_symbols()
            self._log(f"已选择 {len(self.selected_symbols)} 个合约进行监控")
            for symbol in self.selected_symbols:
                self._log(f"  - {symbol}")
        except Exception as e:
            self._log(f"初始化合约列表失败: {str(e)}")
            self.selected_symbols = ['ETHUSDT']  # 默认使用ETH
    
    def update_selected_symbols(self, symbols: List[str]):
        """
        更新选中的标的
        
        Args:
            symbols: 标的列表
        """
        self.selected_symbols = symbols
        self._log(f"已更新标的列表: {len(symbols)} 个合约")
    
    def set_selection_mode(self, mode: SelectionMode):
        """
        设置选择模式
        
        Args:
            mode: 选择模式
        """
        self.symbol_selector.set_selection_mode(mode)
        self.selected_symbols = self.symbol_selector.get_selected_symbols()
        self._log(f"选择模式: {mode.value}, 已选择 {len(self.selected_symbols)} 个合约")
    
    def start(self):
        """启动系统"""
        if self.state == SystemState.RUNNING:
            return False
        
        self.running = True
        self.state = SystemState.RUNNING
        self.thread = threading.Thread(target=self._main_loop, daemon=True)
        self.thread.start()
        
        self._log("多标假突破策略系统已启动")
        self._log(f"监控标的: {', '.join(self.selected_symbols)}")
        self._log("开始主循环...")
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
                
                # 每一轮循环完成一次完整的多标的分析
                skip_reason = self._execute_multi_symbol_cycle()
                
                if skip_reason:
                    self.stats['skips'][skip_reason] = self.stats['skips'].get(skip_reason, 0) + 1
                    # 添加跳过原因日志
                    self._log(f"循环 #{loop_count} 跳过: {skip_reason}")
                else:
                    self._log(f"循环 #{loop_count} 执行交易周期")
                
                # 短暂休眠
                time.sleep(10)  # 每10秒检查一次
                
            except Exception as e:
                self.state = SystemState.ERROR
                self._log(f"主循环错误: {str(e)}")
                import traceback
                self._log(f"错误堆栈: {traceback.format_exc()}")
                if self.on_error:
                    self.on_error(str(e))
                time.sleep(30)  # 错误后等待30秒
    
    def _execute_multi_symbol_cycle(self) -> Optional[str]:
        """
        执行多标的完整周期
        
        Returns:
            跳过原因，None表示执行了交易
        """
        # 1. 系统健康检查
        if not self._health_check():
            return "health_check"
        
        # 2. 全局熔断检查
        allowed, reason = self.risk_manager.is_allowed_to_trade()
        if not allowed:
            self._log(f"熔断检查拒绝: {reason}")
            return "risk_manager"
        
        # 3. 检查是否有选中的标的
        if not self.selected_symbols:
            self._log("没有选中的标的")
            return "no_symbols"
        
        # 4. 批量分析所有选中标的
        self._log(f"开始分析 {len(self.selected_symbols)} 个标的...")
        best_result = self._analyze_all_symbols()
        
        if not best_result:
            self._log("未找到符合条件的标的")
            return None  # 没有找到符合条件的标的
        
        best_symbol, best_signal = best_result
        
        self._log(f"最佳信号: {best_symbol} - 置信度 {best_signal.confidence:.2f}")
        
        # 5. 执行条件校验
        klines = self.data_fetcher.get_klines(best_symbol, self.interval, limit=20)
        allowed, reason = self.execution_gate.check(
            best_signal,
            klines,
            min_stop_loss_distance=0.01
        )
        
        if not allowed:
            self._log(f"执行闸门拒绝: {reason}")
            return "execution_gate"

        
        # 6. 下单执行
        self._execute_trade(best_symbol, best_signal)
        
        return None
    
    def _analyze_all_symbols(self) -> Optional[tuple]:
        """
        分析所有选中的标的
        
        Returns:
            (symbol, signal) 或 None
        """
        all_signals = {}
        market_states = {}
        
        self.stats['symbols_analyzed'] = len(self.selected_symbols)
        
        # 批量获取市场指标
        market_metrics = self.data_fetcher.get_market_metrics_batch(
            self.selected_symbols,
            self.interval,
            atr_period=14,
            volume_period=20
        )
        
        # 更新合约选择器的指标
        self.symbol_selector.update_market_metrics(market_metrics)
        
        # 批量分析市场状态
        state_infos = self.market_state_engine.analyze_batch(self.selected_symbols)
        
        for symbol in self.selected_symbols:
            state_info = state_infos.get(symbol)
            if not state_info:
                continue
            
            market_states[symbol] = {
                'state': state_info.state.value,
                'score': state_info.score,
                'atr_ratio': state_info.atr_ratio,
                'volume_ratio': state_info.volume_ratio
            }
            
            # 1. 市场状态判断（非SLEEP）
            if state_info.state == MarketState.SLEEP:
                self.stats['skips']['market_sleep'] += 1
                continue
            
            # 2. 交易价值判断
            worth_trading = self.worth_trading_filter.check(symbol)
            if not worth_trading.is_worth_trading:
                self.stats['skips']['not_worth'] += 1
                continue
            
            # 3. 假突破识别
            temp_strategy = FakeoutStrategy(self.data_fetcher, symbol, self.interval)
            signals = temp_strategy.analyze()
            
            if signals:
                all_signals[symbol] = signals
                self.stats['signals_found'] += len(signals)
        
        # 更新市场状态缓存
        self.symbol_market_states = market_states
        self.symbol_signals = all_signals
        
        # 选择最佳信号
        if not all_signals:
            return None
        
        best_signal = None
        best_symbol = None
        best_confidence = 0.0
        min_confidence_threshold = 0.6  # 置信度阈值
        
        for symbol, signals in all_signals.items():
            symbol_best = max(signals, key=lambda s: s.confidence)
            if symbol_best.confidence > best_confidence and symbol_best.confidence >= min_confidence_threshold:
                best_confidence = symbol_best.confidence
                best_signal = symbol_best
                best_symbol = symbol
        
        if best_signal is None:
            self._log(f"未找到置信度 >= {min_confidence_threshold:.0%} 的信号")
            return None
        
        return (best_symbol, best_signal)
    
    def _health_check(self) -> bool:
        """
        系统健康检查
        
        Returns:
            是否健康
        """
        # 检查连接状态
        if not self.trading_client.ping():
            self._log("API连接失败")
            return False
        
        return True
    
    def _execute_trade(self, symbol: str, signal: FakeoutSignal):
        """
        执行交易
        
        Args:
            symbol: 标的
            signal: 假突破信号
        """
        try:
            # 计算仓位大小
            account_balance = self.risk_manager.initial_balance + self.risk_manager.metrics.total_pnl
            position_size = self.worth_trading_filter.calculate_position_size(
                symbol,
                account_balance,
                risk_per_trade=0.02
            )
            
            if position_size <= 0:
                self._log("仓位大小计算为0，跳过交易")
                return
            
            # 下市价单
            side = "BUY" if signal.signal_type.value == "BUY" else "SELL"
            
            self._log(f"执行交易: {side} {symbol}")
            self._log(f"  入场价: {signal.entry_price:.2f}")
            self._log(f"  止损: {signal.stop_loss:.2f}")
            self._log(f"  止盈: {signal.take_profit:.2f}")
            self._log(f"  仓位: {position_size:.2f} USDT")
            
            # 实际下单
            result = self.trading_client.place_market_order(
                symbol=symbol,
                side=side,
                quantity=position_size / signal.entry_price
            )
            
            if result.get('error'):
                self._log(f"下单失败: {result.get('message')}")
                return
            
            # 记录交易
            self.execution_gate.record_trade()
            self.stats['trades_executed'] += 1
            
            # 使用持仓管理器记录持仓
            from position_manager import Position, PositionSide
            position = Position(
                symbol=symbol,
                side=PositionSide.LONG if side == "BUY" else PositionSide.SHORT,
                entry_price=signal.entry_price,
                quantity=position_size,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
                order_id=result.get('orderId')
            )
            
            if not self.execution_gate.get_position_manager().add_position(position):
                self._log(f"警告: 持仓添加失败（可能已达上限）")
            
            # 触发回调
            if self.on_order:
                self.on_order({
                    'symbol': symbol,
                    'signal': signal,
                    'order_result': result,
                    'position_size': position_size
                })
            
            self._log("订单已提交")
            
            # 在后台线程中监控持仓
            threading.Thread(target=self._monitor_position, args=(symbol,), daemon=True).start()
            
        except Exception as e:
            self._log(f"执行交易错误: {str(e)}")
            import traceback
            self._log(traceback.format_exc())
            if self.on_error:
                self.on_error(f"下单失败: {str(e)}")
    
    def _monitor_position(self, symbol: str):
        """
        监控持仓，实现自动止盈止损
        
        Args:
            symbol: 交易对
        """
        position_manager = self.execution_gate.get_position_manager()
        
        while self.running:
            try:
                # 检查持仓是否存在
                position = position_manager.get_position(symbol)
                if not position or position.status.value != "ACTIVE":
                    self._log(f"{symbol} 持仓已平仓，停止监控")
                    return
                
                # 获取当前价格
                ticker = self.trading_client.get_ticker(symbol)
                if ticker.get('error'):
                    self._log(f"获取 {symbol} 价格失败，重试中...")
                    time.sleep(10)
                    continue
                
                current_price = float(ticker.get('lastPrice', 0))
                
                # 检查是否需要平仓
                if position.should_stop_loss(current_price):
                    self._log(f"⚠️ {symbol} 触发止损！当前价: {current_price:.2f}, 止损价: {position.stop_loss:.2f}")
                    self._close_position_by_signal(symbol, current_price, "止损")
                    return
                
                if position.should_take_profit(current_price):
                    self._log(f"✅ {symbol} 触发止盈！当前价: {current_price:.2f}, 止盈价: {position.take_profit:.2f}")
                    self._close_position_by_signal(signal=symbol, exit_price=current_price, reason="止盈")
                    return
                
                # 每10秒检查一次
                time.sleep(10)
                
            except Exception as e:
                self._log(f"监控 {symbol} 持仓时出错: {str(e)}")
                import traceback
                self._log(traceback.format_exc())
                time.sleep(30)  # 出错后等待30秒
    
    def _close_position_by_signal(self, symbol: str, exit_price: float, reason: str):
        """
        根据信号平仓
        
        Args:
            symbol: 交易对
            exit_price: 平仓价
            reason: 平仓原因
        """
        try:
            position_manager = self.execution_gate.get_position_manager()
            position = position_manager.get_position(symbol)
            
            if not position:
                self._log(f"{symbol} 持仓不存在")
                return
            
            # 平仓
            side = "SELL" if position.side.value == "LONG" else "BUY"
            
            self._log(f"执行平仓: {side} {symbol} @ {exit_price:.2f}")
            
            # 执行市价平仓单
            result = self.trading_client.place_market_order(
                symbol=symbol,
                side=side,
                quantity=position.quantity / exit_price  # 转换为合约数量
            )
            
            if result.get('error'):
                self._log(f"平仓失败: {result.get('message')}")
                return
            
            # 更新持仓管理器
            closed_position = position_manager.close_position(symbol, exit_price, reason)
            
            if closed_position:
                # 更新风险管理器的盈亏
                self.risk_manager.update_pnl(closed_position.pnl)
                self._log(f"✓ {symbol} 平仓完成 | PnL: {closed_position.pnl:+.2f} USDT | {reason}")
                
                # 触发回调
                if self.on_order:
                    self.on_order({
                        'symbol': symbol,
                        'action': 'CLOSE',
                        'reason': reason,
                        'pnl': closed_position.pnl,
                        'position': closed_position
                    })
        
        except Exception as e:
            self._log(f"平仓 {symbol} 时出错: {str(e)}")
            if self.on_error:
                self.on_error(f"平仓失败: {str(e)}")
    
    def _sync_positions_loop(self):
        """定期同步持仓状态"""
        position_manager = self.execution_gate.get_position_manager()
        
        while self.running:
            try:
                if self.state != SystemState.RUNNING:
                    time.sleep(30)
                    continue
                
                # 每分钟同步一次
                time.sleep(60)
                
                # 获取币安持仓
                binance_positions = self.trading_client.get_positions()
                if binance_positions.get('error'):
                    continue
                
                # 转换为字典 {symbol: position}
                binance_active = {}
                for pos in binance_positions:
                    position_amt = float(pos.get('positionAmt', 0))
                    if abs(position_amt) > 0.00001:  # 有持仓
                        symbol = pos.get('symbol')
                        binance_active[symbol] = position_amt > 0  # True为多头，False为空头
                
                # 检查我们的持仓管理器
                our_positions = position_manager.get_all_positions()
                our_active = {p.symbol: p for p in our_positions}
                
                # 同步差异
                for symbol in list(our_active.keys()):
                    if symbol not in binance_active:
                        # 币安没有持仓但我们有，说明可能被外部平仓
                        self._log(f"⚠️ {symbol} 在币安无持仓，但本地记录为持仓，尝试同步...")
                        # 这里可以选择自动平仓或记录日志
                        # 暂时记录日志
                        continue
                
                for symbol in binance_active:
                    if symbol not in our_active:
                        # 币安有持仓但我们没有记录
                        self._log(f"⚠️ {symbol} 在币安有持仓但无本地记录，可能为外部开仓")
                        continue
                
            except Exception as e:
                self._log(f"同步持仓时出错: {str(e)}")
                import traceback
                self._log(traceback.format_exc())
                time.sleep(60)
    
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
            'interval': self.interval,
            'selected_symbols': self.selected_symbols,
            'symbols_count': len(self.selected_symbols),
            'stats': self.stats,
            'risk_metrics': self.risk_manager.get_metrics(),
            'symbol_market_states': self.symbol_market_states,
            'symbol_signals': {k: len(v) for k, v in self.symbol_signals.items()}
        }
    
    def get_symbol_selector(self) -> SymbolSelector:
        """获取合约选择器"""
        return self.symbol_selector
    
    def update_parameters(self, config_dict: dict):
        """
        动态更新系统参数
        
        Args:
            config_dict: 配置字典，格式为 {'fakeout_strategy': {...}, 'risk_manager': {...}, ...}
        """
        try:
            # 更新假突破策略参数
            if 'fakeout_strategy' in config_dict:
                for key, value in config_dict['fakeout_strategy'].items():
                    if hasattr(self.fakeout_strategy, key):
                        setattr(self.fakeout_strategy, key, value)
                        self._log(f"参数已更新: fakeout_strategy.{key} = {value}")
            
            # 更新风险管理参数
            if 'risk_manager' in config_dict:
                for key, value in config_dict['risk_manager'].items():
                    if hasattr(self.risk_manager, key):
                        setattr(self.risk_manager, key, value)
                        self._log(f"参数已更新: risk_manager.{key} = {value}")
            
            # 更新过滤器参数
            if 'worth_trading_filter' in config_dict:
                for key, value in config_dict['worth_trading_filter'].items():
                    if hasattr(self.worth_trading_filter, key):
                        setattr(self.worth_trading_filter, key, value)
                        self._log(f"参数已更新: worth_trading_filter.{key} = {value}")
            
            # 更新执行闸门参数
            if 'execution_gate' in config_dict:
                for key, value in config_dict['execution_gate'].items():
                    if hasattr(self.execution_gate, key):
                        # 特殊处理时间间隔参数
                        if key == 'min_trade_interval_minutes':
                            self.execution_gate.min_trade_interval = timedelta(minutes=value)
                        else:
                            setattr(self.execution_gate, key, value)
                        self._log(f"参数已更新: execution_gate.{key} = {value}")
            
            # 更新市场状态引擎参数
            if 'market_state_engine' in config_dict:
                for key, value in config_dict['market_state_engine'].items():
                    if hasattr(self.market_state_engine, key):
                        setattr(self.market_state_engine, key, value)
                        self._log(f"参数已更新: market_state_engine.{key} = {value}")
            
            self._log("系统参数更新完成")
            
        except Exception as e:
            self._log(f"参数更新失败: {str(e)}")
            raise


# 测试代码
if __name__ == "__main__":
    print("多标假突破策略系统测试")
    print("\n注意：需要真实的API密钥才能运行")
    print("建议先在模拟模式下测试\n")
    
    # 示例：创建策略系统
    # from binance_trading_client import BinanceTradingClient
    
    # # 创建交易客户端（需要真实API密钥）
    # client = BinanceTradingClient("your_api_key", "your_api_secret")
    
    # # 创建策略系统
    # system = MultiSymbolFakeoutSystem(client)
    
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
    #               f"信号数: {status['stats']['signals_found']} | 交易数: {status['stats']['trades_executed']} | "
    #               f"标的数: {status['symbols_count']}", end="")
    #         time.sleep(10)
    # except KeyboardInterrupt:
    #     print("\n\n停止系统...")
    #     system.stop()
    #     print("系统已停止")
    
    print("\n策略系统框架已就绪，可以集成到GUI中运行")

# 向后兼容：保留旧类名
ETHFakeoutStrategySystem = MultiSymbolFakeoutSystem
