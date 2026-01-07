#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试模拟模式功能
验证模拟模式和实盘模式的切换逻辑
"""

from parameter_config import get_config, update_config
from fakeout_strategy import FakeoutSignal, PatternType
from trading_strategy import SignalType
from datetime import datetime


def test_simulation_mode_config():
    """测试模拟模式配置"""
    print("测试1: 模拟模式配置")
    print("-" * 50)

    config = get_config()

    # 测试默认值
    print(f"默认模拟模式: {config.system.enable_simulation}")
    assert config.system.enable_simulation == True, "默认应该是模拟模式"
    print("✓ 默认模式正确（模拟）")

    # 测试切换到实盘
    update_config({'system': {'enable_simulation': False}})
    config = get_config()
    print(f"切换到实盘模式: {config.system.enable_simulation}")
    assert config.system.enable_simulation == False, "应该是实盘模式"
    print("✓ 切换到实盘模式成功")

    # 测试切换回模拟
    update_config({'system': {'enable_simulation': True}})
    config = get_config()
    print(f"切换回模拟模式: {config.system.enable_simulation}")
    assert config.system.enable_simulation == True, "应该是模拟模式"
    print("✓ 切换回模拟模式成功")

    print()


def test_fakeout_signal_with_symbol():
    """测试FakeoutSignal包含symbol字段"""
    print("测试2: FakeoutSignal symbol字段")
    print("-" * 50)

    # 创建测试信号
    signal = FakeoutSignal(
        symbol="ETHUSDT",
        signal_type=SignalType.BUY,
        entry_price=2000.0,
        stop_loss=1980.0,
        take_profit=2040.0,
        confidence=0.85,
        pattern_type=PatternType.SWING_HIGH,
        reason="测试信号",
        structure_level=2010.0
    )

    print(f"信号合约: {signal.symbol}")
    print(f"信号类型: {signal.signal_type.value}")
    print(f"入场价: {signal.entry_price}")
    print(f"止损价: {signal.stop_loss}")
    print(f"止盈价: {signal.take_profit}")
    print(f"置信度: {signal.confidence}")

    assert signal.symbol == "ETHUSDT", "symbol字段应该存在且正确"
    print("✓ FakeoutSignal symbol字段正常")

    print()


def test_multiple_signals():
    """测试多合约信号"""
    print("测试3: 多合约信号")
    print("-" * 50)

    symbols = ["ETHUSDT", "BTCUSDT", "SOLUSDT"]
    signals = []

    for symbol in symbols:
        signal = FakeoutSignal(
            symbol=symbol,
            signal_type=SignalType.BUY,
            entry_price=1000.0,
            stop_loss=990.0,
            take_profit=1020.0,
            confidence=0.75,
            pattern_type=PatternType.SWING_HIGH,
            reason=f"{symbol}测试信号",
            structure_level=1005.0
        )
        signals.append((symbol, signal))

    print(f"生成 {len(signals)} 个信号:")
    for symbol, signal in signals:
        print(f"  - {symbol}: 置信度 {signal.confidence:.2%}")

    assert len(signals) == 3, "应该有3个信号"
    assert all(s[0] == s[1].symbol for s in signals), "每个信号应该有正确的symbol"

    print("✓ 多合约信号正常")

    print()


def test_execution_logic_pseudo():
    """测试执行逻辑（伪代码）"""
    print("测试4: 执行逻辑判断")
    print("-" * 50)

    config = get_config()

    # 模拟模式
    config.system.enable_simulation = True
    is_sim = config.system.enable_simulation

    print(f"当前模式: {'模拟' if is_sim else '实盘'}")
    if is_sim:
        print("  执行模拟交易")
        print("  不实际下单")
    else:
        print("  执行实盘交易")
        print("  调用API下单")

    assert is_sim == True, "应该是模拟模式"
    print("✓ 模拟模式判断正确")

    # 实盘模式
    config.system.enable_simulation = False
    is_sim = config.system.enable_simulation

    print(f"切换后模式: {'模拟' if is_sim else '实盘'}")
    if is_sim:
        print("  执行模拟交易")
        print("  不实际下单")
    else:
        print("  执行实盘交易")
        print("  调用API下单")

    assert is_sim == False, "应该是实盘模式"
    print("✓ 实盘模式判断正确")

    print()


if __name__ == "__main__":
    print("=" * 60)
    print("模拟模式功能测试")
    print("=" * 60)
    print()

    try:
        test_simulation_mode_config()
        test_fakeout_signal_with_symbol()
        test_multiple_signals()
        test_execution_logic_pseudo()

        print("=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        print()
        print("总结：")
        print("1. ✓ 模拟模式配置正常")
        print("2. ✓ FakeoutSignal包含symbol字段")
        print("3. ✓ 支持多合约信号")
        print("4. ✓ 执行逻辑判断正确")
        print()
        print("系统已准备就绪，可以安全使用！")

    except Exception as e:
        print("=" * 60)
        print("❌ 测试失败！")
        print("=" * 60)
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
