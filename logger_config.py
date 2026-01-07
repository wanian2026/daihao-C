#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志配置模块
统一管理系统日志输出
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path


class LoggerConfig:
    """日志配置类"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化日志配置（单例）"""
        if LoggerConfig._initialized:
            return
        
        self.log_dir = Path("logs")
        self.log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        self.date_format = '%Y-%m-%d %H:%M:%S'
        
        # 创建日志目录
        self.log_dir.mkdir(exist_ok=True)
        
        LoggerConfig._initialized = True
    
    def setup_logger(
        self,
        name: str,
        log_file: str = None,
        level: str = "INFO",
        console: bool = True,
        rotating: bool = True,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ) -> logging.Logger:
        """
        设置日志记录器
        
        Args:
            name: 日志记录器名称
            log_file: 日志文件路径（可选）
            level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
            console: 是否输出到控制台
            rotating: 是否启用日志轮转
            max_bytes: 单个日志文件最大字节数
            backup_count: 保留的备份文件数量
            
        Returns:
            logging.Logger: 配置好的日志记录器
        """
        logger = logging.getLogger(name)
        
        # 如果已经配置过，直接返回
        if logger.handlers:
            return logger
        
        # 设置日志级别
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        
        # 创建格式化器
        formatter = logging.Formatter(self.log_format, self.date_format)
        
        # 控制台处理器
        if console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # 文件处理器
        if log_file:
            log_path = self.log_dir / log_file
            
            if rotating:
                # 轮转文件处理器
                file_handler = logging.handlers.RotatingFileHandler(
                    log_path,
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding='utf-8'
                )
            else:
                # 普通文件处理器
                file_handler = logging.FileHandler(
                    log_path,
                    encoding='utf-8'
                )
            
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        获取日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            logging.Logger: 日志记录器
        """
        return logging.getLogger(name)


# 全局日志记录器
_system_logger = None
_trading_logger = None
_api_logger = None
_strategy_logger = None
_error_logger = None


def get_system_logger() -> logging.Logger:
    """获取系统日志记录器"""
    global _system_logger
    if _system_logger is None:
        config = LoggerConfig()
        _system_logger = config.setup_logger(
            name="system",
            log_file=f"system_{datetime.now().strftime('%Y%m%d')}.log",
            level="DEBUG"
        )
    return _system_logger


def get_trading_logger() -> logging.Logger:
    """获取交易日志记录器"""
    global _trading_logger
    if _trading_logger is None:
        config = LoggerConfig()
        _trading_logger = config.setup_logger(
            name="trading",
            log_file=f"trading_{datetime.now().strftime('%Y%m%d')}.log",
            level="DEBUG"
        )
    return _trading_logger


def get_api_logger() -> logging.Logger:
    """获取API日志记录器"""
    global _api_logger
    if _api_logger is None:
        config = LoggerConfig()
        _api_logger = config.setup_logger(
            name="api",
            log_file=f"api_{datetime.now().strftime('%Y%m%d')}.log",
            level="INFO"
        )
    return _api_logger


def get_strategy_logger() -> logging.Logger:
    """获取策略日志记录器"""
    global _strategy_logger
    if _strategy_logger is None:
        config = LoggerConfig()
        _strategy_logger = config.setup_logger(
            name="strategy",
            log_file=f"strategy_{datetime.now().strftime('%Y%m%d')}.log",
            level="DEBUG"
        )
    return _strategy_logger


def get_error_logger() -> logging.Logger:
    """获取错误日志记录器"""
    global _error_logger
    if _error_logger is None:
        config = LoggerConfig()
        _error_logger = config.setup_logger(
            name="error",
            log_file=f"error_{datetime.now().strftime('%Y%m%d')}.log",
            level="ERROR"
        )
    return _error_logger


def setup_all_loggers(level: str = "INFO"):
    """
    设置所有日志记录器
    
    Args:
        level: 日志级别
    """
    # 获取所有日志记录器，初始化它们
    get_system_logger()
    get_trading_logger()
    get_api_logger()
    get_strategy_logger()
    get_error_logger()
    
    # 更新日志级别
    logging.getLogger("system").setLevel(getattr(logging, level.upper(), logging.INFO))
    logging.getLogger("trading").setLevel(getattr(logging, level.upper(), logging.INFO))
    logging.getLogger("api").setLevel(getattr(logging, level.upper(), logging.INFO))
    logging.getLogger("strategy").setLevel(getattr(logging, level.upper(), logging.INFO))
    logging.getLogger("error").setLevel(logging.ERROR)


class LogContext:
    """日志上下文管理器"""
    
    def __init__(self, logger: logging.Logger, level: int, message: str):
        """
        初始化日志上下文
        
        Args:
            logger: 日志记录器
            level: 日志级别
            message: 日志消息
        """
        self.logger = logger
        self.level = level
        self.message = message
        self.start_time = None
    
    def __enter__(self):
        """进入上下文"""
        self.start_time = datetime.now()
        self.logger.log(self.level, f"{self.message} - 开始")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.log(self.level, f"{self.message} - 完成 (耗时: {duration:.2f}秒)")
        else:
            self.logger.error(f"{self.message} - 失败 (耗时: {duration:.2f}秒, 错误: {exc_val})")
        
        # 不抑制异常
        return False


def log_execution_time(logger: logging.Logger, level: int = logging.INFO):
    """
    装饰器：记录函数执行时间
    
    Args:
        logger: 日志记录器
        level: 日志级别
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            start_time = datetime.now()
            
            logger.log(level, f"{func_name} - 开始")
            
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                logger.log(level, f"{func_name} - 完成 (耗时: {duration:.2f}秒)")
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(f"{func_name} - 失败 (耗时: {duration:.2f}秒, 错误: {e})")
                raise
        
        return wrapper
    return decorator


if __name__ == "__main__":
    # 测试日志配置
    setup_all_loggers(level="DEBUG")
    
    system_logger = get_system_logger()
    trading_logger = get_trading_logger()
    
    system_logger.debug("这是一条调试信息")
    system_logger.info("这是一条普通信息")
    system_logger.warning("这是一条警告信息")
    system_logger.error("这是一条错误信息")
    
    # 测试日志上下文
    with LogContext(system_logger, logging.INFO, "测试操作"):
        import time
        time.sleep(1)
    
    # 测试装饰器
    @log_execution_time(system_logger, logging.INFO)
    def test_function():
        import time
        time.sleep(0.5)
        return "完成"
    
    test_function()
    
    print("日志配置测试完成")
