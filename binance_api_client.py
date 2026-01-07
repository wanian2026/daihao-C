#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
币安API客户端
提供与币安公共API交互的功能
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
import time


class BinanceAPIClient:
    """币安API客户端类"""
    
    # 币安公共API基础URL（无需API Key）
    BASE_URL = "https://fapi.binance.com"
    
    # API端点
    ENDPOINTS = {
        'ping': '/fapi/v1/ping',           # 测试连接
        'time': '/fapi/v1/time',          # 服务器时间
        'exchange_info': '/fapi/v1/exchangeInfo',  # 交易规则和交易对
        'ticker_24h': '/fapi/v1/ticker/24hr',      # 24小时价格变动
    }
    
    def __init__(self):
        """初始化API客户端"""
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'BinanceDesktopApp/1.0'
        })
        self.last_connection_time = None
        self.connection_status = 'disconnected'
        
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        发送API请求
        
        Args:
            endpoint: API端点
            params: 请求参数
            
        Returns:
            响应数据字典
        """
        try:
            url = self.BASE_URL + endpoint
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                self.last_connection_time = datetime.now()
                self.connection_status = 'connected'
                return response.json()
            else:
                self.connection_status = 'error'
                return {
                    'error': True,
                    'status_code': response.status_code,
                    'message': response.text
                }
                
        except requests.exceptions.Timeout:
            self.connection_status = 'timeout'
            return {
                'error': True,
                'message': '请求超时'
            }
        except requests.exceptions.ConnectionError:
            self.connection_status = 'disconnected'
            return {
                'error': True,
                'message': '连接失败'
            }
        except Exception as e:
            self.connection_status = 'error'
            return {
                'error': True,
                'message': str(e)
            }
    
    def ping(self) -> bool:
        """
        测试连接
        
        Returns:
            连接是否成功
        """
        result = self._make_request(self.ENDPOINTS['ping'])
        return not result.get('error', False)
    
    def get_server_time(self) -> Dict:
        """
        获取服务器时间
        
        Returns:
            服务器时间信息
        """
        return self._make_request(self.ENDPOINTS['time'])
    
    def get_exchange_info(self, symbol: Optional[str] = None) -> Dict:
        """
        获取交易规则和交易对信息
        
        Args:
            symbol: 交易对符号，如果为None则获取所有交易对
            
        Returns:
            交易信息
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._make_request(self.ENDPOINTS['exchange_info'], params)
    
    def get_all_symbols(self) -> List[str]:
        """
        获取所有交易对列表
        
        Returns:
            交易对符号列表
        """
        info = self.get_exchange_info()
        if info.get('error'):
            return []
        
        symbols = []
        if 'symbols' in info:
            symbols = [s['symbol'] for s in info['symbols'] if s['status'] == 'TRADING']
        
        return symbols
    
    def get_24h_ticker(self, symbol: Optional[str] = None) -> Dict:
        """
        获取24小时价格变动数据
        
        Args:
            symbol: 交易对符号，如果为None则获取所有交易对
            
        Returns:
            24小时价格数据
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._make_request(self.ENDPOINTS['ticker_24h'], params)
    
    def get_contract_info(self) -> List[Dict]:
        """
        获取所有合约信息
        
        Returns:
            合约信息列表
        """
        info = self.get_exchange_info()
        if info.get('error'):
            return []
        
        contracts = []
        if 'symbols' in info:
            for s in info['symbols']:
                if s['status'] == 'TRADING':
                    contracts.append({
                        'symbol': s['symbol'],
                        'baseAsset': s['baseAsset'],
                        'quoteAsset': s['quoteAsset'],
                        'contractType': s.get('contractType', 'PERPETUAL'),
                        'status': s['status'],
                        'pricePrecision': s.get('pricePrecision', 0),
                        'quantityPrecision': s.get('quantityPrecision', 0),
                    })
        
        return contracts
    
    def get_connection_status(self) -> Dict:
        """
        获取连接状态信息
        
        Returns:
            连接状态字典
        """
        status_info = {
            'status': self.connection_status,
            'last_connected': self.last_connection_time,
            'server_time': None
        }
        
        if self.connection_status == 'connected':
            time_info = self.get_server_time()
            if not time_info.get('error'):
                status_info['server_time'] = time_info.get('serverTime')
        
        return status_info


# 测试代码
if __name__ == "__main__":
    print("测试币安API客户端...")
    
    client = BinanceAPIClient()
    
    # 测试连接
    print("\n1. 测试连接...")
    if client.ping():
        print("✓ 连接成功")
    else:
        print("✗ 连接失败")
    
    # 获取服务器时间
    print("\n2. 获取服务器时间...")
    server_time = client.get_server_time()
    if not server_time.get('error'):
        print(f"✓ 服务器时间: {server_time.get('serverTime')}")
    else:
        print(f"✗ 获取失败: {server_time.get('message')}")
    
    # 获取所有交易对
    print("\n3. 获取所有交易对...")
    symbols = client.get_all_symbols()
    print(f"✓ 共找到 {len(symbols)} 个交易对")
    print(f"  前10个: {symbols[:10]}")
    
    # 获取合约信息
    print("\n4. 获取合约信息...")
    contracts = client.get_contract_info()
    print(f"✓ 共获取 {len(contracts)} 个合约")
    if contracts:
        print(f"  示例合约: {contracts[0]}")
    
    # 获取连接状态
    print("\n5. 连接状态...")
    status = client.get_connection_status()
    print(f"✓ 状态: {status['status']}")
    if status['last_connected']:
        print(f"  最后连接时间: {status['last_connected']}")
