#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SHAP预测API端点 - 基于SHAP框架的环境预测API

专为SHAP环境变化指数框架设计的API端点
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
import sys
import os
import traceback
from pathlib import Path
import numpy as np

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 导入SHAP模型包装器
from ML_Models.models.shap_deployment.shap_model_wrapper import SHAPModelWrapper
from api.utils import ml_prediction_response, error_response

logger = logging.getLogger(__name__)

# 创建蓝图
shap_bp = Blueprint('shap_predict', __name__, url_prefix='/api/v1/shap')

# 全局SHAP模型实例
_shap_model = None

def validate_json_input(request):
    """通用JSON输入验证函数"""
    try:
        if not request.is_json:
            return error_response("请求必须是JSON格式", code=400, error_type="invalid_content_type")
        
        data = request.get_json()
        if data is None:
            return error_response("无效的JSON数据", code=400, error_type="invalid_json")
        
        return data
    except Exception as e:
        return error_response(f"JSON解析错误: {str(e)}", code=400, error_type="json_parse_error")

def get_shap_model():
    """获取SHAP模型实例 (单例模式)"""
    global _shap_model
    
    if _shap_model is None:
        try:
            # 构建模型路径
            models_path = os.path.join(project_root, "ML_Models", "models", "shap_deployment")
            
            if not os.path.exists(models_path):
                raise FileNotFoundError(f"SHAP模型目录不存在: {models_path}")
            
            _shap_model = SHAPModelWrapper(models_directory=models_path)
            logger.info("✅ SHAP模型包装器初始化成功")
            
        except Exception as e:
            logger.error(f"❌ SHAP模型初始化失败: {e}")
            _shap_model = None
            raise
    
    return _shap_model

@shap_bp.route('/predict', methods=['POST'])
def predict():
    """
    SHAP环境预测API
    
    输入:
    {
        "latitude": float,
        "longitude": float,
        "month": int (可选),
        "analyze_shap": bool (可选, 默认true)
    }
    
    输出:
    {
        "city": str,
        "coordinates": {"latitude": float, "longitude": float},
        "climate_score": float,
        "geographic_score": float,
        "economic_score": float,
        "final_score": float,
        "confidence": float,
        "shap_analysis": {...} (如果analyze_shap=true)
    }
    """
    try:
        # 验证输入数据
        data = validate_json_input(request)
        if isinstance(data, tuple):  # 验证失败
            return data
        
        # 必需参数
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if latitude is None or longitude is None:
            return error_response(
                "缺少必需参数: latitude 和 longitude", 
                code=400,
                error_type="validation_error"
            )
        
        # 验证坐标范围
        if not (-90 <= latitude <= 90):
            return error_response(
                f"latitude必须在-90到90之间: {latitude}", 
                code=400,
                error_type="validation_error"
            )
        
        if not (-180 <= longitude <= 180):
            return error_response(
                f"longitude必须在-180到180之间: {longitude}", 
                code=400,
                error_type="validation_error"
            )
        
        # 可选参数
        month = data.get('month')
        analyze_shap = data.get('analyze_shap', True)
        
        if month is not None:
            if not (1 <= month <= 12):
                return error_response(
                    f"month必须在1到12之间: {month}", 
                    code=400,
                    error_type="validation_error"
                )
        
        # 获取模型实例
        model = get_shap_model()
        
        # 进行预测
        start_time = datetime.now()
        result = model.predict_environmental_scores(
            latitude=latitude,
            longitude=longitude,
            month=month,
            analyze_shap=analyze_shap
        )
        
        # 计算响应时间
        response_time = (datetime.now() - start_time).total_seconds()
        
        # 检查预测是否成功
        if 'error' in result:
            return error_response(
                f"预测失败: {result['error']}", 
                code=500,
                error_type="prediction_error",
                details=result
            )
        
        # 添加API元信息
        result['api_info'] = {
            'endpoint': '/api/v1/shap/predict',
            'version': 'v1.0.0',
            'response_time_seconds': response_time,
            'model_type': 'SHAP Environmental Framework'
        }
        
        return ml_prediction_response(
            result, 
            message="SHAP环境预测成功",
            response_time=response_time
        )
        
    except Exception as e:
        logger.error(f"❌ SHAP预测API错误: {e}")
        logger.error(traceback.format_exc())
        return error_response(
            f"服务器内部错误: {str(e)}", 
            code=500,
            error_type="internal_error"
        )

