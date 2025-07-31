#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
训练配置管理
集中管理所有模型训练的参数和配置
"""

import os
from dataclasses import dataclass
from typing import Dict, Any, List

@dataclass
class TrainingConfig:
    """训练配置类"""
    
    # 数据配置
    data_cache_path: str = "training_data_cache/training_data_500_samples.pkl"
    test_size: float = 0.15
    val_size: float = 0.15
    random_state: int = 42
    
    # 特征配置
    n_features: int = 66
    feature_names: List[str] = None
    
    # Climate模型配置 (RandomForest)
    climate_model_params: Dict[str, Any] = None
    
    # Geographic模型配置 (LSTM)
    geographic_model_params: Dict[str, Any] = None
    
    # 训练配置
    max_epochs: int = 100
    batch_size: int = 32
    early_stopping_patience: int = 10
    learning_rate: float = 0.001
    
    # 评估配置
    cv_folds: int = 5
    metrics: List[str] = None
    
    # 输出配置
    models_output_dir: str = "trained_models_66"
    report_output_path: str = "training_report.json"
    
    def __post_init__(self):
        """初始化默认参数"""
        if self.feature_names is None:
            self.feature_names = [f"feature_{i}" for i in range(self.n_features)]
        
        if self.climate_model_params is None:
            self.climate_model_params = {
                'n_estimators': 100,
                'max_depth': 10,
                'min_samples_split': 5,
                'min_samples_leaf': 2,
                'random_state': self.random_state
            }
        
        if self.geographic_model_params is None:
            self.geographic_model_params = {
                'units': 64,
                'dropout': 0.2,
                'recurrent_dropout': 0.2,
                'return_sequences': False
            }
        
        if self.metrics is None:
            self.metrics = ['mse', 'mae', 'r2', 'rmse']
    
    def get_model_paths(self) -> Dict[str, str]:
        """获取模型文件路径"""
        return {
            'climate_model': os.path.join(self.models_output_dir, 'RandomForest_climate_model.joblib'),
            'geographic_model': os.path.join(self.models_output_dir, 'LSTM_geographic_model.h5'),
            'feature_scaler': os.path.join(self.models_output_dir, 'feature_scaler.joblib'),
            'training_report': os.path.join(self.models_output_dir, self.report_output_path)
        }
    
    def validate(self) -> bool:
        """验证配置参数"""
        if not os.path.exists(self.data_cache_path):
            raise FileNotFoundError(f"训练数据文件不存在: {self.data_cache_path}")
        
        if self.test_size + self.val_size >= 1.0:
            raise ValueError("测试集和验证集比例之和不能大于1.0")
        
        if self.max_epochs <= 0:
            raise ValueError("最大训练轮数必须大于0")
        
        return True

# 默认配置实例
default_config = TrainingConfig() 