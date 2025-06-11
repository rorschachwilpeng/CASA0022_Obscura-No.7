#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obscura No.7 - 1.1 本地环境搭建与Mock流程验证
Local Environment Setup & Mock Process Validation

功能：
1. 搭建本地Python环境，安装必要依赖 (OpenAI, requests, flask等)
2. 实现OpenWeather API数据获取模块 (基于已有代码)
3. 创建Mock ML模型 (简单的线性回归或随机预测)
4. 集成OpenAI DALL-E API进行AI图片生成
5. 本地测试完整流程：环境数据 → Mock预测 → AI图片生成 → 本地保存
"""

import os
import sys
import json
import time
import random
import requests
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple
import logging

# 添加项目根目录到路径，确保能找到.env文件
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 与weather_art_generator.py保持一致的依赖加载方式
try:
    from dotenv import load_dotenv
    # 从项目根目录加载.env文件
    load_dotenv(os.path.join(project_root, '.env'))
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("⚠️  python-dotenv库未安装，请运行: pip install python-dotenv")

# API密钥（从环境变量中获取，与weather_art_generator.py保持一致）
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 尝试导入可选依赖，如果没有安装会给出提示
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  OpenAI库未安装，请运行: pip install openai")

try:
    from PIL import Image
    import io
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️  PIL库未安装，请运行: pip install Pillow")

try:
    from sklearn.linear_model import LinearRegression
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("⚠️  scikit-learn库未安装，请运行: pip install scikit-learn")

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class EnvironmentalData:
    """环境数据结构"""
    latitude: float
    longitude: float
    temperature: float
    humidity: float
    pressure: float
    wind_speed: float
    weather_description: str
    timestamp: str
    location_name: str = ""

@dataclass
class PredictionResult:
    """预测结果结构"""
    predicted_temperature: float
    predicted_humidity: float
    predicted_weather_condition: str
    confidence_score: float
    prediction_timestamp: str
    model_version: str = "mock_v1.0"

class DependencyChecker:
    """依赖检查器"""
    
    @staticmethod
    def check_all_dependencies():
        """检查所有必要依赖"""
        logger.info("🔍 检查Python依赖...")
        
        required_packages = {
            'requests': 'pip install requests',
            'numpy': 'pip install numpy',
            'openai': 'pip install openai',
            'Pillow': 'pip install Pillow',
            'scikit-learn': 'pip install scikit-learn',
            'flask': 'pip install flask',
            'python-dotenv': 'pip install python-dotenv'
        }
        
        missing_packages = []
        
        for package, install_cmd in required_packages.items():
            try:
                if package == 'Pillow':
                    import PIL
                elif package == 'scikit-learn':
                    import sklearn
                elif package == 'python-dotenv':
                    import dotenv
                else:
                    __import__(package)
                logger.info(f"✅ {package} 已安装")
            except ImportError:
                logger.warning(f"❌ {package} 未安装")
                missing_packages.append((package, install_cmd))
        
        if missing_packages:
            logger.error("缺少以下依赖包：")
            for package, cmd in missing_packages:
                logger.error(f"  {cmd}")
            return False
        
        logger.info("✅ 所有依赖检查完成！")
        return True
    
    @staticmethod
    def create_requirements_file():
        """创建requirements.txt文件"""
        requirements = [
            "requests>=2.31.0",
            "numpy>=1.24.0",
            "openai>=1.3.0",
            "Pillow>=10.0.0",
            "scikit-learn>=1.3.0",
            "flask>=2.3.0",
            "python-dotenv>=1.0.0"
        ]
        
        with open("requirements.txt", "w") as f:
            f.write("\n".join(requirements))
        
        logger.info("📝 requirements.txt 文件已创建")

def check_api_keys():
    """检查API密钥是否已正确设置"""
    logger.info("🔑 检查API密钥配置...")
    
    issues = []
    
    if not OPENWEATHER_API_KEY:
        issues.append("OPENWEATHER_API_KEY 未设置")
    else:
        logger.info("✅ OpenWeather API密钥已设置")
    
    if not OPENAI_API_KEY:
        issues.append("OPENAI_API_KEY 未设置 (将使用模拟图片生成)")
    else:
        logger.info("✅ OpenAI API密钥已设置")
    
    if issues:
        logger.warning("⚠️  API密钥配置问题：")
        for issue in issues:
            logger.warning(f"   - {issue}")
        
        if not OPENWEATHER_API_KEY:
            logger.info("\n📖 请检查项目根目录的.env文件是否包含:")
            logger.info("   OPENWEATHER_API_KEY=你的密钥")
            logger.info("   OPENAI_API_KEY=你的密钥")
            return False
    
    logger.info("✅ API密钥配置检查完成！")
    return True

class EnvironmentDataCollector:
    """环境数据收集器"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"
    
    def get_weather_data(self, latitude: float, longitude: float) -> Optional[EnvironmentalData]:
        """获取指定坐标的天气数据"""
        if not self.api_key or self.api_key == "mock_key":
            logger.info("🎭 API密钥未配置，使用模拟数据")
            return None
            
        try:
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': self.api_key,
                'units': 'metric'  # 摄氏度
            }
            
            logger.info(f"🌐 正在获取坐标 ({latitude}, {longitude}) 的天气数据...")
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                env_data = EnvironmentalData(
                    latitude=latitude,
                    longitude=longitude,
                    temperature=data['main']['temp'],
                    humidity=data['main']['humidity'],
                    pressure=data['main']['pressure'],
                    wind_speed=data.get('wind', {}).get('speed', 0),
                    weather_description=data['weather'][0]['description'],
                    timestamp=datetime.now().isoformat(),
                    location_name=data.get('name', 'Unknown')
                )
                
                logger.info(f"✅ 天气数据获取成功: {env_data.location_name}")
                return env_data
            
            else:
                logger.error(f"❌ API请求失败: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 获取天气数据时出错: {e}")
            return None
    
    def create_mock_data(self, latitude: float, longitude: float) -> EnvironmentalData:
        """创建模拟天气数据（当API不可用时）"""
        logger.info("🎭 创建模拟天气数据...")
        
        return EnvironmentalData(
            latitude=latitude,
            longitude=longitude,
            temperature=random.uniform(10, 25),
            humidity=random.uniform(40, 80),
            pressure=random.uniform(1000, 1020),
            wind_speed=random.uniform(0, 10),
            weather_description="clear sky",
            timestamp=datetime.now().isoformat(),
            location_name="Mock Location"
        )

