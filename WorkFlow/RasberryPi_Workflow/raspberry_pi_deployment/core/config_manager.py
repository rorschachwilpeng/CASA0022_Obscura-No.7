#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器
管理系统配置加载、验证和默认值设置
"""

import json
import os
from typing import Dict, Any
from dotenv import load_dotenv

class ConfigManager:
    def __init__(self, config_path: str = 'config.json'):
        """初始化配置管理器"""
        self.config_path = config_path
        
        # 加载环境变量（从当前工作目录和上级目录）
        # 尝试多个可能的.env文件位置
        possible_env_paths = [
            '.env',  # 当前工作目录
            os.path.join(os.path.dirname(__file__), '..', '.env'),  # 上级目录
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'),  # 绝对路径上级目录
        ]
        
        env_loaded = False
        for env_path in possible_env_paths:
            if os.path.exists(env_path):
                load_dotenv(env_path)
                print(f"✅ 环境变量文件加载成功: {env_path}")
                env_loaded = True
                break
        
        if not env_loaded:
            print("⚠️ 未找到.env文件，使用系统环境变量")
        
        self.config = self._load_config()
        
        # 用环境变量覆盖API密钥
        self._load_env_api_keys()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"✅ 配置文件加载成功: {self.config_path}")
                return self._merge_with_defaults(config)
            except json.JSONDecodeError as e:
                print(f"❌ 配置文件JSON格式错误: {e}")
                return self._get_default_config()
            except Exception as e:
                print(f"❌ 配置文件加载失败: {e}")
                return self._get_default_config()
        else:
            print(f"⚠️ 配置文件不存在: {self.config_path}，使用默认配置")
            default_config = self._get_default_config()
            self._save_default_config(default_config)
            return default_config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "hardware": {
                "distance_bus": 3,
                "distance_addr": "0x36", 
                "magnetometer_bus": 4,
                "magnetometer_addr": "0x0d",
                "time_bus": 5,
                "encoder_addr": "0x36"
            },
            "api_keys": {
                "openweather_api_key": "YOUR_OPENWEATHER_API_KEY_HERE",
                "openai_api_key": "YOUR_OPENAI_API_KEY_HERE",
                "stability_ai_api_key": "YOUR_STABILITY_AI_API_KEY_HERE",
                "huggingface_api_key": "YOUR_HUGGINGFACE_API_KEY_HERE"
            },
            "api_endpoints": {
                "ml_prediction_url": "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium",
                "image_generation_url": "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                "weather_api_base": "https://api.openweathermap.org/data/2.5",
                "website_upload_url": "http://localhost:5000/api/upload-image"
            },
            "telescope_settings": {
                "base_location": {
                    "latitude": 51.5074,
                    "longitude": -0.1278,
                    "name": "London, UK"
                },
                "distance_range": {
                    "min_km": 1,
                    "max_km": 50,
                    "step_km": 1
                },
                "time_offset_range": {
                    "min_years": 0,
                    "max_years": 50
                }
            },
            "image_generation": {
                "width": 1024,
                "height": 1024,
                "style_prompt_prefix": "A beautiful artistic interpretation of a future landscape showing",
                "quality": "standard",
                "steps": 30,
                "cfg_scale": 7.0
            },
            "retry_settings": {
                "max_retries": 3,
                "retry_delay_seconds": 2,
                "timeout_seconds": 30
            },
            "output_settings": {
                "save_images_locally": True,
                "local_image_directory": "./generated_images/",
                "upload_to_website": True,
                "website_gallery_enabled": True
            },
            "debugging": {
                "verbose_logging": True,
                "save_api_responses": True,
                "log_file": "./logs/telescope_workflow.log"
            }
        }
    
    def _merge_with_defaults(self, user_config: Dict[str, Any]) -> Dict[str, Any]:
        """将用户配置与默认配置合并"""
        default_config = self._get_default_config()
        return self._deep_merge(default_config, user_config)
    
    def _deep_merge(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并两个字典"""
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _load_env_api_keys(self):
        """从环境变量加载API密钥"""
        env_mapping = {
            'OPENWEATHER_API_KEY': 'api_keys.openweather_api_key',
            'OPENAI_API_KEY': 'api_keys.openai_api_key',
            'CLOUDINARY_URL': 'api_keys.cloudinary_url',
            'GOOGLE_MAPS_API_KEY': 'api_keys.google_maps_api_key',
            'DATABASE_URL': 'api_keys.database_url'
        }
        
        for env_var, config_path in env_mapping.items():
            env_value = os.getenv(env_var)
            if env_value:
                self.set(config_path, env_value)
                print(f"✅ 从环境变量加载: {env_var}")
            else:
                print(f"⚠️ 环境变量未设置: {env_var}")
    
    def _save_default_config(self, config: Dict[str, Any]):
        """保存默认配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"📝 默认配置已保存到: {self.config_path}")
        except Exception as e:
            print(f"❌ 保存默认配置失败: {e}")
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self.config
    
    def get(self, key_path: str, default=None):
        """获取配置值（支持点号路径）"""
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any):
        """设置配置值（支持点号路径）"""
        keys = key_path.split('.')
        target = self.config
        
        # 导航到目标位置
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        
        # 设置值
        target[keys[-1]] = value
    
    def save_config(self):
        """保存当前配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"✅ 配置已保存到: {self.config_path}")
            return True
        except Exception as e:
            print(f"❌ 保存配置失败: {e}")
            return False
    
    def validate_api_keys(self) -> Dict[str, bool]:
        """验证API密钥配置"""
        api_keys = self.get('api_keys', {})
        validation_result = {}
        
        for service, key in api_keys.items():
            is_valid = key and key != f"YOUR_{service.upper()}_HERE"
            validation_result[service] = is_valid
            
            if is_valid:
                print(f"✅ {service}: 已配置")
            else:
                print(f"⚠️ {service}: 未配置或使用默认占位符")
        
        return validation_result
    
    def check_output_directories(self):
        """检查并创建输出目录"""
        directories = [
            self.get('output_settings.local_image_directory', './generated_images/'),
            './workflow_outputs/',
            './logs/'
        ]
        
        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"📁 输出目录准备就绪: {directory}")
            except Exception as e:
                print(f"❌ 创建目录失败 {directory}: {e}")
    
    def get_hardware_config(self) -> Dict[str, Any]:
        """获取硬件配置"""
        return self.get('hardware', {})
    
    def get_api_config(self) -> Dict[str, Any]:
        """获取API配置"""
        return {
            'keys': self.get('api_keys', {}),
            'endpoints': self.get('api_endpoints', {}),
            'retry_settings': self.get('retry_settings', {})
        }
    
    def get_telescope_config(self) -> Dict[str, Any]:
        """获取望远镜配置"""
        return self.get('telescope_settings', {})
    
    def print_config_summary(self):
        """打印配置摘要"""
        print("\n📋 配置摘要")
        print("=" * 50)
        
        # 基础位置
        base_location = self.get('telescope_settings.base_location', {})
        print(f"📍 基础位置: {base_location.get('name', 'Unknown')} "
              f"({base_location.get('latitude', 'N/A')}, {base_location.get('longitude', 'N/A')})")
        
        # 距离范围
        distance_range = self.get('telescope_settings.distance_range', {})
        print(f"📏 距离范围: {distance_range.get('min_km', 1)}-{distance_range.get('max_km', 50)} km")
        
        # API状态
        print("\n🔑 API密钥状态:")
        self.validate_api_keys()
        
        # 输出设置
        print(f"\n💾 图像保存: {self.get('output_settings.local_image_directory', './generated_images/')}")
        print(f"🌐 网站上传: {'启用' if self.get('output_settings.upload_to_website', True) else '禁用'}")
        print(f"🔍 详细日志: {'启用' if self.get('debugging.verbose_logging', True) else '禁用'}")

if __name__ == "__main__":
    # 测试用例
    print("🔧 配置管理器测试")
    print("=" * 40)
    
    # 测试配置加载
    config_manager = ConfigManager()
    
    # 打印配置摘要
    config_manager.print_config_summary()
    
    # 测试配置访问
    print("\n🧪 配置访问测试:")
    print(f"OpenWeather API密钥: {config_manager.get('api_keys.openweather_api_key', 'Not Set')[:20]}...")
    print(f"基础纬度: {config_manager.get('telescope_settings.base_location.latitude')}")
    print(f"图像宽度: {config_manager.get('image_generation.width')}")
    print(f"不存在的键: {config_manager.get('non.existent.key', 'Default Value')}")
    
    # 测试配置修改
    print("\n🔧 配置修改测试:")
    config_manager.set('test.new_value', 'Hello World')
    print(f"新设置的值: {config_manager.get('test.new_value')}")
    
    # 检查输出目录
    print("\n📁 输出目录检查:")
    config_manager.check_output_directories()
    
    print("\n✅ 配置管理器测试完成")
