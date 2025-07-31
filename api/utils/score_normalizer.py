#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Score Normalizer for SHAP Environmental Prediction System
将SHAP框架的原始分数归一化到0-100百分制
"""

import logging
from typing import Dict, Tuple, Any
import numpy as np

# 设置日志
logger = logging.getLogger(__name__)

class ScoreNormalizer:
    """
    SHAP分数归一化器
    
    将Climate、Geographic、Economic三个维度的原始分数
    归一化到[0,100]区间，并计算最终的环境变化结果分数
    """
    
    def __init__(self):
        """初始化归一化器，设置各维度的原始分数范围"""
        
        # 基于实际ML模型输出和测试数据确定的分数范围
        self.score_ranges = {
            'climate': {
                'min': -2.5,    # ML模型输出最小值（含安全边距）
                'max': 1.6,     # ML模型输出最大值（含安全边距）
                'source': 'RandomForestRegressor'
            },
            'geographic': {
                'min': -0.4,    # ML模型输出最小值（含安全边距）
                'max': 1.9,     # ML模型输出最大值（含安全边距）
                'source': 'RandomForestRegressor'
            },
            'economic': {
                'min': 0.1,     # 改进启发式算法最小值
                'max': 1.2,     # 改进启发式算法最大值 (移除上限后)
                'source': 'Improved Heuristic Algorithm'
            }
        }
        
        # 权重配置 (总和为1.0)
        self.weights = {
            'climate': 0.3,     # 30% - 气象因素
            'economic': 0.4,    # 40% - 经济因素（最重要）
            'geographic': 0.3   # 30% - 地理因素
        }
        
        logger.info("ScoreNormalizer初始化完成")
        self._log_configuration()
    
    def _log_configuration(self):
        """记录归一化器配置信息"""
        logger.info("归一化配置:")
        for dimension, config in self.score_ranges.items():
            logger.info(f"  {dimension}: [{config['min']}, {config['max']}] ({config['source']})")
        
        logger.info("权重配置:")
        for dimension, weight in self.weights.items():
            logger.info(f"  {dimension}: {weight*100}%")
    
    def normalize_score(self, raw_score: float, dimension: str) -> float:
        """
        将原始分数归一化到[0, 100]区间
        
        Args:
            raw_score: 原始分数
            dimension: 维度名称 ('climate', 'geographic', 'economic')
            
        Returns:
            归一化后的分数 [0, 100]
        """
        if dimension not in self.score_ranges:
            raise ValueError(f"未知维度: {dimension}。支持的维度: {list(self.score_ranges.keys())}")
        
        min_val = self.score_ranges[dimension]['min']
        max_val = self.score_ranges[dimension]['max']
        
        # 线性归一化到[0, 100]
        normalized = (raw_score - min_val) / (max_val - min_val) * 100
        
        # 确保在有效范围内，但记录超出范围的情况
        if normalized < 0:
            logger.warning(f"{dimension}分数 {raw_score} 低于预期范围 [{min_val}, {max_val}]")
            normalized = 0
        elif normalized > 100:
            logger.warning(f"{dimension}分数 {raw_score} 高于预期范围 [{min_val}, {max_val}]")
            normalized = 100
        
        return normalized
    
    def calculate_environment_outcome(self, climate_norm: float, economic_norm: float, 
                                    geographic_norm: float) -> float:
        """
        计算最终的环境变化结果分数
        
        Args:
            climate_norm: 归一化后的Climate分数 [0, 100]
            economic_norm: 归一化后的Economic分数 [0, 100]
            geographic_norm: 归一化后的Geographic分数 [0, 100]
            
        Returns:
            最终环境变化结果分数 [0, 100]
        """
        final_score = (
            self.weights['climate'] * climate_norm +
            self.weights['economic'] * economic_norm +
            self.weights['geographic'] * geographic_norm
        )
        
        # 确保结果在[0, 100]范围内
        final_score = max(0, min(100, final_score))
        
        return final_score
    
    def normalize_shap_result(self, shap_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        对完整的SHAP结果进行归一化处理
        
        Args:
            shap_result: 包含原始分数的SHAP结果字典
            
        Returns:
            包含归一化分数的结果字典
        """
        if not shap_result.get('success', False):
            logger.warning("SHAP结果不成功，跳过归一化")
            return shap_result
        
        # 提取原始分数
        raw_climate = shap_result.get('climate_score')
        raw_geographic = shap_result.get('geographic_score')
        raw_economic = shap_result.get('economic_score')
        
        if any(score is None for score in [raw_climate, raw_geographic, raw_economic]):
            logger.error("原始分数缺失，无法进行归一化")
            return shap_result
        
        # 归一化各维度分数
        try:
            climate_normalized = self.normalize_score(raw_climate, 'climate')
            geographic_normalized = self.normalize_score(raw_geographic, 'geographic')
            economic_normalized = self.normalize_score(raw_economic, 'economic')
            
            # 计算最终分数
            final_outcome = self.calculate_environment_outcome(
                climate_normalized, economic_normalized, geographic_normalized
            )
            
            # 构建归一化结果
            normalized_result = shap_result.copy()
            normalized_result.update({
                # 保留原始分数（用于调试）
                'raw_scores': {
                    'climate': raw_climate,
                    'geographic': raw_geographic,
                    'economic': raw_economic
                },
                
                # 归一化分数 [0, 100]
                'normalized_scores': {
                    'climate': round(climate_normalized, 2),
                    'geographic': round(geographic_normalized, 2),
                    'economic': round(economic_normalized, 2)
                },
                
                # 最终环境变化结果 [0, 100]
                'environment_change_outcome': round(final_outcome, 1),
                
                # 贡献度分析
                'contribution_breakdown': {
                    'climate_contribution': round(self.weights['climate'] * climate_normalized, 2),
                    'economic_contribution': round(self.weights['economic'] * economic_normalized, 2),
                    'geographic_contribution': round(self.weights['geographic'] * geographic_normalized, 2)
                },
                
                # 元数据
                'normalization_metadata': {
                    'score_ranges_used': self.score_ranges,
                    'weights_used': self.weights,
                    'normalization_timestamp': np.datetime64('now').astype(str)
                }
            })
            
            logger.info(f"归一化完成: C={climate_normalized:.1f}, E={economic_normalized:.1f}, "
                       f"G={geographic_normalized:.1f} → 最终={final_outcome:.1f}")
            
            return normalized_result
            
        except Exception as e:
            logger.error(f"归一化过程中发生错误: {e}")
            return shap_result
    
    def get_score_interpretation(self, final_score: float) -> str:
        """
        解释最终环境变化分数的含义
        
        Args:
            final_score: 最终分数 [0, 100]
            
        Returns:
            分数解释文本
        """
        if final_score >= 80:
            return "环境状况优秀，各项指标表现良好"
        elif final_score >= 65:
            return "环境状况良好，大部分指标表现积极"
        elif final_score >= 50:
            return "环境状况中等，存在改善空间"
        elif final_score >= 35:
            return "环境状况需要关注，多项指标存在挑战"
        else:
            return "环境状况需要紧急改善，多项指标表现不佳"
    
    def update_score_ranges(self, new_ranges: Dict[str, Tuple[float, float]]):
        """
        更新分数范围配置（用于动态调整）
        
        Args:
            new_ranges: 新的分数范围字典
        """
        for dimension, (min_val, max_val) in new_ranges.items():
            if dimension in self.score_ranges:
                self.score_ranges[dimension]['min'] = min_val
                self.score_ranges[dimension]['max'] = max_val
                logger.info(f"更新 {dimension} 分数范围为 [{min_val}, {max_val}]")
        
        self._log_configuration()

# 单例实例
_normalizer_instance = None

def get_score_normalizer() -> ScoreNormalizer:
    """获取分数归一化器单例实例"""
    global _normalizer_instance
    if _normalizer_instance is None:
        _normalizer_instance = ScoreNormalizer()
    return _normalizer_instance 