class MockMLPredictor:
    """Mock机器学习预测器"""
    
    def __init__(self):
        self.model_version = "mock_v1.0"
        self.is_trained = False
        
        # 如果sklearn可用，创建一个简单的线性回归模型
        if SKLEARN_AVAILABLE:
            self.temperature_model = LinearRegression()
            self.humidity_model = LinearRegression()
            self._train_mock_models()
    
    def _train_mock_models(self):
        """训练简单的Mock模型"""
        logger.info("🤖 训练Mock ML模型...")
        
        # 生成一些模拟训练数据
        n_samples = 100
        
        # 特征：当前温度、湿度、气压、小时
        current_temp = np.random.uniform(10, 30, n_samples)
        current_humidity = np.random.uniform(30, 90, n_samples)
        current_pressure = np.random.uniform(1000, 1020, n_samples)
        hour_of_day = np.random.randint(0, 24, n_samples)
        
        X = np.column_stack([current_temp, current_humidity, current_pressure, hour_of_day])
        
        # 目标：未来温度和湿度（加一些随机变化）
        future_temp = current_temp + np.random.normal(0, 2, n_samples)
        future_humidity = current_humidity + np.random.normal(0, 5, n_samples)
        
        # 训练模型
        self.temperature_model.fit(X, future_temp)
        self.humidity_model.fit(X, future_humidity)
        
        self.is_trained = True
        logger.info("✅ Mock ML模型训练完成")
    
    def predict_weather(self, env_data: EnvironmentalData, hours_ahead: int = 24) -> PredictionResult:
        """预测未来天气"""
        logger.info(f"🔮 预测 {hours_ahead} 小时后的天气...")
        
        if SKLEARN_AVAILABLE and self.is_trained:
            # 使用训练好的模型进行预测
            current_hour = datetime.now().hour
            future_hour = (current_hour + hours_ahead) % 24
            
            features = np.array([[
                env_data.temperature,
                env_data.humidity,
                env_data.pressure,
                future_hour
            ]])
            
            predicted_temp = self.temperature_model.predict(features)[0]
            predicted_humidity = self.humidity_model.predict(features)[0]
            confidence = random.uniform(0.7, 0.9)  # Mock confidence
            
        else:
            # 简单的基于规则的预测
            temp_change = random.uniform(-3, 3)
            humidity_change = random.uniform(-10, 10)
            
            predicted_temp = env_data.temperature + temp_change
            predicted_humidity = max(0, min(100, env_data.humidity + humidity_change))
            confidence = random.uniform(0.6, 0.8)
        
        # 基于温度预测天气条件
        if predicted_temp < 0:
            weather_condition = "snow"
        elif predicted_temp < 10:
            weather_condition = "cold and cloudy"
        elif predicted_temp < 20:
            weather_condition = "mild"
        elif predicted_humidity > 80:
            weather_condition = "humid and warm"
        else:
            weather_condition = "clear and warm"
        
        result = PredictionResult(
            predicted_temperature=round(predicted_temp, 1),
            predicted_humidity=round(predicted_humidity, 1),
            predicted_weather_condition=weather_condition,
            confidence_score=round(confidence, 2),
            prediction_timestamp=datetime.now().isoformat(),
            model_version=self.model_version
        )
        
        logger.info(f"✅ 预测完成: {result.predicted_temperature}°C, {result.predicted_weather_condition}")
        return result
    
    def save_model(self, filepath: str):
        """保存模型"""
        if SKLEARN_AVAILABLE and self.is_trained:
            model_data = {
                'temperature_model': self.temperature_model,
                'humidity_model': self.humidity_model,
                'model_version': self.model_version,
                'timestamp': datetime.now().isoformat()
            }
            joblib.dump(model_data, filepath)
            logger.info(f"💾 模型已保存到: {filepath}")

