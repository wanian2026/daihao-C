#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多合约标的筛选功能测试脚本
测试各个模块的基本功能
"""

import sys

def test_imports():
    """测试导入"""
    print("=" * 60)
    print("测试1: 模块导入")
    print("=" * 60)
    
    try:
        from symbol_selector import SymbolSelector, SelectionMode
        print("✓ symbol_selector 导入成功")
        
        from data_fetcher import DataFetcher
        print("✓ data_fetcher 导入成功")
        
        from market_state_engine import MarketStateEngine, MarketState
        print("✓ market_state_engine 导入成功")
        
        from fakeout_strategy import FakeoutStrategy
        print("✓ fakeout_strategy 导入成功")
        
        from eth_fakeout_strategy_system import MultiSymbolFakeoutSystem
        print("✓ eth_fakeout_strategy_system 导入成功")
        
        print("\n所有模块导入成功！")
        return True
        
    except Exception as e:
        print(f"\n✗ 导入失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_symbol_selector():
    """测试合约选择器"""
    print("\n" + "=" * 60)
    print("测试2: 合约选择器（需要网络连接）")
    print("=" * 60)
    
    try:
        from binance_api_client import BinanceAPIClient
        from symbol_selector import SymbolSelector, SelectionMode
        
        print("正在初始化合约选择器...")
        client = BinanceAPIClient()
        selector = SymbolSelector(client)
        
        print("正在获取USDT永续合约列表...")
        symbols = selector.update_symbol_list(force_update=True)
        print(f"✓ 获取到 {len(symbols)} 个USDT永续合约")
        
        # 测试自动选择模式
        print("\n测试自动选择模式（综合评分）...")
        selector.set_selection_mode(SelectionMode.AUTO_SCORE)
        selected = selector.get_selected_symbols()
        print(f"✓ 已选择 {len(selected)} 个合约（综合评分）")
        print(f"  前5个: {', '.join(selected[:5])}")
        
        # 测试成交量模式
        print("\n测试自动选择模式（成交量）...")
        selector.set_selection_mode(SelectionMode.AUTO_VOLUME)
        selected = selector.get_selected_symbols()
        print(f"✓ 已选择 {len(selected)} 个合约（成交量）")
        print(f"  前5个: {', '.join(selected[:5])}")
        
        # 测试手动选择
        print("\n测试手动选择模式...")
        selector.set_selection_mode(SelectionMode.MANUAL)
        selector.set_selected_symbols({'ETHUSDT', 'BTCUSDT', 'BNBUSDT'})
        selected = selector.get_selected_symbols()
        print(f"✓ 已选择 {len(selected)} 个合约（手动）")
        print(f"  已选: {', '.join(selected)}")
        
        # 获取评分最高的10个
        print("\n获取评分最高的10个合约...")
        top_symbols = selector.get_top_symbols(10)
        print(f"✓ 评分前10的合约:")
        for i, sym in enumerate(top_symbols, 1):
            print(f"  {i}. {sym.symbol} - 评分: {sym.score:.1f} - 24h成交量: {sym.volume_24h:,.0f}")
        
        print("\n合约选择器测试通过！")
        return True
        
    except Exception as e:
        print(f"\n✗ 合约选择器测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_data_fetcher_batch():
    """测试数据获取器批量功能"""
    print("\n" + "=" * 60)
    print("测试3: 数据获取器批量功能（需要网络连接）")
    print("=" * 60)
    
    try:
        from binance_api_client import BinanceAPIClient
        from data_fetcher import DataFetcher
        
        print("正在初始化数据获取器...")
        client = BinanceAPIClient()
        fetcher = DataFetcher(client)
        
        # 测试批量获取K线
        print("\n测试批量获取K线...")
        symbols = ['ETHUSDT', 'BTCUSDT', 'BNBUSDT']
        klines_dict = fetcher.get_klines_batch(symbols, interval='5m', limit=5)
        
        for symbol, klines in klines_dict.items():
            print(f"✓ {symbol}: 获取到 {len(klines)} 条K线")
        
        # 测试批量获取市场指标
        print("\n测试批量获取市场指标...")
        metrics_dict = fetcher.get_market_metrics_batch(symbols, interval='5m')
        
        for symbol, metrics in metrics_dict.items():
            print(f"✓ {symbol}: ATR={metrics['atr']:.2f}, ATR比率={metrics['atr_ratio']:.4f}, "
                  f"成交量比率={metrics['volume_ratio']:.2f}")
        
        print("\n数据获取器批量功能测试通过！")
        return True
        
    except Exception as e:
        print(f"\n✗ 数据获取器批量功能测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_market_state_batch():
    """测试市场状态引擎批量功能"""
    print("\n" + "=" * 60)
    print("测试4: 市场状态引擎批量功能（需要网络连接）")
    print("=" * 60)
    
    try:
        from binance_api_client import BinanceAPIClient
        from data_fetcher import DataFetcher
        from market_state_engine import MarketStateEngine, MarketState
        
        print("正在初始化市场状态引擎...")
        client = BinanceAPIClient()
        fetcher = DataFetcher(client)
        engine = MarketStateEngine(fetcher, symbol="ETHUSDT", interval="5m")
        
        # 测试批量分析
        print("\n测试批量分析市场状态...")
        symbols = ['ETHUSDT', 'BTCUSDT', 'BNBUSDT', 'SOLUSDT']
        state_infos = engine.analyze_batch(symbols)
        
        print(f"✓ 分析了 {len(state_infos)} 个标的的市场状态:")
        for symbol, state_info in state_infos.items():
            print(f"  {symbol}: {state_info.state.value} - 评分: {state_info.score:.1f} - "
                  f"原因: {', '.join(state_info.reasons)}")
        
        # 测试获取可交易标的
        print("\n测试获取可交易标的...")
        tradeable = engine.get_tradeable_symbols(symbols)
        print(f"✓ 可交易标的: {', '.join(tradeable)}")
        
        print("\n市场状态引擎批量功能测试通过！")
        return True
        
    except Exception as e:
        print(f"\n✗ 市场状态引擎批量功能测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("多合约标的筛选功能测试")
    print("=" * 60)
    print("\n注意：部分测试需要网络连接到币安API")
    print("      如果网络不可用，相关测试会失败\n")
    
    results = []
    
    # 测试1: 模块导入
    results.append(("模块导入", test_imports()))
    
    # 测试2: 合约选择器
    results.append(("合约选择器", test_symbol_selector()))
    
    # 测试3: 数据获取器批量功能
    results.append(("数据获取器批量功能", test_data_fetcher_batch()))
    
    # 测试4: 市场状态引擎批量功能
    results.append(("市场状态引擎批量功能", test_market_state_batch()))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
