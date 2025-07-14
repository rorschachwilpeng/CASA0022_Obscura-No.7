#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像Prompt构建器
专门负责构建高质量的图像生成提示词
基于天气数据、位置信息和预测结果生成详细的模板化prompt
动态场景调整 - 根据真实地理位置和建筑信息智能选择场景类型
增强版：集成Google Places API获取真实建筑信息
"""

from datetime import datetime
from typing import Dict, Any, List, Optional

class ImagePromptBuilder:
    """图像提示词构建器 - 动态场景调整，支持真实建筑信息"""
    
    def __init__(self, maps_client=None):
        """初始化prompt构建器 - 支持动态场景调整
        
        Args:
            maps_client: MapsClient实例，用于获取建筑信息
        """
        self.maps_client = maps_client
        
        # 动态场景配置 - 根据建筑密度和类型调整
        self.scene_configs = {
            "urban_dense": {
                "base": "high-quality photorealistic city street photograph",
                "scene_type": "urban cityscape",
                "description_focus": "architectural elements and urban infrastructure"
            },
            "urban_moderate": {
                "base": "high-quality photorealistic suburban scene photograph", 
                "scene_type": "suburban environment",
                "description_focus": "mixed residential and commercial buildings"
            },
            "mixed_environment": {
                "base": "high-quality photorealistic environmental scene photograph",
                "scene_type": "mixed urban-natural environment", 
                "description_focus": "buildings integrated with natural surroundings"
            },
            "natural_with_structures": {
                "base": "high-quality photorealistic outdoor scene photograph",
                "scene_type": "natural environment with man-made structures",
                "description_focus": "parks, gardens, or open spaces with nearby buildings"
            }
        }
        
        # 统一的技术设置
        self.technical_settings = {
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
            "style_constraints": [
                "no artistic filters",
                "no painterly effects", 
                "no stylization",
                "photorealistic only"
            ]
        }
    
    def _determine_scene_type(self, buildings_info):
        """根据建筑信息动态确定场景类型
        
        Args:
            buildings_info: 建筑信息字典
            
        Returns:
            str: 场景类型键名
        """
        top_places = buildings_info.get('top_places', [])
        buildings_dict = buildings_info.get('buildings_dict', {})
        
        # 根据建筑数量和类型判断场景
        total_buildings = len(top_places)
        
        if total_buildings >= 3:
            # 检查是否有城市地标
            urban_keywords = ['office', 'tower', 'center', 'square', 'station', 'mall', 'hotel']
            has_urban_landmarks = any(
                any(keyword in place.lower() for keyword in urban_keywords) 
                for place in top_places
            )
            
            if has_urban_landmarks:
                return "urban_dense"
            else:
                return "urban_moderate"
                
        elif total_buildings >= 1:
            # 有少量建筑，判断类型
            cultural_keywords = ['museum', 'gallery', 'park', 'garden', 'church', 'cathedral']
            has_cultural_sites = any(
                any(keyword in place.lower() for keyword in cultural_keywords)
                for place in top_places
            )
            
            if has_cultural_sites:
                return "mixed_environment"
            else:
                return "urban_moderate"
        else:
            # 没有明确建筑信息，使用自然+结构混合
            return "natural_with_structures"
    
    def _get_nearby_buildings_info(self, location_info):
        """获取附近建筑信息 - 增强版
        
        Args:
            location_info: 位置信息字典
            
        Returns:
            Dict: 包含建筑信息的字典
        """
        if not self.maps_client:
            print("⚠️ Maps客户端未配置，无法获取建筑信息")
            return {
                'top_places': [],
                'buildings_dict': {},
                'buildings_text': "nearby structures and facilities",
                'scene_type': "natural_with_structures"
            }
        
        try:
            lat = location_info.get('latitude', 0)
            lon = location_info.get('longitude', 0)
            
            if lat == 0 and lon == 0:
                print("⚠️ 无效的坐标信息")
                return {
                    'top_places': [],
                    'buildings_dict': {},
                    'buildings_text': "nearby structures and facilities",
                    'scene_type': "natural_with_structures"
                }
            
            print(f"🏛️ 获取坐标 ({lat:.4f}, {lon:.4f}) 附近的建筑信息...")
            
            # 获取附近著名建筑
            top_places = self.maps_client.get_top_nearby_places(lat, lon, radius=1200, max_places=4)
            buildings_dict = self.maps_client.get_nearby_buildings(lat, lon, radius=1200)
            
            # 构建建筑信息对象
            buildings_info = {
                'top_places': top_places,
                'buildings_dict': buildings_dict
            }
            
            # 动态确定场景类型
            scene_type = self._determine_scene_type(buildings_info)
            
            if top_places:
                buildings_text = ", ".join(top_places)
                print(f"✅ 获取到建筑信息: {buildings_text}")
                print(f"🎯 确定场景类型: {scene_type}")
            else:
                buildings_text = "nearby structures and facilities"
                print("⚠️ 未获取到具体建筑信息，使用默认描述")
                print(f"🎯 默认场景类型: {scene_type}")
            
            return {
                'top_places': top_places,
                'buildings_dict': buildings_dict,
                'buildings_text': buildings_text,
                'scene_type': scene_type
            }
            
        except Exception as e:
            print(f"❌ 获取建筑信息失败: {e}")
            return {
                'top_places': [],
                'buildings_dict': {},
                'buildings_text': "nearby structures and facilities",
                'scene_type': "natural_with_structures"
            }

    def build_comprehensive_prompt(self, weather_data, location_info, prediction_data=None, style_preference="realistic"):
        """构建综合的图像生成prompt - 动态场景调整，包含真实建筑信息"""
        
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
        
        # 获取真实建筑信息并确定场景类型 - 核心改进
        buildings_info = self._get_nearby_buildings_info(location_info)
        top_places = buildings_info['top_places']
        buildings_text = buildings_info['buildings_text']
        scene_type = buildings_info['scene_type']
        
        # 根据场景类型选择配置
        scene_config = self.scene_configs[scene_type]
        
        # 如果有建筑信息，优化地址描述
        if top_places:
            # 使用最著名的建筑作为主要地标
            primary_landmark = top_places[0]
            address = f"near {primary_landmark}"
        
        # 处理预测信息 - 增强None检查
        if prediction_data and isinstance(prediction_data, dict):
            predicted_temp = prediction_data.get("predicted_temperature", temp + 1)
            predicted_weather = prediction_data.get("predicted_weather_condition", weather_desc)
        else:
            # 生成简单的预测变化
            import random
            predicted_temp = temp + random.uniform(-2, 3)
            predicted_weather = f"transitioning {weather_desc}"
        
        # 使用动态选择的场景配置
        camera_details = ", ".join(self.technical_settings["camera_settings"])
        lighting_details = ", ".join(self.technical_settings["lighting"])
        quality_details = ", ".join(self.technical_settings["quality_modifiers"])
        style_constraints = ", ".join(self.technical_settings["style_constraints"])
        
        # 构建动态调整的prompt
        prompt = f"""A {scene_config["base"]} captured {address}.

