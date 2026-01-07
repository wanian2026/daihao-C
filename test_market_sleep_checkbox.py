#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试市场休眠开关配置
验证复选框是否正确配置并可以更新
"""

from parameter_config import get_config, update_config

print("="*60)
print("测试市场休眠开关配置")
print("="*60)

# 1. 检查默认配置
config = get_config()
print(f"\n1. 默认配置:")
print(f"   enable_market_sleep_filter: {config.market_state_engine.enable_market_sleep_filter}")

# 2. 验证参数可以通过字典更新
print(f"\n2. 测试参数更新:")
updates = {
    'market_state_engine': {
        'enable_market_sleep_filter': False
    }
}
update_config(updates)

config = get_config()
print(f"   更新后: {config.market_state_engine.enable_market_sleep_filter}")
assert config.market_state_engine.enable_market_sleep_filter == False, "更新失败"
print(f"   ✓ 参数更新成功")

# 3. 验证参数可以恢复
print(f"\n3. 测试参数恢复:")
updates = {
    'market_state_engine': {
        'enable_market_sleep_filter': True
    }
}
update_config(updates)

config = get_config()
print(f"   恢复后: {config.market_state_engine.enable_market_sleep_filter}")
assert config.market_state_engine.enable_market_sleep_filter == True, "恢复失败"
print(f"   ✓ 参数恢复成功")

# 4. 检查to_dict方法
print(f"\n4. 测试to_dict方法:")
config_dict = config.to_dict()
print(f"   market_state_engine.enable_market_sleep_filter: {config_dict['market_state_engine']['enable_market_sleep_filter']}")
assert 'enable_market_sleep_filter' in config_dict['market_state_engine'], "to_dict方法失败"
print(f"   ✓ to_dict方法正常")

# 5. 检查from_dict方法
print(f"\n5. 测试from_dict方法:")
test_data = {
    'market_state_engine': {
        'enable_market_sleep_filter': False,
        'volatility_window': 20,
        'trend_ma_fast': 10,
        'trend_ma_slow': 30,
        'volume_ma_period': 25
    }
}
config.from_dict(test_data)
config = get_config()
print(f"   enable_market_sleep_filter: {config.market_state_engine.enable_market_sleep_filter}")
print(f"   volatility_window: {config.market_state_engine.volatility_window}")
print(f"   trend_ma_fast: {config.market_state_engine.trend_ma_fast}")
print(f"   trend_ma_slow: {config.market_state_engine.trend_ma_slow}")
print(f"   volume_ma_period: {config.market_state_engine.volume_ma_period}")

assert config.market_state_engine.enable_market_sleep_filter == False, "from_dict失败"
assert config.market_state_engine.volatility_window == 20, "from_dict失败"
assert config.market_state_engine.trend_ma_fast == 10, "from_dict失败"
print(f"   ✓ from_dict方法正常")

# 6. 恢复默认值
print(f"\n6. 恢复默认值:")
updates = {
    'market_state_engine': {
        'enable_market_sleep_filter': True,
        'volatility_window': 14,
        'trend_ma_fast': 7,
        'trend_ma_slow': 25,
        'volume_ma_period': 20
    }
}
update_config(updates)
config = get_config()
print(f"   enable_market_sleep_filter: {config.market_state_engine.enable_market_sleep_filter}")
print(f"   ✓ 默认值已恢复")

print("\n" + "="*60)
print("✓ 所有测试通过！市场休眠开关配置正确")
print("="*60)
print("\nGUI界面说明:")
print("- 市场休眠开关位于「⚙️ 参数配置」标签页")
print("- 在「市场状态引擎参数」组的底部")
print("- 显示文字：'市场休眠过滤开关'")
print("- 描述：'⚡ 市场休眠过滤开关（启用后，市场处于休眠状态时将不执行交易）'")
print("- 默认状态：勾选（启用）")
print("- 可以使用鼠标滚轮滚动查看所有参数")
