# FVG和流动性策略架构设计

## 策略概述

本策略基于 **Fair Value Gap（FVG，公允价值缺口）** 和 **流动性分析** 两个核心技术，通过多周期分析识别高概率交易机会。

---

## 核心概念

### 1. Fair Value Gap (FVG)

**定义**：价格快速移动时留下的价格缺口，通常由三根K线组成：
- **看涨FVG**：
  - 第2根K线的高点 > 第1根K线的低点
  - 中间存在未填充的价格缺口
  - 价格通常会回补这个缺口

- **看跌FVG**：
  - 第2根K线的低点 < 第1根K线的高点
  - 中间存在未填充的价格缺口
  - 价格通常会回补这个缺口

**特点**：
- ✅ 代表市场失衡
- ✅ 高概率被回补
- ✅ 提供明确的入场点（缺口边缘）
- ✅ 可计算风险回报比

---

### 2. 流动性分析

**定义**：识别市场中的买方流动性和卖方流动性聚集区

**买方流动性**：
- **止损买单聚集区**：价格跌破关键支撑位后触发
- 通常位于：前低点、支撑位、FVG缺口下方

**卖方流动性**：
- **止损卖单聚集区**：价格突破关键阻力位后触发
- 通常位于：前高点、阻力位、FVG缺口上方

**流动性捕取（Liquidity Sweep）**：
- 价格短暂突破流动性区后迅速反转
- 形成流动性陷阱
- 提供高概率的反转交易机会

---

## 策略逻辑

### 信号生成流程

```
1. 多周期分析
   ↓
2. 识别FVG缺口
   ↓
3. 分析流动性聚集区
   ↓
4. 检测流动性捕取
   ↓
5. 确认关键位（支撑/阻力）
   ↓
6. 生成交易信号
```

---

### 多周期分析

**支持的周期**：
- 1m（1分钟）- 超短线
- 5m（5分钟）- 短线（默认）
- 15m（15分钟）- 中短线
- 1h（1小时）- 中线
- 4h（4小时）- 长线

**多周期确认逻辑**：
- 高周期（如4h）：识别主要趋势和大级别FVG
- 低周期（如5m）：寻找入场点和流动性捕取
- 当多个周期的FVG和流动性信号共振时，信号质量最高

---

### 信号类型

#### 1. FVG回补信号（做多）

**条件**：
1. 检测到看涨FVG缺口
2. 价格回跌至缺口边缘
3. 缺口下方存在买方流动性
4. 低周期确认反转

**入场**：FVG缺口底部
**止损**：FVG缺口下方
**止盈**：FVG缺口顶部或流动性目标位

---

#### 2. FVG回补信号（做空）

**条件**：
1. 检测到看跌FVG缺口
2. 价格反弹至缺口边缘
3. 缺口上方存在卖方流动性
4. 低周期确认反转

**入场**：FVG缺口顶部
**止损**：FVG缺口上方
**止盈**：FVG缺口底部或流动性目标位

---

#### 3. 流动性捕取信号（做多）

**条件**：
1. 价格短暂突破前低点（捕取买方流动性）
2. 快速反弹回前低点上方
3. 低周期形成看涨反转形态
4. 存在看涨FVG确认

**入场**：流动性捕取后的反弹点
**止损**：新低点下方
**止盈**：上方流动性区或FVG缺口

---

#### 4. 流动性捕取信号（做空）

**条件**：
1. 价格短暂突破前高点（捕取卖方流动性）
2. 快速回落回前高点下方
3. 低周期形成看跌反转形态
4. 存在看跌FVG确认

**入场**：流动性捕取后的回落点
**止损**：新高点上方
**止盈**：下方流动性区或FVG缺口

---

## 系统架构

### 模块划分

```
fvg_liquidity_system/
├── fvg_strategy.py              # FVG策略核心
├── liquidity_analyzer.py        # 流动性分析器
├── multi_timeframe_analyzer.py  # 多周期分析器
├── fvg_signal.py                 # FVG信号数据结构
├── fvg_liquidity_strategy_system.py  # 策略系统
└── parameters/
    └── fvg_liquidity_config.py  # FVG策略参数配置
```

---

### 模块职责

#### 1. fvg_strategy.py
**职责**：
- 识别FVG缺口
- 计算FVG缺口大小
- 判断FVG是否有效
- 生成FVG交易信号

