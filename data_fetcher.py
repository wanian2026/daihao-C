#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据层 - DataFetcher
负责获取K线、Funding、价格与点差数据，所有请求必须可重试
"""

import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from binance_api_client import BinanceAPIClient


class MarketData:
    """市场数据类"""
    
    def __init__(self, 
                 symbol: str,
                 timeframe: str = '5m',
                 open_time: int = 0,
                 open_price: float = 0.0,
                 high: float = 0.0,
                 low: float = 0.0,
                 close: float = 0.0,
                 volume: float = 0.0,
                 close_time: int = 0):
        self.symbol = symbol
        self.timeframe = timeframe
        self.open_time = open_time
        self.open = open_price
        self.high = high
        self.low = low
        self.close = close_price
        self.volume = volume
        self.close_time = close_time
    
    @property
    def body_size(self) -> float:
        """K线实体大小"""
        return abs(self.close - self.open)
    
    @property
    def upper_wick(self) -> float:
        """上影线"""
        return self.high - max(self.open, self.close)
    
    @property
    def lower_wick(self) -> float:
        """下影线"""
        return min(self.open, self.close) - self.low
    
    @property
    def range_size(self) -> float:
        """K线幅度"""
        return self.high - self.low
    
    @property
    def is_bullish(self) -> bool:
        """是否阳线"""
        return self.close > self.open
    
    @property
    def is_bearish(self) -> bool:
        """是否阴线"""
        return self.close < self.open
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'open_time': self.open_time,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'close_time': self.close_time,
            'body_size': self.body_size,
            'upper_wick': self.upper_wick,
            'lower_wick': self.lower_wick,
            'range_size': self.range_size,
            'is_bullish': self.is_bullish,
            'is_bearish': self.is_bearish
        }


class DataFetcher:
    """数据获取器 - 负责获取所有市场数据"""
    
    def __init__(self, api_client: BinanceAPIClient):
        """
        初始化数据获取器
        
        Args:
            api_client: 币安API客户端
        """
        self.api_client = api_client
        self.cache: Dict[str, Dict] = {}
        self.last_update_time: Dict[str, datetime] = {}
        self.cache_ttl_seconds = 10  # 缓存10秒
    
    def _retry_request(self, func, *args, max_retries=3, **kwargs):
        """
        可重试的请求
        
        Args:
            func: 要执行的函数
            max_retries: 最大重试次数
            
        Returns:
            函数执行结果
        """
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(1 * (attempt + 1))  # 递增延迟
    
    def get_klines(self, 
                   symbol: str, 
                   interval: str = '5m', 
                   limit: int = 200) -> List[MarketData]:
        """
        获取K线数据
        
        Args:
            symbol: 交易对
            interval: K线周期 (1m, 5m, 15m, 1h, 4h, 1d等)
            limit: 获取数量
            
        Returns:
            K线数据列表
        """
        cache_key = f"klines_{symbol}_{interval}"
        
        # 检查缓存
        if cache_key in self.cache:
            last_update = self.last_update_time.get(cache_key, datetime.min)
            if (datetime.now() - last_update).total_seconds() < self.cache_ttl_seconds:
                return self.cache[cache_key]
        
        # 获取数据
        def fetch():
            endpoint = '/fapi/v1/klines'
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            result = self.api_client._make_request(endpoint, params=params)
            
            if result.get('error'):
                raise Exception(f"获取K线失败: {result.get('message')}")
            
            # 转换为MarketData对象
            klines = []
            for kline in result:
                klines.append(MarketData(
                    symbol=symbol,
                    timeframe=interval,
                    open_time=kline[0],
                    open_price=float(kline[1]),
                    high=float(kline[2]),
                    low=float(kline[3]),
                    close=float(kline[4]),
                    volume=float(kline[5]),
                    close_time=kline[6]
                ))
            
            return klines
        
        klines = self._retry_request(fetch)
        
        # 更新缓存
        self.cache[cache_key] = klines
        self.last_update_time[cache_key] = datetime.now()
        
        return klines
    
    def get_funding_rate(self, symbol: str) -> Optional[float]:
        """
        获取资金费率
        
        Args:
            symbol: 交易对
            
        Returns:
            资金费率
        """
        def fetch():
            endpoint = '/fapi/v1/premiumIndex'
            params = {'symbol': symbol}
            result = self.api_client._make_request(endpoint, params=params)
            
            if result.get('error'):
                raise Exception(f"获取资金费率失败: {result.get('message')}")
            
            return float(result.get('lastFundingRate', 0.0))
        
        try:
            return self._retry_request(fetch)
        except:
            return None
    
    def get_price_and_spread(self, symbol: str) -> Tuple[float, float]:
        """
        获取价格和点差
        
        Args:
            symbol: 交易对
            
        Returns:
            (价格, 点差)
        """
        def fetch():
            # 获取24小时ticker数据
            endpoint = '/fapi/v1/ticker/24hr'
            params = {'symbol': symbol}
            result = self.api_client._make_request(endpoint, params=params)
            
            if result.get('error'):
                raise Exception(f"获取价格失败: {result.get('message')}")
            
            price = float(result.get('lastPrice', 0))
            spread = float(result.get('askPrice', price)) - float(result.get('bidPrice', price))
            
            return (price, abs(spread))
        
        try:
            return self._retry_request(fetch)
        except:
            return (0.0, 0.0)
    
    def get_atr(self, symbol: str, interval: str = '5m', period: int = 14) -> float:
        """
        计算ATR（平均真实波幅）
        
        Args:
            symbol: 交易对
            interval: K线周期
            period: ATR周期
            
        Returns:
            ATR值
        """
        klines = self.get_klines(symbol, interval, limit=period + 1)
        
        if len(klines) < period + 1:
            return 0.0
        
        true_ranges = []
        for i in range(1, len(klines)):
            prev_kline = klines[i-1]
            curr_kline = klines[i]
            
            tr1 = curr_kline.high - curr_kline.low
            tr2 = abs(curr_kline.high - prev_kline.close)
            tr3 = abs(curr_kline.low - prev_kline.close)
            
            true_ranges.append(max(tr1, tr2, tr3))
        
        if len(true_ranges) == 0:
            return 0.0
        
        return sum(true_ranges) / len(true_ranges)
    
    def get_volume_ma(self, symbol: str, interval: str = '5m', period: int = 20) -> float:
        """
        获取成交量移动平均
        
        Args:
            symbol: 交易对
            interval: K线周期
            period: 周期
            
        Returns:
            成交量移动平均值
        """
        klines = self.get_klines(symbol, interval, limit=period)
        
        if len(klines) < period:
            return 0.0
        
        volumes = [k.volume for k in klines[:period]]
        return sum(volumes) / len(volumes)
    
    def get_latest_price(self, symbol: str) -> float:
        """
        获取最新价格
        
        Args:
            symbol: 交易对
            
        Returns:
            最新价格
        """
        klines = self.get_klines(symbol, interval='1m', limit=1)
        if klines:
            return klines[0].close
        return 0.0
    
    def get_data_freshness(self, symbol: str) -> int:
        """
        获取数据新鲜度（秒）
        
        Args:
            symbol: 交易对
            
        Returns:
            数据延迟秒数
        """
        klines = self.get_klines(symbol, interval='1m', limit=1)
        if not klines:
            return 999
        
        close_time = klines[0].close_time
        current_time = int(datetime.now().timestamp() * 1000)
        return (current_time - close_time) // 1000
    
    def clear_cache(self):
        """清除缓存"""
        self.cache.clear()
        self.last_update_time.clear()


# 测试代码
if __name__ == "__main__":
    print("数据层测试")
    
    # 创建API客户端
    client = BinanceAPIClient()
    fetcher = DataFetcher(client)
    
    symbol = "ETHUSDT"
    
    try:
        # 测试获取K线
        print(f"\n1. 获取 {symbol} 5分钟K线...")
        klines = fetcher.get_klines(symbol, interval='5m', limit=5)
        print(f"✓ 获取到 {len(klines)} 条K线")
        for kline in klines:
            print(f"  {datetime.fromtimestamp(kline.open_time/1000)} | "
                  f"O:{kline.open} H:{kline.high} L:{kline.low} C:{kline.close}")
        
        # 测试获取资金费率
        print(f"\n2. 获取资金费率...")
        funding = fetcher.get_funding_rate(symbol)
        print(f"✓ 资金费率: {funding}")
        
        # 测试获取价格和点差
        print(f"\n3. 获取价格和点差...")
        price, spread = fetcher.get_price_and_spread(symbol)
        print(f"✓ 价格: {price}, 点差: {spread}")
        
        # 测试ATR
        print(f"\n4. 计算ATR...")
        atr = fetcher.get_atr(symbol, interval='5m', period=14)
        print(f"✓ ATR(14): {atr}")
        
        # 测试成交量MA
        print(f"\n5. 计算成交量MA...")
        volume_ma = fetcher.get_volume_ma(symbol, interval='5m', period=20)
        print(f"✓ 成交量MA(20): {volume_ma}")
        
        # 测试数据新鲜度
        print(f"\n6. 检查数据新鲜度...")
        freshness = fetcher.get_data_freshness(symbol)
        print(f"✓ 数据延迟: {freshness} 秒")
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        print("注意：此测试需要网络连接到币安API")
