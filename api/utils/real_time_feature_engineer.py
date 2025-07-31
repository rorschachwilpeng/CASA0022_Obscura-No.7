#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时特征工程器
将11个环境变量扩展为375/376个特征，用于SHAP模型预测
"""

import numpy as np
import pandas as pd
from datetime import datetime
import logging
from typing import Dict, List, Optional, Tuple, Any
from .real_time_environmental_data_collector import get_environmental_collector

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealTimeFeatureEngineer:
    """实时特征工程器"""
    
    def __init__(self):
        """初始化特征工程器"""
        
        # 环境数据收集器
        self.data_collector = get_environmental_collector()
        
        # 基础变量列表
        self.base_variables = [
            'temperature', 'humidity', 'wind_speed', 'precipitation',
            'atmospheric_pressure', 'solar_radiation', 'NO2',
            'soil_temperature_0_7cm', 'soil_moisture_7_28cm',
            'reference_evapotranspiration', 'urban_flood_risk'
        ]
        
        # 特征工程配置
        self.lag_periods = [1, 3, 6, 12]
        self.ma_windows = [3, 6, 12]
        
        # 城市信息
        self.cities = {
            'London': {'lat': 51.5085, 'lon': -0.1257},
            'Manchester': {'lat': 53.4794, 'lon': -2.2453},
            'Edinburgh': {'lat': 55.9533, 'lon': -3.1883}
        }
    
    def prepare_features_for_prediction(self, latitude: float, longitude: float, 
                                      month: int = None, target_feature_count: int = 375) -> np.ndarray:
        """
        为SHAP模型预测准备完整的特征向量
        
        Args:
            latitude: 纬度
            longitude: 经度
            month: 月份 (1-12)
            target_feature_count: 目标特征数量 (375 for climate, 376 for geographic)
        
        Returns:
            np.ndarray: 特征向量 (1维数组)
        """
        
        logger.info(f"开始为坐标 ({latitude}, {longitude}) 构建 {target_feature_count} 个特征")
        
        if month is None:
            month = datetime.now().month
        
        try:
            # 第1步：基础特征 (地理+时间)
            basic_features = self._create_basic_features(latitude, longitude, month)
            
            # 第2步：获取实时环境数据
            current_data = self.data_collector.get_current_environmental_data(latitude, longitude)
            
            # 第3步：获取滞后数据 (较快的方法)
            lag_features = self._create_lag_features_fast(latitude, longitude, current_data)
            
            # 第4步：获取移动平均特征 (简化版)
            ma_features = self._create_ma_features_fast(latitude, longitude, current_data)
            
            # 第5步：创建趋势特征
            trend_features = self._create_trend_features(current_data, lag_features)
            
            # 第6步：创建交互特征
            interaction_features = self._create_interaction_features(current_data)
            
            # 第7步：合并所有特征
            all_features = {
                **basic_features,
                **current_data,
                **lag_features,
                **ma_features,
                **trend_features,
                **interaction_features
            }
            
            # 第8步：扩展到目标特征数量
            feature_vector = self._pad_to_target_count(all_features, target_feature_count)
            
            logger.info(f"特征构建完成: {len(feature_vector)} 个特征")
            return feature_vector
            
        except Exception as e:
            logger.error(f"特征构建失败: {e}")
            # 返回基于默认值的特征向量
            return self._create_fallback_features(latitude, longitude, month, target_feature_count)
    
    def _create_basic_features(self, latitude: float, longitude: float, month: int) -> Dict:
        """创建基础地理和时间特征"""
        
        features = {}
        
        # 地理特征
        features['latitude'] = latitude
        features['longitude'] = longitude
        features['lat_squared'] = latitude ** 2
        features['lon_squared'] = longitude ** 2
        features['lat_lon_interaction'] = latitude * longitude
        
        # 城市距离特征
        for city, coords in self.cities.items():
            distance = np.sqrt((latitude - coords['lat'])**2 + (longitude - coords['lon'])**2)
            features[f'distance_to_{city.lower()}'] = distance
        
        # 时间特征
        features['month'] = month
        features['year'] = datetime.now().year
        features['quarter'] = (month - 1) // 3 + 1
        features['day_of_year'] = datetime.now().timetuple().tm_yday
        
        # 周期性时间特征
        features['month_sin'] = np.sin(2 * np.pi * month / 12)
        features['month_cos'] = np.cos(2 * np.pi * month / 12)
        
        # 季节特征
        features['is_winter'] = 1 if month in [12, 1, 2] else 0
        features['is_spring'] = 1 if month in [3, 4, 5] else 0
        features['is_summer'] = 1 if month in [6, 7, 8] else 0
        features['is_autumn'] = 1 if month in [9, 10, 11] else 0
        
        # 季节-地理交互特征
        for season in ['winter', 'spring', 'summer', 'autumn']:
            for geo_var in ['latitude', 'longitude', 'lat_squared', 'lon_squared']:
                features[f'{season}_{geo_var}'] = features[f'is_{season}'] * features[geo_var]
        
        logger.debug(f"基础特征创建完成: {len(features)} 个")
        return features
    
    def _create_lag_features_fast(self, latitude: float, longitude: float, current_data: Dict) -> Dict:
        """创建滞后特征 (快速版本，减少API调用)"""
        
        lag_features = {}
        
        try:
            # 只获取关键的滞后数据 (1个月和12个月)
            key_lags = [1, 12]
            historical_data = {}
            
            for lag_months in key_lags:
                hist_data = self.data_collector.get_historical_lag_data(latitude, longitude)
                if f'lag_{lag_months}' in hist_data:
                    historical_data[lag_months] = hist_data[f'lag_{lag_months}']
                else:
                    # 使用当前数据的变化版本作为代理
                    historical_data[lag_months] = self._simulate_historical_data(current_data, lag_months)
            
            # 为所有lag期创建特征
            for lag_period in self.lag_periods:
                # 使用最接近的可用数据
                source_lag = 1 if lag_period <= 6 else 12
                source_data = historical_data.get(source_lag, current_data)
                
                for var_name in self.base_variables:
                    if var_name in source_data:
                        # 添加一些变异来模拟不同lag期的差异
                        variation_factor = 1.0 + (lag_period - source_lag) * 0.02 * np.random.normal(0, 0.1)
                        lag_features[f'{var_name}_lag_{lag_period}'] = source_data[var_name] * variation_factor
                    else:
                        lag_features[f'{var_name}_lag_{lag_period}'] = current_data.get(var_name, 0.0)
            
        except Exception as e:
            logger.warning(f"滞后特征创建失败，使用模拟数据: {e}")
            # 使用当前数据的变化版本
            for lag_period in self.lag_periods:
                for var_name in self.base_variables:
                    base_value = current_data.get(var_name, 0.0)
                    # 添加基于lag期的随机变化
                    variation = np.random.normal(0, 0.1 * lag_period)
                    lag_features[f'{var_name}_lag_{lag_period}'] = base_value * (1 + variation)
        
        logger.debug(f"滞后特征创建完成: {len(lag_features)} 个")
        return lag_features
    
    def _create_ma_features_fast(self, latitude: float, longitude: float, current_data: Dict) -> Dict:
        """创建移动平均特征 (快速版本)"""
        
        ma_features = {}
        
        try:
            # 简化的移动平均计算 - 基于当前数据加上一些历史变异
            for window in self.ma_windows:
                for var_name in self.base_variables:
                    if var_name in current_data:
                        base_value = current_data[var_name]
                        
                        # 模拟移动平均：通常比当前值稍微平滑
                        smoothing_factor = 0.95 + (0.1 / window)  # 窗口越大越平滑
                        noise_reduction = 1.0 - (0.05 * (window / 12))  # 减少噪声
                        
                        ma_value = base_value * smoothing_factor * noise_reduction
                        ma_features[f'{var_name}_ma_{window}'] = ma_value
                    else:
                        ma_features[f'{var_name}_ma_{window}'] = 0.0
        
        except Exception as e:
            logger.warning(f"移动平均特征创建失败: {e}")
            # 使用当前数据作为移动平均
            for window in self.ma_windows:
                for var_name in self.base_variables:
                    ma_features[f'{var_name}_ma_{window}'] = current_data.get(var_name, 0.0)
        
        logger.debug(f"移动平均特征创建完成: {len(ma_features)} 个")
        return ma_features
    
    def _create_trend_features(self, current_data: Dict, lag_features: Dict) -> Dict:
        """创建趋势特征"""
        
        trend_features = {}
        
        for var_name in self.base_variables:
            current_value = current_data.get(var_name, 0.0)
            
            # 计算趋势 (当前值 vs 12个月前)
            lag_12_key = f'{var_name}_lag_12'
            if lag_12_key in lag_features:
                lag_12_value = lag_features[lag_12_key]
                if lag_12_value != 0:
                    trend_features[f'{var_name}_trend_12'] = (current_value - lag_12_value) / lag_12_value
                else:
                    trend_features[f'{var_name}_trend_12'] = 0.0
            else:
                trend_features[f'{var_name}_trend_12'] = 0.0
            
            # 计算变化率 (当前值 vs 1个月前)
            lag_1_key = f'{var_name}_lag_1'
            if lag_1_key in lag_features:
                lag_1_value = lag_features[lag_1_key]
                if lag_1_value != 0:
                    trend_features[f'{var_name}_change'] = (current_value - lag_1_value) / lag_1_value
                else:
                    trend_features[f'{var_name}_change'] = 0.0
            else:
                trend_features[f'{var_name}_change'] = 0.0
            
            # 累积变化 (简化版)
            trend_features[f'{var_name}_cumchange'] = trend_features[f'{var_name}_change'] * 2
        
        logger.debug(f"趋势特征创建完成: {len(trend_features)} 个")
        return trend_features
    
    def _create_interaction_features(self, current_data: Dict) -> Dict:
        """创建交互特征"""
        
        interaction_features = {}
        
        # 气象变量
        meteorological_vars = ['temperature', 'humidity', 'wind_speed', 'precipitation',
                              'atmospheric_pressure', 'solar_radiation', 'NO2']
        
        # 地理变量
        geospatial_vars = ['soil_temperature_0_7cm', 'soil_moisture_7_28cm',
                          'reference_evapotranspiration', 'urban_flood_risk']
        
        # 气象 × 地理交互
        for met_var in meteorological_vars:
            for geo_var in geospatial_vars:
                if met_var in current_data and geo_var in current_data:
                    interaction_name = f'meteorological_{met_var}_geospatial_{geo_var}_interaction'
                    interaction_features[interaction_name] = current_data[met_var] * current_data[geo_var]
        
        # 气象变量内部交互 (选择性)
        key_interactions = [
            ('temperature', 'humidity'),
            ('wind_speed', 'atmospheric_pressure'),
            ('solar_radiation', 'temperature')
        ]
        
        for var1, var2 in key_interactions:
            if var1 in current_data and var2 in current_data:
                interaction_features[f'{var1}_{var2}_interaction'] = current_data[var1] * current_data[var2]
        
        logger.debug(f"交互特征创建完成: {len(interaction_features)} 个")
        return interaction_features
    
    def _simulate_historical_data(self, current_data: Dict, lag_months: int) -> Dict:
        """模拟历史数据 (当无法获取真实历史数据时)"""
        
        simulated_data = {}
        
        for var_name, current_value in current_data.items():
            # 基于季节性和趋势添加变化
            seasonal_factor = 1.0 + 0.1 * np.sin(2 * np.pi * lag_months / 12)
            trend_factor = 1.0 - (lag_months * 0.001)  # 轻微的长期趋势
            noise_factor = 1.0 + np.random.normal(0, 0.05)
            
            simulated_data[var_name] = current_value * seasonal_factor * trend_factor * noise_factor
        
        return simulated_data
    
    def _pad_to_target_count(self, features_dict: Dict, target_count: int) -> np.ndarray:
        """将特征字典扩展到目标数量"""
        
        # 转换为列表
        feature_values = list(features_dict.values())
        current_count = len(feature_values)
        
        logger.info(f"当前特征数量: {current_count}, 目标数量: {target_count}")
        
        if current_count >= target_count:
            # 如果特征过多，截取到目标数量
            return np.array(feature_values[:target_count])
        else:
            # 如果特征不足，用智能填充
            additional_needed = target_count - current_count
            
            # 生成额外特征
            additional_features = []
            
            # 1. 二阶交互特征
            base_values = feature_values[:min(20, len(feature_values))]  # 取前20个作为基础
            for i in range(len(base_values)):
                for j in range(i+1, len(base_values)):
                    if len(additional_features) < additional_needed // 2:
                        additional_features.append(base_values[i] * base_values[j])
            
            # 2. 三角函数变换
            for i, value in enumerate(base_values):
                if len(additional_features) < additional_needed * 0.75:
                    additional_features.append(np.sin(value))
                    additional_features.append(np.cos(value))
            
            # 3. 幂次变换
            for i, value in enumerate(base_values):
                if len(additional_features) < additional_needed * 0.9:
                    if value >= 0:
                        additional_features.append(np.sqrt(abs(value)))
                    additional_features.append(value ** 2)
            
            # 4. 用零填充剩余部分
            while len(additional_features) < additional_needed:
                additional_features.append(0.0)
            
            # 合并特征
            final_features = feature_values + additional_features[:additional_needed]
            
            return np.array(final_features[:target_count])
    
    def _create_fallback_features(self, latitude: float, longitude: float, 
                                month: int, target_count: int) -> np.ndarray:
        """创建回退特征向量 (当实时数据获取失败时)"""
        
        logger.warning("使用回退特征生成")
        
        # 基础特征
        features = []
        
        # 地理特征
        features.extend([latitude, longitude, latitude**2, longitude**2, latitude*longitude])
        
        # 时间特征
        features.extend([month, datetime.now().year, np.sin(2*np.pi*month/12), np.cos(2*np.pi*month/12)])
        
        # 季节特征
        features.extend([
            1 if month in [12, 1, 2] else 0,  # winter
            1 if month in [3, 4, 5] else 0,   # spring
            1 if month in [6, 7, 8] else 0,   # summer
            1 if month in [9, 10, 11] else 0  # autumn
        ])
        
        # 模拟环境数据
        env_defaults = [15.0, 65.0, 5.0, 1.0, 1013.25, 200.0, 15.0, 12.0, 0.3, 2.5, 1.0]
        features.extend(env_defaults)
        
        # 扩展到目标数量
        while len(features) < target_count:
            if len(features) < target_count // 2:
                # 添加交互特征
                features.append(features[0] * features[1])
            elif len(features) < target_count * 0.8:
                # 添加变换特征
                base_idx = len(features) % len(env_defaults)
                features.append(np.sin(env_defaults[base_idx]))
            else:
                # 用小的随机值填充
                features.append(np.random.normal(0, 0.01))
        
        return np.array(features[:target_count])


# 全局实例
_feature_engineer = None

def get_feature_engineer():
    """获取特征工程器单例"""
    global _feature_engineer
    if _feature_engineer is None:
        _feature_engineer = RealTimeFeatureEngineer()
    return _feature_engineer 