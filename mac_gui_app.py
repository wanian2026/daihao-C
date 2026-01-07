#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的 Mac 桌面 GUI 应用
这是一个可以在 Mac 桌面直接双击运行的 Python 应用
"""

import tkinter as tk
from tkinter import messagebox, ttk
import platform
from datetime import datetime


class SimpleGUIApp:
    """简单的 GUI 应用程序类"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("我的桌面应用")
        
        # 设置窗口大小和位置
        window_width = 500
        window_height = 400
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 设置窗口最小尺寸
        self.root.minsize(400, 300)
        
        # 初始化界面
        self.create_widgets()
        
    def create_widgets(self):
        """创建界面组件"""
        
        # 顶部标题栏
        header_frame = tk.Frame(self.root, bg="#4A90E2", height=60)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="🖥️ 简单桌面应用",
            bg="#4A90E2",
            fg="white",
            font=("Helvetica", 16, "bold")
        )
        title_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # 主要内容区域
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 欢迎标签
        welcome_label = tk.Label(
            main_frame,
            text="欢迎使用 Python GUI 应用！",
            font=("Helvetica", 12)
        )
        welcome_label.pack(pady=(0, 10))
        
        # 系统信息
        info_text = f"系统: {platform.system()} {platform.release()}\nPython 版本: {platform.python_version()}"
        info_label = tk.Label(
            main_frame,
            text=info_text,
            font=("Helvetica", 10),
            fg="gray"
        )
        info_label.pack(pady=(0, 20))
        
        # 输入区域
        input_frame = tk.LabelFrame(main_frame, text="输入消息", padx=10, pady=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.message_entry = tk.Entry(input_frame, font=("Helvetica", 11))
        self.message_entry.pack(fill=tk.X, pady=5)
        self.message_entry.bind("<Return>", self.show_message)  # 绑定回车键
        
        # 按钮区域
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        show_btn = tk.Button(
            button_frame,
            text="显示消息",
            command=self.show_message,
            bg="#4CAF50",
            fg="white",
            font=("Helvetica", 10, "bold"),
            padx=20,
            pady=5
        )
        show_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        clear_btn = tk.Button(
            button_frame,
            text="清空",
            command=self.clear_input,
            bg="#f44336",
            fg="white",
            font=("Helvetica", 10),
            padx=20,
            pady=5
        )
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # 时间按钮
        time_btn = tk.Button(
            button_frame,
            text="显示时间",
            command=self.show_time,
            bg="#2196F3",
            fg="white",
            font=("Helvetica", 10),
            padx=20,
            pady=5
        )
        time_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 输出区域
        output_frame = tk.LabelFrame(main_frame, text="输出", padx=10, pady=10)
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        self.output_text = tk.Text(
            output_frame,
            height=8,
            font=("Courier", 10),
            wrap=tk.WORD
        )
        scrollbar = tk.Scrollbar(output_frame, orient=tk.VERTICAL, command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=scrollbar.set)
        
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 状态栏
        self.status_bar = tk.Label(
            self.root,
            text="就绪",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def show_message(self, event=None):
        """显示输入的消息"""
        message = self.message_entry.get().strip()
        if message:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            output = f"[{timestamp}] {message}\n"
            self.output_text.insert(tk.END, output)
            self.output_text.see(tk.END)
            self.status_bar.config(text=f"已显示: {message}")
            self.message_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("提示", "请输入消息！")
            self.status_bar.config(text="请输入消息")
            
    def clear_input(self):
        """清空输入和输出"""
        self.message_entry.delete(0, tk.END)
        self.output_text.delete(1.0, tk.END)
        self.status_bar.config(text="已清空")
        
    def show_time(self):
        """显示当前时间"""
        current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        self.message_entry.delete(0, tk.END)
        self.message_entry.insert(0, current_time)
        self.status_bar.config(text=f"当前时间: {current_time}")


def main():
    """主函数"""
    root = tk.Tk()
    
    # 尝试设置 Mac 风格的外观
    try:
        from ctypes import cdll, c_int, c_void_p, c_char_p
        # macOS 特定的外观设置
        pass
    except:
        pass
    
    app = SimpleGUIApp(root)
    
    # 窗口关闭时的处理
    def on_closing():
        if messagebox.askokcancel("退出", "确定要退出应用吗？"):
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 启动应用
    root.mainloop()


if __name__ == "__main__":
    main()
