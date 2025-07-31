#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化特征工程器
实现66特征方案：基础滞后 + 简单统计
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class SimplifiedFeatureEngineer:
    """
    简化特征工程器
    
    特征构成 (总计66个):
    - 时间滞后特征 (44个): 当前值 + 1月前 + 3月前 + 12月前
    - 变化率特征 (22个): 年际变化率 + 短期变化率
    """
    
    def __init__(self):
        """初始化简化特征工程器"""
        
        # 环境变量列表 (11个基础变量)
        self.environmental_variables = [
            'temperature',
            'humidity', 
            'wind_speed',
            'precipitation',
            'atmospheric_pressure',
            'solar_radiation',
            'soil_temperature_0_7cm',
            'soil_moisture_7_28cm',
            'reference_evapotranspiration',
            'urban_flood_risk',
            'NO2'
        ]
        
        # 滞后时间点定义
        self.lag_periods = {
            'current': 0,     # 当前值
            'lag_1m': 1,      # 1月前
            'lag_3m': 3,      # 3月前
            'lag_12m': 12     # 12月前
        }
        
        logger.info("SimplifiedFeatureEngineer初始化完成")
        logger.info(f"环境变量数量: {len(self.environmental_variables)}")
        logger.info(f"预期特征总数: {self._calculate_expected_features()}")
    
    def _calculate_expected_features(self) -> int:
        """计算预期的特征总数"""
        # 时间滞后特征: 11个变量 × 4个时间点 = 44个
        lag_features = len(self.environmental_variables) * len(self.lag_periods)
        
        # 变化率特征: 11个变量 × 2种变化率 = 22个
        change_features = len(self.environmental_variables) * 2
        
        total = lag_features + change_features
        return total
    
    def prepare_features_for_prediction(self, latitude: float, longitude: float, 
                                       month: int, target_features: int) -> np.ndarray:
        """
        为预测准备简化特征
        
        Args:
            latitude: 纬度
            longitude: 经度
            month: 月份
            target_features: 目标特征数量 (应该是66)
            
        Returns:
            包含66个特征的numpy数组
        """
        logger.info(f"开始为坐标 ({latitude}, {longitude}) 构建简化特征")
        
        try:
            # 导入数据收集器
            from utils.real_time_environmental_data_collector import get_environmental_collector
            collector = get_environmental_collector()
            
            # 🕐 步骤1: 收集所需时间点的环境数据
            environmental_data = self._collect_temporal_data(collector, latitude, longitude)
            
            # 🏗️ 步骤2: 构建时间滞后特征
            lag_features = self._build_lag_features(environmental_data)
            
            # 📈 步骤3: 计算变化率特征
            change_features = self._calculate_change_features(environmental_data)
            
            # 🔧 步骤4: 组合所有特征
            all_features = np.concatenate([lag_features, change_features])
            
            # ✅ 步骤5: 验证特征数量
            expected_count = self._calculate_expected_features()
            actual_count = len(all_features)
            
            if actual_count != expected_count:
                logger.warning(f"特征数量不匹配: 实际{actual_count} vs 预期{expected_count}")
            
            if target_features != expected_count:
                logger.warning(f"目标特征数量不匹配: 目标{target_features} vs 预期{expected_count}")
            
            logger.info(f"简化特征构建完成: {actual_count} 个特征")
            return all_features
            
        except Exception as e:
            logger.error(f"简化特征构建失败: {e}")
            raise
    
    def _collect_temporal_data(self, collector, latitude: float, longitude: float) -> Dict:
        """收集不同时间点的环境数据"""
        
        temporal_data = {}
        
        # 获取当前环境数据
        logger.info("📊 获取当前环境数据...")
        temporal_data['current'] = collector.get_current_environmental_data(latitude, longitude)
        
        # 获取历史滞后数据
        logger.info("📚 获取历史滞后数据...")
        historical_data = collector.get_historical_lag_data(latitude, longitude)
        
        # 映射历史数据到我们需要的时间点
        temporal_data['lag_1m'] = historical_data.get('lag_1', {})
        temporal_data['lag_3m'] = historical_data.get('lag_3', {})
        temporal_data['lag_12m'] = historical_data.get('lag_12', {})
        
        # 验证数据完整性
        for period, data in temporal_data.items():
            if not data:
                logger.warning(f"缺少{period}时间点的数据，将使用当前数据填充")
                temporal_data[period] = temporal_data['current'].copy()
        
        logger.info(f"时间数据收集完成: {len(temporal_data)} 个时间点")
        return temporal_data
    
    def _build_lag_features(self, temporal_data: Dict) -> np.ndarray:
        """构建时间滞后特征 (44个)"""
        
        lag_features = []
        
        # 按时间点顺序构建特征
        for period in ['current', 'lag_1m', 'lag_3m', 'lag_12m']:
            period_data = temporal_data[period]
            
            # 按固定顺序提取环境变量
            for var in self.environmental_variables:
                value = period_data.get(var, 0.0)  # 缺失值用0填充
                lag_features.append(float(value))
        
        features_array = np.array(lag_features)
        logger.info(f"时间滞后特征构建完成: {len(features_array)} 个")
        
        return features_array
    
    def _calculate_change_features(self, temporal_data: Dict) -> np.ndarray:
        """计算变化率特征 (22个)"""
        
        change_features = []
        
        current_data = temporal_data['current']
        lag_1m_data = temporal_data['lag_1m']
        lag_12m_data = temporal_data['lag_12m']
        
        # 为每个环境变量计算变化率
        for var in self.environmental_variables:
            current_val = current_data.get(var, 0.0)
            lag_1m_val = lag_1m_data.get(var, current_val)
            lag_12m_val = lag_12m_data.get(var, current_val)
            
            # 📈 年际变化率 = (当前值 - 12月前值) / |12月前值|
            if abs(lag_12m_val) > 1e-6:  # 避免除零
                yearly_change = (current_val - lag_12m_val) / abs(lag_12m_val)
            else:
                yearly_change = 0.0
            
            # 📈 短期变化率 = (当前值 - 1月前值) / |1月前值|
            if abs(lag_1m_val) > 1e-6:  # 避免除零
                monthly_change = (current_val - lag_1m_val) / abs(lag_1m_val)
            else:
                monthly_change = 0.0
            
            # 限制变化率在合理范围内 [-2, 2] (即±200%变化)
            yearly_change = np.clip(yearly_change, -2.0, 2.0)
            monthly_change = np.clip(monthly_change, -2.0, 2.0)
            
            change_features.extend([yearly_change, monthly_change])
        
        features_array = np.array(change_features)
        logger.info(f"变化率特征构建完成: {len(features_array)} 个")
        
        return features_array
    
    def get_feature_names(self) -> List[str]:
        """获取所有特征的名称（用于调试和分析）"""
        
        feature_names = []
        
        # 时间滞后特征名称
        for period in ['current', 'lag_1m', 'lag_3m', 'lag_12m']:
            for var in self.environmental_variables:
                feature_names.append(f"{var}_{period}")
        
        # 变化率特征名称
        for var in self.environmental_variables:
            feature_names.append(f"{var}_yearly_change")
            feature_names.append(f"{var}_monthly_change")
        
        return feature_names
    
    def analyze_features(self, features: np.ndarray) -> Dict:
        """分析特征质量"""
        
        analysis = {
            'count': len(features),
            'mean': float(features.mean()),
            'std': float(features.std()),
            'min': float(features.min()),
            'max': float(features.max()),
            'zeros': int((features == 0).sum()),
            'negatives': int((features < 0).sum()),
            'positives': int((features > 0).sum()),
            'range': float(features.max() - features.min()),
            'inf_count': int(np.isinf(features).sum()),
            'nan_count': int(np.isnan(features).sum())
        }
        
        # 质量评估
        quality_issues = []
        
        if analysis['inf_count'] > 0:
            quality_issues.append(f"包含{analysis['inf_count']}个无穷值")
        
        if analysis['nan_count'] > 0:
            quality_issues.append(f"包含{analysis['nan_count']}个NaN值")
        
        # 检查是否有异常大的值
        if abs(analysis['mean']) > 100:
            quality_issues.append(f"特征均值可能过大: {analysis['mean']:.1f}")
        
        if analysis['std'] > 1000:
            quality_issues.append(f"特征标准差过大: {analysis['std']:.1f}")
        
        if analysis['max'] > 10000:
            quality_issues.append(f"特征最大值过大: {analysis['max']:.1f}")
        
        analysis['quality_issues'] = quality_issues
        analysis['quality_status'] = 'good' if len(quality_issues) == 0 else 'warning'
        
        return analysis

# 单例模式
_simplified_engineer = None

def get_simplified_feature_engineer():
    """获取简化特征工程器单例"""
    global _simplified_engineer
    if _simplified_engineer is None:
        _simplified_engineer = SimplifiedFeatureEngineer()
    return _simplified_engineer 