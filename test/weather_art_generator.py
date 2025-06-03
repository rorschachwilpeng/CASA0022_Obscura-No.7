#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
天气艺术生成器
从OpenWeather API获取当前天气数据，然后使用OpenAI DALL-E生成对应的艺术图像
"""

import os
import requests
import json
import time
from datetime import datetime
import argparse
from PIL import Image, ImageTk
import io
import tkinter as tk
from tkinter import Label
import subprocess
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# API密钥（从环境变量中获取）
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 默认位置
DEFAULT_CITY = "London"

def get_weather_data(city=DEFAULT_CITY):
    """
    从OpenWeather API获取天气数据
    
    Args:
        city (str): 城市名称
    
    Returns:
        dict: 天气数据
    """
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        response = requests.get(url)
        response.raise_for_status()  # 检查请求是否成功
        
        weather_data = response.json()
        
        # 提取并构建有用的天气信息
        processed_data = {
            "city": city,
            "temperature": weather_data["main"]["temp"],
            "feels_like": weather_data["main"]["feels_like"],
            "humidity": weather_data["main"]["humidity"],
            "weather_condition": weather_data["weather"][0]["main"],
            "weather_description": weather_data["weather"][0]["description"],
            "wind_speed": weather_data["wind"]["speed"],
            "clouds": weather_data.get("clouds", {}).get("all", 0),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return processed_data
    except Exception as e:
        print(f"获取天气数据时出错: {e}")
        return None

def generate_prompt(weather_data):
    """
    根据天气数据生成一个适合AI图像生成的提示
    
    Args:
        weather_data (dict): 天气数据
    
    Returns:
        str: 生成的提示
    """
    if not weather_data:
        return "一幅美丽的风景画，天气晴朗"
    
    # 根据天气状况创建情感和艺术风格元素
    condition = weather_data["weather_condition"].lower()
    description = weather_data["weather_description"].lower()
    temp = weather_data["temperature"]
    time_of_day = "早晨" if 5 <= datetime.now().hour < 12 else "下午" if 12 <= datetime.now().hour < 18 else "夜晚"
    city = weather_data["city"]
    
    # 根据不同的天气状况设置不同的风格和氛围
    style_mapping = {
        "clear": "明亮，充满活力，阳光普照的风景，明快的色彩，清晰的轮廓",
        "clouds": "柔和的色调，轻盈的云层，梦幻般的天空，温暖的光线穿过云层",
        "rain": "湿润的城市场景，雨滴反射的灯光，深沉的蓝色和灰色调，安静的氛围",
        "drizzle": "轻柔的雨雾，朦胧的景观，柔和的色彩过渡，微妙的光影效果",
        "thunderstorm": "戏剧性的暴风雨场景，强烈的对比，深色云层，闪电照亮的天sky",
        "snow": "冬季仙境，柔和的白色和蓝色，宁静的雪景，温暖的灯光透过雪花",
        "mist": "神秘的雾气环绕，朦胧的轮廓，柔和的光线，梦幻而宁静的场景",
        "fog": "厚重的雾气，隐约可见的建筑轮廓，沉静的氛围，有限的可见度"
    }
    
    # 选择最匹配的风格
    chosen_style = None
    for key in style_mapping:
        if key in condition or key in description:
            chosen_style = style_mapping[key]
            break
    
    # 如果没有找到匹配的风格，使用默认风格
    if not chosen_style:
        chosen_style = style_mapping["clear"]
    
    # 根据温度添加额外元素
    temp_element = ""
    if temp < 5:
        temp_element = "寒冷的氛围，冰冻的景象，冬季色调"
    elif temp < 15:
        temp_element = "凉爽的氛围，舒适的秋色，温和的光线"
    elif temp < 25:
        temp_element = "温暖舒适的氛围，生机勃勃的色彩，明媚的阳光"
    else:
        temp_element = "炎热的夏日氛围，强烈的阳光，充满活力的场景"
    
    # 构建最终的提示
    prompt = f"创建一幅精美的数字艺术作品，展现{city}在{time_of_day}的{description}天气。{chosen_style}，{temp_element}。温度是{temp}°C。艺术风格细腻，高质量，有吸引力的构图，8K分辨率。"
    
    return prompt

def generate_image(prompt):
    """
    使用OpenAI的API根据提供的提示生成一个图像
    
    Args:
        prompt (str): 用于生成图像的提示
    
    Returns:
        bytes or None: 图像数据或None（如果生成失败）
    """
    try:
        url = "https://api.openai.com/v1/images/generations"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
            "response_format": "url"  # 获取URL而不是base64编码
        }
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        image_url = result["data"][0]["url"]
        
        # 下载图像
        image_response = requests.get(image_url)
        image_response.raise_for_status()
        
        return image_response.content
    
    except Exception as e:
        print(f"生成图像时出错: {e}")
        if 'response' in locals() and hasattr(response, 'text'):
            print(f"API响应: {response.text}")
        return None

def save_image(image_data, output_path="./output_imgs/weather_art.png"):
    """
    保存图像数据到文件
    
    Args:
        image_data (bytes): 图像二进制数据
        output_path (str): 保存路径
    
    Returns:
        str: 保存的文件路径
    """
    try:
        # 获取当前时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 分离路径和文件名
        output_dir = os.path.dirname(output_path)
        filename = os.path.basename(output_path)
        
        # 从原始文件名中提取基本名称和扩展名
        name_parts = os.path.splitext(filename)
        base_name = name_parts[0]
        extension = name_parts[1] if len(name_parts) > 1 else ".png"
        
        # 创建新的文件名
        new_filename = f"{base_name}_{timestamp}{extension}"
        new_output_path = os.path.join(output_dir, new_filename)
        
        # 确保目录存在
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 保存图像
        image = Image.open(io.BytesIO(image_data))
        image.save(new_output_path)
        print(f"图像已保存到 {new_output_path}")
        return new_output_path
    except Exception as e:
        print(f"保存图像时出错: {e}")
        return None

def get_screen_resolution():
    """
    获取屏幕分辨率
    
    Returns:
        tuple: (width, height) 屏幕分辨率
    """
    try:
        # 尝试使用xrandr获取屏幕分辨率
        result = subprocess.run(['xrandr'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        for line in lines:
            if '*' in line:  # 当前分辨率会有*标记
                resolution = line.split()[0]
                width, height = map(int, resolution.split('x'))
                return width, height
    except:
        pass
    
    # 如果xrandr失败，使用默认的HyperPixel分辨率
    return 800, 480  # HyperPixel 4.0的默认分辨率

def display_image_fullscreen(image_data, duration=10):
    """
    在屏幕上全屏显示图像
    
    Args:
        image_data (bytes): 图像二进制数据
        duration (int): 显示时长（秒）
    """
    try:
        # 创建tkinter窗口
        root = tk.Tk()
        root.title("Weather Art Display")
        
        # 获取屏幕分辨率
        screen_width, screen_height = get_screen_resolution()
        
        # 设置窗口为全屏
        root.geometry(f"{screen_width}x{screen_height}")
        root.configure(bg='black')
        root.attributes('-fullscreen', True)
        
        # 加载图像
        image = Image.open(io.BytesIO(image_data))
        
        # 调整图像大小以适应屏幕，保持宽高比
        image.thumbnail((screen_width, screen_height), Image.Resampling.LANCZOS)
        
        # 转换为tkinter可用的格式
        photo = ImageTk.PhotoImage(image)
        
        # 创建标签显示图像
        label = Label(root, image=photo, bg='black')
        label.pack(expand=True)
        
        # 添加退出功能（按ESC键退出）
        def on_escape(event):
            root.destroy()
        
        root.bind('<Escape>', on_escape)
        root.bind('<Button-1>', on_escape)  # 点击屏幕也可以退出
        
        print(f"图像正在全屏显示，{duration}秒后自动关闭，或按ESC/点击屏幕退出")
        
        # 设置自动关闭
        root.after(duration * 1000, root.destroy)
        
        # 显示窗口
        root.mainloop()
        
    except Exception as e:
        print(f"显示图像时出错: {e}")

def display_image_fbi(image_path):
    """
    使用fbi命令在framebuffer上显示图像（适用于无X11环境）
    
    Args:
        image_path (str): 图像文件路径
    """
    try:
        # 使用fbi命令显示图像
        subprocess.run(['sudo', 'fbi', '-T', '1', '-d', '/dev/fb0', '-a', image_path], 
                      timeout=10)
        print(f"图像已通过fbi显示: {image_path}")
    except subprocess.TimeoutExpired:
        print("fbi显示超时，继续执行")
    except Exception as e:
        print(f"使用fbi显示图像时出错: {e}")

def display_image(image_data, image_path=None, method='auto', duration=10):
    """
    显示生成的图像
    
    Args:
        image_data (bytes): 图像二进制数据
        image_path (str): 图像文件路径
        method (str): 显示方法 ('auto', 'tkinter', 'fbi')
        duration (int): 显示时长（秒）
    """
    if method == 'auto':
        # 检查是否有X11显示
        if os.environ.get('DISPLAY'):
            method = 'tkinter'
        else:
            method = 'fbi'
    
    if method == 'tkinter':
        display_image_fullscreen(image_data, duration)
    elif method == 'fbi' and image_path:
        display_image_fbi(image_path)
    else:
        print("无法确定显示方法或缺少必要参数")

def main():
    """主程序"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="基于天气数据生成艺术图像")
    parser.add_argument("--city", type=str, default=DEFAULT_CITY, help=f"要获取天气数据的城市 (默认: {DEFAULT_CITY})")
    parser.add_argument("--display", action="store_true", help="生成后显示图像")
    parser.add_argument("--display-method", type=str, choices=['auto', 'tkinter', 'fbi'], 
                       default='auto', help="显示方法 (默认: auto)")
    parser.add_argument("--display-duration", type=int, default=10, 
                       help="显示时长（秒，默认: 10）")
    parser.add_argument("--output", type=str, default="weather_art.png", help="输出图像的路径 (默认: weather_art.png)")
    args = parser.parse_args()
    
    # 检查API密钥
    if not OPENWEATHER_API_KEY:
        print("错误: 未设置OPENWEATHER_API_KEY环境变量")
        return
    
    if not OPENAI_API_KEY:
        print("错误: 未设置OPENAI_API_KEY环境变量")
        return
    
    # 获取天气数据
    print(f"正在获取{args.city}的天气数据...")
    weather_data = get_weather_data(args.city)
    
    if not weather_data:
        print("无法获取天气数据，退出程序")
        return
    
    print("天气数据:")
    for key, value in weather_data.items():
        print(f"  {key}: {value}")
    
    # 生成提示
    prompt = generate_prompt(weather_data)
    print(f"\n生成的提示:\n{prompt}")
    
    # 生成图像
    print("\n正在生成图像，这可能需要一些时间...")
    image_data = generate_image(prompt)
    
    if not image_data:
        print("图像生成失败，退出程序")
        return
    
    # 保存图像
    output_path = "./output_imgs/weather_art.png"
    saved_path = save_image(image_data, output_path)
    
    # 如果请求显示，则显示图像
    if args.display and saved_path:
        display_image(image_data, saved_path, args.display_method, args.display_duration)

if __name__ == "__main__":
    main() 