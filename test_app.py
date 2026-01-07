#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本 - 验证应用代码逻辑
"""

import sys
import platform

print("=" * 50)
print("Python GUI 应用测试")
print("=" * 50)
print()

# 检查 Python 版本
print(f"✓ Python 版本: {platform.python_version()}")
print(f"✓ 操作系统: {platform.system()} {platform.release()}")

# 检查 Tkinter
try:
    import tkinter as tk
    print(f"✓ Tkinter 已安装 (版本 {tk.TkVersion})")
except ImportError:
    print("✗ Tkinter 未安装")
    print("  注意：在 Mac 上 Tkinter 通常随 Python 一起安装")
    print("  如果未安装，请从 python.org 重新安装 Python")

# 检查主程序
try:
    with open('mac_gui_app.py', 'r', encoding='utf-8') as f:
        code = f.read()
        print(f"✓ 主程序文件存在 ({len(code)} 字节)")
except FileNotFoundError:
    print("✗ 主程序文件不存在")

# 检查启动脚本
import os
if os.path.exists('启动应用.command'):
    print("✓ 启动脚本存在")
    if os.access('启动应用.command', os.X_OK):
        print("✓ 启动脚本具有执行权限")
    else:
        print("✗ 启动脚本缺少执行权限")
else:
    print("✗ 启动脚本不存在")

print()
print("=" * 50)
print("测试完成！")
print("=" * 50)
print()
print("运行应用的方法：")
print("1. 双击 '启动应用.command' 文件")
print("2. 在终端运行: python3 mac_gui_app.py")
print()
