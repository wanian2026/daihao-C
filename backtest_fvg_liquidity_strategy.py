#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FVG流动性策略回测脚本
验证策略的历史表现，计算关键指标
"""

import sys
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import logging

from binance_api_client import BinanceAPIClient
from data_fetcher import DataFetcher
from fvg_strategy import FVGStrategy
from liquidity_analyzer import LiquidityAnalyzer
from multi_timeframe_analyzer import MultiTimeframeAnalyzer
from fvg_signal import TradingSignal
from parameter_config import get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class BacktestTrade:
    """回测交易记录"""
    symbol: str                          # 交易对
    timeframe: str                       # 周期
    entry_time: datetime                 # 入场时间
    exit_time: Optional[datetime]        # 退出时间
    direction: str                       # 方向 (BUY/SELL)
    entry_price: float                   # 入场价
    exit_price: float                    # 退出价
    stop_loss: float                     # 止损价
    take_profit: float                   # 止盈价
    confidence: float                    # 置信度
    pnl: float                           # 盈亏
    pnl_percent: float                   # 盈亏百分比
    exit_reason: str                     # 退出原因 (TP/SL/EXPIRED)
    is_fvg_signal: bool                  # 是否为FVG信号
    is_liquidity_signal: bool            # 是否为流动性信号


@dataclass
class BacktestResult:
    """回测结果"""
    symbol: str                          # 交易对
    timeframe: str                       # 周期
    start_date: datetime                 # 回测开始日期
    end_date: datetime                   # 回测结束日期
    
    # 交易统计
    total_trades: int                    # 总交易次数
    winning_trades: int                  # 盈利交易次数
    losing_trades: int                   # 亏损交易次数
    win_rate: float                      # 胜率
    
    # 盈亏统计
    total_pnl: float                     # 总盈亏
    total_pnl_percent: float             # 总盈亏百分比
    average_win: float                   # 平均盈利
    average_loss: float                  # 平均亏损
    profit_factor: float                 # 盈利因子
    
    # 风险指标
    max_drawdown: float                  # 最大回撤
    max_consecutive_losses: int          # 最大连续亏损次数
    max_consecutive_wins: int            # 最大连续盈利次数
    
    # 信号分析
    fvg_trades: int                      # FVG信号交易次数
    fvg_wins: int                        # FVG信号盈利次数
    liquidity_trades: int                # 流动性信号交易次数
    liquidity_wins: int                  # 流动性信号盈利次数
    
    # 交易记录
    trades: List[BacktestTrade]          # 所有交易记录


class FVGLiquidityBacktester:
    """FVG流动性策略回测器"""
    
    def __init__(self, config=None):
        """
        初始化回测器
        
        Args:
            config: 参数配置
        """
        self.config = config or get_config()
        
        # 初始化API和数据获取器
        self.api_client = BinanceAPIClient()
        self.data_fetcher = DataFetcher(self.api_client)
        
        # 初始化分析器
        self.mtf_analyzer = MultiTimeframeAnalyzer(self.config)
        
        # 交易滑点设置
        self.slippage_percent = 0.0005  # 0.05% 滑点
        
        logger.info("FVG流动性策略回测器初始化完成")
    
    def run_backtest(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime
    ) -> BacktestResult:
        """
        运行回测
        
        Args:
            symbol: 交易对
            timeframe: 周期
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            BacktestResult: 回测结果
        """
        logger.info(f"开始回测 {symbol} {timeframe} "
                   f"({start_date.date()} 至 {end_date.date()})")
        
        # 计算需要的K线数量
        time_diff = (end_date - start_date).days
        limit = max(1000, time_diff * (24 * 60 // self._timeframe_to_minutes(timeframe)))
        limit = min(limit, 5000)  # Binance API限制
        
        # 获取K线数据
        logger.info(f"获取 {limit} 条K线数据...")
        klines = self.data_fetcher.get_klines(symbol, timeframe, limit=limit)
        
        if not klines or len(klines) < 100:
            logger.error(f"K线数据不足: {len(klines) if klines else 0}")
            return None
        
        # 过滤时间范围
        klines = [k for k in klines 
                  if start_date <= datetime.fromtimestamp(k[0]/1000) <= end_date]
        
        logger.info(f"有效K线数量: {len(klines)}")
        
        # 执行回测
        trades = self._backtest_signals(symbol, timeframe, klines)
        
        # 计算回测结果
        result = self._calculate_result(
            symbol, timeframe, start_date, end_date, trades
        )
        
        return result
    
    def _backtest_signals(
        self,
        symbol: str,
        timeframe: str,
        klines: List[Dict]
    ) -> List[BacktestTrade]:
        """
        回测信号执行
        
        Args:
            symbol: 交易对
            timeframe: 周期
            klines: K线数据
            
        Returns:
            List[BacktestTrade]: 交易记录
        """
        trades = []
        open_positions: Dict[str, BacktestTrade] = {}
        
        lookback = self.config.fvg_strategy.fvg_detection_lookback
        
        # 逐K线扫描
        for i in range(lookback, len(klines)):
            current_kline = klines[i]
            current_price = float(current_kline[4])  # 收盘价
            current_time = datetime.fromtimestamp(current_kline[0]/1000)
            
            # 获取当前窗口的K线
            window_klines = klines[max(0, i-lookback):i+1]
            
            # 生成信号
            klines_data = {timeframe: window_klines}
            timeframe_analyses = self.mtf_analyzer.analyze_multi_timeframe(
                symbol, klines_data
            )
            
            # 获取最佳信号
            best_signals = self.mtf_analyzer.get_best_signals(
                symbol, timeframe_analyses, top_n=1
            )
            
            if best_signals and best_signals[0].confidence >= self.config.fvg_strategy.min_confidence:
                signal = best_signals[0]
                
                # 检查是否已经有该方向的持仓
                position_key = f"{symbol}_{signal.direction}"
                if position_key in open_positions:
                    # 已有持仓，不重复开仓
                    continue
                
                # 检查价格有效性
                if signal.entry_price <= 0 or signal.stop_loss <= 0 or signal.take_profit <= 0:
                    continue
                
                # 创建交易记录
                trade = BacktestTrade(
                    symbol=symbol,
                    timeframe=timeframe,
                    entry_time=current_time,
                    exit_time=None,
                    direction=signal.direction,
                    entry_price=signal.entry_price,
                    exit_price=0.0,
                    stop_loss=signal.stop_loss,
                    take_profit=signal.take_profit,
                    confidence=signal.confidence,
                    pnl=0.0,
                    pnl_percent=0.0,
                    exit_reason="",
                    is_fvg_signal=signal.signal_type == "FVG",
                    is_liquidity_signal=signal.signal_type == "LIQUIDITY_CATCH"
                )
                
                open_positions[position_key] = trade
                logger.debug(f"开仓: {signal.direction} {symbol} @ {signal.entry_price:.6f}")
            
            # 检查持仓的止盈止损
            closed_positions = []
            for key, trade in open_positions.items():
                sl_hit = False
                tp_hit = False
                
                if trade.direction == "BUY":
                    if current_price <= trade.stop_loss:
                        sl_hit = True
                        exit_reason = "SL"
                    elif current_price >= trade.take_profit:
                        tp_hit = True
                        exit_reason = "TP"
                else:  # SELL
                    if current_price >= trade.stop_loss:
                        sl_hit = True
                        exit_reason = "SL"
                    elif current_price <= trade.take_profit:
                        tp_hit = True
                        exit_reason = "TP"
                
                if sl_hit or tp_hit:
                    # 计算盈亏（考虑滑点）
                    slippage = trade.entry_price * self.slippage_percent
                    
                    if trade.direction == "BUY":
                        actual_exit_price = current_price - slippage if tp_hit else current_price + slippage
                        price_diff = actual_exit_price - trade.entry_price
                    else:  # SELL
                        actual_exit_price = current_price + slippage if tp_hit else current_price - slippage
                        price_diff = trade.entry_price - actual_exit_price
                    
                    trade.exit_time = current_time
                    trade.exit_price = actual_exit_price
                    trade.exit_reason = exit_reason
                    trade.pnl = price_diff * 100  # 假设100个单位
                    trade.pnl_percent = (price_diff / trade.entry_price) * 100
                    
                    trades.append(trade)
                    closed_positions.append(key)
                    
                    logger.debug(f"平仓: {trade.direction} {symbol} @ {actual_exit_price:.6f} "
                               f"({exit_reason}, PnL: {trade.pnl:.2f})")
            
            # 移除已平仓的持仓
            for key in closed_positions:
                del open_positions[key]
        
        # 平掉所有未平仓的持仓（按最后价格）
        if klines:
            last_price = float(klines[-1][4])
            last_time = datetime.fromtimestamp(klines[-1][0]/1000)
            
            for key, trade in open_positions.items():
                slippage = trade.entry_price * self.slippage_percent
                
                if trade.direction == "BUY":
                    actual_exit_price = last_price - slippage
                    price_diff = actual_exit_price - trade.entry_price
                else:  # SELL
                    actual_exit_price = last_price + slippage
                    price_diff = trade.entry_price - actual_exit_price
                
                trade.exit_time = last_time
                trade.exit_price = actual_exit_price
                trade.exit_reason = "EXPIRED"
                trade.pnl = price_diff * 100
                trade.pnl_percent = (price_diff / trade.entry_price) * 100
                
                trades.append(trade)
        
        return trades
    
    def _calculate_result(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        trades: List[BacktestTrade]
    ) -> BacktestResult:
        """
        计算回测结果
        
        Args:
            symbol: 交易对
            timeframe: 周期
            start_date: 开始日期
            end_date: 结束日期
            trades: 交易记录
            
        Returns:
            BacktestResult: 回测结果
        """
        total_trades = len(trades)
        
        if total_trades == 0:
            return BacktestResult(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                total_pnl=0.0,
                total_pnl_percent=0.0,
                average_win=0.0,
                average_loss=0.0,
                profit_factor=0.0,
                max_drawdown=0.0,
                max_consecutive_losses=0,
                max_consecutive_wins=0,
                fvg_trades=0,
                fvg_wins=0,
                liquidity_trades=0,
                liquidity_wins=0,
                trades=[]
            )
        
        # 基础统计
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl < 0]
        
        wins = len(winning_trades)
        losses = len(losing_trades)
        win_rate = wins / total_trades if total_trades > 0 else 0
        
        # 盈亏统计
        total_pnl = sum(t.pnl for t in trades)
        average_win = sum(t.pnl for t in winning_trades) / wins if wins > 0 else 0
        average_loss = sum(t.pnl for t in losing_trades) / losses if losses > 0 else 0
        
        total_win = sum(t.pnl for t in winning_trades)
        total_loss = abs(sum(t.pnl for t in losing_trades))
        profit_factor = total_win / total_loss if total_loss > 0 else 0
        
        # 风险指标
        max_drawdown = self._calculate_max_drawdown(trades)
        max_consecutive_losses = self._calculate_max_consecutive(trades, win=True)
        max_consecutive_wins = self._calculate_max_consecutive(trades, win=False)
        
        # 信号分析
        fvg_trades = [t for t in trades if t.is_fvg_signal]
        fvg_wins = len([t for t in fvg_trades if t.pnl > 0])
        
        liquidity_trades = [t for t in trades if t.is_liquidity_signal]
        liquidity_wins = len([t for t in liquidity_trades if t.pnl > 0])
        
        return BacktestResult(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            total_trades=total_trades,
            winning_trades=wins,
            losing_trades=losses,
            win_rate=win_rate,
            total_pnl=total_pnl,
            total_pnl_percent=(total_pnl / (trades[0].entry_price * 100)) * 100 if trades else 0,
            average_win=average_win,
            average_loss=average_loss,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            max_consecutive_losses=max_consecutive_losses,
            max_consecutive_wins=max_consecutive_wins,
            fvg_trades=len(fvg_trades),
            fvg_wins=fvg_wins,
            liquidity_trades=len(liquidity_trades),
            liquidity_wins=liquidity_wins,
            trades=trades
        )
    
    def _calculate_max_drawdown(self, trades: List[BacktestTrade]) -> float:
        """计算最大回撤"""
        if not trades:
            return 0.0
        
        cumulative = 0.0
        peak = 0.0
        max_dd = 0.0
        
        for trade in trades:
            cumulative += trade.pnl
            if cumulative > peak:
                peak = cumulative
            
            dd = (peak - cumulative) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)
        
        return max_dd * 100  # 转换为百分比
    
    def _calculate_max_consecutive(self, trades: List[BacktestTrade], win: bool) -> int:
        """计算最大连续盈利或亏损次数"""
        if not trades:
            return 0
        
        max_streak = 0
        current_streak = 0
        
        for trade in trades:
            is_win = trade.pnl > 0
            if is_win == win:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return max_streak
    
    def _timeframe_to_minutes(self, timeframe: str) -> int:
        """将周期转换为分钟"""
        timeframe = timeframe.lower()
        if 'm' in timeframe:
            return int(timeframe.replace('m', ''))
        elif 'h' in timeframe:
            return int(timeframe.replace('h', '')) * 60
        elif 'd' in timeframe:
            return int(timeframe.replace('d', '')) * 60 * 24
        else:
            return 60
    
    def print_result(self, result: BacktestResult):
        """打印回测结果"""
        print("\n" + "="*80)
        print(f"FVG流动性策略回测报告")
        print("="*80)
        print(f"交易对: {result.symbol}")
        print(f"周期: {result.timeframe}")
        print(f"回测时间: {result.start_date.date()} 至 {result.end_date.date()}")
        print("-"*80)
        
        print(f"【交易统计】")
        print(f"  总交易次数: {result.total_trades}")
        print(f"  盈利交易: {result.winning_trades}")
        print(f"  亏损交易: {result.losing_trades}")
        print(f"  胜率: {result.win_rate*100:.2f}%")
        
        print(f"\n【盈亏统计】")
        print(f"  总盈亏: {result.total_pnl:.2f} USDT")
        print(f"  总盈亏百分比: {result.total_pnl_percent:.2f}%")
        print(f"  平均盈利: {result.average_win:.2f} USDT")
        print(f"  平均亏损: {result.average_loss:.2f} USDT")
        print(f"  盈利因子: {result.profit_factor:.2f}")
        
        print(f"\n【风险指标】")
        print(f"  最大回撤: {result.max_drawdown:.2f}%")
        print(f"  最大连续亏损: {result.max_consecutive_losses}")
        print(f"  最大连续盈利: {result.max_consecutive_wins}")
        
        print(f"\n【信号分析】")
        print(f"  FVG信号交易: {result.fvg_trades} 次 (胜率: {result.fvg_wins/result.fvg_trades*100 if result.fvg_trades>0 else 0:.2f}%)")
        print(f"  流动性信号交易: {result.liquidity_trades} 次 (胜率: {result.liquidity_wins/result.liquidity_trades*100 if result.liquidity_trades>0 else 0:.2f}%)")
        
        print("="*80)


def main():
    """主函数"""
    # 配置
    symbol = "ETHUSDT"
    timeframe = "1h"
    
    # 回测时间范围（最近30天）
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # 创建回测器
    backtester = FVGLiquidityBacktester()
    
    # 运行回测
    result = backtester.run_backtest(symbol, timeframe, start_date, end_date)
    
    # 打印结果
    if result:
        backtester.print_result(result)
    else:
        print("回测失败！")


if __name__ == "__main__":
    main()
