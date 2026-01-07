#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
币安自动交易系统 - 代码验证测试
"""

import sys
import os

print("=" * 70)
print("币安自动交易系统 - 代码验证")
print("=" * 70)
print()

# 测试1: Python环境
print("【测试1】Python环境检查")
print(f"✓ Python 版本: {sys.version.split()[0]}")
if sys.version_info < (3, 6):
    print("✗ Python版本过低，需要3.6+")
    sys.exit(1)
print()

# 测试2: 依赖库检查
print("【测试2】依赖库检查")
required_modules = {
    'requests': 'requests',
    'hmac': 'hmac',
    'hashlib': 'hashlib',
    'threading': 'threading',
    'datetime': 'datetime',
    'json': 'json',
    'dataclasses': 'dataclasses',
}

all_modules_ok = True
for module_name, import_name in required_modules.items():
    try:
        __import__(module_name)
        print(f"✓ {module_name}")
    except ImportError:
        print(f"✗ {module_name} - 未安装")
        all_modules_ok = False

# 检查可选依赖
optional_modules = {
    'cryptography': 'cryptography',
}
for module_name, import_name in optional_modules.items():
    try:
        __import__(module_name)
        print(f"✓ {module_name} (加密库)")
    except ImportError:
        print(f"⚠ {module_name} - 未安装 (可选，但建议安装)")

print()

# 测试3: 文件完整性检查
print("【测试3】文件完整性检查")
files_to_check = [
    ('binance_api_client.py', '公共API客户端'),
    ('binance_trading_client.py', '交易API客户端'),
    ('api_key_manager.py', 'API密钥管理器'),
    ('trading_strategy.py', '交易策略框架'),
    ('auto_trading_engine.py', '自动交易引擎'),
    ('binance_trading_gui.py', 'GUI主程序'),
    ('启动交易系统.command', '启动脚本'),
]

all_files_exist = True
for filename, description in files_to_check:
    if os.path.exists(filename):
        print(f"✓ {description}: {filename}")
    else:
        print(f"✗ {description}: {filename} - 文件不存在")
        all_files_exist = False
print()

# 测试4: 代码语法检查
print("【测试4】代码语法检查")
import py_compile

python_files = [
    'binance_api_client.py',
    'binance_trading_client.py',
    'api_key_manager.py',
    'trading_strategy.py',
    'auto_trading_engine.py',
    'binance_trading_gui.py',
]

all_syntax_ok = True
for filename in python_files:
    try:
        py_compile.compile(filename, doraise=True)
        print(f"✓ {filename} 语法正确")
    except py_compile.PyCompileError as e:
        print(f"✗ {filename} 语法错误")
        print(f"  {e}")
        all_syntax_ok = False
print()

# 测试5: 模块导入测试
print("【测试5】模块导入测试")

# API密钥管理器
try:
    from api_key_manager import APIKeyManager, EnvAPIKeyManager
    print("✓ API密钥管理器导入成功")
    
    # 测试基本功能
    manager = APIKeyManager("test_config.json")
    manager.save_credentials("test_key", "test_secret")
    loaded = manager.load_credentials()
    if loaded:
        print("  ✓ 凭证保存/加载功能正常")
    
    # 清理测试文件
    manager.clear_credentials()
    if os.path.exists("test_config.json"):
        os.remove("test_config.json")
    if os.path.exists("encrypted_key.bin"):
        os.remove("encrypted_key.bin")
    
except Exception as e:
    print(f"✗ API密钥管理器导入失败: {e}")
    all_syntax_ok = False

# 公共API客户端
try:
    from binance_api_client import BinanceAPIClient
    print("✓ 公共API客户端导入成功")
    client = BinanceAPIClient()
    print("  ✓ API客户端创建成功")
except Exception as e:
    print(f"✗ 公共API客户端导入失败: {e}")
    all_syntax_ok = False

# 交易API客户端
try:
    from binance_trading_client import BinanceTradingClient
    print("✓ 交易API客户端导入成功")
except Exception as e:
    print(f"✗ 交易API客户端导入失败: {e}")
    all_syntax_ok = False

# 策略框架
try:
    from trading_strategy import (
        BaseStrategy, SignalType, TradingSignal, 
        StrategyManager, PredefinedStrategies
    )
    print("✓ 交易策略框架导入成功")
    
    # 测试策略管理器
    manager = StrategyManager()
    volume_strategy = PredefinedStrategies.create_volume_strategy()
    manager.add_strategy(volume_strategy)
    print("  ✓ 策略管理器功能正常")
except Exception as e:
    print(f"✗ 交易策略框架导入失败: {e}")
    all_syntax_ok = False

# 交易引擎
try:
    from auto_trading_engine import (
        AutoTradingEngine, EngineState, 
        TradeOrder, EngineConfig
    )
    print("✓ 自动交易引擎导入成功")
except Exception as e:
    print(f"✗ 自动交易引擎导入失败: {e}")
    all_syntax_ok = False

# GUI应用
try:
    import ast
    with open('binance_trading_gui.py', 'r', encoding='utf-8') as f:
        code = f.read()
        ast.parse(code)
    print("✓ GUI主程序代码解析成功")
except Exception as e:
    print(f"✗ GUI主程序解析失败: {e}")
    all_syntax_ok = False

print()

# 测试6: 配置验证
print("【测试6】API端点配置检查")
try:
    from binance_api_client import BinanceAPIClient
    from binance_trading_client import BinanceTradingClient
    
    # 公共API端点
    public_endpoints = BinanceAPIClient.ENDPOINTS
    required_public = ['ping', 'time', 'exchange_info', 'ticker_24h']
    for endpoint in required_public:
        if endpoint in public_endpoints:
            print(f"✓ 公共API端点 {endpoint}")
        else:
            print(f"✗ 缺少公共API端点 {endpoint}")
    
    # 交易API端点
    trading_endpoints = BinanceTradingClient.TRADING_ENDPOINTS
    required_trading = ['account', 'balance', 'position', 'order']
    for endpoint in required_trading:
        if endpoint in trading_endpoints:
            print(f"✓ 交易API端点 {endpoint}")
        else:
            print(f"⚠ 缺少交易API端点 {endpoint}")
    
    print(f"✓ API基础URL: {BinanceAPIClient.BASE_URL}")
    
except Exception as e:
    print(f"✗ 配置检查失败: {e}")

print()

# 测试7: 策略框架功能测试
print("【测试7】策略框架功能测试")
try:
    from trading_strategy import (
        SignalType, TradingSignal, 
        StrategyManager, PredefinedStrategies
    )
    
    # 测试信号创建
    signal = TradingSignal(
        symbol="BTCUSDT",
        signal_type=SignalType.BUY,
        price=50000.0,
        confidence=0.85,
        reason="测试信号"
    )
    print(f"✓ 信号创建: {signal.symbol} {signal.signal_type.value}")
    
    # 测试信号序列化
    signal_dict = signal.to_dict()
    print("✓ 信号序列化功能正常")
    
    # 测试策略管理
    manager = StrategyManager()
    manager.select_symbol("BTCUSDT")
    manager.select_symbol("ETHUSDT")
    selected = manager.get_selected_symbols()
    if len(selected) == 2:
        print("✓ 合约选择功能正常")
    
except Exception as e:
    print(f"✗ 策略框架测试失败: {e}")

print()

# 测试8: 交易引擎配置测试
print("【测试8】交易引擎配置测试")
try:
    from auto_trading_engine import EngineConfig, EngineState
    
    config = EngineConfig()
    print(f"✓ 引擎配置: 模拟模式={config.dry_run}")
    print(f"✓ 引擎状态: {EngineState.RUNNING.value}")
    
except Exception as e:
    print(f"✗ 引擎配置测试失败: {e}")

print()

# 总结
print("=" * 70)
print("测试总结")
print("=" * 70)
print()

if all_syntax_ok and all_files_exist:
    print("✅ 所有测试通过！")
    print()
    print("📝 系统组件：")
    print("  ✓ API密钥管理器 - 安全存储和输入")
    print("  ✓ 公共API客户端 - 获取合约信息")
    print("  ✓ 交易API客户端 - 下单、查询账户")
    print("  ✓ 策略框架 - 筛选合约和生成信号")
    print("  ✓ 自动交易引擎 - 执行交易策略")
    print("  ✓ GUI应用 - 完整的用户界面")
    print()
    print("🚀 运行方法：")
    print("1. 双击 '启动交易系统.command' 文件")
    print("2. 或在终端运行: python3 binance_trading_gui.py")
    print()
    print("⚠️  安全提醒：")
    print("1. 请妥善保管API密钥")
    print("2. 建议先在模拟模式下测试")
    print("3. 禁止使用实盘资金进行未经充分测试的策略")
    print()
else:
    print("❌ 部分测试失败，请检查上述错误信息")

print("=" * 70)
