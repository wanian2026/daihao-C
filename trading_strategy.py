#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易策略框架
提供策略基础类和接口，支持策略扩展
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime


class SignalType(Enum):
    """信号类型"""
    BUY = "BUY"           # 买入
    SELL = "SELL"         # 卖出
    HOLD = "HOLD"         # 持有
    CLOSE_LONG = "CLOSE_LONG"  # 平多
    CLOSE_SHORT = "CLOSE_SHORT"  # 平空


@dataclass
class TradingSignal:
    """交易信号"""
    symbol: str
    signal_type: SignalType
    price: Optional[float] = None
    quantity: Optional[float] = None
    confidence: float = 1.0  # 置信度 0-1
    reason: str = ""
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'signal_type': self.signal_type.value,
            'price': self.price,
            'quantity': self.quantity,
            'confidence': self.confidence,
            'reason': self.reason,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class StrategyResult:
    """策略执行结果"""
    symbols: List[str]  # 筛选出的合约列表
    signals: List[TradingSignal]  # 交易信号
    metrics: Dict[str, Any]  # 策略指标
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class BaseStrategy(ABC):
    """策略基类"""
    
    def __init__(self, name: str, params: Optional[Dict] = None):
        """
        初始化策略
        
        Args:
            name: 策略名称
            params: 策略参数
        """
        self.name = name
        self.params = params or {}
        self.is_enabled = True
        self.signals_cache: List[TradingSignal] = []
    
    @abstractmethod
    def filter_symbols(self, all_symbols: List[Dict]) -> List[str]:
        """
        筛选合约
        
        Args:
            all_symbols: 所有合约信息列表
            
        Returns:
            筛选出的合约符号列表
        """
        pass
    
    @abstractmethod
    def generate_signals(self, symbols: List[str], market_data: Dict) -> List[TradingSignal]:
        """
        生成交易信号
        
        Args:
            symbols: 合约符号列表
            market_data: 市场数据
            
        Returns:
            交易信号列表
        """
        pass
    
    def execute(self, all_symbols: List[Dict], market_data: Dict) -> StrategyResult:
        """
        执行策略
        
        Args:
            all_symbols: 所有合约信息
            market_data: 市场数据
            
        Returns:
            策略执行结果
        """
        # 筛选合约
        filtered_symbols = self.filter_symbols(all_symbols)
        
        # 生成信号
        signals = []
        if self.is_enabled:
            signals = self.generate_signals(filtered_symbols, market_data)
            self.signals_cache = signals
        
        # 计算策略指标
        metrics = {
            'filtered_count': len(filtered_symbols),
            'signal_count': len(signals),
            'buy_signals': sum(1 for s in signals if s.signal_type == SignalType.BUY),
            'sell_signals': sum(1 for s in signals if s.signal_type == SignalType.SELL),
        }
        
        return StrategyResult(
            symbols=filtered_symbols,
            signals=signals,
            metrics=metrics
        )
    
    def enable(self):
        """启用策略"""
        self.is_enabled = True
    
    def disable(self):
        """禁用策略"""
        self.is_enabled = False
    
    def update_params(self, params: Dict):
        """更新策略参数"""
        self.params.update(params)
    
    def get_info(self) -> Dict:
        """获取策略信息"""
        return {
            'name': self.name,
            'enabled': self.is_enabled,
            'params': self.params,
            'signal_count': len(self.signals_cache)
        }


class VolumeStrategy(BaseStrategy):
    """成交量策略示例"""
    
    def __init__(self, min_volume: float = 1000000, **kwargs):
        super().__init__(
            name="成交量策略",
            params={'min_volume': min_volume, **kwargs}
        )
    
    def filter_symbols(self, all_symbols: List[Dict]) -> List[str]:
        """基于成交量筛选合约"""
        filtered = []
        for symbol_info in all_symbols:
            # 这里可以从symbol_info中获取成交量数据
            # 简化示例：只返回某些热门交易对
            symbol = symbol_info.get('symbol', '')
            # 示例：筛选BTC和ETH相关合约
            if any(x in symbol for x in ['BTCUSDT', 'ETHUSDT']):
                filtered.append(symbol)
        return filtered
    
    def generate_signals(self, symbols: List[str], market_data: Dict) -> List[TradingSignal]:
        """生成信号（示例）"""
        signals = []
        for symbol in symbols:
            # 示例：这里应该有实际的信号生成逻辑
            # 简化示例：不生成信号
            pass
        return signals


