#!/bin/bash
# -*- coding: utf-8 -*-
# 币安自动交易系统启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 切换到脚本目录
cd "$SCRIPT_DIR"

# 检查 Python 3 是否安装
if ! command -v python3 &> /dev/null; then
    osascript -e 'display dialog "未找到 Python 3，请先安装 Python 3。\n\n你可以从 python.org/downloads 下载安装。" buttons {"确定"} default button "确定"'
    exit 1
fi

# 检查依赖库
python3 -c "import requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "正在安装 requests 库..."
    pip3 install requests
fi

python3 -c "import cryptography" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "正在安装 cryptography 库..."
    pip3 install cryptography
fi

# 运行交易系统
echo "正在启动币安自动交易系统..."
echo ""
echo "⚠️  重要提示："
echo "1. 请妥善保管您的API密钥"
echo "2. 建议先在模拟模式下测试策略"
echo "3. 禁止使用实盘资金进行测试"
echo ""
echo "按回车键继续..."
read

python3 binance_trading_gui.py

# 如果程序异常退出，等待用户确认
read -p "按回车键关闭窗口..."
