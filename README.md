# 币安期货自动交易系统

基于FVG（Fair Value Gap）缺口识别和流动性捕取的自动交易系统，支持多合约标的筛选与自动交易。

## 功能特性

### 核心功能
- ✅ FVG流动性策略
- ✅ 多标的策略识别与自动交易
- ✅ 市场状态过滤（休眠/活跃/激进）
- ✅ 交易价值过滤器
- ✅ 风险管理和熔断机制
- ✅ 模拟模式和实盘模式
- ✅ 自动止盈止损
- ✅ 持仓管理和监控

### FVG流动性策略特点
- **时间框架**：15分钟、1小时、4小时多周期分析
- **核心逻辑**：
  - 识别看涨/看跌FVG价格缺口
  - 流动性区识别与流动性捕取检测
  - 多周期共振分析（15m + 1h + 4h）
  - 智能置信度评分系统
- **多层过滤**：市场状态 → 交易价值 → FVG缺口验证 → 多周期共振 → 执行闸门
- **风险控制**：最大回撤5%、连续亏损3次、每日亏损30U熔断
- **置信度评分**：FVG质量30% + 新鲜度25% + 位置25% + 盈亏比20%

### GUI功能
- 现代化的白色主题界面
- 7个标签页：登录、合约选择、监控、信号、风险、交易、参数配置、手动控制
- 实时参数更新（无需重启）
- 市场休眠限制开关
- 模拟/实盘模式切换
- 实时日志和信号显示

## 系统架构

### FVG流动性策略系统
```
fvg_liquidity_strategy_system.py  # FVG策略主系统
├── parameter_config.py            # 参数配置管理
├── fvg_strategy.py               # FVG缺口识别策略
├── liquidity_analyzer.py         # 流动性分析器
├── multi_timeframe_analyzer.py   # 多周期分析器
├── fvg_signal.py                 # FVG信号数据结构
├── market_state_engine.py       # 市场状态引擎
├── worth_trading_filter.py      # 交易价值过滤器
├── risk_manager.py              # 风险管理器
├── execution_gate.py            # 执行闸门
├── position_manager.py          # 持仓管理器
├── symbol_selector.py           # 合约选择器
├── data_fetcher.py              # 数据获取器
├── binance_api_client.py        # 币安API客户端
├── binance_trading_client.py    # 币安交易客户端
├── api_key_manager.py           # API密钥管理
├── exceptions.py                # 自定义异常类
├── logger_config.py             # 日志配置模块
├── utils.py                    # 工具函数模块
└── eth_fakeout_gui.py           # GUI界面（统一入口）
```

## 安装和运行

### 环境要求
- Python 3.6+
- macOS / Linux / Windows
- 币安期货账户（需要API密钥）

### 依赖安装

#### 方法一：使用requirements.txt（推荐）
```bash
pip install -r requirements.txt
```

#### 方法二：手动安装
```bash
pip install requests python-docx cryptography
```

### 运行方式

#### 方法一：双击运行（macOS）
1. 确保已安装Python 3
2. 双击 `启动FVG策略应用.command` 文件

#### 方法二：命令行运行
```bash
python3 fvg_liquidity_gui.py
```

## 使用说明

### 1. 登录
- 输入币安API Key和API Secret
- 勾选"保存凭证"可加密存储密钥
- 点击"登录"按钮连接

### 2. 合约选择
- 切换到"合约选择"标签页
- 选择选择模式：
  - 自动（综合评分）：自动选择评分最高的N个合约
  - 自动（成交量）：自动选择成交量最大的N个合约
  - 自动（波动率）：自动选择波动率最大的N个合约
  - 手动：手动选择要监控的合约
- 双击合约可添加/移除

### 3. 参数配置
- 切换到"参数配置"标签页
- 调整各类参数：
  - FVG策略参数
  - 风险管理参数
  - 交易价值过滤参数
  - 执行闸门参数
  - 市场状态引擎参数（包括市场休眠限制开关）
  - 系统运行参数
- 点击"保存并应用"实时更新参数

### 4. 启动策略
- 切换到"监控"标签页
- 勾选"模拟模式"（推荐首次使用）
- 点击"▶️ 启动策略"按钮
- 系统每10秒执行一次完整决策周期

### 5. 手动控制
- 切换到"手动控制"标签页
- 可暂停/恢复/停止策略
- 可手动开仓/平仓
- 可切换模拟/实盘模式

## 参数说明

### FVG策略参数
- `timeframes`: 分析周期列表（默认：['15m', '1h', '4h']）
- `primary_timeframe`: 主周期（默认：'1h'）
- `min_confidence`: 最小置信度阈值（默认：0.6）
- `gap_min_size_ratio`: 最小缺口大小比例（默认：0.001）
- `gap_max_size_ratio`: 最大缺口大小比例（默认：0.01）
- `fvg_valid_bars`: FVG有效K线数（默认：50）
- `min_rr_ratio`: 最小盈亏比（默认：2.0）

### 流动性分析参数
- `swing_period`: 摆动点检测周期（默认：3）
- `liquidity_zone_lookback`: 流动性区回溯K线数（默认：100）
- `min_touches`: 最小触碰次数（默认：3）
- `liquidity_range_percent`: 流动性区范围百分比（默认：0.2）

### 多周期分析参数
- `confluence_threshold`: 共振阈值（默认：0.6）
- `min_confluence_timeframes`: 最小共振周期数（默认：2）

