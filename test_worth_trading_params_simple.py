#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易价值过滤参数测试工具（离线版本）
使用模拟数据演示参数调整的影响
"""

from dataclasses import dataclass
from typing import List
from datetime import datetime


class Color:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


@dataclass
class MockWorthTradingResult:
    """模拟的值得交易结果"""
    is_worth_trading: bool
    risk_reward_ratio: float
    expected_move: float
    reasons: List[str]


def print_header(title: str):
    """打印标题"""
    print("\n" + "=" * 80)
    print(f"{Color.BOLD}{Color.BLUE}{title}{Color.RESET}")
    print("=" * 80 + "\n")


def print_success(text: str):
    """打印成功信息"""
    print(f"{Color.GREEN}✓ {text}{Color.RESET}")


def print_warning(text: str):
    """打印警告信息"""
    print(f"{Color.YELLOW}⚠ {text}{Color.RESET}")


def print_info(text: str):
    """打印信息"""
    print(f"  {text}")


def simulate_worth_check(
    risk_reward_ratio: float,
    expected_move: float,
    min_rr_ratio: float,
    min_expected_move: float,
    cost_multiplier: float,
    total_cost: float = 0.0015  # 假设总成本为 0.15%
) -> MockWorthTradingResult:
    """
    模拟交易价值检查

    Args:
        risk_reward_ratio: 实际盈亏比
        expected_move: 实际预期波动
        min_rr_ratio: 最小盈亏比要求
        min_expected_move: 最小预期波动要求
        cost_multiplier: 成本倍数
        total_cost: 交易成本

    Returns:
        MockWorthTradingResult
    """
    reasons = []

    # 检查 1: 盈亏比
    if risk_reward_ratio < min_rr_ratio:
        reasons.append(f"盈亏比不足 ({risk_reward_ratio:.2f} < {min_rr_ratio:.1f})")

    # 检查 2: 预期波动
    if expected_move < min_expected_move:
        reasons.append(f"预期波动不足 ({expected_move*100:.2f}% < {min_expected_move*100:.1f}%)")

    # 检查 3: 成本倍数
    if expected_move < total_cost * cost_multiplier:
        reasons.append(f"预期波动不足以覆盖成本 ({expected_move*100:.2f}% < {total_cost*cost_multiplier*100:.2f}%)")

    is_worth = len(reasons) == 0

    return MockWorthTradingResult(
        is_worth_trading=is_worth,
        risk_reward_ratio=risk_reward_ratio,
        expected_move=expected_move,
        reasons=reasons
    )


def compare_configurations():
    """
    比较不同配置的效果
    """
    print_header("比较不同参数配置")

    # 模拟市场数据
    market_data = {
        "ETHUSDT": {
            "risk_reward_ratio": 2.35,
            "expected_move": 0.0085  # 0.85%
        },
        "BTCUSDT": {
            "risk_reward_ratio": 1.85,
            "expected_move": 0.0065  # 0.65%
        },
        "SOLUSDT": {
            "risk_reward_ratio": 2.60,
            "expected_move": 0.0120  # 1.20%
        }
    }

    # 定义不同的配置
    configs = [
        {
            "name": "保守型",
            "min_rr_ratio": 2.5,
            "min_expected_move": 0.006,
            "cost_multiplier": 2.5
        },
        {
            "name": "平衡型（默认）",
            "min_rr_ratio": 2.0,
            "min_expected_move": 0.005,
            "cost_multiplier": 2.0
        },
        {
            "name": "激进型",
            "min_rr_ratio": 1.5,
            "min_expected_move": 0.003,
            "cost_multiplier": 1.5
        }
    ]

    # 测试每个交易对
    for symbol, data in market_data.items():
        print(f"{Color.BOLD}交易对: {symbol}{Color.RESET}")
        print(f"  实际盈亏比: {data['risk_reward_ratio']:.2f}")
        print(f"  实际预期波动: {data['expected_move']*100:.2f}%")
        print()

        for config in configs:
            print_info(f"{config['name']:15s} - min_rr_ratio: {config['min_rr_ratio']:.1f}, min_expected_move: {config['min_expected_move']*100:.1f}%")

            result = simulate_worth_check(
                risk_reward_ratio=data['risk_reward_ratio'],
                expected_move=data['expected_move'],
                min_rr_ratio=config['min_rr_ratio'],
                min_expected_move=config['min_expected_move'],
                cost_multiplier=config['cost_multiplier']
            )

            if result.is_worth_trading:
                print_success(f"值得交易  盈亏比: {result.risk_reward_ratio:.2f}")
            else:
                print_warning(f"不值得交易  原因: {', '.join(result.reasons)}")

        print()


def test_single_parameter():
    """
    测试单个参数的影响
    """
    print_header("测试单个参数的影响")

    # 模拟市场数据
    market_rr = 2.35  # 实际盈亏比
    market_move = 0.0085  # 实际预期波动 0.85%

    print_info(f"市场数据: 盈亏比={market_rr:.2f}, 预期波动={market_move*100:.2f}%")
    print()

    # 测试 min_rr_ratio 的影响
    print(f"{Color.BOLD}参数 1: min_rr_ratio（最小盈亏比）{Color.RESET}\n")

    rr_values = [1.5, 1.8, 2.0, 2.2, 2.5, 3.0]
    print_info(f"{'参数值':>8s}  {'结果':>8s}  {'实际盈亏比':>12s}  {'要求盈亏比':>12s}")
    print_info("-" * 50)

    for value in rr_values:
        result = simulate_worth_check(
            risk_reward_ratio=market_rr,
            expected_move=market_move,
            min_rr_ratio=value,
            min_expected_move=0.005,
            cost_multiplier=2.0
        )

        status = "✓ 通过" if result.is_worth_trading else "✗ 未通过"
        print_info(f"{value:8.2f}  {status:>8s}  {market_rr:12.2f}  {value:12.2f}")

    print()
    print()

    # 测试 min_expected_move 的影响
    print(f"{Color.BOLD}参数 2: min_expected_move（最小预期波动）{Color.RESET}\n")

    move_values = [0.003, 0.004, 0.005, 0.006, 0.008, 0.010]
    print_info(f"{'参数值':>10s}  {'结果':>8s}  {'实际波动':>12s}  {'要求波动':>12s}")
    print_info("-" * 50)

    for value in move_values:
        result = simulate_worth_check(
            risk_reward_ratio=market_rr,
            expected_move=market_move,
            min_rr_ratio=2.0,
            min_expected_move=value,
            cost_multiplier=2.0
        )

        status = "✓ 通过" if result.is_worth_trading else "✗ 未通过"
        print_info(f"{value*100:8.2f}%  {status:>8s}  {market_move*100:10.2f}%  {value*100:10.2f}%")

    print()
    print()

    # 测试 cost_multiplier 的影响
    print(f"{Color.BOLD}参数 3: cost_multiplier（成本倍数）{Color.RESET}\n")

    multiplier_values = [1.5, 2.0, 2.5, 3.0]
    total_cost = 0.0015  # 0.15%

    print_info(f"交易成本: {total_cost*100:.3f}%")
    print()
    print_info(f"{'参数值':>8s}  {'结果':>8s}  {'实际波动':>12s}  {'最小要求波动':>12s}")
    print_info("-" * 50)

    for value in multiplier_values:
        result = simulate_worth_check(
            risk_reward_ratio=market_rr,
            expected_move=market_move,
            min_rr_ratio=2.0,
            min_expected_move=0.005,
            cost_multiplier=value
        )

        min_required = total_cost * value
        status = "✓ 通过" if result.is_worth_trading else "✗ 未通过"
        print_info(f"{value:8.2f}  {status:>8s}  {market_move*100:10.2f}%  {min_required*100:10.2f}%")

    print()


def demonstrate_parameter_tuning():
    """
    演示参数调优过程
    """
    print_header("参数调优演示")

    # 场景：市场波动降低
    market_rr = 1.85  # 盈亏比降低
    market_move = 0.0065  # 预期波动降低

    print_info("场景：市场波动降低")
    print_info(f"  当前盈亏比: {market_rr:.2f}（之前: 2.35）")
    print_info(f"  当前预期波动: {market_move*100:.2f}%（之前: 0.85%）")
    print()

    # 默认配置（平衡型）
    default_config = {
        "min_rr_ratio": 2.0,
        "min_expected_move": 0.005,
        "cost_multiplier": 2.0
    }

    print_info("使用默认配置（平衡型）:")
    result1 = simulate_worth_check(
        risk_reward_ratio=market_rr,
        expected_move=market_move,
        min_rr_ratio=default_config['min_rr_ratio'],
        min_expected_move=default_config['min_expected_move'],
        cost_multiplier=default_config['cost_multiplier']
    )

    if result1.is_worth_trading:
        print_success(f"值得交易  盈亏比: {result1.risk_reward_ratio:.2f}")
    else:
        print_warning(f"不值得交易  原因: {', '.join(result1.reasons)}")

    print()

    # 调整后的配置
    print_info("调整后配置（降低要求）:")
    adjusted_config = {
        "min_rr_ratio": 1.8,
        "min_expected_move": 0.004,
        "cost_multiplier": 1.8
    }

    print_info(f"  min_rr_ratio: {default_config['min_rr_ratio']:.1f} → {adjusted_config['min_rr_ratio']:.1f}")
    print_info(f"  min_expected_move: {default_config['min_expected_move']*100:.1f}% → {adjusted_config['min_expected_move']*100:.1f}%")
    print_info(f"  cost_multiplier: {default_config['cost_multiplier']:.1f} → {adjusted_config['cost_multiplier']:.1f}")
    print()

    result2 = simulate_worth_check(
        risk_reward_ratio=market_rr,
        expected_move=market_move,
        min_rr_ratio=adjusted_config['min_rr_ratio'],
        min_expected_move=adjusted_config['min_expected_move'],
        cost_multiplier=adjusted_config['cost_multiplier']
    )

    if result2.is_worth_trading:
        print_success(f"值得交易  盈亏比: {result2.risk_reward_ratio:.2f}")
    else:
        print_warning(f"不值得交易  原因: {', '.join(result2.reasons)}")

    print()
    print()


def main():
    """主函数"""
    print_header("交易价值过滤参数测试工具（离线版）")

    # 测试 1: 比较不同配置
    compare_configurations()

    # 测试 2: 测试单个参数影响
    test_single_parameter()

    # 测试 3: 参数调优演示
    demonstrate_parameter_tuning()

    print_header("测试完成")
    print_info("以上测试演示了参数调整对交易价值判断的影响")
    print_info(f"建议：{Color.BOLD}{Color.GREEN}从平衡型配置开始，根据实际效果微调{Color.RESET}")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_warning("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
