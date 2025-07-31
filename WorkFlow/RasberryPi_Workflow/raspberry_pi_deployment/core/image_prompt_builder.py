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
    """图像提示词构建器 - 动态场景调整，支持多种艺术风格"""
    
    def __init__(self, maps_client=None):
        """初始化prompt构建器 - 支持多种艺术风格
        
        Args:
            maps_client: MapsClient实例，用于获取建筑信息
        """
        self.maps_client = maps_client
        
        # 🎨 多种艺术风格配置
        self.art_styles = {
            "realistic": {
                "name": "Realistic",
                "base_description": "high-quality photorealistic",
                "technical_approach": "professional DSLR photography",
                "quality_terms": ["photojournalistic", "documentary", "natural lighting", "authentic colors"],
                "constraints": ["no artistic filters", "no stylization", "photorealistic only"]
            },
            "comic": {
                "name": "Comic", 
                "base_description": "vibrant comic book style illustration",
                "technical_approach": "digital comic art technique",
                "quality_terms": ["bold colors", "clean line art", "dynamic composition", "cel-shading"],
                "constraints": ["comic book aesthetic", "illustrated style", "bright color palette"]
            },
            "futuristic": {
                "name": "Futuristic",
                "base_description": "futuristic sci-fi concept art",
                "technical_approach": "digital concept art rendering",
                "quality_terms": ["neon lighting", "holographic elements", "metallic surfaces", "advanced technology"],
                "constraints": ["cyberpunk aesthetic", "high-tech environment", "glowing elements"]
            },
            "steampunk": {
                "name": "Steampunk",
                "base_description": "steampunk Victorian-era inspired artwork",
                "technical_approach": "vintage mechanical aesthetic",
                "quality_terms": ["brass and copper tones", "steam-powered machinery", "clockwork elements", "industrial heritage"],
                "constraints": ["Victorian-era technology", "mechanical details", "warm metallic colors"]
            },

            "watercolor": {
                "name": "Watercolor",
                "base_description": "artistic watercolor painting style",
                "technical_approach": "traditional watercolor technique",
                "quality_terms": ["soft brushstrokes", "transparent washes", "flowing colors", "organic textures"],
                "constraints": ["painterly effects", "watercolor medium", "artistic interpretation"]
            }
        }
        
        # 动态场景配置 - 现在支持多种风格
        self.scene_configs = {
            "urban_dense": {
                "base": "city street scene",
                "scene_type": "urban cityscape",
                "description_focus": "architectural elements and urban infrastructure"
            },
            "urban_moderate": {
                "base": "suburban scene", 
                "scene_type": "suburban environment",
                "description_focus": "mixed residential and commercial buildings"
            },
            "mixed_environment": {
                "base": "environmental scene",
                "scene_type": "mixed urban-natural environment", 
                "description_focus": "buildings integrated with natural surroundings"
            },
            "natural_with_structures": {
                "base": "outdoor landscape scene",
                "scene_type": "natural environment with man-made structures",
                "description_focus": "parks, gardens, or open spaces with nearby buildings"
            }
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
    
    def _select_random_style(self):
        """随机选择一种艺术风格"""
        import random
        available_styles = list(self.art_styles.keys())
        selected_style = random.choice(available_styles)
        print(f"🎨 随机选择艺术风格: {self.art_styles[selected_style]['name']} ({selected_style})")
        return selected_style
    
    def _build_style_specific_prompt(self, style_key, scene_config, buildings_text, address, weather_info, prediction_info):
        """根据指定风格构建prompt
        
        Args:
            style_key: 艺术风格键名
            scene_config: 场景配置
            buildings_text: 建筑描述文本
            address: 地址信息
            weather_info: 当前天气信息
            prediction_info: 预测天气信息
            
        Returns:
            str: 风格化的prompt
        """
        style = self.art_styles[style_key]
        
        # 基础场景描述
        base_scene = f"A {style['base_description']} {scene_config['base']} {address}"
        
        # 技术方法描述
        technical_approach = f"Created using {style['technical_approach']}"
        
        # 质量特征
        quality_features = ", ".join(style['quality_terms'])
        
        # 风格约束
        style_constraints = ", ".join(style['constraints'])
        
        # 环境信息
        env_description = f"Weather transition: {weather_info} to {prediction_info}"
        
        # 建筑信息
        location_context = f"Near by there is {buildings_text}" if buildings_text != "nearby structures and facilities" else "Local architectural context"
        
        # 根据不同风格构建不同的prompt结构
        if style_key == "realistic":
            prompt = f"""{base_scene}.

STYLE: {style['name']} - {technical_approach}
SCENE: {scene_config['scene_type']} focusing on {scene_config['description_focus']}
ENVIRONMENT: {env_description}
LOCATION: {location_context}
QUALITY: {quality_features}
CONSTRAINTS: {style_constraints}

Professional environmental documentation with authentic detail and natural accuracy."""

        elif style_key == "comic":
            prompt = f"""{base_scene}.

COMIC STYLE: {style['name']} illustration with {quality_features}
SCENE: Dynamic {scene_config['scene_type']} with {scene_config['description_focus']}
WEATHER STORY: Visual narrative showing {env_description}
SETTING: {location_context}
ART DIRECTION: {style_constraints}, vibrant storytelling approach

Engaging comic book interpretation of environmental change with clear visual storytelling."""

        elif style_key == "futuristic":
            prompt = f"""{base_scene}.

FUTURISTIC VISION: {style['name']} concept featuring {quality_features}
ADVANCED SCENE: High-tech {scene_config['scene_type']} showcasing {scene_config['description_focus']}
CLIMATE PROJECTION: Sci-fi visualization of {env_description}
TECH ENVIRONMENT: {location_context} enhanced with future technology
AESTHETIC: {style_constraints}, cutting-edge digital artistry

Visionary sci-fi interpretation of future environmental conditions with advanced technological integration."""

        elif style_key == "steampunk":
            prompt = f"""{base_scene}.

STEAMPUNK AESTHETIC: {style['name']} featuring {quality_features}
VICTORIAN SCENE: Steam-era {scene_config['scene_type']} with mechanical {scene_config['description_focus']}
WEATHER MACHINERY: Clockwork interpretation of {env_description}
INDUSTRIAL SETTING: {location_context} with vintage scientific instruments
DESIGN: {style_constraints}, mechanical precision artistry

Victorian-era inspired environmental documentation with steam-powered scientific equipment and brass instrumentation."""

        elif style_key == "watercolor":
            prompt = f"""{base_scene}.

WATERCOLOR ART: {style['name']} with {quality_features}
ARTISTIC SCENE: Painted {scene_config['scene_type']} showcasing {scene_config['description_focus']}
WEATHER MOOD: Atmospheric portrayal of {env_description}
PAINTED SETTING: Artistic interpretation of {location_context}
MEDIUM: {style_constraints}, flowing artistic expression

Traditional watercolor painting capturing the mood and atmosphere of environmental transition with artistic fluidity."""

        else:
            # 默认风格（保底）
            prompt = f"{base_scene}. {technical_approach} showing {env_description}. {location_context}. {quality_features}, {style_constraints}."
        
        return prompt

    def build_comprehensive_prompt(self, weather_data, location_info, prediction_data=None, style_preference="random"):
        """构建综合的图像生成prompt - 支持多种艺术风格随机选择
        
        Args:
            weather_data: 天气数据
            location_info: 位置信息
            prediction_data: 预测数据
            style_preference: 风格偏好 ("random"为随机选择，或指定具体风格)
        """
        
        # 🎨 第1步：选择艺术风格
        if style_preference == "random":
            selected_style = self._select_random_style()
        elif style_preference in self.art_styles:
            selected_style = style_preference
            print(f"🎨 使用指定艺术风格: {self.art_styles[selected_style]['name']} ({selected_style})")
        else:
            print(f"⚠️ 无效的风格偏好 '{style_preference}'，使用随机选择")
            selected_style = self._select_random_style()
        
        # 🗺️ 第2步：获取地理和建筑信息
        buildings_info = self._get_nearby_buildings_info(location_info)
        top_places = buildings_info['top_places']
        buildings_text = buildings_info['buildings_text']
        scene_type = buildings_info['scene_type']
        scene_config = self.scene_configs[scene_type]
        
        # 📍 第3步：处理地址信息
        map_info = location_info.get("map_info", {})
        lat = location_info.get("latitude", 0)
        lon = location_info.get("longitude", 0)
        address = map_info.get("location_info", f"coordinates {lat:.4f}, {lon:.4f}")
        
        if top_places:
            primary_landmark = top_places[0]
            address = f"near {primary_landmark}"
        
        # 🌤️ 第4步：处理天气信息
        current_weather = weather_data.get("current_weather", {})
        temp = current_weather.get("temperature", 15)
        weather_desc = current_weather.get("weather_description", "clear sky")
        
        # 🔮 第5步：处理预测信息
        if prediction_data and isinstance(prediction_data, dict):
            predicted_temp = prediction_data.get("predicted_temperature", temp + 1)
            predicted_weather = prediction_data.get("predicted_weather_condition", weather_desc)
        else:
            import random
            predicted_temp = temp + random.uniform(-2, 3)
            predicted_weather = f"transitioning {weather_desc}"
        
        # 📝 第6步：构建风格化prompt
        weather_info = f"{weather_desc}, {temp}°C"
        prediction_info = f"{predicted_weather}, {predicted_temp:.1f}°C"
        
        prompt = self._build_style_specific_prompt(
            style_key=selected_style,
            scene_config=scene_config,
            buildings_text=buildings_text,
            address=address,
            weather_info=weather_info,
            prediction_info=prediction_info
        )
        
        # 📏 第7步：确保prompt长度适中（DALL-E限制）
        if len(prompt) > 950:
            # 简化版本
            simplified_buildings = ", ".join(top_places[:2]) if top_places else "local structures"
            style_name = self.art_styles[selected_style]['name']
            simplified_prompt = f"A {self.art_styles[selected_style]['base_description']} {scene_config['base']} {address}. {style_name} showing weather transition from {weather_info} to {prediction_info}. Near {simplified_buildings}. {', '.join(self.art_styles[selected_style]['quality_terms'][:3])}, {', '.join(self.art_styles[selected_style]['constraints'][:2])}."
            prompt = simplified_prompt
        
        # 📊 第8步：输出生成信息
        print(f"🎨 生成prompt (长度: {len(prompt)}字符)")
        print(f"🎯 艺术风格: {self.art_styles[selected_style]['name']}")
        print(f"🏛️ 场景类型: {scene_type}")
        if top_places:
            print(f"🏢 包含建筑: {', '.join(top_places)}")
        
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
    print("🎨 多风格艺术 Prompt构建器测试")
    print("=" * 60)
    
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
    
    print(f"🌟 可用艺术风格: {list(builder.art_styles.keys())}")
    print()
    
    # 测试随机风格选择（默认）
    print("🎲 测试1: 随机风格选择")
    prompt1 = builder.build_comprehensive_prompt(test_weather, test_location)
    print(f"Prompt 长度: {len(prompt1)} 字符")
    print("-" * 40)
    
    # 测试指定风格
    print("\n🎯 测试2: 指定漫画风格")
    prompt2 = builder.build_comprehensive_prompt(test_weather, test_location, style_preference="comic")
    print(f"Prompt 长度: {len(prompt2)} 字符")
    print("-" * 40)
    
    print("\n🔮 测试3: 指定未来主义风格")
    prompt3 = builder.build_comprehensive_prompt(test_weather, test_location, style_preference="futuristic")
    print(f"Prompt 长度: {len(prompt3)} 字符")
    print("-" * 40)
    
    print("\n⚙️ 测试4: 指定蒸汽朋克风格")
    prompt4 = builder.build_comprehensive_prompt(test_weather, test_location, style_preference="steampunk")
    print(f"Prompt 长度: {len(prompt4)} 字符")
    print("-" * 40)
    
    print("\n🎨 测试5: 再次随机选择（演示随机性）")
    prompt5 = builder.build_comprehensive_prompt(test_weather, test_location)
    print(f"Prompt 长度: {len(prompt5)} 字符")
    
    print("\n" + "=" * 60)
    print("✅ 多风格测试完成！每次调用都会随机选择不同的艺术风格。")
