#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单导入测试
"""

import sys

print("测试模块导入...")

try:
    from symbol_selector import SymbolSelector, SelectionMode
    print("✓ symbol_selector 导入成功")
except Exception as e:
    print(f"✗ symbol_selector 导入失败: {str(e)}")
    sys.exit(1)

try:
    from data_fetcher import DataFetcher
    print("✓ data_fetcher 导入成功")
except Exception as e:
    print(f"✗ data_fetcher 导入失败: {str(e)}")
    sys.exit(1)

try:
    from market_state_engine import MarketStateEngine, MarketState
    print("✓ market_state_engine 导入成功")
except Exception as e:
    print(f"✗ market_state_engine 导入失败: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from fakeout_strategy import FakeoutStrategy
    print("✓ fakeout_strategy 导入成功")
except Exception as e:
    print(f"✗ fakeout_strategy 导入失败: {str(e)}")
    sys.exit(1)

try:
    from eth_fakeout_strategy_system import MultiSymbolFakeoutSystem
    print("✓ eth_fakeout_strategy_system 导入成功")
except Exception as e:
    print(f"✗ eth_fakeout_strategy_system 导入失败: {str(e)}")
    sys.exit(1)

print("\n🎉 所有模块导入成功！")
