# 币安自动交易系统 - 完整文档

一个功能完善的币安期货自动交易系统，支持策略筛选合约、手动选择和自动化交易。

## 📋 目录

- [系统功能](#系统功能)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [详细使用说明](#详细使用说明)
- [安全说明](#安全说明)
- [API接口说明](#api接口说明)
- [策略开发指南](#策略开发指南)
- [常见问题](#常见问题)

## ✨ 系统功能

### 第一步功能（已完成）

1. **实时连接状态监控**
   - 自动检测与币安API的连接状态
   - 实时显示服务器时间
   - 可视化状态指示器

2. **合约信息获取**
   - 获取币安平台所有合约信息
   - 显示交易对、基础资产、计价资产等
   - 支持搜索过滤

### 第二步功能（已完成）

1. **API密钥管理**
   - 安全的API密钥存储（加密）
   - 支持保存凭证到本地
   - 凭证格式验证

2. **策略筛选合约**
   - 策略框架支持扩展
   - 预定义策略（成交量策略、价格策略）
   - 支持自定义策略

3. **手动选择合约**
   - 从策略筛选结果中选择
   - 支持添加/移除合约
   - 已选合约列表管理

4. **自动化交易**
   - 自动交易引擎
   - 支持模拟模式（不实际下单）
   - 实时日志记录
   - 错误处理和重试机制

5. **账户管理**
   - 账户余额查询
   - 持仓信息查看
   - 订单历史记录

## 🏗️ 系统架构

```
币安自动交易系统
├── GUI层
│   └── binance_trading_gui.py (主界面)
├── 交易引擎层
│   ├── auto_trading_engine.py (自动交易引擎)
│   └── trading_strategy.py (策略框架)
├── API层
│   ├── binance_api_client.py (公共API)
│   └── binance_trading_client.py (交易API)
└── 工具层
    └── api_key_manager.py (密钥管理)
```

## 🚀 快速开始

### 前置要求

1. **Python 3.6+**
   ```bash
   python3 --version
   ```

2. **依赖库**
   ```bash
   pip3 install requests cryptography
   ```

3. **币安账户**
   - 注册币安账户
   - 开启期货交易权限
   - 创建API密钥

### 创建币安API密钥

1. 登录币安账户
2. 进入「API管理」页面
3. 创建新API密钥
4. **重要**：启用期货交易权限
5. 保存API Key和Secret（只显示一次）

### 运行系统

#### 方法一：双击运行（推荐）

```bash
双击 '启动交易系统.command' 文件
```

#### 方法二：命令行运行

```bash
python3 binance_trading_gui.py
```

### 首次使用流程

1. **登录系统**
   - 在"登录"标签页输入API Key和Secret
   - 勾选"保存凭证"以便下次自动登录
   - 点击"登录"按钮

2. **执行策略**
   - 切换到"策略筛选"标签页
   - 点击"执行策略"按钮
   - 查看策略筛选结果

3. **选择合约**
   - 在"策略筛选"结果中选择要交易的合约
   - 将合约添加到交易列表（后续功能）

4. **启动自动交易**
   - 切换到"自动交易"标签页
   - 确保勾选"模拟模式"
   - 点击"启动引擎"开始自动交易

5. **查看账户**
   - 切换到"账户信息"标签页
   - 查看账户余额和持仓

## 📖 详细使用说明

### 1. 登录界面

**字段说明：**
- **API Key**: 从币安获取的API密钥
- **API Secret**: 对应的密钥
- **保存凭证**: 加密保存到本地，下次无需重新输入

**注意事项：**
- API密钥只显示一次，请妥善保存
- 建议创建测试账户的API密钥进行测试
- 不要分享API密钥给他人

### 2. 策略筛选界面

**功能说明：**
- **执行策略**: 运行所有策略并生成筛选结果
- **合约**: 策略筛选出的交易对
- **策略名称**: 生成该结果的策略
- **信号类型**: BUY/SELL/HOLD等信号
- **置信度**: 信号的可信程度（0-1）
- **原因**: 生成信号的原因

**预定义策略：**

1. **成交量策略**
   - 筛选BTCUSDT、ETHUSDT等主流合约
   - 参数：最小成交量

2. **价格策略**
   - 筛选所有USDT合约
   - 参数：价格变动阈值

### 3. 自动交易界面

**引擎控制：**
- **启动/停止引擎**: 控制自动交易引擎
- **模拟模式**: 勾选后不实际下单，仅记录日志
- **已选合约**: 显示当前选中的交易合约

**交易日志：**
- 实时显示交易信号
- 订单执行状态
- 错误信息

**使用步骤：**

1. 在"策略筛选"界面选择合约
2. 切换到"自动交易"界面
3. 勾选"模拟模式"（重要！）
4. 点击"启动引擎"
5. 观察日志输出

### 4. 账户信息界面

**功能：**
- 查看账户总余额
- 查看可用余额
- 查看持仓详情
- 查看未实现盈亏

**操作：**
- 点击"刷新账户"按钮获取最新数据

## 🔒 安全说明

### API密钥安全

1. **本地加密存储**
   - 使用Fernet加密算法
   - 密钥文件单独存储
   - 即使文件泄露也无法直接使用

2. **不要泄露**
   - API密钥只用于本系统
   - 不要上传到公共仓库
   - 不要分享给他人

3. **权限控制**
   - 建议创建只读或有限权限的API密钥
   - 禁用提现权限
   - 限制IP白名单（可选）

### 交易安全

1. **模拟模式**
   - 首次使用必须启用模拟模式
   - 充分测试策略后再切换实盘
   - 模拟模式下不会实际下单

2. **风险控制**
   - 设置合理的杠杆倍数
   - 控制单笔交易金额
   - 设置止损止盈

3. **数据备份**
   - 定期备份交易日志
   - 记录策略参数
   - 保存API配置

### 系统安全

1. **网络连接**
   - 确保网络连接稳定
   - 使用VPN（如所在地区限制访问）
   - 避免公共WiFi

2. **环境安全**
   - 保持系统更新
   - 安装杀毒软件
   - 不要在公用电脑使用

## 🔌 API接口说明

### 公共API（无需认证）

| 端点 | 方法 | 功能 |
|-----|------|------|
| `/fapi/v1/ping` | GET | 测试连接 |
| `/fapi/v1/time` | GET | 获取服务器时间 |
| `/fapi/v1/exchangeInfo` | GET | 获取交易规则和交易对 |
| `/fapi/v1/ticker/24hr` | GET | 获取24小时价格变动 |

### 交易API（需要认证）

| 端点 | 方法 | 功能 |
|-----|------|------|
| `/fapi/v2/account` | GET | 获取账户信息 |
| `/fapi/v2/balance` | GET | 获取账户余额 |
| `/fapi/v2/positionRisk` | GET | 获取持仓信息 |
| `/fapi/v1/order` | POST | 下单 |
| `/fapi/v1/openOrders` | GET | 获取当前挂单 |
| `/fapi/v1/order` | DELETE | 取消订单 |
| `/fapi/v1/userTrades` | GET | 获取成交记录 |

**API基础URL**: `https://fapi.binance.com`

**官方文档**: https://binance-docs.github.io/apidocs/futures/cn/

## 📊 策略开发指南

### 创建自定义策略

```python
from trading_strategy import BaseStrategy, TradingSignal, SignalType
from typing import List, Dict, Optional

class MyStrategy(BaseStrategy):
    """自定义策略"""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="我的策略",
            params=kwargs
        )
    
    def filter_symbols(self, all_symbols: List[Dict]) -> List[str]:
        """筛选合约"""
        filtered = []
        for symbol_info in all_symbols:
            symbol = symbol_info.get('symbol', '')
            # 添加你的筛选逻辑
            if 'USDT' in symbol and 'BTC' in symbol:
                filtered.append(symbol)
        return filtered
    
    def generate_signals(self, symbols: List[str], market_data: Dict) -> List[TradingSignal]:
        """生成交易信号"""
        signals = []
        for symbol in symbols:
            # 添加你的信号生成逻辑
            # 示例：生成买入信号
            signal = TradingSignal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                price=50000.0,
                quantity=0.001,
                confidence=0.8,
                reason="我的分析逻辑"
            )
            signals.append(signal)
        return signals
```

### 使用自定义策略

```python
from trading_strategy import StrategyManager

# 创建策略管理器
manager = StrategyManager()

# 添加自定义策略
my_strategy = MyStrategy(param1="value1")
manager.add_strategy(my_strategy)

# 执行策略
results = manager.execute_all(all_symbols, market_data)
```

## ❓ 常见问题

### Q1: 登录失败怎么办？

**A**: 请检查：
1. API Key和Secret是否正确
2. API密钥是否启用了期货交易权限
3. IP白名单是否正确设置（如果启用）
4. 网络连接是否正常

### Q2: 为什么看不到合约数据？

**A**: 请确保：
1. 已成功登录币安API
2. 点击了"执行策略"按钮
3. 网络连接正常
4. 查看日志是否有错误信息

### Q3: 模拟模式下资金会扣减吗？

**A**: 不会。模拟模式下：
- 不会实际下单
- 不会扣减资金
- 仅记录日志供查看

### Q4: 如何切换到实盘交易？

**A**: 步骤如下：
1. 充分测试策略，确保稳定运行
2. 取消勾选"模拟模式"
3. 确认账户有足够余额
4. 点击"启动引擎"
5. 密切监控交易日志

**⚠️ 警告**：实盘交易有风险，请谨慎操作！

### Q5: 系支持哪些订单类型？

**A**: 当前支持的订单类型：
- MARKET（市价单）
- LIMIT（限价单，待添加）
- STOP（止损单，待添加）
- 其他订单类型可在后续添加

### Q6: 如何添加新的策略？

**A**: 有两种方式：

1. **修改代码**：在`trading_strategy.py`中添加新策略类
2. **使用自定义策略函数**：
```python
strategy = PredefinedStrategies.create_custom_strategy(
    name="新策略",
    filter_func=my_filter_func,
    signal_func=my_signal_func
)
manager.add_strategy(strategy)
```

### Q7: 系统安全吗？

**A**: 系统有多层安全保护：
1. API密钥本地加密存储
2. 不发送密钥到第三方服务器
3. 支持模拟模式测试
4. 开源代码，可自行审计

但仍需注意：
- 妥善保管API密钥
- 不要在公用电脑使用
- 定期更改密码
- 启用2FA双重认证

### Q8: 出现错误怎么办？

**A**: 请按以下步骤排查：
1. 查看交易日志中的错误信息
2. 检查网络连接
3. 确认API密钥有效
4. 尝试重新登录
5. 如问题持续，查看币安API状态页

## 📝 后续计划

- [ ] 添加更多预定义策略
- [ ] 支持更多订单类型
- [ ] 添加K线图表显示
- [ ] 添加回测功能
- [ ] 添加风险控制参数
- [ ] 支持多账户管理
- [ ] 添加策略性能统计
- [ ] 添加WebSocket实时行情
- [ ] 添加价格预警功能
- [ ] 导出交易报告

## 📄 免责声明

本系统仅供学习和研究使用，不构成投资建议。使用本系统进行实盘交易存在资金损失风险。使用币安API需要遵守币安的服务条款和API使用规范。

**作者不对因使用本系统造成的任何损失负责。**

使用前请确保：
1. 充分理解交易风险
2. 先在模拟模式下充分测试
3. 不要投入无法承受损失的资金
4. 遵守当地法律法规

## 📞 技术支持

如有问题或建议，欢迎反馈。

---

**祝交易顺利！** 🚀📈
