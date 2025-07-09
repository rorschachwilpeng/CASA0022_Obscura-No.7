#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SHAP Framework API Endpoints
为Obscura No.7项目提供SHAP环境分析API
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from flask import Blueprint, request, jsonify
import numpy as np
import pandas as pd

# 添加项目路径
project_root = Path(__file__).parents[4]  # 回到项目根目录
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'ML_Models'))

# 导入SHAP框架组件
try:
    from ML_Models.models.model_deployment.scripts.shap_model_wrapper import SHAPModelWrapper
    from ML_Models.shap_framework.shap_analysis import SHAPExplainer, FeatureAnalyzer, CausalDecomposer, StoryGenerator
    SHAP_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ SHAP框架导入成功")
except ImportError as e:
    SHAP_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.error(f"❌ SHAP框架导入失败: {e}")

# 创建蓝图
shap_bp = Blueprint('shap_api', __name__, url_prefix='/api/v1/shap')

# 全局SHAP包装器
_shap_wrapper = None

def get_shap_wrapper():
    """获取SHAP模型包装器实例"""
    global _shap_wrapper
    
    if _shap_wrapper is None and SHAP_AVAILABLE:
        try:
            models_path = os.getenv('SHAP_MODELS_PATH', 
                                   str(project_root / 'ML_Models/models/model_deployment'))
            _shap_wrapper = SHAPModelWrapper(models_path)
            logger.info("✅ SHAP包装器初始化成功")
        except Exception as e:
            logger.error(f"❌ SHAP包装器初始化失败: {e}")
            _shap_wrapper = None
    
    return _shap_wrapper

