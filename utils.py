#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具函数模块
提供常用的辅助函数
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Callable, Any, Optional, List, Dict, Tuple
from functools import wraps


def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple = (Exception,),
    on_failure: Callable = None
):
    """
    重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 退避因子（每次重试后延迟时间乘以此因子）
        exceptions: 需要重试的异常类型
        on_failure: 失败后的回调函数
        
    Example:
        @retry_on_failure(max_retries=3, delay=1.0)
        def fetch_data():
            # 可能失败的操作
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries - 1:
                        # 最后一次尝试失败
                        if on_failure:
                            on_failure(e, max_retries)
                        raise
                    
                    # 记录重试信息
                    print(f"重试 {func.__name__} (第{attempt + 1}次/{max_retries}次), "
                          f"错误: {str(e)}, 延迟: {current_delay:.2f}秒")
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
        return wrapper
    return decorator


def timeout_handler(timeout: float):
    """
    超时装饰器
    
    Args:
        timeout: 超时时间（秒）
        
    Example:
        @timeout_handler(timeout=5.0)
        def long_running_operation():
            # 耗时操作
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = [None]
            exception = [None]
            
            def worker():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=worker)
            thread.daemon = True
            thread.start()
            thread.join(timeout=timeout)
            
            if thread.is_alive():
                from exceptions import TimeoutError
                raise TimeoutError(func.__name__, timeout)
            
            if exception[0]:
                raise exception[0]
            
            return result[0]
        
        return wrapper
    return decorator


def rate_limit(calls_per_second: float):
    """
    速率限制装饰器
    
    Args:
        calls_per_second: 每秒最大调用次数
        
    Example:
        @rate_limit(calls_per_second=2)
        def api_call():
            # API调用
            pass
    """
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            elapsed = now - last_called[0]
            
            if elapsed < min_interval:
                sleep_time = min_interval - elapsed
                time.sleep(sleep_time)
            
            last_called[0] = time.time()
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def safe_cast(value: Any, target_type: type, default: Any = None) -> Any:
    """
    安全类型转换
    
    Args:
        value: 要转换的值
        target_type: 目标类型
        default: 转换失败时的默认值
        
    Returns:
        转换后的值或默认值
    """
    try:
        if value is None:
            return default
        return target_type(value)
    except (ValueError, TypeError):
        return default


