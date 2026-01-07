#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
币安交易API客户端
提供需要认证的交易功能
"""

import hmac
import hashlib
import time
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Union
from binance_api_client import BinanceAPIClient


class BinanceTradingClient(BinanceAPIClient):
    """币安交易API客户端（继承自公共API客户端）"""
    
    # 交易相关API端点
    TRADING_ENDPOINTS = {
        'account': '/fapi/v2/account',           # 账户信息
        'balance': '/fapi/v2/balance',            # 账户余额
        'position': '/fapi/v2/positionRisk',      # 持仓信息
        'order': '/fapi/v1/order',                # 下单
        'open_orders': '/fapi/v1/openOrders',     # 当前挂单
        'all_orders': '/fapi/v1/allOrders',       # 所有订单
        'cancel_order': '/fapi/v1/order',         # 取消订单
        'cancel_all': '/fapi/v1/allOpenOrders',   # 取消所有订单
        'my_trades': '/fapi/v1/userTrades',       # 成交记录
        'leverage': '/fapi/v1/leverage',          # 调整杠杆
        'position_side': '/fapi/v1/positionSide', # 调整持仓模式
    }
    
    def __init__(self, api_key: str, api_secret: str, passphrase: Optional[str] = None):
        """
        初始化交易客户端
        
        Args:
            api_key: API密钥
            api_secret: API密钥
            passphrase: 密码短语（可选，用于其他交易所）
        """
        super().__init__()
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        
        # 更新session headers
        self.session.headers.update({
            'X-MBX-APIKEY': api_key
        })
    
    def _generate_signature(self, params: Dict) -> str:
        """
        生成HMAC SHA256签名
        
        Args:
            params: 请求参数
            
        Returns:
            签名字符串
        """
        # 对参数进行排序并拼接
        query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        
        # 使用HMAC SHA256进行签名
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _make_signed_request(
        self,
        endpoint: str,
        method: str = 'GET',
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict:
        """
        发送签名请求
        
        Args:
            endpoint: API端点
            method: HTTP方法
            params: 请求参数
            data: 请求体数据（POST请求）
            
        Returns:
            响应数据字典
        """
        try:
            # 准备参数
            timestamp = int(time.time() * 1000)
            if params is None:
                params = {}
            params['timestamp'] = timestamp
            
            # 生成签名
            signature = self._generate_signature(params)
            params['signature'] = signature
            
            url = self.BASE_URL + endpoint
            
            # 发送请求
            if method == 'GET':
                response = self.session.get(url, params=params, timeout=10)
            elif method == 'POST':
                response = self.session.post(url, params=params, json=data, timeout=10)
            elif method == 'DELETE':
                response = self.session.delete(url, params=params, timeout=10)
            else:
                return {
                    'error': True,
                    'message': f'不支持的HTTP方法: {method}'
                }
            
            # 处理响应
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.text
                try:
                    error_data = response.json()
                    if 'msg' in error_data:
                        error_msg = error_data['msg']
                    elif 'message' in error_data:
                        error_msg = error_data['message']
                except:
                    pass
                
                return {
                    'error': True,
                    'status_code': response.status_code,
                    'message': error_msg
                }
                
        except requests.exceptions.Timeout:
            return {
                'error': True,
                'message': '请求超时'
            }
        except requests.exceptions.ConnectionError:
            return {
                'error': True,
                'message': '连接失败'
            }
        except Exception as e:
            return {
                'error': True,
                'message': str(e)
            }
    
    def test_connection(self) -> Dict:
        """
        测试API连接和凭证
        
        Returns:
            测试结果
        """
        # 先测试公共API
        if not self.ping():
            return {
                'success': False,
                'message': '公共API连接失败'
            }
        
        # 测试账户信息（需要认证）
        account = self.get_account_info()
        if account.get('error'):
            return {
                'success': False,
                'message': f'认证失败: {account.get("message")}'
            }
        
        return {
            'success': True,
            'message': '认证成功',
            'account_info': account
        }
    
    def get_account_info(self) -> Dict:
        """
        获取账户信息
        
        Returns:
            账户信息
        """
        return self._make_signed_request(self.TRADING_ENDPOINTS['account'])
    
    def get_balance(self) -> Dict:
        """
        获取账户余额
        
        Returns:
            余额信息
        """
        return self._make_signed_request(self.TRADING_ENDPOINTS['balance'])
    
    def get_positions(self) -> List[Dict]:
        """
        获取当前持仓
        
        Returns:
            持仓列表
        """
        result = self._make_signed_request(self.TRADING_ENDPOINTS['position'])
        if result.get('error'):
            return []
        return result
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        获取当前挂单
        
        Args:
            symbol: 交易对符号，如果为None则获取所有
            
        Returns:
            挂单列表
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        result = self._make_signed_request(self.TRADING_ENDPOINTS['open_orders'], params=params)
        if result.get('error'):
            return []
        return result
    
    def place_order(
        self,
        symbol: str,
        side: str,  # 'BUY' or 'SELL'
        order_type: str,  # 'MARKET', 'LIMIT', 'STOP', etc.
        quantity: float,
        price: Optional[float] = None,
        time_in_force: str = 'GTC',  # GTC, IOC, FOK, GTX
        position_side: str = 'BOTH',  # BOTH, LONG, SHORT
        reduce_only: bool = False
    ) -> Dict:
        """
        下单
        
        Args:
            symbol: 交易对
            side: 买卖方向 'BUY' or 'SELL'
            order_type: 订单类型
            quantity: 数量
            price: 价格（限价单需要）
            time_in_force: 有效期类型
            position_side: 持仓方向
            reduce_only: 是否只减仓
            
        Returns:
            订单响应
        """
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': str(quantity),
            'timeInForce': time_in_force,
            'positionSide': position_side,
            'reduceOnly': 'true' if reduce_only else 'false'
        }
        
        if order_type == 'LIMIT' and price:
            params['price'] = str(price)
        
        return self._make_signed_request(
            self.TRADING_ENDPOINTS['order'],
            method='POST',
            params=params
        )
    
    def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        position_side: str = 'BOTH',
        reduce_only: bool = False
    ) -> Dict:
        """
        下市价单
        
        Args:
            symbol: 交易对
            side: 买卖方向
            quantity: 数量
            position_side: 持仓方向
            reduce_only: 是否只减仓
            
        Returns:
            订单响应
        """
        return self.place_order(
            symbol=symbol,
            side=side,
            order_type='MARKET',
            quantity=quantity,
            position_side=position_side,
            reduce_only=reduce_only
        )
    
    def cancel_order(self, symbol: str, order_id: Optional[int] = None, client_order_id: Optional[str] = None) -> Dict:
        """
        取消订单
        
        Args:
            symbol: 交易对
            order_id: 订单ID
            client_order_id: 客户端订单ID
            
        Returns:
            响应
        """
        params = {'symbol': symbol}
        
        if order_id:
            params['orderId'] = order_id
        elif client_order_id:
            params['origClientOrderId'] = client_order_id
        else:
            return {
                'error': True,
                'message': '必须提供orderId或clientOrderId'
            }
        
        return self._make_signed_request(
            self.TRADING_ENDPOINTS['cancel_order'],
            method='DELETE',
            params=params
        )
    
    def cancel_all_orders(self, symbol: str) -> Dict:
        """
        取消某交易对的所有订单
        
        Args:
            symbol: 交易对
            
        Returns:
            响应
        """
        params = {'symbol': symbol}
        return self._make_signed_request(
            self.TRADING_ENDPOINTS['cancel_all'],
            method='DELETE',
            params=params
        )
    
    def set_leverage(self, symbol: str, leverage: int) -> Dict:
        """
        设置杠杆倍数
        
        Args:
            symbol: 交易对
            leverage: 杠杆倍数 (1-125)
            
        Returns:
            响应
        """
        params = {
            'symbol': symbol,
            'leverage': leverage
        }
        return self._make_signed_request(
            self.TRADING_ENDPOINTS['leverage'],
            method='POST',
            params=params
        )
    
    def get_my_trades(self, symbol: str, limit: int = 500) -> List[Dict]:
        """
        获取成交记录
        
        Args:
            symbol: 交易对
            limit: 返回数量限制
            
        Returns:
            成交记录列表
        """
        params = {
            'symbol': symbol,
            'limit': limit
        }
        result = self._make_signed_request(self.TRADING_ENDPOINTS['my_trades'], params=params)
        if result.get('error'):
            return []
        return result


# 测试代码
if __name__ == "__main__":
    print("币安交易API客户端测试")
    print("注意：需要提供真实的API密钥才能测试交易功能")
    print()
    
    # 示例：创建交易客户端（需要提供真实API密钥）
    # api_key = "your_api_key_here"
    # api_secret = "your_api_secret_here"
    
    # client = BinanceTradingClient(api_key, api_secret)
    
    # 测试连接
    # print("测试连接...")
    # result = client.test_connection()
    # if result['success']:
    #     print("✓ 认证成功")
    #     print(f"账户信息: {result['account_info']}")
    # else:
    #     print(f"✗ 认证失败: {result['message']}")
    
    # 测试获取账户余额
    # balance = client.get_balance()
    # print(f"账户余额: {balance}")
    
    # 测试获取持仓
    # positions = client.get_positions()
    # print(f"持仓数量: {len(positions)}")
    
    print("\n注意：请勿在生产环境中运行未经充分测试的交易策略！")
