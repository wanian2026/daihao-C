#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易价值过滤器 - WorthTradingFilter
在策略前判断波动是否足以覆盖交易成本
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from data_fetcher import DataFetcher


@dataclass
class TradingCost:
    """交易成本"""
    taker_fee: float = 0.0005  # 0.05% taker费率
    maker_fee: float = 0.0002  # 0.02% maker费率
    funding_impact: float = 0.0  # 资金费率影响
    spread_cost: float = 0.0  # 点差成本
    slippage: float = 0.0005  # 滑点预估 0.05%
    
    @property
    def total_cost(self) -> float:
        """总成本比例"""
        return self.taker_fee * 2 + self.spread_cost + self.slippage


@dataclass
class WorthTradingResult:
    """值得交易结果"""
    is_worth_trading: bool
    expected_move: float
    total_cost: float
    risk_reward_ratio: float
    min_profit_target: float
    min_stop_loss: float
    reasons: list
    timestamp: datetime


class WorthTradingFilter:
    """交易价值过滤器"""
    
    def __init__(self, data_fetcher: DataFetcher):
        """
        初始化过滤器
        
        Args:
            data_fetcher: 数据获取器
        """
        self.data_fetcher = data_fetcher
        
        # 默认参数
        self.min_rr_ratio = 2.0  # 最小盈亏比
        self.min_expected_move = 0.005  # 最小预期波动 0.5%
        self.cost_multiplier = 2.0  # 成本倍数，预期波动必须大于成本的2倍
    
    def check(self, 
              symbol: str, 
              expected_move: Optional[float] = None,
              stop_loss: Optional[float] = None,
              take_profit: Optional[float] = None) -> WorthTradingResult:
        """
        检查是否值得交易
        
        Args:
            symbol: 交易对
            expected_move: 预期波动比例（如0.01表示1%）
            stop_loss: 止损比例
            take_profit: 止盈比例
            
        Returns:
            是否值得交易
        """
        reasons = []
        
        # 获取当前价格
        current_price = self.data_fetcher.get_latest_price(symbol)
        if current_price == 0:
            return WorthTradingResult(
                is_worth_trading=False,
                expected_move=0,
                total_cost=0,
                risk_reward_ratio=0,
                min_profit_target=0,
                min_stop_loss=0,
                reasons=["无法获取当前价格"],
                timestamp=datetime.now()
            )
        
        # 获取ATR
        atr = self.data_fetcher.get_atr(symbol, interval='5m', period=14)
        if atr == 0:
            return WorthTradingResult(
                is_worth_trading=False,
                expected_move=0,
                total_cost=0,
                risk_reward_ratio=0,
                min_profit_target=0,
                min_stop_loss=0,
                reasons=["无法获取ATR"],
                timestamp=datetime.now()
            )
        
        # 计算成本
        trading_cost = self._calculate_trading_cost(symbol, current_price, atr)
        
        # 计算预期波动（如果未提供）
        if expected_move is None:
            expected_move = atr / current_price
        
        # 计算盈亏比
        risk_reward_ratio = 0
        if stop_loss and take_profit:
            risk_reward_ratio = take_profit / stop_loss
        elif expected_move and trading_cost.total_cost > 0:
            # 使用ATR和成本估算
            risk_reward_ratio = expected_move / (trading_cost.total_cost * self.cost_multiplier)
        
        # 判断是否值得交易
        is_worth = True
        
        # 检查1：预期波动是否足够
        if expected_move < self.min_expected_move:
            is_worth = False
            reasons.append(f"预期波动{expected_move*100:.2f}% < 最小要求{self.min_expected_move*100:.2f}%")
        else:
            reasons.append(f"预期波动{expected_move*100:.2f}% >= 最小要求")
        
        # 检查2：成本是否过高
        cost_threshold = expected_move / self.cost_multiplier
        if trading_cost.total_cost > cost_threshold:
            is_worth = False
            reasons.append(f"交易成本{trading_cost.total_cost*100:.2f}% > 预期波动的{1/self.cost_multiplier*100:.0f}%")
        else:
            reasons.append(f"交易成本{trading_cost.total_cost*100:.3f}% 合理")
        
        # 检查3：盈亏比是否合理
        if risk_reward_ratio > 0 and risk_reward_ratio < self.min_rr_ratio:
            is_worth = False
            reasons.append(f"盈亏比{risk_reward_ratio:.2f} < 最小要求{self.min_rr_ratio:.1f}")
        elif risk_reward_ratio > 0:
            reasons.append(f"盈亏比{risk_reward_ratio:.2f} 合理")
        
        # 计算最小止盈止损
        min_profit_target = max(expected_move, trading_cost.total_cost * self.cost_multiplier)
        min_stop_loss = min_profit_target / self.min_rr_ratio
        
        return WorthTradingResult(
            is_worth_trading=is_worth,
            expected_move=expected_move,
            total_cost=trading_cost.total_cost,
            risk_reward_ratio=risk_reward_ratio,
            min_profit_target=min_profit_target,
            min_stop_loss=min_stop_loss,
            reasons=reasons,
            timestamp=datetime.now()
        )
    
    def _calculate_trading_cost(self, 
                               symbol: str, 
                               current_price: float, 
                               atr: float) -> TradingCost:
        """
        计算交易成本
        
        Args:
            symbol: 交易对
            current_price: 当前价格
            atr: ATR值
            
        Returns:
            交易成本
        """
        cost = TradingCost()
        
        # 获取点差
        price, spread = self.data_fetcher.get_price_and_spread(symbol)
        cost.spread_cost = spread / price if price > 0 else 0
        
        # 获取资金费率
        funding = self.data_fetcher.get_funding_rate(symbol)
        if funding:
            cost.funding_impact = abs(funding)
        
        # 根据市场波动调整滑点
        atr_ratio = atr / current_price
        if atr_ratio > 0.02:
            cost.slippage = 0.001  # 高波动时滑点更大
        elif atr_ratio > 0.01:
            cost.slippage = 0.0007
        
        return cost
    
    def calculate_position_size(self, 
                               symbol: str,
                               account_balance: float,
                               risk_per_trade: float = 0.02) -> float:
        """
        计算仓位大小
        
        Args:
            symbol: 交易对
            account_balance: 账户余额
            risk_per_trade: 单笔风险比例（默认2%）
            
        Returns:
            仓位大小（USDT）
        """
        # 获取ATR
        atr = self.data_fetcher.get_atr(symbol, interval='5m', period=14)
        current_price = self.data_fetcher.get_latest_price(symbol)
        
        if atr == 0 or current_price == 0:
            return 0.0
        
        # 计算止损距离（2倍ATR）
        stop_loss_distance = atr * 2
        
        # 计算风险金额
        risk_amount = account_balance * risk_per_trade
        
        # 计算仓位
        position_size = risk_amount / stop_loss_distance * current_price
        
        return position_size
    
    def calculate_stop_loss(self, 
                           entry_price: float,
                           atr: float,
                           multiplier: float = 2.0,
                           is_long: bool = True) -> float:
        """
        计算止损价格
        
        Args:
            entry_price: 入场价
            atr: ATR值
            multiplier: ATR倍数
            is_long: 是否做多
            
        Returns:
            止损价格
        """
        stop_distance = atr * multiplier
        if is_long:
            return entry_price - stop_distance
        else:
            return entry_price + stop_distance
    
    def calculate_take_profit(self,
                             entry_price: float,
                             stop_loss: float,
                             rr_ratio: float = 2.0,
                             is_long: bool = True) -> float:
        """
        计算止盈价格
        
        Args:
            entry_price: 入场价
            stop_loss: 止损价
            rr_ratio: 盈亏比
            is_long: 是否做多
            
        Returns:
            止盈价格
        """
        risk_distance = abs(entry_price - stop_loss)
        reward_distance = risk_distance * rr_ratio
        
        if is_long:
            return entry_price + reward_distance
        else:
            return entry_price - reward_distance