def format_timestamp(timestamp: int, format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化时间戳
    
    Args:
        timestamp: 时间戳（毫秒或秒）
        format: 格式字符串
        
    Returns:
        格式化的时间字符串
    """
    if timestamp > 1e12:  # 毫秒时间戳
        timestamp = timestamp / 1000
    return datetime.fromtimestamp(timestamp).strftime(format)


def calculate_percentage(value: float, total: float) -> float:
    """
    计算百分比
    
    Args:
        value: 值
        total: 总数
        
    Returns:
        百分比（0-100）
    """
    if total == 0:
        return 0.0
    return (value / total) * 100


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    限制值在指定范围内
    
    Args:
        value: 原始值
        min_val: 最小值
        max_val: 最大值
        
    Returns:
        限制后的值
    """
    return max(min_val, min(max_val, value))


def round_to_precision(value: float, precision: float = 0.01) -> float:
    """
    四舍五入到指定精度
    
    Args:
        value: 原始值
        precision: 精度
        
    Returns:
        四舍五入后的值
    """
    return round(value / precision) * precision


def format_number(value: float, decimals: int = 2) -> str:
    """
    格式化数字显示
    
    Args:
        value: 数字
        decimals: 小数位数
        
    Returns:
        格式化的字符串
    """
    return f"{value:.{decimals}f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    格式化百分比显示
    
    Args:
        value: 百分比值（0-100）
        decimals: 小数位数
        
    Returns:
        格式化的字符串
    """
    return f"{value:.{decimals}f}%"


def format_currency(value: float, decimals: int = 2) -> str:
    """
    格式化货币显示
    
    Args:
        value: 货币值
        decimals: 小数位数
        
    Returns:
        格式化的字符串
    """
    return f"{value:,.{decimals}f}"


def calculate_pnl(
    entry_price: float,
    exit_price: float,
    side: str,
    quantity: float
) -> float:
    """
    计算盈亏
    
    Args:
        entry_price: 入场价
        exit_price: 退出价
        side: 方向（BUY/SELL）
        quantity: 数量
        
    Returns:
        盈亏
    """
    if side.upper() == "BUY":
        return (exit_price - entry_price) * quantity
    else:  # SELL
        return (entry_price - exit_price) * quantity


def calculate_rr_ratio(
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    side: str
) -> float:
    """
    计算盈亏比
    
    Args:
        entry_price: 入场价
        stop_loss: 止损价
        take_profit: 止盈价
        side: 方向（BUY/SELL）
        
    Returns:
        盈亏比
    """
    if side.upper() == "BUY":
        risk = entry_price - stop_loss
        reward = take_profit - entry_price
    else:  # SELL
        risk = stop_loss - entry_price
        reward = entry_price - take_profit
    
    if risk == 0:
        return float('inf')
    
    return reward / risk


def validate_price(price: float) -> bool:
    """
    验证价格有效性
    
    Args:
        price: 价格
        
    Returns:
        是否有效
    """
    return price is not None and price > 0


def validate_quantity(quantity: float) -> bool:
    """
    验证数量有效性
    
    Args:
        quantity: 数量
        
    Returns:
        是否有效
    """
    return quantity is not None and quantity > 0


class MovingAverage:
    """移动平均线"""
    
    def __init__(self, period: int):
        """
        初始化移动平均线
        
        Args:
            period: 周期
        """
        self.period = period
        self.values = []
    
    def update(self, value: float) -> Optional[float]:
        """
        更新并获取移动平均值
        
        Args:
            value: 新值
            
        Returns:
            移动平均值（如果数据不足则返回None）
        """
        self.values.append(value)
        
        if len(self.values) > self.period:
            self.values.pop(0)
        
        if len(self.values) < self.period:
            return None
        
        return sum(self.values) / self.period


class ExponentialMovingAverage:
    """指数移动平均线"""
    
    def __init__(self, period: int):
        """
        初始化指数移动平均线
        
        Args:
            period: 周期
        """
        self.period = period
        self.multiplier = 2 / (period + 1)
        self.ema: Optional[float] = None
    
    def update(self, value: float) -> float:
        """
        更新并获取EMA值
        
        Args:
            value: 新值
            
        Returns:
            EMA值
        """
        if self.ema is None:
            self.ema = value
        else:
            self.ema = (value - self.ema) * self.multiplier + self.ema
        
        return self.ema


class Timer:
    """计时器"""
    
    def __init__(self):
        """初始化计时器"""
        self.start_time = None
        self.end_time = None
        self.elapsed = None
    
    def start(self):
        """开始计时"""
        self.start_time = time.time()
        self.end_time = None
        self.elapsed = None
    
    def stop(self):
        """停止计时"""
        if self.start_time is None:
            raise RuntimeError("计时器未启动")
        
        self.end_time = time.time()
        self.elapsed = self.end_time - self.start_time
    
    def get_elapsed(self) -> Optional[float]:
        """
        获取经过时间
        
        Returns:
            经过时间（秒），如果未停止则返回当前经过时间
        """
        if self.start_time is None:
            return None
        
        if self.elapsed is not None:
            return self.elapsed
        
        return time.time() - self.start_time
    
    def reset(self):
        """重置计时器"""
        self.start_time = None
        self.end_time = None
        self.elapsed = None


class RateLimiter:
    """速率限制器"""
    
    def __init__(self, calls_per_second: float):
        """
        初始化速率限制器
        
        Args:
            calls_per_second: 每秒最大调用次数
        """
        self.min_interval = 1.0 / calls_per_second
        self.last_called = 0.0
    
    def acquire(self) -> float:
        """
        获取调用权限
        
        Returns:
            等待时间（秒）
        """
        now = time.time()
        elapsed = now - self.last_called
        
        wait_time = 0.0
        if elapsed < self.min_interval:
            wait_time = self.min_interval - elapsed
            time.sleep(wait_time)
        
        self.last_called = time.time()
        return wait_time


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """
    将列表分割成块
    
    Args:
        lst: 原始列表
        chunk_size: 块大小
        
    Returns:
        分割后的列表
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


if __name__ == "__main__":
    # 测试工具函数
    print("测试工具函数...")
    
    # 测试重试装饰器
    @retry_on_failure(max_retries=3, delay=0.5)
    def test_retry():
        import random
        if random.random() < 0.7:  # 70%概率失败
            raise ValueError("随机失败")
        return "成功"
    
    print(f"重试测试: {test_retry()}")
    
    # 测试安全转换
    print(f"安全转换: {safe_cast('123.45', float)}")
    print(f"安全转换: {safe_cast('abc', float, 0.0)}")
    
    # 测试格式化
    print(f"格式化数字: {format_number(1234.5678, 2)}")
    print(f"格式化百分比: {format_percentage(12.3456, 1)}")
    print(f"格式化货币: {format_currency(1234567.89, 2)}")
    
    # 测试盈亏计算
    pnl = calculate_pnl(2000.0, 2050.0, "BUY", 10)
    print(f"盈亏: {format_currency(pnl)}")
    
    # 测试盈亏比
    rr = calculate_rr_ratio(2000.0, 1990.0, 2020.0, "BUY")
    print(f"盈亏比: {rr:.2f}")
    
    # 测试移动平均
    ma = MovingAverage(5)
    for i in range(10):
        value = i * 10
        avg = ma.update(value)
        if avg is not None:
            print(f"MA({i}): {avg:.2f}")
    
    print("工具函数测试完成")
