#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型评估器
统一的模型评估和性能分析功能
"""

import os
import json
import numpy as np
import pandas as pd
from typing import Dict, Any, List
import logging
from datetime import datetime

class ModelEvaluator:
    """模型评估器"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def compare_models(self, climate_results: Dict[str, Any], 
                      geographic_results: Dict[str, Any]) -> Dict[str, Any]:
        """比较两个模型的性能"""
        self.logger.info("📊 比较Climate和Geographic模型性能...")
        
        comparison = {
            'climate_model': {
                'model_type': climate_results['model_type'],
                'target': climate_results['target'],
                'metrics': climate_results['metrics'],
                'model_path': climate_results['model_path']
            },
            'geographic_model': {
                'model_type': geographic_results['model_type'],
                'target': geographic_results['target'],
                'metrics': geographic_results['metrics'],
                'model_path': geographic_results['model_path']
            },
            'comparison_summary': {
                'climate_r2': climate_results['metrics']['r2'],
                'geographic_r2': geographic_results['metrics']['r2'],
                'climate_rmse': climate_results['metrics']['rmse'],
                'geographic_rmse': geographic_results['metrics']['rmse'],
                'best_climate_metric': 'r2' if climate_results['metrics']['r2'] > 0.5 else 'rmse',
                'best_geographic_metric': 'r2' if geographic_results['metrics']['r2'] > 0.5 else 'rmse'
            }
        }
        
        self.logger.info("📈 模型性能对比:")
        self.logger.info(f"   Climate R²: {climate_results['metrics']['r2']:.4f}")
        self.logger.info(f"   Geographic R²: {geographic_results['metrics']['r2']:.4f}")
        self.logger.info(f"   Climate RMSE: {climate_results['metrics']['rmse']:.4f}")
        self.logger.info(f"   Geographic RMSE: {geographic_results['metrics']['rmse']:.4f}")
        
        return comparison
    
    def generate_training_report(self, climate_results: Dict[str, Any], 
                               geographic_results: Dict[str, Any],
                               config: Any) -> Dict[str, Any]:
        """生成完整的训练报告"""
        self.logger.info("📋 生成训练报告...")
        
        # 比较模型性能
        comparison = self.compare_models(climate_results, geographic_results)
        
        # 生成完整报告
        report = {
            'training_info': {
                'timestamp': datetime.now().isoformat(),
                'data_source': config.data_cache_path,
                'n_samples': 500,  # 从配置中获取
                'n_features': config.n_features,
                'test_size': config.test_size,
                'val_size': config.val_size,
                'random_state': config.random_state
            },
            'model_results': {
                'climate': climate_results,
                'geographic': geographic_results
            },
            'performance_comparison': comparison,
            'model_paths': config.get_model_paths(),
            'training_config': {
                'climate_model_params': config.climate_model_params,
                'geographic_model_params': config.geographic_model_params,
                'training_params': {
                    'max_epochs': config.max_epochs,
                    'batch_size': config.batch_size,
                    'learning_rate': config.learning_rate,
                    'early_stopping_patience': config.early_stopping_patience
                }
            }
        }
        
        self.logger.info("✅ 训练报告生成完成")
        return report
    
    def save_training_report(self, report: Dict[str, Any], output_path: str):
        """保存训练报告到文件"""
        self.logger.info(f"💾 保存训练报告到: {output_path}")
        
        try:
            # 创建输出目录
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 保存报告
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info("✅ 训练报告保存完成")
            
        except Exception as e:
            self.logger.error(f"❌ 保存训练报告失败: {e}")
            raise
    
    def print_summary(self, report: Dict[str, Any]):
        """打印训练总结"""
        self.logger.info("=" * 60)
        self.logger.info("🎉 模型训练总结")
        self.logger.info("=" * 60)
        
        # 训练信息
        training_info = report['training_info']
        self.logger.info(f"📊 训练信息:")
        self.logger.info(f"   时间: {training_info['timestamp']}")
        self.logger.info(f"   样本数: {training_info['n_samples']}")
        self.logger.info(f"   特征数: {training_info['n_features']}")
        self.logger.info(f"   测试集比例: {training_info['test_size']}")
        
        # 模型性能
        climate_metrics = report['model_results']['climate']['metrics']
        geographic_metrics = report['model_results']['geographic']['metrics']
        
        self.logger.info(f"🌲 Climate模型 (RandomForest):")
        self.logger.info(f"   R²: {climate_metrics['r2']:.4f}")
        self.logger.info(f"   RMSE: {climate_metrics['rmse']:.4f}")
        self.logger.info(f"   MAE: {climate_metrics['mae']:.4f}")
        
        self.logger.info(f"🧠 Geographic模型 (LSTM):")
        self.logger.info(f"   R²: {geographic_metrics['r2']:.4f}")
        self.logger.info(f"   RMSE: {geographic_metrics['rmse']:.4f}")
        self.logger.info(f"   MAE: {geographic_metrics['mae']:.4f}")
        
        # 模型文件路径
        model_paths = report['model_paths']
        self.logger.info(f"💾 模型文件:")
        self.logger.info(f"   Climate模型: {model_paths['climate_model']}")
        self.logger.info(f"   Geographic模型: {model_paths['geographic_model']}")
        self.logger.info(f"   特征缩放器: {model_paths['feature_scaler']}")
        
        self.logger.info("=" * 60)
    
    def validate_model_performance(self, report: Dict[str, Any]) -> bool:
        """验证模型性能是否满足要求"""
        self.logger.info("🔍 验证模型性能...")
        
        climate_r2 = report['model_results']['climate']['metrics']['r2']
        geographic_r2 = report['model_results']['geographic']['metrics']['r2']
        
        # 设置最低性能要求
        min_r2_threshold = 0.3  # 可以根据实际情况调整
        
        climate_ok = climate_r2 >= min_r2_threshold
        geographic_ok = geographic_r2 >= min_r2_threshold
        
        self.logger.info(f"📊 性能验证结果:")
        self.logger.info(f"   Climate R² ({climate_r2:.4f}) >= {min_r2_threshold}: {'✅' if climate_ok else '❌'}")
        self.logger.info(f"   Geographic R² ({geographic_r2:.4f}) >= {min_r2_threshold}: {'✅' if geographic_ok else '❌'}")
        
        if climate_ok and geographic_ok:
            self.logger.info("✅ 模型性能验证通过!")
            return True
        else:
            self.logger.warning("⚠️ 模型性能未达到要求，建议重新训练或调整参数")
            return False 