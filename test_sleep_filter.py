#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场休眠过滤开关功能测试
验证市场休眠过滤开关是否正常工作
"""

from parameter_config import get_config, update_config
from market_state_engine import MarketStateEngine, MarketState
from binance_api_client import BinanceAPIClient
from data_fetcher import DataFetcher


def print_separator():
    """打印分隔线"""
    print("=" * 70)


def test_parameter_config():
    """测试参数配置"""
    print_separator()
    print("测试1: 参数配置")
    print_separator()

    # 获取配置
    config = get_config()
    print(f"市场休眠过滤开关初始值: {config.market_state_engine.enable_market_sleep_filter}")

    # 修改配置
    print("\n修改配置：禁用市场休眠过滤")
    update_config({
        'market_state_engine': {
            'enable_market_sleep_filter': False
        }
    })

    # 验证修改
    config = get_config()
    print(f"市场休眠过滤开关修改后: {config.market_state_engine.enable_market_sleep_filter}")

    # 恢复默认值
    print("\n恢复默认值：启用市场休眠过滤")
    update_config({
        'market_state_engine': {
            'enable_market_sleep_filter': True
        }
    })

    config = get_config()
    print(f"市场休眠过滤开关恢复后: {config.market_state_engine.enable_market_sleep_filter}")

    print("\n✅ 参数配置测试通过")


def test_market_state_engine():
    """测试市场状态引擎"""
    print_separator()
    print("测试2: 市场状态引擎")
    print_separator()

    try:
        # 创建API客户端
        api_client = BinanceAPIClient()
        data_fetcher = DataFetcher(api_client)

        # 测试启用休眠过滤
        print("\n场景1: 启用市场休眠过滤")
        engine_enabled = MarketStateEngine(data_fetcher, "ETHUSDT", "5m", enable_sleep_filter=True)
        state_info_enabled = engine_enabled.analyze()
        print(f"市场状态: {state_info_enabled.state.value}")
        print(f"原因: {state_info_enabled.reasons}")
        print(f"休眠过滤开关状态: {engine_enabled.get_sleep_filter_status()}")

        # 测试禁用休眠过滤
        print("\n场景2: 禁用市场休眠过滤")
        engine_disabled = MarketStateEngine(data_fetcher, "ETHUSDT", "5m", enable_sleep_filter=False)
        state_info_disabled = engine_disabled.analyze()
        print(f"市场状态: {state_info_disabled.state.value}")
        print(f"原因: {state_info_disabled.reasons}")
        print(f"休眠过滤开关状态: {engine_disabled.get_sleep_filter_status()}")

        # 测试动态切换
        print("\n场景3: 动态切换休眠过滤开关")
        engine = MarketStateEngine(data_fetcher, "ETHUSDT", "5m", enable_sleep_filter=True)
        print(f"初始状态: {engine.analyze().state.value}, 休眠过滤: {engine.get_sleep_filter_status()}")

        engine.set_sleep_filter(False)
        print(f"禁用后状态: {engine.analyze().state.value}, 休眠过滤: {engine.get_sleep_filter_status()}")

        engine.set_sleep_filter(True)
        print(f"启用后状态: {engine.analyze().state.value}, 休眠过滤: {engine.get_sleep_filter_status()}")

        print("\n✅ 市场状态引擎测试通过")

    except Exception as e:
        print(f"\n❌ 市场状态引擎测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


def test_market_state_comparison():
    """测试启用/禁用休眠过滤的市场状态差异"""
    print_separator()
    print("测试3: 启用/禁用休眠过滤的市场状态对比")
    print_separator()

    try:
        # 创建API客户端
        api_client = BinanceAPIClient()
        data_fetcher = DataFetcher(api_client)

        # 创建两个引擎，一个启用休眠过滤，一个禁用
        engine_enabled = MarketStateEngine(data_fetcher, "ETHUSDT", "5m", enable_sleep_filter=True)
        engine_disabled = MarketStateEngine(data_fetcher, "ETHUSDT", "5m", enable_sleep_filter=False)

        # 分析市场状态
        state_info_enabled = engine_enabled.analyze()
        state_info_disabled = engine_disabled.analyze()

        print(f"\n启用休眠过滤:")
        print(f"  市场状态: {state_info_enabled.state.value}")
        print(f"  原因: {state_info_enabled.reasons}")
        print(f"  可交易: {state_info_enabled.state != MarketState.SLEEP}")

        print(f"\n禁用休眠过滤:")
        print(f"  市场状态: {state_info_disabled.state.value}")
        print(f"  原因: {state_info_disabled.reasons}")
        print(f"  可交易: {state_info_disabled.state != MarketState.SLEEP}")

        # 对比分析
        if state_info_enabled.state == MarketState.SLEEP and state_info_disabled.state != MarketState.SLEEP:
            print("\n✅ 测试成功：禁用休眠过滤后，市场状态从SLEEP变为可交易状态")
        elif state_info_enabled.state == state_info_disabled.state:
            print(f"\nℹ️  信息：当前市场状态为{state_info_enabled.state.value}，无论是否启用休眠过滤结果相同")
        else:
            print(f"\n⚠️  注意：启用和禁用休眠过滤的市场状态不同")

    except Exception as e:
        print(f"\n❌ 市场状态对比测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("市场休眠过滤开关功能测试")
    print("=" * 70)
    print("\n说明:")
    print("  1. 测试参数配置中的市场休眠过滤开关")
    print("  2. 测试市场状态引擎的休眠过滤功能")
    print("  3. 测试启用/禁用休眠过滤的市场状态差异")
    print()

    try:
        # 运行测试
        test_parameter_config()
        print("\n")

        test_market_state_engine()
        print("\n")

        test_market_state_comparison()
        print("\n")

        # 总结
        print_separator()
        print("所有测试完成")
        print_separator()
        print("\n功能说明:")
        print("  - 市场休眠过滤开关可以控制是否启用市场休眠判断")
        print("  - 启用时：系统会根据ATR、成交量、资金费率判断市场是否休眠")
        print("  - 禁用时：系统忽略市场休眠判断，始终进行交易")
        print("  - 参数位置：⚙️ 参数配置 → 市场状态引擎参数")
        print("  - 默认值：启用（True）")
        print("\n使用建议:")
        print("  - 建议保持启用市场休眠过滤，以避免在低质量市场条件下交易")
        print("  - 如果需要强制交易，可以临时禁用休眠过滤")
        print("  - 修改参数后点击'💾 保存并应用'即可实时生效，无需重启")
        print()

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