class PriceStrategy(BaseStrategy):
    """价格策略示例"""
    
    def __init__(self, price_change_threshold: float = 0.05, **kwargs):
        super().__init__(
            name="价格策略",
            params={'price_change_threshold': price_change_threshold, **kwargs}
        )
    
    def filter_symbols(self, all_symbols: List[Dict]) -> List[str]:
        """基于价格筛选合约"""
        filtered = []
        for symbol_info in all_symbols:
            symbol = symbol_info.get('symbol', '')
            # 筛选所有USDT合约
            if 'USDT' in symbol:
                filtered.append(symbol)
        return filtered
    
    def generate_signals(self, symbols: List[str], market_data: Dict) -> List[TradingSignal]:
        """生成信号（示例）"""
        signals = []
        # 示例：这里应该有实际的信号生成逻辑
        return signals


class StrategyManager:
    """策略管理器"""
    
    def __init__(self):
        self.strategies: Dict[str, BaseStrategy] = {}
        self.selected_symbols: set = set()
    
    def add_strategy(self, strategy: BaseStrategy):
        """添加策略"""
        self.strategies[strategy.name] = strategy
    
    def remove_strategy(self, name: str):
        """移除策略"""
        if name in self.strategies:
            del self.strategies[name]
    
    def get_strategy(self, name: str) -> Optional[BaseStrategy]:
        """获取策略"""
        return self.strategies.get(name)
    
    def list_strategies(self) -> List[str]:
        """列出所有策略"""
        return list(self.strategies.keys())
    
    def execute_all(self, all_symbols: List[Dict], market_data: Dict) -> Dict[str, StrategyResult]:
        """执行所有策略"""
        results = {}
        for name, strategy in self.strategies.items():
            results[name] = strategy.execute(all_symbols, market_data)
        return results
    
    def select_symbol(self, symbol: str):
        """手动选择合约"""
        self.selected_symbols.add(symbol)
    
    def unselect_symbol(self, symbol: str):
        """取消选择合约"""
        self.selected_symbols.discard(symbol)
    
    def get_selected_symbols(self) -> List[str]:
        """获取已选择的合约"""
        return list(self.selected_symbols)
    
    def clear_selection(self):
        """清空选择"""
        self.selected_symbols.clear()


# 预定义策略
class PredefinedStrategies:
    """预定义策略集合"""
    
    @staticmethod
    def create_volume_strategy(min_volume: float = 1000000) -> VolumeStrategy:
        """创建成交量策略"""
        return VolumeStrategy(min_volume=min_volume)
    
    @staticmethod
    def create_price_strategy(threshold: float = 0.05) -> PriceStrategy:
        """创建价格策略"""
        return PriceStrategy(price_change_threshold=threshold)
    
    @staticmethod
    def create_custom_strategy(name: str, 
                               filter_func: callable,
                               signal_func: callable) -> BaseStrategy:
        """创建自定义策略"""
        class CustomStrategy(BaseStrategy):
            def filter_symbols(self, all_symbols: List[Dict]) -> List[str]:
                return filter_func(all_symbols)
            
            def generate_signals(self, symbols: List[str], market_data: Dict) -> List[TradingSignal]:
                return signal_func(symbols, market_data)
        
        return CustomStrategy(name=name)


# 测试代码
if __name__ == "__main__":
    print("交易策略框架测试")
    print()
    
    # 创建策略管理器
    manager = StrategyManager()
    
    # 添加预定义策略
    volume_strategy = PredefinedStrategies.create_volume_strategy(min_volume=1000000)
    manager.add_strategy(volume_strategy)
    print(f"✓ 添加策略: {volume_strategy.name}")
    
    price_strategy = PredefinedStrategies.create_price_strategy(threshold=0.05)
    manager.add_strategy(price_strategy)
    print(f"✓ 添加策略: {price_strategy.name}")
    
    # 模拟合约数据
    mock_symbols = [
        {'symbol': 'BTCUSDT', 'baseAsset': 'BTC', 'quoteAsset': 'USDT'},
        {'symbol': 'ETHUSDT', 'baseAsset': 'ETH', 'quoteAsset': 'USDT'},
        {'symbol': 'BNBUSDT', 'baseAsset': 'BNB', 'quoteAsset': 'USDT'},
    ]
    
    # 执行策略
    print("\n执行策略...")
    results = manager.execute_all(mock_symbols, {})
    
    for name, result in results.items():
        print(f"\n策略: {name}")
        print(f"  筛选的合约: {result.symbols}")
        print(f"  信号数量: {len(result.signals)}")
        print(f"  指标: {result.metrics}")
    
    # 手动选择合约
    print("\n手动选择合约...")
    manager.select_symbol('BTCUSDT')
    manager.select_symbol('ETHUSDT')
    print(f"已选择的合约: {manager.get_selected_symbols()}")
    
    print("\n✓ 策略框架测试完成")