**核心方法**：
```python
class FVGStrategy:
    def identify_fvg(self, klines: List[KLine]) -> List[FVG]:
        """识别FVG缺口"""

    def validate_fvg(self, fvg: FVG, current_price: float) -> bool:
        """验证FVG有效性"""

    def calculate_entry_sl_tp(self, fvg: FVG, signal_type: SignalType) -> Tuple[float, float, float]:
        """计算入场价、止损、止盈"""

    def generate_fvg_signal(self, fvg: FVG, signal_type: SignalType) -> FVGSignal:
        """生成FVG交易信号"""
```

---

#### 2. liquidity_analyzer.py
**职责**：
- 识别买方流动性区
- 识别卖方流动性区
- 检测流动性捕取
- 计算流动性目标位

**核心方法**：
```python
class LiquidityAnalyzer:
    def identify_buyside_liquidity(self, klines: List[KLine]) -> List[LiquidityZone]:
        """识别买方流动性区"""

    def identify_sellside_liquidity(self, klines: List[KLine]) -> List[LiquidityZone]:
        """识别卖方流动性区"""

    def detect_liquidity_sweep(self, klines: List[KLine], liquidity_zone: LiquidityZone) -> bool:
        """检测流动性捕取"""

    def calculate_liquidity_target(self, liquidity_zone: LiquidityZone) -> float:
        """计算流动性目标位"""
```

---

#### 3. multi_timeframe_analyzer.py
**职责**：
- 多周期数据获取
- 多周期FVG分析
- 多周期流动性分析
- 周期信号共振确认

**核心方法**：
```python
class MultiTimeframeAnalyzer:
    def analyze_all_timeframes(self, symbol: str, timeframes: List[str]) -> Dict[str, TimeframeAnalysis]:
        """分析所有周期"""

    def find_confluence(self, analyses: Dict[str, TimeframeAnalysis]) -> ConfluenceAnalysis:
        """寻找周期共振"""

    def prioritize_signals(self, signals: List[FVGSignal]) -> List[FVGSignal]:
        """优先级排序信号"""
```

---

#### 4. fvg_signal.py
**职责**：定义FVG信号数据结构

**数据结构**：
```python
@dataclass
class FVG:
    """FVG缺口"""
    gap_type: FVGType  # BULLISH or BEARISH
    high_bound: float   # 缺口上界
    low_bound: float    # 缺口下界
    size: float         # 缺口大小
    formation_time: int # 形成时间
    kline_index: int    # K线索引
    is_filled: bool     # 是否被填充

@dataclass
class LiquidityZone:
    """流动性区域"""
    zone_type: LiquidityType  # BUYSIDE or SELLSIDE
    level: float              # 流动性水平
    strength: float           # 流动性强度
    touched_count: int        # 被触摸次数
    is_swept: bool           # 是否被扫过

@dataclass
class FVGSignal:
    """FVG交易信号"""
    signal_type: SignalType           # BUY or SELL
    signal_source: SignalSource        # FVG or LIQUIDITY_SWEEP
    symbol: str
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float                  # 信号置信度
    timeframe: str                     # 交易周期
    fvg: Optional[FVG]                 # 关联的FVG
    liquidity_zone: Optional[LiquidityZone]  # 关联的流动性区
    timeframe_confluence: Dict[str, bool]    # 多周期共振
    reason: str
    timestamp: int
```

---

#### 5. fvg_liquidity_strategy_system.py
**职责**：整合所有模块，实现完整的交易流程

**核心流程**：
```python
class FVGLiquidityStrategySystem:
    def analyze_all_symbols(self) -> List[FVGSignal]:
        """分析所有合约"""

    def filter_and_rank_signals(self, signals: List[FVGSignal]) -> List[FVGSignal]:
        """过滤和排序信号"""

    def execute_best_signal(self, signals: List[FVGSignal]) -> bool:
        """执行最佳信号"""
```

---

## 参数配置

### FVG策略参数

```python
@dataclass
class FVGStrategyConfig:
    # FVG识别参数
    min_fvg_size: float = 0.001        # 最小FVG大小（0.1%）
    max_fvg_age: int = 100             # 最大FVG年龄（K线数）
    fvg_timeout_minutes: int = 60      # FVG过期时间（分钟）

    # 入场参数
    entry_tolerance: float = 0.0005    # 入场容差（0.05%）
    require_partial_fill: bool = True  # 要求部分填充后才入场

    # 风险管理
    min_risk_reward: float = 2.0       # 最小盈亏比
    max_risk_per_trade: float = 0.01   # 单笔最大风险（1%）

    # 多周期参数
    primary_timeframe: str = "5m"      # 主周期
    confirm_timeframes: List[str] = field(default_factory=lambda: ["15m", "1h"])  # 确认周期
    min_confluence_count: int = 1     # 最小共振周期数
```