@shap_bp.route('/analyze', methods=['POST'])
def analyze():
    """
    深度SHAP分析API
    
    输入:
    {
        "latitude": float,
        "longitude": float,
        "month": int (可选),
        "analysis_depth": str (可选: "basic", "detailed", "full")
    }
    """
    try:
        # 验证输入数据
        data = validate_json_input(request)
        if isinstance(data, tuple):
            return data
        
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        month = data.get('month')
        analysis_depth = data.get('analysis_depth', 'detailed')
        
        if latitude is None or longitude is None:
            return error_response(
                "缺少必需参数: latitude 和 longitude", 
                code=400
            )
        
        # 获取模型实例
        model = get_shap_model()
        
        # 进行详细分析
        start_time = datetime.now()
        result = model.predict_environmental_scores(
            latitude=latitude,
            longitude=longitude,
            month=month,
            analyze_shap=True
        )
        
        if 'error' in result:
            return error_response(f"分析失败: {result['error']}", code=500)
        
        # 增强分析结果
        analysis_result = {
            'basic_prediction': {
                'city': result.get('city'),
                'final_score': result.get('final_score'),
                'confidence': result.get('overall_confidence')
            },
            'detailed_scores': {
                'climate_score': result.get('climate_score'),
                'geographic_score': result.get('geographic_score'),
                'economic_score': result.get('economic_score')
            },
            'shap_analysis': result.get('shap_analysis', {}),
            'analysis_metadata': {
                'analysis_depth': analysis_depth,
                'analysis_time': datetime.now().isoformat(),
                'response_time_seconds': (datetime.now() - start_time).total_seconds()
            }
        }
        
        return jsonify({
            'success': True,
            'message': 'SHAP深度分析完成',
            'data': analysis_result
        })
        
    except Exception as e:
        logger.error(f"❌ SHAP分析API错误: {e}")
        return error_response(f"分析失败: {str(e)}", code=500)

@shap_bp.route('/compare', methods=['POST'])
def compare():
    """
    多城市/位置对比API
    
    输入:
    {
        "locations": [
            {"latitude": float, "longitude": float, "name": str (可选)},
            ...
        ],
        "month": int (可选),
        "comparison_type": str (可选: "scores", "shap", "full")
    }
    """
    try:
        data = validate_json_input(request)
        if isinstance(data, tuple):
            return data
        
        locations = data.get('locations', [])
        month = data.get('month')
        comparison_type = data.get('comparison_type', 'scores')
        
        if not locations:
            return error_response("缺少locations参数", code=400)
        
        if len(locations) > 10:
            return error_response("最多支持10个位置的对比", code=400)
        
        # 获取模型实例
        model = get_shap_model()
        
        # 批量预测
        start_time = datetime.now()
        analyze_shap = comparison_type in ['shap', 'full']
        results = model.predict_batch(locations, month=month, analyze_shap=analyze_shap)
        
        # 生成对比分析
        comparison_result = {
            'locations_count': len(locations),
            'predictions': results,
            'comparison_summary': _generate_comparison_summary(results),
            'metadata': {
                'comparison_type': comparison_type,
                'month': month,
                'comparison_time': datetime.now().isoformat(),
                'response_time_seconds': (datetime.now() - start_time).total_seconds()
            }
        }
        
        return jsonify({
            'success': True,
            'message': f'成功对比{len(locations)}个位置',
            'data': comparison_result
        })
        
    except Exception as e:
        logger.error(f"❌ SHAP对比API错误: {e}")
        return error_response(f"对比失败: {str(e)}", code=500)

@shap_bp.route('/visualize', methods=['POST'])
def visualize():
    """
    SHAP可视化数据API
    
    输入:
    {
        "latitude": float,
        "longitude": float,
        "month": int (可选),
        "visualization_type": str (可选: "bubble", "importance", "waterfall")
    }
    """
    try:
        data = validate_json_input(request)
        if isinstance(data, tuple):
            return data
        
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        month = data.get('month')
        viz_type = data.get('visualization_type', 'bubble')
        
        if latitude is None or longitude is None:
            return error_response("缺少必需参数: latitude 和 longitude", code=400)
        
        # 获取模型实例
        model = get_shap_model()
        
        # 获取预测和SHAP数据
        result = model.predict_environmental_scores(
            latitude=latitude,
            longitude=longitude,
            month=month,
            analyze_shap=True
        )
        
        if 'error' in result:
            return error_response(f"可视化数据生成失败: {result['error']}", code=500)
        
        # 生成可视化数据
        viz_data = _generate_visualization_data(result, viz_type)
        
        return jsonify({
            'success': True,
            'message': f'{viz_type}可视化数据生成成功',
            'data': viz_data
        })
        
    except Exception as e:
        logger.error(f"❌ SHAP可视化API错误: {e}")
        return error_response(f"可视化失败: {str(e)}", code=500)

