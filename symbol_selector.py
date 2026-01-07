#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合约选择器 - SymbolSelector
获取币安USDT永续合约列表，支持手动选择和自动筛选
"""

from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from binance_api_client import BinanceAPIClient


class SelectionMode(Enum):
    """选择模式"""
    MANUAL = "MANUAL"         # 手动选择
    AUTO_VOLUME = "AUTO_VOLUME"       # 自动：按成交量
    AUTO_VOLATILITY = "AUTO_VOLATILITY"  # 自动：按波动率
    AUTO_SCORE = "AUTO_SCORE"     # 自动：按综合评分


@dataclass
class SymbolInfo:
    """合约信息"""
    symbol: str
    base_asset: str
    quote_asset: str
    contract_type: str
    status: str
    price: float
    volume_24h: float
    change_24h: float
    mark_price: float
    funding_rate: Optional[float] = None
    atr: Optional[float] = None
    atr_ratio: Optional[float] = None
    volume_ratio: Optional[float] = None
    score: float = 0.0  # 综合评分
    reasons: List[str] = None  # 选择原因


class SymbolSelector:
    """合约选择器"""
    
    def __init__(self, api_client: BinanceAPIClient):
        """
        初始化合约选择器
        
        Args:
            api_client: 币安API客户端
        """
        self.api_client = api_client
        self.all_symbols: List[SymbolInfo] = []
        self.selected_symbols: Set[str] = set()
        self.selection_mode = SelectionMode.AUTO_SCORE
        self.last_update: Optional[datetime] = None
        self.update_interval_minutes = 5  # 每5分钟更新一次合约列表
        
        # 筛选参数
        self.min_volume_24h = 10000000  # 最小24h成交量(USDT)
        self.min_price = 0.1  # 最小价格
        self.max_price = 50000  # 最大价格
        self.top_n_symbols = 10  # 自动筛选时保留前N个
        self.exclude_symbols = {
            'BTCUSDT',  # 保留BTC但设为较低优先级
            'ETHUSDT',  # 保留ETH但设为较高优先级
        }
        
        # 缓存
        self._symbol_cache: Dict[str, Dict] = {}
    
    def update_symbol_list(self, force_update: bool = False) -> List[SymbolInfo]:
        """
        更新合约列表
        
        Args:
            force_update: 是否强制更新
            
        Returns:
            合约列表
        """
        # 检查是否需要更新
        if not force_update and self.last_update:
            elapsed = (datetime.now() - self.last_update).total_seconds() / 60
            if elapsed < self.update_interval_minutes and self.all_symbols:
                return self.all_symbols
        
        try:
            # 获取所有USDT永续合约
            exchange_info = self.api_client._make_request('/fapi/v1/exchangeInfo')
            
            # 检查是否出错
            if isinstance(exchange_info, dict) and exchange_info.get('error'):
                raise Exception(f"获取合约信息失败: {exchange_info.get('message')}")
            
            # 检查是否是有效的数据
            if not isinstance(exchange_info, dict) or 'symbols' not in exchange_info:
                raise Exception("获取合约信息失败: 返回数据格式错误")
            
            # 筛选USDT永续合约
            usdt_perpetuals = []
            for symbol_info in exchange_info.get('symbols', []):
                symbol = symbol_info.get('symbol')
                contract_type = symbol_info.get('contractType')
                quote_asset = symbol_info.get('quoteAsset')
                status = symbol_info.get('status')
                
                # 筛选条件：USDT永续合约且在交易
                if (contract_type == 'PERPETUAL' and 
                    quote_asset == 'USDT' and 
                    status == 'TRADING'):
                    
                    usdt_perpetuals.append({
                        'symbol': symbol,
                        'base_asset': symbol_info.get('baseAsset'),
                        'quote_asset': quote_asset,
                        'contract_type': contract_type,
                        'status': status
                    })
            
            # 获取24小时统计数据
            ticker_24h = self.api_client._make_request('/fapi/v1/ticker/24hr')
            
            # 检查是否出错
            if isinstance(ticker_24h, dict) and ticker_24h.get('error'):
                raise Exception(f"获取24h统计失败: {ticker_24h.get('message')}")
            
            # 检查是否是有效的数据
            if not isinstance(ticker_24h, list):
                raise Exception("获取24h统计失败: 返回数据格式错误")
            
            # 构建24h统计字典
            ticker_dict = {t['symbol']: t for t in ticker_24h}
            
            # 获取标记价格和资金费率
            premium_index = self.api_client._make_request('/fapi/v1/premiumIndex')
            
            # 检查是否出错
            if isinstance(premium_index, dict) and premium_index.get('error'):
                raise Exception(f"获取标记价格失败: {premium_index.get('message')}")
            
            # 检查是否是有效的数据
            if not isinstance(premium_index, list):
                raise Exception("获取标记价格失败: 返回数据格式错误")
            
            premium_dict = {p['symbol']: p for p in premium_index}
            
            # 构建SymbolInfo列表
            symbols = []
            for sym in usdt_perpetuals:
                symbol = sym['symbol']
                ticker = ticker_dict.get(symbol, {})
                premium = premium_dict.get(symbol, {})
                
                try:
                    price = float(premium.get('markPrice', 0))
                    volume_24h = float(ticker.get('quoteVolume', 0))
                    change_24h = float(ticker.get('priceChangePercent', 0))
                    funding_rate = float(premium.get('lastFundingRate', 0)) if premium.get('lastFundingRate') else None
                except (ValueError, TypeError):
                    continue
                
                # 应用基本筛选
                if volume_24h < self.min_volume_24h:
                    continue
                if price < self.min_price or price > self.max_price:
                    continue
                
                symbol_info = SymbolInfo(
                    symbol=symbol,
                    base_asset=sym['base_asset'],
                    quote_asset=sym['quote_asset'],
                    contract_type=sym['contract_type'],
                    status=sym['status'],
                    price=price,
                    volume_24h=volume_24h,
                    change_24h=change_24h,
                    mark_price=price,
                    funding_rate=funding_rate,
                    reasons=[]
                )
                
                symbols.append(symbol_info)
            
            self.all_symbols = symbols
            self.last_update = datetime.now()
            
            # 更新选中的标的
            if self.selection_mode != SelectionMode.MANUAL:
                self._apply_auto_selection()
            
            return self.all_symbols
            
        except Exception as e:
            print(f"更新合约列表失败: {str(e)}")
            return self.all_symbols
    
    def _apply_auto_selection(self):
        """应用自动选择"""
        if not self.all_symbols:
            self.selected_symbols = set()
            return
        
        if self.selection_mode == SelectionMode.AUTO_VOLUME:
            # 按成交量排序
            sorted_symbols = sorted(self.all_symbols, key=lambda x: x.volume_24h, reverse=True)
            self.selected_symbols = {s.symbol for s in sorted_symbols[:self.top_n_symbols]}
            
            # 添加原因
            for s in sorted_symbols[:self.top_n_symbols]:
                s.reasons = [f"成交量排名: {sorted_symbols.index(s) + 1}"]
        
        elif self.selection_mode == SelectionMode.AUTO_VOLATILITY:
            # 按波动率排序（这里用24h涨跌幅代替）
            sorted_symbols = sorted(self.all_symbols, key=lambda x: abs(x.change_24h), reverse=True)
            self.selected_symbols = {s.symbol for s in sorted_symbols[:self.top_n_symbols]}
            
            for s in sorted_symbols[:self.top_n_symbols]:
                s.reasons = [f"波动率: {abs(s.change_24h):.2f}%"]
        
        elif self.selection_mode == SelectionMode.AUTO_SCORE:
            # 按综合评分排序
            for s in self.all_symbols:
                s.score = self._calculate_score(s)
            
            sorted_symbols = sorted(self.all_symbols, key=lambda x: x.score, reverse=True)
            self.selected_symbols = {s.symbol for s in sorted_symbols[:self.top_n_symbols]}
            
            for s in sorted_symbols[:self.top_n_symbols]:
                s.reasons = [f"评分: {s.score:.1f}"]
    
    def _calculate_score(self, symbol_info: SymbolInfo) -> float:
        """
        计算综合评分
        
        Args:
            symbol_info: 合约信息
            
        Returns:
            评分 (0-100)
        """
        score = 0.0
        
        # 1. 成交量评分 (0-30分)
        if symbol_info.volume_24h > 100000000:  # > 1亿
            score += 30
        elif symbol_info.volume_24h > 50000000:  # > 5000万
            score += 25
        elif symbol_info.volume_24h > 10000000:  # > 1000万
            score += 20
        else:
            score += 10
        
        # 2. 波动率评分 (0-25分)
        volatility = abs(symbol_info.change_24h)
        if volatility > 5:
            score += 25
        elif volatility > 3:
            score += 20
        elif volatility > 1:
            score += 15
        else:
            score += 5
        
        # 3. 资金费率评分 (0-20分)
        if symbol_info.funding_rate:
            if -0.0001 <= symbol_info.funding_rate <= 0.0001:  # 费率适中
                score += 20
            elif -0.0003 <= symbol_info.funding_rate <= 0.0003:
                score += 15
            else:
                score += 5  # 费率过高或过低
        else:
            score += 10
        
        # 4. 特殊标的加分/减分
        if symbol_info.symbol == 'ETHUSDT':
            score += 15  # ETH加15分
        elif symbol_info.symbol == 'BTCUSDT':
            score += 10  # BTC加10分
        elif symbol_info.symbol in ['BNBUSDT', 'SOLUSDT', 'DOGEUSDT', 'ADAUSDT']:
            score += 5  # 主流币加5分
        
        return min(score, 100.0)
    
    def update_market_metrics(self, symbol_metrics: Dict[str, Dict]):
        """
        更新市场指标（ATR、成交量比率等）
        
        Args:
            symbol_metrics: 标的指标字典 {symbol: {atr, atr_ratio, volume_ratio}}
        """
        for symbol_info in self.all_symbols:
            symbol = symbol_info.symbol
            if symbol in symbol_metrics:
                metrics = symbol_metrics[symbol]
                symbol_info.atr = metrics.get('atr')
                symbol_info.atr_ratio = metrics.get('atr_ratio')
                symbol_info.volume_ratio = metrics.get('volume_ratio')
                
                # 更新评分
                if self.selection_mode == SelectionMode.AUTO_SCORE:
                    symbol_info.score = self._calculate_score(symbol_info)
        
        # 重新应用自动选择
        if self.selection_mode != SelectionMode.MANUAL:
            self._apply_auto_selection()
    
    def get_selected_symbols(self) -> List[str]:
        """
        获取选中的标的列表
        
        Returns:
            标的列表
        """
        return sorted(list(self.selected_symbols))
    
    def set_selected_symbols(self, symbols: Set[str]):
        """
        手动设置选中的标的
        
        Args:
            symbols: 标的集合
        """
        self.selected_symbols = symbols
        self.selection_mode = SelectionMode.MANUAL
    
    def set_selection_mode(self, mode: SelectionMode):
        """
        设置选择模式
        
        Args:
            mode: 选择模式
        """
        self.selection_mode = mode
        
        # 如果是自动模式，立即应用选择
        if mode != SelectionMode.MANUAL:
            self._apply_auto_selection()
    
    def get_symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        """
        获取指定标的信息
        
        Args:
            symbol: 标的代码
            
        Returns:
            标的信息
        """
        for sym_info in self.all_symbols:
            if sym_info.symbol == symbol:
                return sym_info
        return None
    
    def get_top_symbols(self, n: int = 10) -> List[SymbolInfo]:
        """
        获取评分最高的N个标的
        
        Args:
            n: 数量
            
        Returns:
            标的列表
        """
        sorted_symbols = sorted(self.all_symbols, key=lambda x: x.score, reverse=True)
        return sorted_symbols[:n]
    
    def get_all_symbols(self) -> List[SymbolInfo]:
        """
        获取所有标的
        
        Returns:
            所有标的列表
        """
        return self.all_symbols
