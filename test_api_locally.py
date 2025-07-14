#!/usr/bin/env python3
"""
快速API测试脚本 - 模拟树莓派上传请求
避免每次都要部署等5分钟来测试
"""

import requests
import json
from datetime import datetime
import tempfile
import os
from PIL import Image

def create_test_image():
    """创建一个测试图片文件"""
    # 创建一个简单的测试图片
    img = Image.new('RGB', (400, 300), color='blue')
    
    # 保存到临时文件
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    img.save(temp_file.name, 'PNG')
    temp_file.close()
    
    return temp_file.name

def test_health_api(base_url="https://casa0022-obscura-no-7.onrender.com"):
    """测试健康检查API"""
    print("🏥 测试健康检查API...")
    
    try:
        url = f"{base_url}/health"
        
        print(f"📤 向 {url} 发送请求...")
        response = requests.get(url, timeout=10)
        
        print(f"📊 状态码: {response.status_code}")
        print(f"📄 响应内容:")
        
        try:
            response_json = response.json()
            print(json.dumps(response_json, indent=2, ensure_ascii=False))
        except:
            print(response.text)
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_ml_predict_api(base_url="https://casa0022-obscura-no-7.onrender.com"):
    """测试ML预测API"""
    print("\n🔮 测试ML预测API...")
    
    url = f"{base_url}/api/v1/ml/predict"
    
    payload = {
        "latitude": 51.5074,
        "longitude": -0.1278,
        "temperature": 20.0,
        "humidity": 65,
        "pressure": 1013,
        "wind_speed": 5.0,
        "weather_description": "partly cloudy",
        "location_name": "London Test",
        "hours_ahead": 24
    }
    
    try:
        print(f"📤 向 {url} 发送请求...")
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"📊 状态码: {response.status_code}")
        print(f"📄 响应内容:")
        
        try:
            response_json = response.json()
            print(json.dumps(response_json, indent=2, ensure_ascii=False))
        except:
            print(response.text)
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_image_upload_api(base_url="https://casa0022-obscura-no-7.onrender.com"):
    """测试图片上传API"""
    print("\n🧪 测试图片上传API...")
    
    # 创建测试图片
    test_image_path = create_test_image()
    
    try:
        url = f"{base_url}/api/v1/images"
        
        # 准备上传数据
        with open(test_image_path, 'rb') as img_file:
            files = {'file': img_file}
            data = {
                'description': 'Test image from API testing script',
                'prediction_id': '1'
            }
            
            print(f"📤 向 {url} 发送请求...")
            response = requests.post(url, files=files, data=data, timeout=30)
            
            print(f"📊 状态码: {response.status_code}")
            print(f"📄 响应内容:")
            
            try:
                response_json = response.json()
                print(json.dumps(response_json, indent=2, ensure_ascii=False))
            except:
                print(response.text)
                
            return response.status_code == 201
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    finally:
        # 清理临时文件
        if os.path.exists(test_image_path):
            os.unlink(test_image_path)

def test_register_image_api(base_url="https://casa0022-obscura-no-7.onrender.com"):
    """测试注册图片API"""
    print("\n🧪 测试图片注册API...")
    
    url = f"{base_url}/api/v1/images/register"
    
    payload = {
        "url": "https://res.cloudinary.com/dvbqtwgko/image/upload/v1752430768/telescope/test_image.png",
        "description": "Test image registration",
        "source": "api_test",
        "metadata": {
            "style": {
                "prediction_id": 1
            }
        }
    }
    
    try:
        print(f"📤 向 {url} 发送请求...")
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"📊 状态码: {response.status_code}")
        print(f"📄 响应内容:")
        
        try:
            response_json = response.json()
            print(json.dumps(response_json, indent=2, ensure_ascii=False))
        except:
            print(response.text)
            
        return response.status_code == 201
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_gallery_api(base_url="https://casa0022-obscura-no-7.onrender.com"):
    """测试Gallery API"""
    print("\n🖼️ 测试Gallery API...")
    
    url = f"{base_url}/api/v1/images"
    
    try:
        print(f"📤 向 {url} 发送请求...")
        response = requests.get(url, timeout=10)
        
        print(f"📊 状态码: {response.status_code}")
        print(f"📄 响应内容:")
        
        try:
            response_json = response.json()
            print(json.dumps(response_json, indent=2, ensure_ascii=False))
        except:
            print(response.text)
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🔧 API快速测试工具")
    print("=" * 50)
    
    # 默认使用生产环境URL
    base_url = "https://casa0022-obscura-no-7.onrender.com"
    
    print(f"🎯 测试目标: {base_url}")
    print()
    
    # 测试1: 健康检查
    health_success = test_health_api(base_url)
    
    # 测试2: ML预测
    ml_success = test_ml_predict_api(base_url)
    
    # 测试3: Gallery API
    gallery_success = test_gallery_api(base_url)
    
    # 测试4: 图片上传
    upload_success = test_image_upload_api(base_url)
    
    # 测试5: 图片注册  
    register_success = test_register_image_api(base_url)
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print(f"  健康检查API: {'✅ 成功' if health_success else '❌ 失败'}")
    print(f"  ML预测API: {'✅ 成功' if ml_success else '❌ 失败'}")
    print(f"  Gallery API: {'✅ 成功' if gallery_success else '❌ 失败'}")
    print(f"  图片上传API: {'✅ 成功' if upload_success else '❌ 失败'}")
    print(f"  图片注册API: {'✅ 成功' if register_success else '❌ 失败'}")
    
    success_count = sum([health_success, ml_success, gallery_success, upload_success, register_success])
    total_count = 5
    
    if success_count == total_count:
        print(f"\n🎉 所有测试通过！({success_count}/{total_count}) 系统运行正常。")
    else:
        print(f"\n⚠️ {total_count - success_count} 个测试失败。({success_count}/{total_count})")

if __name__ == "__main__":
    main() 