@shap_bp.route('/model/status', methods=['GET'])
def model_status():
    """获取SHAP模型状态"""
    try:
        model = get_shap_model()
        status = model.get_model_status()
        
        return jsonify({
            'success': True,
            'message': 'SHAP模型状态获取成功',
            'data': status
        })
        
    except Exception as e:
        logger.error(f"❌ 获取SHAP模型状态错误: {e}")
        return error_response(f"状态获取失败: {str(e)}", code=500)

@shap_bp.route('/health', methods=['GET'])
def health_check():
    """SHAP服务健康检查"""
    try:
        model = get_shap_model()
        status = model.get_model_status()
        
        # 检查关键组件
        health_status = {
            'service_status': 'healthy',
            'model_loaded': len(status.get('loaded_cities', [])) > 0,
            'manifest_loaded': status.get('manifest_loaded', False),
            'available_cities': status.get('available_cities', []),
            'timestamp': datetime.now().isoformat()
        }
        
        # 确定总体健康状态
        if not health_status['manifest_loaded']:
            health_status['service_status'] = 'degraded'
        
        return jsonify({
            'success': True,
            'message': 'SHAP服务健康检查完成',
            'data': health_status
        })
        
    except Exception as e:
        logger.error(f"❌ SHAP健康检查错误: {e}")
        return jsonify({
            'success': False,
            'message': f'健康检查失败: {str(e)}',
            'data': {
                'service_status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        }), 500

def _generate_comparison_summary(results):
    """生成对比摘要"""
    valid_results = [r for r in results if 'error' not in r]
    
    if not valid_results:
        return {'error': '没有有效的预测结果'}
    
    # 计算统计信息
    final_scores = [r.get('final_score', 0) for r in valid_results]
    climate_scores = [r.get('climate_score', 0) for r in valid_results]
    geo_scores = [r.get('geographic_score', 0) for r in valid_results]
    
    return {
        'total_locations': len(results),
        'valid_predictions': len(valid_results),
        'score_statistics': {
            'final_score': {
                'min': min(final_scores) if final_scores else 0,
                'max': max(final_scores) if final_scores else 0,
                'mean': np.mean(final_scores) if final_scores else 0,
                'std': np.std(final_scores) if final_scores else 0
            },
            'climate_score': {
                'min': min(climate_scores) if climate_scores else 0,
                'max': max(climate_scores) if climate_scores else 0,
                'mean': np.mean(climate_scores) if climate_scores else 0
            },
            'geographic_score': {
                'min': min(geo_scores) if geo_scores else 0,
                'max': max(geo_scores) if geo_scores else 0,
                'mean': np.mean(geo_scores) if geo_scores else 0
            }
        },
        'best_location': valid_results[np.argmax(final_scores)] if final_scores else None,
        'worst_location': valid_results[np.argmin(final_scores)] if final_scores else None
    }

def _generate_visualization_data(result, viz_type):
    """生成可视化数据"""
    if viz_type == 'bubble':
        return {
            'type': 'bubble',
            'data': {
                'scores': [
                    {'name': 'Climate', 'value': result.get('climate_score', 0), 'confidence': result.get('climate_confidence', 0)},
                    {'name': 'Geographic', 'value': result.get('geographic_score', 0), 'confidence': result.get('geographic_confidence', 0)},
                    {'name': 'Economic', 'value': result.get('economic_score', 0), 'confidence': result.get('economic_confidence', 0)}
                ],
                'final_score': result.get('final_score', 0),
                'city': result.get('city', 'Unknown')
            }
        }
    
    elif viz_type == 'importance':
        shap_analysis = result.get('shap_analysis', {})
        feature_importance = shap_analysis.get('feature_importance', {})
        
        return {
            'type': 'importance',
            'data': {
                'features': [
                    {'name': name, 'importance': importance}
                    for name, importance in feature_importance.items()
                ],
                'base_value': shap_analysis.get('base_value', 0),
                'prediction_value': shap_analysis.get('prediction_value', 0)
            }
        }
    
    elif viz_type == 'waterfall':
        shap_analysis = result.get('shap_analysis', {})
        feature_importance = shap_analysis.get('feature_importance', {})
        
        return {
            'type': 'waterfall',
            'data': {
                'base_value': shap_analysis.get('base_value', 0),
                'contributions': [
                    {'feature': name, 'contribution': contribution}
                    for name, contribution in feature_importance.items()
                ],
                'final_value': shap_analysis.get('prediction_value', 0)
            }
        }
    
    else:
        return {'error': f'不支持的可视化类型: {viz_type}'}

# 错误处理器
@shap_bp.errorhandler(404)
def not_found(error):
    return error_response("API端点不存在", code=404, error_type="not_found")

@shap_bp.errorhandler(500)
def internal_error(error):
    return error_response("服务器内部错误", code=500, error_type="internal_error") 