#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖包检查脚本
验证云端是否安装了所有必需的依赖包
"""

import sys
import importlib

def check_dependency(package_name, import_name=None):
    """检查单个依赖包"""
    if import_name is None:
        import_name = package_name
    
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"✅ {package_name}: {version}")
        return True
    except ImportError as e:
        print(f"❌ {package_name}: {e}")
        return False

def main():
    """主检查函数"""
    print("🔍 检查ML模型依赖包...")
    print("=" * 60)
    
    # 核心依赖
    core_deps = [
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('scikit-learn', 'sklearn'),
        ('joblib', 'joblib'),
        ('tensorflow', 'tensorflow'),
        ('requests', 'requests'),
        ('Flask', 'flask'),
        ('psycopg2', 'psycopg2'),
    ]
    
    # 可选依赖
    optional_deps = [
        ('shap', 'shap'),
        ('scipy', 'scipy'),
        ('Pillow', 'PIL'),
    ]
    
    print("📦 核心依赖:")
    core_success = 0
    for package, import_name in core_deps:
        if check_dependency(package, import_name):
            core_success += 1
    
    print(f"\n📦 可选依赖:")
    optional_success = 0
    for package, import_name in optional_deps:
        if check_dependency(package, import_name):
            optional_success += 1
    
    print(f"\n📊 检查结果:")
    print(f"核心依赖: {core_success}/{len(core_deps)} 可用")
    print(f"可选依赖: {optional_success}/{len(optional_deps)} 可用")
    
    if core_success == len(core_deps):
        print("✅ 所有核心依赖都可用，ML模型应该能正常工作")
    else:
        print("❌ 缺少核心依赖，ML模型可能无法正常工作")
    
    return core_success == len(core_deps)

if __name__ == "__main__":
    main() 