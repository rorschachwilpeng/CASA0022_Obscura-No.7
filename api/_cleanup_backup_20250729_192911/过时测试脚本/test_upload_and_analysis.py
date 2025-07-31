#!/usr/bin/env python3
"""
测试图片上传和分析功能
"""

import requests
import json
import time
import os

# 服务器配置
SERVER_URL = "http://localhost:52778"
API_BASE = f"{SERVER_URL}/api/v1"

def test_image_upload():
    """测试图片上传功能"""
    print("🔄 Testing image upload...")
    
    # 创建一个测试图片（这里使用现有的图片文件）
    test_image_path = "test_image.png"
    
    # 如果没有测试图片，创建一个简单的测试文件
    if not os.path.exists(test_image_path):
        # 创建一个简单的测试文件
        with open(test_image_path, 'wb') as f:
            # 写入一些测试数据
            f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82')
    
    # 上传图片
    with open(test_image_path, 'rb') as f:
        files = {'file': ('test_image.png', f, 'image/png')}
        data = {
            'description': 'Test Environmental Vision',
            'prediction_id': '1'
        }
        
        response = requests.post(f"{API_BASE}/images", files=files, data=data)
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Image uploaded successfully: {result['image']['id']}")
            return result['image']['id']
        else:
            print(f"❌ Image upload failed: {response.status_code}")
            print(f"Error: {response.text}")
            return None

def test_image_detail(image_id):
    """测试图片详情获取"""
    print(f"🔄 Testing image detail for ID: {image_id}")
    
    response = requests.get(f"{API_BASE}/images/{image_id}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Image detail retrieved successfully")
        print(f"   Description: {result['image']['description']}")
        print(f"   URL: {result['image']['url']}")
        return True
    else:
        print(f"❌ Image detail failed: {response.status_code}")
        print(f"Error: {response.text}")
        return False

def test_shap_analysis(image_id):
    """测试SHAP分析"""
    print(f"🔄 Testing SHAP analysis for ID: {image_id}")
    
    # 等待一段时间让后台分析完成
    print("⏳ Waiting for background analysis to complete...")
    time.sleep(3)
    
    response = requests.get(f"{API_BASE}/images/{image_id}/shap-analysis")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ SHAP analysis retrieved successfully")
        print(f"   Mode: {result.get('mode', 'unknown')}")
        print(f"   Climate Score: {result['data']['climate_score']}")
        print(f"   Geographic Score: {result['data']['geographic_score']}")
        print(f"   Economic Score: {result['data']['economic_score']}")
        print(f"   Overall Score: {result['data']['output_score']}")
        
        # 检查是否有AI故事
        if 'ai_story' in result['data']:
            story = result['data']['ai_story']
            print(f"   AI Story Length: {len(story.get('story', ''))}")
            print(f"   Story Source: {story.get('source', 'unknown')}")
        
        return True
    else:
        print(f"❌ SHAP analysis failed: {response.status_code}")
        print(f"Error: {response.text}")
        return False

def test_server_health():
    """测试服务器健康状态"""
    print("🔄 Testing server health...")
    
    try:
        response = requests.get(f"{SERVER_URL}/health")
        if response.status_code == 200:
            print("✅ Server is healthy")
            return True
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server")
        return False

def main():
    """主测试函数"""
    print("🚀 Starting image upload and analysis test...")
    print("=" * 50)
    
    # 测试服务器健康状态
    if not test_server_health():
        print("❌ Server is not accessible, exiting...")
        return
    
    # 测试图片上传
    image_id = test_image_upload()
    if not image_id:
        print("❌ Image upload failed, exiting...")
        return
    
    print()
    
    # 测试图片详情
    if not test_image_detail(image_id):
        print("❌ Image detail test failed")
        return
    
    print()
    
    # 测试SHAP分析
    if not test_shap_analysis(image_id):
        print("❌ SHAP analysis test failed")
        return
    
    print()
    print("🎉 All tests passed successfully!")
    print("=" * 50)

if __name__ == "__main__":
    main() 