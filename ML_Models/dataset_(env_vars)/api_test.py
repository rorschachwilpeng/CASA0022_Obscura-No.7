#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试OpenWeatherMap API密钥的可用服务
"""

import requests
import json

def test_openweather_services(api_key):
    """测试不同的OpenWeatherMap API服务"""
    
    print("🔍 测试OpenWeatherMap API密钥可用性")
    print("=" * 60)
    
    # 测试服务列表
    tests = [
        {
            'name': '当前天气API',
            'url': 'https://api.openweathermap.org/data/2.5/weather',
            'params': {'q': 'London,GB', 'appid': api_key}
        },
        {
            'name': '5天预报API', 
            'url': 'https://api.openweathermap.org/data/2.5/forecast',
            'params': {'q': 'London,GB', 'appid': api_key}
        },
        {
            'name': '历史天气API',
            'url': 'https://api.openweathermap.org/data/2.5/onecall/timemachine',
            'params': {'lat': 51.5074, 'lon': -0.1278, 'dt': 1609459200, 'appid': api_key}
        },
        {
            'name': '统计API (年度)',
            'url': 'https://history.openweathermap.org/data/2.5/aggregated/year',
            'params': {'q': 'London,GB', 'appid': api_key}
        },
        {
            'name': '统计API (月度)',
            'url': 'https://history.openweathermap.org/data/2.5/aggregated/month',
            'params': {'q': 'London,GB', 'month': 6, 'appid': api_key}
        }
    ]
    
    results = []
    
    for test in tests:
        print(f"\n📡 测试: {test['name']}")
        
        try:
            response = requests.get(test['url'], params=test['params'], timeout=10)
            
            if response.status_code == 200:
                print(f"✅ 成功 - {test['name']} 可用")
                data = response.json()
                if isinstance(data, dict) and len(str(data)) > 100:
                    print(f"   数据示例: {str(data)[:100]}...")
                results.append((test['name'], True, response.status_code))
            else:
                print(f"❌ 失败 - {test['name']} 不可用 (状态码: {response.status_code})")
                print(f"   错误信息: {response.text[:200]}")
                results.append((test['name'], False, response.status_code))
                
        except Exception as e:
            print(f"❌ 异常 - {test['name']}: {e}")
            results.append((test['name'], False, 'Exception'))
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    
    available_services = []
    for name, success, status in results:
        if success:
            available_services.append(name)
            print(f"✅ {name}")
        else:
            print(f"❌ {name} (错误: {status})")
    
    print(f"\n🎯 可用服务数量: {len(available_services)}/{len(tests)}")
    
    if available_services:
        print("💡 建议: 使用可用的API服务获取数据")
        if '当前天气API' in available_services:
            print("   - 可以获取实时天气数据")
        if '5天预报API' in available_services:
            print("   - 可以获取短期预报数据")
    else:
        print("⚠️ 没有可用的API服务，请检查API密钥")

def main():
    api_key = "9a5b95af3b09cae239fea38a996a8094"
    test_openweather_services(api_key)

if __name__ == "__main__":
    main() 