#!/bin/bash
# -*- coding: utf-8 -*-
# 币安合约监控应用启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 切换到脚本目录
cd "$SCRIPT_DIR"

# 检查 Python 3 是否安装
if ! command -v python3 &> /dev/null; then
    osascript -e 'display dialog "未找到 Python 3，请先安装 Python 3。\n\n你可以从 python.org/downloads 下载安装。" buttons {"确定"} default button "确定"'
    exit 1
fi

# 检查 requests 库是否安装
python3 -c "import requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "正在安装 requests 库..."
    pip3 install requests
    if [ $? -ne 0 ]; then
        echo "安装 requests 库失败，请手动运行: pip3 install requests"
        read -p "按回车键关闭窗口..."
        exit 1
    fi
fi

# 运行币安监控应用
echo "正在启动币安合约监控应用..."
python3 binance_gui_app.py

# 如果程序异常退出，等待用户确认
read -p "按回车键关闭窗口..."
