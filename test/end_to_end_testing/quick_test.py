#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obscura No.7 快速测试脚本
用于快速验证系统基本功能和API可用性
"""

import requests
import json
import time
from datetime import datetime

class QuickTest:
    """快速测试类"""
    
    def __init__(self, base_url: str = "https://casa0022-obscura-no-7.onrender.com"):
        self.base_url = base_url
        
    def test_system_status(self):
        """测试系统状态"""
        print("🏥 测试系统状态...")
        try:
            response = requests.get(f"{self.base_url}/api/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 系统在线 - 版本: {data.get('version', 'Unknown')}")
                print(f"   ✅ 服务状态: {data.get('services', {})}")
                return True
            else:
                print(f"   ❌ 系统状态异常 - 状态码: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ 系统状态检查失败: {e}")
            return False
    
    def test_ml_api(self):
        """测试ML预测API"""
        print("🔮 测试ML预测API...")
        payload = {
            "environmental_data": {
                "latitude": 51.5074,
                "longitude": -0.1278,
                "temperature": 20.0,
                "humidity": 65,
                "pressure": 1013,
                "wind_speed": 5.0,
                "weather_description": "partly cloudy",
                "location_name": "London Test"
            },
            "hours_ahead": 24
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/v1/ml/predict",
                json=payload,
                timeout=15
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                pred = result.get("prediction", {})
                print(f"   ✅ ML预测成功 - 响应时间: {response_time:.3f}s")
                print(f"   📊 预测温度: {pred.get('predicted_temperature', 'N/A')}°C")
                print(f"   📊 置信度: {pred.get('confidence_score', 'N/A')}")
                return True
            else:
                print(f"   ❌ ML预测失败 - 状态码: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ ML预测异常: {e}")
            return False
    
    def test_gallery_access(self):
        """测试Gallery访问"""
        print("🖼️ 测试Gallery访问...")
        try:
            response = requests.get(f"{self.base_url}/gallery", timeout=10)
            if response.status_code == 200:
                print("   ✅ Gallery页面可访问")
                return True
            else:
                print(f"   ❌ Gallery访问失败 - 状态码: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Gallery访问异常: {e}")
            return False
    
    def test_image_api(self):
        """测试图片API"""
        print("📸 测试图片API...")
        try:
            response = requests.get(f"{self.base_url}/api/v1/images", timeout=10)
            if response.status_code == 200:
                data = response.json()
                count = data.get("count", 0)
                print(f"   ✅ 图片API正常 - 当前图片数: {count}")
                return True
            else:
                print(f"   ❌ 图片API失败 - 状态码: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ 图片API异常: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有快速测试"""
        print("🔭 Obscura No.7 快速测试")
        print("="*50)
        print(f"🕒 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 测试目标: {self.base_url}")
        print("")
        
        tests = [
            ("系统状态", self.test_system_status),
            ("ML预测API", self.test_ml_api),
            ("Gallery访问", self.test_gallery_access),
            ("图片API", self.test_image_api)
        ]
        
        results = []
        for test_name, test_func in tests:
            result = test_func()
            results.append(result)
            print("")
        
        # 统计结果
        passed = sum(results)
        total = len(results)
        success_rate = (passed / total) * 100
        
        print("="*50)
        print(f"📊 测试结果: {passed}/{total} 通过 ({success_rate:.1f}%)")
        
        if success_rate == 100:
            print("🎉 所有测试通过！系统运行正常。")
            return 0
        else:
            print("⚠️ 部分测试失败，请检查系统状态。")
            return 1

def main():
    """主函数"""
    quick_test = QuickTest()
    return quick_test.run_all_tests()

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code) 