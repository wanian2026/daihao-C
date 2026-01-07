#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FVG流动性策略系统 - 图形界面
提供完整的交易策略监控和参数配置功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
import threading
import time

from binance_api_client import BinanceAPIClient
from binance_trading_client import BinanceTradingClient
from api_key_manager import APIKeyManager
from fvg_liquidity_strategy_system import FVGLiquidityStrategySystem, SystemState
from symbol_selector import SymbolSelector, SelectionMode
from parameter_config import get_config, update_config
from position_manager import Position


class FVGLiquidityGUI:
    """FVG流动性策略GUI应用"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("FVG流动性策略系统")
        
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
        self.symbol_selector = None
        
        # 状态变量
        self.is_logged_in = False
        self.simulation_mode = tk.BooleanVar(value=True)
        self.selected_symbols = []
        self.signals = []
        self.positions = []
        self.auto_update_running = False
        
        # 创建界面
        self.create_widgets()
        
        # 加载保存的API密钥
        self.load_saved_credentials()
    
    def create_widgets(self):
        """创建界面组件"""
        
        # 创建主框架
        main_container = tk.Frame(self.root, bg="#FFFFFF")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # 创建Notebook（标签页）
        style = ttk.Style()
        style.configure("TNotebook", background="#FFFFFF")
        style.configure("TNotebook.Tab", background="#F5F5F5", foreground="#000000")
        style.map("TNotebook.Tab", background=[("selected", "#FFFFFF")])
        
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建各个标签页
        self.create_login_tab()
        self.create_symbol_tab()
        self.create_monitor_tab()
        self.create_signals_tab()
        self.create_risk_tab()
        self.create_parameters_tab()
        self.create_manual_tab()
    
    def create_login_tab(self):
        """创建登录标签页"""
        login_frame = tk.Frame(self.notebook, bg="#FFFFFF")
        self.notebook.add(login_frame, text="🔐 登录")
        
        # 登录表单容器
        login_container = tk.Frame(login_frame, bg="#FFFFFF", padx=100, pady=80)
        login_container.place(relx=0.5, rely=0.4, anchor=tk.CENTER)
        
        # 标题
        tk.Label(
            login_container,
            text="FVG流动性策略系统",
            font=("Helvetica", 24, "bold"),
            bg="#FFFFFF",
            fg="#000000"
        ).pack(pady=(0, 10))
        
        tk.Label(
            login_container,
            text="登录币安账户",
            font=("Helvetica", 14),
            bg="#FFFFFF",
            fg="#666666"
        ).pack(pady=(0, 50))
        
        # API Key
        tk.Label(
            login_container,
            text="API Key:",
            font=("Helvetica", 12),
            bg="#FFFFFF",
            fg="#000000"
        ).pack(anchor=tk.W)
        
        self.api_key_entry = tk.Entry(
            login_container,
            font=("Helvetica", 11),
            width=50
        )
        self.api_key_entry.pack(pady=(0, 20))
        
        # API Secret
        tk.Label(
            login_container,
            text="API Secret:",
            font=("Helvetica", 12),
            bg="#FFFFFF",
            fg="#000000"
        ).pack(anchor=tk.W)
        
        self.api_secret_entry = tk.Entry(
            login_container,
            font=("Helvetica", 11),
            width=50,
            show="*"
        )
        self.api_secret_entry.pack(pady=(0, 20))
        
        # 保存凭证
        self.save_credentials_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            login_container,
            text="保存凭证（加密存储）",
            variable=self.save_credentials_var,
            font=("Helvetica", 10),
            bg="#FFFFFF",
            fg="#000000"
        ).pack(anchor=tk.W, pady=(0, 30))
        
        # 登录按钮
        login_btn = tk.Button(
            login_container,
            text="登录",
            command=self.login,
            bg="#4CAF50",
            fg="white",
            font=("Helvetica", 12, "bold"),
            width=20,
            height=2
        )
        login_btn.pack(pady=10)
        
        # 状态标签
        self.login_status_label = tk.Label(
            login_container,
            text="",
            font=("Helvetica", 10),
            bg="#FFFFFF",
            fg="#666666"
        )
        self.login_status_label.pack(pady=(10, 0))
    
    def create_symbol_tab(self):
        """创建合约选择标签页"""
        symbol_frame = tk.Frame(self.notebook, bg="#FFFFFF")
        self.notebook.add(symbol_frame, text="📊 合约选择")
        
        # 顶部控制栏
        control_frame = tk.Frame(symbol_frame, bg="#F5F5F5", height=60)
        control_frame.pack(fill=tk.X, padx=0, pady=0)
        control_frame.pack_propagate(False)
        
        tk.Label(
            control_frame,
            text="选择模式:",
            font=("Helvetica", 11),
            bg="#F5F5F5",
            fg="#000000"
        ).pack(side=tk.LEFT, padx=20, pady=15)
        
        # 选择模式下拉框
        self.selection_mode_var = tk.StringVar(value="自动（综合评分）")
        mode_combo = ttk.Combobox(
            control_frame,
            textvariable=self.selection_mode_var,
            values=[
                "自动（综合评分）",
                "自动（成交量）",
                "自动（波动率）",
                "手动"
            ],
            state="readonly",
            width=20,
            font=("Helvetica", 10)
        )
        mode_combo.pack(side=tk.LEFT, padx=10, pady=15)
        mode_combo.bind("<<ComboboxSelected>>", self.on_selection_mode_changed)
        
        # 刷新按钮
        refresh_btn = tk.Button(
            control_frame,
            text="🔄 刷新",
            command=self.refresh_symbols,
            bg="#2196F3",
            fg="white",
            font=("Helvetica", 10, "bold"),
            width=12
        )
        refresh_btn.pack(side=tk.LEFT, padx=20, pady=15)
        
        # 已选数量
        self.selected_count_label = tk.Label(
            control_frame,
            text="已选: 0",
            font=("Helvetica", 11),
            bg="#F5F5F5",
            fg="#000000"
        )
        self.selected_count_label.pack(side=tk.RIGHT, padx=20, pady=15)
        
        # 合约列表
        list_frame = tk.Frame(symbol_frame, bg="#FFFFFF")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建Treeview
        columns = ("symbol", "volume", "volatility", "score", "selected")
        self.symbol_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=20)
        
        self.symbol_tree.heading("symbol", text="交易对")
        self.symbol_tree.heading("volume", text="成交量")
        self.symbol_tree.heading("volatility", text="波动率")
        self.symbol_tree.heading("score", text="评分")
        self.symbol_tree.heading("selected", text="已选")
        
        self.symbol_tree.column("symbol", width=150, anchor=tk.CENTER)
        self.symbol_tree.column("volume", width=150, anchor=tk.CENTER)
        self.symbol_tree.column("volatility", width=120, anchor=tk.CENTER)
        self.symbol_tree.column("score", width=100, anchor=tk.CENTER)
        self.symbol_tree.column("selected", width=80, anchor=tk.CENTER)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.symbol_tree.yview)
        self.symbol_tree.configure(yscrollcommand=scrollbar.set)
        
        self.symbol_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # 双击事件
        self.symbol_tree.bind("<Double-1>", self.on_symbol_double_click)
    
    def create_monitor_tab(self):
        """创建监控标签页"""
        monitor_frame = tk.Frame(self.notebook, bg="#FFFFFF")
        self.notebook.add(monitor_frame, text="📈 监控")
        
        # 顶部控制栏
        control_frame = tk.Frame(monitor_frame, bg="#F5F5F5", height=60)
        control_frame.pack(fill=tk.X, padx=0, pady=0)
        control_frame.pack_propagate(False)
        
        # 模拟模式
        tk.Checkbutton(
            control_frame,
            text="模拟模式",
            variable=self.simulation_mode,
            font=("Helvetica", 11),
            bg="#F5F5F5",
            fg="#000000"
        ).pack(side=tk.LEFT, padx=20, pady=15)
        
        # 启动/停止按钮
        self.start_btn = tk.Button(
            control_frame,
            text="▶️ 启动策略",
            command=self.toggle_strategy,
            bg="#4CAF50",
            fg="white",
            font=("Helvetica", 11, "bold"),
            width=15,
            height=2
        )
        self.start_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        # 状态标签
        self.system_status_label = tk.Label(
            control_frame,
            text="状态: 未启动",
            font=("Helvetica", 11, "bold"),
            bg="#F5F5F5",
            fg="#666666"
        )
        self.system_status_label.pack(side=tk.RIGHT, padx=20, pady=15)
        
        # 统计信息
        stats_frame = tk.Frame(monitor_frame, bg="#FFFFFF")
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.stats_labels = {}
        stats_info = [
            ("循环次数", "total_loops"),
            ("发现共振", "confluences"),
            ("执行交易", "trades"),
            ("监控标的", "symbols"),
            ("分析周期", "timeframes")
        ]
        
        for i, (label_text, key) in enumerate(stats_info):
            frame = tk.Frame(stats_frame, bg="#FFFFFF")
            frame.pack(side=tk.LEFT, padx=20)
            
            tk.Label(
                frame,
                text=label_text,
                font=("Helvetica", 10),
                bg="#FFFFFF",
                fg="#666666"
            ).pack()
            
            self.stats_labels[key] = tk.Label(
                frame,
                text="0",
                font=("Helvetica", 14, "bold"),
                bg="#FFFFFF",
                fg="#000000"
            )
            self.stats_labels[key].pack()
        
        # 系统日志
        log_frame = tk.LabelFrame(monitor_frame, text="系统日志", padx=10, pady=10, bg="#FFFFFF")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=("Courier", 10),
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def create_signals_tab(self):
        """创建信号标签页"""
        signals_frame = tk.Frame(self.notebook, bg="#FFFFFF")
        self.notebook.add(signals_frame, text="🎯 信号")
        
        # 信号表格
        table_frame = tk.Frame(signals_frame, bg="#FFFFFF")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("time", "symbol", "type", "source", "entry", "sl", "tp", "confidence", "rr")
        self.signals_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=25)
        
        self.signals_tree.heading("time", text="时间")
        self.signals_tree.heading("symbol", text="合约")
        self.signals_tree.heading("type", text="类型")
        self.signals_tree.heading("source", text="来源")
        self.signals_tree.heading("entry", text="入场")
        self.signals_tree.heading("sl", text="止损")
        self.signals_tree.heading("tp", text="止盈")
        self.signals_tree.heading("confidence", text="置信度")
        self.signals_tree.heading("rr", text="盈亏比")
        
        for col in columns:
            self.signals_tree.column(col, anchor=tk.CENTER)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.signals_tree.yview)
        self.signals_tree.configure(yscrollcommand=scrollbar.set)
        
        self.signals_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
    
    def create_risk_tab(self):
        """创建风险管理标签页"""
        risk_frame = tk.Frame(self.notebook, bg="#FFFFFF")
        self.notebook.add(risk_frame, text="⚠️ 风险管理")
        
        # 持仓表格
        positions_frame = tk.LabelFrame(risk_frame, text="当前持仓", padx=10, pady=10, bg="#FFFFFF")
        positions_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("symbol", "side", "size", "entry", "current", "pnl", "pnl_percent", "sl", "tp")
        self.positions_tree = ttk.Treeview(positions_frame, columns=columns, show="headings", height=15)
        
        self.positions_tree.heading("symbol", text="合约")
        self.positions_tree.heading("side", text="方向")
        self.positions_tree.heading("size", text="数量")
        self.positions_tree.heading("entry", text="入场价")
        self.positions_tree.heading("current", text="当前价")
        self.positions_tree.heading("pnl", text="盈亏")
        self.positions_tree.heading("pnl_percent", text="盈亏%")
        self.positions_tree.heading("sl", text="止损")
        self.positions_tree.heading("tp", text="止盈")
        
        for col in columns:
            self.positions_tree.column(col, anchor=tk.CENTER)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(positions_frame, orient=tk.VERTICAL, command=self.positions_tree.yview)
        self.positions_tree.configure(yscrollcommand=scrollbar.set)
        
        self.positions_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        positions_frame.grid_rowconfigure(0, weight=1)
        positions_frame.grid_columnconfigure(0, weight=1)
    
    def create_parameters_tab(self):
        """创建参数配置标签页"""
        params_frame = tk.Frame(self.notebook, bg="#FFFFFF")
        self.notebook.add(params_frame, text="⚙️ 参数配置")
        
        # 创建滚动框架
        canvas = tk.Canvas(params_frame, bg="#FFFFFF")
        scrollbar = ttk.Scrollbar(params_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#FFFFFF")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # FVG策略参数
        fvg_frame = tk.LabelFrame(scrollable_frame, text="FVG策略参数", padx=15, pady=15, bg="#FFFFFF")
        fvg_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.fvg_params = {}
        fvg_params = [
            ("timeframes", "分析周期", "['15m', '1h', '4h']"),
            ("primary_timeframe", "主周期", "1h"),
            ("min_confidence", "最小置信度", "0.6"),
            ("gap_min_size_ratio", "最小缺口比例", "0.001"),
            ("gap_max_size_ratio", "最大缺口比例", "0.01"),
            ("fvg_valid_bars", "FVG有效K线数", "50"),
            ("min_rr_ratio", "最小盈亏比", "2.0")
        ]
        
        for i, (key, label, default) in enumerate(fvg_params):
            row_frame = tk.Frame(fvg_frame, bg="#FFFFFF")
            row_frame.pack(fill=tk.X, pady=5)
            
            tk.Label(row_frame, text=label, width=20, anchor=tk.W, font=("Helvetica", 10), bg="#FFFFFF").pack(side=tk.LEFT)
            
            entry = tk.Entry(row_frame, font=("Helvetica", 10))
            entry.insert(0, default)
            entry.pack(side=tk.LEFT, padx=10)
            self.fvg_params[key] = entry
        
        # 流动性分析参数
        liquidity_frame = tk.LabelFrame(scrollable_frame, text="流动性分析参数", padx=15, pady=15, bg="#FFFFFF")
        liquidity_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.liquidity_params = {}
        liquidity_params = [
            ("swing_period", "摆动点周期", "3"),
            ("liquidity_zone_lookback", "流动性区回溯", "100"),
            ("min_touches", "最小触碰次数", "3"),
            ("liquidity_range_percent", "流动性区范围", "0.2")
        ]
        
        for i, (key, label, default) in enumerate(liquidity_params):
            row_frame = tk.Frame(liquidity_frame, bg="#FFFFFF")
            row_frame.pack(fill=tk.X, pady=5)
            
            tk.Label(row_frame, text=label, width=20, anchor=tk.W, font=("Helvetica", 10), bg="#FFFFFF").pack(side=tk.LEFT)
            
            entry = tk.Entry(row_frame, font=("Helvetica", 10))
            entry.insert(0, default)
            entry.pack(side=tk.LEFT, padx=10)
            self.liquidity_params[key] = entry
        
        # 风险管理参数
        risk_frame = tk.LabelFrame(scrollable_frame, text="风险管理参数", padx=15, pady=15, bg="#FFFFFF")
        risk_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.risk_params = {}
        risk_params = [
            ("max_drawdown_percent", "最大回撤%", "5"),
            ("max_consecutive_losses", "最大连续亏损", "3"),
            ("daily_loss_limit", "每日亏损限制(U)", "30"),
            ("risk_per_trade", "单笔风险比例", "0.02"),
            ("max_position_size", "最大仓位比例", "0.3"),
            ("position_size_leverage", "杠杆倍数", "10")
        ]
        
        for i, (key, label, default) in enumerate(risk_params):
            row_frame = tk.Frame(risk_frame, bg="#FFFFFF")
            row_frame.pack(fill=tk.X, pady=5)
            
            tk.Label(row_frame, text=label, width=20, anchor=tk.W, font=("Helvetica", 10), bg="#FFFFFF").pack(side=tk.LEFT)
            
            entry = tk.Entry(row_frame, font=("Helvetica", 10))
            entry.insert(0, default)
            entry.pack(side=tk.LEFT, padx=10)
            self.risk_params[key] = entry
        
        # 保存按钮
        save_btn = tk.Button(
            scrollable_frame,
            text="保存并应用",
            command=self.save_parameters,
            bg="#4CAF50",
            fg="white",
            font=("Helvetica", 12, "bold"),
            width=20,
            height=2
        )
        save_btn.pack(pady=20)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_manual_tab(self):
        """创建手动控制标签页"""
        manual_frame = tk.Frame(self.notebook, bg="#FFFFFF")
        self.notebook.add(manual_frame, text="🎮 手动控制")
        
        # 控制按钮
        control_frame = tk.Frame(manual_frame, bg="#FFFFFF", padx=20, pady=20)
        control_frame.pack(fill=tk.X)
        
        tk.Label(control_frame, text="策略控制", font=("Helvetica", 14, "bold"), bg="#FFFFFF", fg="#000000").pack(pady=(0, 15))
        
        buttons_frame = tk.Frame(control_frame, bg="#FFFFFF")
        buttons_frame.pack()
        
        tk.Button(
            buttons_frame,
            text="⏸️ 暂停",
            command=self.pause_strategy,
            bg="#FF9800",
            fg="white",
            font=("Helvetica", 11, "bold"),
            width=12
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            buttons_frame,
            text="▶️ 恢复",
            command=self.resume_strategy,
            bg="#4CAF50",
            fg="white",
            font=("Helvetica", 11, "bold"),
            width=12
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            buttons_frame,
            text="⏹️ 停止",
            command=self.stop_strategy,
            bg="#F44336",
            fg="white",
            font=("Helvetica", 11, "bold"),
            width=12
        ).pack(side=tk.LEFT, padx=10)
        
        # 手动交易
        trade_frame = tk.LabelFrame(manual_frame, text="手动交易", padx=20, pady=20, bg="#FFFFFF")
        trade_frame.pack(fill=tk.X, padx=20, pady=10)
        
        input_frame = tk.Frame(trade_frame, bg="#FFFFFF")
        input_frame.pack()
        
        tk.Label(input_frame, text="合约:", font=("Helvetica", 10), bg="#FFFFFF", fg="#000000").grid(row=0, column=0, padx=5)
        self.manual_symbol_entry = tk.Entry(input_frame, font=("Helvetica", 10), width=15)
        self.manual_symbol_entry.grid(row=0, column=1, padx=5)
        self.manual_symbol_entry.insert(0, "BTCUSDT")
        
        tk.Label(input_frame, text="方向:", font=("Helvetica", 10), bg="#FFFFFF", fg="#000000").grid(row=0, column=2, padx=5)
        self.manual_side_var = tk.StringVar(value="BUY")
        ttk.Combobox(input_frame, textvariable=self.manual_side_var, values=["BUY", "SELL"], state="readonly", width=10).grid(row=0, column=3, padx=5)
        
        tk.Label(input_frame, text="数量:", font=("Helvetica", 10), bg="#FFFFFF", fg="#000000").grid(row=0, column=4, padx=5)
        self.manual_size_entry = tk.Entry(input_frame, font=("Helvetica", 10), width=10)
        self.manual_size_entry.grid(row=0, column=5, padx=5)
        self.manual_size_entry.insert(0, "0.001")
        
        tk.Button(
            input_frame,
            text="开仓",
            command=self.manual_open_position,
            bg="#2196F3",
            fg="white",
            font=("Helvetica", 10, "bold"),
            width=10
        ).grid(row=0, column=6, padx=10)
        
        tk.Button(
            input_frame,
            text="平仓",
            command=self.manual_close_position,
            bg="#F44336",
            fg="white",
            font=("Helvetica", 10, "bold"),
            width=10
        ).grid(row=0, column=7, padx=10)
    
    def load_saved_credentials(self):
        """加载保存的凭证"""
        try:
            saved = self.key_manager.load_credentials()
            if saved:
                # load_credentials 返回元组 (api_key, api_secret, passphrase)
                api_key, api_secret, _ = saved
                self.api_key_entry.delete(0, tk.END)
                self.api_key_entry.insert(0, api_key)
                self.api_secret_entry.delete(0, tk.END)
                self.api_secret_entry.insert(0, api_secret)
                self.save_credentials_var.set(True)
        except Exception as e:
            self.log(f"加载凭证失败: {e}")
    
    def login(self):
        """登录"""
        api_key = self.api_key_entry.get().strip()
        api_secret = self.api_secret_entry.get().strip()
        
        if not api_key or not api_secret:
            messagebox.showerror("错误", "请输入API Key和API Secret")
            return
        
        try:
            self.login_status_label.config(text="登录中...", fg="#FF9800")
            self.root.update()
            
            # 创建交易客户端
            self.trading_client = BinanceTradingClient(api_key, api_secret)
            
            # 测试连接
            account_info = self.trading_client.get_account_info()
            if account_info.get('error'):
                raise Exception(account_info.get('msg', '连接失败'))
            
            # 保存凭证
            if self.save_credentials_var.get():
                self.key_manager.save_credentials(api_key, api_secret)
            
            # 初始化系统
            self.strategy_system = FVGLiquidityStrategySystem(self.trading_client)
            self.symbol_selector = SymbolSelector(self.api_client)
            
            self.is_logged_in = True
            self.login_status_label.config(text="登录成功！", fg="#4CAF50")
            
            # 切换到合约选择标签页
            self.notebook.select(1)
            
            # 加载合约列表
            self.refresh_symbols()
            
            messagebox.showinfo("成功", "登录成功！")
            
        except Exception as e:
            self.login_status_label.config(text=f"登录失败: {str(e)}", fg="#F44336")
            messagebox.showerror("登录失败", str(e))
    
    def refresh_symbols(self):
        """刷新合约列表"""
        try:
            self.symbol_selector.update_symbol_list(force_update=True)
            symbols = self.symbol_selector.get_all_symbols()
            
            # 清空表格
            for item in self.symbol_tree.get_children():
                self.symbol_tree.delete(item)
            
            # 添加合约
            for symbol_info in symbols:
                # 使用属性访问，而不是下标访问（SymbolInfo是dataclass）
                self.symbol_tree.insert("", tk.END, values=(
                    symbol_info.symbol,
                    f"{symbol_info.volume_24h:.0f}",
                    f"{abs(symbol_info.change_24h):.2f}%",
                    f"{symbol_info.score:.2f}",
                    "✓" if symbol_info.symbol in self.selected_symbols else "✗"
                ))
            
            self.log(f"已加载 {len(symbols)} 个合约")
            
        except Exception as e:
            self.log(f"刷新合约列表失败: {e}")
            messagebox.showerror("错误", f"刷新失败: {e}")
    
    def on_selection_mode_changed(self, event):
        """选择模式改变"""
        mode_map = {
            "自动（综合评分）": SelectionMode.SCORE,
            "自动（成交量）": SelectionMode.VOLUME,
            "自动（波动率）": SelectionMode.VOLATILITY,
            "手动": SelectionMode.MANUAL
        }
        
        mode = mode_map.get(self.selection_mode_var.get())
        if mode and self.symbol_selector:
            self.symbol_selector.set_selection_mode(mode)
            self.selected_symbols = self.symbol_selector.get_selected_symbols()
            self.update_selected_count()
            self.refresh_symbols()
    
    def on_symbol_double_click(self, event):
        """双击合约"""
        selection = self.symbol_tree.selection()
        if not selection:
            return
        
        item = self.symbol_tree.item(selection[0])
        symbol = item['values'][0]
        
        if symbol in self.selected_symbols:
            self.selected_symbols.remove(symbol)
        else:
            self.selected_symbols.append(symbol)
        
        self.update_selected_count()
        self.refresh_symbols()
    
    def update_selected_count(self):
        """更新已选数量"""
        self.selected_count_label.config(text=f"已选: {len(self.selected_symbols)}")
        
        if self.strategy_system:
            self.strategy_system.update_selected_symbols(self.selected_symbols)
    
    def toggle_strategy(self):
        """切换策略启动/停止"""
        if self.strategy_system is None:
            messagebox.showerror("错误", "请先登录")
            return
        
        if self.strategy_system.state == SystemState.RUNNING:
            self.stop_strategy()
        else:
            self.start_strategy()
    
    def start_strategy(self):
        """启动策略"""
        try:
            if not self.selected_symbols:
                messagebox.showwarning("警告", "请先选择要监控的合约")
                return
            
            # 应用参数
            self.apply_parameters()
            
            # 启动系统
            self.strategy_system.start()
            
            # 更新UI
            self.start_btn.config(text="⏹️ 停止策略", bg="#F44336")
            self.system_status_label.config(text="状态: 运行中", fg="#4CAF50")
            
            # 启动UI更新
            self.auto_update_running = True
            threading.Thread(target=self.auto_update_loop, daemon=True).start()
            
            self.log("策略已启动")
            
        except Exception as e:
            messagebox.showerror("错误", f"启动失败: {e}")
            self.log(f"启动失败: {e}")
    
    def stop_strategy(self):
        """停止策略"""
        if self.strategy_system:
            self.strategy_system.stop()
        
        self.auto_update_running = False
        self.start_btn.config(text="▶️ 启动策略", bg="#4CAF50")
        self.system_status_label.config(text="状态: 已停止", fg="#666666")
        
        self.log("策略已停止")
    
    def pause_strategy(self):
        """暂停策略"""
        if self.strategy_system:
            self.strategy_system.pause()
        self.system_status_label.config(text="状态: 已暂停", fg="#FF9800")
        self.log("策略已暂停")
    
    def resume_strategy(self):
        """恢复策略"""
        if self.strategy_system:
            self.strategy_system.resume()
        self.system_status_label.config(text="状态: 运行中", fg="#4CAF50")
        self.log("策略已恢复")
    
    def auto_update_loop(self):
        """自动更新循环"""
        while self.auto_update_running:
            try:
                # 使用after确保在主线程更新UI
                self.root.after(0, self.update_stats)
                self.root.after(0, self.update_positions)
                self.root.after(0, self.update_signals)
                
                time.sleep(2)
            except Exception as e:
                self.log(f"更新失败: {e}")
    
    def update_stats(self):
        """更新统计信息"""
        if self.strategy_system:
            stats = self.strategy_system.stats
            self.stats_labels['total_loops'].config(text=str(stats['total_loops']))
            self.stats_labels['confluences'].config(text=str(stats['confluences_found']))
            self.stats_labels['trades'].config(text=str(stats['trades_executed']))
            self.stats_labels['symbols'].config(text=str(len(self.selected_symbols)))
            self.stats_labels['timeframes'].config(text=str(stats['timeframes_analyzed']))
    
    def update_positions(self):
        """更新持仓"""
        if self.trading_client:
            try:
                positions = self.trading_client.get_positions()
                
                # 清空表格
                for item in self.positions_tree.get_children():
                    self.positions_tree.delete(item)
                
                # 添加持仓
                for pos in positions:
                    pnl_percent = (pos['unRealizedProfit'] / pos['notional']) * 100 if pos['notional'] != 0 else 0
                    pnl_color = "#4CAF50" if pos['unRealizedProfit'] >= 0 else "#F44336"
                    
                    self.positions_tree.insert("", tk.END, values=(
                        pos['symbol'],
                        pos['positionSide'],
                        f"{pos['positionAmt']:.4f}",
                        f"{pos['entryPrice']:.2f}",
                        f"{pos['markPrice']:.2f}",
                        f"{pos['unRealizedProfit']:.2f}",
                        f"{pnl_percent:.2f}%",
                        f"{pos['stopLossPrice']:.2f}" if pos['stopLossPrice'] else "-",
                        f"{pos['takeProfitPrice']:.2f}" if pos['takeProfitPrice'] else "-"
                    ))
                
            except Exception as e:
                pass
    
    def update_signals(self):
        """更新信号显示"""
        if self.strategy_system:
            try:
                # 获取所有共振信号
                confluences = self.strategy_system.symbol_confluences
                
                # 清空表格
                for item in self.signals_tree.get_children():
                    self.signals_tree.delete(item)
                
                # 添加信号
                for symbol, confluence in confluences.items():
                    if confluence and confluence.primary_signal:
                        signal = confluence.primary_signal
                        time_str = datetime.now().strftime("%H:%M:%S")
                        
                        # 计算盈亏比
                        if signal.entry_price > 0:
                            if signal.stop_loss > 0:
                                sl_distance = abs(signal.entry_price - signal.stop_loss)
                            else:
                                sl_distance = 0
                            
                            if signal.take_profit > 0:
                                tp_distance = abs(signal.take_profit - signal.entry_price)
                            else:
                                tp_distance = 0
                            
                            rr_ratio = tp_distance / sl_distance if sl_distance > 0 else 0
                        else:
                            rr_ratio = 0
                        
                        self.signals_tree.insert("", tk.END, values=(
                            time_str,
                            symbol,
                            confluence.confluence_type,
                            ", ".join(confluence.contributing_timeframes),
                            f"{signal.entry_price:.6f}",
                            f"{signal.stop_loss:.6f}",
                            f"{signal.take_profit:.6f}",
                            f"{confluence.confidence:.1%}",
                            f"{rr_ratio:.2f}"
                        ))
                
            except Exception as e:
                self.log(f"更新信号失败: {e}")
    
    def save_parameters(self):
        """保存参数"""
        try:
            # 收集FVG参数
            fvg_config = {}
            for key, entry in self.fvg_params.items():
                value = entry.get()
                fvg_config[key] = value
            
            # 收集流动性参数
            liquidity_config = {}
            for key, entry in self.liquidity_params.items():
                value = entry.get()
                liquidity_config[key] = value
            
            # 收集风险参数
            risk_config = {}
            for key, entry in self.risk_params.items():
                value = entry.get()
                risk_config[key] = value
            
            # 更新配置
            update_config({
                'fvg_strategy': fvg_config,
                'liquidity_analyzer': liquidity_config,
                'risk_manager': risk_config
            })
            
            self.apply_parameters()
            
            messagebox.showinfo("成功", "参数已保存并应用")
            self.log("参数已更新")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")
    
    def apply_parameters(self):
        """应用参数"""
        if self.strategy_system:
            self.strategy_system.update_config()
            self.log("参数已应用到策略系统")
    
    def manual_open_position(self):
        """手动开仓"""
        try:
            symbol = self.manual_symbol_entry.get().strip()
            side = self.manual_side_var.get()
            size = float(self.manual_size_entry.get())
            
            if not symbol or size <= 0:
                messagebox.showerror("错误", "请输入有效的合约和数量")
                return
            
            if not self.trading_client:
                messagebox.showerror("错误", "请先登录")
                return
            
            # 模拟模式
            if self.simulation_mode.get():
                self.log(f"[模拟] {side} {size} {symbol}")
                return
            
            # 实盘模式
            result = self.trading_client.place_order(symbol, side, size)
            if result.get('error'):
                raise Exception(result.get('msg'))
            
            self.log(f"已开仓: {side} {size} {symbol}")
            messagebox.showinfo("成功", f"已开仓: {side} {size} {symbol}")
            
        except Exception as e:
            messagebox.showerror("错误", f"开仓失败: {e}")
    
    def manual_close_position(self):
        """手动平仓"""
        try:
            symbol = self.manual_symbol_entry.get().strip()
            
            if not symbol:
                messagebox.showerror("错误", "请输入合约")
                return
            
            if not self.trading_client:
                messagebox.showerror("错误", "请先登录")
                return
            
            # 获取当前持仓
            positions = self.trading_client.get_positions()
            target_pos = None
            for pos in positions:
                if pos['symbol'] == symbol and abs(float(pos['positionAmt'])) > 0:
                    target_pos = pos
                    break
            
            if not target_pos:
                messagebox.showwarning("警告", f"未找到 {symbol} 的持仓")
                return
            
            side = "SELL" if float(target_pos['positionAmt']) > 0 else "BUY"
            size = abs(float(target_pos['positionAmt']))
            
            # 模拟模式
            if self.simulation_mode.get():
                self.log(f"[模拟] 平仓 {size} {symbol}")
                return
            
            # 实盘模式
            result = self.trading_client.place_order(symbol, side, size, reduce_only=True)
            if result.get('error'):
                raise Exception(result.get('msg'))
            
            self.log(f"已平仓: {size} {symbol}")
            messagebox.showinfo("成功", f"已平仓: {size} {symbol}")
            
        except Exception as e:
            messagebox.showerror("错误", f"平仓失败: {e}")
    
    def log(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        print(message)


if __name__ == "__main__":
    import logging
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建应用
    root = tk.Tk()
    app = FVGLiquidityGUI(root)
    root.mainloop()
