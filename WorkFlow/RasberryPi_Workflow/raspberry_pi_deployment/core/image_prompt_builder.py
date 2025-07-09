#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像Prompt构建器
专门负责构建高质量的图像生成提示词
基于天气数据、位置信息和预测结果生成详细的模板化prompt
"""

from datetime import datetime
from typing import Dict, Any, List, Optional

class ImagePromptBuilder:
    """图像提示词构建器"""
    
    def __init__(self):
        """初始化prompt构建器"""
        self.style_presets = {
            "realistic": {
                "base": "photorealistic landscape photograph",
                "modifiers": ["professional photography", "high resolution", "natural lighting"],
                "atmosphere": "realistic environmental conditions"
            },
            "artistic": {
                "base": "artistic interpretation of landscape", 
                "modifiers": ["painterly style", "vibrant colors", "artistic composition"],
                "atmosphere": "artistic environmental storytelling"
            }
        }
    
    def build_comprehensive_prompt(self, weather_data, location_info, prediction_data=None, style_preference="realistic"):
        """构建综合的图像生成prompt"""
        
        # 获取当前时间信息
        current_time = datetime.now()
        time_of_day = current_time.strftime("%I:%M %p")
        current_date = current_time.strftime("%B %d, %Y")
        
        # 提取天气信息
        current_weather = weather_data.get("current_weather", {})
        temp = current_weather.get("temperature", 15)
        humidity = current_weather.get("humidity", 50)
        pressure = current_weather.get("pressure", 1013)
        wind_speed = current_weather.get("wind_speed", 5)
        weather_desc = current_weather.get("weather_description", "clear sky")
        
        # 提取位置信息
        map_info = location_info.get("map_info", {})
        lat = location_info.get("latitude", 0)
        lon = location_info.get("longitude", 0)
        address = map_info.get("location_info", f"coordinates {lat:.4f}, {lon:.4f}")
        
        # 处理周围兴趣点
        nearby_places = []
        location_details = map_info.get("location_details", {})
        if location_details.get("locality"):
            nearby_places.append(location_details["locality"])
        if location_details.get("country"):
            nearby_places.append(f"in {location_details['country']}")
        
        if not nearby_places:
            nearby_places = ["urban buildings", "local landmarks"]
        
        # 处理预测信息
        if prediction_data:
            predicted_temp = prediction_data.get("predicted_temperature", temp + 1)
            predicted_weather = prediction_data.get("predicted_weather_condition", weather_desc)
        else:
            # 生成简单的预测变化
            import random
            predicted_temp = temp + random.uniform(-2, 3)
            predicted_weather = f"transitioning {weather_desc}"
        
        # 选择风格
        style_config = self.style_presets.get(style_preference, self.style_presets["realistic"])
        
        # 构建详细prompt（基于1_1脚本的模板）
        places_text = " and ".join(nearby_places) if len(nearby_places) > 1 else nearby_places[0] if nearby_places else "local features"
        
        prompt = f"""A {style_config["base"]} taken at {address}.

Time of day: {time_of_day}
Address: {address}
Coordinates: {lat:.4f}, {lon:.4f}
Weather: {weather_desc} transitioning to {predicted_weather}
Temperature: {temp}°C (predicted: {predicted_temp:.1f}°C)
Humidity: {humidity}%
Pressure: {pressure} hPa
Wind Speed: {wind_speed} m/s
Date: {current_date}
Nearby there are {places_text}.

The scene shows the environmental changes from current conditions ({temp}°C, {weather_desc}) 
to predicted future conditions ({predicted_temp:.1f}°C, {predicted_weather}). 
The atmosphere should reflect the humidity level of {humidity}% and atmospheric pressure of {pressure} hPa.

Style: {", ".join(style_config["modifiers"])}, {style_config["atmosphere"]}, 
showing the transition from current to predicted weather conditions in an artistic way."""
        
        # 确保prompt长度适中（DALL-E限制）
        if len(prompt) > 950:
            # 简化版本
            prompt = f"""A {style_config["base"]} at {address} showing weather transition from {weather_desc} ({temp}°C) to {predicted_weather} ({predicted_temp:.1f}°C). {", ".join(style_config["modifiers"][:2])}, atmospheric environmental storytelling, professional quality."""
        
        return prompt

if __name__ == "__main__":
    # 测试用例
    print("🎨 图像Prompt构建器测试")
    
    # 模拟数据
    test_weather = {
        "current_weather": {
            "temperature": 18,
            "humidity": 65,
            "pressure": 1015,
            "wind_speed": 3.5,
            "weather_description": "partly cloudy"
        }
    }
    
    test_location = {
        "latitude": 51.5074,
        "longitude": -0.1278,
        "map_info": {
            "location_info": "London, UK",
            "location_details": {
                "locality": "London",
                "country": "United Kingdom"
            }
        }
    }
    
    builder = ImagePromptBuilder()
    prompt = builder.build_comprehensive_prompt(test_weather, test_location)
    print(f"\nGenerated prompt ({len(prompt)} chars):")
    print(prompt)
