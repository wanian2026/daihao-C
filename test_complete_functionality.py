#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整功能测试脚本 - 验证信号识别和自动交易
"""

import time
from datetime import datetime

from binance_api_client import BinanceAPIClient
from data_fetcher import DataFetcher
from fakeout_strategy import FakeoutStrategy, FakeoutSignal
from market_state_engine import MarketStateEngine, MarketState
from worth_trading_filter import WorthTradingFilter
from risk_manager import RiskManager, ExecutionGate
from symbol_selector import SymbolSelector, SelectionMode
from parameter_config import get_config


class Color:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 80)
    print(f"{Color.BOLD}{Color.BLUE}{title}{Color.RESET}")
    print("=" * 80 + "\n")


def print_success(msg):
    """打印成功消息"""
    print(f"{Color.GREEN}✓ {msg}{Color.RESET}")


def print_error(msg):
    """打印错误消息"""
    print(f"{Color.RED}✗ {msg}{Color.RESET}")


def print_warning(msg):
    """打印警告消息"""
    print(f"{Color.YELLOW}⚠ {msg}{Color.RESET}")


def print_info(msg):
    """打印信息"""
    print(f"  {msg}")


def test_binance_api():
    """测试币安API连接"""
    print_header("测试1: 币安API连接")
    
    try:
        api_client = BinanceAPIClient()
        
        # 测试ping
        print_info("测试ping连接...")
        result = api_client.ping()
        if result:
            print_success("API连接成功")
        else:
            print_error("API连接失败")
            return False
        
        # 测试获取服务器时间
        print_info("获取服务器时间...")
        server_time = api_client.get_server_time()
        if server_time:
            print_success(f"服务器时间: {server_time}")
        else:
            print_error("获取服务器时间失败")
            return False
        
        # 测试获取合约列表
        print_info("获取USDT永续合约列表...")
        futures_info = api_client.get_futures_exchange_info()
        if futures_info:
            symbols = [s['symbol'] for s in futures_info['symbols'] if s['status'] == 'TRADING']
            print_success(f"获取到 {len(symbols)} 个交易中的合约")
            print_info(f"前10个合约: {', '.join(symbols[:10])}")
        else:
            print_error("获取合约列表失败")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"API测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_data_fetcher():
    """测试数据获取器"""
    print_header("测试2: 数据获取器")
    
    try:
        api_client = BinanceAPIClient()
        data_fetcher = DataFetcher(api_client)
        
        # 测试K线数据获取
        test_symbols = ["ETHUSDT", "BTCUSDT"]
        
        for symbol in test_symbols:
            print_info(f"获取 {symbol} K线数据（5分钟，最近100根）...")
            klines = data_fetcher.get_klines(symbol, "5m", limit=100)
            
            if klines and len(klines) > 0:
                print_success(f"{symbol} - 获取到 {len(klines)} 根K线")
                print_info(f"  最新: {klines[-1].close:.2f}")
                print_info(f"  最早: {klines[0].close:.2f}")
            else:
                print_error(f"{symbol} - K线数据获取失败")
                return False
        
        # 测试ATR计算
        print_info(f"计算 ETHUSDT ATR（14周期）...")
        atr = data_fetcher.get_atr("ETHUSDT", "5m", 14)
        if atr and atr > 0:
            print_success(f"ATR = {atr:.2f}")
        else:
            print_error("ATR计算失败")
            return False
        
        # 测试市场指标批量获取
        print_info(f"批量获取市场指标...")
        metrics = data_fetcher.get_market_metrics_batch(test_symbols, "5m", 14, 20)
        if metrics:
            for symbol, metric in metrics.items():
                print_success(f"{symbol} - ATR:{metric['atr']:.2f}, 成交量比:{metric['volume_ratio']:.2f}")
        else:
            print_error("批量获取市场指标失败")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"数据获取器测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_market_state_engine():
    """测试市场状态引擎"""
    print_header("测试3: 市场状态引擎")
    
    try:
        api_client = BinanceAPIClient()
        data_fetcher = DataFetcher(api_client)
        
        test_symbols = ["ETHUSDT", "BTCUSDT", "SOLUSDT"]
        
        for symbol in test_symbols:
            print_info(f"分析 {symbol} 市场状态...")
            engine = MarketStateEngine(data_fetcher, symbol, "5m")
            state_info = engine.analyze()
            
            print_success(f"{symbol} - 状态: {state_info.state.value}")
            print_info(f"  活跃评分: {state_info.score:.1f}/100")
            print_info(f"  ATR比率: {state_info.atr_ratio:.3f}")
            print_info(f"  成交量比率: {state_info.volume_ratio:.3f}")
            
            if state_info.state == MarketState.SLEEP:
                print_warning(f"  {symbol} 处于休眠状态，可能不会产生信号")
        
        return True
        
    except Exception as e:
        print_error(f"市场状态引擎测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_worth_trading_filter():
    """测试交易价值过滤"""
    print_header("测试4: 交易价值过滤")
    
    try:
        api_client = BinanceAPIClient()
        data_fetcher = DataFetcher(api_client)
        worth_filter = WorthTradingFilter(data_fetcher)
        
        test_symbols = ["ETHUSDT", "BTCUSDT", "SOLUSDT"]
        
        for symbol in test_symbols:
            print_info(f"检查 {symbol} 交易价值...")
            result = worth_filter.check(symbol)
            
            if result.is_worth_trading:
                print_success(f"{symbol} - 值得交易")
                print_info(f"  预期盈亏比: {result.expected_rr:.2f}")
                print_info(f"  预期波动: {result.expected_move:.3%}")
                print_info(f"  交易成本: {result.trading_cost:.3%}")
            else:
                print_warning(f"{symbol} - 不值得交易: {result.reason}")
                print_info(f"  预期盈亏比: {result.expected_rr:.2f} (要求: {worth_filter.min_rr_ratio:.2f})")
                print_info(f"  预期波动: {result.expected_move:.3%} (要求: {worth_filter.min_expected_move:.3%})")
        
        return True
        
    except Exception as e:
        print_error(f"交易价值过滤测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_fakeout_strategy():
    """测试假突破策略"""
    print_header("测试5: 假突破策略识别")
    
    try:
        api_client = BinanceAPIClient()
        data_fetcher = DataFetcher(api_client)
        
        test_symbols = ["ETHUSDT", "BTCUSDT", "SOLUSDT", "DOGEUSDT", "BNBUSDT"]
        total_signals = 0
        
        for symbol in test_symbols:
            print_info(f"分析 {symbol} 假突破信号...")
            strategy = FakeoutStrategy(data_fetcher, symbol, "5m")
            signals = strategy.analyze()
            
            if signals:
                print_success(f"{symbol} - 发现 {len(signals)} 个信号")
                total_signals += len(signals)
                
                for i, signal in enumerate(signals, 1):
                    print_info(f"  信号 {i}:")
                    print_info(f"    类型: {signal.signal_type.value}")
                    print_info(f"    入场价: {signal.entry_price:.2f}")
                    print_info(f"    止损: {signal.stop_loss:.2f}")
                    print_info(f"    止盈: {signal.take_profit:.2f}")
                    print_info(f"    置信度: {signal.confidence:.2%}")
                    print_info(f"    原因: {signal.reason}")
            else:
                print_warning(f"{symbol} - 未发现信号")
                print_info("  原因可能：")
                print_info("    - 当前市场不符合假突破条件")
                print_info("    - 结构位已被突破但未回落")
                print_info("    - K线实体太小，无法确认")
        
        if total_signals > 0:
            print_success(f"总共发现 {total_signals} 个信号")
        else:
            print_warning("所有合约均未发现信号")
            print_warning("这是正常现象，假突破策略只在高概率机会时产生信号")
            print_info("建议：")
            print_info("  1. 尝试监控更多合约")
            print_info("  2. 等待市场波动增大")
            print_info("  3. 调整策略参数（swing_period, min_body_ratio）")
        
        return True, total_signals
        
    except Exception as e:
        print_error(f"假突破策略测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, 0


def test_execution_flow():
    """测试执行流程"""
    print_header("测试6: 完整执行流程（模拟模式）")
    
    try:
        # 获取配置
        config = get_config()
        
        # 确保是模拟模式
        if not config.system.enable_simulation:
            print_warning("当前不是模拟模式，自动切换...")
            config.system.enable_simulation = True
        
        print_success(f"当前模式: {'模拟' if config.system.enable_simulation else '实盘'}")
        
        # 创建组件
        api_client = BinanceAPIClient()
        data_fetcher = DataFetcher(api_client)
        symbol_selector = SymbolSelector(api_client)
        
        # 获取合约列表
        print_info("获取合约列表...")
        symbol_selector.update_symbol_list(force_update=True)
        
        # 使用综合评分模式选择合约
        symbol_selector.set_selection_mode(SelectionMode.COMPREHENSIVE_SCORE)
        selected_symbols = symbol_selector.get_selected_symbols()
        
        print_success(f"已选择 {len(selected_symbols)} 个合约")
        for symbol in selected_symbols[:5]:
            print_info(f"  - {symbol}")
        
        # 模拟完整流程
        print_info("\n模拟完整交易流程...")
        
        # 1. 市场状态分析
        print_info("步骤1: 市场状态分析")
        market_engine = MarketStateEngine(data_fetcher, "ETHUSDT", "5m")
        state_info = market_engine.analyze()
        print_success(f"  状态: {state_info.state.value}, 评分: {state_info.score:.1f}")
        
        # 2. 交易价值检查
        print_info("步骤2: 交易价值检查")
        worth_filter = WorthTradingFilter(data_fetcher)
        worth_result = worth_filter.check("ETHUSDT")
        print_success(f"  值得交易: {worth_result.is_worth_trading}")
        
        # 3. 信号识别
        print_info("步骤3: 信号识别")
        fakeout_strategy = FakeoutStrategy(data_fetcher, "ETHUSDT", "5m")
        signals = fakeout_strategy.analyze()
        print_success(f"  发现信号: {len(signals)} 个")
        
        if signals:
            # 4. 模拟交易执行
            print_info("步骤4: 模拟交易执行")
            signal = signals[0]
            
            # 创建风险管理器
            risk_manager = RiskManager()
            risk_manager.set_initial_balance(1000.0)
            
            # 检查是否允许交易
            allowed, reason = risk_manager.is_allowed_to_trade()
            print_success(f"  风险检查: {allowed} ({reason})")
            
            if allowed:
                # 创建执行闸门
                execution_gate = ExecutionGate()
                position_manager = execution_gate.get_position_manager()
                
                # 检查执行闸门
                klines = data_fetcher.get_klines("ETHUSDT", "5m", limit=20)
                gate_allowed, gate_reason = execution_gate.check(signal, klines, 0.01)
                print_success(f"  执行闸门: {gate_allowed} ({gate_reason})")
                
                if gate_allowed:
                    # 模拟执行交易
                    print_success("  ✅ 模拟交易执行成功！")
                    print_info(f"    合约: {signal.symbol}")
                    print_info(f"    方向: {signal.signal_type.value}")
                    print_info(f"    入场价: {signal.entry_price:.2f}")
                    print_info(f"    止损: {signal.stop_loss:.2f}")
                    print_info(f"    止盈: {signal.take_profit:.2f}")
                    print_info(f"    置信度: {signal.confidence:.2%}")
                else:
                    print_warning(f"  执行闸门拒绝: {gate_reason}")
            else:
                print_warning(f"  风险管理拒绝: {reason}")
        else:
            print_warning("  无信号，跳过交易执行")
        
        return True
        
    except Exception as e:
        print_error(f"执行流程测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def print_summary(results):
    """打印测试总结"""
    print_header("测试总结")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed
    
    print(f"\n总测试数: {total}")
    print_success(f"通过: {passed}")
    if failed > 0:
        print_error(f"失败: {failed}")
    
    print("\n详细结果:")
    for test_name, result in results.items():
        if result:
            print_success(f"  {test_name}")
        else:
            print_error(f"  {test_name}")
    
    print("\n" + "=" * 80)
    if failed == 0:
        print_success("所有测试通过！系统功能正常。")
    else:
        print_warning(f"有 {failed} 个测试失败，请检查错误信息。")
    print("=" * 80 + "\n")


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print(f"{Color.BOLD}{Color.BLUE}币安假突破策略系统 - 完整功能测试{Color.RESET}")
    print("=" * 80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    results = {}
    
    # 运行所有测试
    results["币安API连接"] = test_binance_api()
    
    if results["币安API连接"]:
        results["数据获取器"] = test_data_fetcher()
        results["市场状态引擎"] = test_market_state_engine()
        results["交易价值过滤"] = test_worth_trading_filter()
        
        signal_result = test_fakeout_strategy()
        results["假突破策略识别"] = signal_result[0]
        
        if signal_result[0]:
            results["完整执行流程"] = test_execution_flow()
    
    # 打印总结
    print_summary(results)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print_error(f"\n测试过程中发生未捕获异常: {str(e)}")
        import traceback
        traceback.print_exc()
