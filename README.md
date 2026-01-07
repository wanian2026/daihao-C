# 币安期货自动交易系统

基于5分钟K线的假突破策略，支持多合约标的筛选与自动交易。

## 功能特性

### 核心功能
- ✅ 多标的假突破策略识别
- ✅ 市场状态过滤（休眠/活跃/激进）
- ✅ 交易价值过滤器
- ✅ 风险管理和熔断机制
- ✅ 模拟模式和实盘模式
- ✅ 自动止盈止损
- ✅ 持仓管理和监控

### 策略特点
- **时间框架**：5分钟K线
- **核心逻辑**：识别结构极值与失败突破
- **多层过滤**：市场状态 → 交易价值 → 结构位置 → 假突破识别 → 执行闸门
- **风险控制**：最大回撤5%、连续亏损3次、每日亏损30U熔断

### GUI功能
- 现代化的白色主题界面
- 7个标签页：登录、合约选择、监控、信号、风险、交易、参数配置、手动控制
- 实时参数更新（无需重启）
- 市场休眠限制开关
- 模拟/实盘模式切换
- 实时日志和信号显示

## 系统架构

```
eth_fakeout_strategy_system.py  # 主系统
├── parameter_config.py         # 参数配置管理
├── market_state_engine.py     # 市场状态引擎
├── worth_trading_filter.py    # 交易价值过滤器
├── fakeout_strategy.py        # 假突破策略
├── risk_manager.py            # 风险管理器
├── execution_gate.py          # 执行闸门
├── position_manager.py        # 持仓管理器
├── symbol_selector.py         # 合约选择器
├── data_fetcher.py            # 数据获取器
├── binance_api_client.py      # 币安API客户端
├── binance_trading_client.py  # 币安交易客户端
├── api_key_manager.py         # API密钥管理
└── eth_fakeout_gui.py         # GUI界面
```

## 安装和运行

### 环境要求
- Python 3.6+
- macOS / Linux / Windows
- 币安期货账户（需要API密钥）

### 依赖安装
```bash
pip install requests python-docx cryptography
```

### 运行方式

#### 方法一：双击运行（macOS）
1. 确保已安装Python 3
2. 双击 `启动应用.command` 文件

#### 方法二：命令行运行
```bash
python3 eth_fakeout_gui.py
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
  - 假突破策略参数
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

### 假突破策略参数
- `swing_period`: 摆动点检测周期（默认3）
- `breakout_confirmation`: 突破确认K线数（默认2）
- `fakeout_confirmation`: 假突破确认K线数（默认1）
- `min_body_ratio`: K线实体占比（默认0.3）
- `max_structure_levels`: 最大结构位数量（默认20）
- `structure_valid_bars`: 结构位有效K线数（默认50）

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

运行综合测试：
```bash
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

### 最新更新
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
├── eth_fakeout_gui.py              # GUI主程序
├── eth_fakeout_strategy_system.py  # 策略系统
├── parameter_config.py             # 参数配置
├── market_state_engine.py          # 市场状态引擎
├── worth_trading_filter.py         # 交易价值过滤器
├── fakeout_strategy.py             # 假突破策略
├── risk_manager.py                 # 风险管理器
├── position_manager.py             # 持仓管理器
├── symbol_selector.py              # 合约选择器
├── data_fetcher.py                 # 数据获取器
├── binance_api_client.py           # 币安API客户端
├── binance_trading_client.py       # 币安交易客户端
├── api_key_manager.py              # API密钥管理
├── 启动应用.command                # macOS启动脚本
├── test_*.py                       # 测试脚本
└── README.md                       # 本文件
```

## 许可证

MIT License

## 联系方式

如有问题或建议，欢迎提交Issue或Pull Request。
