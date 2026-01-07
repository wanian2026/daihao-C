#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API密钥管理模块
安全存储和管理币安API密钥
"""

import json
import os
import hashlib
import base64
from typing import Optional, Tuple
from cryptography.fernet import Fernet


class APIKeyManager:
    """API密钥管理器"""
    
    def __init__(self, config_file: str = "api_config.json"):
        """
        初始化密钥管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.encrypted_key_file = "encrypted_key.bin"
        self.fernet = None
        self._init_encryption()
    
    def _init_encryption(self):
        """初始化加密"""
        # 检查是否存在加密密钥文件
        if os.path.exists(self.encrypted_key_file):
            with open(self.encrypted_key_file, 'rb') as f:
                key = f.read()
        else:
            # 生成新的加密密钥
            key = Fernet.generate_key()
            with open(self.encrypted_key_file, 'wb') as f:
                f.write(key)
        
        self.fernet = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """加密数据"""
        if not self.fernet:
            return data
        encrypted = self.fernet.encrypt(data.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """解密数据"""
        if not self.fernet:
            return encrypted_data
        try:
            encrypted = base64.b64decode(encrypted_data.encode())
            decrypted = self.fernet.decrypt(encrypted)
            return decrypted.decode()
        except Exception:
            return ""
    
    def save_credentials(self, api_key: str, api_secret: str, passphrase: Optional[str] = None):
        """
        保存API凭证
        
        Args:
            api_key: API密钥
            api_secret: API密钥
            passphrase: 密码短语（可选）
        """
        config = {
            'api_key': self.encrypt(api_key),
            'api_secret': self.encrypt(api_secret),
            'passphrase': self.encrypt(passphrase) if passphrase else "",
            'is_encrypted': True
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def load_credentials(self) -> Optional[Tuple[str, str, Optional[str]]]:
        """
        加载API凭证
        
        Returns:
            (api_key, api_secret, passphrase) 或 None
        """
        if not os.path.exists(self.config_file):
            return None
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            api_key = self.decrypt(config.get('api_key', ''))
            api_secret = self.decrypt(config.get('api_secret', ''))
            passphrase = self.decrypt(config.get('passphrase', ''))
            
            if not api_key or not api_secret:
                return None
            
            return (api_key, api_secret, passphrase if passphrase else None)
        except Exception as e:
            print(f"加载凭证失败: {e}")
            return None
    
    def has_credentials(self) -> bool:
        """检查是否存在保存的凭证"""
        return os.path.exists(self.config_file)
    
    def clear_credentials(self):
        """清除保存的凭证"""
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
    
    def validate_credentials(self, api_key: str, api_secret: str) -> bool:
        """
        验证凭证格式是否正确
        
        Args:
            api_key: API密钥
            api_secret: API密钥
            
        Returns:
            是否有效
        """
        if not api_key or len(api_key) < 10:
            return False
        if not api_secret or len(api_secret) < 10:
            return False
        return True


# 环境变量支持（可选）
class EnvAPIKeyManager:
    """从环境变量读取API密钥"""
    
    @staticmethod
    def get_credentials() -> Optional[Tuple[str, str, Optional[str]]]:
        """
        从环境变量获取凭证
        
        环境变量：
        - BINANCE_API_KEY
        - BINANCE_API_SECRET
        - BINANCE_API_PASSPHRASE (可选)
        
        Returns:
            (api_key, api_secret, passphrase) 或 None
        """
        api_key = os.environ.get('BINANCE_API_KEY')
        api_secret = os.environ.get('BINANCE_API_SECRET')
        passphrase = os.environ.get('BINANCE_API_PASSPHRASE')
        
        if not api_key or not api_secret:
            return None
        
        return (api_key, api_secret, passphrase)
    
    @staticmethod
    def set_credentials(api_key: str, api_secret: str, passphrase: Optional[str] = None):
        """设置环境变量（仅对当前进程有效）"""
        os.environ['BINANCE_API_KEY'] = api_key
        os.environ['BINANCE_API_SECRET'] = api_secret
        if passphrase:
            os.environ['BINANCE_API_PASSPHRASE'] = passphrase


# 测试代码
if __name__ == "__main__":
    print("测试API密钥管理器...")
    
    manager = APIKeyManager("test_config.json")
    
    # 测试加密解密
    test_data = "test_secret_key_12345"
    encrypted = manager.encrypt(test_data)
    print(f"加密后: {encrypted[:20]}...")
    
    decrypted = manager.decrypt(encrypted)
    print(f"解密后: {decrypted}")
    assert decrypted == test_data, "加密解密失败"
    print("✓ 加密解密测试通过")
    
    # 测试保存和加载
    api_key = "test_api_key_1234567890"
    api_secret = "test_api_secret_0987654321"
    
    manager.save_credentials(api_key, api_secret)
    print("✓ 凭证已保存")
    
    loaded = manager.load_credentials()
    print(f"✓ 凭证已加载: {loaded[0][:10]}... {loaded[1][:10]}...")
    
    assert loaded[0] == api_key, "API密钥不匹配"
    assert loaded[1] == api_secret, "API密钥不匹配"
    print("✓ 保存加载测试通过")
    
    # 清理
    manager.clear_credentials()
    print("✓ 凭证已清除")
    
    # 测试验证
    assert manager.validate_credentials("valid_key_123", "valid_secret_456"), "验证失败"
    assert not manager.validate_credentials("short", "valid_secret_456"), "验证应该失败"
    assert not manager.validate_credentials("valid_key_123", "short"), "验证应该失败"
    print("✓ 凭证验证测试通过")
    
    # 清理测试文件
    if os.path.exists("test_config.json"):
        os.remove("test_config.json")
    if os.path.exists("encrypted_key.bin"):
        os.remove("encrypted_key.bin")
    
    print("\n所有测试通过！")
