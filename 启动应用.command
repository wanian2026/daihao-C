#!/bin/bash
# -*- coding: utf-8 -*-
# 这是一个 Mac 可执行脚本，双击即可运行 Python GUI 应用

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 切换到脚本目录
cd "$SCRIPT_DIR"

# 检查 Python 3 是否安装
if ! command -v python3 &> /dev/null; then
    osascript -e 'display dialog "未找到 Python 3，请先安装 Python 3。\n\n你可以从 python.org/downloads 下载安装。" buttons {"确定"} default button "确定"'
    exit 1
fi

# 运行 Python 应用
python3 mac_gui_app.py

# 如果程序异常退出，等待用户确认
read -p "按回车键关闭窗口..."
