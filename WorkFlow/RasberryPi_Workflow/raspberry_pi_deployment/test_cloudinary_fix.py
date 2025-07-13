#!/usr/bin/env python3
"""测试Cloudinary修复是否有效"""

import os
import sys

# 确保能找到core模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_cloudinary_detection():
    """测试Cloudinary环境变量检测"""
    print("🧪 测试Cloudinary环境变量检测...")
    
    # 检查环境变量
    cloudinary_url = os.getenv('CLOUDINARY_URL')
    if cloudinary_url:
        print(f"✅ 检测到CLOUDINARY_URL: {cloudinary_url[:50]}...")
        return True
    else:
        print("❌ 未检测到CLOUDINARY_URL环境变量")
        return False

def test_cloudinary_import():
    """测试Cloudinary库是否可用"""
    print("🧪 测试Cloudinary库导入...")
    
    try:
        import cloudinary
        import cloudinary.uploader
        print("✅ Cloudinary库导入成功")
        return True
    except ImportError as e:
        print(f"❌ Cloudinary库导入失败: {e}")
        print("   请运行: pip install cloudinary")
        return False

def test_config_manager():
    """测试配置管理器读取环境变量"""
    print("🧪 测试配置管理器...")
    
    try:
        from core.config_manager import ConfigManager
        config_manager = ConfigManager('config/config.json')
        
        # 检查是否能读取Cloudinary URL
        cloudinary_url = config_manager.get('api_keys.cloudinary_url') or os.getenv('CLOUDINARY_URL')
        if cloudinary_url:
            print(f"✅ 配置管理器检测到Cloudinary: {cloudinary_url[:50]}...")
            return True
        else:
            print("❌ 配置管理器未检测到Cloudinary配置")
            return False
            
    except Exception as e:
        print(f"❌ 配置管理器测试失败: {e}")
        return False

def test_cloud_api_client():
    """测试云端API客户端的Cloudinary支持"""
    print("🧪 测试云端API客户端...")
    
    try:
        from core.cloud_api_client import CloudAPIClient
        client = CloudAPIClient()
        
        # 检查client是否有新的方法
        if hasattr(client, '_upload_to_cloudinary'):
            print("✅ 云端API客户端包含Cloudinary方法")
            return True
        else:
            print("❌ 云端API客户端缺少Cloudinary方法")
            return False
            
    except Exception as e:
        print(f"❌ 云端API客户端测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🔧 Cloudinary修复验证测试")
    print("=" * 50)
    
    tests = [
        test_cloudinary_detection,
        test_cloudinary_import,
        test_config_manager,
        test_cloud_api_client
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
        print()
    
    print("=" * 50)
    print("📋 测试结果总结:")
    test_names = [
        "环境变量检测",
        "Cloudinary库",
        "配置管理器",
        "API客户端"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {i+1}. {name}: {status}")
    
    success_count = sum(results)
    print(f"\n📊 成功率: {success_count}/{len(results)} ({success_count/len(results)*100:.0f}%)")
    
    if success_count == len(results):
        print("\n🎉 所有测试通过！修复成功！")
        print("💡 现在在树莓派上运行main.py应该使用Cloudinary上传")
    else:
        print("\n⚠️ 部分测试失败，请检查:")
        if not results[0]:
            print("  - 确保.env文件在正确位置且包含CLOUDINARY_URL")
        if not results[1]:
            print("  - 在树莓派上运行: pip install cloudinary")
        if not results[2] or not results[3]:
            print("  - 检查代码修改是否正确应用")

if __name__ == "__main__":
    main() 