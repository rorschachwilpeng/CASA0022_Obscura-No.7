#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻量级ML预测API - 无需外部模型文件
专为云端部署设计，将模型逻辑直接嵌入代码
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
import math

logger = logging.getLogger(__name__)

# 创建蓝图
lightweight_ml_bp = Blueprint('lightweight_ml', __name__, url_prefix='/api/v1/ml')

class LightweightEnvironmentalPredictor:
    """轻量级环境预测器 - 基于经验规则和简单算法"""
    
    def __init__(self):
        self.version = "1.0.0-lightweight"
        self.city_centers = {
            'London': {'lat': 51.5074, 'lon': -0.1278, 'base_temp': 11.2},
            'Manchester': {'lat': 53.4808, 'lon': -2.2426, 'base_temp': 10.1},
            'Edinburgh': {'lat': 55.9533, 'lon': -3.1883, 'base_temp': 8.7}
        }
        
        # 月度温度调整因子（基于真实数据的简化）
        self.monthly_adjustments = {
            1: -6.5,   # 1月
            2: -6.0,   # 2月
            3: -3.5,   # 3月
            4: -1.0,   # 4月
            5: 2.0,    # 5月
            6: 5.0,    # 6月
            7: 7.5,    # 7月
            8: 7.0,    # 8月
            9: 4.0,    # 9月
            10: 1.0,   # 10月
            11: -2.5,  # 11月
            12: -5.0   # 12月
        }
    
    def get_closest_city(self, lat, lon):
        """获取最接近的城市"""
        min_distance = float('inf')
        closest_city = "London"
        
        for city, center in self.city_centers.items():
            distance = math.sqrt((lat - center['lat'])**2 + (lon - center['lon'])**2)
            if distance < min_distance:
                min_distance = distance
                closest_city = city
                
        return closest_city, self.city_centers[closest_city]
    
    def predict_temperature(self, lat, lon, month, future_years=0):
        """预测温度"""
        # 获取最近城市
        closest_city, city_data = self.get_closest_city(lat, lon)
        
        # 基础温度
        base_temp = city_data['base_temp']
        
        # 月度调整
        monthly_adj = self.monthly_adjustments.get(month, 0)
        
        # 地理位置微调（基于与城市中心的距离）
        lat_diff = lat - city_data['lat']
        lon_diff = lon - city_data['lon']
        geo_adjustment = -0.5 * lat_diff  # 纬度越高越冷
        
        # 未来年份调整（气候变化趋势）
        future_adjustment = future_years * 0.2  # 每年0.2°C增温
        
        # 最终温度
        temperature = base_temp + monthly_adj + geo_adjustment + future_adjustment
        
        return temperature, closest_city
    
    def predict_humidity(self, temperature, month, coastal_factor=1.0):
        """基于温度和月份预测湿度"""
        # 基础湿度模型：温度越高湿度相对越低
        base_humidity = 85 - (temperature - 5) * 1.5
        
        # 季节性调整
        if month in [12, 1, 2]:  # 冬季更湿润
            base_humidity += 8
        elif month in [6, 7, 8]:  # 夏季相对干燥
            base_humidity -= 5
        
        # 限制范围
        humidity = max(30, min(95, base_humidity))
        
        return humidity
    
    def predict_pressure(self, lat, temperature):
        """基于地理位置和温度预测气压"""
        # 基础海平面气压
        base_pressure = 1013.25
        
        # 纬度调整（高纬度通常低压）
        lat_adjustment = (lat - 51.5) * -0.5
        
        # 温度调整（高温通常低压）
        temp_adjustment = (temperature - 15) * -0.3
        
        # 随机变化模拟
        import random
        random_variation = random.uniform(-8, 8)
        
        pressure = base_pressure + lat_adjustment + temp_adjustment + random_variation
        
        return max(980, min(1040, pressure))
    
    def predict(self, latitude, longitude, month=None, future_years=0):
        """完整预测"""
        if month is None:
            month = datetime.now().month
            
        # 预测温度
        temperature, closest_city = self.predict_temperature(latitude, longitude, month, future_years)
        
        # 预测湿度
        humidity = self.predict_humidity(temperature, month)
        
        # 预测气压
        pressure = self.predict_pressure(latitude, temperature)
        
        return {
            'temperature': round(temperature, 2),
            'humidity': round(humidity, 1),
            'pressure': round(pressure, 1),
            'closest_city': closest_city,
            'prediction_confidence': 0.75,
            'model_version': self.version,
            'predicted_at': datetime.now().isoformat(),
            'model_type': 'lightweight_embedded'
        }

# 全局预测器实例
_predictor = LightweightEnvironmentalPredictor()

@lightweight_ml_bp.route('/predict', methods=['POST'])
def predict():
    """轻量级ML预测端点"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "No JSON data provided"}), 400
        
        # 验证必需字段
        required_fields = ['latitude', 'longitude']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                "success": False, 
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # 提取预测参数
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
        month = data.get('month', datetime.now().month)
        future_years = data.get('future_years', 0)
        
        # 验证参数范围
        if not (-90 <= latitude <= 90):
            return jsonify({"success": False, "error": "Latitude must be between -90 and 90"}), 400
        
        if not (-180 <= longitude <= 180):
            return jsonify({"success": False, "error": "Longitude must be between -180 and 180"}), 400
        
        if not (1 <= month <= 12):
            return jsonify({"success": False, "error": "Month must be between 1 and 12"}), 400
        
        if not (0 <= future_years <= 50):
            return jsonify({"success": False, "error": "Future years must be between 0 and 50"}), 400
        
        # 进行预测
        prediction = _predictor.predict(latitude, longitude, month, future_years)
        
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
                "closest_city": prediction['closest_city'],
                "prediction_type": "future" if future_years > 0 else "current"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ 轻量级预测成功 - 位置: {latitude:.4f}, {longitude:.4f}")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"❌ 轻量级预测失败: {e}")
        return jsonify({
            "success": False, 
            "error": f"Prediction failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@lightweight_ml_bp.route('/model/info', methods=['GET'])
def model_info():
    """获取轻量级模型信息"""
    model_info = {
        "success": True,
        "model_info": {
            "version": _predictor.version,
            "type": "lightweight_embedded",
            "description": "轻量级环境预测模型，专为云端部署设计",
            "no_external_files": True,
            "cloud_ready": True
        },
        "supported_locations": [
            {"city": "London", "coordinates": [51.5074, -0.1278]},
            {"city": "Manchester", "coordinates": [53.4808, -2.2426]},
            {"city": "Edinburgh", "coordinates": [55.9533, -3.1883]}
        ],
        "prediction_variables": ["temperature", "humidity", "pressure"],
        "available_months": list(range(1, 13)),
        "future_years_range": [0, 50],
        "deployment_advantages": [
            "无需外部模型文件",
            "最小依赖包需求",
            "快速云端部署",
            "低内存占用"
        ],
        "timestamp": datetime.now().isoformat()
    }
    
    return jsonify(model_info), 200

@lightweight_ml_bp.route('/health', methods=['GET'])
def health_check():
    """轻量级模型健康检查"""
    health_data = {
        "status": "healthy",
        "model_available": True,
        "model_loaded": True,
        "model_type": "lightweight_embedded",
        "external_dependencies": False,
        "timestamp": datetime.now().isoformat(),
        "version": _predictor.version
    }
    
    return jsonify(health_data), 200

logger.info("🚀 轻量级ML预测API模块已加载") 