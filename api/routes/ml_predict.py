#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ML Prediction API Routes - 机器学习预测API端点
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
import sys
import os
import traceback
from pathlib import Path
import numpy as np
import joblib

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from api.schemas import validate_ml_input
from api.utils import validate_json_input, ml_prediction_response, error_response

logger = logging.getLogger(__name__)

# 创建蓝图
ml_bp = Blueprint('ml_predict', __name__, url_prefix='/api/v1/ml')

# 全局模型实例
_environmental_model = None

class LocalEnvironmentalPredictor:
    """本地环境预测器 - 加载pkl模型文件"""
    
    def __init__(self, model_data=None):
        self.model_data = model_data
        self.temperature_model = None
        self.humidity_model = None
        self.pressure_model = None
        self.scaler = None
        self.version = "1.0.0-local"
        self.model_loaded = False
        
        # 城市映射
        self.city_centers = {
            'London': {'lat': 51.5074, 'lon': -0.1278},
            'Manchester': {'lat': 53.4808, 'lon': -2.2426},
            'Edinburgh': {'lat': 55.9533, 'lon': -3.1883}
        }
        
        # 处理模型数据
        if model_data:
            self._process_model_data(model_data)
        
        # 模型信息
        self.model_info = {
            "version": self.version,
            "type": "local_sklearn" if self.model_loaded else "fallback",
            "description": "Local Environmental Prediction Model",
            "training_data_points": "~10,000",
            "r2_score": 0.9797 if self.model_loaded else 0.75,
            "features": ["latitude", "longitude", "month", "seasonal_features", "city_encoding"]
        }
    
    def _process_model_data(self, model_data):
        """处理加载的模型数据"""
        try:
            if isinstance(model_data, dict):
                # 提取各个模型组件
                self.temperature_model = model_data.get('temperature_model')
                self.humidity_model = model_data.get('humidity_model')
                self.pressure_model = model_data.get('pressure_model')
                self.scaler = model_data.get('scaler')
                
                # 检查是否有主模型（向后兼容）
                if not self.temperature_model and 'model' in model_data:
                    self.temperature_model = model_data.get('model')
                
                # 验证模型是否存在
                if self.temperature_model and hasattr(self.temperature_model, 'predict'):
                    self.model_loaded = True
                    logger.info("✅ 模型数据处理成功")
                    logger.info(f"   温度模型: {type(self.temperature_model)}")
                    logger.info(f"   湿度模型: {type(self.humidity_model) if self.humidity_model else 'None'}")
                    logger.info(f"   气压模型: {type(self.pressure_model) if self.pressure_model else 'None'}")
                    logger.info(f"   标准化器: {type(self.scaler) if self.scaler else 'None'}")
                else:
                    raise Exception("未找到有效的temperature_model")
                
            else:
                # 单个模型对象
                self.temperature_model = model_data
                self.humidity_model = None
                self.pressure_model = None
                self.scaler = None
                self.model_loaded = True
                logger.info("✅ 单个模型加载成功")
                
        except Exception as e:
            logger.error(f"❌ 模型数据处理失败: {e}")
            self.model_loaded = False
            self.temperature_model = None
            self.humidity_model = None
            self.pressure_model = None
    
    def get_closest_city(self, lat, lon):
        """获取最接近的城市"""
        min_distance = float('inf')
        closest_city = "London"
        
        for city, center in self.city_centers.items():
            distance = np.sqrt((lat - center['lat'])**2 + (lon - center['lon'])**2)
            if distance < min_distance:
                min_distance = distance
                closest_city = city
        
        return closest_city
    
    def prepare_features(self, latitude, longitude, month, future_years=0):
        """准备特征向量（与训练时保持一致）"""
        # 基础特征（与训练时相同）
        features = [
            latitude,
            longitude,
            month,
            np.sin(2 * np.pi * (month - 1) / 12),  # 注意：训练时使用的是(month-1)
            np.cos(2 * np.pi * (month - 1) / 12),
            # 注意：训练时没有future_years特征
        ]
        
        # 城市编码（3个独热编码）
        closest_city = self.get_closest_city(latitude, longitude)
        city_encodings = {
            'London': [1, 0, 0],
            'Manchester': [0, 1, 0],
            'Edinburgh': [0, 0, 1]
        }
        
        city_code = city_encodings.get(closest_city, [1, 0, 0])  # 默认伦敦
        features.extend(city_code)
        
        return np.array(features).reshape(1, -1), closest_city
    
    def predict(self, latitude, longitude, month=None, future_years=0):
        """进行预测"""
        if month is None:
            month = datetime.now().month
        
        # 准备特征
        features, closest_city = self.prepare_features(latitude, longitude, month, future_years)
        
        # 进行预测
        if self.model_loaded and self.temperature_model and hasattr(self.temperature_model, 'predict'):
            try:
                # 如果有scaler，进行标准化
                processed_features = features
                if self.scaler:
                    processed_features = self.scaler.transform(features)
                
                # 使用训练好的模型预测温度
                temperature = float(self.temperature_model.predict(processed_features)[0])
                
                # 使用训练好的模型预测湿度（如果存在）
                if self.humidity_model and hasattr(self.humidity_model, 'predict'):
                    humidity = float(self.humidity_model.predict(processed_features)[0])
                else:
                    humidity = self._predict_humidity(temperature, month)
                
                # 使用训练好的模型预测气压（如果存在）
                if self.pressure_model and hasattr(self.pressure_model, 'predict'):
                    pressure = float(self.pressure_model.predict(processed_features)[0])
                else:
                    pressure = self._predict_pressure(latitude, temperature)
                
                # 未来预测调整（基于训练代码的逻辑）
                if future_years > 0:
                    # 气候变化趋势：温度上升，湿度变化
                    temperature += future_years * 0.2  # 每年0.2°C增长
                    humidity *= (1 + future_years * 0.01)  # 轻微湿度变化
                
                # 合理性检查
                temperature = max(-10, min(40, temperature))
                humidity = max(20, min(95, humidity))
                pressure = max(980, min(1040, pressure))
                
                confidence = 0.95
                model_type = "trained_sklearn"
                
                logger.info(f"✅ 使用训练模型预测成功: T={temperature:.1f}°C, H={humidity:.1f}%, P={pressure:.1f}hPa")
                
            except Exception as e:
                logger.warning(f"⚠️ 模型预测失败，使用降级方法: {e}")
                temperature = self._fallback_predict(latitude, longitude, month, future_years)
                humidity = self._predict_humidity(temperature, month)
                pressure = self._predict_pressure(latitude, temperature)
                confidence = 0.75
                model_type = "fallback"
        else:
            # 使用降级预测
            temperature = self._fallback_predict(latitude, longitude, month, future_years)
            humidity = self._predict_humidity(temperature, month)
            pressure = self._predict_pressure(latitude, temperature)
            confidence = 0.75
            model_type = "fallback"
        
        # 构建预测结果
        result = {
            'temperature': round(temperature, 2),
            'humidity': round(humidity, 1),
            'pressure': round(pressure, 1),
            'closest_city': closest_city,
            'prediction_confidence': confidence,
            'model_version': self.version,
            'predicted_at': datetime.now().isoformat(),
            'model_type': model_type
        }
        
        return result
    
    def _predict_humidity(self, temperature, month):
        """基于温度和月份预测湿度"""
        base_humidity = 85 - (temperature - 5) * 1.5
        if month in [12, 1, 2]:
            base_humidity += 8
        elif month in [6, 7, 8]:
            base_humidity -= 5
        return max(30, min(95, base_humidity))
    
    def _predict_pressure(self, latitude, temperature):
        """基于位置和温度预测气压"""
        base_pressure = 1013.25
        lat_adj = (latitude - 51.5) * -0.5
        temp_adj = (temperature - 15) * -0.3
        return max(980, min(1040, base_pressure + lat_adj + temp_adj))
    
    def _fallback_predict(self, latitude, longitude, month, future_years):
        """降级预测方法"""
        closest_city = self.get_closest_city(latitude, longitude)
        
        base_temps = {'London': 11.2, 'Manchester': 10.1, 'Edinburgh': 8.7}
        monthly_adj = {
            1: -6.5, 2: -6.0, 3: -3.5, 4: -1.0, 5: 2.0, 6: 5.0,
            7: 7.5, 8: 7.0, 9: 4.0, 10: 1.0, 11: -2.5, 12: -5.0
        }
        
        base_temp = base_temps.get(closest_city, 11.2)
        month_adj = monthly_adj.get(month, 0)
        future_adj = future_years * 0.2
        
        return base_temp + month_adj + future_adj