### 流动性分析参数

```python
@dataclass
class LiquidityAnalysisConfig:
    # 流动性识别参数
    swing_lookback: int = 20          # 摆动点回溯周期
    liquidity_threshold: float = 0.001  # 流动性强度阈值（0.1%）
    min_swings_between: int = 3       # 流动性区间之间的最小摆动点数

    # 流动性捕取参数
    sweep_threshold: float = 0.0003   # 捕取阈值（0.03%）
    sweep_retreat: float = 0.0005     # 捕取后的回落阈值（0.05%）
    max_sweep_age: int = 10           # 最大捕取年龄（K线数）

    # 流动性目标
    liquidity_target_atr_ratio: float = 2.0  # 流动性目标 = ATR × 2.0
```

### 多周期分析参数

```python
@dataclass
class MultiTimeframeConfig:
    available_timeframes: List[str] = field(default_factory=lambda: [
        "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d"
    ])

    # 分析深度
    fvg_lookback_periods: Dict[str, int] = field(default_factory=lambda: {
        "1m": 100, "5m": 100, "15m": 100, "1h": 50, "4h": 30
    })

    # 周期权重（用于信号排序）
    timeframe_weights: Dict[str, float] = field(default_factory=lambda: {
        "1m": 0.5, "5m": 1.0, "15m": 1.2, "1h": 1.5, "4h": 2.0
    })
```

---

## 信号评估与排序

### 信号评分系统

**评分维度**（总分100分）：

1. **FVG质量（30分）**
   - FVG大小：10分
   - FVG新鲜度：10分
   - FVG位置：10分（相对于关键位）

2. **流动性强度（25分）**
   - 流动性聚集程度：15分
   - 流动性新鲜度：10分

3. **多周期共振（25分）**
   - 周期共振数量：15分
   - 周期一致性：10分

4. **风险回报比（20分）**
   - 盈亏比：15分
   - 仓位合理性：5分

**置信度计算**：
```
confidence = 总分 / 100
```

**信号过滤**：
- 只执行置信度 ≥ 0.6 的信号
- 优先执行置信度 ≥ 0.8 的信号

---

## 实施计划

### Phase 1: 核心模块开发
1. ✅ 创建 `fvg_signal.py` - 数据结构定义
2. ✅ 创建 `fvg_strategy.py` - FVG策略核心
3. ✅ 创建 `liquidity_analyzer.py` - 流动性分析器
4. ✅ 创建 `multi_timeframe_analyzer.py` - 多周期分析器

### Phase 2: 策略系统集成
5. ✅ 创建 `fvg_liquidity_strategy_system.py` - 策略系统
6. ✅ 更新 `eth_fakeout_gui.py` - GUI界面适配
7. ✅ 更新 `parameter_config.py` - 参数配置

### Phase 3: 测试与优化
8. ✅ 创建测试脚本验证策略
9. ✅ 回测验证策略效果
10. ✅ 优化参数和信号质量

---

## 预期效果

### 与原策略对比

| 维度 | 假突破策略 | FVG流动性策略 |
|-----|-----------|-------------|
| 信号质量 | 中等 | 高 |
| 交易频率 | 中等 | 中高 |
| 胜率 | 50%-60% | 55%-65% |
| 盈亏比 | 2:1 | 2.5:1 |
| 回撤控制 | 一般 | 优秀 |
| 多周期支持 | ❌ | ✅ |

### 策略优势

1. **更高的信号质量**：FVG缺口提供明确的入场点
2. **更好的风险控制**：明确的止损位和止盈目标
3. **多周期确认**：减少假信号
4. **流动性利用**：捕捉市场流动性捕取机会
5. **可扩展性**：支持更多周期和合约

---

## 后续优化方向

1. **机器学习增强**：使用ML模型预测FVG回补概率
2. **订单流分析**：集成订单流数据提升流动性分析精度
3. **自适应参数**：根据市场状态动态调整参数
4. **多策略融合**：将FVG策略与其他策略融合

---

**文档版本**：v1.0
**创建日期**：2026-01-08
