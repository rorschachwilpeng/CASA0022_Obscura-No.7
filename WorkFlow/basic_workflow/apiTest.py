#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Maps API 测试脚本 - 简化版
"""

import requests
from PIL import Image
import io

def test_static_map_api(api_key):
    """直接测试Static Maps API"""
    
    # 构建静态地图URL
    base_url = "https://maps.googleapis.com/maps/api/staticmap"
    params = {
        'center': '51.5074,-0.1278',  # 伦敦
        'zoom': '15',
        'size': '800x480',
        'maptype': 'roadmap',
        'key': api_key
    }
    
    # 构建完整URL
    url = f"{base_url}?" + "&".join([f"{k}={v}" for k, v in params.items()])
    print(f"请求URL: {url}")
    
    try:
        response = requests.get(url)
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            # 保存图像
            image = Image.open(io.BytesIO(response.content))
            image.save("test_map.png")
            print("✅ 地图获取成功! 已保存为 test_map.png")
            
            # 在macOS上打开图片
            import os
            os.system("open test_map.png")
            
            return True
        else:
            print(f"❌ 请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求错误: {e}")
        return False

def main():
    API_KEY = "AIzaSyClOdMUhS3lWQqycXGkU2cT9FNdnRuyjro"
    
    print("测试Google Maps Static API...")
    test_static_map_api(API_KEY)

if __name__ == "__main__":
    main()