# 测试代码
if __name__ == "__main__":
    print("交易价值过滤器测试")
    
    from data_fetcher import DataFetcher
    from binance_api_client import BinanceAPIClient
    
    client = BinanceAPIClient()
    fetcher = DataFetcher(client)
    filter_engine = WorthTradingFilter(fetcher)
    
    symbol = "ETHUSDT"
    
    try:
        print(f"\n检查 {symbol} 是否值得交易...")
        result = filter_engine.check(symbol)
        
        print(f"\n值得交易: {result.is_worth_trading}")
        print(f"预期波动: {result.expected_move*100:.2f}%")
        print(f"交易成本: {result.total_cost*100:.3f}%")
        print(f"盈亏比: {result.risk_reward_ratio:.2f}")
        print(f"最小止盈: {result.min_profit_target*100:.2f}%")
        print(f"最小止损: {result.min_stop_loss*100:.2f}%")
        print(f"\n原因:")
        for reason in result.reasons:
            print(f"  - {reason}")
        
        print(f"\n计算仓位大小...")
        position_size = filter_engine.calculate_position_size(symbol, account_balance=1000.0)
        print(f"账户余额: 1000 USDT")
        print(f"仓位大小: {position_size:.2f} USDT")
        
        print(f"\n计算止损止盈...")
        atr = fetcher.get_atr(symbol, interval='5m', period=14)
        current_price = fetcher.get_latest_price(symbol)
        
        stop_loss = filter_engine.calculate_stop_loss(current_price, atr, multiplier=2.0, is_long=True)
        take_profit = filter_engine.calculate_take_profit(current_price, stop_loss, rr_ratio=2.0, is_long=True)
        
        print(f"入场价: {current_price:.2f}")
        print(f"ATR: {atr:.2f}")
        print(f"止损价: {stop_loss:.2f} ({(1-stop_loss/current_price)*100:.2f}%)")
        print(f"止盈价: {take_profit:.2f} ({(take_profit/current_price-1)*100:.2f}%)")
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        print("注意：此测试需要网络连接到币安API")
