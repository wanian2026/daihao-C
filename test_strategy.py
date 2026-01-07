#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试策略系统 - 验证程序是否能发现信号
"""

from parameter_config import get_config
from fvg_liquidity_strategy_system import FVGLiquidityStrategySystem
from binance_trading_client import BinanceTradingClient
import time

def test_strategy():
    """测试策略系统"""
    print("=" * 60)
    print("测试FVG流动性策略系统")
    print("=" * 60)
    
    # 1. 检查配置
    print("\n1. 检查配置...")
    config = get_config()
    print(f"  ✓ 周期: {config.fvg_strategy.timeframes}")
    print(f"  ✓ 主周期: {config.fvg_strategy.primary_timeframe}")
    print(f"  ✓ 最小置信度: {config.fvg_strategy.min_confidence}")
    print(f"  ✓ 模拟模式: {config.system.enable_simulation}")
    
    # 2. 初始化策略系统
    print("\n2. 初始化策略系统...")
    try:
        trading_client = BinanceTradingClient()
        strategy = FVGLiquidityStrategySystem(trading_client)
        print("  ✓ 策略系统初始化成功")
    except Exception as e:
        print(f"  ✗ 初始化失败: {e}")
        return
    
    # 3. 设置回调
    def on_signal(signal_info):
        print(f"\n📊 发现信号:")
        print(f"  标的: {signal_info.get('symbol')}")
        print(f"  类型: {signal_info.get('type')}")
        print(f"  入场: {signal_info.get('entry')}")
        print(f"  止损: {signal_info.get('stop_loss')}")
        print(f"  止盈: {signal_info.get('take_profit')}")
        print(f"  置信度: {signal_info.get('confidence')}")
    
    def on_order(order_info):
        print(f"\n💰 订单执行:")
        print(f"  标的: {order_info.get('symbol')}")
        print(f"  类型: {order_info.get('type')}")
    
    strategy.on_signal = on_signal
    strategy.on_order = on_order
    
    # 4. 启动策略
    print("\n3. 启动策略...")
    if strategy.start():
        print("  ✓ 策略已启动")
    else:
        print("  ✗ 策略启动失败")
        return
    
    # 5. 运行60秒，观察信号
    print("\n4. 运行60秒，观察信号发现...")
    print("-" * 60)
    
    for i in range(60):
        time.sleep(1)
        if i % 10 == 0:
            print(f"[{i}s] 运行中...")
    
    # 6. 停止策略
    print("\n5. 停止策略...")
    strategy.stop()
    print("  ✓ 策略已停止")
    
    # 7. 统计信息
    print("\n6. 统计信息:")
    print(f"  总循环次数: {strategy.stats.get('total_loops', 0)}")
    print(f"  发现共振: {strategy.stats.get('confluences_found', 0)}")
    print(f"  执行交易: {strategy.stats.get('trades_executed', 0)}")
    print(f"  分析标的: {strategy.stats.get('symbols_analyzed', 0)}")
    print(f"  分析周期: {strategy.stats.get('timeframes_analyzed', 0)}")
    print(f"  跳过次数:")
    for key, value in strategy.stats.get('skips', {}).items():
        if value > 0:
            print(f"    - {key}: {value}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_strategy()
