#!/bin/bash
# FVG流动性策略系统 - macOS启动脚本
# 双击此文件即可启动应用

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 切换到脚本目录
cd "$SCRIPT_DIR"

# 检查Python3是否安装
if ! command -v python3 &> /dev/null; then
    osascript -e 'display dialog "未找到Python3，请先安装Python3。\n\n推荐使用Homebrew安装：\nbrew install python3" buttons={"确定"} default button 1 with title "错误"'
    exit 1
fi

# 检查依赖是否安装
if ! python3 -c "import requests" 2>/dev/null; then
    osascript -e 'display dialog "缺少必要的依赖包，正在自动安装..." buttons={"确定"} default button 1 with title "提示"'
    python3 -m pip install requests python-docx cryptography
fi

# 启动应用
python3 eth_fakeout_gui.py