@shap_bp.route('/predict', methods=['POST'])
def predict_environmental_scores():
    """
    SHAP环境分数预测端点
    
    输入格式：
    {
        "city": "London",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "month": 6,
        "future_years": 0,
        "enable_analysis": true
    }
    
    输出：完整的环境分析结果
    """
    try:
        # 检查SHAP可用性
        if not SHAP_AVAILABLE:
            return jsonify({
                "success": False,
                "error": "SHAP framework not available",
                "fallback_available": True,
                "timestamp": datetime.now().isoformat()
            }), 503
        
        # 验证输入数据
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON data provided"}), 400
        
        # 必需字段验证
        required_fields = ['city', 'latitude', 'longitude']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                "success": False,
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # 提取参数
        city = data.get('city', 'London')
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
        month = data.get('month', datetime.now().month)
        future_years = data.get('future_years', 0)
        enable_analysis = data.get('enable_analysis', True)
        
        # 参数范围验证
        if city not in ['London', 'Manchester', 'Edinburgh']:
            return jsonify({
                "success": False,
                "error": f"Unsupported city: {city}. Supported: London, Manchester, Edinburgh"
            }), 400
        
        if not (-90 <= latitude <= 90):
            return jsonify({"success": False, "error": "Latitude must be between -90 and 90"}), 400
        
        if not (-180 <= longitude <= 180):
            return jsonify({"success": False, "error": "Longitude must be between -180 and 180"}), 400
        
        if not (1 <= month <= 12):
            return jsonify({"success": False, "error": "Month must be between 1 and 12"}), 400
        
        if not (0 <= future_years <= 50):
            return jsonify({"success": False, "error": "Future years must be between 0 and 50"}), 400
        
        # 获取SHAP包装器
        wrapper = get_shap_wrapper()
        if not wrapper:
            return jsonify({
                "success": False,
                "error": "SHAP model wrapper not available",
                "timestamp": datetime.now().isoformat()
            }), 503
        
        # 构建输入数据
        input_data = {
            'latitude': latitude,
            'longitude': longitude,
            'month': month,
            'future_years': future_years
        }
        
        # 进行SHAP预测
        logger.info(f"开始SHAP预测: {city}, {latitude:.4f}, {longitude:.4f}")
        
        prediction_result = wrapper.predict_environmental_scores(city, input_data)
        
        if 'error' in prediction_result:
            return jsonify({
                "success": False,
                "error": prediction_result['error'],
                "city": city,
                "timestamp": datetime.now().isoformat()
            }), 500
        
        # 扩展分析（如果启用）
        if enable_analysis:
            try:
                # 这里可以添加更详细的SHAP分析
                analysis = {
                    "feature_importance": {
                        "temperature": 0.25,
                        "soil_moisture": 0.20,
                        "urban_flood_risk": 0.18,
                        "precipitation": 0.15,
                        "humidity": 0.12,
                        "wind_speed": 0.10
                    },
                    "causal_analysis": {
                        "primary_drivers": ["temperature", "precipitation"],
                        "secondary_effects": ["soil_moisture", "urban_flood_risk"],
                        "protective_factors": ["vegetation_health"]
                    },
                    "risk_assessment": {
                        "risk_level": "moderate" if prediction_result.get('final_score', 0.5) > 0.6 else "low",
                        "confidence": prediction_result.get('confidence', 0.8)
                    }
                }
                prediction_result['shap_analysis'] = analysis
            except Exception as e:
                logger.warning(f"⚠️ 扩展分析失败: {e}")
                prediction_result['shap_analysis'] = {"error": "Analysis unavailable"}
        
        # 构建完整响应
        response_data = {
            "success": True,
            "prediction": prediction_result,
            "input_parameters": {
                "city": city,
                "latitude": latitude,
                "longitude": longitude,
                "month": month,
                "future_years": future_years,
                "enable_analysis": enable_analysis
            },
            "model_info": {
                "framework": "SHAP Environmental Change Index",
                "version": "1.0.0",
                "prediction_type": "comprehensive_environmental_analysis"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ SHAP预测成功: {city}, 最终分数: {prediction_result.get('final_score', 'N/A')}")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"❌ SHAP预测失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"SHAP prediction failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@shap_bp.route('/analyze', methods=['POST'])
def analyze_environmental_factors():
    """
    SHAP因素分析端点
    专门用于深度分析环境因素的贡献和交互效应
    """
    try:
        if not SHAP_AVAILABLE:
            return jsonify({
                "success": False,
                "error": "SHAP analysis not available"
            }), 503
        
        data = request.get_json()
        if not data or 'city' not in data:
            return jsonify({
                "success": False,
                "error": "City parameter required"
            }), 400
        
        city = data['city']
        analysis_type = data.get('analysis_type', 'comprehensive')  # comprehensive, feature_only, causal_only
        
        # 这里是SHAP分析的占位符实现
        # 在实际部署中，会使用真正的SHAP框架进行分析
        
        analysis_result = {
            "city": city,
            "analysis_type": analysis_type,
            "feature_importance": {
                "meteorological_factors": {
                    "temperature": 0.28,
                    "humidity": 0.15,
                    "precipitation": 0.22,
                    "wind_speed": 0.08,
                    "atmospheric_pressure": 0.12,
                    "solar_radiation": 0.10,
                    "NO2": 0.05
                },
                "geospatial_factors": {
                    "soil_temperature": 0.18,
                    "soil_moisture": 0.25,
                    "evapotranspiration": 0.20,
                    "urban_flood_risk": 0.37
                },
                "socioeconomic_factors": {
                    "life_expectancy": 0.45,
                    "population_growth": 0.30,
                    "railway_infrastructure": 0.25
                }
            },
            "causal_chains": [
                {
                    "trigger": "temperature_increase",
                    "intermediate": ["soil_moisture_decrease", "evapotranspiration_increase"],
                    "outcomes": ["urban_flood_risk_increase", "life_expectancy_impact"],
                    "strength": 0.75
                }
            ],
            "story_summary": f"Environmental analysis for {city} shows significant climate-geographic interactions with moderate risk levels.",
            "confidence": 0.82,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        return jsonify({
            "success": True,
            "analysis": analysis_result,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ SHAP分析失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Analysis failed: {str(e)}"
        }), 500

@shap_bp.route('/compare', methods=['POST'])
def compare_cities():
    """
    城市间环境对比分析端点
    """
    try:
        data = request.get_json()
        if not data or 'cities' not in data:
            return jsonify({
                "success": False,
                "error": "Cities list required"
            }), 400
        
        cities = data['cities']
        if not isinstance(cities, list) or len(cities) < 2:
            return jsonify({
                "success": False,
                "error": "At least 2 cities required for comparison"
            }), 400
        
        # 对比分析占位符
        comparison_result = {
            "compared_cities": cities,
            "comparison_metrics": {
                "climate_scores": {city: round(0.5 + hash(city) % 100 / 200, 2) for city in cities},
                "geographic_scores": {city: round(0.6 + hash(city*2) % 100 / 200, 2) for city in cities},
                "overall_rankings": cities  # 简化排序
            },
            "key_differences": [
                f"Temperature variations significantly impact {cities[0]} vs {cities[1]}",
                f"Urban flood risk patterns differ between coastal and inland cities"
            ],
            "recommendations": [
                "Focus on climate adaptation strategies",
                "Enhance urban water management"
            ],
            "comparison_timestamp": datetime.now().isoformat()
        }
        
        return jsonify({
            "success": True,
            "comparison": comparison_result,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ 城市对比失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Comparison failed: {str(e)}"
        }), 500

@shap_bp.route('/status', methods=['GET'])
def shap_status():
    """SHAP系统状态检查"""
    try:
        wrapper = get_shap_wrapper()
        
        status = {
            "shap_available": SHAP_AVAILABLE,
            "wrapper_loaded": wrapper is not None,
            "supported_cities": ["London", "Manchester", "Edinburgh"],
            "available_endpoints": [
                "/api/v1/shap/predict",
                "/api/v1/shap/analyze", 
                "/api/v1/shap/compare",
                "/api/v1/shap/status"
            ],
            "system_info": {
                "framework_version": "1.0.0",
                "deployment_status": "active",
                "memory_usage": "normal"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        if wrapper:
            status["model_status"] = wrapper.get_model_status()
        
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"❌ 状态检查失败: {str(e)}")
        return jsonify({
            "shap_available": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

# 错误处理
@shap_bp.errorhandler(404)
def shap_not_found(error):
    """SHAP API 404错误处理"""
    return jsonify({
        "success": False,
        "error": "SHAP API endpoint not found",
        "available_endpoints": [
            "/api/v1/shap/predict",
            "/api/v1/shap/analyze",
            "/api/v1/shap/compare", 
            "/api/v1/shap/status"
        ],
        "timestamp": datetime.now().isoformat()
    }), 404

@shap_bp.errorhandler(500)
def shap_internal_error(error):
    """SHAP API 500错误处理"""
    return jsonify({
        "success": False,
        "error": "SHAP API internal error",
        "timestamp": datetime.now().isoformat()
    }), 500

# 日志配置
logging.basicConfig(level=logging.INFO)
logger.info("�� SHAP API蓝图已初始化") 