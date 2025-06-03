#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
电子墨水屏幕显示脚本
用于在树莓派连接的电子墨水屏幕上显示生成的图像
注意：此脚本需要根据您的具体电子墨水屏幕型号进行调整
"""

import os
import sys
import time
import argparse
from PIL import Image

# 尝试导入waveshare电子墨水屏幕库
# 如果您使用不同的电子墨水屏幕，请调整此部分
try:
    # 这里假设使用的是Waveshare的电子墨水屏幕
    # 您需要安装Waveshare的库：https://github.com/waveshare/e-Paper
    sys.path.append("lib/waveshare/e-Paper/RaspberryPi_JetsonNano/python/lib/")
    from waveshare_epd import epd2in13_V2  # 根据您的屏幕型号调整导入
    WAVESHARE_AVAILABLE = True
except ImportError:
    print("警告：未找到Waveshare电子墨水屏幕库。将使用模拟模式。")
    WAVESHARE_AVAILABLE = False

def simulate_eink_display(image_path):
    """模拟电子墨水屏幕显示，用于测试"""
    try:
        image = Image.open(image_path)
        print(f"模拟显示图像：{image_path}")
        print(f"图像大小: {image.size[0]}x{image.size[1]}")
        print("在实际环境中，图像将显示在电子墨水屏幕上")
        image.show()  # 在GUI环境中显示图像
    except Exception as e:
        print(f"模拟显示时出错: {e}")
        return False
    return True

def display_on_waveshare(image_path, screen_width=122, screen_height=250):
    """在Waveshare电子墨水屏幕上显示图像"""
    try:
        # 初始化电子墨水屏幕
        epd = epd2in13_V2.EPD()  # 根据您的屏幕型号调整
        epd.init(epd.FULL_UPDATE)
        epd.Clear(0xFF)  # 清除屏幕
        
        # 打开图像
        image = Image.open(image_path)
        
        # 调整图像大小以适应屏幕
        resized_image = image.resize((screen_width, screen_height))
        
        # 将图像转换为黑白（1位）
        bw_image = resized_image.convert('1')
        
        # 显示图像
        epd.display(epd.getbuffer(bw_image))
        
        # 进入深度睡眠模式以节省电量
        epd.sleep()
        
        print(f"已在电子墨水屏幕上显示图像: {image_path}")
        return True
        
    except Exception as e:
        print(f"在电子墨水屏幕上显示图像时出错: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="在电子墨水屏幕上显示图像")
    parser.add_argument("--image", type=str, default="weather_art.png", help="要显示的图像路径")
    parser.add_argument("--width", type=int, default=122, help="屏幕宽度（像素）")
    parser.add_argument("--height", type=int, default=250, help="屏幕高度（像素）")
    parser.add_argument("--simulate", action="store_true", help="模拟模式，不实际使用电子墨水屏幕")
    args = parser.parse_args()
    
    # 检查图像是否存在
    if not os.path.exists(args.image):
        print(f"错误：图像文件不存在: {args.image}")
        return False
    
    # 显示图像
    if args.simulate or not WAVESHARE_AVAILABLE:
        return simulate_eink_display(args.image)
    else:
        return display_on_waveshare(args.image, args.width, args.height)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 