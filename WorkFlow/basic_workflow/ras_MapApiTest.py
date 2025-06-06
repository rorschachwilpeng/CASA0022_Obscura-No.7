#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Maps API 测试脚本 - HyperPixel版本
优化版：保存到当前目录 + 屏幕显示 + 自动检测分辨率
"""

import requests
from PIL import Image, ImageTk
import tkinter as tk
import io
import os

class HyperPixelMapDisplay:
    def __init__(self, api_key):
        self.api_key = api_key
        
        # 获取脚本所在目录
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 自动检测屏幕分辨率
        self.detect_screen_resolution()
        
        # 默认参数
        self.default_location = (51.5074, -0.1278)  # 伦敦
        self.default_zoom = 15
        
    def detect_screen_resolution(self):
        """自动检测屏幕分辨率"""
        try:
            # 创建临时tkinter窗口检测分辨率
            temp_root = tk.Tk()
            temp_root.withdraw()  # 隐藏窗口
            
            self.screen_width = temp_root.winfo_screenwidth()
            self.screen_height = temp_root.winfo_screenheight()
            
            temp_root.destroy()
            
            print(f"🖥️ 检测到屏幕分辨率: {self.screen_width}x{self.screen_height}")
            
        except Exception as e:
            print(f"⚠️ 无法检测屏幕分辨率，使用默认值: {e}")
            # HyperPixel 4" 实际尺寸（基于xrandr结果：480x800）
            self.screen_width = 480   # 修正：宽度
            self.screen_height = 800  # 修正：高度
            print(f"🖥️ 使用默认分辨率: {self.screen_width}x{self.screen_height}")
    
    def test_api_connection(self):
        """测试API连接"""
        print("🔍 测试API连接...")
        
        geocoding_url = f"https://maps.googleapis.com/maps/api/geocode/json?address=London&key={self.api_key}"
        
        try:
            response = requests.get(geocoding_url)
            print(f"Geocoding响应状态: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'OK':
                    print("✅ Geocoding API工作正常")
                    return True
                else:
                    print(f"❌ Geocoding API错误: {data['status']}")
                    return False
            else:
                print(f"❌ Geocoding API HTTP错误: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Geocoding API异常: {e}")
            return False
    
    def get_static_map(self, center, zoom, debug=True):
        """获取静态地图图像"""
        base_url = "https://maps.googleapis.com/maps/api/staticmap"
        
        # 为信息栏预留50像素高度
        map_height = self.screen_height - 50
        
        params = {
            'center': f"{center[0]},{center[1]}",
            'zoom': str(zoom),
            'size': f"{self.screen_width}x{map_height}",
            'maptype': 'roadmap',
            'key': self.api_key
        }
        
        url = base_url + "?" + "&".join([f"{k}={v}" for k, v in params.items()])
        
        if debug:
            print(f"🌐 请求URL: {url}")
            print(f"📍 中心点: {center}")
            print(f"🔍 缩放级别: {zoom}")
            print(f"📏 地图尺寸: {self.screen_width}x{map_height}")
        
        try:
            print("📡 发送请求...")
            response = requests.get(url, timeout=30)
            
            print(f"📊 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ 请求成功!")
                content_type = response.headers.get('content-type', '')
                print(f"📄 内容类型: {content_type}")
                
                if 'image' in content_type:
                    return Image.open(io.BytesIO(response.content))
                else:
                    print("❌ 响应不是图像格式")
                    return None
            else:
                print(f"❌ 请求失败: {response.status_code}")
                print(f"错误内容: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return None
    
    def save_map_image(self, map_image, filename="map_test.png"):
        """保存地图图像到脚本同一目录"""
        save_path = os.path.join(self.script_dir, filename)
        
        try:
            map_image.save(save_path)
            print(f"💾 图像已保存到: {save_path}")
            return save_path
        except Exception as e:
            print(f"❌ 保存图像失败: {e}")
            return None
    
    def display_on_hyperpixel(self, map_image):
        """在HyperPixel上全屏显示地图"""
        try:
            # 创建全屏tkinter窗口
            root = tk.Tk()
            root.title("Google Maps - HyperPixel")
            root.configure(bg='black')
            
            # 全屏显示
            root.attributes('-fullscreen', True)
            root.geometry(f"{self.screen_width}x{self.screen_height}")
            
            # ESC键退出
            root.bind('<Escape>', lambda e: root.quit())
            
            # 转换图像为tkinter格式
            photo = ImageTk.PhotoImage(map_image)
            
            # 创建地图显示区域
            map_label = tk.Label(root, image=photo, bg='black')
            map_label.pack(expand=True)
            
            # 创建信息显示区域
            info_frame = tk.Frame(root, bg='black', height=50)
            info_frame.pack(side='bottom', fill='x')
            
            info_text = f"位置: {self.default_location[0]:.4f}, {self.default_location[1]:.4f} | 缩放: {self.default_zoom} | 按ESC退出"
            info_label = tk.Label(
                info_frame,
                text=info_text,
                fg='white',
                bg='black',
                font=('Arial', 10)
            )
            info_label.pack(pady=5)
            
            print("🖥️ 地图正在HyperPixel上显示，按ESC键退出...")
            
            # 显示窗口
            root.mainloop()
            
            return True
            
        except Exception as e:
            print(f"❌ 显示失败: {e}")
            return False
    
    def complete_test(self):
        """完整测试：API + 保存 + 显示"""
        print("=" * 50)
        print("Google Maps HyperPixel 完整测试")
        print("=" * 50)
        
        # 1. 测试API连接
        if not self.test_api_connection():
            print("⚠️ API连接测试失败，但继续尝试Static Map...")
        
        print("\n" + "=" * 50)
        print("获取并显示地图")
        print("=" * 50)
        
        # 2. 获取地图
        map_image = self.get_static_map(self.default_location, self.default_zoom)
        
        if map_image:
            print("🎉 地图获取成功!")
            print(f"图像尺寸: {map_image.size}")
            
            # 3. 保存到当前目录
            self.save_map_image(map_image, "hyperpixel_map.png")
            
            # 4. 在HyperPixel上显示
            self.display_on_hyperpixel(map_image)
            
            return True
        else:
            print("❌ 地图获取失败")
            return False

def main():
    API_KEY = "AIzaSyClOdMUhS3lWQqycXGkU2cT9FNdnRuyjro"
    
    print("🚀 启动HyperPixel地图测试...")
    
    # 创建显示器实例
    display = HyperPixelMapDisplay(API_KEY)
    
    # 运行完整测试
    display.complete_test()

if __name__ == "__main__":
    main()
