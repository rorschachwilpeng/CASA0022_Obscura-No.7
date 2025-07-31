#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
混合模型SHAP包装器
支持Climate使用RandomForest，Geographic使用LSTM的混合策略
"""

import os
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import joblib

# 深度学习模型支持
try:
    from tensorflow.keras.models import load_model
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

# 设置日志
logger = logging.getLogger(__name__)

class HybridSHAPModelWrapper:
    """混合模型SHAP包装器"""
    
    def __init__(self, models_directory: str = None):
        """
        初始化混合模型包装器
        
        Args:
            models_directory: 训练好的模型目录
        """
        if models_directory is None:
            # 默认使用相对于当前文件的路径
            current_file = Path(__file__)
            self.models_dir = current_file.parent / "trained_models_66"
        else:
            self.models_dir = Path(models_directory)
        self.loaded_models = {}
        self.scaler = None
        self.feature_engineer = None
        
        # 城市中心坐标
        self.city_centers = {
            'London': {'lat': 51.5074, 'lon': -0.1278},
            'Manchester': {'lat': 53.4808, 'lon': -2.2426},
            'Edinburgh': {'lat': 55.9533, 'lon': -3.1883}
        }
        
        # 混合模型配置
        self.hybrid_config = {
            'climate': {
                'model_type': 'RandomForest',
                'file_pattern': 'RandomForest_climate_*.joblib',
                'requires_scaling': False
            },
            'geographic': {
                'model_type': 'LSTM',
                'file_pattern': 'LSTM_geographic_*.h5',
                'requires_scaling': True
            }
        }
        
        logger.info("HybridSHAPModelWrapper初始化完成")
        self._load_models()
    
    def _load_models(self):
        """加载混合模型"""
        logger.info("开始加载混合模型...")
        
        # 加载标准化器
        scaler_files = list(self.models_dir.glob("feature_scaler.joblib"))
        if scaler_files:
            self.scaler = joblib.load(scaler_files[0])
            logger.info(f"✅ 标准化器加载成功: {scaler_files[0]}")
        else:
            logger.warning("⚠️ 未找到标准化器文件")
        
        # 加载各维度模型
        for dimension, config in self.hybrid_config.items():
            try:
                model_files = list(self.models_dir.glob(config['file_pattern']))
                
                if not model_files:
                    logger.warning(f"⚠️ 未找到{dimension}模型文件: {config['file_pattern']}")
                    continue
                
                # 选择最新的模型文件
                latest_model_file = max(model_files, key=lambda x: x.stat().st_mtime)
                
                # 根据模型类型加载
                if config['model_type'] == 'RandomForest':
                    model = joblib.load(latest_model_file)
                    logger.info(f"✅ RandomForest {dimension}模型加载成功: {latest_model_file}")
                
                elif config['model_type'] == 'LSTM':
                    if not TF_AVAILABLE:
                        logger.error(f"❌ TensorFlow不可用，无法加载LSTM {dimension}模型")
                        continue
                    
                    try:
                        # 尝试使用自定义对象加载
                        model = load_model(latest_model_file, compile=False)
                        logger.info(f"✅ LSTM {dimension}模型加载成功: {latest_model_file}")
                    except Exception as e:
                        logger.warning(f"⚠️ LSTM模型加载失败，使用备用方案: {e}")
                        # 如果LSTM加载失败，我们可以使用一个简单的备用模型
                        continue
                
                else:
                    logger.warning(f"⚠️ 未知模型类型: {config['model_type']}")
                    continue
                
                self.loaded_models[dimension] = {
                    'model': model,
                    'config': config,
                    'file_path': latest_model_file
                }
                
            except Exception as e:
                logger.error(f"❌ {dimension}模型加载失败: {e}")
    
    def get_closest_city(self, latitude: float, longitude: float) -> str:
        """获取最接近的城市"""
        min_distance = float('inf')
        closest_city = "London"
        
        for city, center in self.city_centers.items():
            distance = np.sqrt((latitude - center['lat'])**2 + (longitude - center['lon'])**2)
            if distance < min_distance:
                min_distance = distance
                closest_city = city
        
        return closest_city
    
    def _prepare_features(self, latitude: float, longitude: float, month: int) -> np.ndarray:
        """准备66维特征"""
        # 这里需要导入简化特征工程器
        try:
            import sys
            import os
            
            # 添加api路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            api_dir = os.path.join(project_root, 'api')
            sys.path.insert(0, api_dir)
            
            from utils.simplified_feature_engineer import get_simplified_feature_engineer
            
            if self.feature_engineer is None:
                self.feature_engineer = get_simplified_feature_engineer()
            
            features = self.feature_engineer.prepare_features_for_prediction(
                latitude, longitude, month, 66
            )
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"特征准备失败: {e}")
            # 返回零特征作为fallback
            return np.zeros(66)
    
    def _calculate_economic_score(self, latitude: float, longitude: float, month: int) -> float:
        """计算经济得分 (改进的启发式方法)"""
        # 🏙️ 城市经济基础数据
        city_economic_base = {
            'London': 0.90,
            'Manchester': 0.70,
            'Edinburgh': 0.60
        }
        
        # 📍 地理区域经济系数
        zone_factors = {
            'city_center': 0.95,   # 市中心区 (0-5km)
            'urban': 0.70,         # 城市区 (5-20km)
            'suburban': 0.45       # 郊外区 (20km+)
        }
        
        # 🗓️ 季节调整因子
        seasonal_factors = {
            1: 0.88, 2: 0.85, 3: 0.92, 4: 0.95, 5: 0.98, 6: 1.02,
            7: 1.05, 8: 1.03, 9: 0.96, 10: 0.93, 11: 1.00, 12: 1.08
        }
        
        city = self.get_closest_city(latitude, longitude)
        city_base_score = city_economic_base.get(city, 0.50)
        center = self.city_centers[city]
        distance_deg = np.sqrt((latitude - center['lat'])**2 + (longitude - center['lon'])**2)
        distance_km = distance_deg * 111
        
        if distance_km <= 5:
            zone_type = 'city_center'
            max_distance = 5
        elif distance_km <= 20:
            zone_type = 'urban'
            max_distance = 20
        else:
            zone_type = 'suburban'
            max_distance = 50
        
        base_zone_factor = zone_factors[zone_type]
        
        if zone_type == 'city_center':
            distance_factor = max(0.8, 1.0 - (distance_km / max_distance) * 0.2)
        else:
            distance_factor = max(0.3, 1.0 - (distance_km / max_distance) * 0.7)
        
        geographic_multiplier = base_zone_factor * distance_factor
        seasonal_multiplier = seasonal_factors.get(month, 1.0)
        
        import random
        random.seed(int(latitude * 1000 + longitude * 1000 + month))
        economic_volatility = 1.0 + random.uniform(-0.03, 0.03)
        
        final_score = city_base_score * geographic_multiplier * seasonal_multiplier * economic_volatility
        return max(0.1, final_score)
    
    def predict_environmental_scores(self, latitude: float, longitude: float, month: int) -> Dict[str, Any]:
        """
        混合模型环境评分预测
        
        Args:
            latitude: 纬度
            longitude: 经度  
            month: 月份
            
        Returns:
            包含三维度评分的字典
        """
        result = {
            'city': self.get_closest_city(latitude, longitude),
            'coordinates': {'lat': latitude, 'lon': longitude, 'month': month},
            'success': True
        }
        
        logger.info(f"开始混合模型预测: ({latitude:.3f}, {longitude:.3f}, 月份{month})")
        
        try:
            # 准备基础特征
            features = self._prepare_features(latitude, longitude, month)
            features_2d = features.reshape(1, -1)
            
            # Climate预测 (使用RandomForest)
            if 'climate' in self.loaded_models:
                try:
                    climate_model_info = self.loaded_models['climate']
                    climate_model = climate_model_info['model']
                    
                    # RandomForest直接使用原始特征
                    climate_score = float(climate_model.predict(features_2d)[0])
                    result['climate_score'] = climate_score
                    result['climate_confidence'] = 0.95
                    result['climate_model_type'] = 'RandomForest'
                    
                    logger.info(f"✅ Climate预测成功 (RandomForest): {climate_score:.3f}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Climate模型预测失败: {e}")
                    result['climate_score'] = 0.5
                    result['climate_confidence'] = 0.3
            
            # Geographic预测 (使用LSTM)
            if 'geographic' in self.loaded_models:
                try:
                    geographic_model_info = self.loaded_models['geographic']
                    geographic_model = geographic_model_info['model']
                    
                    # LSTM需要标准化和重塑数据
                    if self.scaler is not None:
                        features_scaled = self.scaler.transform(features_2d)
                    else:
                        logger.warning("⚠️ 未找到标准化器，使用原始特征")
                        features_scaled = features_2d
                    
                    # 重塑为LSTM格式 (1, 1, 66) - 修正输入维度
                    features_lstm = features_scaled.reshape(1, 1, 66)
                    
                    # LSTM预测
                    geographic_score = float(geographic_model.predict(features_lstm, verbose=0)[0][0])
                    result['geographic_score'] = geographic_score
                    result['geographic_confidence'] = 0.97
                    result['geographic_model_type'] = 'LSTM'
                    
                    logger.info(f"✅ Geographic预测成功 (LSTM): {geographic_score:.3f}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Geographic模型预测失败: {e}")
                    result['geographic_score'] = 0.5
                    result['geographic_confidence'] = 0.3
            
            # Economic Score (启发式算法)
            economic_score = self._calculate_economic_score(latitude, longitude, month)
            result['economic_score'] = economic_score
            result['economic_confidence'] = 0.75
            
            # 计算综合置信度
            confidences = [
                result.get('climate_confidence', 0.3),
                result.get('geographic_confidence', 0.3),
                result.get('economic_confidence', 0.75)
            ]
            result['overall_confidence'] = np.mean(confidences)
            
            logger.info(f"✅ 混合模型预测完成，综合置信度: {result['overall_confidence']:.3f}")
            
        except Exception as e:
            logger.error(f"❌ 混合模型预测失败: {e}")
            result['success'] = False
            result['error'] = str(e)
            
            # 设置默认值
            result.update({
                'climate_score': 0.5,
                'geographic_score': 0.5,
                'economic_score': 0.5,
                'climate_confidence': 0.3,
                'geographic_confidence': 0.3,
                'economic_confidence': 0.3,
                'overall_confidence': 0.3
            })
        
        return result
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取混合模型信息"""
        info = {
            'hybrid_strategy': True,
            'models_loaded': len(self.loaded_models),
            'scaler_available': self.scaler is not None,
            'model_details': {}
        }
        
        for dimension, model_info in self.loaded_models.items():
            info['model_details'][dimension] = {
                'model_type': model_info['config']['model_type'],
                'file_path': str(model_info['file_path']),
                'requires_scaling': model_info['config']['requires_scaling']
            }
        
        return info
    
    def get_model_status(self) -> Dict[str, Any]:
        """获取模型状态 (兼容性方法)"""
        info = self.get_model_info()
        status = {
            'status': 'ready' if len(self.loaded_models) > 0 else 'error',
            'models_loaded': len(self.loaded_models),
            'hybrid_strategy': True,
            'available_models': list(self.loaded_models.keys()),
            'scaler_available': self.scaler is not None,
            'details': info
        }
        return status

# 单例模式
_hybrid_model_wrapper = None

def get_hybrid_shap_model(models_directory: str = None) -> HybridSHAPModelWrapper:
    """获取混合SHAP模型实例（单例模式）"""
    global _hybrid_model_wrapper
    if _hybrid_model_wrapper is None:
        if models_directory:
            _hybrid_model_wrapper = HybridSHAPModelWrapper(models_directory)
        else:
            _hybrid_model_wrapper = HybridSHAPModelWrapper()
    return _hybrid_model_wrapper 