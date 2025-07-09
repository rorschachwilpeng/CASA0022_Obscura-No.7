#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速API测试脚本
验证云端ML API是否正常工作
"""

import requests
import json
from datetime import datetime

# 云端API URL
API_URL = 'https://casa0022-obscura-no-7.onrender.com'

def quick_test():
    """快速测试API功能"""
    print("🚀 快速API测试")
    print("=" * 40)
    
    # 测试数据
    test_locations = [
        {'name': '伦敦', 'lat': 51.5074, 'lon': -0.1278},
        {'name': '曼彻斯特', 'lat': 53.4808, 'lon': -2.2426},
        {'name': '爱丁堡', 'lat': 55.9533, 'lon': -3.1883}
    ]
    
    print(f"🌐 测试URL: {API_URL}")
    
    # 1. 健康检查
    print("\n1️⃣ 健康检查...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ 网站正常运行")
        else:
            print(f"❌ 网站异常: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return
    
    # 2. 测试ML API
    print("\n2️⃣ 测试ML预测...")
    for location in test_locations:
        print(f"\n📍 测试 {location['name']}...")
        
        data = {
            'latitude': location['lat'],
            'longitude': location['lon'],
            'month': datetime.now().month,
            'future_years': 0
        }
        
        try:
            response = requests.post(
                f"{API_URL}/api/v1/ml/predict",
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                pred = result.get('prediction', {})
                
                print(f"   ✅ 预测成功")
                print(f"   🌡️ 温度: {pred.get('temperature', 'N/A'):.1f}°C")
                print(f"   💧 湿度: {pred.get('humidity', 'N/A'):.1f}%")
                print(f"   🌀 气压: {pred.get('pressure', 'N/A'):.1f} hPa")
            else:
                print(f"   ❌ 预测失败: {response.status_code}")
                print(f"   错误: {response.text}")
        except Exception as e:
            print(f"   ❌ 请求异常: {e}")
    
    # 3. 测试网站前端
    print("\n3️⃣ 测试网站前端...")
    try:
        response = requests.get(f"{API_URL}/prediction", timeout=10)
        if response.status_code == 200:
            print("✅ 预测页面正常")
            print(f"   📱 可访问: {API_URL}/prediction")
        else:
            print(f"❌ 预测页面异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 前端测试失败: {e}")
    
    print("\n🎉 快速测试完成！")

if __name__ == "__main__":
    quick_test() 