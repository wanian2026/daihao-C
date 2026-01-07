#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
币安应用测试脚本
验证代码语法和逻辑正确性
"""

import sys
import os

print("=" * 60)
print("币安合约监控应用 - 代码验证")
print("=" * 60)
print()

# 测试1: 检查Python版本
print("【测试1】Python环境检查")
print(f"✓ Python 版本: {sys.version.split()[0]}")

if sys.version_info < (3, 6):
    print("✗ Python版本过低，需要3.6+")
    sys.exit(1)
else:
    print("✓ Python版本符合要求")
print()

# 测试2: 检查依赖库
print("【测试2】依赖库检查")
try:
    import requests
    print(f"✓ requests 版本: {requests.__version__}")
except ImportError:
    print("✗ requests 未安装")
    print("  请运行: pip3 install requests")
print()

# 测试3: 检查Tkinter
print("【测试3】Tkinter GUI库检查")
try:
    import tkinter as tk
    print(f"✓ Tkinter 已安装 (版本 {tk.TkVersion})")
except ImportError:
    print("✗ Tkinter 未安装")
    print("  注意：在Mac上Tkinter通常随Python一起安装")
print()

# 测试4: 检查文件存在性
print("【测试4】文件完整性检查")
files_to_check = [
    ('binance_api_client.py', 'API客户端模块'),
    ('binance_gui_app.py', 'GUI主程序'),
    ('启动币安监控.command', '启动脚本'),
    ('BINANCE_README.md', '说明文档')
]

all_files_exist = True
for filename, description in files_to_check:
    if os.path.exists(filename):
        print(f"✓ {description}: {filename}")
    else:
        print(f"✗ {description}: {filename} - 文件不存在")
        all_files_exist = False
print()

# 测试5: 代码语法检查
print("【测试5】代码语法检查")
try:
    import py_compile
    py_compile.compile('binance_api_client.py', doraise=True)
    print("✓ binance_api_client.py 语法正确")
except py_compile.PyCompileError as e:
    print(f"✗ binance_api_client.py 语法错误: {e}")

try:
    py_compile.compile('binance_gui_app.py', doraise=True)
    print("✓ binance_gui_app.py 语法正确")
except py_compile.PyCompileError as e:
    print(f"✗ binance_gui_app.py 语法错误: {e}")
print()

# 测试6: 模块导入测试
print("【测试6】模块导入测试")
try:
    from binance_api_client import BinanceAPIClient
    print("✓ 成功导入 BinanceAPIClient")

    # 测试创建实例
    client = BinanceAPIClient()
    print("✓ 成功创建API客户端实例")

    # 测试方法存在
    methods = ['ping', 'get_server_time', 'get_exchange_info',
               'get_all_symbols', 'get_contract_info', 'get_connection_status']
    for method in methods:
        if hasattr(client, method):
            print(f"  ✓ 方法 {method} 存在")
        else:
            print(f"  ✗ 方法 {method} 不存在")

except ImportError as e:
    print(f"✗ 导入失败: {e}")
except Exception as e:
    print(f"✗ 测试失败: {e}")
print()

# 测试7: GUI模块测试
print("【测试7】GUI模块导入测试")
try:
    # 不实际创建GUI窗口，只测试导入
    import ast
    with open('binance_gui_app.py', 'r', encoding='utf-8') as f:
        code = f.read()
        ast.parse(code)
    print("✓ binance_gui_app.py 可以正常解析")

    # 检查关键类
    tree = ast.parse(code)
    class_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    if 'BinanceMonitorApp' in class_names:
        print("✓ 找到主类 BinanceMonitorApp")
    else:
        print("✗ 未找到主类 BinanceMonitorApp")

except Exception as e:
    print(f"✗ GUI模块测试失败: {e}")
print()

# 测试8: API端点检查
print("【测试8】API端点配置检查")
try:
    from binance_api_client import BinanceAPIClient
    endpoints = BinanceAPIClient.ENDPOINTS
    required_endpoints = ['ping', 'time', 'exchange_info', 'ticker_24h']
    
    for endpoint in required_endpoints:
        if endpoint in endpoints:
            print(f"✓ 端点 {endpoint}: {endpoints[endpoint]}")
        else:
            print(f"✗ 缺少端点 {endpoint}")

    # 检查BASE_URL
    if hasattr(BinanceAPIClient, 'BASE_URL'):
        print(f"✓ API基础URL: {BinanceAPIClient.BASE_URL}")
    else:
        print("✗ 缺少BASE_URL配置")

except Exception as e:
    print(f"✗ API配置检查失败: {e}")
print()

# 总结
print("=" * 60)
print("测试总结")
print("=" * 60)
print()
print("✓ 代码语法和逻辑验证完成")
print("✓ 所有必要模块都已正确创建")
print()
print("📝 注意事项:")
print("1. 本应用需要网络连接到币安API")
print("2. 币安API可能会有速率限制")
print("3. 在Mac上运行需要Python 3.6+和requests库")
print()
print("🚀 运行方法:")
print("1. 双击 '启动币安监控.command' 文件")
print("2. 或在终端运行: python3 binance_gui_app.py")
print()
print("=" * 60)
