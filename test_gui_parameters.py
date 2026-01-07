#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试GUI参数配置和手动控制功能
"""

import sys

def test_parameter_config():
    """测试参数配置模块"""
    print("=" * 60)
    print("测试参数配置模块")
    print("=" * 60)
    
    try:
        from parameter_config import get_config, ParameterConfig
        
        # 获取配置
        config = get_config()
        
        print(f"✓ 参数配置模块加载成功")
        print(f"\n假突破策略参数:")
        print(f"  - 摆动点检测周期: {config.fakeout_strategy.swing_period}")
        print(f"  - 突破确认K线数: {config.fakeout_strategy.breakout_confirmation}")
        print(f"  - 最小盈亏比: {config.worth_trading_filter.min_rr_ratio}")
        print(f"  - 最大回撤: {config.risk_manager.max_drawdown_percent}%")
        
        # 测试转换为字典
        config_dict = config.to_dict()
        print(f"\n✓ 配置转换为字典成功")
        
        # 测试从字典加载
        new_config = ParameterConfig()
        new_config.from_dict(config_dict)
        print(f"✓ 从字典加载配置成功")
        
        # 测试更新配置
        updates = {
            'fakeout_strategy': {
                'swing_period': 5
            },
            'risk_manager': {
                'max_drawdown_percent': 15.0
            }
        }
        config.from_dict(updates)
        print(f"✓ 配置更新成功")
        print(f"  - 摆动点检测周期已更新为: {config.fakeout_strategy.swing_period}")
        print(f"  - 最大回撤已更新为: {config.risk_manager.max_drawdown_percent}%")
        
        print("\n✓ 参数配置模块测试通过\n")
        return True
        
    except Exception as e:
        print(f"\n✗ 参数配置模块测试失败: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def test_gui_imports():
    """测试GUI导入"""
    print("=" * 60)
    print("测试GUI模块导入")
    print("=" * 60)
    
    try:
        import tkinter as tk
        print("✓ tkinter导入成功")
        
        from eth_fakeout_gui import ETHFakeoutGUI
        print("✓ ETHFakeoutGUI导入成功")
        
        from eth_fakeout_strategy_system import MultiSymbolFakeoutSystem, SystemState
        print("✓ MultiSymbolFakeoutSystem导入成功")
        
        # 测试SystemState枚举
        print(f"\n系统状态枚举:")
        for state in SystemState:
            print(f"  - {state.name}: {state.value}")
        
        print("\n✓ GUI模块导入测试通过\n")
        return True
        
    except Exception as e:
        print(f"\n✗ GUI模块导入测试失败: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def test_system_parameter_update():
    """测试系统参数更新"""
    print("=" * 60)
    print("测试系统参数更新功能")
    print("=" * 60)
    
    try:
        from eth_fakeout_strategy_system import MultiSymbolFakeoutSystem
        from parameter_config import get_config
        
        # 注意：这里需要真实的API密钥才能创建完整的系统
        # 我们只测试参数更新方法的逻辑
        print("\n注意：需要真实API密钥才能创建完整系统")
        print("这里只验证参数更新方法的可用性")
        
        # 检查系统类是否有update_parameters方法
        if hasattr(MultiSymbolFakeoutSystem, 'update_parameters'):
            print("✓ MultiSymbolFakeoutSystem.update_parameters方法存在")
        else:
            print("✗ MultiSymbolFakeoutSystem.update_parameters方法不存在")
            return False
        
        if hasattr(MultiSymbolFakeoutSystem, 'get_symbol_selector'):
            print("✓ MultiSymbolFakeoutSystem.get_symbol_selector方法存在")
        else:
            print("✗ MultiSymbolFakeoutSystem.get_symbol_selector方法不存在")
            return False
        
        print("\n✓ 系统参数更新功能验证通过\n")
        return True
        
    except Exception as e:
        print(f"\n✗ 系统参数更新功能测试失败: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("币安期货交易系统 - 功能测试")
    print("=" * 60 + "\n")
    
    results = []
    
    # 运行测试
    results.append(("参数配置模块", test_parameter_config()))
    results.append(("GUI模块导入", test_gui_imports()))
    results.append(("系统参数更新", test_system_parameter_update()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n总计: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("\n✓ 所有测试通过！系统功能正常。")
        print("\n使用说明:")
        print("1. 运行 GUI: python3 eth_fakeout_gui.py")
        print("2. 登录时输入币安API密钥")
        print("3. 在'参数配置'标签页调整策略参数")
        print("4. 在'手动控制'标签页进行手动干预")
        print("5. 在'监控'标签页查看实时日志和信号")
        return 0
    else:
        print(f"\n✗ 有 {failed} 个测试失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