### 风险管理参数
- `max_drawdown_percent`: 最大回撤百分比（默认5%）
- `max_consecutive_losses`: 最大连续亏损次数（默认3）
- `daily_loss_limit`: 每日亏损限制USDT（默认30）
- `risk_per_trade`: 单笔风险比例（默认0.02）
- `max_position_size`: 最大仓位比例（默认0.3）
- `position_size_leverage`: 杠杆倍数（默认10）

### 市场状态引擎参数
- `enable_market_sleep_filter`: 启用市场休眠过滤（默认True）
- `volatility_window`: 波动率计算窗口（默认14）
- `trend_ma_fast`: 快速均线周期（默认7）
- `trend_ma_slow`: 慢速均线周期（默认25）
- `volume_ma_period`: 成交量均线周期（默认20）

### 系统运行参数
- `loop_interval_seconds`: 主循环间隔秒数（默认10）
- `data_refresh_interval`: 数据刷新间隔秒数（默认30）
- `max_symbols_to_monitor`: 最大监控标的数（默认5）

## 风险提示

⚠️ **重要警告**
- 本系统仅供学习研究使用
- 实盘交易存在资金损失风险
- 建议先在模拟模式充分测试
- 请合理设置风险参数
- 作者不承担任何交易损失责任

## 测试

### FVG流动性策略测试
```bash
# 运行FVG策略综合测试
python3 test_fvg_liquidity_system.py

# 运行FVG策略单元测试
python3 test_fvg_liquidity_strategy.py
```

测试包括：
- 参数配置模块
- FVG信号数据结构
- FVG策略功能
- 流动性分析器功能
- 多周期分析器功能
- API连接测试
- 系统集成测试

### 假突破策略测试
```bash
# 运行假突破策略综合测试
python3 test_system_comprehensive.py
```

测试包括：
- 参数配置模块
- 市场状态引擎
- 风险管理器
- 交易价值过滤器
- 假突破策略
- 系统集成

## 更新日志

### 最新更新（FVG流动性策略）
- ✅ 完成FVG流动性策略系统完整开发
- ✅ 实现FVG缺口识别和多周期分析
- ✅ 实现流动性分析和流动性捕取检测
- ✅ 实现多周期共振分析（15m + 1h + 4h）
- ✅ 创建综合测试脚本（test_fvg_liquidity_system.py）
- ✅ 创建异常处理模块（exceptions.py）
- ✅ 创建日志配置模块（logger_config.py）
- ✅ 创建工具函数模块（utils.py）
- ✅ 创建FVG流动性策略使用手册
- ✅ 创建依赖管理文件（requirements.txt）
- ✅ 更新README文档，添加FVG策略说明

### 假突破策略更新
- 添加市场休眠限制开关功能
- 优化参数配置，增加交易机会
- 完善参数动态更新机制
- 修复模拟模式判断逻辑
- 添加系统功能综合测试

### 之前的更新
- 完成实盘交易功能全面检查
- 修复信号界面不显示合约名称
- 添加离线功能测试脚本
- 优化风险管理参数
- 完善线程安全和平仓重试机制

## 技术栈

- **语言**: Python 3.6+
- **GUI框架**: Tkinter
- **HTTP请求**: requests
- **加密**: cryptography
- **文档处理**: python-docx

## 文件结构

```
.
├── eth_fakeout_gui.py                   # GUI主程序（支持FVG和假突破策略）
├── fvg_liquidity_strategy_system.py     # FVG流动性策略系统
├── eth_fakeout_strategy_system.py       # 假突破策略系统
│
├── FVG策略模块
│   ├── fvg_strategy.py                  # FVG缺口识别策略
│   ├── liquidity_analyzer.py            # 流动性分析器
│   ├── multi_timeframe_analyzer.py      # 多周期分析器
│   └── fvg_signal.py                    # FVG信号数据结构
│
├── 假突破策略模块
│   └── fakeout_strategy.py              # 假突破策略
│
├── 核心功能模块
│   ├── parameter_config.py               # 参数配置管理
│   ├── parameter_config_optimized.py    # 优化参数配置
│   ├── market_state_engine.py           # 市场状态引擎
│   ├── worth_trading_filter.py          # 交易价值过滤器
│   ├── risk_manager.py                  # 风险管理器
│   ├── execution_gate.py                # 执行闸门
│   ├── position_manager.py              # 持仓管理器
│   ├── symbol_selector.py               # 合约选择器
│   └── data_fetcher.py                  # 数据获取器
│
├── API模块
│   ├── binance_api_client.py            # 币安API客户端
│   ├── binance_trading_client.py        # 币安交易客户端
│   └── api_key_manager.py               # API密钥管理
│
├── 工具模块
│   ├── exceptions.py                    # 自定义异常类
│   ├── logger_config.py                 # 日志配置模块
│   └── utils.py                         # 工具函数模块
│
├── 测试脚本
│   ├── test_fvg_liquidity_system.py     # FVG策略综合测试
│   ├── test_fvg_liquidity_strategy.py   # FVG策略单元测试
│   ├── test_system_comprehensive.py     # 假突破策略综合测试
│   └── test_*.py                         # 其他测试脚本
│
├── 文档
│   ├── FVG流动性策略系统使用手册.md     # FVG策略详细使用手册
│   ├── FVG流动性策略架构设计.md         # FVG策略架构说明
│   ├── 快速开始指南.md                  # 快速入门指南
│   ├── 交易价值过滤参数调整指南.md       # 参数调整指南
│   └── requirements.txt                  # Python依赖包列表
│
└── README.md                            # 本文件
```

## 许可证

MIT License

## 联系方式

如有问题或建议，欢迎提交Issue或Pull Request。
