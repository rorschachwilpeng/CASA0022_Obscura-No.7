#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Maps API 基础测试脚本
先在笔记本上运行验证
"""

import googlemaps
import requests
from PIL import Image
import tkinter as tk
from tkinter import ttk
import io

class GoogleMapsTest:
    def __init__(self, api_key):
        self.api_key = api_key
        self.gmaps = googlemaps.Client(key=api_key)
        
        # 默认参数
        self.default_location = (51.5074, -0.1278)  # 伦敦
        self.default_zoom = 15
        self.map_size = (800, 480)  # HyperPixel尺寸
        
    def test_api_connection(self):
        """测试API连接"""
        try:
            # 测试地理编码
            result = self.gmaps.geocode('London')
            print("✅ API连接成功!")
            print(f"测试结果: {result[0]['formatted_address']}")
            return True
        except Exception as e:
            print(f"❌ API连接失败: {e}")
            return False
    
    def get_static_map(self, center, zoom, size=(800, 480)):
        """获取静态地图图像"""
        base_url = "https://maps.googleapis.com/maps/api/staticmap?"
        
        params = {
            'center': f"{center[0]},{center[1]}",
            'zoom': zoom,
            'size': f"{size[0]}x{size[1]}",
            'maptype': 'roadmap',
            'key': self.api_key
        }
        
        # 构建URL
        url = base_url + "&".join([f"{k}={v}" for k, v in params.items()])
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return Image.open(io.BytesIO(response.content))
            else:
                print(f"地图获取失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"地图获取错误: {e}")
            return None
    
    def display_map_tkinter(self, center, zoom):
        """在tkinter窗口中显示地图"""
        map_image = self.get_static_map(center, zoom, self.map_size)
        
        if map_image:
            # 创建tkinter窗口
            root = tk.Tk()
            root.title("Google Maps 测试 - HyperPixel模拟")
            root.geometry("820x520")
            
            # 转换图像供tkinter使用
            from PIL import ImageTk
            photo = ImageTk.PhotoImage(map_image)
            
            # 显示图像
            label = tk.Label(root, image=photo)
            label.pack(padx=10, pady=10)
            
            # 添加信息显示
            info_frame = tk.Frame(root)
            info_frame.pack(pady=5)
            
            tk.Label(info_frame, text=f"位置: {center}").pack()
            tk.Label(info_frame, text=f"缩放: {zoom}").pack()
            
            root.mainloop()
        else:
            print("无法显示地图")

def main():
    # TODO: 替换为你的API Key
    API_KEY = "AIzaSyClOdMUhS3lWQqycXGkU2cT9FNdnRuyjro"
    
    # 创建测试实例
    map_test = GoogleMapsTest(API_KEY)
    
    # 测试API连接
    if map_test.test_api_connection():
        # 显示默认地图
        print("显示默认地图...")
        map_test.display_map_tkinter(map_test.default_location, map_test.default_zoom)
    else:
        print("请检查API Key是否正确设置")

if __name__ == "__main__":
    main()