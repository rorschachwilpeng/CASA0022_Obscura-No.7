#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
树莓派ML API集成测试
测试从树莓派调用网站的ML预测API
"""

import os
import sys
import requests
import json
from datetime import datetime
import time

# 添加core目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

def test_ml_api_integration():
    """测试ML API集成功能"""
    
    print("=" * 60)
    print("🔬 树莓派ML API集成测试")
    print("=" * 60)
    
    # 配置测试参数
    test_locations = [
        {
            'name': 'London',
            'latitude': 51.5074,
            'longitude': -0.1278,
            'expected_temp_range': (8, 18)  # 大致温度范围
        },
        {
            'name': 'Manchester',
            'latitude': 53.4808,
            'longitude': -2.2426,
            'expected_temp_range': (7, 16)
        },
        {
            'name': 'Edinburgh',
            'latitude': 55.9533,
            'longitude': -3.1883,
            'expected_temp_range': (6, 15)
        }
    ]
    
    # 测试不同的网站URL
    test_urls = [
        'https://your-app.onrender.com',  # 替换为实际的URL
        'http://localhost:5000',  # 本地测试
        'https://obscura-no7.onrender.com'  # 可能的URL
    ]
    
    successful_tests = 0
    total_tests = 0
    
    # 测试每个URL
    for base_url in test_urls:
        print(f"\n🌐 测试API URL: {base_url}")
        print("-" * 50)
        
        # 首先测试健康检查
        try:
            health_response = requests.get(f"{base_url}/health", timeout=10)
            if health_response.status_code == 200:
                print("✅ 健康检查通过")
            else:
                print(f"⚠️ 健康检查失败: {health_response.status_code}")
                continue
        except Exception as e:
            print(f"❌ 无法连接到 {base_url}: {e}")
            continue
        
        # 测试每个位置
        for location in test_locations:
            total_tests += 1
            
            print(f"\n📍 测试位置: {location['name']}")
            print(f"   坐标: {location['latitude']}, {location['longitude']}")
            
            try:
                # 构建预测请求
                prediction_data = {
                    'latitude': location['latitude'],
                    'longitude': location['longitude'],
                    'month': datetime.now().month,
                    'future_years': 0
                }
                
                # 发送预测请求
                start_time = time.time()
                response = requests.post(
                    f"{base_url}/api/v1/ml/predict",
                    json=prediction_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # 验证响应结构
                    if 'prediction' in result and 'model_info' in result:
                        prediction = result['prediction']
                        model_info = result['model_info']
                        
                        print(f"✅ 预测成功 (耗时: {response_time:.2f}s)")
                        print(f"   🌡️ 温度: {prediction.get('temperature', 'N/A')}°C")
                        print(f"   💧 湿度: {prediction.get('humidity', 'N/A')}%")
                        print(f"   🌀 气压: {prediction.get('pressure', 'N/A')} hPa")
                        print(f"   🤖 模型置信度: {model_info.get('confidence', 'N/A')}")
                        print(f"   📊 模型类型: {model_info.get('model_type', 'N/A')}")
                        
                        # 验证温度范围
                        temp = prediction.get('temperature')
                        if temp is not None:
                            min_temp, max_temp = location['expected_temp_range']
                            if min_temp <= temp <= max_temp:
                                print(f"   ✅ 温度在合理范围内")
                            else:
                                print(f"   ⚠️ 温度超出预期范围 ({min_temp}-{max_temp}°C)")
                        
                        successful_tests += 1
                        
                    else:
                        print(f"❌ 响应格式错误: {result}")
                        
                else:
                    print(f"❌ 预测失败: {response.status_code}")
                    try:
                        error_data = response.json()
                        print(f"   错误信息: {error_data.get('error', 'Unknown error')}")
                    except:
                        print(f"   错误信息: {response.text}")
                
            except Exception as e:
                print(f"❌ 请求异常: {e}")
        
        # 如果这个URL有成功的测试，使用它
        if successful_tests > 0:
            print(f"\n🎉 找到可用的API URL: {base_url}")
            working_url = base_url
            break
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果汇总")
    print("=" * 60)
    print(f"总测试数: {total_tests}")
    print(f"成功测试数: {successful_tests}")
    print(f"成功率: {(successful_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
    
    if successful_tests > 0:
        print(f"✅ API集成测试通过！")
        return True
    else:
        print(f"❌ API集成测试失败！")
        return False

def test_cloud_api_client():
    """测试CloudAPIClient的环境预测功能"""
    
    print("\n" + "=" * 60)
    print("🔧 CloudAPIClient 环境预测测试")
    print("=" * 60)
    
    try:
        # 导入CloudAPIClient
        from core.cloud_api_client import CloudAPIClient
        
        # 创建客户端实例（使用默认配置）
        client = CloudAPIClient()
        
        # 测试环境预测
        print("\n📍 测试伦敦环境预测...")
        
        prediction_result = client.predict_environmental_data(
            latitude=51.5074,
            longitude=-0.1278,
            month=datetime.now().month,
            future_years=0
        )
        
        if prediction_result:
            print("✅ 环境预测成功")
            print(f"   预测结果: {prediction_result}")
            
            # 测试与艺术风格预测的集成
            print("\n🎨 测试艺术风格预测集成...")
            
            weather_features = {
                'temperature': 15.0,
                'humidity': 65.0,
                'pressure': 1013.0
            }
            
            location_info = {
                'latitude': 51.5074,
                'longitude': -0.1278,
                'city': 'London'
            }
            
            style_prediction = client.predict_art_style(weather_features, location_info)
            
            if style_prediction:
                print("✅ 艺术风格预测成功")
                print(f"   预测结果: {style_prediction}")
                return True
            else:
                print("❌ 艺术风格预测失败")
                return False
        else:
            print("❌ 环境预测失败")
            return False
            
    except Exception as e:
        print(f"❌ CloudAPIClient测试失败: {e}")
        return False

def main():
    """主函数"""
    print(f"🚀 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试1: 直接API调用
    api_test_result = test_ml_api_integration()
    
    # 测试2: CloudAPIClient集成
    client_test_result = test_cloud_api_client()
    
    print("\n" + "=" * 60)
    print("🏁 总体测试结果")
    print("=" * 60)
    
    if api_test_result and client_test_result:
        print("✅ 所有测试通过！树莓派ML API集成成功！")
        print("\n🎯 下一步:")
        print("  1. 更新config.json中的website_api_url")
        print("  2. 在树莓派上运行完整工作流测试")
        print("  3. 验证端到端数据流")
    else:
        print("❌ 部分测试失败，请检查:")
        print("  - 网站是否正常运行")
        print("  - ML API是否正确部署")
        print("  - 网络连接是否正常")
        print("  - API密钥是否正确配置")
    
    print(f"\n🏁 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 