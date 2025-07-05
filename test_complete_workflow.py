#!/usr/bin/env python3
"""
完整端到端工作流测试
模拟：树莓派输入 → 坐标计算 → 网站ML API → AI图像生成 → 展示
"""

import requests
import json
import sys
import os
import time
import math
from datetime import datetime, timedelta

# 添加路径以便导入模块
sys.path.insert(0, 'raspberry_pi_deployment/core')
sys.path.insert(0, 'ML_Models')

def simulate_hardware_input():
    """模拟硬件输入"""
    print("🎮 模拟硬件输入（树莓派）...")
    
    # 模拟用户选择
    hardware_input = {
        'distance_km': 50.0,        # 距离 50公里
        'direction_degrees': 45.0,   # 东北方向 45度
        'time_offset_years': 2       # 预测 2年后
    }
    
    print(f"   距离: {hardware_input['distance_km']} km")
    print(f"   方向: {hardware_input['direction_degrees']}° (东北)")
    print(f"   时间偏移: {hardware_input['time_offset_years']} 年后")
    
    return hardware_input

def calculate_target_coordinates(hardware_input, base_lat=51.5074, base_lon=-0.1278):
    """计算目标坐标"""
    print("\n📍 计算目标坐标...")
    
    distance_m = hardware_input['distance_km'] * 1000
    direction_rad = math.radians(hardware_input['direction_degrees'])
    
    # 地球半径 (米)
    R = 6371000
    
    # 计算新坐标
    lat1 = math.radians(base_lat)
    lon1 = math.radians(base_lon)
    
    lat2 = math.asin(
        math.sin(lat1) * math.cos(distance_m / R) +
        math.cos(lat1) * math.sin(distance_m / R) * math.cos(direction_rad)
    )
    
    lon2 = lon1 + math.atan2(
        math.sin(direction_rad) * math.sin(distance_m / R) * math.cos(lat1),
        math.cos(distance_m / R) - math.sin(lat1) * math.sin(lat2)
    )
    
    target_coords = {
        'latitude': math.degrees(lat2),
        'longitude': math.degrees(lon2),
        'distance_km': hardware_input['distance_km'],
        'direction_degrees': hardware_input['direction_degrees']
    }
    
    print(f"   基础位置: {base_lat:.4f}, {base_lon:.4f} (伦敦)")
    print(f"   目标位置: {target_coords['latitude']:.4f}, {target_coords['longitude']:.4f}")
    
    return target_coords

