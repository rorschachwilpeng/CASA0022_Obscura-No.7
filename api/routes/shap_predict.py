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

# 导入归一化工具
from utils.score_normalizer import get_score_normalizer

# 🔧 修复：确保能够正确找到ML_Models模块
try:
    # 尝试从项目根目录加载ML_Models
    import importlib.util
    ml_models_path = os.path.join(project_root, 'ML_Models')
    if os.path.exists(ml_models_path) and ml_models_path not in sys.path:
        sys.path.insert(0, ml_models_path)
        print(f"✅ 已添加ML_Models路径到sys.path: {ml_models_path}")
    
    # 验证混合模型包装器路径
    hybrid_wrapper_path = os.path.join(project_root, 'ML_Models', 'models', 'shap_deployment', 'hybrid_model_wrapper.py')
    if os.path.exists(hybrid_wrapper_path):
        print(f"✅ 混合模型包装器文件存在: {hybrid_wrapper_path}")
    else:
        print(f"❌ 混合模型包装器文件不存在: {hybrid_wrapper_path}")
        
except Exception as e:
    print(f"⚠️ 路径设置过程中出现警告: {e}")

# 条件导入混合SHAP模型包装器
try:
    from ML_Models.models.shap_deployment.hybrid_model_wrapper import get_hybrid_shap_model
    SHAP_AVAILABLE = True
    print("✅ HybridSHAPModelWrapper导入成功")
except ImportError as e:
    print(f"⚠️ 混合SHAP模型不可用: {e}")
    SHAP_AVAILABLE = False
    get_hybrid_shap_model = None

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
            return error_response("请求必须是JSON格式", status_code=400, error_code="invalid_content_type")
        
        data = request.get_json()
        if data is None:
            return error_response("无效的JSON数据", status_code=400, error_code="invalid_json")
        
        return data
    except Exception as e:
        return error_response(f"JSON解析错误: {str(e)}", status_code=400, error_code="json_parse_error")

def get_shap_model():
    """获取混合SHAP模型实例 (单例模式)"""
    global _shap_model
    
    if not SHAP_AVAILABLE:
        raise RuntimeError("混合SHAP模型不可用，可能缺少依赖包")
    
    if _shap_model is None:
        try:
            # 🔧 修复：使用混合模型包装器，指定正确的模型路径
            import os
            models_path = os.path.join(project_root, "ML_Models", "models", "shap_deployment", "trained_models_66")
            _shap_model = get_hybrid_shap_model(models_path)
            print("✅ 混合SHAP模型包装器初始化成功")
            
            # 验证模型状态
            status = _shap_model.get_model_status()
            print(f"📊 SHAP模型状态: {status}")
            
        except Exception as e:
            print(f"❌ SHAP模型初始化失败: {e}")
            logger.error(f"❌ SHAP模型初始化失败: {e}")
            _shap_model = None
            raise
    
    return _shap_model

