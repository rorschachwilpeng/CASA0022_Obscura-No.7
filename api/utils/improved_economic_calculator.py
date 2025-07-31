#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进的Economic Score计算器
解决当前启发式算法过于简化的问题
"""

import logging
import math
import random
from typing import Dict, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class ImprovedEconomicCalculator:
    """
    改进的经济分数计算器
    
    考虑更多经济因素：
    1. 城市规模和经济活力
    2. 地理位置（市中心、郊区、乡村）
    3. 季节性经济波动
    4. 随机经济周期因素
    """
    
    def __init__(self):
        """初始化经济计算器"""
        
        # 城市经济基础数据 (更真实的经济指标)
        self.city_economic_data = {
            'London': {
                'base_gdp_score': 0.85,        # 基础GDP水平 (0-1)
                'economic_diversity': 0.90,     # 经济多样性
                'innovation_index': 0.88,       # 创新指数
                'employment_rate': 0.82,        # 就业率
                'center': {'lat': 51.5074, 'lon': -0.1278}
            },
            'Manchester': {
                'base_gdp_score': 0.72,
                'economic_diversity': 0.75,
                'innovation_index': 0.71,
                'employment_rate': 0.78,
                'center': {'lat': 53.4808, 'lon': -2.2426}
            },
            'Edinburgh': {
                'base_gdp_score': 0.68,
                'economic_diversity': 0.70,
                'innovation_index': 0.74,
                'employment_rate': 0.80,
                'center': {'lat': 55.9533, 'lon': -3.1883}
            }
        }
        
        # 地理位置经济影响因子
        self.location_factors = {
            'urban_core': (0.0, 0.05),      # 市中心5公里内
            'urban': (0.05, 0.15),          # 城市区域
            'suburban': (0.15, 0.40),       # 郊区
            'rural': (0.40, float('inf'))   # 乡村
        }
        
        # 季节性经济影响 (更细致的季节调整)
        self.seasonal_factors = {
            1: 0.88,   # 1月：后圣诞消费低迷
            2: 0.85,   # 2月：经济活动较低
            3: 0.92,   # 3月：春季复苏开始
            4: 0.95,   # 4月：稳定增长
            5: 0.98,   # 5月：良好增长
            6: 1.02,   # 6月：夏季旅游开始
            7: 1.05,   # 7月：旅游旺季
            8: 1.03,   # 8月：持续旺季
            9: 0.96,   # 9月：回归正常
            10: 0.93,  # 10月：秋季调整
            11: 1.00,  # 11月：节前消费
            12: 1.08   # 12月：圣诞经济
        }
        
        logger.info("ImprovedEconomicCalculator初始化完成")
    
    def get_closest_city(self, latitude: float, longitude: float) -> str:
        """找到最近的城市"""
        min_distance = float('inf')
        closest_city = 'London'
        
        for city, data in self.city_economic_data.items():
            center = data['center']
            distance = math.sqrt((latitude - center['lat'])**2 + (longitude - center['lon'])**2)
            if distance < min_distance:
                min_distance = distance
                closest_city = city
        
        return closest_city
    
    def calculate_location_factor(self, latitude: float, longitude: float, city: str) -> Tuple[float, str]:
        """计算地理位置对经济的影响"""
        center = self.city_economic_data[city]['center']
        distance = math.sqrt((latitude - center['lat'])**2 + (longitude - center['lon'])**2)
        
        # 确定位置类型
        location_type = 'rural'
        for loc_type, (min_dist, max_dist) in self.location_factors.items():
            if min_dist <= distance < max_dist:
                location_type = loc_type
                break
        
        # 计算位置因子 (距离越近，经济活动越强)
        if location_type == 'urban_core':
            location_factor = 1.0 - distance * 2  # 市中心衰减较慢
        elif location_type == 'urban':
            location_factor = 0.9 - distance * 1.5
        elif location_type == 'suburban':
            location_factor = 0.7 - distance * 0.8
        else:  # rural
            location_factor = 0.4 - distance * 0.3
        
        # 确保在合理范围内
        location_factor = max(0.1, min(1.0, location_factor))
        
        return location_factor, location_type
    
    def calculate_economic_cycle_factor(self, month: int) -> float:
        """计算经济周期因子 (增加一些随机性模拟真实经济波动)"""
        # 基础季节因子
        base_seasonal = self.seasonal_factors.get(month, 1.0)
        
        # 添加小幅随机经济波动 (±5%)
        random.seed(month * 1000)  # 使用月份作为种子，确保同月份结果一致
        cycle_variation = 1.0 + random.uniform(-0.05, 0.05)
        
        return base_seasonal * cycle_variation
    
    def calculate_improved_economic_score(self, latitude: float, longitude: float, month: int) -> Dict[str, any]:
        """
        计算改进的经济分数
        
        Returns:
            包含详细经济分析的字典
        """
        # 1. 确定城市和基础数据
        city = self.get_closest_city(latitude, longitude)
        city_data = self.city_economic_data[city]
        
        # 2. 计算各个因子
        location_factor, location_type = self.calculate_location_factor(latitude, longitude, city)
        seasonal_factor = self.calculate_economic_cycle_factor(month)
        
        # 3. 综合经济分数计算
        economic_components = {
            'base_gdp': city_data['base_gdp_score'],
            'economic_diversity': city_data['economic_diversity'],
            'innovation': city_data['innovation_index'],
            'employment': city_data['employment_rate']
        }
        
        # 计算基础经济实力 (各指标加权平均)
        base_economic_strength = (
            economic_components['base_gdp'] * 0.35 +
            economic_components['economic_diversity'] * 0.25 +
            economic_components['innovation'] * 0.25 +
            economic_components['employment'] * 0.15
        )
        
        # 应用地理和季节调整
        final_score = base_economic_strength * location_factor * seasonal_factor
        
        # 确保在合理范围内 [0.1, 1.0]
        final_score = max(0.1, min(1.0, final_score))
        
        return {
            'economic_score': final_score,
            'city': city,
            'location_type': location_type,
            'components': economic_components,
            'factors': {
                'base_strength': base_economic_strength,
                'location_factor': location_factor,
                'seasonal_factor': seasonal_factor
            },
            'analysis': self._generate_economic_analysis(final_score, city, location_type, month)
        }
    
    def _generate_economic_analysis(self, score: float, city: str, location_type: str, month: int) -> str:
        """生成经济分数解释"""
        month_names = ['', '一月', '二月', '三月', '四月', '五月', '六月', 
                      '七月', '八月', '九月', '十月', '十一月', '十二月']
        
        if score >= 0.8:
            level = "强劲"
        elif score >= 0.6:
            level = "良好"
        elif score >= 0.4:
            level = "中等"
        else:
            level = "疲软"
        
        location_desc = {
            'urban_core': '市中心核心区域',
            'urban': '城市区域',
            'suburban': '郊区',
            'rural': '乡村地区'
        }
        
        return f"{city}{location_desc[location_type]}{month_names[month]}经济活动{level}"

# 单例模式
_economic_calculator = None

def get_improved_economic_calculator():
    """获取改进的经济计算器单例"""
    global _economic_calculator
    if _economic_calculator is None:
        _economic_calculator = ImprovedEconomicCalculator()
    return _economic_calculator 