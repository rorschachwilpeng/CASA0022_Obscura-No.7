#!/usr/bin/env python3
"""
网络和API诊断脚本
检查网络连接、API配置和基本功能
"""

import json
import os
import requests
import time
from datetime import datetime

def check_network_connectivity():
    """检查基本网络连接"""
    print("🌐 检查网络连接...")
    
    test_sites = [
        "google.com",
        "api.openweathermap.org", 
        "httpbin.org"
    ]
    
    results = {}
    for site in test_sites:
        try:
            import subprocess
            result = subprocess.run(['ping', '-c', '3', site], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"  ✅ {site} - 连接正常")
                results[site] = True
            else:
                print(f"  ❌ {site} - 连接失败")
                results[site] = False
        except Exception as e:
            print(f"  ❌ {site} - 连接失败: {e}")
            results[site] = False
    
    return results

def check_config_file():
    """检查配置文件"""
    print("\n📁 检查配置文件...")
    
    config_path = "config/config.json"
    
    if not os.path.exists(config_path):
        print(f"  ❌ 配置文件不存在: {config_path}")
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"  ✅ 配置文件加载成功")
        
        # 检查关键配置项
        required_keys = ['openweather_api_key', 'google_maps_api_key', 'cloud_api_base_url']
        for key in required_keys:
            if key in config:
                value = config[key]
                if value and value.strip():
                    print(f"  ✅ {key}: {value[:10]}...")
                else:
                    print(f"  ❌ {key}: 空值")
            else:
                print(f"  ❌ {key}: 缺失")
        
        return config
        
    except json.JSONDecodeError as e:
        print(f"  ❌ 配置文件JSON格式错误: {e}")
        return None
    except Exception as e:
        print(f"  ❌ 读取配置文件失败: {e}")
        return None

def test_openweather_api(config):
    """测试OpenWeather API"""
    print("\n🌤️ 测试OpenWeather API...")
    
    if not config or 'openweather_api_key' not in config:
        print("  ❌ 缺少API密钥配置")
        return False
    
    api_key = config['openweather_api_key']
    if not api_key or api_key.strip() == "":
        print("  ❌ API密钥为空")
        return False
    
    # 测试基本API调用
    test_lat, test_lon = 51.5074, -0.1278  # 伦敦坐标
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={test_lat}&lon={test_lon}&appid={api_key}&units=metric"
    
    try:
        print(f"  🔗 测试URL: {url[:50]}...")
        response = requests.get(url, timeout=10)
        
        print(f"  📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ API调用成功")
            print(f"  📍 位置: {data.get('name', 'Unknown')}")
            print(f"  🌡️ 温度: {data.get('main', {}).get('temp', 'N/A')}°C")
            return True
        elif response.status_code == 401:
            print(f"  ❌ API密钥无效 (401)")
            return False
        else:
            print(f"  ❌ API调用失败: {response.status_code}")
            print(f"  📄 响应: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"  ❌ API调用超时")
        return False
    except requests.exceptions.ConnectionError:
        print(f"  ❌ 网络连接错误")
        return False
    except Exception as e:
        print(f"  ❌ API测试失败: {e}")
        return False

def test_cloud_api(config):
    """测试云端API"""
    print("\n☁️ 测试云端API...")
    
    if not config or 'cloud_api_base_url' not in config:
        print("  ❌ 缺少云端API URL配置")
        return False
    
    base_url = config['cloud_api_base_url']
    if not base_url or base_url.strip() == "":
        print("  ❌ 云端API URL为空")
        return False
    
    # 测试健康检查
    health_url = f"{base_url.rstrip('/')}/health"
    
    try:
        print(f"  🔗 测试URL: {health_url}")
        response = requests.get(health_url, timeout=10)
        
        print(f"  📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            print(f"  ✅ 云端API连接正常")
            return True
        else:
            print(f"  ❌ 云端API连接失败: {response.status_code}")
            print(f"  📄 响应: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"  ❌ 云端API调用超时")
        return False
    except requests.exceptions.ConnectionError:
        print(f"  ❌ 云端API网络连接错误")
        return False
    except Exception as e:
        print(f"  ❌ 云端API测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 Obscura No.7 网络和API诊断工具")
    print("=" * 60)
    print(f"⏰ 诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 检查网络连接
    network_results = check_network_connectivity()
    
    # 2. 检查配置文件
    config = check_config_file()
    
    # 3. 测试OpenWeather API
    if config:
        openweather_ok = test_openweather_api(config)
    else:
        openweather_ok = False
    
    # 4. 测试云端API
    if config:
        cloud_api_ok = test_cloud_api(config)
    else:
        cloud_api_ok = False
    
    # 5. 总结报告
    print("\n" + "=" * 60)
    print("📋 诊断总结:")
    print(f"  🌐 网络连接: {'✅ 正常' if any(network_results.values()) else '❌ 异常'}")
    print(f"  📁 配置文件: {'✅ 正常' if config else '❌ 异常'}")
    print(f"  🌤️ OpenWeather API: {'✅ 正常' if openweather_ok else '❌ 异常'}")
    print(f"  ☁️ 云端API: {'✅ 正常' if cloud_api_ok else '❌ 异常'}")
    
    if not any([openweather_ok, cloud_api_ok]):
        print("\n⚠️ 建议:")
        if not config:
            print("  1. 检查config/config.json文件是否存在且格式正确")
        if not openweather_ok:
            print("  2. 检查OpenWeather API密钥是否有效")
        if not any(network_results.values()):
            print("  3. 检查网络连接是否正常")
        if not cloud_api_ok:
            print("  4. 检查云端API服务是否运行")

if __name__ == "__main__":
    main() 