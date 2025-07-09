#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网站前端测试脚本
测试网站的前端页面和可视化功能
"""

import requests
import webbrowser
import time
from datetime import datetime

# 云端API URL
API_URL = 'https://casa0022-obscura-no-7.onrender.com'

def test_website_pages():
    """测试网站页面"""
    print("🌐 网站前端测试")
    print("=" * 40)
    
    # 要测试的页面
    pages = [
        {'name': '主页', 'url': '/'},
        {'name': '预测页面', 'url': '/prediction'},
        {'name': '图库', 'url': '/gallery'},
        {'name': '关于页面', 'url': '/about'},
        {'name': '健康检查', 'url': '/health'}
    ]
    
    print(f"🌐 测试网站: {API_URL}")
    
    for page in pages:
        print(f"\n📄 测试 {page['name']}...")
        
        try:
            response = requests.get(f"{API_URL}{page['url']}", timeout=10)
            if response.status_code == 200:
                print(f"   ✅ 页面正常 (大小: {len(response.content)} bytes)")
                
                # 检查页面内容
                content = response.text.lower()
                if 'obscura no.7' in content or 'obscura' in content:
                    print("   ✅ 包含项目标识")
                else:
                    print("   ⚠️ 可能缺少项目标识")
                    
            else:
                print(f"   ❌ 页面异常: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 请求失败: {e}")

def test_api_endpoints():
    """测试API端点"""
    print("\n🔌 API端点测试")
    print("=" * 40)
    
    # API端点
    endpoints = [
        {'name': 'ML预测', 'url': '/api/v1/ml/predict', 'method': 'POST'},
        {'name': 'ML健康', 'url': '/api/v1/ml/health', 'method': 'GET'},
        {'name': '模型信息', 'url': '/api/v1/ml/model/info', 'method': 'GET'},
        {'name': '系统状态', 'url': '/api/status', 'method': 'GET'}
    ]
    
    for endpoint in endpoints:
        print(f"\n🔗 测试 {endpoint['name']}...")
        
        try:
            if endpoint['method'] == 'GET':
                response = requests.get(f"{API_URL}{endpoint['url']}", timeout=10)
            else:
                # POST请求，发送测试数据
                test_data = {
                    'latitude': 51.5074,
                    'longitude': -0.1278,
                    'month': datetime.now().month,
                    'future_years': 0
                }
                response = requests.post(
                    f"{API_URL}{endpoint['url']}", 
                    json=test_data, 
                    timeout=30
                )
            
            if response.status_code == 200:
                print(f"   ✅ API正常")
                try:
                    data = response.json()
                    print(f"   📊 响应字段: {list(data.keys())}")
                except:
                    print(f"   📊 响应长度: {len(response.text)} 字符")
            else:
                print(f"   ❌ API异常: {response.status_code}")
                print(f"   错误: {response.text[:200]}...")
                
        except Exception as e:
            print(f"   ❌ 请求失败: {e}")

def open_website_in_browser():
    """在浏览器中打开网站"""
    print("\n🌐 在浏览器中打开网站...")
    
    urls_to_open = [
        f"{API_URL}/",
        f"{API_URL}/prediction"
    ]
    
    for url in urls_to_open:
        print(f"🔗 打开: {url}")
        try:
            webbrowser.open(url)
            time.sleep(1)  # 稍等一下再打开下一个
        except Exception as e:
            print(f"   ❌ 打开失败: {e}")

def interactive_test():
    """交互式测试"""
    print("\n🎮 交互式测试")
    print("=" * 40)
    
    print("你可以手动测试以下功能:")
    print(f"1. 主页: {API_URL}/")
    print(f"2. 预测页面: {API_URL}/prediction")
    print(f"3. 图库: {API_URL}/gallery")
    print(f"4. 关于页面: {API_URL}/about")
    
    print("\n在预测页面，尝试输入以下测试数据:")
    print("📍 伦敦: 纬度 51.5074, 经度 -0.1278")
    print("📍 曼彻斯特: 纬度 53.4808, 经度 -2.2426")
    print("📍 爱丁堡: 纬度 55.9533, 经度 -3.1883")
    
    print("\n检查点:")
    print("✓ 页面是否正常加载")
    print("✓ 蒸汽朋克风格是否正确显示")
    print("✓ 预测表单是否可以提交")
    print("✓ 预测结果是否正确显示")
    print("✓ 加载动画是否正常")
    print("✓ 响应式设计是否在不同屏幕尺寸下正常工作")

def main():
    """主函数"""
    print(f"🚀 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 测试网站: {API_URL}")
    
    # 1. 测试网站页面
    test_website_pages()
    
    # 2. 测试API端点
    test_api_endpoints()
    
    # 3. 在浏览器中打开网站
    print("\n" + "=" * 60)
    response = input("是否要在浏览器中打开网站进行手动测试? (y/n): ")
    if response.lower() == 'y':
        open_website_in_browser()
        interactive_test()
    
    print(f"\n🏁 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n🎉 前端测试完成！")

if __name__ == "__main__":
    main() 