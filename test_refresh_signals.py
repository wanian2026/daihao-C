#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试信号刷新功能
"""

from fakeout_strategy import FakeoutSignal, SignalType, PatternType
from datetime import datetime

# 模拟策略系统
class MockStrategySystem:
    def __init__(self):
        self.symbol_signals = {
            'ETHUSDT': [
                FakeoutSignal(
                    symbol='ETHUSDT',
                    signal_type=SignalType.BUY,
                    entry_price=1000.0,
                    stop_loss=990.0,
                    take_profit=1020.0,
                    confidence=0.8,
                    pattern_type=PatternType.SWING_HIGH,
                    reason='高点假突破',
                    structure_level=1010.0
                )
            ],
            'BTCUSDT': [
                FakeoutSignal(
                    symbol='BTCUSDT',
                    signal_type=SignalType.SELL,
                    entry_price=20000.0,
                    stop_loss=20100.0,
                    take_profit=19800.0,
                    confidence=0.75,
                    pattern_type=PatternType.SWING_LOW,
                    reason='低点假突破',
                    structure_level=19900.0
                ),
                FakeoutSignal(
                    symbol='BTCUSDT',
                    signal_type=SignalType.BUY,
                    entry_price=19950.0,
                    stop_loss=19850.0,
                    take_profit=20150.0,
                    confidence=0.7,
                    pattern_type=PatternType.SWING_HIGH,
                    reason='高点假突破',
                    structure_level=20050.0
                )
            ]
        }

# 模拟 refresh_signals 方法
def refresh_signals(strategy_system):
    """模拟 GUI 的 refresh_signals 方法"""
    if not strategy_system:
        print("策略系统不存在")
        return

    # 获取所有合约的最新信号
    all_signals = []
    symbol_signals = strategy_system.symbol_signals

    print(f"symbol_signals 内容: {symbol_signals}")
    print(f"symbol_signals 类型: {type(symbol_signals)}")
    print(f"symbol_signals 长度: {len(symbol_signals)}")
    print()

    # 收集所有合约的信号
    for symbol, signals in symbol_signals.items():
        print(f"处理合约: {symbol}")
        print(f"  信号数量: {len(signals)}")
        for signal in signals:
            print(f"  信号详情:")
            print(f"    合约: {signal.symbol}")
            print(f"    类型: {signal.signal_type.value}")
            print(f"    入场价: {signal.entry_price:.2f}")
            print(f"    止损: {signal.stop_loss:.2f}")
            print(f"    止盈: {signal.take_profit:.2f}")
            print(f"    置信度: {signal.confidence:.2f}")
            print(f"    原因: {signal.reason}")
            all_signals.append((symbol, signal))
        print()

    print(f"总信号数量: {len(all_signals)}")
    print()

    # 模拟显示信号
    print("模拟显示信号到表格:")
    for symbol, signal in all_signals:
        values = (
            symbol,  # 合约名称
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            signal.signal_type.value,
            f"{signal.entry_price:.2f}",
            f"{signal.stop_loss:.2f}",
            f"{signal.take_profit:.2f}",
            f"{signal.confidence:.2f}",
            signal.reason
        )
        print(f"  {values}")
    print()

# 测试空的情况
print("=" * 60)
print("测试 1: symbol_signals 为空")
print("=" * 60)
empty_system = MockStrategySystem()
empty_system.symbol_signals = {}
refresh_signals(empty_system)

# 测试有数据的情况
print("=" * 60)
print("测试 2: symbol_signals 有数据")
print("=" * 60)
system_with_data = MockStrategySystem()
refresh_signals(system_with_data)

# 测试 None 的情况
print("=" * 60)
print("测试 3: 策略系统为 None")
print("=" * 60)
refresh_signals(None)

print()
print("所有测试完成！")
