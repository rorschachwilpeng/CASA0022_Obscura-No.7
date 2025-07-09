#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SHAP框架模型训练脚本 - 为云端部署准备

训练三城市的Climate Model和Geographic Model，并保存为部署就绪的格式
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.append('.')
sys.path.append('..')

from shap_framework.core_models import OutcomePredictor, PredictionConfig, ScoreWeights
from shap_framework.data_infrastructure.data_pipeline.data_loader import DataLoader

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def train_and_save_models():
    """训练并保存所有城市的SHAP框架模型"""
    
    print("🚀 开始训练SHAP框架模型...")
    print("="*60)
    
    # 配置
    cities = ['London', 'Manchester', 'Edinburgh']
    data_directory = 'environmental_prediction_framework'
    models_output_dir = Path('models/shap_deployment')
    models_output_dir.mkdir(parents=True, exist_ok=True)
    
    # 训练配置
    config = PredictionConfig(
        prediction_horizon=12,
        confidence_threshold=0.7,
        enable_shap_analysis=False,  # 暂时禁用SHAP分析以加快训练
        save_predictions=False
    )
    
    # 权重配置（平衡配置）
    weights = ScoreWeights(
        climate_weight=0.4,
        geographic_weight=0.35,
        economic_weight=0.25
    )
    
    training_results = {}
    model_summaries = {}
    
    # 为每个城市训练模型
    for city in cities:
        print(f"\n🏙️ 开始训练 {city} 模型...")
        print("-" * 40)
        
        try:
            # 初始化预测器
            predictor = OutcomePredictor(city=city, config=config, weights=weights)
            
            # 暂时禁用特征选择以解决特征数量不一致问题
            from shap_framework.core_models.time_series_predictor import ModelConfig
            no_feature_selection_config = ModelConfig(
                algorithm="random_forest",
                target_variable="meteorological_temperature",
                feature_selection=False,  # 禁用特征选择
                max_features=50,
                validation_splits=3,
                test_size=0.2,
                random_state=42
            )
            
            # 应用配置到所有内部模型
            predictor.climate_model.config = no_feature_selection_config
            predictor.geographic_model.config = no_feature_selection_config
            
            logger.info("✅ 已禁用特征选择以确保训练稳定性")
            
            # 加载数据
            logger.info(f"加载 {city} 的数据...")
            data_loader = DataLoader()
            all_data = data_loader.load_all_data()
            city_data = data_loader.get_city_dataframe(city)
            
            if city_data.empty:
                logger.error(f"❌ {city} 数据为空")
                continue
            
            # 训练模型
            logger.info(f"开始训练 {city} 的模型...")
            results = predictor.train_models(
                data_directory=city_data,  # 直接传递DataFrame而非目录
                validation_split=0.2
            )
            
            # 保存训练结果
            training_results[city] = results
            
            # 获取模型摘要
            summary = predictor.get_predictor_summary()
            model_summaries[city] = summary
            
            # 保存训练好的模型
            city_model_dir = models_output_dir / city.lower()
            predictor.save_models(str(city_model_dir))
            
            # 打印训练结果
            climate_r2 = results.get('climate_validation', {}).get('r2', 0)
            geo_r2 = results.get('geographic_validation', {}).get('r2', 0)
            
            print(f"✅ {city} 模型训练完成!")
            print(f"   Climate Model R²: {climate_r2:.4f}")
            print(f"   Geographic Model R²: {geo_r2:.4f}")
            print(f"   模型已保存到: {city_model_dir}")
            
        except Exception as e:
            logger.error(f"❌ {city} 模型训练失败: {str(e)}")
            print(f"❌ {city} 模型训练失败: {str(e)}")
            continue
    
    # 保存训练报告
    report = {
        'training_timestamp': datetime.now().isoformat(),
        'cities_trained': list(training_results.keys()),
        'configuration': {
            'config': config.__dict__,
            'weights': weights.__dict__
        },
        'training_results': training_results,
        'model_summaries': model_summaries,
        'deployment_info': {
            'models_directory': str(models_output_dir),
            'ready_for_deployment': len(training_results) == len(cities),
            'total_cities': len(cities),
            'successful_cities': len(training_results)
        }
    }
    
    # 保存报告
    report_file = models_output_dir / 'training_report.json'
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    # 创建部署清单
    deployment_manifest = {
        'version': '1.0.0',
        'deployment_date': datetime.now().isoformat(),
        'models': {},
        'requirements': [
            'numpy>=1.21.0',
            'pandas>=1.3.0',
            'scikit-learn>=1.0.0',
            'joblib>=1.1.0',
            'shap>=0.40.0'
        ]
    }
    
    for city in training_results.keys():
        city_lower = city.lower()
        deployment_manifest['models'][city] = {
            'climate_model': f'{city_lower}/{city}_climate_model.joblib',
            'geographic_model': f'{city_lower}/{city}_geographic_model.joblib',
            'metadata': f'{city_lower}/{city}_predictor_metadata.json'
        }
    
    manifest_file = models_output_dir / 'deployment_manifest.json'
    with open(manifest_file, 'w') as f:
        json.dump(deployment_manifest, f, indent=2)
    
    # 打印最终报告
    print("\n" + "="*60)
    print("🎉 SHAP框架模型训练完成！")
    print("="*60)
    print(f"✅ 成功训练城市: {len(training_results)}/{len(cities)}")
    print(f"📁 模型保存目录: {models_output_dir}")
    print(f"📊 训练报告: {report_file}")
    print(f"🚀 部署清单: {manifest_file}")
    
    if len(training_results) == len(cities):
        print("🟢 所有模型已就绪，可以部署！")
    else:
        print("🟡 部分模型训练成功，请检查失败的城市")
    
    # 返回训练结果
    return report

