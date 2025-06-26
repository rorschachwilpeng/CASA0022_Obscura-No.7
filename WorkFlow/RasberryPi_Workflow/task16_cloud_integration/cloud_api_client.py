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
from config_manager import ConfigManager

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
        
        # 调试：显示API密钥状态
        print(f"🔑 OpenAI API密钥状态: {'已配置' if self.openai_key and self.openai_key != 'YOUR_OPENAI_API_KEY_HERE' else '未配置'}")
        if self.openai_key and self.openai_key != 'YOUR_OPENAI_API_KEY_HERE':
            print(f"   OpenAI密钥前缀: {self.openai_key[:10]}...")
        
        # API端点
        self.endpoints = self.config_manager.get('api_endpoints', {})
        
        # 重试设置
        self.max_retries = self.config_manager.get('retry_settings.max_retries', 3)
        self.retry_delay = self.config_manager.get('retry_settings.retry_delay_seconds', 2)
        self.timeout = self.config_manager.get('retry_settings.timeout_seconds', 30)
    
    def predict_art_style(self, weather_features, location_info):
        """使用真实ML模型预测艺术风格"""
        print("🤖 调用真实ML预测API...")
        
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
        """使用真实API生成艺术作品"""
        print("🎨 调用真实图像生成API...")
        
        # 构建详细的艺术提示词
        art_prompt = self._build_art_prompt(style_prediction, weather_data, location_info)
        
        # 方案1: 使用OpenAI DALL-E (优先)
        if self.openai_key and self.openai_key != "YOUR_OPENAI_API_KEY_HERE":
            image_data = self._call_openai_dalle(art_prompt)
            if image_data:
                return self._save_generated_image(image_data, "openai_dalle")
        
        # 方案2: 使用Stability AI
        if self.stability_key and self.stability_key != "YOUR_STABILITY_AI_API_KEY_HERE":
            image_data = self._call_stability_ai(art_prompt)
            if image_data:
                return self._save_generated_image(image_data, "stability_ai")
        
        # 方案3: 使用HuggingFace图像生成
        if self.huggingface_key and self.huggingface_key != "YOUR_HUGGINGFACE_API_KEY_HERE":
            image_data = self._call_huggingface_image_generation(art_prompt)
            if image_data:
                return self._save_generated_image(image_data, "huggingface")
        
        # 方案4: 备用 - 生成基础艺术图像
        print("⚠️ 图像生成API不可用，创建基础可视化...")
        return self._create_fallback_visualization(weather_data, location_info)
    
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
        """上传环境数据到API"""
        try:
            env_upload_url = self.endpoints.get('environmental_upload_url', 'http://localhost:5000/api/v1/environmental/upload')
            
            # 构建环境数据payload
            env_payload = {
                "coordinates": metadata.get('coordinates', {}),
                "weather_data": metadata.get('weather', {}),
                "timestamp": metadata.get('timestamp', datetime.now().isoformat()),
                "source": "obscura_telescope_workflow"
            }
            
            response = self.session.post(
                env_upload_url,
                json=env_payload,
                headers={'Content-Type': 'application/json'},
                timeout=self.timeout
            )
            
            if response.status_code == 201:
                result = response.json()
                print(f"✅ 环境数据上传成功: ID {result.get('environmental_data', {}).get('id', 'N/A')}")
                return result
            else:
                print(f"❌ 环境数据上传失败: {response.status_code}")
                if response.text:
                    print(f"   错误详情: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 环境数据上传错误: {e}")
            return None
    
    def _upload_image_file(self, image_path, metadata, env_data_result):
        """上传图像文件到API"""
        try:
            # 获取prediction_id (如果有环境数据ID就用它，否则用时间戳)
            prediction_id = 1  # 默认预测ID
            if env_data_result and env_data_result.get('environmental_data', {}).get('id'):
                prediction_id = env_data_result['environmental_data']['id']
            
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
        """构建图像生成的详细提示词"""
        style = style_prediction.get('style_recommendation', 'impressionist landscape')
        temp = weather_data.get('current_weather', {}).get('temperature', 15)
        weather_desc = weather_data.get('current_weather', {}).get('weather_description', 'clear sky')
        
        # 基础提示词
        base_prompt = self.config_manager.get('image_generation.style_prompt_prefix', 
                                     'A beautiful artistic interpretation of a future landscape showing')
        
        # 详细艺术提示词
        art_prompt = f"""{base_prompt} {weather_desc} at {temp}°C, painted in {style} style. 
        The scene should evoke the feeling of {weather_desc} with appropriate lighting and atmosphere. 
        High quality, professional artwork, detailed composition, masterpiece quality."""
        
        return art_prompt
    
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
        """调用OpenAI DALL-E生成图像"""
        if not self.openai_key or self.openai_key == "YOUR_OPENAI_API_KEY_HERE":
            return None
        
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
            response = self.session.post(api_url, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                data = response.json()
                if data.get('data') and len(data['data']) > 0:
                    image_url = data['data'][0]['url']
                    # 下载图像
                    img_response = self.session.get(image_url, timeout=30)
                    if img_response.status_code == 200:
                        return img_response.content
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
        """创建备用可视化图像"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # 创建基础图像
            width, height = 1024, 1024
            img = Image.new('RGB', (width, height), color='skyblue')
            draw = ImageDraw.Draw(img)
            
            # 基于天气数据选择颜色
            current = weather_data.get('current_weather', {})
            temp = current.get('temperature', 15)
            weather_desc = current.get('weather_description', 'clear')
            
            # 绘制简单的可视化
            if 'rain' in weather_desc.lower():
                # 雨天 - 灰蓝色调
                img = Image.new('RGB', (width, height), color='#4A90E2')
            elif 'cloud' in weather_desc.lower():
                # 多云 - 灰色调
                img = Image.new('RGB', (width, height), color='#B0C4DE')
            elif temp > 25:
                # 炎热 - 暖色调
                img = Image.new('RGB', (width, height), color='#FFB84D')
            else:
                # 默认 - 蓝色调
                img = Image.new('RGB', (width, height), color='#87CEEB')
            
            draw = ImageDraw.Draw(img)
            
            # 添加文本信息
            try:
                font = ImageFont.load_default()
            except:
                font = None
            
            text_lines = [
                f"Temperature: {temp}°C",
                f"Weather: {weather_desc}",
                f"Coordinates: {location_info.get('formatted_coords', 'N/A')}",
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            ]
            
            y_offset = 50
            for line in text_lines:
                draw.text((50, y_offset), line, fill='white', font=font)
                y_offset += 40
            
            # 保存图像
            output_dir = self.config_manager.get('output_settings.local_image_directory', './generated_images/')
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"telescope_fallback_{timestamp}.png"
            filepath = os.path.join(output_dir, filename)
            
            img.save(filepath, 'PNG')
            print(f"✅ 备用可视化已保存: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ 创建备用可视化错误: {e}")
            return None

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
