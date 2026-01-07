#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FVG流动性策略系统 - 完整系统
整合多周期分析器、FVG策略和流动性分析器，支持多合约标的分析与自动交易
"""

import time
import threading
from typing import Optional, Callable, List, Dict, Tuple
from datetime import datetime, timedelta
from enum import Enum
import logging

from binance_trading_client import BinanceTradingClient
from binance_api_client import BinanceAPIClient
from data_fetcher import DataFetcher
from market_state_engine import MarketStateEngine, MarketState
from worth_trading_filter import WorthTradingFilter
from risk_manager import RiskManager, ExecutionGate
from symbol_selector import SymbolSelector, SelectionMode
from position_manager import Position, PositionSide

from fvg_strategy import FVGStrategy
from liquidity_analyzer import LiquidityAnalyzer
from multi_timeframe_analyzer import MultiTimeframeAnalyzer, TimeframeAnalysis, MultiTimeframeConfluence
from fvg_signal import TradingSignal
from parameter_config import get_config

logger = logging.getLogger(__name__)


class SystemState(Enum):
    """系统状态"""
    INITIALIZING = "INITIALIZING"     # 初始化中
    RUNNING = "RUNNING"               # 运行中
    PAUSED = "PAUSED"                 # 已暂停
    ERROR = "ERROR"                  # 错误状态
    STOPPED = "STOPPED"               # 已停止


class FVGLiquidityStrategySystem:
    """FVG流动性策略系统"""
    
    def __init__(self, trading_client: BinanceTradingClient):
        """
        初始化策略系统
        
        Args:
            trading_client: 交易客户端
        """
        self.trading_client = trading_client
        
        # 读取配置
        self.config = get_config()
        self.fvg_config = self.config.fvg_strategy
        self.liquidity_config = self.config.liquidity_analyzer
        
        # 主周期（默认1小时）
        self.primary_timeframe = self.fvg_config.primary_timeframe
        
        # 创建各模块
        self.api_client = BinanceAPIClient()
        self.data_fetcher = DataFetcher(self.api_client)
        self.symbol_selector = SymbolSelector(self.api_client)
        
        # 市场状态引擎（使用主周期）
        self.market_state_engine = MarketStateEngine(
            self.data_fetcher,
            "ETHUSDT",
            self.primary_timeframe,
            enable_sleep_filter=self.config.market_state_engine.enable_market_sleep_filter
        )
        
        # 多周期分析器（传递data_fetcher）
        self.mtf_analyzer = MultiTimeframeAnalyzer(self.config, self.data_fetcher)
        
        # 交易价值过滤
        self.worth_trading_filter = WorthTradingFilter(self.data_fetcher)
        
        # 风险管理
        self.risk_manager = RiskManager()
        self.execution_gate = ExecutionGate()
        
        # 多标的状态
        self.selected_symbols: List[str] = []
        self.symbol_market_states: Dict[str, dict] = {}
        self.symbol_analyses: Dict[str, Dict[str, TimeframeAnalysis]] = {}
        self.symbol_confluences: Dict[str, MultiTimeframeConfluence] = {}
        
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
            'confluences_found': 0,
            'trades_executed': 0,
            'symbols_analyzed': 0,
            'timeframes_analyzed': 0,
            'skips': {
                'market_sleep': 0,
                'not_worth': 0,
                'execution_gate': 0,
                'risk_manager': 0,
                'no_confluence': 0,
                'low_confidence': 0
            }
        }
        
        # 初始化
        self._initialize()
    
    def _initialize(self):
        """初始化系统"""
        try:
            # 初始化合约选择器
            self._log("正在获取USDT永续合约列表...")
            self.symbol_selector.update_symbol_list(force_update=True)
            self.selected_symbols = self.symbol_selector.get_selected_symbols()
            self._log(f"已选择 {len(self.selected_symbols)} 个合约进行监控")
            for symbol in self.selected_symbols:
                self._log(f"  - {symbol}")
            
            # 初始化风险管理器
            account_info = self.trading_client.get_account_info()
            if not account_info.get('error'):
                balance = float(account_info.get('totalWalletBalance', 0))
                self.risk_manager.set_initial_balance(balance)
                self._log(f"账户余额: {balance:.2f} USDT")
            
            # 启动持仓同步任务
            threading.Thread(target=self._sync_positions_loop, daemon=True).start()
            
            self.state = SystemState.RUNNING
            self._log("FVG流动性策略系统初始化完成")
            
        except Exception as e:
            self._log(f"初始化失败: {str(e)}")
            self.state = SystemState.ERROR
    
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
        
        self._log("FVG流动性策略系统已启动")
        self._log(f"监控标的: {', '.join(self.selected_symbols)}")
        self._log(f"分析周期: {', '.join(self.fvg_config.timeframes)}")
        self._log(f"主周期: {self.primary_timeframe}")
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
                    # 每10次循环记录一次跳过日志
                    if loop_count % 10 == 0:
                        self._log(f"循环 #{loop_count} 跳过: {skip_reason}")
                else:
                    self._log(f"循环 #{loop_count} 执行交易周期")
                
                # 短暂休眠
                interval = self.config.system.loop_interval_seconds
                time.sleep(interval)
                
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
            # self._log(f"熔断检查拒绝: {reason}")  # 减少日志输出
            return "risk_manager"
        
        # 3. 检查是否有选中的标的
        if not self.selected_symbols:
            # self._log("没有选中的标的")
            return "no_symbols"
        
        # 4. 批量分析所有选中标的
        # self._log(f"开始分析 {len(self.selected_symbols)} 个标的...")
        best_result = self._analyze_all_symbols()
        
        if not best_result:
            # self._log("未找到符合条件的标的")
            return None  # 没有找到符合条件的标的
        
        best_symbol, best_confluence = best_result
        
        self._log(f"✓ 最佳信号: {best_symbol} {best_confluence.confluence_type} | "
                 f"置信度: {best_confluence.confidence:.1%} | "
                 f"共振评分: {best_confluence.confluence_score:.2f} | "
                 f"周期: {', '.join(best_confluence.contributing_timeframes)}")
        
        # 5. 执行条件校验
        primary_signal = best_confluence.primary_signal
        if not primary_signal:
            self._log("⚠ 缺少主周期信号")
            return "no_primary_signal"
        
        # 获取主周期K线用于执行闸门检查
        klines = self.data_fetcher.get_klines(
            best_symbol, 
            self.primary_timeframe, 
            limit=100
        )
        
        allowed, reason = self.execution_gate.check(
            primary_signal,
            klines,
            min_stop_loss_distance=0.01
        )
        
        if not allowed:
            self._log(f"✗ 执行闸门拒绝: {reason}")
            return "execution_gate"
        
        # 6. 下单执行
        self._execute_trade(best_symbol, best_confluence)
        
        return None
    
    def _analyze_all_symbols(self) -> Optional[Tuple[str, MultiTimeframeConfluence]]:
        """
        分析所有选中的标的
        
        Returns:
            (symbol, confluence) 或 None
        """
        all_confluences = {}
        market_states = {}
        
        self.stats['symbols_analyzed'] = len(self.selected_symbols)
        
        # 批量获取市场指标
        market_metrics = self.data_fetcher.get_market_metrics_batch(
            self.selected_symbols,
            self.primary_timeframe,
            atr_period=14,
            volume_period=20
        )
        
        # 更新合约选择器的指标
        self.symbol_selector.update_market_metrics(market_metrics)
        
        # 批量分析市场状态
        state_infos = self.market_state_engine.analyze_batch(self.selected_symbols)
        
        # 为每个标的分析多周期
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
            
            # 3. 获取各周期K线数据
            klines_data = {}
            for tf in self.fvg_config.timeframes:
                try:
                    klines = self.data_fetcher.get_klines(
                        symbol, 
                        tf, 
                        limit=self.fvg_config.fvg_detection_lookback + 50
                    )
                    if klines and len(klines) > self.fvg_config.fvg_detection_lookback:
                        klines_data[tf] = klines
                        self.stats['timeframes_analyzed'] += 1
                except Exception as e:
                    logger.warning(f"获取 {symbol} {tf} K线失败: {e}")
            
            if not klines_data:
                continue
            
            # 4. 多周期分析
            timeframe_analyses = self.mtf_analyzer.analyze_multi_timeframe(
                symbol, 
                klines_data
            )
            self.symbol_analyses[symbol] = timeframe_analyses
            
            # 5. 检测共振
            confluence = self.mtf_analyzer.detect_confluence(
                symbol,
                timeframe_analyses
            )
            
            if confluence and confluence.confidence >= self.fvg_config.min_confidence:
                all_confluences[symbol] = confluence
                self.stats['confluences_found'] += 1
        
        # 更新市场状态缓存
        self.symbol_market_states = market_states
        self.symbol_confluences = all_confluences
        
        # 选择最佳共振信号
        if not all_confluences:
            return None
        
        best_confluence = max(
            all_confluences.values(),
            key=lambda c: c.confidence
        )
        
        best_symbol = best_confluence.symbol
        
        return (best_symbol, best_confluence)
    
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
    
    def _execute_trade(self, symbol: str, confluence: MultiTimeframeConfluence):
        """
        执行交易
        
        Args:
            symbol: 标的
            confluence: 多周期共振分析结果
        """
        try:
            # 获取主信号
            primary_signal = confluence.primary_signal
            if not primary_signal:
                self._log("❌ 主信号为空，无法执行交易")
                return
            
            # 检查是否为模拟模式
            if self.config.system.enable_simulation:
                self._log(f"📊 模拟交易: {confluence.confluence_type} {symbol}")
                self._log(f"  入场价: {primary_signal.entry_price:.6f}")
                self._log(f"  止损: {primary_signal.stop_loss:.6f}")
                self._log(f"  止盈: {primary_signal.take_profit:.6f}")
                self._log(f"  置信度: {confluence.confidence:.1%}")
                
                # 记录模拟交易
                self.stats['trades_executed'] += 1
                self.execution_gate.record_trade()
                
                # 触发回调
                if self.on_order:
                    self.on_order({
                        'symbol': symbol,
                        'signal': primary_signal,
                        'confluence': confluence,
                        'order_result': {'success': True, 'orderId': f"SIM_{datetime.now().timestamp()}"},
                        'type': 'SIMULATION'
                    })
                
                return
            
            # 实盘模式：计算仓位大小
            account_balance = self.risk_manager.initial_balance + self.risk_manager.metrics.total_pnl
            position_size = self.worth_trading_filter.calculate_position_size(
                symbol,
                account_balance,
                risk_per_trade=self.config.risk_manager.risk_per_trade
            )
            
            if position_size <= 0:
                self._log("仓位大小计算为0，跳过交易")
                return
            
            # 下市价单
            side = confluence.confluence_type
            
            self._log(f"💰 实盘交易: {side} {symbol}")
            self._log(f"  入场价: {primary_signal.entry_price:.6f}")
            self._log(f"  止损: {primary_signal.stop_loss:.6f}")
            self._log(f"  止盈: {primary_signal.take_profit:.6f}")
            self._log(f"  仓位: {position_size:.2f} USDT")
            self._log(f"  置信度: {confluence.confidence:.1%}")
            
            # 实际下单
            result = self.trading_client.place_market_order(
                symbol=symbol,
                side=side,
                quantity=position_size / primary_signal.entry_price
            )
            
            if result.get('error'):
                self._log(f"下单失败: {result.get('message')}")
                return
            
            # 记录交易
            self.execution_gate.record_trade()
            self.stats['trades_executed'] += 1
            
            # 使用持仓管理器记录持仓
            position_side = PositionSide.LONG if side == "BUY" else PositionSide.SHORT
            position = Position(
                symbol=symbol,
                side=position_side,
                entry_price=primary_signal.entry_price,
                quantity=position_size,
                stop_loss=primary_signal.stop_loss,
                take_profit=primary_signal.take_profit,
                order_id=result.get('orderId')
            )
            
            if not self.execution_gate.get_position_manager().add_position(position):
                self._log(f"❌ 持仓添加失败（已达上限），立即平仓...")
                # 持仓添加失败，立即平仓刚创建的持仓
                close_side = "SELL" if side == "BUY" else "BUY"
                close_result = self.trading_client.place_market_order(
                    symbol=symbol,
                    side=close_side,
                    quantity=position_size / primary_signal.entry_price
                )
                if close_result.get('error'):
                    self._log(f"❌ 紧急平仓失败: {close_result.get('message')}")
                else:
                    self._log(f"✓ 紧急平仓成功")
                return  # 终止交易流程
            
            # 触发回调
            if self.on_order:
                self.on_order({
                    'symbol': symbol,
                    'signal': primary_signal,
                    'confluence': confluence,
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
            symbol: 标的
        """
        try:
            while self.running:
                # 获取当前持仓
                position = self.execution_gate.get_position_manager().get_position(symbol)
                
                if not position:
                    break  # 持仓不存在，退出监控
                
                # 获取当前价格
                current_price = self.data_fetcher.get_current_price(symbol)
                if not current_price:
                    time.sleep(2)
                    continue
                
                # 检查止盈止损
                should_close, close_type = self.execution_gate.check_stop_take_profit(
                    position,
                    current_price
                )
                
                if should_close:
                    self._log(f"触发{close_type}: {symbol}")
                    
                    # 平仓
                    side = "SELL" if position.side == PositionSide.LONG else "BUY"
                    result = self.trading_client.place_market_order(
                        symbol=symbol,
                        side=side,
                        quantity=position.quantity
                    )
                    
                    if result.get('error'):
                        self._log(f"平仓失败: {result.get('message')}")
                    else:
                        self._log(f"平仓成功: {close_type}")
                        # 更新持仓管理器状态
                        self.execution_gate.get_position_manager().close_position(symbol)
                    
                    break
                
                # 短暂休眠
                time.sleep(1)
                
        except Exception as e:
            self._log(f"监控持仓错误: {str(e)}")
    
    def _sync_positions_loop(self):
        """后台线程：同步持仓"""
        while self.running:
            try:
                self.execution_gate.get_position_manager().sync_positions(
                    self.trading_client
                )
                time.sleep(5)
            except Exception as e:
                logger.error(f"同步持仓失败: {e}")
                time.sleep(10)
    
    def _log(self, message: str):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        # 输出到控制台
        print(log_message)
        
        # 触发回调
        if self.on_status_update:
            self.on_status_update(log_message)
        
        # 记录到logger
        logger.info(message)
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            **self.stats,
            'selected_symbols_count': len(self.selected_symbols),
            'state': self.state.value
        }
    
    def get_symbol_states(self) -> Dict[str, dict]:
        """获取各标的状态"""
        return self.symbol_market_states.copy()
    
    def get_symbol_confluences(self) -> Dict[str, dict]:
        """获取各标的多周期共振"""
        return {
            symbol: {
                'type': c.confluence_type,
                'score': c.confluence_score,
                'confidence': c.confidence,
                'timeframes': c.contributing_timeframes
            }
            for symbol, c in self.symbol_confluences.items()
        }
    
    def get_symbol_analyses(self) -> Dict[str, dict]:
        """获取各标的分析结果"""
        result = {}
        for symbol, analyses in self.symbol_analyses.items():
            result[symbol] = {}
            for tf, analysis in analyses.items():
                result[symbol][tf] = {
                    'signals_count': len(analysis.trading_signals),
                    'bullish_fvgs': len(analysis.bullish_fvgs),
                    'bearish_fvgs': len(analysis.bearish_fvgs),
                    'liquidity_zones': len(analysis.liquidity_zones)
                }
        return result
