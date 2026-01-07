#!/bin/bash
# -*- coding: utf-8 -*-
# ETH 5m假突破策略系统启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 切换到脚本目录
cd "$SCRIPT_DIR"

# 检查 Python 3
if ! command -v python3 &> /dev/null; then
    osascript -e 'display dialog "未找到 Python 3，请先安装 Python 3。\n\n你可以从 python.org/downloads 下载安装。" buttons {"确定"} default button "确定"'
    exit 1
fi

# 检查依赖
echo "检查依赖..."

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

python3 -c "import python-docx" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "正在安装 python-docx 库..."
    pip3 install python-docx
fi

echo ""
echo "========================================"
echo "  ETH 5m 假突破策略系统"
echo "========================================"
echo ""
echo "策略说明："
echo "- 识别结构极值（摆动高低点）"
echo "- 检测失败突破（假突破）"
echo "- 多层过滤机制"
echo "- 自动风险管理"
echo ""
echo "⚠️  重要提示："
echo "1. 建议先在模拟模式下测试"
echo "2. 请妥善保管API密钥"
echo "3. 禁止使用实盘资金进行未经充分测试的策略"
echo ""
echo "按回车键启动..."
read

# 运行应用
python3 eth_fakeout_gui.py

# 如果程序异常退出
read -p "按回车键关闭窗口..."
