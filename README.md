# Mac 桌面 GUI 应用

这是一个简单但功能完善的 Python GUI 应用程序，可以在 Mac 桌面上直接运行。

## 功能特性

- ✅ 现代化的图形界面
- ✅ 消息输入和显示
- ✅ 实时时间显示
- ✅ 系统信息展示
- ✅ 支持键盘快捷键（回车发送消息）
- ✅ 输出历史记录
- ✅ 窗口居中显示

## 运行方法

### 方法一：双击运行（推荐）

1. 确保你的 Mac 已安装 Python 3
   - 在终端中运行 `python3 --version` 检查
   - 如果未安装，访问 https://www.python.org/downloads/ 下载安装

2. 双击 `启动应用.command` 文件即可启动应用
   - 首次运行可能会提示"无法验证开发者"，选择"打开"即可
   - 应用将在新终端窗口中运行

### 方法二：命令行运行

在终端中执行：

```bash
python3 mac_gui_app.py
```

或者先添加执行权限：

```bash
chmod +x mac_gui_app.py
./mac_gui_app.py
```

## 使用说明

### 基本操作

1. **输入消息**：在输入框中输入文字
2. **显示消息**：点击"显示消息"按钮或按回车键
3. **清空内容**：点击"清空"按钮清除所有输入和输出
4. **显示时间**：点击"显示时间"按钮，当前时间会自动填入输入框

### 输出区域

- 所有显示的消息都会记录在输出区域
- 每条消息都带有时间戳
- 支持滚动查看历史记录

### 退出应用

- 点击窗口左上角的红色关闭按钮
- 在弹出的确认框中点击"确定"

## 打包为 .app 应用（可选）

如果你想将应用打包成 Mac 原生的 .app 应用程序，可以使用以下方法：

### 使用 py2app

1. 安装 py2app：
```bash
pip3 install py2app
```

2. 创建 setup.py：
```python
from setuptools import setup

APP = ['mac_gui_app.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'packages': ['tkinter'],
    'iconfile': None,
    'plist': {
        'CFBundleName': "桌面应用",
        'CFBundleDisplayName': "桌面应用",
        'CFBundleGetInfoString': "我的桌面应用",
        'CFBundleIdentifier': "com.example.desktopapp",
        'CFBundleVersion': "1.0.0",
        'CFBundleShortVersionString': "1.0.0",
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
```

3. 构建应用：
```bash
python3 setup.py py2app
```

4. 在 `dist` 目录中找到生成的 .app 应用

### 使用 PyInstaller

1. 安装 PyInstaller：
```bash
pip3 install pyinstaller
```

2. 打包应用：
```bash
pyinstaller --onefile --windowed --name="桌面应用" mac_gui_app.py
```

3. 在 `dist` 目录中找到可执行文件

## 系统要求

- macOS 10.12 或更高版本
- Python 3.6 或更高版本

## 故障排除

### 问题：双击 .command 文件没有反应

**解决方案**：
1. 打开"系统偏好设置" > "安全性与隐私"
2. 找到"已阻止的应用"并点击"仍要打开"
3. 或者在终端中运行：`chmod +x 启动应用.command`

### 问题：提示"未找到 Python 3"

**解决方案**：
1. 访问 https://www.python.org/downloads/
2. 下载并安装最新版本的 Python 3
3. 重新运行应用

### 问题：窗口显示异常或字体显示不正常

**解决方案**：
- Tkinter 使用系统默认字体，不同的 Mac 系统可能显示略有差异
- 这是正常现象，不影响功能使用

## 自定义开发

如果你想修改这个应用，可以编辑 `mac_gui_app.py` 文件：

- 修改窗口大小：调整 `window_width` 和 `window_height` 变量
- 修改界面颜色：调整各组件的 `bg`（背景色）和 `fg`（前景色）参数
- 添加新功能：在 `SimpleGUIApp` 类中添加新的方法

## 技术栈

- **语言**：Python 3
- **GUI 框架**：Tkinter（Python 内置）
- **平台**：macOS

## 许可证

本项目仅供学习和个人使用。

## 联系方式

如有问题或建议，欢迎反馈。