@shap_bp.route('/debug/files', methods=['GET'])
def debug_files():
    """调试端点：检查云端文件系统状态"""
    try:
        import os
        from pathlib import Path
        
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        models_path = os.path.join(project_root, "ML_Models", "models", "shap_deployment")
        
        debug_info = {
            'project_root': project_root,
            'models_path': models_path,
            'models_path_exists': os.path.exists(models_path),
            'files_in_models_dir': [],
            'file_sizes': {},
            'city_directories': {},
            'python_version': sys.version,
            'available_memory': 'unknown'
        }
        
        if os.path.exists(models_path):
            # 列出模型目录中的所有文件
            for root, dirs, files in os.walk(models_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, models_path)
                    debug_info['files_in_models_dir'].append(relative_path)
                    try:
                        debug_info['file_sizes'][relative_path] = os.path.getsize(file_path)
                    except:
                        debug_info['file_sizes'][relative_path] = 'unknown'
            
            # 检查各城市目录
            for city in ['london', 'manchester', 'edinburgh']:
                city_path = os.path.join(models_path, city)
                debug_info['city_directories'][city] = {
                    'exists': os.path.exists(city_path),
                    'files': []
                }
                if os.path.exists(city_path):
                    debug_info['city_directories'][city]['files'] = os.listdir(city_path)
        
        # 尝试检查内存
        try:
            import psutil
            debug_info['available_memory'] = f"{psutil.virtual_memory().available / (1024**3):.2f} GB"
        except:
            pass
        
        return jsonify({
            'success': True,
            'debug_info': debug_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

@shap_bp.route('/predict', methods=['POST'])
def predict():
    """
    SHAP环境预测API - 带降级处理
    """
    try:
        # 检查SHAP可用性
        if not SHAP_AVAILABLE:
            return _fallback_prediction_response(request)
        
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
                error_status_code="validation_error",
                status_status_code=400
            )
        
        # 验证坐标范围
        if not (-90 <= latitude <= 90):
            return error_response(
                f"latitude必须在-90到90之间: {latitude}", 
                error_status_code="validation_error",
                status_status_code=400
            )
        
        if not (-180 <= longitude <= 180):
            return error_response(
                f"longitude必须在-180到180之间: {longitude}", 
                error_status_code="validation_error",
                status_status_code=400
            )
        
        # 可选参数
        month = data.get('month')
        analyze_shap = data.get('analyze_shap', True)
        
        if month is not None:
            if not (1 <= month <= 12):
                return error_response(
                    f"month必须在1到12之间: {month}", 
                    error_status_code="validation_error",
                    status_status_code=400
                )
        
        # 尝试获取模型实例
        try:
            model = get_shap_model()
            # 检查模型状态
            status = model.get_model_status()
            
            # 检查是否有可用的城市配置（而不是已加载的城市）
            if not status.get('manifest_loaded') or not status.get('available_cities'):
                logger.warning("⚠️ 模型配置不可用，使用降级预测")
                return _fallback_prediction_response(request, fallback_reason="manifest_not_loaded")
            
        except Exception as e:
            logger.error(f"❌ 模型获取失败: {e}")
            return _fallback_prediction_response(request, fallback_reason=f"model_error: {str(e)}")
        
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
            logger.warning(f"⚠️ 预测返回错误，使用降级处理: {result['error']}")
            return _fallback_prediction_response(request, fallback_reason=f"prediction_error: {result['error']}")
        
        # 添加API元信息
        result['api_info'] = {
            'endpoint': '/api/v1/shap/predict',
            'version': 'v1.0.0',
            'response_time_seconds': response_time,
            'model_type': 'SHAP Environmental Framework',
            'fallback_used': False
        }
        
        return jsonify({
            'success': True,
            'message': "SHAP环境预测成功",
            'data': result,
            'response_time_seconds': response_time
        })
        
    except Exception as e:
        logger.error(f"❌ SHAP预测API错误: {e}")
        # 最终降级处理
        return _fallback_prediction_response(request, fallback_reason=f"api_error: {str(e)}")

def _fallback_prediction_response(request, fallback_reason="shap_unavailable"):
    """降级预测响应 - 当SHAP模型不可用时使用简化算法"""
    try:
        data = request.get_json() if request.is_json else {}
        latitude = data.get('latitude', 51.5074)  # 默认伦敦
        longitude = data.get('longitude', -0.1278)
        month = data.get('month', datetime.now().month)
        location_name = data.get('location_name')  # 获取真实地理位置信息
        
        # 简化的环境评分算法
        city_centers = {
            'London': {'lat': 51.5074, 'lon': -0.1278, 'base_climate': 0.75, 'base_geo': 0.70},
            'Manchester': {'lat': 53.4808, 'lon': -2.2426, 'base_climate': 0.68, 'base_geo': 0.65},
            'Edinburgh': {'lat': 55.9533, 'lon': -3.1883, 'base_climate': 0.72, 'base_geo': 0.68}
        }
        
        # 确定城市信息：优先使用真实地理位置，否则基于坐标查找
        if location_name and location_name != "Unknown Location":
            # 使用真实地理位置信息
            closest_city = location_name
            # 基于位置名称选择合适的基础评分
            if 'London' in location_name or 'london' in location_name.lower():
                closest_info = city_centers['London']
            elif 'Manchester' in location_name or 'manchester' in location_name.lower():
                closest_info = city_centers['Manchester']
            elif 'Edinburgh' in location_name or 'edinburgh' in location_name.lower():
                closest_info = city_centers['Edinburgh']
            else:
                # 对于其他地点，使用默认的中等评分
                closest_info = {'lat': latitude, 'lon': longitude, 'base_climate': 0.70, 'base_geo': 0.68}
            
            distance_factor = 1.0  # 真实位置信息，距离因子设为1
            logger.info(f"✅ Using real location name: {closest_city}")
        else:
            # 回退到基于坐标的城市查找
            min_distance = float('inf')
            closest_city = "London"
            closest_info = city_centers['London']
            
            for city, info in city_centers.items():
                distance = np.sqrt((latitude - info['lat'])**2 + (longitude - info['lon'])**2)
                if distance < min_distance:
                    min_distance = distance
                    closest_city = city
                    closest_info = info
            
            distance_factor = max(0.5, 1.0 - min_distance * 0.1)
            logger.info(f"⚠️ Using coordinate-based city detection: {closest_city}")
        
        # 基于距离和季节的简化评分
        seasonal_factor = 1.0 + 0.1 * np.sin(2 * np.pi * month / 12)  # 季节性变化
        
        climate_score = max(0.0, min(1.0, closest_info['base_climate'] * distance_factor * seasonal_factor))
        geographic_score = max(0.0, min(1.0, closest_info['base_geo'] * distance_factor))
        economic_score = max(0.2, min(1.0, 0.8 * distance_factor))
        
        final_score = climate_score * 0.4 + geographic_score * 0.35 + economic_score * 0.25
        
        result = {
            'city': closest_city,
            'coordinates': {'latitude': latitude, 'longitude': longitude},
            'climate_score': round(climate_score, 3),
            'geographic_score': round(geographic_score, 3),
            'economic_score': round(economic_score, 3),
            'final_score': round(final_score, 3),
            'confidence': 0.6,  # 降级模式置信度较低
            'prediction_timestamp': datetime.now().isoformat(),
            'month': month,
            'model_status': 'fallback',
            'api_info': {
                'endpoint': '/api/v1/shap/predict',
                'version': 'v1.0.0-fallback',
                'model_type': 'Simplified Environmental Algorithm',
                'fallback_used': True,
                'fallback_reason': fallback_reason
            },
            'shap_analysis': {
                'error': 'SHAP分析在降级模式下不可用',
                'fallback_feature_importance': {
                    'distance_to_city_center': 0.4,
                    'seasonal_factor': 0.3,
                    'base_climate_rating': 0.2,
                    'geographic_proximity': 0.1
                }
            }
        }
        
        return jsonify({
            'success': True,
            'message': f"环境预测成功 (降级模式: {fallback_reason})",
            'data': result,
            'response_time_seconds': 0.01
        })
        
    except Exception as e:
        logger.error(f"❌ 降级预测也失败了: {e}")
        return error_response(
            f"系统暂时不可用: {str(e)}", 
            error_status_code="system_unavailable",
            status_status_code=503
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
                error_status_code="validation_error",
                status_status_code=400
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
            return error_response(f"分析失败: {result['error']}", status_code=500)
        
        # 🌟 新增：应用分数归一化
        normalizer = get_score_normalizer()
        normalized_result = normalizer.normalize_shap_result(result)
        
        # 增强分析结果
        analysis_result = {
            'basic_prediction': {
                'city': normalized_result.get('city'),
                'final_score': normalized_result.get('final_score'),  # 保留原始最终分数
                'confidence': normalized_result.get('overall_confidence')
            },
            'detailed_scores': {
                'climate_score': normalized_result.get('climate_score'),
                'geographic_score': normalized_result.get('geographic_score'),
                'economic_score': normalized_result.get('economic_score')
            },
            'normalized_scores': normalized_result.get('normalized_scores', {}),
            'environment_change_outcome': normalized_result.get('environment_change_outcome'),
            'contribution_breakdown': normalized_result.get('contribution_breakdown', {}),
            'raw_scores': normalized_result.get('raw_scores', {}),
            'shap_analysis': normalized_result.get('shap_analysis', {}),
            'analysis_metadata': {
                'analysis_depth': analysis_depth,
                'analysis_time': datetime.now().isoformat(),
                'response_time_seconds': (datetime.now() - start_time).total_seconds(),
                'normalization_applied': True
            }
        }
        
        return jsonify({
            'success': True,
            'message': 'SHAP深度分析完成',
            'data': analysis_result
        })
        
    except Exception as e:
        logger.error(f"❌ SHAP分析API错误: {e}")
        return error_response(f"分析失败: {str(e)}", status_code=500)

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
            return error_response("缺少locations参数", status_code=400)
        
        if len(locations) > 10:
            return error_response("最多支持10个位置的对比", status_code=400)
        
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
        return error_response(f"对比失败: {str(e)}", status_code=500)

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
            return error_response("缺少必需参数: latitude 和 longitude", status_code=400)
        
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
            return error_response(f"可视化数据生成失败: {result['error']}", status_code=500)
        
        # 生成可视化数据
        viz_data = _generate_visualization_data(result, viz_type)
        
        return jsonify({
            'success': True,
            'message': f'{viz_type}可视化数据生成成功',
            'data': viz_data
        })
        
    except Exception as e:
        logger.error(f"❌ SHAP可视化API错误: {e}")
        return error_response(f"可视化失败: {str(e)}", status_code=500)

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
        return error_response(f"状态获取失败: {str(e)}", status_code=500)

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
    return error_response("API端点不存在", status_code=404, error_code="not_found")

@shap_bp.errorhandler(500)
def internal_error(error):
    return error_response("服务器内部错误", status_code=500, error_code="internal_error") 