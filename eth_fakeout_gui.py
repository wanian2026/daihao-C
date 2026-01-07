#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETH 5m假突破策略 - 完整GUI应用
集成所有策略模块，提供可视化的交易界面
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
import threading
import time

from binance_api_client import BinanceAPIClient
from binance_trading_client import BinanceTradingClient
from api_key_manager import APIKeyManager
from eth_fakeout_strategy_system import MultiSymbolFakeoutSystem, SystemState
from symbol_selector import SelectionMode


class ETHFakeoutGUI:
    """ETH假突破策略GUI应用"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("ETH 5m 假突破策略系统")
        
        # 设置窗口大小和位置
        window_width = 1400
        window_height = 900
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 设置窗口最小尺寸
        self.root.minsize(1200, 800)
        
        # 初始化组件
        self.api_client = BinanceAPIClient()
        self.trading_client = None
        self.key_manager = APIKeyManager()
        self.strategy_system = None
        
        # 状态变量
        self.is_logged_in = False
        self.current_market_state = "未知"
        self.current_score = 0
        
        # 创建界面
        self.create_widgets()
        
        # 加载已保存的凭证
        self.load_saved_credentials()
    
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
        self.create_symbol_selector_tab()  # 新增标的选择标签页
        self.create_monitor_tab()
        self.create_signals_tab()
        self.create_risk_tab()
        self.create_trading_tab()
    
    def create_login_tab(self):
        """创建登录标签页"""
        login_frame = ttk.Frame(self.notebook)
        self.notebook.add(login_frame, text="🔐 登录")
        
        # 登录表单
        login_container = tk.Frame(login_frame, padx=80, pady=80)
        login_container.place(relx=0.5, rely=0.4, anchor=tk.CENTER)
        
        # 标题
        tk.Label(
            login_container,
            text="ETH 5m 假突破策略系统",
            font=("Helvetica", 24, "bold"),
            fg="#2E7D32"
        ).pack(pady=(0, 10))
        
        tk.Label(
            login_container,
            text="识别结构极值与失败突破",
            font=("Helvetica", 14),
            fg="gray"
        ).pack(pady=(0, 40))
        
        # API Key
        tk.Label(login_container, text="API Key:", font=("Helvetica", 12)).pack(anchor=tk.W)
        self.api_key_entry = tk.Entry(login_container, font=("Helvetica", 11), width=50)
        self.api_key_entry.pack(pady=(0, 15))
        
        # API Secret
        tk.Label(login_container, text="API Secret:", font=("Helvetica", 12)).pack(anchor=tk.W)
        self.api_secret_entry = tk.Entry(login_container, font=("Helvetica", 11), width=50, show="*")
        self.api_secret_entry.pack(pady=(0, 15))
        
        # 保存凭证选项
        self.save_credentials_var = tk.BooleanVar()
        tk.Checkbutton(
            login_container,
            text="保存凭证（加密存储）",
            variable=self.save_credentials_var,
            font=("Helvetica", 10)
        ).pack(pady=(0, 25))
        
        # 按钮
        button_frame = tk.Frame(login_container)
        button_frame.pack()
        
        tk.Button(
            button_frame,
            text="登录系统",
            command=self.login,
            bg="#4CAF50",
            fg="white",
            font=("Helvetica", 12, "bold"),
            width=18,
            height=2
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            button_frame,
            text="清除保存",
            command=self.clear_saved_credentials,
            bg="#f44336",
            fg="white",
            font=("Helvetica", 12),
            width=18,
            height=2
        ).pack(side=tk.LEFT, padx=10)
        
        # 登录状态
        self.login_status_label = tk.Label(
            login_container,
            text="未登录",
            fg="gray",
            font=("Helvetica", 14)
        )
        self.login_status_label.pack(pady=(40, 0))
    
    def create_symbol_selector_tab(self):
        """创建标的选择标签页"""
        selector_frame = ttk.Frame(self.notebook)
        self.notebook.add(selector_frame, text="🎯 标的选择")
        
        # 顶部控制栏
        control_frame = tk.LabelFrame(selector_frame, text="选择模式", padx=15, pady=15)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 模式选择
        mode_frame = tk.Frame(control_frame)
        mode_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Label(mode_frame, text="选择模式:", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=5)
        
        self.selection_mode_var = tk.StringVar(value="AUTO_SCORE")
        
        modes = [
            ("自动（综合评分）", "AUTO_SCORE"),
            ("自动（成交量）", "AUTO_VOLUME"),
            ("自动（波动率）", "AUTO_VOLATILITY"),
            ("手动选择", "MANUAL")
        ]
        
        for i, (label, value) in enumerate(modes):
            rb = tk.Radiobutton(
                mode_frame,
                text=label,
                variable=self.selection_mode_var,
                value=value,
                command=self.on_selection_mode_change,
                font=("Helvetica", 11)
            )
            rb.pack(side=tk.LEFT, padx=10)
        
        # 刷新按钮
        button_frame = tk.Frame(control_frame)
        button_frame.pack(side=tk.RIGHT, padx=10)
        
        tk.Button(
            button_frame,
            text="🔄 刷新合约列表",
            command=self.refresh_symbol_list,
            bg="#2196F3",
            fg="white",
            font=("Helvetica", 11),
            width=18
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="✅ 应用选择",
            command=self.apply_symbol_selection,
            bg="#4CAF50",
            fg="white",
            font=("Helvetica", 11, "bold"),
            width=18
        ).pack(side=tk.LEFT, padx=5)
        
        # 主内容区域
        content_frame = tk.Frame(selector_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧：所有合约列表
        left_frame = tk.LabelFrame(content_frame, text="所有合约（双击添加）", padx=10, pady=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # 搜索框
        search_frame = tk.Frame(left_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(search_frame, text="搜索:", font=("Helvetica", 11)).pack(side=tk.LEFT, padx=5)
        self.symbol_search_entry = tk.Entry(search_frame, font=("Helvetica", 11), width=30)
        self.symbol_search_entry.pack(side=tk.LEFT, padx=5)
        self.symbol_search_entry.bind("<KeyRelease>", self.on_symbol_search)
        
        # 所有合约列表
        all_columns = ("symbol", "score", "volume_24h", "change_24h")
        self.all_symbols_tree = ttk.Treeview(left_frame, columns=all_columns, show="headings", height=20)
        
        self.all_symbols_tree.heading("symbol", text="合约")
        self.all_symbols_tree.heading("score", text="评分")
        self.all_symbols_tree.heading("volume_24h", text="24h成交量")
        self.all_symbols_tree.heading("change_24h", text="24h涨跌幅")
        
        self.all_symbols_tree.column("symbol", width=120, anchor=tk.CENTER)
        self.all_symbols_tree.column("score", width=80, anchor=tk.CENTER)
        self.all_symbols_tree.column("volume_24h", width=120, anchor=tk.E)
        self.all_symbols_tree.column("change_24h", width=100, anchor=tk.CENTER)
        
        # 双击事件
        self.all_symbols_tree.bind("<Double-Button-1>", self.on_symbol_double_click)
        
        scrollbar1_y = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.all_symbols_tree.yview)
        self.all_symbols_tree.configure(yscrollcommand=scrollbar1_y.set)
        
        self.all_symbols_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar1_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 中间：控制按钮
        center_frame = tk.Frame(content_frame)
        center_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            center_frame,
            text="▶️",
            command=self.add_selected_symbols,
            font=("Helvetica", 20),
            width=3,
            height=2
        ).pack(pady=10)
        
        tk.Button(
            center_frame,
            text="◀️",
            command=self.remove_selected_symbols,
            font=("Helvetica", 20),
            width=3,
            height=2
        ).pack(pady=10)
        
        # 右侧：已选合约列表
        right_frame = tk.LabelFrame(content_frame, text="已选合约（双击移除）", padx=10, pady=10)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        selected_columns = ("symbol", "score", "reason")
        self.selected_symbols_tree = ttk.Treeview(right_frame, columns=selected_columns, show="headings", height=20)
        
        self.selected_symbols_tree.heading("symbol", text="合约")
        self.selected_symbols_tree.heading("score", text="评分")
        self.selected_symbols_tree.heading("reason", text="选择原因")
        
        self.selected_symbols_tree.column("symbol", width=120, anchor=tk.CENTER)
        self.selected_symbols_tree.column("score", width=80, anchor=tk.CENTER)
        self.selected_symbols_tree.column("reason", width=200, anchor=tk.W)
        
        # 双击事件
        self.selected_symbols_tree.bind("<Double-Button-1>", self.on_selected_symbol_double_click)
        
        scrollbar2_y = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.selected_symbols_tree.yview)
        self.selected_symbols_tree.configure(yscrollcommand=scrollbar2_y.set)
        
        self.selected_symbols_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar2_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 状态栏
        status_frame = tk.Frame(selector_frame, padx=10, pady=5)
        status_frame.pack(fill=tk.X)
        
        self.symbol_status_label = tk.Label(
            status_frame,
            text="未加载合约列表",
            font=("Helvetica", 10),
            fg="gray"
        )
        self.symbol_status_label.pack(side=tk.LEFT)
        
        # 合约列表缓存
        self.all_symbols_list = []
        self.selected_symbols_list = []
    
    def create_monitor_tab(self):
        """创建监控标签页"""
        monitor_frame = ttk.Frame(self.notebook)
        self.notebook.add(monitor_frame, text="📊 市场监控")
        
        # 顶部状态栏
        status_frame = tk.LabelFrame(monitor_frame, text="系统状态", padx=15, pady=15)
        status_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 左侧：系统状态
        left_frame = tk.Frame(status_frame)
        left_frame.pack(side=tk.LEFT, padx=20)
        
        self.system_state_label = tk.Label(
            left_frame,
            text="状态: 未启动",
            font=("Helvetica", 14, "bold"),
            fg="gray"
        )
        self.system_state_label.pack(anchor=tk.W, pady=5)
        
        self.market_state_label = tk.Label(
            left_frame,
            text="市场状态: 未知",
            font=("Helvetica", 12),
            fg="gray"
        )
        self.market_state_label.pack(anchor=tk.W, pady=5)
        
        self.loop_count_label = tk.Label(
            left_frame,
            text="循环次数: 0",
            font=("Helvetica", 12),
            fg="gray"
        )
        self.loop_count_label.pack(anchor=tk.W, pady=5)
        
        # 右侧：市场指标
        right_frame = tk.Frame(status_frame)
        right_frame.pack(side=tk.LEFT, padx=40)
        
        self.atr_label = tk.Label(right_frame, text="ATR: -", font=("Helvetica", 12))
        self.atr_label.pack(anchor=tk.W, pady=3)
        
        self.volume_label = tk.Label(right_frame, text="成交量比率: -", font=("Helvetica", 12))
        self.volume_label.pack(anchor=tk.W, pady=3)
        
        self.funding_label = tk.Label(right_frame, text="资金费率: -", font=("Helvetica", 12))
        self.funding_label.pack(anchor=tk.W, pady=3)
        
        self.score_label = tk.Label(right_frame, text="活跃评分: -/100", font=("Helvetica", 12))
        self.score_label.pack(anchor=tk.W, pady=3)
        
        # 控制按钮
        control_frame = tk.Frame(status_frame)
        control_frame.pack(side=tk.RIGHT, padx=20)
        
        self.start_btn = tk.Button(
            control_frame,
            text="▶️ 启动策略",
            command=self.start_strategy,
            bg="#4CAF50",
            fg="white",
            font=("Helvetica", 12, "bold"),
            width=15,
            height=2
        )
        self.start_btn.pack(pady=5)
        
        self.dry_run_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            control_frame,
            text="模拟模式",
            variable=self.dry_run_var,
            font=("Helvetica", 12)
        ).pack(pady=5)
        
        # 实时日志
        log_frame = tk.LabelFrame(monitor_frame, text="实时日志", padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=20,
            font=("Courier", 10),
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def create_signals_tab(self):
        """创建信号标签页"""
        signals_frame = ttk.Frame(self.notebook)
        self.notebook.add(signals_frame, text="💡 假突破信号")
        
        # 工具栏
        toolbar = tk.Frame(signals_frame, padx=10, pady=10)
        toolbar.pack(fill=tk.X)
        
        self.signal_count_label = tk.Label(
            toolbar,
            text="信号数量: 0",
            font=("Helvetica", 12, "bold")
        )
        self.signal_count_label.pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            toolbar,
            text="🔄 刷新信号",
            command=self.refresh_signals,
            bg="#2196F3",
            fg="white",
            font=("Helvetica", 11),
            width=15
        ).pack(side=tk.RIGHT, padx=5)
        
        # 信号表格
        table_frame = tk.Frame(signals_frame, padx=10, pady=10)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("time", "type", "entry", "sl", "tp", "confidence", "reason")
        self.signal_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        # 设置列标题
        self.signal_tree.heading("time", text="时间")
        self.signal_tree.heading("type", text="类型")
        self.signal_tree.heading("entry", text="入场价")
        self.signal_tree.heading("sl", text="止损")
        self.signal_tree.heading("tp", text="止盈")
        self.signal_tree.heading("confidence", text="置信度")
        self.signal_tree.heading("reason", text="原因")
        
        # 设置列宽
        self.signal_tree.column("time", width=180, anchor=tk.CENTER)
        self.signal_tree.column("type", width=100, anchor=tk.CENTER)
        self.signal_tree.column("entry", width=120, anchor=tk.CENTER)
        self.signal_tree.column("sl", width=120, anchor=tk.CENTER)
        self.signal_tree.column("tp", width=120, anchor=tk.CENTER)
        self.signal_tree.column("confidence", width=100, anchor=tk.CENTER)
        self.signal_tree.column("reason", width=300, anchor=tk.W)
        
        # 添加滚动条
        scrollbar_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.signal_tree.yview)
        scrollbar_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.signal_tree.xview)
        self.signal_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # 布局
        self.signal_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
    
    def create_risk_tab(self):
        """创建风险管理标签页"""
        risk_frame = ttk.Frame(self.notebook)
        self.notebook.add(risk_frame, text="🛡️ 风险管理")
        
        # 工具栏
        toolbar = tk.Frame(risk_frame, padx=10, pady=10)
        toolbar.pack(fill=tk.X)
        
        tk.Button(
            toolbar,
            text="🔄 刷新数据",
            command=self.refresh_risk_metrics,
            bg="#2196F3",
            fg="white",
            font=("Helvetica", 11),
            width=15
        ).pack(side=tk.RIGHT, padx=5)
        
        # 风险指标显示
        metrics_frame = tk.Frame(risk_frame, padx=20, pady=20)
        metrics_frame.pack(fill=tk.BOTH, expand=True)
        
        # 第一行：交易统计
        row1 = tk.Frame(metrics_frame)
        row1.pack(fill=tk.X, pady=10)
        
        self.create_metric_card(row1, "总交易次数", "total_trades", 0)
        self.create_metric_card(row1, "盈利次数", "winning_trades", 1)
        self.create_metric_card(row1, "亏损次数", "losing_trades", 2)
        self.create_metric_card(row1, "胜率", "win_rate", 3, percent=True)
        
        # 第二行：盈亏统计
        row2 = tk.Frame(metrics_frame)
        row2.pack(fill=tk.X, pady=10)
        
        self.create_metric_card(row2, "总盈亏 (USDT)", "total_pnl", 0)
        self.create_metric_card(row2, "当前余额 (USDT)", "current_balance", 1)
        self.create_metric_card(row2, "最大回撤 (%)", "max_drawdown", 2)
        self.create_metric_card(row2, "每日盈亏 (USDT)", "daily_pnl", 3)
        
        # 第三行：风险控制
        row3 = tk.Frame(metrics_frame)
        row3.pack(fill=tk.X, pady=10)
        
        self.create_metric_card(row3, "连续亏损", "consecutive_losses", 0)
        self.create_metric_card(row3, "平均盈利 (USDT)", "avg_win", 1)
        self.create_metric_card(row3, "平均亏损 (USDT)", "avg_loss", 2)
        self.create_metric_card(row3, "熔断状态", "circuit_breaker_state", 3)
        
        # 熔断控制
        control_frame = tk.LabelFrame(metrics_frame, text="熔断控制", padx=15, pady=15)
        control_frame.pack(fill=tk.X, pady=20)
        
        tk.Button(
            control_frame,
            text="重置熔断",
            command=self.reset_circuit_breaker,
            bg="#FF9800",
            fg="white",
            font=("Helvetica", 11),
            width=20
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Label(
            control_frame,
            text="熔断后系统将暂停交易30分钟，可手动重置",
            font=("Helvetica", 10),
            fg="gray"
        ).pack(side=tk.LEFT, padx=20)
    
    def create_metric_card(self, parent, title, key, column, percent=False):
        """创建指标卡片"""
        card = tk.Frame(parent, relief=tk.RIDGE, borderwidth=1, padx=15, pady=15)
        card.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10)
        
        tk.Label(card, text=title, font=("Helvetica", 10), fg="gray").pack()
        
        label = tk.Label(card, text="-", font=("Helvetica", 16, "bold"))
        label.pack()
        setattr(self, f"{key}_label", label)
    
    def create_trading_tab(self):
        """创建交易标签页"""
        trading_frame = ttk.Frame(self.notebook)
        self.notebook.add(trading_frame, text="💹 自动交易")
        
        # 顶部说明
        info_frame = tk.LabelFrame(trading_frame, text="交易控制", padx=15, pady=15)
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(
            info_frame,
            text="ETH 5m假突破策略自动交易 - 识别结构极值与失败突破",
            font=("Helvetica", 14, "bold"),
            fg="#2E7D32"
        ).pack(anchor=tk.W, pady=5)
        
        tk.Label(
            info_frame,
            text="策略通过多层过滤确保只在高质量机会时交易：市场状态 → 交易价值 → 结构位置 → 假突破识别 → 执行闸门 → 风险管理",
            font=("Helvetica", 11),
            fg="gray",
            wraplength=1200
        ).pack(anchor=tk.W, pady=10)
        
        # 统计信息
        stats_frame = tk.LabelFrame(trading_frame, text="策略统计", padx=15, pady=15)
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.stats_labels = {}
        stats_items = [
            ("循环次数", "total_loops"),
            ("发现信号", "signals_found"),
            ("执行交易", "trades_executed"),
            ("市场休眠跳过", "market_sleep"),
            ("不值得交易跳过", "not_worth"),
            ("执行闸门跳过", "execution_gate"),
            ("风险管理跳过", "risk_manager")
        ]
        
        for i, (label, key) in enumerate(stats_items):
            row = i // 4
            col = i % 4
            if row == 0:
                row_frame = tk.Frame(stats_frame)
                row_frame.pack(fill=tk.X, pady=5)
            
            frame = tk.Frame(row_frame, padx=10)
            frame.pack(side=tk.LEFT, expand=True, fill=tk.X)
            
            tk.Label(frame, text=label, font=("Helvetica", 10), fg="gray").pack(anchor=tk.W)
            lbl = tk.Label(frame, text="0", font=("Helvetica", 14, "bold"))
            lbl.pack(anchor=tk.W)
            self.stats_labels[key] = lbl
    
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
        
        if not self.key_manager.validate_credentials(api_key, api_secret):
            messagebox.showerror("错误", "凭证格式不正确")
            return
        
        self.login_status_label.config(text="正在连接...", fg="orange")
        
        def login_thread():
            self.trading_client = BinanceTradingClient(api_key, api_secret)
            result = self.trading_client.test_connection()
            
            if result['success']:
                self.is_logged_in = True
                
                if self.save_credentials_var.get():
                    self.key_manager.save_credentials(api_key, api_secret)
                
                # 创建策略系统
                self.strategy_system = MultiSymbolFakeoutSystem(self.trading_client)
                
                # 设置回调
                self.strategy_system.on_status_update = self.on_status_update
                self.strategy_system.on_order = self.on_order
                self.strategy_system.on_error = self.on_error
                
                self.root.after(0, self.on_login_success)
            else:
                self.root.after(0, lambda: self.on_login_failed(result['message']))
        
        threading.Thread(target=login_thread, daemon=True).start()
    
    def on_login_success(self):
        """登录成功"""
        self.login_status_label.config(text="✓ 登录成功", fg="green")
        messagebox.showinfo("成功", "API登录成功！")
        
        # 切换到监控标签页
        self.notebook.select(1)
    
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
    
    def start_strategy(self):
        """启动策略"""
        if not self.is_logged_in or not self.strategy_system:
            messagebox.showwarning("警告", "请先登录")
            return
        
        if self.strategy_system.state == SystemState.RUNNING:
            # 停止
            self.strategy_system.stop()
            self.start_btn.config(text="▶️ 启动策略", bg="#4CAF50")
            self.system_state_label.config(text="状态: 已停止", fg="gray")
            self.log_message("策略已停止")
        else:
            # 启动
            self.strategy_system.start()
            self.start_btn.config(text="⏸️ 停止策略", bg="#f44336")
            self.system_state_label.config(text="状态: 运行中", fg="green")
            self.log_message("策略已启动")
    
    def on_status_update(self, status_data):
        """状态更新回调"""
        # 更新日志
        self.log_message(status_data['message'])
        
        # 更新系统状态
        self.system_state_label.config(
            text=f"状态: {status_data['state']}",
            fg="green" if status_data['state'] == "RUNNING" else "gray"
        )
        
        # 更新循环次数
        stats = status_data['stats']
        self.loop_count_label.config(text=f"循环次数: {stats['total_loops']}")
        
        # 更新市场状态
        market_state = status_data.get('market_state', {})
        state = market_state.get('state', '未知')
        self.current_market_state = state
        self.market_state_label.config(text=f"市场状态: {state}")
        
        # 更新市场指标
        self.atr_label.config(text=f"ATR: {market_state.get('atr', 0):.2f}")
        self.volume_label.config(text=f"成交量比率: {market_state.get('volume_ratio', 0):.2f}")
        self.funding_label.config(text=f"资金费率: {market_state.get('funding_rate', 0):.6f}")
        self.score_label.config(text=f"活跃评分: {market_state.get('score', 0):.1f}/100")
        
        # 更新风险指标
        risk_metrics = status_data.get('risk_metrics', {})
        self.update_risk_metrics(risk_metrics)
        
        # 更新策略统计
        for key, label in self.stats_labels.items():
            if key in stats['skips']:
                label.config(text=str(stats['skips'][key]))
            else:
                label.config(text=str(stats.get(key, 0)))
    
    def on_order(self, order_info):
        """订单回调"""
        self.log_message(f"订单已执行: {order_info['signal'].signal_type.value}")
        # 这里可以更新订单显示
    
    def on_error(self, error_msg):
        """错误回调"""
        self.log_message(f"❌ 错误: {error_msg}")
    
    def log_message(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def refresh_signals(self):
        """刷新信号"""
        if not self.strategy_system:
            return
        
        # 清空表格
        for item in self.signal_tree.get_children():
            self.signal_tree.delete(item)
        
        # 获取最新信号
        signals = self.strategy_system.fakeout_strategy.analyze()
        
        self.signal_count_label.config(text=f"信号数量: {len(signals)}")
        
        for signal in signals:
            self.signal_tree.insert("", tk.END, values=(
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                signal.signal_type.value,
                f"{signal.entry_price:.2f}",
                f"{signal.stop_loss:.2f}",
                f"{signal.take_profit:.2f}",
                f"{signal.confidence:.2f}",
                signal.reason
            ))
    
    def refresh_risk_metrics(self):
        """刷新风险指标"""
        if not self.strategy_system:
            return
        
        metrics = self.strategy_system.risk_manager.get_metrics()
        self.update_risk_metrics(metrics)
    
    def update_risk_metrics(self, metrics):
        """更新风险指标显示"""
        metrics_map = {
            'total_trades': ('total_trades_label', lambda x: str(x)),
            'winning_trades': ('winning_trades_label', lambda x: str(x)),
            'losing_trades': ('losing_trades_label', lambda x: str(x)),
            'win_rate': ('win_rate_label', lambda x: f"{x*100:.1f}%"),
            'total_pnl': ('total_pnl_label', lambda x: f"{x:.2f}"),
            'current_balance': ('current_balance_label', lambda x: f"{x:.2f}"),
            'max_drawdown': ('max_drawdown_label', lambda x: f"{x:.2f}"),
            'daily_pnl': ('daily_pnl_label', lambda x: f"{x:.2f}"),
            'consecutive_losses': ('consecutive_losses_label', lambda x: str(x)),
            'avg_win': ('avg_win_label', lambda x: f"{x:.2f}"),
            'avg_loss': ('avg_loss_label', lambda x: f"{x:.2f}"),
            'circuit_breaker_state': ('circuit_breaker_state_label', lambda x: x)
        }
        
        for key, (label_attr, formatter) in metrics_map.items():
            if hasattr(self, label_attr):
                label = getattr(self, label_attr)
                value = metrics.get(key, 0)
                label.config(text=formatter(value))
                
                # 颜色设置
                if key == 'total_pnl' or key == 'daily_pnl':
                    label.config(fg="red" if value < 0 else "green")
                elif key == 'max_drawdown':
                    label.config(fg="red" if value > 5 else "black")
                elif key == 'circuit_breaker_state':
                    label.config(fg="red" if x == "TRIGGERED" else "black")
    
    def reset_circuit_breaker(self):
        """重置熔断"""
        if self.strategy_system:
            self.strategy_system.risk_manager.reset_circuit_breaker()
            self.log_message("熔断已重置")
            messagebox.showinfo("成功", "熔断已重置")
    
    def refresh_symbol_list(self):
        """刷新合约列表"""
        if not self.strategy_system:
            messagebox.showwarning("警告", "请先登录")
            return
        
        def refresh_thread():
            try:
                selector = self.strategy_system.get_symbol_selector()
                selector.update_symbol_list(force_update=True)
                self.all_symbols_list = selector.get_all_symbols()
                
                self.root.after(0, self._update_symbol_list_display)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("错误", f"刷新失败: {str(e)}"))
        
        threading.Thread(target=refresh_thread, daemon=True).start()
        self.symbol_status_label.config(text="正在加载合约列表...", fg="orange")
    
    def _update_symbol_list_display(self):
        """更新合约列表显示"""
        # 清空列表
        for item in self.all_symbols_tree.get_children():
            self.all_symbols_tree.delete(item)
        
        # 添加合约
        for symbol_info in self.all_symbols_list:
            self.all_symbols_tree.insert("", tk.END, values=(
                symbol_info.symbol,
                f"{symbol_info.score:.1f}",
                f"{symbol_info.volume_24h:,.0f}",
                f"{symbol_info.change_24h:+.2f}%"
            ))
        
        # 更新已选列表
        self._update_selected_symbols_display()
        
        self.symbol_status_label.config(
            text=f"共 {len(self.all_symbols_list)} 个合约，已选 {len(self.selected_symbols_list)} 个",
            fg="black"
        )
    
    def _update_selected_symbols_display(self):
        """更新已选合约列表显示"""
        # 清空列表
        for item in self.selected_symbols_tree.get_children():
            self.selected_symbols_tree.delete(item)
        
        # 添加已选合约
        for symbol_info in self.selected_symbols_list:
            reason = symbol_info.reasons[0] if symbol_info.reasons else ""
            self.selected_symbols_tree.insert("", tk.END, values=(
                symbol_info.symbol,
                f"{symbol_info.score:.1f}",
                reason
            ))
        
        self.symbol_status_label.config(
            text=f"共 {len(self.all_symbols_list)} 个合约，已选 {len(self.selected_symbols_list)} 个",
            fg="black"
        )
    
    def on_symbol_search(self, event):
        """搜索合约"""
        search_text = self.symbol_search_entry.get().upper()
        
        # 清空列表
        for item in self.all_symbols_tree.get_children():
            self.all_symbols_tree.delete(item)
        
        # 筛选并显示
        for symbol_info in self.all_symbols_list:
            if search_text in symbol_info.symbol:
                self.all_symbols_tree.insert("", tk.END, values=(
                    symbol_info.symbol,
                    f"{symbol_info.score:.1f}",
                    f"{symbol_info.volume_24h:,.0f}",
                    f"{symbol_info.change_24h:+.2f}%"
                ))
    
    def on_selection_mode_change(self):
        """选择模式改变"""
        mode = self.selection_mode_var.get()
        
        if mode == "MANUAL":
            # 手动模式，允许用户选择
            pass
        else:
            # 自动模式，自动选择
            if not self.strategy_system:
                return
            
            try:
                selection_mode = SelectionMode(mode)
                self.strategy_system.set_selection_mode(selection_mode)
                self.selected_symbols_list = []
                
                selector = self.strategy_system.get_symbol_selector()
                for symbol in selector.get_selected_symbols():
                    symbol_info = selector.get_symbol_info(symbol)
                    if symbol_info:
                        self.selected_symbols_list.append(symbol_info)
                
                self._update_selected_symbols_display()
            except Exception as e:
                messagebox.showerror("错误", f"模式切换失败: {str(e)}")
    
    def on_symbol_double_click(self, event):
        """双击添加合约"""
        selection = self.all_symbols_tree.selection()
        if not selection:
            return
        
        for item in selection:
            symbol = self.all_symbols_tree.item(item)['values'][0]
            
            # 检查是否已选
            if any(s.symbol == symbol for s in self.selected_symbols_list):
                continue
            
            # 添加到已选列表
            for symbol_info in self.all_symbols_list:
                if symbol_info.symbol == symbol:
                    symbol_info.reasons = ["手动选择"]
                    self.selected_symbols_list.append(symbol_info)
                    break
        
        self._update_selected_symbols_display()
    
    def on_selected_symbol_double_click(self, event):
        """双击移除合约"""
        selection = self.selected_symbols_tree.selection()
        if not selection:
            return
        
        for item in selection:
            symbol = self.selected_symbols_tree.item(item)['values'][0]
            
            # 从已选列表中移除
            self.selected_symbols_list = [
                s for s in self.selected_symbols_list 
                if s.symbol != symbol
            ]
        
        self._update_selected_symbols_display()
    
    def add_selected_symbols(self):
        """添加选中的合约"""
        selection = self.all_symbols_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择合约")
            return
        
        for item in selection:
            symbol = self.all_symbols_tree.item(item)['values'][0]
            
            # 检查是否已选
            if any(s.symbol == symbol for s in self.selected_symbols_list):
                continue
            
            # 添加到已选列表
            for symbol_info in self.all_symbols_list:
                if symbol_info.symbol == symbol:
                    symbol_info.reasons = ["手动选择"]
                    self.selected_symbols_list.append(symbol_info)
                    break
        
        self._update_selected_symbols_display()
    
    def remove_selected_symbols(self):
        """移除选中的合约"""
        selection = self.selected_symbols_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择合约")
            return
        
        for item in selection:
            symbol = self.selected_symbols_tree.item(item)['values'][0]
            
            # 从已选列表中移除
            self.selected_symbols_list = [
                s for s in self.selected_symbols_list 
                if s.symbol != symbol
            ]
        
        self._update_selected_symbols_display()
    
    def apply_symbol_selection(self):
        """应用合约选择"""
        if not self.strategy_system:
            messagebox.showwarning("警告", "请先登录")
            return
        
        if not self.selected_symbols_list:
            messagebox.showwarning("警告", "请至少选择一个合约")
            return
        
        symbols = [s.symbol for s in self.selected_symbols_list]
        self.strategy_system.update_selected_symbols(symbols)
        
        messagebox.showinfo("成功", f"已应用选择，共 {len(symbols)} 个合约")
        self.log_message(f"合约选择已更新: {', '.join(symbols)}")


def main():
    """主函数"""
    root = tk.Tk()
    app = ETHFakeoutGUI(root)
    
    def on_closing():
        if app.strategy_system:
            app.strategy_system.stop()
        if messagebox.askokcancel("退出", "确定要退出应用吗？"):
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
