#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义异常类
定义系统中使用的各种异常类型
"""


class TradingSystemError(Exception):
    """交易系统基础异常"""
    pass


class APIError(TradingSystemError):
    """API相关异常"""
    def __init__(self, message: str, status_code: int = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(APIError):
    """认证失败异常"""
    def __init__(self, message: str = "API认证失败"):
        super().__init__(message, status_code=401)


class NetworkError(APIError):
    """网络连接异常"""
    def __init__(self, message: str = "网络连接失败"):
        super().__init__(message)


class DataFetchError(TradingSystemError):
    """数据获取异常"""
    def __init__(self, symbol: str, timeframe: str, message: str = "数据获取失败"):
        self.symbol = symbol
        self.timeframe = timeframe
        self.message = f"{symbol} {timeframe}: {message}"
        super().__init__(self.message)


class StrategyError(TradingSystemError):
    """策略执行异常"""
    def __init__(self, message: str = "策略执行失败"):
        super().__init__(message)


class SignalGenerationError(StrategyError):
    """信号生成异常"""
    def __init__(self, symbol: str, timeframe: str, reason: str = "信号生成失败"):
        self.symbol = symbol
        self.timeframe = timeframe
        self.message = f"{symbol} {timeframe}: {reason}"
        super().__init__(self.message)


class OrderExecutionError(TradingSystemError):
    """订单执行异常"""
    def __init__(self, symbol: str, side: str, message: str = "订单执行失败"):
        self.symbol = symbol
        self.side = side
        self.message = f"{symbol} {side}: {message}"
        super().__init__(self.message)


class RiskManagementError(TradingSystemError):
    """风险管理异常"""
    def __init__(self, message: str = "风险管理检查失败"):
        super().__init__(message)


class PositionError(TradingSystemError):
    """持仓管理异常"""
    def __init__(self, symbol: str, message: str = "持仓操作失败"):
        self.symbol = symbol
        self.message = f"{symbol}: {message}"
        super().__init__(self.message)


class ConfigurationError(TradingSystemError):
    """配置错误异常"""
    def __init__(self, parameter: str, message: str = "配置错误"):
        self.parameter = parameter
        self.message = f"{parameter}: {message}"
        super().__init__(self.message)


class SystemStateError(TradingSystemError):
    """系统状态异常"""
    def __init__(self, current_state: str, expected_state: str = None, message: str = None):
        self.current_state = current_state
        self.expected_state = expected_state
        if message is None:
            if expected_state:
                self.message = f"当前状态: {current_state}, 期望状态: {expected_state}"
            else:
                self.message = f"无效状态: {current_state}"
        else:
            self.message = message
        super().__init__(self.message)


class ValidationError(TradingSystemError):
    """数据验证异常"""
    def __init__(self, field: str, value: any, reason: str = "验证失败"):
        self.field = field
        self.value = value
        self.message = f"{field}={value}: {reason}"
        super().__init__(self.message)


class TimeoutError(TradingSystemError):
    """超时异常"""
    def __init__(self, operation: str, timeout: float):
        self.operation = operation
        self.timeout = timeout
        self.message = f"{operation} 超时 ({timeout}秒)"
        super().__init__(self.message)


class InsufficientFundsError(OrderExecutionError):
    """资金不足异常"""
    def __init__(self, symbol: str, required: float, available: float):
        self.required = required
        self.available = available
        message = f"资金不足 (需要: {required:.2f}, 可用: {available:.2f})"
        super().__init__(symbol, "ORDER", message)


class MaxPositionSizeExceededError(RiskManagementError):
    """超出最大仓位异常"""
    def __init__(self, symbol: str, current: float, max_size: float):
        self.current = current
        self.max_size = max_size
        message = f"{symbol} 超出最大仓位 (当前: {current:.2f}, 最大: {max_size:.2f})"
        super().__init__(message)


class CircuitBreakerTriggeredError(RiskManagementError):
    """熔断触发异常"""
    def __init__(self, reason: str):
        self.reason = reason
        message = f"熔断已触发: {reason}"
        super().__init__(message)


class MarketSleepError(TradingSystemError):
    """市场休眠异常"""
    def __init__(self, symbol: str, reason: str = "市场休眠"):
        self.symbol = symbol
        self.message = f"{symbol}: {reason}"
        super().__init__(self.message)
