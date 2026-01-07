#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
币安合约信息监控应用
实时显示币安平台合约信息和连接状态
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
import threading
import time

from binance_api_client import BinanceAPIClient


class BinanceMonitorApp:
    """币安合约监控应用"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("币安合约信息监控")
        
        # 设置窗口大小和位置
        window_width = 1000
        window_height = 700
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 设置窗口最小尺寸
        self.root.minsize(800, 600)
        
        # 初始化API客户端
        self.api_client = BinanceAPIClient()
        self.is_monitoring = False
        self.monitor_thread = None
        self.contract_data = []
        
        # 创建界面
        self.create_widgets()
        
        # 启动后自动连接
        self.root.after(500, self.auto_connect)
    
    def create_widgets(self):
        """创建界面组件"""
        
        # 顶部标题和状态栏
        header_frame = tk.Frame(self.root, bg="#2E7D32", height=80)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # 标题
        title_label = tk.Label(
            header_frame,
            text="📊 币安合约信息监控",
            bg="#2E7D32",
            fg="white",
            font=("Helvetica", 18, "bold")
        )
        title_label.pack(pady=(10, 5))
        
        # 连接状态显示
        self.status_label = tk.Label(
            header_frame,
            text="⚪ 未连接",
            bg="#2E7D32",
            fg="#FFD700",
            font=("Helvetica", 12, "bold")
        )
        self.status_label.pack(pady=5)
        
        # 主要内容区域
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 控制按钮区域
        control_frame = tk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.connect_btn = tk.Button(
            control_frame,
            text="🔗 连接币安",
            command=self.connect_binance,
            bg="#4CAF50",
            fg="white",
            font=("Helvetica", 11, "bold"),
            width=15,
            height=2
        )
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        self.refresh_btn = tk.Button(
            control_frame,
            text="🔄 刷新数据",
            command=self.refresh_data,
            bg="#2196F3",
            fg="white",
            font=("Helvetica", 11, "bold"),
            width=15,
            height=2,
            state=tk.DISABLED
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        self.monitor_btn = tk.Button(
            control_frame,
            text="▶️ 开始监控",
            command=self.toggle_monitoring,
            bg="#FF9800",
            fg="white",
            font=("Helvetica", 11, "bold"),
            width=15,
            height=2,
            state=tk.DISABLED
        )
        self.monitor_btn.pack(side=tk.LEFT, padx=5)
        
        # 合约信息统计
        self.info_label = tk.Label(
            control_frame,
            text="合约数量: 0",
            font=("Helvetica", 10),
            fg="gray"
        )
        self.info_label.pack(side=tk.RIGHT, padx=10)
        
        # 搜索框
        search_frame = tk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            search_frame,
            text="🔍 搜索合约:",
            font=("Helvetica", 10)
        ).pack(side=tk.LEFT, padx=5)
        
        self.search_entry = tk.Entry(
            search_frame,
            font=("Helvetica", 10),
            width=20
        )
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<KeyRelease>", self.filter_contracts)
        
        # 合约信息表格
        table_frame = tk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建Treeview
        columns = ("symbol", "base", "quote", "type", "price_precision", "quantity_precision")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        # 设置列标题
        self.tree.heading("symbol", text="交易对")
        self.tree.heading("base", text="基础资产")
        self.tree.heading("quote", text="计价资产")
        self.tree.heading("type", text="合约类型")
        self.tree.heading("price_precision", text="价格精度")
        self.tree.heading("quantity_precision", text="数量精度")
        
        # 设置列宽
        self.tree.column("symbol", width=150, anchor=tk.CENTER)
        self.tree.column("base", width=100, anchor=tk.CENTER)
        self.tree.column("quote", width=100, anchor=tk.CENTER)
        self.tree.column("type", width=120, anchor=tk.CENTER)
        self.tree.column("price_precision", width=100, anchor=tk.CENTER)
        self.tree.column("quantity_precision", width=100, anchor=tk.CENTER)
        
        # 添加滚动条
        scrollbar_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # 布局
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # 日志输出区域
        log_frame = tk.LabelFrame(main_frame, text="📋 系统日志", padx=5, pady=5)
        log_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=6,
            font=("Courier", 9),
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 状态栏
        self.status_bar = tk.Label(
            self.root,
            text="就绪 - 等待连接",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def log_message(self, message: str):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.status_bar.config(text=message)
    
    def update_connection_status(self):
        """更新连接状态显示"""
        status_info = self.api_client.get_connection_status()
        status = status_info['status']
        
        if status == 'connected':
            self.status_label.config(text="🟢 已连接", fg="#4CAF50")
            self.connect_btn.config(text="🔌 断开连接", bg="#f44336")
            self.refresh_btn.config(state=tk.NORMAL)
            self.monitor_btn.config(state=tk.NORMAL)
        elif status == 'disconnected':
            self.status_label.config(text="⚪ 未连接", fg="#FFD700")
            self.connect_btn.config(text="🔗 连接币安", bg="#4CAF50")
            self.refresh_btn.config(state=tk.DISABLED)
            self.monitor_btn.config(state=tk.DISABLED)
        elif status == 'timeout':
            self.status_label.config(text="🟡 连接超时", fg="#FF9800")
        else:
            self.status_label.config(text="🔴 连接错误", fg="#f44336")
        
        if status_info['server_time']:
            server_time = status_info['server_time']
            dt = datetime.fromtimestamp(server_time / 1000)
            self.status_label.config(text=f"🟢 已连接 (服务器: {dt.strftime('%H:%M:%S')})", fg="#4CAF50")
    
    def connect_binance(self):
        """连接币安API"""
        if self.api_client.connection_status == 'connected':
            # 断开连接
            self.api_client.connection_status = 'disconnected'
            self.is_monitoring = False
            self.log_message("已断开连接")
            self.update_connection_status()
            return
        
        self.log_message("正在连接币安API...")
        
        # 在线程中执行连接，避免阻塞UI
        def connect_thread():
            if self.api_client.ping():
                self.root.after(0, lambda: self.on_connect_success())
            else:
                self.root.after(0, lambda: self.on_connect_failed())
        
        threading.Thread(target=connect_thread, daemon=True).start()
    
    def on_connect_success(self):
        """连接成功回调"""
        self.log_message("✓ 连接成功！")
        self.update_connection_status()
        
        # 自动获取合约数据
        self.refresh_data()
    
    def on_connect_failed(self):
        """连接失败回调"""
        self.log_message("✗ 连接失败！请检查网络连接")
        self.update_connection_status()
    
    def refresh_data(self):
        """刷新合约数据"""
        if self.api_client.connection_status != 'connected':
            self.log_message("请先连接币安API")
            return
        
        self.log_message("正在获取合约信息...")
        self.refresh_btn.config(state=tk.DISABLED)
        
        # 在线程中执行数据获取
        def fetch_thread():
            try:
                contracts = self.api_client.get_contract_info()
                self.contract_data = contracts
                self.root.after(0, lambda: self.update_contract_table(contracts))
                self.root.after(0, lambda: self.log_message(f"✓ 成功获取 {len(contracts)} 个合约信息"))
                self.root.after(0, lambda: self.info_label.config(text=f"合约数量: {len(contracts)}"))
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"✗ 获取数据失败: {str(e)}"))
            finally:
                self.root.after(0, lambda: self.refresh_btn.config(state=tk.NORMAL))
        
        threading.Thread(target=fetch_thread, daemon=True).start()
    
    def update_contract_table(self, contracts: list):
        """更新合约信息表格"""
        # 清空表格
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 添加数据
        for contract in contracts:
            self.tree.insert("", tk.END, values=(
                contract['symbol'],
                contract['baseAsset'],
                contract['quoteAsset'],
                contract['contractType'],
                contract['pricePrecision'],
                contract['quantityPrecision']
            ))
    
    def filter_contracts(self, event=None):
        """过滤合约"""
        search_text = self.search_entry.get().upper().strip()
        
        # 清空表格
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 过滤并添加数据
        for contract in self.contract_data:
            symbol = contract['symbol']
            if search_text in symbol:
                self.tree.insert("", tk.END, values=(
                    contract['symbol'],
                    contract['baseAsset'],
                    contract['quoteAsset'],
                    contract['contractType'],
                    contract['pricePrecision'],
                    contract['quantityPrecision']
                ))
    
    def toggle_monitoring(self):
        """切换监控状态"""
        if self.is_monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()
    
    def start_monitoring(self):
        """开始监控"""
        self.is_monitoring = True
        self.monitor_btn.config(text="⏸️ 停止监控", bg="#f44336")
        self.log_message("开始实时监控...")
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        self.monitor_btn.config(text="▶️ 开始监控", bg="#FF9800")
        self.log_message("停止监控")
    
    def monitor_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 检查连接状态
                self.api_client.ping()
                
                # 更新UI状态
                self.root.after(0, self.update_connection_status)
                
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"监控错误: {str(e)}"))
            
            # 每5秒检查一次
            time.sleep(5)
    
    def auto_connect(self):
        """自动连接"""
        self.log_message("正在初始化，自动连接币安API...")
        self.root.after(500, self.connect_binance)


def main():
    """主函数"""
    root = tk.Tk()
    app = BinanceMonitorApp(root)
    
    # 窗口关闭时的处理
    def on_closing():
        app.is_monitoring = False
        if messagebox.askokcancel("退出", "确定要退出应用吗？"):
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