def get_environmental_model():
    """获取环境预测模型实例"""
    global _environmental_model
    
    if _environmental_model is None:
        try:
            # 直接加载pkl模型文件
            model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'simple_environmental_model.pkl')
            
            if os.path.exists(model_path):
                # 加载模型
                model_data = joblib.load(model_path)
                
                # 创建模型包装器
                _environmental_model = LocalEnvironmentalPredictor(model_data)
                logger.info("✅ 环境预测模型已加载")
            else:
                logger.warning("⚠️ 模型文件不存在，使用降级预测")
                _environmental_model = LocalEnvironmentalPredictor(None)
                
        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            traceback.print_exc()
            _environmental_model = LocalEnvironmentalPredictor(None)
    
    return _environmental_model

@ml_bp.route('/predict', methods=['POST'])
def predict():
    """
    ML预测API端点
    
    输入格式：
    {
        "latitude": 51.5074,
        "longitude": -0.1278,
        "month": 6,
        "future_years": 0
    }
    
    输出：环境预测结果
    """
    try:
        # 验证输入数据
        data = request.get_json()
        
        if not data:
            return error_response("No JSON data provided", 400)
        
        # 验证必需字段
        required_fields = ['latitude', 'longitude']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return error_response(f"Missing required fields: {', '.join(missing_fields)}", 400)
        
        # 提取预测参数
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
        month = data.get('month', datetime.now().month)
        future_years = data.get('future_years', 0)
        
        # 验证参数范围
        if not (-90 <= latitude <= 90):
            return error_response("Latitude must be between -90 and 90", 400)
        
        if not (-180 <= longitude <= 180):
            return error_response("Longitude must be between -180 and 180", 400)
        
        if not (1 <= month <= 12):
            return error_response("Month must be between 1 and 12", 400)
        
        if not (0 <= future_years <= 50):
            return error_response("Future years must be between 0 and 50", 400)
        
        # 获取模型实例
        model = get_environmental_model()
        if not model:
            return error_response("Environmental model not available", 503)
        
        # 进行预测
        try:
            prediction = model.predict(
                latitude=latitude,
                longitude=longitude,
                month=month,
                future_years=future_years
            )
            
            # 构建响应
            response_data = {
                "success": True,
                "prediction": prediction,
                "input_parameters": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "month": month,
                    "future_years": future_years
                },
                "location_info": {
                    "coordinates": f"{latitude:.6f}, {longitude:.6f}",
                    "closest_city": _get_closest_city(latitude, longitude),
                    "prediction_type": "future" if future_years > 0 else "current"
                },
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ 预测成功 - 位置: {latitude:.4f}, {longitude:.4f}, "
                       f"月份: {month}, 未来年数: {future_years}")
            
            return jsonify(response_data), 200
            
        except Exception as e:
            logger.error(f"❌ 预测失败: {e}")
            return error_response(f"Prediction failed: {str(e)}", 500)
            
    except Exception as e:
        logger.error(f"❌ API错误: {e}")
        traceback.print_exc()
        return error_response(f"API error: {str(e)}", 500)