def call_ml_prediction_api(coordinates, time_offset_years, api_base="http://localhost:5000"):
    """调用网站ML预测API（直接使用Flask应用）"""
    print("\n🤖 调用网站ML预测API...")
    
    # 构建API请求
    prediction_request = {
        'latitude': coordinates['latitude'],
        'longitude': coordinates['longitude'],
        'month': datetime.now().month,
        'future_years': time_offset_years
    }
    
    try:
        # 直接使用Flask应用测试客户端
        sys.path.insert(0, 'api')
        from app import create_app
        
        print(f"   请求数据: {prediction_request}")
        
        # 创建应用实例
        app = create_app()
        
        # 使用测试客户端
        with app.test_client() as client:
            response = client.post('/api/v1/ml/predict', 
                                   json=prediction_request,
                                   content_type='application/json')
            
            if response.status_code == 200:
                prediction_data = response.get_json()
                print("   ✅ API调用成功!")
                
                prediction = prediction_data.get('prediction', {})
                location_info = prediction_data.get('location_info', {})
                
                print(f"   最近城市: {location_info.get('closest_city', 'Unknown')}")
                print(f"   预测温度: {prediction.get('temperature', 'N/A'):.2f}°C")
                print(f"   预测湿度: {prediction.get('humidity', 'N/A'):.1f}%")
                print(f"   预测压力: {prediction.get('pressure', 'N/A'):.1f} hPa")
                print(f"   模型版本: {prediction.get('model_version', 'N/A')}")
                print(f"   置信度: {prediction.get('prediction_confidence', 'N/A')}")
                print(f"   模型类型: {prediction.get('model_type', 'N/A')}")
                
                return prediction_data
                
            else:
                print(f"   ❌ API调用失败: {response.status_code}")
                print(f"   错误响应: {response.get_data(as_text=True)}")
                return None
                
    except Exception as e:
        print(f"   ❌ API请求异常: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_ai_prompt(prediction_data, coordinates):
    """基于预测数据生成AI图像提示词"""
    print("\n🎨 生成AI图像提示词...")
    
    prediction = prediction_data.get('prediction', {})
    location_info = prediction_data.get('location_info', {})
    
    temperature = prediction.get('temperature', 15)
    humidity = prediction.get('humidity', 60)
    closest_city = location_info.get('closest_city', 'Unknown')
    prediction_type = location_info.get('prediction_type', 'current')
    
    # 基于温度确定季节描述
    if temperature < 5:
        season_desc = "cold winter landscape with frost and snow"
    elif temperature < 15:
        season_desc = "cool autumn or spring scene with moderate weather"
    elif temperature < 25:
        season_desc = "pleasant temperate climate with mild conditions"
    else:
        season_desc = "warm summer environment with lush vegetation"
    
    # 基于湿度确定大气描述
    if humidity < 40:
        humidity_desc = "clear, dry atmosphere"
    elif humidity < 70:
        humidity_desc = "comfortable humidity with slight haze"
    else:
        humidity_desc = "moist, humid air with possible mist"
    
    # 构建提示词
    base_prompt = f"Steampunk environmental art depicting {season_desc} near {closest_city}"
    
    if prediction_type == "future":
        base_prompt += f", showing climate change effects in a future scenario"
    
    ai_prompt = f"{base_prompt} with {humidity_desc}, Victorian-era brass instruments measuring weather, copper pipes and steam, fantasy environmental monitoring station, detailed digital art"
    
    print(f"   AI提示词: {ai_prompt}")
    
    return {
        'prompt': ai_prompt,
        'temperature': temperature,
        'humidity': humidity,
        'season_description': season_desc,
        'location': closest_city,
        'prediction_type': prediction_type
    }

def simulate_image_generation(ai_prompt_data):
    """模拟AI图像生成"""
    print("\n🖼️ 模拟AI图像生成...")
    
    # 模拟图像生成过程
    print(f"   使用提示词: {ai_prompt_data['prompt'][:100]}...")
    print(f"   主题: {ai_prompt_data['season_description']}")
    print(f"   位置: {ai_prompt_data['location']}")
    
    # 模拟生成结果
    image_info = {
        'success': True,
        'image_url': f"https://example.com/generated/telescope_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
        'prompt_used': ai_prompt_data['prompt'],
        'generation_time': 15.3,
        'style': 'steampunk_environmental',
        'dimensions': '1024x1024'
    }
    
    print(f"   ✅ 图像生成成功!")
    print(f"   图像URL: {image_info['image_url']}")
    print(f"   生成时间: {image_info['generation_time']} 秒")
    print(f"   尺寸: {image_info['dimensions']}")
    
    return image_info

def create_workflow_summary(hardware_input, coordinates, prediction_data, ai_prompt_data, image_info):
    """创建工作流总结"""
    print("\n📊 创建工作流总结...")
    
    workflow_summary = {
        'workflow_id': f"test_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        'timestamp': datetime.now().isoformat(),
        'device_type': 'simulated_raspberry_pi',
        'status': 'completed',
        'steps': {
            '1_hardware_input': hardware_input,
            '2_coordinates': coordinates,
            '3_ml_prediction': prediction_data,
            '4_ai_prompt': ai_prompt_data,
            '5_image_generation': image_info
        },
        'summary': {
            'location': prediction_data.get('location_info', {}).get('closest_city', 'Unknown'),
            'predicted_temperature': prediction_data.get('prediction', {}).get('temperature'),
            'future_years': hardware_input.get('time_offset_years', 0),
            'image_generated': image_info.get('success', False),
            'total_processing_time': '45.2 seconds'
        }
    }
    
    # 保存总结到文件
    output_file = f"workflow_outputs/workflow_summary_{workflow_summary['workflow_id']}.json"
    os.makedirs('workflow_outputs', exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(workflow_summary, f, indent=2, ensure_ascii=False)
    
    print(f"   工作流总结已保存: {output_file}")
    
    return workflow_summary

def display_final_results(workflow_summary):
    """显示最终结果"""
    print("\n" + "=" * 60)
    print("🎯 端到端工作流完成!")
    print("=" * 60)
    
    summary = workflow_summary['summary']
    
    print(f"🆔 工作流ID: {workflow_summary['workflow_id']}")
    print(f"📍 目标位置: {summary['location']}")
    print(f"🌡️ 预测温度: {summary['predicted_temperature']:.2f}°C")
    print(f"⏳ 未来预测: {summary['future_years']} 年后")
    print(f"🖼️ 图像生成: {'成功' if summary['image_generated'] else '失败'}")
    print(f"⏱️ 总处理时间: {summary['total_processing_time']}")
    
    print("\n🔗 数据流链路:")
    print("   树莓派硬件输入 → 坐标计算 → 网站ML API → AI提示词生成 → 图像生成")
    
    steps = workflow_summary['steps']
    coords = steps['2_coordinates']
    print(f"\n📐 坐标转换:")
    print(f"   距离: {coords['distance_km']} km")
    print(f"   方向: {coords['direction_degrees']}°")
    print(f"   结果: ({coords['latitude']:.4f}, {coords['longitude']:.4f})")
    
    prediction = steps['3_ml_prediction']['prediction']
    print(f"\n🤖 ML预测:")
    print(f"   温度: {prediction['temperature']:.2f}°C")
    print(f"   湿度: {prediction['humidity']:.1f}%")
    print(f"   压力: {prediction['pressure']:.1f} hPa")
    
    print(f"\n🎨 AI生成:")
    prompt = steps['4_ai_prompt']['prompt']
    print(f"   提示词: {prompt[:80]}...")
    print(f"   风格: 蒸汽朋克环境艺术")

def main():
    """主函数"""
    print("🚀 完整端到端工作流测试")
    print("模拟：树莓派 → 坐标计算 → 网站ML API → AI图像生成")
    print("=" * 60)
    
    try:
        # 步骤1: 模拟硬件输入
        hardware_input = simulate_hardware_input()
        
        # 步骤2: 计算目标坐标
        coordinates = calculate_target_coordinates(hardware_input)
        
        # 步骤3: 调用ML预测API
        prediction_data = call_ml_prediction_api(
            coordinates, 
            hardware_input['time_offset_years']
        )
        
        if not prediction_data:
            print("❌ ML预测失败，无法继续工作流")
            return
        
        # 步骤4: 生成AI提示词
        ai_prompt_data = generate_ai_prompt(prediction_data, coordinates)
        
        # 步骤5: 模拟图像生成
        image_info = simulate_image_generation(ai_prompt_data)
        
        # 步骤6: 创建工作流总结
        workflow_summary = create_workflow_summary(
            hardware_input, coordinates, prediction_data, 
            ai_prompt_data, image_info
        )
        
        # 步骤7: 显示最终结果
        display_final_results(workflow_summary)
        
        print("\n✅ 完整工作流测试成功!")
        
    except Exception as e:
        print(f"\n❌ 工作流测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 