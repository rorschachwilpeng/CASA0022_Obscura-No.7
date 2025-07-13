#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像Prompt构建器
专门负责构建高质量的图像生成提示词
基于天气数据、位置信息和预测结果生成详细的模板化prompt
统一写实风格 - 确保所有生成图像保持一致的摄影写实画风
"""

from datetime import datetime
from typing import Dict, Any, List, Optional

class ImagePromptBuilder:
    """图像提示词构建器 - 统一写实风格"""
    
    def __init__(self):
        """初始化prompt构建器 - 专注写实摄影风格"""
        # 统一使用强化的写实风格，确保画风一致性
        self.unified_realistic_style = {
            "base": "high-quality photorealistic landscape photograph",
            "camera_settings": [
                "shot with professional DSLR camera",
                "35mm lens",
                "natural depth of field",
                "crisp focus"
            ],
            "lighting": [
                "natural lighting conditions",
                "atmospheric lighting",
                "realistic shadows and highlights",
                "authentic color temperature"
            ],
            "quality_modifiers": [
                "professional photography",
                "high resolution 4K",
                "sharp details",
                "photojournalistic style",
                "documentary photography aesthetic"
            ],
            "atmosphere": "realistic environmental documentation with authentic weather conditions",
            "style_constraints": [
                "no artistic filters",
                "no painterly effects",
                "no stylization",
                "photorealistic only"
            ]
        }
    
    def build_comprehensive_prompt(self, weather_data, location_info, prediction_data=None, style_preference="realistic"):
        """构建综合的图像生成prompt - 统一写实风格"""
        
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
            nearby_places = ["natural landscape features", "local terrain"]
        
        # 处理预测信息 - 增强None检查
        if prediction_data and isinstance(prediction_data, dict):
            predicted_temp = prediction_data.get("predicted_temperature", temp + 1)
            predicted_weather = prediction_data.get("predicted_weather_condition", weather_desc)
        else:
            # 生成简单的预测变化
            import random
            predicted_temp = temp + random.uniform(-2, 3)
            predicted_weather = f"transitioning {weather_desc}"
        
        # 使用统一的写实风格配置
        style_config = self.unified_realistic_style
        
        # 构建地点描述
        places_text = " and ".join(nearby_places) if len(nearby_places) > 1 else nearby_places[0] if nearby_places else "natural terrain"
        
        # 构建强化写实风格的prompt
        camera_details = ", ".join(style_config["camera_settings"])
        lighting_details = ", ".join(style_config["lighting"])
        quality_details = ", ".join(style_config["quality_modifiers"])
        style_constraints = ", ".join(style_config["style_constraints"])
        
        prompt = f"""A {style_config["base"]} captured at {address}.

PHOTOGRAPHIC DETAILS:
- Camera: {camera_details}
- Lighting: {lighting_details}
- Time: {time_of_day}, {current_date}
- Location: {places_text}

ENVIRONMENTAL CONDITIONS:
- Current weather: {weather_desc} at {temp}°C
- Predicted conditions: {predicted_weather} at {predicted_temp:.1f}°C  
- Humidity: {humidity}%, Pressure: {pressure} hPa
- Wind: {wind_speed} m/s
- Coordinates: {lat:.4f}, {lon:.4f}

STYLE REQUIREMENTS:
{quality_details}, {style_constraints}, {style_config["atmosphere"]}.

The photograph documents the environmental transition from current conditions to predicted future weather, captured with authentic photorealistic detail and natural color accuracy."""
        
        # 确保prompt长度适中（DALL-E限制）
        if len(prompt) > 950:
            # 简化版本，保持写实风格核心要素
            prompt = f"""A {style_config["base"]} at {address}. {camera_details}, {lighting_details[:2]}. Weather transition: {weather_desc} ({temp}°C) to {predicted_weather} ({predicted_temp:.1f}°C). {quality_details[:3]}, {style_constraints[:2]}, photorealistic environmental documentation."""
        
        return prompt
    
    def build_steampunk_futuristic_prompt(self, weather_data, location_info, prediction_data=None):
        """构建蒸汽朋克未来主义风格的写实prompt - 符合项目概念"""
        
        # 获取基础信息
        current_time = datetime.now()
        current_weather = weather_data.get("current_weather", {})
        temp = current_weather.get("temperature", 15)
        weather_desc = current_weather.get("weather_description", "clear sky")
        
        # 预测信息 - 增强None检查
        if prediction_data and isinstance(prediction_data, dict):
            predicted_temp = prediction_data.get("predicted_temperature", temp + 1)
            predicted_weather = prediction_data.get("predicted_weather_condition", weather_desc)
        else:
            import random
            predicted_temp = temp + random.uniform(-2, 3)
            predicted_weather = f"evolved {weather_desc}"
        
        # 蒸汽朋克写实风格
        steampunk_realistic_prompt = f"""A high-quality photorealistic landscape photograph with subtle steampunk elements. 

PHOTOGRAPHIC STYLE: Professional documentary photography, natural lighting, DSLR camera with 35mm lens, photojournalistic quality.

SCENE: A realistic landscape showing environmental conditions transitioning from {weather_desc} ({temp}°C) to predicted future state {predicted_weather} ({predicted_temp:.1f}°C).

STEAMPUNK ELEMENTS: Subtle brass instruments for weather measurement, vintage scientific equipment integrated naturally into the landscape, steam-powered environmental monitoring devices, copper pipes and gauges, all rendered with photorealistic detail.

ATMOSPHERE: Victorian-era scientific expedition aesthetic merged with modern environmental documentation, brass and copper tones, mechanical precision, industrial heritage meets natural environment.

QUALITY: Professional photography, high resolution, natural color grading, authentic materials and textures, no artistic stylization or filters."""
        
        return steampunk_realistic_prompt

if __name__ == "__main__":
    # 测试用例
    print("🎨 统一写实风格 Prompt构建器测试")
    
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
    
    # 测试标准写实风格
    prompt = builder.build_comprehensive_prompt(test_weather, test_location)
    print(f"\n📸 标准写实风格 Prompt ({len(prompt)} chars):")
    print(prompt)
    
    # 测试蒸汽朋克写实风格
    steampunk_prompt = builder.build_steampunk_futuristic_prompt(test_weather, test_location)
    print(f"\n⚙️ 蒸汽朋克写实风格 Prompt ({len(steampunk_prompt)} chars):")
    print(steampunk_prompt)
