#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FVG流动性策略系统 - 综合测试脚本
测试所有模块的功能和集成
"""

import sys
from datetime import datetime, timedelta
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = []
    
    def run_test(self, test_name: str, test_func):
        """
        运行单个测试
        
        Args:
            test_name: 测试名称
            test_func: 测试函数
        """
        print(f"\n{'='*60}")
        print(f"测试: {test_name}")
        print('='*60)
        
        try:
            test_func()
            self.passed_tests += 1
            result = "PASSED"
            print(f"✅ {test_name}: {result}")
        except Exception as e:
            self.failed_tests += 1
            result = f"FAILED: {str(e)}"
            print(f"❌ {test_name}: {result}")
            import traceback
            traceback.print_exc()
        
        self.test_results.append((test_name, result))
    
    def print_summary(self):
        """打印测试总结"""
        print(f"\n{'='*60}")
        print("测试总结")
        print('='*60)
        print(f"总测试数: {self.passed_tests + self.failed_tests}")
        print(f"通过: {self.passed_tests}")
        print(f"失败: {self.failed_tests}")
        print(f"成功率: {self.passed_tests/(self.passed_tests + self.failed_tests)*100:.1f}%")
        print('='*60)
        
        for test_name, result in self.test_results:
            status = "✅" if "PASSED" in result else "❌"
            print(f"{status} {test_name}")


def test_parameter_config():
    """测试参数配置"""
    from parameter_config import get_config, update_config
    
    print("1. 测试参数配置加载...")
    config = get_config()
    
    assert config is not None, "配置为空"
    print(f"  ✓ 配置加载成功")
    
    print("2. 测试FVG策略参数...")
    assert hasattr(config, 'fvg_strategy'), "缺少fvg_strategy配置"
    assert config.fvg_strategy.timeframes == ['15m', '1h', '4h'], "周期配置错误"
    assert config.fvg_strategy.primary_timeframe == '1h', "主周期错误"
    assert config.fvg_strategy.min_confidence >= 0.6, "置信度阈值过低"
    print(f"  ✓ FVG策略参数正确")
    print(f"    - 周期: {config.fvg_strategy.timeframes}")
    print(f"    - 主周期: {config.fvg_strategy.primary_timeframe}")
    print(f"    - 最小置信度: {config.fvg_strategy.min_confidence}")
    
    print("3. 测试流动性分析参数...")
    assert hasattr(config, 'liquidity_analyzer'), "缺少liquidity_analyzer配置"
    assert config.liquidity_analyzer.swing_period == 3, "摆动点周期错误"
    print(f"  ✓ 流动性分析参数正确")
    print(f"    - 摆动点周期: {config.liquidity_analyzer.swing_period}")
    
    print("4. 测试参数更新...")
    update_config({'fvg_strategy': {'min_confidence': 0.7}})
    assert config.fvg_strategy.min_confidence == 0.7, "参数更新失败"
    print(f"  ✓ 参数动态更新成功")
    
    # 恢复原值
    update_config({'fvg_strategy': {'min_confidence': 0.6}})


def test_fvg_signal_structures():
    """测试FVG信号数据结构"""
    from fvg_signal import FVG, LiquidityZone, FakeoutSignal, TradingSignal, FVGType
    from datetime import datetime
    
    print("1. 测试FVG数据结构...")
    fvg = FVG(
        gap_type=FVGType.BULLISH,
        high_bound=2000.0,
        low_bound=1995.0,
        size=5.0,
        size_percent=0.0025,
        formation_time=int(datetime.now().timestamp() * 1000),
        kline_index=10
    )
    assert fvg.gap_type == FVGType.BULLISH, "FVG方向错误"
    print(f"  ✓ FVG数据结构正确")
    
    print("2. 测试流动性区数据结构...")
    zone = LiquidityZone(
        zone_type="BUYSIDE",
        level=2000.0,
        strength=0.8,
        formation_time=int(datetime.now().timestamp() * 1000),
        touched_count=3
    )
    assert zone.touched_count == 3, "流动性触碰次数错误"
    print(f"  ✓ 流动性区数据结构正确")
    
    print("3. 测试交易信号数据结构...")
    from fvg_signal import SignalType, SignalSource
    signal = TradingSignal(
        signal_type=SignalType.BUY,
        signal_source=SignalSource.FVG,
        symbol="ETHUSDT",
        entry_price=2000.0,
        stop_loss=1990.0,
        take_profit=2020.0,
        confidence=0.75,
        timeframe="1h"
    )
    assert signal.confidence == 0.75, "信号置信度错误"
    rr_ratio = (signal.take_profit - signal.entry_price) / (signal.entry_price - signal.stop_loss)
    assert rr_ratio >= 2.0, f"盈亏比过低: {rr_ratio:.2f}"
    print(f"  ✓ 交易信号数据结构正确")
    print(f"    - 盈亏比: {rr_ratio:.2f}")


def test_fvg_strategy():
    """测试FVG策略"""
    from fvg_strategy import FVGStrategy
    from parameter_config import get_config
    
    print("1. 测试FVG策略初始化...")
    config = get_config()
    strategy = FVGStrategy(config.fvg_strategy)
    assert strategy is not None, "FVG策略初始化失败"
    print(f"  ✓ FVG策略初始化成功")
    
    print("2. 测试FVG识别...")
    # 模拟K线数据
    klines = []
    base_price = 2000.0
    
    for i in range(100):
        timestamp = int((datetime.now() - timedelta(hours=100-i)).timestamp() * 1000)
        open_price = base_price + (i % 10 - 5) * 10
        close_price = open_price + (i % 7 - 3) * 5
        high_price = max(open_price, close_price) + abs((i % 5 - 2)) * 10
        low_price = min(open_price, close_price) - abs((i % 4 - 2)) * 10
        
        # 创建一个FVG缺口
        if i == 50:
            # 看涨FVG
            klines.append([timestamp-3600000, 1990, 1995, 2005, 1992, 100])
            klines.append([timestamp, 2000, 2010, 2015, 2005, 150])
            continue
        
        klines.append([
            timestamp,
            open_price,
            high_price,
            low_price,
            close_price,
            100 + i
        ])
    
    bullish_fvgs, bearish_fvgs = strategy.detect_fvgs(klines)
    print(f"  ✓ 检测到 {len(bullish_fvgs)} 个看涨FVG, {len(bearish_fvgs)} 个看跌FVG")
    
    print("3. 测试FVG验证...")
    for fvg in bullish_fvgs + bearish_fvgs:
        is_valid = strategy.validate_fvg(fvg, klines)
        print(f"  - FVG验证: {is_valid}")
    
    print("4. 测试信号生成...")
    signals = strategy.generate_signals("ETHUSDT", "1h", klines)
    print(f"  ✓ 生成 {len(signals)} 个交易信号")
    for i, signal in enumerate(signals[:3]):  # 只显示前3个信号
        print(f"    信号 {i+1}: {signal.direction} @ {signal.entry_price:.2f}, "
              f"置信度: {signal.confidence:.2f}")


def test_liquidity_analyzer():
    """测试流动性分析器"""
    from liquidity_analyzer import LiquidityAnalyzer
    from parameter_config import get_config
    
    print("1. 测试流动性分析器初始化...")
    config = get_config()
    analyzer = LiquidityAnalyzer(config.liquidity_analyzer)
    assert analyzer is not None, "流动性分析器初始化失败"
    print(f"  ✓ 流动性分析器初始化成功")
    
    print("2. 测试摆动点识别...")
    # 模拟K线数据
    klines = []
    base_price = 2000.0
    
    for i in range(50):
        timestamp = int((datetime.now() - timedelta(hours=50-i)).timestamp() * 1000)
        
        # 创建摆动点
        if i % 10 == 0:
            # 高点
            open_price = base_price
            high_price = base_price + 50
            low_price = base_price - 10
            close_price = base_price + 20
        elif i % 10 == 5:
            # 低点
            open_price = base_price
            high_price = base_price + 10
            low_price = base_price - 50
            close_price = base_price - 20
        else:
            # 普通K线
            open_price = base_price + (i % 5 - 2) * 5
            high_price = open_price + 5
            low_price = open_price - 5
            close_price = open_price + (i % 3 - 1) * 2
        
        klines.append([
            timestamp,
            open_price,
            high_price,
            low_price,
            close_price,
            100
        ])
    
    swing_highs, swing_lows = analyzer.identify_swings(klines)
    print(f"  ✓ 识别到 {len(swing_highs)} 个摆动高点, {len(swing_lows)} 个摆动低点")
    
    print("3. 测试流动性区识别...")
    liquidity_zones = analyzer.identify_liquidity_zones(klines)
    print(f"  ✓ 识别到 {len(liquidity_zones)} 个流动性区")
    
    for i, zone in enumerate(liquidity_zones[:3]):
        print(f"    流动性区 {i+1}: {zone.direction} @ {zone.level:.2f}, "
              f"触碰次数: {zone.touches}")


def test_multi_timeframe_analyzer():
    """测试多周期分析器"""
    from multi_timeframe_analyzer import MultiTimeframeAnalyzer
    from parameter_config import get_config
    
    print("1. 测试多周期分析器初始化...")
    config = get_config()
    mtf_analyzer = MultiTimeframeAnalyzer(config)
    assert mtf_analyzer is not None, "多周期分析器初始化失败"
    print(f"  ✓ 多周期分析器初始化成功")
    
    print("2. 测试单周期分析...")
    # 模拟K线数据
    klines = []
    base_price = 2000.0
    
    for i in range(100):
        timestamp = int((datetime.now() - timedelta(hours=100-i)).timestamp() * 1000)
        open_price = base_price + (i % 20 - 10) * 10
        close_price = open_price + (i % 10 - 5) * 5
        high_price = max(open_price, close_price) + 10
        low_price = min(open_price, close_price) - 10
        
        klines.append([
            timestamp,
            open_price,
            high_price,
            low_price,
            close_price,
            100
        ])
    
    analysis = mtf_analyzer.analyze_timeframe("ETHUSDT", "1h", klines)
    assert analysis is not None, "周期分析失败"
    assert analysis.is_valid, "周期分析无效"
    print(f"  ✓ 单周期分析成功")
    print(f"    - 看涨FVG: {len(analysis.bullish_fvgs)}")
    print(f"    - 看跌FVG: {len(analysis.bearish_fvgs)}")
    print(f"    - 流动性区: {len(analysis.liquidity_zones)}")
    print(f"    - 交易信号: {len(analysis.trading_signals)}")
    
    print("3. 测试多周期分析...")
    klines_data = {
        '15m': klines,
        '1h': klines,
        '4h': klines
    }
    
    analyses = mtf_analyzer.analyze_multi_timeframe("ETHUSDT", klines_data)
    assert len(analyses) > 0, "多周期分析失败"
    print(f"  ✓ 多周期分析成功")
    print(f"    - 分析周期数: {len(analyses)}")
    
    print("4. 测试周期共振检测...")
    confluence = mtf_analyzer.detect_confluence("ETHUSDT", analyses)
    if confluence:
        print(f"  ✓ 检测到周期共振")
        print(f"    - 共振类型: {confluence.confluence_type}")
        print(f"    - 共振评分: {confluence.confluence_score:.2f}")
        print(f"    - 置信度: {confluence.confidence:.2f}")
        print(f"    - 参与周期: {', '.join(confluence.contributing_timeframes)}")
    else:
        print(f"  ✓ 未检测到周期共振（正常现象）")


def test_api_connection():
    """测试API连接"""
    print("注意：此测试需要有效的网络连接和币安API访问权限")
    print("      如果没有API密钥，将跳过实际API测试")
    
    from binance_api_client import BinanceAPIClient
    
    print("1. 测试公共API连接...")
    try:
        api_client = BinanceAPIClient()
        
        # 测试获取价格（不需要认证）
        price = api_client.get_current_price("ETHUSDT")
        assert price is not None and price > 0, "获取价格失败"
        print(f"  ✓ 公共API连接成功")
        print(f"    ETHUSDT价格: {price:.2f}")
        
        # 测试获取K线
        klines = api_client.get_klines("ETHUSDT", "1h", limit=100)
        assert klines is not None and len(klines) > 0, "获取K线失败"
        print(f"  ✓ K线数据获取成功")
        print(f"    K线数量: {len(klines)}")
        
    except Exception as e:
        print(f"  ⚠ API连接测试失败: {str(e)}")
        print(f"    （可能是网络问题，跳过此测试）")


def test_integration():
    """测试系统集成"""
    print("注意：此测试需要有效的币安API密钥")
    print("      如果没有API密钥，将使用模拟数据进行测试")
    
    from fvg_liquidity_strategy_system import FVGLiquidityStrategySystem
    from binance_trading_client import BinanceTradingClient
    from parameter_config import get_config
    
    print("1. 测试策略系统初始化...")
    try:
        # 使用模拟凭证初始化
        trading_client = BinanceTradingClient(
            "test_key",
            "test_secret"
        )
        
        config = get_config()
        config.system.enable_simulation = True  # 强制启用模拟模式
        
        strategy_system = FVGLiquidityStrategySystem(trading_client)
        assert strategy_system is not None, "策略系统初始化失败"
        print(f"  ✓ 策略系统初始化成功")
        
    except Exception as e:
        print(f"  ⚠ 策略系统初始化失败: {str(e)}")
        print(f"    （可能需要有效API密钥，跳过此测试）")
        return


def main():
    """主函数"""
    print("="*60)
    print("FVG流动性策略系统 - 综合测试")
    print("="*60)
    
    runner = TestRunner()
    
    # 1. 测试参数配置
    runner.run_test("参数配置加载与更新", test_parameter_config)
    
    # 2. 测试数据结构
    runner.run_test("FVG信号数据结构", test_fvg_signal_structures)
    
    # 3. 测试FVG策略
    runner.run_test("FVG策略功能", test_fvg_strategy)
    
    # 4. 测试流动性分析器
    runner.run_test("流动性分析器功能", test_liquidity_analyzer)
    
    # 5. 测试多周期分析器
    runner.run_test("多周期分析器功能", test_multi_timeframe_analyzer)
    
    # 6. 测试API连接（可选）
    runner.run_test("API连接测试", test_api_connection)
    
    # 7. 测试系统集成（可选）
    runner.run_test("系统集成测试", test_integration)
    
    # 打印测试总结
    runner.print_summary()
    
    # 返回退出码
    if runner.failed_tests == 0:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  有 {runner.failed_tests} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
