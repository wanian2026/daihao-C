#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统功能综合测试脚本
测试系统各项功能的正确性，包括参数配置、市场状态引擎、风险管理等
"""

import sys
from datetime import datetime

def test_parameter_config():
    """测试参数配置模块"""
    print("\n" + "="*60)
    print("测试1: 参数配置模块")
    print("="*60)
    
    from parameter_config import get_config, update_config
    
    try:
        config = get_config()
        
        # 测试读取配置
        print("✓ 配置读取成功")
        print(f"  - 假突破策略: swing_period={config.fakeout_strategy.swing_period}")
        print(f"  - 风险管理: max_drawdown={config.risk_manager.max_drawdown_percent}%")
        print(f"  - 市场状态: enable_sleep_filter={config.market_state_engine.enable_market_sleep_filter}")
        
        # 测试更新配置
        updates = {
            'fakeout_strategy': {'swing_period': 5},
            'risk_manager': {'max_drawdown_percent': 8.0}
        }
        update_config(updates)
        
        config = get_config()
        assert config.fakeout_strategy.swing_period == 5
        assert config.risk_manager.max_drawdown_percent == 8.0
        print("✓ 配置更新成功")
        
        # 恢复默认值
        updates = {
            'fakeout_strategy': {'swing_period': 3},
            'risk_manager': {'max_drawdown_percent': 5.0}
        }
        update_config(updates)
        print("✓ 配置恢复成功")
        
        return True
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        return False


def test_market_state_engine():
    """测试市场状态引擎"""
    print("\n" + "="*60)
    print("测试2: 市场状态引擎")
    print("="*60)
    
    try:
        from binance_api_client import BinanceAPIClient
        from data_fetcher import DataFetcher
        from market_state_engine import MarketStateEngine, MarketState
        
        # 创建引擎（启用休眠过滤）
        client = BinanceAPIClient()
        fetcher = DataFetcher(client)
        engine = MarketStateEngine(fetcher, symbol="ETHUSDT", interval="5m", enable_sleep_filter=True)
        
        # 测试分析功能
        state_info = engine.analyze()
        print(f"✓ 市场状态分析成功")
        print(f"  - 状态: {state_info.state.value}")
        print(f"  - ATR: {state_info.atr:.2f}")
        print(f"  - ATR比率: {state_info.atr_ratio:.2f}")
        print(f"  - 成交量比率: {state_info.volume_ratio:.2f}")
        print(f"  - 评分: {state_info.score:.1f}/100")
        print(f"  - 原因: {', '.join(state_info.reasons)}")
        
        # 测试休眠过滤开关
        engine.set_sleep_filter(False)
        assert engine.get_sleep_filter_status() == False
        print("✓ 休眠过滤关闭成功")
        
        engine.set_sleep_filter(True)
        assert engine.get_sleep_filter_status() == True
        print("✓ 休眠过滤开启成功")
        
        # 测试批量分析
        symbols = ["ETHUSDT", "BTCUSDT"]
        results = engine.analyze_batch(symbols)
        print(f"✓ 批量分析成功: {len(results)} 个标的")
        
        # 测试可交易标的筛选
        tradeable = engine.get_tradeable_symbols(symbols)
        print(f"✓ 可交易标的: {tradeable}")
        
        return True
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_risk_manager():
    """测试风险管理器"""
    print("\n" + "="*60)
    print("测试3: 风险管理器")
    print("="*60)
    
    try:
        from risk_manager import RiskManager, CircuitBreakerState
        
        # 创建风险管理器
        risk_mgr = RiskManager(
            max_drawdown_percent=5.0,
            max_consecutive_losses=3,
            daily_loss_limit=30.0
        )
        
        # 设置初始余额
        risk_mgr.set_initial_balance(1000.0)
        print("✓ 风险管理器初始化成功")
        print(f"  - 初始余额: 1000.0 USDT")
        
        # 测试盈利
        risk_mgr.update_pnl(50.0)
        metrics = risk_mgr.get_metrics()
        print(f"✓ 盈利更新成功")
        print(f"  - 总交易: {metrics['total_trades']}")
        print(f"  - 盈利交易: {metrics['winning_trades']}")
        print(f"  - 总盈亏: {metrics['total_pnl']:.2f} USDT")
        
        # 测试亏损
        risk_mgr.update_pnl(-30.0)
        metrics = risk_mgr.get_metrics()
        print(f"✓ 亏损更新成功")
        print(f"  - 总交易: {metrics['total_trades']}")
        print(f"  - 亏损交易: {metrics['losing_trades']}")
        print(f"  - 总盈亏: {metrics['total_pnl']:.2f} USDT")
        print(f"  - 连续亏损: {metrics['consecutive_losses']}")
        
        # 测试连续亏损熔断
        risk_mgr.update_pnl(-10.0)
        risk_mgr.update_pnl(-15.0)
        risk_mgr.update_pnl(-20.0)
        metrics = risk_mgr.get_metrics()
        print(f"✓ 连续亏损熔断测试")
        print(f"  - 连续亏损: {metrics['consecutive_losses']}")
        print(f"  - 熔断状态: {metrics['circuit_breaker_state']}")
        
        # 测试重置熔断
        risk_mgr.reset_circuit_breaker()
        metrics = risk_mgr.get_metrics()
        print(f"✓ 熔断重置成功")
        print(f"  - 连续亏损: {metrics['consecutive_losses']}")
        print(f"  - 熔断状态: {metrics['circuit_breaker_state']}")
        
        # 测试交易许可检查
        allowed, reason = risk_mgr.is_allowed_to_trade()
        print(f"✓ 交易许可检查")
        print(f"  - 允许交易: {allowed}")
        print(f"  - 原因: {reason}")
        
        return True
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_worth_trading_filter():
    """测试交易价值过滤器"""
    print("\n" + "="*60)
    print("测试4: 交易价值过滤器")
    print("="*60)
    
    try:
        from binance_api_client import BinanceAPIClient
        from data_fetcher import DataFetcher
        from worth_trading_filter import WorthTradingFilter
        
        # 创建过滤器
        client = BinanceAPIClient()
        fetcher = DataFetcher(client)
        filter_engine = WorthTradingFilter(fetcher)
        
        print("✓ 过滤器初始化成功")
        print(f"  - 最小盈亏比: {filter_engine.min_rr_ratio}")
        print(f"  - 最小预期波动: {filter_engine.min_expected_move*100:.1f}%")
        print(f"  - 成本倍数: {filter_engine.cost_multiplier}")
        
        # 测试检查功能
        result = filter_engine.check("ETHUSDT")
        print(f"✓ 交易价值检查成功")
        print(f"  - 值得交易: {result.is_worth_trading}")
        print(f"  - 预期波动: {result.expected_move*100:.2f}%")
        print(f"  - 交易成本: {result.total_cost*100:.3f}%")
        print(f"  - 盈亏比: {result.risk_reward_ratio:.2f}")
        print(f"  - 原因: {', '.join(result.reasons)}")
        
        return True
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_fakeout_strategy():
    """测试假突破策略"""
    print("\n" + "="*60)
    print("测试5: 假突破策略")
    print("="*60)
    
    try:
        from binance_api_client import BinanceAPIClient
        from data_fetcher import DataFetcher
        from fakeout_strategy import FakeoutStrategy
        
        # 创建策略
        client = BinanceAPIClient()
        fetcher = DataFetcher(client)
        strategy = FakeoutStrategy(fetcher, "ETHUSDT", "5m")
        
        print("✓ 策略初始化成功")
        print(f"  - 摆动点周期: {strategy.swing_period}")
        print(f"  - 突破确认: {strategy.breakout_confirmation}")
        print(f"  - 假突破确认: {strategy.fakeout_confirmation}")
        
        # 测试分析功能
        signals = strategy.analyze()
        print(f"✓ 策略分析成功")
        print(f"  - 信号数量: {len(signals)}")
        
        if signals:
            for i, signal in enumerate(signals):
                print(f"  信号 {i+1}:")
                print(f"    - 类型: {signal.signal_type.value}")
                print(f"    - 入场价: {signal.entry_price:.2f}")
                print(f"    - 止损价: {signal.stop_loss:.2f}")
                print(f"    - 止盈价: {signal.take_profit:.2f}")
                print(f"    - 置信度: {signal.confidence:.2f}")
                print(f"    - 原因: {signal.reason}")
        
        return True
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_system_integration():
    """测试系统集成（不启动主循环）"""
    print("\n" + "="*60)
    print("测试6: 系统集成")
    print("="*60)
    
    try:
        # 注意：此测试需要API密钥，如果未提供则跳过
        import os
        
        api_key = os.environ.get('BINANCE_API_KEY')
        api_secret = os.environ.get('BINANCE_API_SECRET')
        
        if not api_key or not api_secret:
            print("⚠ 跳过测试: 未设置BINANCE_API_KEY或BINANCE_API_SECRET环境变量")
            return True
        
        from binance_trading_client import BinanceTradingClient
        from eth_fakeout_strategy_system import MultiSymbolFakeoutSystem
        
        # 创建系统
        client = BinanceTradingClient(api_key, api_secret)
        result = client.test_connection()
        
        if not result['success']:
            print(f"✗ API连接失败: {result['message']}")
            return False
        
        print("✓ API连接成功")
        
        # 创建策略系统
        system = MultiSymbolFakeoutSystem(client)
        print("✓ 策略系统初始化成功")
        print(f"  - 监控标的: {', '.join(system.selected_symbols)}")
        print(f"  - 系统状态: {system.state.value}")
        
        # 测试参数更新
        from parameter_config import get_config
        config = get_config()
        config_dict = config.to_dict()
        system.update_parameters(config_dict)
        print("✓ 参数更新成功")
        
        # 测试市场状态分析
        state_info = system.market_state_engine.analyze()
        print(f"✓ 市场状态分析成功")
        print(f"  - 状态: {state_info.state.value}")
        print(f"  - 评分: {state_info.score:.1f}/100")
        
        return True
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("系统功能综合测试")
    print("="*60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("参数配置模块", test_parameter_config),
        ("市场状态引擎", test_market_state_engine),
        ("风险管理器", test_risk_manager),
        ("交易价值过滤器", test_worth_trading_filter),
        ("假突破策略", test_fakeout_strategy),
        ("系统集成", test_system_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ 测试异常: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # 输出测试结果汇总
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name:30s}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("-" * 60)
    print(f"总计: {len(results)} 个测试, 通过 {passed} 个, 失败 {failed} 个")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
