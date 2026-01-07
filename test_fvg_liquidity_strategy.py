#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FVG和流动性策略测试脚本
测试FVG策略和流动性分析器的基本功能
"""

import sys
from binance_api_client import BinanceAPIClient
from data_fetcher import DataFetcher
from fvg_strategy import FVGStrategy, FVGStrategyConfig
from liquidity_analyzer import LiquidityAnalyzer, LiquidityAnalysisConfig
from fvg_signal import FVGType, LiquidityType


class Color:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(title: str):
    """打印标题"""
    print("\n" + "=" * 80)
    print(f"{Color.BOLD}{Color.BLUE}{title}{Color.RESET}")
    print("=" * 80 + "\n")


def print_success(text: str):
    """打印成功信息"""
    print(f"{Color.GREEN}✓ {text}{Color.RESET}")


def print_error(text: str):
    """打印错误信息"""
    print(f"{Color.RED}✗ {text}{Color.RESET}")


def print_warning(text: str):
    """打印警告信息"""
    print(f"{Color.YELLOW}⚠ {text}{Color.RESET}")


def print_info(text: str):
    """打印信息"""
    print(f"  {text}")


def test_fvg_strategy(symbol: str = "ETHUSDT", timeframe: str = "5m"):
    """测试FVG策略"""
    print_header(f"测试FVG策略 - {symbol} ({timeframe})")

    try:
        # 初始化
        client = BinanceAPIClient()
        fetcher = DataFetcher(client)
        fetcher.interval = timeframe

        # 配置
        config = FVGStrategyConfig(
            min_fvg_size_percent=0.0005,  # 最小FVG大小 0.05%
            max_fvg_age_minutes=60,        # 最大FVG年龄 60分钟
            fvg_lookback=100,              # 回溯100根K线
            min_risk_reward=2.0            # 最小盈亏比 2.0
        )

        strategy = FVGStrategy(fetcher, symbol, config)

        # 测试1: 识别FVG
        print_info("步骤1: 识别FVG缺口...")
        fvgs = strategy.identify_fvgs(timeframe)

        if fvgs:
            print_success(f"发现 {len(fvgs)} 个FVG缺口")

            # 显示前5个FVG
            print_info("前5个FVG详情：")
            for i, fvg in enumerate(fvgs[:5]):
                type_str = "看涨" if fvg.gap_type == FVGType.BULLISH else "看跌"
                status_str = "已填充" if fvg.is_filled else "活跃"
                print_info(f"  {i+1}. [{type_str}] {fvg.high_bound:.2f} - {fvg.low_bound:.2f} "
                           f"(大小: {fvg.size_percent:.3f}%, 状态: {status_str})")
        else:
            print_warning("未发现FVG缺口")

        # 测试2: 生成信号
        print_info("\n步骤2: 生成FVG交易信号...")
        signals = strategy.generate_fvg_signals(timeframe)

        if signals:
            print_success(f"生成 {len(signals)} 个FVG信号")

            # 显示前3个信号
            print_info("前3个信号详情：")
            for i, signal in enumerate(signals[:3]):
                print_info(f"  {i+1}. {signal.signal_type.value}")
                print_info(f"     入场: {signal.entry_price:.2f}")
                print_info(f"     止损: {signal.stop_loss:.2f}")
                print_info(f"     止盈: {signal.take_profit:.2f}")
                print_info(f"     盈亏比: {signal.risk_reward_ratio:.2f}")
                print_info(f"     置信度: {signal.confidence:.2f}")
                print_info(f"     原因: {signal.reason}")
                print()
        else:
            print_warning("未生成FVG信号")

        return True

    except Exception as e:
        print_error(f"FVG策略测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_liquidity_analyzer(symbol: str = "ETHUSDT", timeframe: str = "5m"):
    """测试流动性分析器"""
    print_header(f"测试流动性分析器 - {symbol} ({timeframe})")

    try:
        # 初始化
        client = BinanceAPIClient()
        fetcher = DataFetcher(client)
        fetcher.interval = timeframe

        # 配置
        config = LiquidityAnalysisConfig(
            swing_lookback=20,              # 摆动点回溯20根K线
            swing_threshold=0.001,          # 摆动点阈值 0.1%
            liquidity_threshold=0.001,     # 流动性阈值 0.1%
            sweep_threshold_percent=0.0003, # 捕取阈值 0.03%
            sweep_retreat_percent=0.0005   # 回落阈值 0.05%
        )

        analyzer = LiquidityAnalyzer(fetcher, symbol, config)

        # 测试1: 识别摆动点
        print_info("步骤1: 识别摆动点...")
        swing_highs, swing_lows = analyzer.identify_swing_points(timeframe)

        print_success(f"摆动高点: {len(swing_highs)} 个")
        print_success(f"摆动低点: {len(swing_lows)} 个")

        # 测试2: 识别流动性区
        print_info("\n步骤2: 识别流动性区...")

        buyside_zones = analyzer.identify_buyside_liquidity(timeframe)
        sellside_zones = analyzer.identify_sellside_liquidity(timeframe)

        print_success(f"买方流动性区: {len(buyside_zones)} 个")
        if buyside_zones:
            print_info("前3个买方流动性区：")
            for i, zone in enumerate(buyside_zones[:3]):
                swept_str = "已扫过" if zone.is_swept else "活跃"
                print_info(f"  {i+1}. 价格: {zone.level:.2f}, "
                           f"强度: {zone.strength:.2f}, "
                           f"触摸次数: {zone.touched_count}, "
                           f"状态: {swept_str}")

        print_success(f"卖方流动性区: {len(sellside_zones)} 个")
        if sellside_zones:
            print_info("前3个卖方流动性区：")
            for i, zone in enumerate(sellside_zones[:3]):
                swept_str = "已扫过" if zone.is_swept else "活跃"
                print_info(f"  {i+1}. 价格: {zone.level:.2f}, "
                           f"强度: {zone.strength:.2f}, "
                           f"触摸次数: {zone.touched_count}, "
                           f"状态: {swept_str}")

        # 测试3: 生成流动性捕取信号
        print_info("\n步骤3: 生成流动性捕取信号...")
        signals = analyzer.generate_liquidity_sweep_signals(timeframe)

        if signals:
            print_success(f"生成 {len(signals)} 个流动性捕取信号")

            # 显示前3个信号
            print_info("前3个信号详情：")
            for i, signal in enumerate(signals[:3]):
                print_info(f"  {i+1}. {signal.signal_type.value}")
                print_info(f"     入场: {signal.entry_price:.2f}")
                print_info(f"     止损: {signal.stop_loss:.2f}")
                print_info(f"     止盈: {signal.take_profit:.2f}")
                print_info(f"     盈亏比: {signal.risk_reward_ratio:.2f}")
                print_info(f"     置信度: {signal.confidence:.2f}")
                print_info(f"     原因: {signal.reason}")
                print()
        else:
            print_warning("未生成流动性捕取信号")

        return True

    except Exception as e:
        print_error(f"流动性分析器测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_symbols(symbols: list):
    """测试多个交易对"""
    print_header(f"测试多个交易对")

    results = {}

    for symbol in symbols:
        print_info(f"分析 {symbol}...")

        # 测试FVG策略
        try:
            client = BinanceAPIClient()
            fetcher = DataFetcher(client)
            fetcher.interval = "5m"

            strategy = FVGStrategy(fetcher, symbol)
            fvgs = strategy.identify_fvgs("5m")
            signals = strategy.generate_fvg_signals("5m")

            results[symbol] = {
                "fvg_count": len(fvgs),
                "signal_count": len(signals),
                "status": "成功"
            }

            print_success(f"{symbol}: FVG {len(fvgs)}, 信号 {len(signals)}")

        except Exception as e:
            results[symbol] = {
                "status": "失败",
                "error": str(e)
            }
            print_error(f"{symbol}: {str(e)}")

    # 总结
    print_header("测试总结")
    print_info("交易对分析结果：\n")

    for symbol, result in results.items():
        if result["status"] == "成功":
            print_success(f"{symbol}: FVG {result['fvg_count']}, 信号 {result['signal_count']}")
        else:
            print_error(f"{symbol}: {result['error']}")

    print()


def main():
    """主函数"""
    print_header("FVG和流动性策略测试工具")

    # 测试配置
    test_symbol = "ETHUSDT"
    test_timeframe = "5m"
    test_symbols = ["ETHUSDT", "BTCUSDT", "SOLUSDT"]

    # 测试1: FVG策略
    print(f"{Color.BOLD}测试 1: FVG策略{Color.RESET}\n")
    fvg_success = test_fvg_strategy(test_symbol, test_timeframe)

    # 测试2: 流动性分析器
    print(f"\n{Color.BOLD}测试 2: 流动性分析器{Color.RESET}\n")
    liquidity_success = test_liquidity_analyzer(test_symbol, test_timeframe)

    # 测试3: 多个交易对
    print(f"\n{Color.BOLD}测试 3: 多个交易对{Color.RESET}\n")
    test_multiple_symbols(test_symbols)

    # 总结
    print_header("测试完成")

    if fvg_success and liquidity_success:
        print_success("所有核心测试通过！")
        print_info("FVG策略和流动性分析器已准备就绪")
        print_info("可以开始下一步：多周期分析器和策略系统集成")
    else:
        print_error("部分测试失败，请检查错误信息")

    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_warning("\n\n测试被用户中断")
    except Exception as e:
        print_error(f"\n测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
