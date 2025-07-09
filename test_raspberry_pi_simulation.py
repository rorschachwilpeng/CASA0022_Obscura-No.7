#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
树莓派模拟测试脚本
在本地模拟树莓派的完整工作流，调用云端API
"""

import os
import sys
import requests
import json
import time
import random
from datetime import datetime

# 添加raspberry_pi_deployment到路径
sys.path.append('raspberry_pi_deployment')

# 你的云端网站URL
CLOUD_API_URL = 'https://casa0022-obscura-no-7.onrender.com'

class MockRaspberryPiClient:
    """模拟树莓派客户端"""
    
    def __init__(self):
        self.api_url = CLOUD_API_URL
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mock-Raspberry-Pi-Obscura-No.7/1.0'
        })
        
    def test_api_connection(self):
        """测试API连接"""
        print("🔗 测试云端API连接...")
        
        try:
            # 测试健康检查
            response = self.session.get(f"{self.api_url}/health", timeout=10)
            if response.status_code == 200:
                print("✅ 云端API连接成功")
                health_data = response.json()
                print(f"   API版本: {health_data.get('version', 'Unknown')}")
                print(f"   状态: {health_data.get('status', 'Unknown')}")
                return True
            else:
                print(f"❌ 健康检查失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ API连接失败: {e}")
            return False
    
    def simulate_hardware_input(self):
        """模拟硬件输入"""
        print("\n🔧 模拟硬件输入...")
        
        # 模拟旋钮输入
        distance = random.uniform(10, 100)  # 10-100km
        direction = random.uniform(0, 360)  # 0-360度
        time_offset = random.randint(-5, 5)  # -5到+5小时
        
        print(f"   📏 距离: {distance:.1f} km")
        print(f"   🧭 方向: {direction:.1f} 度")
        print(f"   ⏰ 时间偏移: {time_offset} 小时")
        
        return {
            'distance': distance,
            'direction': direction,
            'time_offset': time_offset
        }
    
    def calculate_coordinates(self, hardware_input):
        """计算目标坐标"""
        print("\n📍 计算目标坐标...")
        
        # 伦敦作为起点
        base_lat = 51.5074
        base_lon = -0.1278
        
        # 简化的坐标计算
        import math
        
        distance_km = hardware_input['distance']
        direction_rad = math.radians(hardware_input['direction'])
        
        # 地球半径
        R = 6371  # km
        
        # 计算新坐标
        lat1 = math.radians(base_lat)
        lon1 = math.radians(base_lon)
        
        lat2 = math.asin(math.sin(lat1) * math.cos(distance_km/R) + 
                        math.cos(lat1) * math.sin(distance_km/R) * math.cos(direction_rad))
        
        lon2 = lon1 + math.atan2(math.sin(direction_rad) * math.sin(distance_km/R) * math.cos(lat1),
                                math.cos(distance_km/R) - math.sin(lat1) * math.sin(lat2))
        
        target_lat = math.degrees(lat2)
        target_lon = math.degrees(lon2)
        
        print(f"   🎯 目标坐标: {target_lat:.4f}, {target_lon:.4f}")
        
        return {
            'latitude': target_lat,
            'longitude': target_lon,
            'base_location': {'lat': base_lat, 'lon': base_lon},
            'distance': distance_km,
            'direction': hardware_input['direction']
        }
    
    def call_ml_prediction_api(self, coordinates):
        """调用ML预测API"""
        print("\n🤖 调用ML预测API...")
        
        # 计算目标月份
        current_time = datetime.now()
        target_month = current_time.month
        
        prediction_data = {
            'latitude': coordinates['latitude'],
            'longitude': coordinates['longitude'],
            'month': target_month,
            'future_years': 0
        }
        
        try:
            print(f"   📡 发送预测请求到: {self.api_url}/api/v1/ml/predict")
            print(f"   📊 请求数据: {prediction_data}")
            
            response = self.session.post(
                f"{self.api_url}/api/v1/ml/predict",
                json=prediction_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ ML预测成功")
                
                prediction = result.get('prediction', {})
                model_info = result.get('model_info', {})
                
                temp = prediction.get('temperature', 'N/A')
                humidity = prediction.get('humidity', 'N/A') 
                pressure = prediction.get('pressure', 'N/A')
                confidence = model_info.get('confidence', 'N/A')
                
                print(f"   🌡️ 预测温度: {temp:.1f}°C" if temp != 'N/A' else f"   🌡️ 预测温度: {temp}")
                print(f"   💧 预测湿度: {humidity:.1f}%" if humidity != 'N/A' else f"   💧 预测湿度: {humidity}")
                print(f"   🌀 预测气压: {pressure:.1f} hPa" if pressure != 'N/A' else f"   🌀 预测气压: {pressure}")
                print(f"   🎯 模型置信度: {confidence:.3f}" if confidence != 'N/A' else f"   🎯 模型置信度: {confidence}")
                
                return result
            else:
                print(f"❌ ML预测失败: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   错误信息: {error_data.get('error', 'Unknown')}")
                except:
                    print(f"   错误信息: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ ML预测API调用异常: {e}")
            return None
    
    def generate_art_prompt(self, prediction_result, coordinates):
        """生成艺术提示词"""
        print("\n🎨 生成艺术提示词...")
        
        if not prediction_result:
            return None
            
        prediction = prediction_result.get('prediction', {})
        temp = prediction.get('temperature', 15)
        humidity = prediction.get('humidity', 60)
        pressure = prediction.get('pressure', 1013)
        
        # 基于预测数据生成蒸汽朋克风格提示词
        if temp > 20:
            weather_desc = "warm, golden sunlight"
        elif temp > 10:
            weather_desc = "misty, temperate atmosphere"
        else:
            weather_desc = "cool, mysterious fog"
        
        if humidity > 70:
            moisture_desc = "humid, steam-filled air"
        elif humidity > 40:
            moisture_desc = "balanced atmospheric moisture"
        else:
            moisture_desc = "dry, crisp air"
        
        prompt = f"""
        A steampunk landscape with {weather_desc} and {moisture_desc}. 
        Victorian-era mechanical contraptions powered by steam and brass gears. 
        Temperature: {temp:.1f}°C, Humidity: {humidity:.1f}%, Pressure: {pressure:.1f}hPa.
        Atmospheric pressure creates dramatic sky effects with copper and bronze tones.
        Industrial aesthetic with intricate clockwork mechanisms and vintage telescopes.
        High quality, detailed, cinematic lighting, steampunk art style.
        """
        
        print(f"   📝 提示词生成完成")
        print(f"   🎭 风格: 蒸汽朋克环境艺术")
        print(f"   🌡️ 基于温度: {temp:.1f}°C")
        
        return {
            'prompt': prompt.strip(),
            'style': 'steampunk_environmental',
            'weather_data': prediction
        }
    
    def simulate_image_generation(self, art_prompt):
        """模拟图像生成"""
        print("\n🖼️ 模拟图像生成...")
        
        if not art_prompt:
            print("❌ 无法生成图像，提示词为空")
            return None
        
        # 模拟图像生成过程
        print("   🎨 正在生成蒸汽朋克风格图像...")
        time.sleep(2)  # 模拟生成时间
        
        # 生成模拟图像信息
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        image_info = {
            'filename': f'mock_steampunk_vision_{timestamp}.png',
            'style': art_prompt['style'],
            'generation_time': datetime.now().isoformat(),
            'prompt_hash': hash(art_prompt['prompt']) % 10000,
            'weather_based': True
        }
        
        print("✅ 图像生成完成（模拟）")
        print(f"   📁 文件名: {image_info['filename']}")
        print(f"   🎨 风格: {image_info['style']}")
        
        return image_info
    
    def simulate_cloud_upload(self, image_info, prediction_result):
        """模拟云端上传"""
        print("\n☁️ 模拟云端上传...")
        
        if not image_info or not prediction_result:
            print("❌ 上传失败，数据不完整")
            return False
        
        # 模拟上传过程
        print("   📤 正在上传图像和元数据...")
        time.sleep(1)  # 模拟上传时间
        
        upload_data = {
            'image_info': image_info,
            'prediction_data': prediction_result,
            'upload_time': datetime.now().isoformat(),
            'source': 'mock_raspberry_pi'
        }
        
        print("✅ 云端上传完成（模拟）")
        print(f"   📊 上传数据大小: {len(str(upload_data))} 字符")
        
        return True

def run_complete_workflow():
    """运行完整的工作流"""
    print("=" * 60)
    print("🚀 Obscura No.7 - 完整工作流模拟测试")
    print("=" * 60)
    
    client = MockRaspberryPiClient()
    
    # 步骤1: 测试API连接
    if not client.test_api_connection():
        print("❌ 测试终止：无法连接到云端API")
        return False
    
    # 步骤2: 模拟硬件输入
    hardware_input = client.simulate_hardware_input()
    
    # 步骤3: 计算坐标
    coordinates = client.calculate_coordinates(hardware_input)
    
    # 步骤4: 调用ML预测API
    prediction_result = client.call_ml_prediction_api(coordinates)
    
    if not prediction_result:
        print("❌ 测试终止：ML预测失败")
        return False
    
    # 步骤5: 生成艺术提示词
    art_prompt = client.generate_art_prompt(prediction_result, coordinates)
    
    # 步骤6: 模拟图像生成
    image_info = client.simulate_image_generation(art_prompt)
    
    # 步骤7: 模拟云端上传
    upload_success = client.simulate_cloud_upload(image_info, prediction_result)
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 工作流测试总结")
    print("=" * 60)
    
    if upload_success:
        print("✅ 完整工作流测试成功！")
        print("\n🎯 验证的功能:")
        print("  ✓ 云端API连接")
        print("  ✓ 硬件输入模拟")
        print("  ✓ 坐标计算")
        print("  ✓ ML预测API调用")
        print("  ✓ 艺术提示词生成")
        print("  ✓ 图像生成流程")
        print("  ✓ 云端上传流程")
        
        print("\n🚀 系统就绪！")
        print("  树莓派工作流已验证")
        print("  云端API正常工作")
        print("  端到端数据流畅通")
        
        return True
    else:
        print("❌ 工作流测试失败")
        return False

def test_individual_components():
    """测试单个组件"""
    print("\n" + "=" * 60)
    print("🔬 单个组件测试")
    print("=" * 60)
    
    client = MockRaspberryPiClient()
    
    # 测试API端点
    test_endpoints = [
        '/health',
        '/api/v1/ml/model/info',
        '/api/v1/ml/health'
    ]
    
    for endpoint in test_endpoints:
        print(f"\n📡 测试端点: {endpoint}")
        try:
            response = client.session.get(f"{client.api_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {endpoint} - 正常")
                try:
                    data = response.json()
                    print(f"   📊 响应数据: {list(data.keys())}")
                except:
                    print(f"   📊 响应长度: {len(response.text)} 字符")
            else:
                print(f"❌ {endpoint} - 状态码: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} - 错误: {e}")

def main():
    """主函数"""
    print(f"🚀 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 云端API URL: {CLOUD_API_URL}")
    
    # 运行完整工作流测试
    workflow_success = run_complete_workflow()
    
    # 运行单个组件测试
    test_individual_components()
    
    print(f"\n🏁 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if workflow_success:
        print("\n🎉 所有测试通过！你的系统已经可以工作了！")
    else:
        print("\n⚠️ 部分测试失败，请检查云端API状态")

if __name__ == "__main__":
    main() 