SCENE TYPE: {scene_config["scene_type"]} focusing on {scene_config["description_focus"]}

PHOTOGRAPHIC DETAILS:
- Camera: {camera_details}
- Lighting: {lighting_details}
- Time: {time_of_day}, {current_date}
- Location context: Near by there is {buildings_text}

ENVIRONMENTAL CONDITIONS:
- Current weather: {weather_desc} at {temp}°C
- Predicted conditions: {predicted_weather} at {predicted_temp:.1f}°C  
- Humidity: {humidity}%, Pressure: {pressure} hPa
- Wind: {wind_speed} m/s
- Coordinates: {lat:.4f}, {lon:.4f}

STYLE REQUIREMENTS:
{quality_details}, {style_constraints}, realistic environmental documentation with authentic weather conditions.

The photograph documents the environmental transition from current conditions to predicted future weather, showing {buildings_text} within the {scene_config["scene_type"]}, captured with authentic photorealistic detail and natural color accuracy."""
        
        # 确保prompt长度适中（DALL-E限制）
        if len(prompt) > 950:
            # 简化版本，保持动态场景核心要素和建筑信息
            simplified_buildings = ", ".join(top_places[:2]) if top_places else "local structures"
            prompt = f"""A {scene_config["base"]} {address}. {scene_config["scene_type"]} with {camera_details}, {lighting_details[:50]}. Weather transition: {weather_desc} ({temp}°C) to {predicted_weather} ({predicted_temp:.1f}°C). Near by there is {simplified_buildings}. {quality_details[:50]}, {style_constraints[:30]}, photorealistic environmental documentation showing {scene_config["description_focus"]}."""
        
        print(f"🎨 生成prompt (长度: {len(prompt)}字符)")
        print(f"🎯 场景类型: {scene_type}")
        if top_places:
            print(f"🏛️ 包含建筑: {', '.join(top_places)}")
        
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
