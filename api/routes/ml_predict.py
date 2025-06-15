#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ML Prediction API Routes - 机器学习预测API端点
"""

from flask import Blueprint, request
from datetime import datetime
import logging
import sys
import os
import importlib.util

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from api.schemas import validate_ml_input
from api.utils import validate_json_input, ml_prediction_response, error_response

logger = logging.getLogger(__name__)

# 创建蓝图
ml_bp = Blueprint('ml_predict', __name__, url_prefix='/api/v1/ml')

@ml_bp.route('/predict', methods=['POST'])
@validate_json_input(validate_ml_input)
def predict():
    """
    ML预测API端点
    
    输入：环境数据 + 预测时间
    输出：预测结果
    """
    try:
        data = request.get_json()
        
        env_data_dict = data['environmental_data']
        hours_ahead = data.get('hours_ahead', 24)
        
        # 导入必要的类
        try:
            # 动态导入以数字开头的模块
            module_path = os.path.join(project_root, 'WorkFlow', 'NonRasberryPi_Workflow', '1_1_local_environment_setup_and_mock_process_validation.py')
            spec = importlib.util.spec_from_file_location("workflow_module", module_path)
            workflow_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(workflow_module)
            
            # 获取需要的类
            EnvironmentalData = workflow_module.EnvironmentalData
            MockMLPredictor = workflow_module.MockMLPredictor
            
        except Exception as import_error:
            logger.error(f"Failed to import workflow modules: {import_error}")
            return error_response(
                "ML prediction service temporarily unavailable",
                "IMPORT_ERROR",
                503
            )
        
        # 创建EnvironmentalData对象
        env_data = EnvironmentalData(
            latitude=env_data_dict['latitude'],
            longitude=env_data_dict['longitude'],
            temperature=env_data_dict['temperature'],
            humidity=env_data_dict['humidity'],
            pressure=env_data_dict['pressure'],
            wind_speed=env_data_dict['wind_speed'],
            weather_description=env_data_dict['weather_description'],
            timestamp=env_data_dict.get('timestamp', datetime.now().isoformat()),
            location_name=env_data_dict.get('location_name', '')
        )
        
        # 初始化ML预测器
        ml_predictor = MockMLPredictor()
        
        # 执行预测
        prediction = ml_predictor.predict_weather(env_data, hours_ahead)
        
        # 构建响应数据
        prediction_data = {
            "predicted_temperature": prediction.predicted_temperature,
            "predicted_humidity": prediction.predicted_humidity,
            "predicted_weather_condition": prediction.predicted_weather_condition,
            "confidence_score": prediction.confidence_score,
            "prediction_timestamp": prediction.prediction_timestamp,
            "model_version": prediction.model_version
        }
        
        input_summary = {
            "location": f"({env_data.latitude}, {env_data.longitude})",
            "current_conditions": f"{env_data.temperature}°C, {env_data.weather_description}",
            "hours_ahead": hours_ahead
        }
        
        logger.info(f"ML prediction successful for location ({env_data.latitude}, {env_data.longitude})")
        
        return ml_prediction_response(prediction_data, input_summary)
        
    except Exception as e:
        logger.error(f"ML prediction failed: {e}")
        return error_response(
            "ML prediction processing failed",
            "PREDICTION_ERROR",
            500
        )

@ml_bp.route('/health', methods=['GET'])
def ml_health():
    """ML服务健康检查"""
    try:
        # 获取项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # 动态导入模块
        module_path = os.path.join(project_root, 'WorkFlow', 'NonRasberryPi_Workflow', '1_1_local_environment_setup_and_mock_process_validation.py')
        spec = importlib.util.spec_from_file_location("workflow_module", module_path)
        workflow_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(workflow_module)
        
        MockMLPredictor = workflow_module.MockMLPredictor
        predictor = MockMLPredictor()
        
        return ml_prediction_response(
            {
                "status": "healthy",
                "model_version": predictor.model_version,
                "model_trained": predictor.is_trained
            },
            {
                "service": "ML Prediction API",
                "endpoint": "/api/v1/ml/predict"
            }
        )
        
    except Exception as e:
        logger.error(f"ML health check failed: {e}")
        return error_response(
            "ML service unhealthy",
            "HEALTH_CHECK_FAILED",
            503
        )