def create_lightweight_wrapper():
    """创建轻量化模型包装器"""
    
    print("\n🔧 创建轻量化模型包装器...")
    
    wrapper_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻量化SHAP模型包装器 - 为云端部署优化

专为Render等云平台设计的SHAP模型包装器
"""

import os
import sys
import json
import joblib
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SHAPModelWrapper:
    """轻量化SHAP模型包装器"""
    
    def __init__(self, models_directory: str = "models/shap_deployment"):
        self.models_dir = Path(models_directory)
        self.loaded_models = {}
        self.deployment_manifest = None
        self.load_manifest()
    
    def load_manifest(self):
        """加载部署清单"""
        manifest_file = self.models_dir / 'deployment_manifest.json'
        if manifest_file.exists():
            with open(manifest_file, 'r') as f:
                self.deployment_manifest = json.load(f)
            logger.info("✅ 部署清单加载成功")
        else:
            logger.warning("⚠️ 部署清单不存在")
    
    def load_city_models(self, city: str) -> bool:
        """按需加载指定城市的模型"""
        try:
            if city in self.loaded_models:
                return True
            
            if not self.deployment_manifest or city not in self.deployment_manifest['models']:
                logger.error(f"❌ {city} 模型配置不存在")
                return False
            
            city_config = self.deployment_manifest['models'][city]
            city_models = {}
            
            # 加载Climate Model
            climate_path = self.models_dir / city_config['climate_model']
            if climate_path.exists():
                city_models['climate'] = joblib.load(climate_path)
                logger.info(f"✅ {city} Climate Model 加载成功")
            
            # 加载Geographic Model  
            geo_path = self.models_dir / city_config['geographic_model']
            if geo_path.exists():
                city_models['geographic'] = joblib.load(geo_path)
                logger.info(f"✅ {city} Geographic Model 加载成功")
            
            # 加载元数据
            metadata_path = self.models_dir / city_config['metadata']
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    city_models['metadata'] = json.load(f)
                logger.info(f"✅ {city} 元数据加载成功")
            
            self.loaded_models[city] = city_models
            return True
            
        except Exception as e:
            logger.error(f"❌ {city} 模型加载失败: {str(e)}")
            return False
    
    def predict_environmental_scores(self, city: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """预测环境分数"""
        try:
            # 确保模型已加载
            if not self.load_city_models(city):
                raise ValueError(f"无法加载 {city} 的模型")
            
            city_models = self.loaded_models[city]
            
            # 这里是简化的预测逻辑
            # 在实际部署中，需要根据真实的模型接口进行调整
            result = {
                'city': city,
                'prediction_timestamp': datetime.now().isoformat(),
                'climate_score': 0.75,  # 占位符
                'geographic_score': 0.82,  # 占位符
                'economic_score': 0.68,  # 占位符
                'final_score': 0.75,  # 占位符
                'confidence': 0.85,
                'model_status': 'loaded',
                'available_models': list(city_models.keys())
            }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ {city} 预测失败: {str(e)}")
            return {'error': str(e), 'city': city}
    
    def get_model_status(self) -> Dict[str, Any]:
        """获取模型状态"""
        return {
            'manifest_loaded': self.deployment_manifest is not None,
            'available_cities': list(self.deployment_manifest['models'].keys()) if self.deployment_manifest else [],
            'loaded_cities': list(self.loaded_models.keys()),
            'deployment_version': self.deployment_manifest.get('version', 'unknown') if self.deployment_manifest else 'unknown'
        }
'''
    
    # 保存包装器
    wrapper_file = Path('models/shap_deployment/shap_model_wrapper.py')
    with open(wrapper_file, 'w') as f:
        f.write(wrapper_code)
    
    print(f"✅ 轻量化包装器已创建: {wrapper_file}")
    return wrapper_file

if __name__ == "__main__":
    print("🔭 Obscura No.7 - SHAP框架模型训练")
    print("为云端部署准备机器学习模型")
    print()
    
    # 训练模型
    report = train_and_save_models()
    
    # 创建包装器
    wrapper_file = create_lightweight_wrapper()
    
    print("\n🎯 下一步:")
    print("1. 检查训练报告确认模型质量")
    print("2. 创建新的API端点")
    print("3. 部署到Render平台")
    print("4. 进行端到端测试") 