class AIImageGenerator:
    """AI图片生成器"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = None
        
        if api_key and OPENAI_AVAILABLE:
            self.client = OpenAI(api_key=api_key)
    
    def create_weather_prompt(self, env_data: EnvironmentalData, prediction: PredictionResult) -> str:
        """创建基于天气数据的图片生成prompt"""
        
        location_desc = f"in {env_data.location_name}" if env_data.location_name != "Unknown" else "in a distant location"
        
        prompt = f"""A realistic landscape photograph {location_desc}, showing the future weather conditions. 
        The scene depicts {prediction.predicted_weather_condition} weather with a temperature of {prediction.predicted_temperature}°C 
        and humidity of {prediction.predicted_humidity}%. 
        
        Current conditions: {env_data.weather_description}, {env_data.temperature}°C
        Predicted conditions: {prediction.predicted_weather_condition}, {prediction.predicted_temperature}°C
        
        The image should be atmospheric and moody, capturing the essence of the predicted weather. 
        Style: photorealistic, high quality, professional photography, dramatic lighting"""
        
        return prompt
    
    def generate_image(self, env_data: EnvironmentalData, prediction: PredictionResult) -> Optional[str]:
        """生成AI图片"""
        
        if not self.client:
            logger.warning("⚠️  OpenAI客户端未配置，创建模拟图片...")
            return self._create_mock_image(env_data, prediction)
        
        try:
            prompt = self.create_weather_prompt(env_data, prediction)
            logger.info("🎨 正在生成AI图片...")
            logger.info(f"Prompt: {prompt[:100]}...")
            
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            
            image_url = response.data[0].url
            logger.info("✅ AI图片生成成功")
            
            # 下载并保存图片
            return self._download_and_save_image(image_url, env_data, prediction)
            
        except Exception as e:
            logger.error(f"❌ AI图片生成失败: {e}")
            return self._create_mock_image(env_data, prediction)
    
    def _download_and_save_image(self, image_url: str, env_data: EnvironmentalData, prediction: PredictionResult) -> str:
        """下载并保存图片"""
        try:
            response = requests.get(image_url, timeout=30)
            
            if response.status_code == 200:
                # 创建文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"weather_prediction_{timestamp}_{prediction.predicted_temperature}C.png"
                filepath = os.path.join("generated_images", filename)
                
                # 确保目录存在
                os.makedirs("generated_images", exist_ok=True)
                
                # 保存图片
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"💾 图片已保存: {filepath}")
                return filepath
            else:
                logger.error(f"❌ 图片下载失败: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 保存图片时出错: {e}")
            return None
    
    def _create_mock_image(self, env_data: EnvironmentalData, prediction: PredictionResult) -> str:
        """创建模拟图片"""
        if not PIL_AVAILABLE:
            logger.warning("⚠️  PIL不可用，跳过图片创建")
            return None
        
        try:
            # 创建一个简单的彩色图片作为placeholder
            img = Image.new('RGB', (512, 512), color='lightblue')
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"mock_weather_prediction_{timestamp}_{prediction.predicted_temperature}C.png"
            filepath = os.path.join("generated_images", filename)
            
            os.makedirs("generated_images", exist_ok=True)
            img.save(filepath)
            
            logger.info(f"🎭 模拟图片已创建: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ 创建模拟图片失败: {e}")
            return None

class WorkflowOrchestrator:
    """工作流程协调器"""
    
    def __init__(self, openweather_api_key: str, openai_api_key: Optional[str] = None):
        self.data_collector = EnvironmentDataCollector(openweather_api_key)
        self.ml_predictor = MockMLPredictor()
        self.image_generator = AIImageGenerator(openai_api_key)
        
        # 创建输出目录
        os.makedirs("workflow_outputs", exist_ok=True)
        os.makedirs("generated_images", exist_ok=True)
    
    def run_complete_workflow(self, latitude: float, longitude: float, hours_ahead: int = 24) -> Dict[str, Any]:
        """运行完整的工作流程"""
        logger.info("🚀 开始完整工作流程...")
        
        workflow_start_time = time.time()
        
        # 第一步：获取环境数据
        logger.info("📊 步骤1: 获取环境数据")
        env_data = self.data_collector.get_weather_data(latitude, longitude)
        
        if not env_data:
            logger.info("使用模拟数据...")
            env_data = self.data_collector.create_mock_data(latitude, longitude)
        
        # 第二步：ML预测
        logger.info("🤖 步骤2: 机器学习预测")
        prediction = self.ml_predictor.predict_weather(env_data, hours_ahead)
        
        # 第三步：AI图片生成
        logger.info("🎨 步骤3: AI图片生成")
        image_path = self.image_generator.generate_image(env_data, prediction)
        
        # 第四步：保存结果
        logger.info("💾 步骤4: 保存工作流结果")
        workflow_result = {
            'environmental_data': {
                'latitude': env_data.latitude,
                'longitude': env_data.longitude,
                'temperature': env_data.temperature,
                'humidity': env_data.humidity,
                'pressure': env_data.pressure,
                'wind_speed': env_data.wind_speed,
                'weather_description': env_data.weather_description,
                'location_name': env_data.location_name,
                'timestamp': env_data.timestamp
            },
            'prediction_result': {
                'predicted_temperature': prediction.predicted_temperature,
                'predicted_humidity': prediction.predicted_humidity,
                'predicted_weather_condition': prediction.predicted_weather_condition,
                'confidence_score': prediction.confidence_score,
                'prediction_timestamp': prediction.prediction_timestamp,
                'model_version': prediction.model_version
            },
            'generated_image': {
                'image_path': image_path,
                'generation_method': 'openai' if self.image_generator.client else 'mock'
            },
            'workflow_metadata': {
                'execution_time_seconds': time.time() - workflow_start_time,
                'hours_ahead': hours_ahead,
                'workflow_version': '1.1.0'
            }
        }
        
        # 保存结果到JSON文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_filename = f"workflow_result_{timestamp}.json"
        result_filepath = os.path.join("workflow_outputs", result_filename)
        
        with open(result_filepath, 'w', encoding='utf-8') as f:
            json.dump(workflow_result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ 工作流程完成！结果保存到: {result_filepath}")
        logger.info(f"⏱️  总耗时: {workflow_result['workflow_metadata']['execution_time_seconds']:.2f}秒")
        
        return workflow_result
    
    def print_workflow_summary(self, result: Dict[str, Any]):
        """打印工作流程摘要"""
        print("\n" + "="*60)
        print("🔭 Obscura No.7 - 工作流程执行摘要")
        print("="*60)
        
        env = result['environmental_data']
        pred = result['prediction_result']
        img = result['generated_image']
        meta = result['workflow_metadata']
        
        print(f"📍 位置: {env['location_name']} ({env['latitude']}, {env['longitude']})")
        print(f"🌡️  当前天气: {env['weather_description']}, {env['temperature']}°C")
        print(f"💨 湿度: {env['humidity']}%, 气压: {env['pressure']}hPa")
        print(f"")
        print(f"🔮 {meta['hours_ahead']}小时后预测:")
        print(f"🌡️  温度: {pred['predicted_temperature']}°C")
        print(f"💨 湿度: {pred['predicted_humidity']}%")
        print(f"☁️  天气状况: {pred['predicted_weather_condition']}")
        print(f"🎯 置信度: {pred['confidence_score']}")
        print(f"")
        print(f"🎨 生成图片: {img['image_path'] or '未生成'}")
        print(f"⚙️  生成方式: {img['generation_method']}")
        print(f"⏱️  执行时间: {meta['execution_time_seconds']:.2f}秒")
        print("="*60)

def main():
    """主函数"""
    print("🔭 Obscura No.7 - 1.1 本地环境搭建与Mock流程验证")
    print("="*60)
    
    # 1. 检查依赖
    dependency_checker = DependencyChecker()
    if not dependency_checker.check_all_dependencies():
        dependency_checker.create_requirements_file()
        print("\n请先安装依赖包：pip install -r requirements.txt")
        return
    
    # 2. 检查API密钥配置
    if not check_api_keys():
        print("\n⚠️  请检查项目根目录的.env文件配置")
        return
    
    # 3. 初始化工作流程
    # 即使没有OpenAI密钥也继续，会使用模拟图片生成
    orchestrator = WorkflowOrchestrator(OPENWEATHER_API_KEY, OPENAI_API_KEY)
    
    # 4. 测试位置 (伦敦市中心)
    test_latitude = 51.5074
    test_longitude = -0.1278
    
    print(f"\n🧪 测试坐标: ({test_latitude}, {test_longitude})")
    
    # 5. 运行完整工作流程
    try:
        result = orchestrator.run_complete_workflow(
            latitude=test_latitude,
            longitude=test_longitude,
            hours_ahead=24
        )
        
        # 6. 显示结果摘要
        orchestrator.print_workflow_summary(result)
        
        # 7. 保存模型（如果可用）
        try:
            orchestrator.ml_predictor.save_model("workflow_outputs/mock_ml_model.joblib")
        except Exception as e:
            logger.warning(f"模型保存失败: {e}")
        
        print("\n✅ 1.1 本地环境搭建与Mock流程验证 - 完成！")
        print("📁 输出文件位置:")
        print("   - workflow_outputs/")
        print("   - generated_images/")
        
    except Exception as e:
        logger.error(f"❌ 工作流程执行失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 