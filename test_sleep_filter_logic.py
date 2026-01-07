#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场休眠过滤开关逻辑测试
不依赖网络连接，只测试核心逻辑
"""

from parameter_config import get_config, update_config


def print_separator():
    """打印分隔线"""
    print("=" * 70)


def test_parameter_config_logic():
    """测试参数配置逻辑"""
    print_separator()
    print("测试1: 参数配置逻辑")
    print_separator()

    # 获取配置
    config = get_config()
    print(f"1.1 市场休眠过滤开关初始值: {config.market_state_engine.enable_market_sleep_filter}")

    # 修改配置
    print("\n1.2 修改配置：禁用市场休眠过滤")
    update_config({
        'market_state_engine': {
            'enable_market_sleep_filter': False
        }
    })

    # 验证修改
    config = get_config()
    print(f"    修改后值: {config.market_state_engine.enable_market_sleep_filter}")
    assert config.market_state_engine.enable_market_sleep_filter == False, "配置修改失败"

    # 恢复默认值
    print("\n1.3 恢复默认值：启用市场休眠过滤")
    update_config({
        'market_state_engine': {
            'enable_market_sleep_filter': True
        }
    })

    config = get_config()
    print(f"    恢复后值: {config.market_state_engine.enable_market_sleep_filter}")
    assert config.market_state_engine.enable_market_sleep_filter == True, "配置恢复失败"

    print("\n✅ 参数配置逻辑测试通过")


def test_market_state_engine_logic():
    """测试市场状态引擎逻辑"""
    print_separator()
    print("测试2: 市场状态引擎逻辑")
    print_separator()

    from market_state_engine import MarketStateEngine

    # 测试初始化
    print("\n2.1 测试引擎初始化")
    engine = MarketStateEngine(None, "ETHUSDT", "5m", enable_sleep_filter=True)
    print(f"    休眠过滤开关状态: {engine.get_sleep_filter_status()}")
    assert engine.get_sleep_filter_status() == True, "初始化失败"

    # 测试动态切换
    print("\n2.2 测试动态切换休眠过滤开关")
    engine.set_sleep_filter(False)
    print(f"    设置为False后: {engine.get_sleep_filter_status()}")
    assert engine.get_sleep_filter_status() == False, "设置False失败"

    engine.set_sleep_filter(True)
    print(f"    设置为True后: {engine.get_sleep_filter_status()}")
    assert engine.get_sleep_filter_status() == True, "设置True失败"

    # 测试默认值
    print("\n2.3 测试默认值")
    engine_default = MarketStateEngine(None, "ETHUSDT", "5m")
    print(f"    默认值: {engine_default.get_sleep_filter_status()}")
    assert engine_default.get_sleep_filter_status() == True, "默认值不正确"

    print("\n✅ 市场状态引擎逻辑测试通过")


def test_determine_state_logic():
    """测试市场状态判断逻辑"""
    print_separator()
    print("测试3: 市场状态判断逻辑")
    print_separator()

    from market_state_engine import MarketStateEngine, MarketState

    # 创建引擎
    engine = MarketStateEngine(None, "ETHUSDT", "5m", enable_sleep_filter=True)

    # 模拟市场数据：低ATR（应触发SLEEP）
    print("\n3.1 模拟低ATR市场（启用休眠过滤）")
    engine.atr_sleep_threshold = 0.005
    state, reasons = engine._determine_state(atr_ratio=0.003, volume_ratio=1.0, funding_rate=0.0, atr_avg_ratio=1.0)
    print(f"    市场状态: {state.value}")
    print(f"    原因: {reasons}")
    assert state == MarketState.SLEEP, "低ATR应触发SLEEP"

    # 模拟市场数据：低ATR（禁用休眠过滤）
    print("\n3.2 模拟低ATR市场（禁用休眠过滤）")
    engine.set_sleep_filter(False)
    state, reasons = engine._determine_state(atr_ratio=0.003, volume_ratio=1.0, funding_rate=0.0, atr_avg_ratio=1.0)
    print(f"    市场状态: {state.value}")
    print(f"    原因: {reasons}")
    assert state != MarketState.SLEEP, "禁用休眠过滤后不应触发SLEEP"

    # 模拟市场数据：高ATR（应触发AGGRESSIVE）
    print("\n3.3 模拟高ATR市场")
    engine.set_sleep_filter(True)
    engine.atr_active_threshold = 0.02
    state, reasons = engine._determine_state(atr_ratio=0.025, volume_ratio=1.0, funding_rate=0.0, atr_avg_ratio=1.0)
    print(f"    市场状态: {state.value}")
    print(f"    原因: {reasons}")
    assert state == MarketState.AGGRESSIVE, "高ATR应触发AGGRESSIVE"

    # 模拟市场数据：正常波动（应触发ACTIVE）
    print("\n3.4 模拟正常波动市场")
    state, reasons = engine._determine_state(atr_ratio=0.01, volume_ratio=1.0, funding_rate=0.0, atr_avg_ratio=1.0)
    print(f"    市场状态: {state.value}")
    print(f"    原因: {reasons}")
    assert state == MarketState.ACTIVE, "正常波动应触发ACTIVE"

    print("\n✅ 市场状态判断逻辑测试通过")


def test_integrated_logic():
    """测试集成逻辑"""
    print_separator()
    print("测试4: 集成逻辑")
    print_separator()

    # 测试配置到引擎的传递
    print("\n4.1 测试配置到引擎的传递")

    from market_state_engine import MarketStateEngine

    # 修改配置
    update_config({
        'market_state_engine': {
            'enable_market_sleep_filter': False
        }
    })

    config = get_config()
    print(f"    配置值: {config.market_state_engine.enable_market_sleep_filter}")

    # 创建引擎（不从配置读取）
    engine = MarketStateEngine(None, "ETHUSDT", "5m", enable_sleep_filter=config.market_state_engine.enable_market_sleep_filter)
    print(f"    引擎值: {engine.get_sleep_filter_status()}")

    assert engine.get_sleep_filter_status() == config.market_state_engine.enable_market_sleep_filter, "配置传递失败"

    # 恢复默认值
    update_config({
        'market_state_engine': {
            'enable_market_sleep_filter': True
        }
    })

    print("\n✅ 集成逻辑测试通过")


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("市场休眠过滤开关逻辑测试")
    print("=" * 70)
    print("\n说明:")
    print("  - 不依赖网络连接，只测试核心逻辑")
    print("  - 测试参数配置、引擎逻辑、状态判断和集成功能")
    print()

    try:
        # 运行测试
        test_parameter_config_logic()
        print("\n")

        test_market_state_engine_logic()
        print("\n")

        test_determine_state_logic()
        print("\n")

        test_integrated_logic()
        print("\n")

        # 总结
        print_separator()
        print("所有逻辑测试通过 ✅")
        print_separator()
        print("\n功能总结:")
        print("  1. ✅ 参数配置功能正常")
        print("  2. ✅ 市场状态引擎支持休眠过滤开关")
        print("  3. ✅ 动态切换休眠过滤开关正常")
        print("  4. ✅ 市场状态判断逻辑正确")
        print("  5. ✅ 配置到引擎的传递正常")
        print("\nGUI使用说明:")
        print("  - 打开程序，进入'⚙️ 参数配置'标签页")
        print("  - 找到'市场状态引擎参数'部分")
        print("  - 勾选/取消'启用 enable_market_sleep_filter'复选框")
        print("  - 点击'💾 保存并应用'按钮")
        print("  - 参数实时生效，无需重启")
        print()

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