def _get_closest_city(lat, lon):
    """获取最接近的城市"""
    cities = {
        'London': {'lat': 51.5074, 'lon': -0.1278},
        'Manchester': {'lat': 53.4808, 'lon': -2.2426},
        'Edinburgh': {'lat': 55.9533, 'lon': -3.1883}
    }
    
    min_distance = float('inf')
    closest_city = "Unknown"
    
    for city, center in cities.items():
        distance = ((lat - center['lat'])**2 + (lon - center['lon'])**2)**0.5
        if distance < min_distance:
            min_distance = distance
            closest_city = city
    
    return closest_city

@ml_bp.route('/model/info', methods=['GET'])
def model_info():
    """获取模型信息"""
    try:
        model = get_environmental_model()
        if not model:
            return error_response("Environmental model not available", 503)
        
        model_info = {
            "success": True,
            "model_info": model.model_info,
            "supported_locations": [
                {"city": "London", "coordinates": [51.5074, -0.1278]},
                {"city": "Manchester", "coordinates": [53.4808, -2.2426]},
                {"city": "Edinburgh", "coordinates": [55.9533, -3.1883]}
            ],
            "prediction_variables": [
                "temperature",
                "humidity", 
                "pressure"
            ],
            "available_months": list(range(1, 13)),
            "future_years_range": [0, 50],
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(model_info), 200
        
    except Exception as e:
        logger.error(f"❌ 模型信息获取失败: {e}")
        return error_response(f"Model info error: {str(e)}", 500)

@ml_bp.route('/model/status', methods=['GET'])
def model_status():
    """检查模型状态"""
    try:
        model = get_environmental_model()
        
        status = {
            "success": True,
            "model_available": model is not None,
            "model_loaded": model is not None and model.temperature_model is not None,
            "timestamp": datetime.now().isoformat()
        }
        
        if model and model.temperature_model:
            status["model_version"] = model.model_info.get('version', 'unknown')
            status["training_data_size"] = model.model_info.get('training_data_size', 0)
            status["performance_metrics"] = model.model_info.get('performance_metrics', {})
        
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"❌ 模型状态检查失败: {e}")
        return error_response(f"Model status error: {str(e)}", 500)

