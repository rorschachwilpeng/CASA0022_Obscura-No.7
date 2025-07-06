import json
import requests
import os
import time
import random
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt

def json_serializer(obj):
    """JSON序列化辅助函数，处理datetime对象"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云端API客户端
调用真实的ML预测和图像生成API
"""

import requests
import json
import base64
import time
import os
from datetime import datetime
from io import BytesIO
from PIL import Image
try:
    from .config_manager import ConfigManager
except ImportError:
    from config_manager import ConfigManager


def json_serializer(obj):
    """JSON序列化辅助函数，处理datetime对象"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

class CloudAPIClient:
    def __init__(self, config_manager=None):
        """初始化云端API客户端"""
        # 如果没有传入配置管理器，创建一个新的
        if config_manager is None:
            self.config_manager = ConfigManager()
        else:
            self.config_manager = config_manager
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Obscura-No.7-Telescope/1.0'
        })
        
        # 设置API密钥（现在从环境变量获取）
        self.openweather_key = self.config_manager.get('api_keys.openweather_api_key')
        self.openai_key = self.config_manager.get('api_keys.openai_api_key')
        self.stability_key = self.config_manager.get('api_keys.stability_ai_api_key')
        self.huggingface_key = self.config_manager.get('api_keys.huggingface_api_key')
        
        # 获取网站API URL
        self.website_api_url = self.config_manager.get('api_endpoints.website_api_url', 'https://casa0022-obscura-no-7.onrender.com')
        
        # 调试：显示API密钥状态
        print(f"🔑 OpenAI API密钥状态: {'已配置' if self.openai_key and self.openai_key != 'YOUR_OPENAI_API_KEY_HERE' else '未配置'}")
        if self.openai_key and self.openai_key != 'YOUR_OPENAI_API_KEY_HERE':
            print(f"   OpenAI密钥前缀: {self.openai_key[:10]}...")
        
        print(f"🌐 网站API URL: {self.website_api_url}")
        
        # API端点
        self.endpoints = self.config_manager.get('api_endpoints', {})
        
        # 重试设置
        self.max_retries = self.config_manager.get('retry_settings.max_retries', 3)
        self.retry_delay = self.config_manager.get('retry_settings.retry_delay_seconds', 2)
        self.timeout = 120  # 增加到120秒，处理大文件上传
    
    def predict_environmental_data(self, latitude, longitude, month=None, future_years=0):
        """
        调用网站的ML预测API获取环境数据
        
        Args:
            latitude (float): 纬度
            longitude (float): 经度
            month (int): 月份 (1-12)，如果为None则使用当前月份
            future_years (int): 未来年份偏移量（0表示当年）
        
        Returns:
            dict: 环境预测数据
        """
        print(f"🔮 调用环境预测API: lat={latitude}, lon={longitude}")
        
        # 如果没有指定月份，使用当前月份
        if month is None:
            month = datetime.now().month
        
        # 构建请求数据
        prediction_data = {
            'latitude': latitude,
            'longitude': longitude,
            'month': month,
            'future_years': future_years
        }
        
        # 尝试调用网站API
        try:
            url = f"{self.website_api_url}/api/v1/ml/predict"
            print(f"📡 调用URL: {url}")
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Obscura-No.7-Telescope/1.0'
            }
            
            response = self.session.post(
                url,
                json=prediction_data,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 环境预测成功: {result.get('prediction', {}).get('temperature', 'N/A')}°C")
                return result
            else:
                print(f"❌ 环境预测API错误: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 环境预测API调用异常: {e}")
            return None
    
    def predict_art_style(self, weather_features, location_info):
        """使用真实ML模型预测艺术风格"""
        print("🤖 调用真实ML预测API...")
        
        # 首先调用环境预测API
        if 'latitude' in location_info and 'longitude' in location_info:
            env_prediction = self.predict_environmental_data(
                location_info['latitude'],
                location_info['longitude']
            )
            
            if env_prediction:
                # 将环境预测结果整合到weather_features中
                prediction_data = env_prediction.get('prediction', {})
                weather_features.update({
                    'predicted_temperature': prediction_data.get('temperature'),
                    'predicted_humidity': prediction_data.get('humidity'),
                    'predicted_pressure': prediction_data.get('pressure'),
                    'model_confidence': env_prediction.get('model_info', {}).get('confidence', 0)
                })
                print(f"🌡️ 环境预测已整合: {prediction_data.get('temperature', 'N/A')}°C")
        
        # 构建提示词，基于天气和位置数据
        prompt = self._build_style_prompt(weather_features, location_info)
        
        # 方案1: 使用OpenAI ChatGPT
        if self.openai_key and self.openai_key != "YOUR_OPENAI_API_KEY_HERE":
            prediction = self._call_openai_chat(prompt)
            if prediction:
                return self._process_ml_prediction(prediction, weather_features)
        
        # 方案2: 使用HuggingFace推理API
        prediction = self._call_huggingface_inference(prompt)
        if prediction:
            return self._process_ml_prediction(prediction, weather_features)
        
        # 方案3: 备用 - 使用规则基算法
        print("⚠️ ML API不可用，使用规则基预测...")
        return self._fallback_style_prediction(weather_features, location_info)
    
    def generate_artwork(self, style_prediction, weather_data, location_info):
        """生成艺术作品 - 确保总是返回有效的图像文件"""
        print("🎨 调用真实图像生成API...")
        
        # 调试信息：显示OpenAI密钥状态
        print(f"🔍 调试信息:")
        print(f"   OpenAI密钥状态: {bool(self.openai_key)}")
        print(f"   密钥前缀: {self.openai_key[:15] if self.openai_key else 'None'}...")
        print(f"   是否为默认值: {self.openai_key == 'YOUR_OPENAI_API_KEY_HERE' if self.openai_key else 'N/A'}")
        
        # 尝试构建prompt
        try:
            prompt = self._build_art_prompt(style_prediction, weather_data, location_info)
            print(f"✅ Prompt构建成功: {prompt[:100]}...")
        except Exception as e:
            print(f"⚠️ Prompt构建错误，使用默认prompt: {e}")
            prompt = "A beautiful landscape photograph with atmospheric conditions, high quality, professional photography."
        
        # 按优先级尝试不同的生成方案
        image_path = None
        
        # 方案1: OpenAI DALL-E
        print(f"🔍 检查OpenAI DALL-E条件:")
        print(f"   image_path is None: {image_path is None}")
        print(f"   self.openai_key exists: {bool(self.openai_key)}")
        print(f"   not default key: {self.openai_key != 'YOUR_OPENAI_API_KEY_HERE' if self.openai_key else False}")
        
        if not image_path and self.openai_key and self.openai_key != "YOUR_OPENAI_API_KEY_HERE":
            print("🚀 开始调用OpenAI DALL-E...")
            try:
                image_path = self._call_openai_dalle(prompt)
                if image_path and os.path.exists(image_path):
                    print(f"✅ OpenAI DALL-E 生成成功: {os.path.basename(image_path)}")
                else:
                    print("❌ OpenAI DALL-E返回了无效路径")
                    image_path = None
            except Exception as e:
                print(f"❌ OpenAI DALL-E错误: {e}")
                image_path = None
        else:
            print("⏭️ 跳过OpenAI DALL-E，条件不满足")
        
        # 方案2: 备用可视化
        if not image_path:
            print("⚠️ AI图像生成不可用，创建基础可视化...")
            try:
                image_path = self._create_fallback_visualization(weather_data, location_info)
                if image_path and os.path.exists(image_path) and image_path.endswith('.png'):
                    print(f"✅ 备用可视化创建成功: {os.path.basename(image_path)}")
                else:
                    image_path = None
            except Exception as e:
                print(f"❌ 备用可视化错误: {e}")
                image_path = None
        
        # 方案3: 简单PNG图像生成 (新增)
        if not image_path:
            print("⚠️ 备用可视化失败，创建简单PNG图像...")
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'telescope_simple_{timestamp}.png'
                filepath = os.path.join('outputs', 'images', filename)
                
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                # 创建简单的PNG图像
                try:
                    from PIL import Image, ImageDraw, ImageFont
                    
                    # 创建图像
                    img = Image.new('RGB', (800, 600), color='lightblue')
                    draw = ImageDraw.Draw(img)
                    
                    # 尝试使用字体
                    try:
                        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
                    except:
                        font = ImageFont.load_default()
                    
                    # 获取天气信息
                    current_weather = weather_data.get('current_weather', {}) if weather_data else {}
                    temp = current_weather.get('temperature', 15) if current_weather else 15
                    weather_main = current_weather.get('weather_main', 'Clear') if current_weather else 'Clear'
                    
                    # 绘制文本
                    draw.text((50, 50), f"Obscura No.7 Telescope", fill='black', font=font)
                    draw.text((50, 100), f"Temperature: {temp}°C", fill='black', font=font)
                    draw.text((50, 150), f"Weather: {weather_main}", fill='black', font=font)
                    draw.text((50, 250), f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", fill='black', font=font)
                    
                    # 保存图像
                    img.save(filepath, 'PNG')
                    
                except ImportError:
                    # 如果没有PIL，使用matplotlib
                    import matplotlib.pyplot as plt
                    
                    fig, ax = plt.subplots(figsize=(8, 6))
                    
                    current_weather = weather_data.get('current_weather', {}) if weather_data else {}
                    temp = current_weather.get('temperature', 15) if current_weather else 15
                    weather_main = current_weather.get('weather_main', 'Clear') if current_weather else 'Clear'
                    
                    ax.text(0.5, 0.8, 'Obscura No.7 Telescope', ha='center', fontsize=16, transform=ax.transAxes)
                    ax.text(0.5, 0.6, f'Temperature: {temp}°C', ha='center', fontsize=14, transform=ax.transAxes)
                    ax.text(0.5, 0.4, f'Weather: {weather_main}', ha='center', fontsize=14, transform=ax.transAxes)
                    ax.text(0.5, 0.2, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', ha='center', fontsize=12, transform=ax.transAxes)
                    
                    ax.set_facecolor('lightblue')
                    ax.set_xlim(0, 1)
                    ax.set_ylim(0, 1)
                    ax.axis('off')
                    
                    plt.savefig(filepath, dpi=150, bbox_inches='tight')
                    plt.close()
                
                if os.path.exists(filepath):
                    image_path = filepath
                    print(f"✅ 简单PNG图像创建成功: {os.path.basename(image_path)}")
                else:
                    raise Exception("简单PNG创建失败")
                    
            except Exception as e:
                print(f"❌ 简单PNG创建错误: {e}")
                image_path = None
        
        # 方案4: 最小PNG备用方案 (确保总是返回PNG)
        if not image_path:
            print("⚠️ 所有方案失败，创建最小PNG文件...")
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'telescope_minimal_{timestamp}.png'
                filepath = os.path.join('outputs', 'images', filename)
                
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                # 创建最小的有效PNG文件
                png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xdd\x8d\xb4\x1c\x00\x00\x00\x00IEND\xaeB`\x82'
                
                with open(filepath, 'wb') as f:
                    f.write(png_data)
                
                image_path = filepath
                print(f"✅ 最小PNG文件创建成功: {os.path.basename(image_path)}")
                    
            except Exception as e:
                print(f"❌ 最小PNG创建也失败了: {e}")
                # 这里真的没办法了，返回None让上层处理
                return None
        
        return image_path

    def upload_to_website(self, image_path, metadata):
        """上传图像和环境数据到展示网站"""
        print("☁️ 上传到展示网站...")
        
        if not os.path.exists(image_path):
            print("❌ 图像文件不存在")
            return None
        
        try:
            # 步骤1: 尝试上传环境数据（如果API可用）
            env_data_result = self._upload_environmental_data(metadata)
            if not env_data_result:
                print("ℹ️ 环境数据API暂不可用，继续图像上传...")
            
            # 步骤2: 上传图像
            image_result = self._upload_image_file(image_path, metadata, env_data_result)
            
            # 返回综合结果
            return {
                "environmental_data": env_data_result,
                "image_data": image_result,
                "success": bool(image_result),  # 只要图像上传成功就算成功
                "message": "图像上传成功" + (", 环境数据上传成功" if env_data_result else "")
            }
                    
        except Exception as e:
            print(f"❌ 上传错误: {e}")
            return None
    
    def _upload_environmental_data(self, metadata):
        """上传环境数据到ML预测API"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 使用ML预测API而不是环境数据上传API
                ml_predict_url = self.endpoints.get('ml_predict_url', 'http://localhost:5000/api/v1/ml/predict')
                
                # 从天气数据中提取ML预测所需的环境数据
                weather_data = metadata.get('weather', {})
                current_weather = weather_data.get('current_weather', {})
                coordinates = metadata.get('coordinates', {})
                
                # 构建ML预测API需要的数据格式
                ml_payload = {
                    "environmental_data": {
                        "latitude": coordinates.get('latitude', 0),
                        "longitude": coordinates.get('longitude', 0),
                        "temperature": current_weather.get('temperature', 15),
                        "humidity": current_weather.get('humidity', 50),
                        "pressure": current_weather.get('pressure', 1013),
                        "wind_speed": current_weather.get('wind_speed', 0),
                        "weather_description": current_weather.get('weather_description', 'clear'),
                        "timestamp": metadata.get('timestamp', datetime.now().isoformat()),
                        "location_name": metadata.get('location_name', '')
                    },
                    "hours_ahead": 24  # 预测24小时后的天气
                }
                
                response = self.session.post(
                    ml_predict_url,
                    data=json.dumps(ml_payload, default=json_serializer),
                    headers={'Content-Type': 'application/json'},
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ ML预测成功: 预测温度 {result.get('prediction', {}).get('predicted_temperature', 'N/A')}°C")
                    return result
                else:
                    print(f"❌ ML预测失败: {response.status_code}")
                    if response.text:
                        print(f"   错误详情: {response.text}")
                    if attempt < max_retries - 1:
                        print(f"   正在重试... ({attempt + 1}/{max_retries})")
                        time.sleep(2 ** attempt)
                        continue
                    return None
                    
            except Exception as e:
                print(f"❌ ML预测错误 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    print(f"   正在重试...")
                    time.sleep(2 ** attempt)
                    continue
                return None
        return None

    def _clean_weather_data(self, weather_data):
        """清理天气数据中的datetime对象"""
        if not isinstance(weather_data, dict):
            return weather_data
        
        cleaned = {}
        for key, value in weather_data.items():
            if isinstance(value, datetime):
                cleaned[key] = value.isoformat()
            elif isinstance(value, dict):
                cleaned[key] = self._clean_weather_data(value)
            elif isinstance(value, list):
                cleaned[key] = [
                    item.isoformat() if isinstance(item, datetime) 
                    else (self._clean_weather_data(item) if isinstance(item, dict) else item)
                    for item in value
                ]
            else:
                cleaned[key] = value
        return cleaned

    def _upload_image_file(self, image_path, metadata, env_data_result):
        """上传图像文件到API"""
        try:
            # 获取prediction_id (如果有ML预测ID就用它，否则用默认)
            prediction_id = 1  # 默认预测ID
            if env_data_result and env_data_result.get('data', {}).get('prediction_id'):
                prediction_id = env_data_result['data']['prediction_id']
            
            image_upload_url = self.endpoints.get('image_upload_url', 'http://localhost:5000/api/v1/images')
            
            with open(image_path, 'rb') as img_file:
                files = {'file': img_file}
                data = {
                    'description': f"Telescope generated artwork based on {metadata.get('style', {}).get('prediction_type', 'unknown')} style",
                    'prediction_id': str(prediction_id)
                }
                
                response = self.session.post(
                    image_upload_url,
                    files=files,
                    data=data,
                    timeout=self.timeout
                )
                
                if response.status_code == 201:
                    result = response.json()
                    print(f"✅ 图像上传成功: {result.get('image', {}).get('url', 'N/A')}")
                    return result
                else:
                    print(f"❌ 图像上传失败: {response.status_code}")
                    if response.text:
                        print(f"   错误详情: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ 图像上传错误: {e}")
            return None
    
    def _build_style_prompt(self, weather_features, location_info):
        """构建ML风格预测的提示词"""
        temp = weather_features.get('temperature', 15)
        weather_main = weather_features.get('weather_main', 'Clear')
        humidity = weather_features.get('humidity', 50)
        
        prompt = f"""Based on the following environmental conditions, suggest an artistic style for a landscape painting:
        
Temperature: {temp}°C
Weather: {weather_main}
Humidity: {humidity}%
Location: {location_info.get('formatted_coords', 'Unknown')}

Suggest a specific art style (like Impressionism, Realism, Abstract, etc.) and color palette that would best represent these conditions."""
        
        return prompt
    
    def _build_art_prompt(self, style_prediction, weather_data, location_info):
        """构建图像生成的详细提示词 - 修复format错误"""
        try:
            # 安全地获取数据，避免None值
            current_weather = weather_data.get('current_weather', {}) if weather_data else {}
            temp = current_weather.get('temperature', 15) if current_weather else 15
            weather_desc = current_weather.get('weather_description', 'clear sky') if current_weather else 'clear sky'
            style = style_prediction.get('style_recommendation', 'realistic landscape') if style_prediction else 'realistic landscape'
            
            # 安全的字符串格式化
            prompt = f"A professional landscape photograph showing {weather_desc} at {temp}°C, created in {style} style. The scene captures the atmospheric conditions with detailed environmental elements. High quality, professional photography, artistic composition."
            
            return prompt
            
        except Exception as e:
            print(f"⚠️ Prompt构建错误: {e}")
            # 返回默认prompt
            return "A beautiful landscape photograph with clear atmospheric conditions, high quality, professional photography."

    def _call_huggingface_inference(self, prompt):
        """调用HuggingFace推理API"""
        if not self.huggingface_key or self.huggingface_key == "YOUR_HUGGINGFACE_API_KEY_HERE":
            return None
        
        # 使用文本生成模型进行风格预测
        api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        
        headers = {
            "Authorization": f"Bearer {self.huggingface_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 200,
                "temperature": 0.7,
                "do_sample": True
            }
        }
        
        try:
            response = self.session.post(api_url, headers=headers, json=payload, timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ HuggingFace API错误: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ HuggingFace请求错误: {e}")
            return None
    
    def _call_stability_ai(self, prompt):
        """调用Stability AI图像生成"""
        if not self.stability_key or self.stability_key == "YOUR_STABILITY_AI_API_KEY_HERE":
            return None
        
        api_url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        
        headers = {
            "Authorization": f"Bearer {self.stability_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "text_prompts": [
                {
                    "text": prompt,
                    "weight": 1
                }
            ],
            "cfg_scale": self.config.get('image_generation', {}).get('cfg_scale', 7),
            "height": self.config.get('image_generation', {}).get('height', 1024),
            "width": self.config.get('image_generation', {}).get('width', 1024),
            "samples": 1,
            "steps": self.config.get('image_generation', {}).get('steps', 30),
        }
        
        try:
            response = self.session.post(api_url, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                data = response.json()
                if data.get('artifacts'):
                    # 解码base64图像
                    image_data = base64.b64decode(data['artifacts'][0]['base64'])
                    return image_data
            else:
                print(f"❌ Stability AI错误: {response.status_code}")
                if response.text:
                    print(f"   错误详情: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Stability AI请求错误: {e}")
            return None
    
    def _call_huggingface_image_generation(self, prompt):
        """调用HuggingFace图像生成API"""
        if not self.huggingface_key or self.huggingface_key == "YOUR_HUGGINGFACE_API_KEY_HERE":
            return None
        
        # 使用DALL-E风格的图像生成模型
        api_url = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
        
        headers = {
            "Authorization": f"Bearer {self.huggingface_key}",
        }
        
        payload = {"inputs": prompt}
        
        try:
            response = self.session.post(api_url, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                return response.content  # 直接返回图像字节
            else:
                print(f"❌ HuggingFace图像生成错误: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ HuggingFace图像生成请求错误: {e}")
            return None
    
    def _call_openai_chat(self, prompt):
        """调用OpenAI ChatGPT进行风格预测"""
        if not self.openai_key or self.openai_key == "YOUR_OPENAI_API_KEY_HERE":
            return None
        
        api_url = "https://api.openai.com/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert art curator who suggests painting styles based on environmental conditions. Respond with specific art styles and color recommendations."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 150,
            "temperature": 0.7
        }
        
        try:
            response = self.session.post(api_url, headers=headers, json=payload, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                if data.get('choices') and len(data['choices']) > 0:
                    return {'generated_text': data['choices'][0]['message']['content']}
                return None
            else:
                print(f"❌ OpenAI ChatGPT错误: {response.status_code}")
                if response.text:
                    print(f"   错误详情: {response.text}")
                return None
        except Exception as e:
            print(f"❌ OpenAI ChatGPT请求错误: {e}")
            return None
    
    def _call_openai_dalle(self, prompt):
        """调用OpenAI DALL-E生成图像并保存到文件"""
        if not self.openai_key or self.openai_key == "YOUR_OPENAI_API_KEY_HERE":
            print("⚠️ OpenAI API密钥未配置")
            return None
        
        print("🎨 调用OpenAI DALL-E API...")
        api_url = "https://api.openai.com/v1/images/generations"
        
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        
        # 限制提示词长度（DALL-E有1000字符限制）
        if len(prompt) > 900:
            prompt = prompt[:900] + "..."
        
        payload = {
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
            "response_format": "url"
        }
        
        try:
            response = self.session.post(api_url, headers=headers, json=payload, timeout=120)
            if response.status_code == 200:
                data = response.json()
                if data.get('data') and len(data['data']) > 0:
                    image_url = data['data'][0]['url']
                    print(f"✅ OpenAI DALL-E生成成功，正在下载图像...")
                    
                    # 下载图像
                    img_response = self.session.get(image_url, timeout=60)
                    if img_response.status_code == 200:
                        # 保存图像到文件
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f'telescope_art_{timestamp}_openai_dalle.png'
                        filepath = os.path.join('outputs', 'images', filename)
                        
                        # 确保目录存在
                        os.makedirs(os.path.dirname(filepath), exist_ok=True)
                        
                        # 保存图像
                        with open(filepath, 'wb') as f:
                            f.write(img_response.content)
                        
                        print(f"💾 OpenAI图像已保存: {filename}")
                        return filepath
                    else:
                        print(f"❌ 下载OpenAI图像失败: {img_response.status_code}")
                        return None
                else:
                    print("❌ OpenAI DALL-E响应中没有图像数据")
                    return None
            else:
                print(f"❌ OpenAI DALL-E错误: {response.status_code}")
                if response.text:
                    print(f"   错误详情: {response.text}")
                return None
        except Exception as e:
            print(f"❌ OpenAI DALL-E请求错误: {e}")
            return None
    
    def _process_ml_prediction(self, prediction, weather_features):
        """处理ML预测结果"""
        try:
            # 从API响应中提取风格信息
            if isinstance(prediction, list) and len(prediction) > 0:
                generated_text = prediction[0].get('generated_text', '')
            elif isinstance(prediction, dict):
                generated_text = prediction.get('generated_text', str(prediction))
            else:
                generated_text = str(prediction)
            
            # 简单的关键词匹配来确定风格
            style_keywords = {
                'impressionist': ['impressionist', 'impressionism', 'monet', 'soft'],
                'realistic': ['realistic', 'realism', 'detailed', 'photographic'],
                'abstract': ['abstract', 'modern', 'geometric', 'conceptual'],
                'romantic': ['romantic', 'dreamy', 'ethereal', 'soft'],
                'dramatic': ['dramatic', 'dark', 'stormy', 'intense']
            }
            
            detected_style = 'impressionist'  # 默认风格
            for style, keywords in style_keywords.items():
                if any(keyword in generated_text.lower() for keyword in keywords):
                    detected_style = style
                    break
            
            return {
                'prediction_type': f'{detected_style.title()} Landscape',
                'confidence': 0.85,  # 模拟置信度
                'style_recommendation': detected_style,
                'raw_prediction': generated_text,
                'weather_influence': self._analyze_weather_influence(weather_features)
            }
            
        except Exception as e:
            print(f"❌ 处理ML预测错误: {e}")
            return self._fallback_style_prediction(weather_features, {})
    
    def _fallback_style_prediction(self, weather_features, location_info):
        """备用风格预测算法"""
        temp = weather_features.get('temperature', 15)
        weather_main = weather_features.get('weather_main', 'Clear')
        humidity = weather_features.get('humidity', 50)
        
        # 基于天气条件的规则
        if weather_main in ['Rain', 'Drizzle', 'Thunderstorm']:
            style = 'dramatic rainy landscape'
            recommendation = 'dark colors, stormy atmosphere'
        elif weather_main in ['Snow']:
            style = 'winter impressionist scene'
            recommendation = 'cool tones, soft textures'
        elif temp > 25:
            style = 'bright summer landscape'
            recommendation = 'warm colors, vibrant lighting'
        elif temp < 5:
            style = 'cool winter scene'
            recommendation = 'cool tones, crisp details'
        else:
            style = 'temperate landscape'
            recommendation = 'balanced colors, natural lighting'
        
        return {
            'prediction_type': style.title(),
            'confidence': 0.75,
            'style_recommendation': recommendation,
            'weather_influence': f"Based on {weather_main} at {temp}°C"
        }
    
    def _analyze_weather_influence(self, weather_features):
        """分析天气对艺术风格的影响"""
        influences = []
        
        temp = weather_features.get('temperature', 15)
        if temp > 25:
            influences.append("warm temperature suggests vibrant colors")
        elif temp < 5:
            influences.append("cold temperature suggests cool tones")
        
        humidity = weather_features.get('humidity', 50)
        if humidity > 80:
            influences.append("high humidity suggests soft, misty atmosphere")
        elif humidity < 30:
            influences.append("low humidity suggests clear, crisp details")
        
        return "; ".join(influences) if influences else "moderate conditions"
    
    def _save_generated_image(self, image_data, source):
        """保存生成的图像"""
        try:
            # 确保输出目录存在
            output_dir = self.config_manager.get('output_settings.local_image_directory', './generated_images/')
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"telescope_art_{timestamp}_{source}.png"
            filepath = os.path.join(output_dir, filename)
            
            # 保存图像
            if isinstance(image_data, bytes):
                with open(filepath, 'wb') as f:
                    f.write(image_data)
            else:
                # 如果是PIL Image对象
                image_data.save(filepath, 'PNG')
            
            print(f"✅ 图像已保存: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ 保存图像错误: {e}")
            return None
    
    def _create_fallback_visualization(self, weather_data, location_info):
        """创建备用可视化 - 修复编码问题"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.font_manager as fm
            
            # 创建图像
            fig, ax = plt.subplots(figsize=(8, 6))
            
            # 获取天气数据
            current_weather = weather_data.get('current_weather', {}) if weather_data else {}
            temp = current_weather.get('temperature', 15) if current_weather else 15
            humidity = current_weather.get('humidity', 60) if current_weather else 60
            weather_main = current_weather.get('weather_main', 'Clear') if current_weather else 'Clear'
            
            # 绘制基础信息（使用英文避免编码问题）
            ax.text(0.5, 0.7, f'Temperature: {temp}°C', ha='center', va='center', fontsize=16, transform=ax.transAxes)
            ax.text(0.5, 0.5, f'Humidity: {humidity}%', ha='center', va='center', fontsize=14, transform=ax.transAxes)
            ax.text(0.5, 0.3, f'Weather: {weather_main}', ha='center', va='center', fontsize=14, transform=ax.transAxes)
            ax.text(0.5, 0.1, 'Obscura No.7 Telescope', ha='center', va='center', fontsize=12, transform=ax.transAxes)
            
            # 设置背景色
            if weather_main == 'Clear':
                ax.set_facecolor('#87CEEB')  # 天蓝色
            elif weather_main == 'Rain':
                ax.set_facecolor('#708090')  # 灰色
            else:
                ax.set_facecolor('#D3D3D3')  # 浅灰色
            
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            
            # 使用英文文件名避免编码问题
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'telescope_fallback_{timestamp}.png'
            filepath = os.path.join('outputs', 'images', filename)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # 保存图像
            plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            
            print(f"💾 备用可视化已保存: {filename}")
            return filepath
            
        except Exception as e:
            print(f"❌ 创建备用可视化错误: {e}")
            # 创建一个最简单的文本文件作为占位符
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'telescope_placeholder_{timestamp}.txt'
            filepath = os.path.join('outputs', 'images', filename)
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Telescope session {timestamp}\nFallback visualization failed")
            
            return filepath


if __name__ == "__main__":
    # 测试用例
    print("☁️ 云端API客户端测试")
    print("=" * 40)
    
    # 使用配置管理器
    client = CloudAPIClient()
    
    # 模拟天气数据进行测试
    mock_weather_features = {
        'temperature': 18.5,
        'humidity': 65,
        'pressure': 1013,
        'weather_main': 'Clouds',
        'weather_description': '多云'
    }
    
    mock_location = {
        'latitude': 51.5074,
        'longitude': -0.1278,
        'formatted_coords': '51.5074, -0.1278'
    }
    
    mock_weather_data = {
        'current_weather': mock_weather_features
    }
    
    print("🧪 测试风格预测...")
    style_prediction = client.predict_art_style(mock_weather_features, mock_location)
    print(f"   风格预测: {style_prediction}")
    
    print("\n🧪 测试图像生成...")
    image_path = client.generate_artwork(style_prediction, mock_weather_data, mock_location)
    print(f"   生成图像: {image_path}")
    
    if image_path:
        print("\n🧪 测试网站上传...")
        metadata = {
            'coordinates': mock_location,
            'weather': mock_weather_features,
            'style': style_prediction
        }
        upload_result = client.upload_to_website(image_path, metadata)
        print(f"   上传结果: {upload_result}")
    
    print("\n✅ 云端API客户端测试完成")
    print("\n📝 注意：要使用真实API，请在config.json中配置有效的API密钥")
