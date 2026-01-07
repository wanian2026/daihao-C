#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
币安自动交易应用
包含登录、策略筛选、手动选择和自动交易功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
import threading
import time

from binance_api_client import BinanceAPIClient
from binance_trading_client import BinanceTradingClient
from api_key_manager import APIKeyManager
from trading_strategy import StrategyManager, PredefinedStrategies
from auto_trading_engine import AutoTradingEngine, EngineState


class BinanceTradingApp:
    """币安自动交易应用"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("币安自动交易系统")
        
        # 设置窗口大小和位置
        window_width = 1200
        window_height = 800
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 设置窗口最小尺寸
        self.root.minsize(1000, 700)
        
        # 初始化组件
        self.api_client = BinanceAPIClient()
        self.trading_client = None
        self.key_manager = APIKeyManager()
        self.strategy_manager = StrategyManager()
        self.trading_engine = None
        
        # 状态变量
        self.is_logged_in = False
        self.contract_data = []
        self.selected_contracts = set()
        
        # 创建界面
        self.create_widgets()
        
        # 初始化策略
        self.init_strategies()
    
    def create_widgets(self):
        """创建界面组件"""
        
        # 创建主框架
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # 创建Notebook（标签页）
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建各个标签页
        self.create_login_tab()
        self.create_strategy_tab()
        self.create_trading_tab()
        self.create_account_tab()
    
    def create_login_tab(self):
        """创建登录标签页"""
        login_frame = ttk.Frame(self.notebook)
        self.notebook.add(login_frame, text="🔐 登录")
        
        # 登录表单
        login_container = tk.Frame(login_frame, padx=50, pady=50)
        login_container.place(relx=0.5, rely=0.4, anchor=tk.CENTER)
        
        # 标题
        tk.Label(
            login_container,
            text="币安API登录",
            font=("Helvetica", 20, "bold")
        ).pack(pady=(0, 30))
        
        # API Key
        tk.Label(login_container, text="API Key:", font=("Helvetica", 12)).pack(anchor=tk.W)
        self.api_key_entry = tk.Entry(login_container, font=("Helvetica", 11), width=40)
        self.api_key_entry.pack(pady=(0, 15))
        
        # API Secret
        tk.Label(login_container, text="API Secret:", font=("Helvetica", 12)).pack(anchor=tk.W)
        self.api_secret_entry = tk.Entry(login_container, font=("Helvetica", 11), width=40, show="*")
        self.api_secret_entry.pack(pady=(0, 15))
        
        # 保存凭证选项
        self.save_credentials_var = tk.BooleanVar()
        tk.Checkbutton(
            login_container,
            text="保存凭证（加密存储）",
            variable=self.save_credentials_var,
            font=("Helvetica", 10)
        ).pack(pady=(0, 20))
        
        # 按钮
        button_frame = tk.Frame(login_container)
        button_frame.pack()
        
        tk.Button(
            button_frame,
            text="登录",
            command=self.login,
            bg="#4CAF50",
            fg="white",
            font=("Helvetica", 11, "bold"),
            width=15,
            height=2
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="清除保存",
            command=self.clear_saved_credentials,
            bg="#f44336",
            fg="white",
            font=("Helvetica", 11),
            width=15,
            height=2
        ).pack(side=tk.LEFT, padx=5)
        
        # 登录状态
        self.login_status_label = tk.Label(
            login_container,
            text="未登录",
            fg="gray",
            font=("Helvetica", 12)
        )
        self.login_status_label.pack(pady=(30, 0))
        
        # 加载已保存的凭证
        self.load_saved_credentials()
    
    def create_strategy_tab(self):
        """创建策略标签页"""
        strategy_frame = ttk.Frame(self.notebook)
        self.notebook.add(strategy_frame, text="📊 策略筛选")
        
        # 顶部控制栏
        control_frame = tk.Frame(strategy_frame, padx=10, pady=10)
        control_frame.pack(fill=tk.X)
        
        tk.Button(
            control_frame,
            text="🔄 执行策略",
            command=self.execute_strategies,
            bg="#4CAF50",
            fg="white",
            font=("Helvetica", 11, "bold"),
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        self.strategy_info_label = tk.Label(
            control_frame,
            text="策略数量: 0",
            font=("Helvetica", 10)
        )
        self.strategy_info_label.pack(side=tk.RIGHT, padx=10)
        
        # 策略结果表格
        table_frame = tk.Frame(strategy_frame, padx=10, pady=10)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建Treeview
        columns = ("symbol", "strategy_name", "signal_type", "confidence", "reason")
        self.strategy_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        # 设置列标题
        self.strategy_tree.heading("symbol", text="合约")
        self.strategy_tree.heading("strategy_name", text="策略名称")
        self.strategy_tree.heading("signal_type", text="信号类型")
        self.strategy_tree.heading("confidence", text="置信度")
        self.strategy_tree.heading("reason", text="原因")
        
        # 设置列宽
        self.strategy_tree.column("symbol", width=150, anchor=tk.CENTER)
        self.strategy_tree.column("strategy_name", width=200, anchor=tk.CENTER)
        self.strategy_tree.column("signal_type", width=100, anchor=tk.CENTER)
        self.strategy_tree.column("confidence", width=100, anchor=tk.CENTER)
        self.strategy_tree.column("reason", width=300, anchor=tk.W)
        
        # 添加滚动条
        scrollbar_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.strategy_tree.yview)
        scrollbar_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.strategy_tree.xview)
        self.strategy_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # 布局
        self.strategy_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
    
    def create_trading_tab(self):
        """创建交易标签页"""
        trading_frame = ttk.Frame(self.notebook)
        self.notebook.add(trading_frame, text="💹 自动交易")
        
        # 顶部控制面板
        control_frame = tk.LabelFrame(trading_frame, text="交易控制", padx=10, pady=10)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 左侧：引擎控制
        engine_frame = tk.Frame(control_frame)
        engine_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Label(engine_frame, text="引擎状态:", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky=tk.W)
        self.engine_status_label = tk.Label(
            engine_frame,
            text="未启动",
            fg="gray",
            font=("Helvetica", 10)
        )
        self.engine_status_label.grid(row=0, column=1, sticky=tk.W, padx=10)
        
        self.start_engine_btn = tk.Button(
            engine_frame,
            text="▶️ 启动引擎",
            command=self.start_engine,
            bg="#4CAF50",
            fg="white",
            font=("Helvetica", 10, "bold"),
            width=15
        )
        self.start_engine_btn.grid(row=1, column=0, columnspan=2, pady=10)
        
        # 模拟模式开关
        self.dry_run_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            engine_frame,
            text="模拟模式（不实际下单）",
            variable=self.dry_run_var,
            font=("Helvetica", 10)
        ).grid(row=2, column=0, columnspan=2, pady=5)
        
        # 右侧：已选合约
        selected_frame = tk.Frame(control_frame)
        selected_frame.pack(side=tk.LEFT, padx=30)
        
        tk.Label(selected_frame, text="已选合约:", font=("Helvetica", 10, "bold")).pack(anchor=tk.W)
        
        # 已选合约列表
        self.selected_listbox = tk.Listbox(
            selected_frame,
            height=5,
            width=30,
            font=("Courier", 10)
        )
        self.selected_listbox.pack(pady=5)
        
        # 移除按钮
        tk.Button(
            selected_frame,
            text="移除选中",
            command=self.remove_selected_contract,
            bg="#f44336",
            fg="white",
            font=("Helvetica", 10),
            width=15
        ).pack(pady=5)
        
        # 交易日志
        log_frame = tk.LabelFrame(trading_frame, text="交易日志", padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.trading_log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            font=("Courier", 9),
            wrap=tk.WORD
        )
        self.trading_log_text.pack(fill=tk.BOTH, expand=True)
    
    def create_account_tab(self):
        """创建账户标签页"""
        account_frame = ttk.Frame(self.notebook)
        self.notebook.add(account_frame, text="💰 账户信息")
        
        # 顶部控制
        control_frame = tk.Frame(account_frame, padx=10, pady=10)
        control_frame.pack(fill=tk.X)
        
        tk.Button(
            control_frame,
            text="🔄 刷新账户",
            command=self.refresh_account,
            bg="#2196F3",
            fg="white",
            font=("Helvetica", 11, "bold"),
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        # 账户信息显示
        info_frame = tk.LabelFrame(account_frame, text="账户详情", padx=10, pady=10)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.account_info_text = scrolledtext.ScrolledText(
            info_frame,
            height=20,
            font=("Courier", 10),
            wrap=tk.WORD
        )
        self.account_info_text.pack(fill=tk.BOTH, expand=True)
        
        self.account_info_text.insert(tk.END, "请先登录以查看账户信息\n")
        self.account_info_text.config(state=tk.DISABLED)
    
    def init_strategies(self):
        """初始化策略"""
        # 添加预定义策略
        volume_strategy = PredefinedStrategies.create_volume_strategy()
        self.strategy_manager.add_strategy(volume_strategy)
        
        price_strategy = PredefinedStrategies.create_price_strategy()
        self.strategy_manager.add_strategy(price_strategy)
        
        # 更新信息
        self.strategy_info_label.config(
            text=f"策略数量: {len(self.strategy_manager.list_strategies())}"
        )
    
    def load_saved_credentials(self):
        """加载已保存的凭证"""
        if self.key_manager.has_credentials():
            credentials = self.key_manager.load_credentials()
            if credentials:
                api_key, api_secret, _ = credentials
                self.api_key_entry.delete(0, tk.END)
                self.api_key_entry.insert(0, api_key)
                self.api_secret_entry.delete(0, tk.END)
                self.api_secret_entry.insert(0, api_secret)
                self.save_credentials_var.set(True)
    
    def login(self):
        """登录"""
        api_key = self.api_key_entry.get().strip()
        api_secret = self.api_secret_entry.get().strip()
        
        if not api_key or not api_secret:
            messagebox.showerror("错误", "请输入API Key和API Secret")
            return
        
        # 验证凭证格式
        if not self.key_manager.validate_credentials(api_key, api_secret):
            messagebox.showerror("错误", "凭证格式不正确")
            return
        
        self.login_status_label.config(text="正在连接...", fg="orange")
        
        # 创建交易客户端
        self.trading_client = BinanceTradingClient(api_key, api_secret)
        
        # 在线程中测试连接
        def login_thread():
            result = self.trading_client.test_connection()
            if result['success']:
                # 登录成功
                self.is_logged_in = True
                
                # 保存凭证（如果勾选）
                if self.save_credentials_var.get():
                    self.key_manager.save_credentials(api_key, api_secret)
                
                # 更新UI
                self.root.after(0, self.on_login_success)
            else:
                # 登录失败
                self.root.after(0, lambda: self.on_login_failed(result['message']))
        
        threading.Thread(target=login_thread, daemon=True).start()
    
    def on_login_success(self):
        """登录成功"""
        self.login_status_label.config(text="✓ 登录成功", fg="green")
        messagebox.showinfo("成功", "API登录成功！")
        
        # 切换到策略标签页
        self.notebook.select(1)
        
        # 自动加载合约数据
        self.load_contracts()
    
    def on_login_failed(self, error_msg):
        """登录失败"""
        self.login_status_label.config(text="✗ 登录失败", fg="red")
        messagebox.showerror("错误", f"登录失败：{error_msg}")
    
    def clear_saved_credentials(self):
        """清除保存的凭证"""
        self.key_manager.clear_credentials()
        self.api_key_entry.delete(0, tk.END)
        self.api_secret_entry.delete(0, tk.END)
        messagebox.showinfo("成功", "已清除保存的凭证")
    
    def load_contracts(self):
        """加载合约数据"""
        self.contract_data = self.trading_client.get_contract_info()
        self.log_trading(f"已加载 {len(self.contract_data)} 个合约")
    
    def execute_strategies(self):
        """执行策略"""
        if not self.is_logged_in:
            messagebox.showwarning("警告", "请先登录")
            return
        
        # 清空表格
        for item in self.strategy_tree.get_children():
            self.strategy_tree.delete(item)
        
        # 执行策略
        results = self.strategy_manager.execute_all(self.contract_data, {})
        
        # 显示结果
        for strategy_name, result in results.items():
            for signal in result.signals:
                self.strategy_tree.insert("", tk.END, values=(
                    signal.symbol,
                    strategy_name,
                    signal.signal_type.value,
                    f"{signal.confidence:.2f}",
                    signal.reason
                ))
        
        self.log_trading(f"策略执行完成，共生成 {sum(len(r.signals) for r in results.values())} 个信号")
    
    def start_engine(self):
        """启动交易引擎"""
        if not self.is_logged_in:
            messagebox.showwarning("警告", "请先登录")
            return
        
        if not self.trading_engine:
            # 创建引擎
            self.trading_engine = AutoTradingEngine(self.trading_client, self.strategy_manager)
            
            # 设置配置
            self.trading_engine.config.dry_run = self.dry_run_var.get()
            
            # 设置回调
            self.trading_engine.on_signal_callback = self.on_trading_signal
            self.trading_engine.on_order_callback = self.on_trading_order
            self.trading_engine.on_error_callback = self.on_trading_error
        
        # 启动引擎
        if self.trading_engine.state == EngineState.STOPPED:
            self.trading_engine.start()
            self.start_engine_btn.config(text="⏸️ 停止引擎", bg="#f44336")
            self.engine_status_label.config(text="运行中", fg="green")
            self.log_trading("交易引擎已启动")
        else:
            self.trading_engine.stop()
            self.start_engine_btn.config(text="▶️ 启动引擎", bg="#4CAF50")
            self.engine_status_label.config(text="已停止", fg="gray")
            self.log_trading("交易引擎已停止")
    
    def on_trading_signal(self, signal):
        """交易信号回调"""
        self.log_trading(f"信号: {signal.symbol} {signal.signal_type.value} - {signal.reason}")
    
    def on_trading_order(self, order):
        """订单回调"""
        self.log_trading(f"订单: {order.symbol} {order.side} {order.status}")
    
    def on_trading_error(self, error):
        """错误回调"""
        self.log_trading(f"错误: {error}")
    
    def remove_selected_contract(self):
        """移除选中的合约"""
        selection = self.selected_listbox.curselection()
        if selection:
            index = selection[0]
            symbol = self.selected_listbox.get(index)
            self.selected_listbox.delete(index)
            self.strategy_manager.unselect_symbol(symbol)
            self.log_trading(f"已移除合约: {symbol}")
    
    def refresh_account(self):
        """刷新账户信息"""
        if not self.is_logged_in:
            messagebox.showwarning("警告", "请先登录")
            return
        
        # 获取账户信息
        account_info = self.trading_client.get_account_info()
        balance = self.trading_client.get_balance()
        positions = self.trading_client.get_positions()
        
        # 更新显示
        self.account_info_text.config(state=tk.NORMAL)
        self.account_info_text.delete(1.0, tk.END)
        
        self.account_info_text.insert(tk.END, "="*50 + "\n")
        self.account_info_text.insert(tk.END, "账户信息\n")
        self.account_info_text.insert(tk.END, "="*50 + "\n\n")
        
        if account_info.get('error'):
            self.account_info_text.insert(tk.END, f"错误: {account_info.get('message')}\n")
        else:
            self.account_info_text.insert(tk.END, f"总余额: {account_info.get('totalWalletBalance', 0)} USDT\n")
            self.account_info_text.insert(tk.END, f"可用余额: {account_info.get('availableBalance', 0)} USDT\n\n")
        
        self.account_info_text.insert(tk.END, "="*50 + "\n")
        self.account_info_text.insert(tk.END, "持仓信息\n")
        self.account_info_text.insert(tk.END, "="*50 + "\n\n")
        
        for pos in positions:
            if float(pos.get('positionAmt', 0)) != 0:
                self.account_info_text.insert(tk.END, f"合约: {pos.get('symbol')}\n")
                self.account_info_text.insert(tk.END, f"  方向: {pos.get('positionSide')}\n")
                self.account_info_text.insert(tk.END, f"  数量: {pos.get('positionAmt')}\n")
                self.account_info_text.insert(tk.END, f"  入场价: {pos.get('entryPrice')}\n")
                self.account_info_text.insert(tk.END, f"  未实现盈亏: {pos.get('unRealizedProfit')} USDT\n\n")
        
        self.account_info_text.config(state=tk.DISABLED)
    
    def log_trading(self, message: str):
        """记录交易日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.trading_log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.trading_log_text.see(tk.END)


def main():
    """主函数"""
    root = tk.Tk()
    app = BinanceTradingApp(root)
    
    # 窗口关闭时的处理
    def on_closing():
        if app.trading_engine:
            app.trading_engine.stop()
        if messagebox.askokcancel("退出", "确定要退出应用吗？"):
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