@ml_bp.route('/predict/batch', methods=['POST'])
def predict_batch():
    """批量预测API端点"""
    try:
        data = request.get_json()
        
        if not data or 'locations' not in data:
            return error_response("No locations data provided", 400)
        
        locations = data['locations']
        if not isinstance(locations, list) or len(locations) == 0:
            return error_response("Locations must be a non-empty list", 400)
        
        if len(locations) > 100:
            return error_response("Maximum 100 locations allowed", 400)
        
        # 获取模型实例
        model = get_environmental_model()
        if not model:
            return error_response("Environmental model not available", 503)
        
        # 批量预测
        results = []
        for i, location in enumerate(locations):
            try:
                lat = float(location['latitude'])
                lon = float(location['longitude'])
                month = location.get('month', datetime.now().month)
                future_years = location.get('future_years', 0)
                
                prediction = model.predict(lat, lon, month, future_years)
                
                results.append({
                    "index": i,
                    "success": True,
                    "prediction": prediction,
                    "input": location,
                    "closest_city": _get_closest_city(lat, lon)
                })
                
            except Exception as e:
                results.append({
                    "index": i,
                    "success": False,
                    "error": str(e),
                    "input": location
                })
        
        # 统计结果
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        response_data = {
            "success": True,
            "total_predictions": len(results),
            "successful_predictions": successful,
            "failed_predictions": failed,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ 批量预测完成 - 总数: {len(results)}, 成功: {successful}, 失败: {failed}")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"❌ 批量预测失败: {e}")
        return error_response(f"Batch prediction error: {str(e)}", 500)

# 健康检查端点
@ml_bp.route('/health', methods=['GET'])
def health_check():
    """ML模块健康检查"""
    try:
        model = get_environmental_model()
        
        health_data = {
            "status": "healthy" if model else "unhealthy",
            "model_available": model is not None,
            "model_loaded": model is not None and model.temperature_model is not None,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }
        
        if model and model.temperature_model:
            health_data["model_info"] = model.model_info
        
        status_code = 200 if model else 503
        return jsonify(health_data), status_code
        
    except Exception as e:
        logger.error(f"❌ 健康检查失败: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

# 错误处理
@ml_bp.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return error_response("ML endpoint not found", 404)

@ml_bp.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    logger.error(f"内部错误: {error}")
    return error_response("Internal server error", 500)

logger.info("🤖 ML预测API模块已加载")
