#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易价值过滤参数测试工具
用于测试不同参数配置下的交易价值判断
"""

from binance_api_client import BinanceAPIClient
from data_fetcher import DataFetcher
from worth_trading_filter import WorthTradingFilter, WorthTradingResult
from typing import Dict, List


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


def test_parameter_config(
    symbol: str,
    min_rr_ratio: float,
    min_expected_move: float,
    cost_multiplier: float,
    min_atr_ratio: float
) -> WorthTradingResult:
    """
    测试特定参数配置

    Args:
        symbol: 交易对
        min_rr_ratio: 最小盈亏比
        min_expected_move: 最小预期波动
        cost_multiplier: 成本倍数
        min_atr_ratio: 最小ATR比例

    Returns:
        WorthTradingResult
    """
    # 初始化
    client = BinanceAPIClient()
    fetcher = DataFetcher(client)
    filter_engine = WorthTradingFilter(fetcher)

    # 设置参数
    filter_engine.min_rr_ratio = min_rr_ratio
    filter_engine.min_expected_move = min_expected_move
    filter_engine.cost_multiplier = cost_multiplier

    # 检查
    result = filter_engine.check(symbol)

    return result


def compare_configurations(symbol: str):
    """
    比较不同配置的效果

    Args:
        symbol: 交易对
    """
    print_header(f"比较不同参数配置 - {symbol}")

    # 定义不同的配置
    configs = [
        {
            "name": "保守型",
            "min_rr_ratio": 2.5,
            "min_expected_move": 0.006,
            "cost_multiplier": 2.5,
            "min_atr_ratio": 0.012
        },
        {
            "name": "平衡型（默认）",
            "min_rr_ratio": 2.0,
            "min_expected_move": 0.005,
            "cost_multiplier": 2.0,
            "min_atr_ratio": 0.01
        },
        {
            "name": "激进型",
            "min_rr_ratio": 1.5,
            "min_expected_move": 0.003,
            "cost_multiplier": 1.5,
            "min_atr_ratio": 0.006
        }
    ]

    results = []

    for config in configs:
        print_info(f"测试配置: {config['name']}")
        print_info(f"  min_rr_ratio: {config['min_rr_ratio']}")
        print_info(f"  min_expected_move: {config['min_expected_move']*100:.1f}%")
        print_info(f"  cost_multiplier: {config['cost_multiplier']}")
        print_info(f"  min_atr_ratio: {config['min_atr_ratio']*100:.1f}%")

        try:
            result = test_parameter_config(
                symbol,
                config['min_rr_ratio'],
                config['min_expected_move'],
                config['cost_multiplier'],
                config['min_atr_ratio']
            )
            results.append({
                "config": config,
                "result": result
            })

            if result.is_worth_trading:
                print_success(f"值得交易")
                print_info(f"  盈亏比: {result.risk_reward_ratio:.2f} (要求: {config['min_rr_ratio']:.1f})")
                print_info(f"  预期波动: {result.expected_move*100:.2f}% (要求: {config['min_expected_move']*100:.1f}%)")
                print_info(f"  交易成本: {result.total_cost*100:.3f}%")
            else:
                print_warning(f"不值得交易")
                print_info(f"  盈亏比: {result.risk_reward_ratio:.2f} (要求: {config['min_rr_ratio']:.1f})")
                print_info(f"  预期波动: {result.expected_move*100:.2f}% (要求: {config['min_expected_move']*100:.1f}%)")
                print_info(f"  原因: {', '.join(result.reasons)}")
        except Exception as e:
            print_error(f"测试失败: {str(e)}")

        print()

    # 总结
    print_header("总结")
    print_info("配置对比结果：\n")

    for item in results:
        config = item['config']
        result = item['result']

        status = f"{Color.GREEN}✓ 通过{Color.RESET}" if result.is_worth_trading else f"{Color.RED}✗ 未通过{Color.RESET}"
        print_info(f"{config['name']:20s} {status}  盈亏比: {result.risk_reward_ratio:.2f}")

    print()


def test_single_parameter(symbol: str, param_name: str, values: List[float]):
    """
    测试单个参数的影响

    Args:
        symbol: 交易对
        param_name: 参数名
        values: 参数值列表
    """
    print_header(f"测试参数影响: {param_name} - {symbol}")

    # 默认参数
    default_config = {
        "min_rr_ratio": 2.0,
        "min_expected_move": 0.005,
        "cost_multiplier": 2.0,
        "min_atr_ratio": 0.01
    }

    results = []

    for value in values:
        # 更新配置
        config = default_config.copy()
        config[param_name] = value

        print_info(f"测试 {param_name} = {value}")

        try:
            result = test_parameter_config(
                symbol,
                config['min_rr_ratio'],
                config['min_expected_move'],
                config['cost_multiplier'],
                config['min_atr_ratio']
            )

            results.append({
                "value": value,
                "result": result
            })

            if result.is_worth_trading:
                print_success(f"值得交易  盈亏比: {result.risk_reward_ratio:.2f}")
            else:
                print_warning(f"不值得交易  盈亏比: {result.risk_reward_ratio:.2f}")
        except Exception as e:
            print_error(f"测试失败: {str(e)}")

        print()

    # 总结
    print_header("参数影响分析")
    print_info(f"{param_name} 的影响：\n")

    for item in results:
        value = item['value']
        result = item['result']

        status = f"{Color.GREEN}✓{Color.RESET}" if result.is_worth_trading else f"{Color.RED}✗{Color.RESET}"
        print_info(f"{value:6.2f}  {status}  盈亏比: {result.risk_reward_ratio:.2f}  预期波动: {result.expected_move*100:.2f}%")

    print()


def test_multiple_symbols(symbols: List[str], config_name: str = "平衡型"):
    """
    测试多个交易对

    Args:
        symbols: 交易对列表
        config_name: 配置名称
    """
    print_header(f"测试多个交易对 - {config_name}配置")

    # 选择配置
    configs = {
        "保守型": {
            "min_rr_ratio": 2.5,
            "min_expected_move": 0.006,
            "cost_multiplier": 2.5,
            "min_atr_ratio": 0.012
        },
        "平衡型": {
            "min_rr_ratio": 2.0,
            "min_expected_move": 0.005,
            "cost_multiplier": 2.0,
            "min_atr_ratio": 0.01
        },
        "激进型": {
            "min_rr_ratio": 1.5,
            "min_expected_move": 0.003,
            "cost_multiplier": 1.5,
            "min_atr_ratio": 0.006
        }
    }

    config = configs.get(config_name, configs["平衡型"])

    print_info(f"使用配置: {config_name}")
    print_info(f"  min_rr_ratio: {config['min_rr_ratio']}")
    print_info(f"  min_expected_move: {config['min_expected_move']*100:.1f}%")
    print_info(f"  cost_multiplier: {config['cost_multiplier']}")
    print_info(f"  min_atr_ratio: {config['min_atr_ratio']*100:.1f}%")
    print()

    worth_count = 0

    for symbol in symbols:
        print_info(f"检查 {symbol}...")

        try:
            result = test_parameter_config(
                symbol,
                config['min_rr_ratio'],
                config['min_expected_move'],
                config['cost_multiplier'],
                config['min_atr_ratio']
            )

            if result.is_worth_trading:
                worth_count += 1
                print_success(f"{symbol:15s}  值得交易  盈亏比: {result.risk_reward_ratio:.2f}  预期波动: {result.expected_move*100:.2f}%")
            else:
                print_warning(f"{symbol:15s}  不值得交易  盈亏比: {result.risk_reward_ratio:.2f}  原因: {result.reasons[0] if result.reasons else '未知'}")
        except Exception as e:
            print_error(f"{symbol:15s}  测试失败: {str(e)}")

    print()
    print_info(f"总结: {worth_count}/{len(symbols)} 个交易对值得交易")
    print()


def main():
    """主函数"""
    print_header("交易价值过滤参数测试工具")

    # 测试交易对
    symbols = ["ETHUSDT", "BTCUSDT", "SOLUSDT"]

    # 测试 1: 比较不同配置
    print(f"{Color.BOLD}测试 1: 比较不同配置{Color.RESET}\n")
    compare_configurations("ETHUSDT")

    # 测试 2: 测试单个参数影响
    print(f"{Color.BOLD}测试 2: 测试单个参数影响{Color.RESET}\n")
    test_single_parameter("ETHUSDT", "min_rr_ratio", [1.5, 1.8, 2.0, 2.2, 2.5, 3.0])
    test_single_parameter("ETHUSDT", "min_expected_move", [0.003, 0.004, 0.005, 0.006, 0.008])
    test_single_parameter("ETHUSDT", "cost_multiplier", [1.5, 2.0, 2.5, 3.0])

    # 测试 3: 测试多个交易对
    print(f"{Color.BOLD}测试 3: 测试多个交易对{Color.RESET}\n")
    test_multiple_symbols(symbols, "平衡型")

    print_header("测试完成")
    print_info("使用以上测试结果来调整参数配置！")
    print_info("建议：先在模拟模式下测试，确认效果后再切换到实盘模式。\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_warning("\n\n测试被用户中断")
    except Exception as e:
        print_error(f"\n测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
