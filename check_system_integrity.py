#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FVG流动性策略系统 - 完整性检查脚本
检查所有必需的模块和依赖是否完整
"""

import sys
import os
from pathlib import Path
from typing import List, Tuple


class SystemIntegrityChecker:
    """系统完整性检查器"""
    
    # 必需的核心模块
    CORE_MODULES = [
        # FVG策略核心模块
        'fvg_strategy.py',
        'liquidity_analyzer.py',
        'multi_timeframe_analyzer.py',
        'fvg_signal.py',
        'fvg_liquidity_strategy_system.py',
        
        # 核心功能模块
        'parameter_config.py',
        'market_state_engine.py',
        'worth_trading_filter.py',
        'risk_manager.py',
        'position_manager.py',
        'symbol_selector.py',
        'data_fetcher.py',
        
        # API模块
        'binance_api_client.py',
        'binance_trading_client.py',
        'api_key_manager.py',
        
        # 工具模块
        'exceptions.py',
        'logger_config.py',
        'utils.py',
    ]
    
    # 可选的测试模块
    TEST_MODULES = [
        'test_fvg_liquidity_system.py',
        'test_fvg_liquidity_strategy.py',
        'test_system_comprehensive.py',
    ]
    
    # Python依赖包
    DEPENDENCIES = [
        'requests',
        'cryptography',
        'docx',  # python-docx
    ]
    
    def __init__(self, project_root: str = None):
        """
        初始化检查器
        
        Args:
            project_root: 项目根目录（默认为脚本所在目录）
        """
        if project_root is None:
            self.project_root = Path(__file__).parent
        else:
            self.project_root = Path(project_root)
        
        self.check_results = []
    
    def check_file_exists(self, file_path: str) -> Tuple[bool, str]:
        """
        检查文件是否存在
        
        Args:
            file_path: 文件路径（相对于项目根目录）
            
        Returns:
            (是否存在, 消息)
        """
        full_path = self.project_root / file_path
        if full_path.exists():
            return True, f"✓ {file_path}"
        else:
            return False, f"✗ {file_path} (缺失)"
    
    def check_module_importable(self, module_name: str) -> Tuple[bool, str]:
        """
        检查模块是否可导入
        
        Args:
            module_name: 模块名（不带.py后缀）
            
        Returns:
            (是否可导入, 消息)
        """
        try:
            __import__(module_name)
            return True, f"✓ {module_name}"
        except ImportError as e:
            return False, f"✗ {module_name} (导入失败: {e})"
    
    def check_python_version(self) -> Tuple[bool, str]:
        """
        检查Python版本
        
        Returns:
            (是否满足要求, 消息)
        """
        version = sys.version_info
        if version >= (3, 6):
            return True, f"✓ Python {version.major}.{version.minor}.{version.micro}"
        else:
            return False, f"✗ Python {version.major}.{version.minor}.{version.micro} (需要3.6+)"
    
    def check_dependencies(self) -> List[Tuple[bool, str]]:
        """
        检查Python依赖包
        
        Returns:
            检查结果列表
        """
        results = []
        for dep in self.DEPENDENCIES:
            if dep == 'docx':
                module_name = 'docx'
            else:
                module_name = dep
            
            success, message = self.check_module_importable(module_name)
            results.append((success, f"  {message}"))
        
        return results
    
    def check_core_modules(self) -> List[Tuple[bool, str]]:
        """
        检查核心模块文件
        
        Returns:
            检查结果列表
        """
        results = []
        for module in self.CORE_MODULES:
            success, message = self.check_file_exists(module)
            results.append((success, f"  {message}"))
        
        return results
    
    def check_test_modules(self) -> List[Tuple[bool, str]]:
        """
        检查测试模块文件（可选）
        
        Returns:
            检查结果列表
        """
        results = []
        for module in self.TEST_MODULES:
            success, message = self.check_file_exists(module)
            results.append((success, f"  {message}"))
        
        return results
    
    def check_configuration_files(self) -> List[Tuple[bool, str]]:
        """
        检查配置文件
        
        Returns:
            检查结果列表
        """
        config_files = [
            'requirements.txt',
            'README.md',
            'FVG流动性策略系统使用手册.md',
        ]
        
        results = []
        for file in config_files:
            success, message = self.check_file_exists(file)
            results.append((success, f"  {message}"))
        
        return results
    
    def run_all_checks(self) -> bool:
        """
        运行所有检查
        
        Returns:
            是否所有必需检查都通过
        """
        print("="*70)
        print("FVG流动性策略系统 - 完整性检查")
        print("="*70)
        print()
        
        # 检查Python版本
        print("1. Python版本检查")
        print("-" * 70)
        success, message = self.check_python_version()
        print(f"  {message}")
        print()
        
        # 检查Python依赖
        print("2. Python依赖包检查")
        print("-" * 70)
        dep_results = self.check_dependencies()
        dep_passed = sum(1 for r, _ in dep_results if r)
        dep_total = len(dep_results)
        for _, message in dep_results:
            print(message)
        print(f"  通过: {dep_passed}/{dep_total}")
        print()
        
        # 检查核心模块
        print("3. 核心模块文件检查")
        print("-" * 70)
        core_results = self.check_core_modules()
        core_passed = sum(1 for r, _ in core_results if r)
        core_total = len(core_results)
        for _, message in core_results:
            print(message)
        print(f"  通过: {core_passed}/{core_total}")
        print()
        
        # 检查配置文件
        print("4. 配置文件检查")
        print("-" * 70)
        config_results = self.check_configuration_files()
        config_passed = sum(1 for r, _ in config_results if r)
        config_total = len(config_results)
        for _, message in config_results:
            print(message)
        print(f"  通过: {config_passed}/{config_total}")
        print()
        
        # 检查测试模块（可选）
        print("5. 测试模块检查（可选）")
        print("-" * 70)
        test_results = self.check_test_modules()
        test_passed = sum(1 for r, _ in test_results if r)
        test_total = len(test_results)
        for _, message in test_results:
            print(message)
        print(f"  通过: {test_passed}/{test_total}")
        print()
        
        # 总结
        print("="*70)
        print("检查总结")
        print("="*70)
        
        # 必需检查项：Python版本、依赖包、核心模块
        required_passed = success + dep_passed + core_passed + config_passed
        required_total = 1 + dep_total + core_total + config_total
        
        print(f"必需项: {required_passed}/{required_total}")
        print(f"Python版本: {'✓' if success else '✗'}")
        print(f"依赖包: {dep_passed}/{dep_total}")
        print(f"核心模块: {core_passed}/{core_total}")
        print(f"配置文件: {config_passed}/{config_total}")
        print(f"测试模块: {test_passed}/{test_total} (可选)")
        print()
        
        # 判断是否通过
        all_required_passed = (success and dep_passed == dep_total and 
                               core_passed == core_total and 
                               config_passed == config_total)
        
        if all_required_passed:
            print("✓ 所有必需检查通过！系统可以正常运行。")
            if test_passed < test_total:
                print(f"  提示: 有{test_total - test_passed}个测试模块缺失（可选）")
        else:
            print("✗ 部分必需检查失败，请修复后再运行系统。")
            
            # 给出修复建议
            print()
            print("修复建议：")
            if not success:
                print("  - 请安装Python 3.6或更高版本")
            if dep_passed < dep_total:
                print("  - 请运行: pip install -r requirements.txt")
            if core_passed < core_total:
                print("  - 请确保所有核心模块文件存在于项目目录中")
            if config_passed < config_total:
                print("  - 请确保配置文件完整")
        
        print()
        print("="*70)
        
        return all_required_passed


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='FVG流动性策略系统完整性检查')
    parser.add_argument('--project-root', type=str, 
                        help='项目根目录（默认为脚本所在目录）')
    
    args = parser.parse_args()
    
    checker = SystemIntegrityChecker(args.project_root)
    success = checker.run_all_checks()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
