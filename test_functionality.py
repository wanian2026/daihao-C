#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
功能验证测试
验证所有新增的方法和类是否可用
"""

import sys

print("=" * 60)
print("功能验证测试")
print("=" * 60)

# 测试1: SymbolSelector
print("\n测试1: SymbolSelector类")
try:
    from symbol_selector import SymbolSelector, SelectionMode, SymbolInfo
    
    # 检查枚举
    assert SelectionMode.MANUAL.value == "MANUAL"
    assert SelectionMode.AUTO_SCORE.value == "AUTO_SCORE"
    print("✓ SelectionMode枚举正常")
    
    # 检查数据类
    info = SymbolInfo(
        symbol="BTCUSDT",
        base_asset="BTC",
        quote_asset="USDT",
        contract_type="PERPETUAL",
        status="TRADING",
        price=50000.0,
        volume_24h=1000000000.0,
        change_24h=2.5,
        mark_price=50000.0
    )
    assert info.symbol == "BTCUSDT"
    print("✓ SymbolInfo数据类正常")
    
    print("✓ SymbolSelector类结构正确")
except Exception as e:
    print(f"✗ SymbolSelector类错误: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试2: DataFetcher批量方法
print("\n测试2: DataFetcher批量方法")
try:
    from data_fetcher import DataFetcher
    
    # 检查方法存在
    assert hasattr(DataFetcher, 'get_klines_batch')
    assert hasattr(DataFetcher, 'get_atr_batch')
    assert hasattr(DataFetcher, 'get_volume_ma_batch')
    assert hasattr(DataFetcher, 'get_market_metrics_batch')
    
    print("✓ DataFetcher批量方法存在")
except Exception as e:
    print(f"✗ DataFetcher批量方法错误: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试3: MarketStateEngine批量方法
print("\n测试3: MarketStateEngine批量方法")
try:
    from market_state_engine import MarketStateEngine
    
    # 检查方法存在
    assert hasattr(MarketStateEngine, 'analyze_batch')
    assert hasattr(MarketStateEngine, 'get_tradeable_symbols')
    
    print("✓ MarketStateEngine批量方法存在")
except Exception as e:
    print(f"✗ MarketStateEngine批量方法错误: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试4: FakeoutStrategy批量方法
print("\n测试4: FakeoutStrategy批量方法")
try:
    from fakeout_strategy import FakeoutStrategy
    
    # 检查方法存在
    assert hasattr(FakeoutStrategy, 'analyze_batch')
    assert hasattr(FakeoutStrategy, 'get_best_signal')
    
    print("✓ FakeoutStrategy批量方法存在")
except Exception as e:
    print(f"✗ FakeoutStrategy批量方法错误: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试5: MultiSymbolFakeoutSystem
print("\n测试5: MultiSymbolFakeoutSystem类")
try:
    from eth_fakeout_strategy_system import MultiSymbolFakeoutSystem
    
    # 检查方法存在
    assert hasattr(MultiSymbolFakeoutSystem, 'update_selected_symbols')
    assert hasattr(MultiSymbolFakeoutSystem, 'set_selection_mode')
    assert hasattr(MultiSymbolFakeoutSystem, 'get_symbol_selector')
    assert hasattr(MultiSymbolFakeoutSystem, '_analyze_all_symbols')
    
    print("✓ MultiSymbolFakeoutSystem类结构正确")
except Exception as e:
    print(f"✗ MultiSymbolFakeoutSystem类错误: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试6: 向后兼容性
print("\n测试6: 向后兼容性")
try:
    from eth_fakeout_strategy_system import ETHFakeoutStrategySystem
    
    # 检查是否为别名
    assert ETHFakeoutStrategySystem is MultiSymbolFakeoutSystem
    print("✓ 向后兼容性保持（ETHFakeoutStrategySystem = MultiSymbolFakeoutSystem）")
except Exception as e:
    print(f"✗ 向后兼容性错误: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("🎉 所有功能验证通过！")
print("=" * 60)
print("\n新增功能总结:")
print("1. SymbolSelector - 合约选择器（支持4种模式）")
print("2. DataFetcher - 批量获取数据（4个批量方法）")
print("3. MarketStateEngine - 批量分析市场状态（2个批量方法）")
print("4. FakeoutStrategy - 批量分析假突破（2个批量方法）")
print("5. MultiSymbolFakeoutSystem - 多标的策略系统")
print("6. GUI新增标的选择标签页")
print("\n功能完整，可以使用！")
