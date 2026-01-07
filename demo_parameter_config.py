#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
参数配置功能演示
展示如何使用parameter_config模块动态调整策略参数
"""

from parameter_config import get_config, ParameterConfig


def demo_basic_usage():
    """演示基本使用"""
    print("=" * 60)
    print("参数配置基本使用演示")
    print("=" * 60)
    
    # 1. 获取全局配置
    config = get_config()
    
    print("\n当前默认配置:")
    print(f"假突破策略:")
    print(f"  - 摆动点检测周期: {config.fakeout_strategy.swing_period}")
    print(f"  - 突破确认K线数: {config.fakeout_strategy.breakout_confirmation}")
    print(f"  - 假突破确认K线数: {config.fakeout_strategy.fakeout_confirmation}")
    
    print(f"\n风险管理:")
    print(f"  - 最大回撤: {config.risk_manager.max_drawdown_percent}%")
    print(f"  - 最大连续亏损: {config.risk_manager.max_consecutive_losses}次")
    print(f"  - 每日亏损限制: {config.risk_manager.daily_loss_limit} USDT")
    
    print(f"\n交易价值过滤:")
    print(f"  - 最小盈亏比: {config.worth_trading_filter.min_rr_ratio}")
    print(f"  - 最小预期波动: {config.worth_trading_filter.min_expected_move * 100:.2f}%")
    print(f"  - 成本倍数: {config.worth_trading_filter.cost_multiplier}")


def demo_parameter_update():
    """演示参数更新"""
    print("\n" + "=" * 60)
    print("参数更新演示")
    print("=" * 60)
    
    config = get_config()
    
    print("\n示例1: 更新假突破策略参数")
    print("将摆动点检测周期从3改为5")
    
    config.fakeout_strategy.swing_period = 5
    print(f"✓ 更新后: {config.fakeout_strategy.swing_period}")
    
    print("\n示例2: 更新风险管理参数")
    print("将最大回撤从10%改为15%")
    
    config.risk_manager.max_drawdown_percent = 15.0
    print(f"✓ 更新后: {config.risk_manager.max_drawdown_percent}%")
    
    print("\n示例3: 批量更新（使用from_dict方法）")
    
    updates = {
        'fakeout_strategy': {
            'swing_period': 4,
            'breakout_confirmation': 3,
            'min_body_ratio': 0.4
        },
        'risk_manager': {
            'max_consecutive_losses': 5,
            'daily_loss_limit': 100.0
        },
        'worth_trading_filter': {
            'min_rr_ratio': 2.5,
            'cost_multiplier': 2.5
        }
    }
    
    config.from_dict(updates)
    
    print("\n批量更新后的配置:")
    print(f"  - 摆动点检测周期: {config.fakeout_strategy.swing_period}")
    print(f"  - 突破确认K线数: {config.fakeout_strategy.breakout_confirmation}")
    print(f"  - K线实体占比: {config.fakeout_strategy.min_body_ratio}")
    print(f"  - 最大连续亏损: {config.risk_manager.max_consecutive_losses}次")
    print(f"  - 每日亏损限制: {config.risk_manager.daily_loss_limit} USDT")
    print(f"  - 最小盈亏比: {config.worth_trading_filter.min_rr_ratio}")
    print(f"  - 成本倍数: {config.worth_trading_filter.cost_multiplier}")


def demo_export_import():
    """演示导出和导入配置"""
    print("\n" + "=" * 60)
    print("配置导出和导入演示")
    print("=" * 60)
    
    config = get_config()
    
    # 导出为字典
    config_dict = config.to_dict()
    
    print("\n导出为字典（JSON格式）:")
    import json
    print(json.dumps(config_dict, indent=2, ensure_ascii=False))
    
    # 创建新的配置对象
    print("\n从字典创建新配置对象:")
    new_config = ParameterConfig()
    new_config.from_dict(config_dict)
    
    print(f"✓ 新配置对象创建成功")
    print(f"  摆动点检测周期: {new_config.fakeout_strategy.swing_period}")
    print(f"  最大回撤: {new_config.risk_manager.max_drawdown_percent}%")


def demo_preset_configurations():
    """演示预设配置"""
    print("\n" + "=" * 60)
    print("预设配置演示")
    print("=" * 60)
    
    config = get_config()
    
    # 激进配置
    print("\n激进配置（追求高收益，风险较高）:")
    aggressive = {
        'fakeout_strategy': {
            'swing_period': 2,
            'breakout_confirmation': 1,
            'fakeout_confirmation': 1
        },
        'risk_manager': {
            'max_drawdown_percent': 20.0,
            'max_consecutive_losses': 5,
            'risk_per_trade': 0.05
        },
        'worth_trading_filter': {
            'min_rr_ratio': 1.5,
            'min_expected_move': 0.003,
            'cost_multiplier': 1.5
        }
    }
    
    print("参数:")
    print(f"  - 摆动点检测周期: {aggressive['fakeout_strategy']['swing_period']}")
    print(f"  - 最大回撤: {aggressive['risk_manager']['max_drawdown_percent']}%")
    print(f"  - 单笔风险: {aggressive['risk_manager']['risk_per_trade'] * 100}%")
    print(f"  - 最小盈亏比: {aggressive['worth_trading_filter']['min_rr_ratio']}")
    
    # 保守配置
    print("\n保守配置（追求稳定，风险较低）:")
    conservative = {
        'fakeout_strategy': {
            'swing_period': 5,
            'breakout_confirmation': 3,
            'fakeout_confirmation': 2
        },
        'risk_manager': {
            'max_drawdown_percent': 5.0,
            'max_consecutive_losses': 2,
            'risk_per_trade': 0.01
        },
        'worth_trading_filter': {
            'min_rr_ratio': 3.0,
            'min_expected_move': 0.008,
            'cost_multiplier': 2.5
        }
    }
    
    print("参数:")
    print(f"  - 摆动点检测周期: {conservative['fakeout_strategy']['swing_period']}")
    print(f"  - 最大回撤: {conservative['risk_manager']['max_drawdown_percent']}%")
    print(f"  - 单笔风险: {conservative['risk_manager']['risk_per_trade'] * 100}%")
    print(f"  - 最小盈亏比: {conservative['worth_trading_filter']['min_rr_ratio']}")


def demo_system_integration():
    """演示与系统集成"""
    print("\n" + "=" * 60)
    print("与系统集成演示")
    print("=" * 60)
    
    config = get_config()
    
    # 模拟从GUI获取的更新
    print("\n模拟用户在GUI中调整参数:")
    gui_updates = {
        'fakeout_strategy': {
            'swing_period': 6,
            'min_body_ratio': 0.35
        },
        'risk_manager': {
            'max_drawdown_percent': 12.0
        }
    }
    
    print("GUI更新:")
    print(json.dumps(gui_updates, indent=2, ensure_ascii=False))
    
    # 应用到全局配置
    config.from_dict(gui_updates)
    
    print("\n应用到系统:")
    print(f"✓ 摆动点检测周期: {config.fakeout_strategy.swing_period}")
    print(f"✓ K线实体占比: {config.fakeout_strategy.min_body_ratio}")
    print(f"✓ 最大回撤: {config.risk_manager.max_drawdown_percent}%")
    
    # 如果系统正在运行，可以调用系统的update_parameters方法
    # system.update_parameters(config.to_dict())
    print("\n（在实际运行中，会调用 system.update_parameters() 应用到策略系统）")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("币安期货交易系统 - 参数配置功能演示")
    print("=" * 60)
    
    demo_basic_usage()
    demo_parameter_update()
    demo_export_import()
    demo_preset_configurations()
    demo_system_integration()
    
    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)
    
    print("\n总结:")
    print("✓ parameter_config模块提供了完整的参数管理功能")
    print("✓ 支持动态更新参数，无需重启系统")
    print("✓ 支持导出/导入配置，便于备份和分享")
    print("✓ 可以创建多种预设配置（激进/保守等）")
    print("✓ 与GUI无缝集成，提供友好的参数调整界面")
    print("\n使用建议:")
    print("1. 根据市场环境调整参数")
    print("2. 保存常用的配置为预设")
    print("3. 调整参数后观察策略表现")
    print("4. 始终使用模拟模式充分测试")


if __name__ == "__main__":
    import json
    main()
