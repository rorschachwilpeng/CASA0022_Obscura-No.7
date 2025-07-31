#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主训练脚本
整合Climate和Geographic模型训练流程
"""

import os
import sys
import logging
from datetime import datetime

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from model_trainer.training_config import TrainingConfig
from model_trainer.climate_trainer import ClimateTrainer
from model_trainer.geographic_trainer import GeographicTrainer
from model_trainer.model_evaluator import ModelEvaluator

def setup_logging():
    """设置日志记录"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('training.log', encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)

def main():
    """主训练流程"""
    logger = setup_logging()
    
    logger.info("🚀 开始模型训练流程...")
    logger.info("=" * 60)
    
    try:
        # 1. 初始化配置
        logger.info("📋 初始化训练配置...")
        config = TrainingConfig()
        config.validate()
        logger.info("✅ 配置验证通过")
        
        # 2. 训练Climate模型
        logger.info("🌲 开始训练Climate模型...")
        climate_trainer = ClimateTrainer(config)
        climate_results = climate_trainer.train_and_evaluate()
        logger.info("✅ Climate模型训练完成")
        
        # 3. 训练Geographic模型
        logger.info("🧠 开始训练Geographic模型...")
        geographic_trainer = GeographicTrainer(config)
        geographic_results = geographic_trainer.train_and_evaluate()
        logger.info("✅ Geographic模型训练完成")
        
        # 4. 评估和生成报告
        logger.info("📊 生成训练报告...")
        evaluator = ModelEvaluator()
        report = evaluator.generate_training_report(
            climate_results, geographic_results, config
        )
        
        # 5. 保存报告
        report_path = config.get_model_paths()['training_report']
        evaluator.save_training_report(report, report_path)
        
        # 6. 验证模型性能
        performance_ok = evaluator.validate_model_performance(report)
        
        # 7. 打印总结
        evaluator.print_summary(report)
        
        if performance_ok:
            logger.info("🎉 模型训练流程成功完成!")
            return True
        else:
            logger.warning("⚠️ 模型性能未达到要求，但训练流程已完成")
            return False
            
    except Exception as e:
        logger.error(f"❌ 训练流程失败: {e}")
        raise

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 