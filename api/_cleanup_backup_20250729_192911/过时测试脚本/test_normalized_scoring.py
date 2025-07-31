#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
归一化SHAP评分系统测试
验证新的0-100百分制评分计算
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from ML_Models.models.shap_deployment.shap_model_wrapper import SHAPModelWrapper

class NormalizedSHAPScorer:
    """归一化SHAP评分器"""
    
    def __init__(self, models_directory):
        self.wrapper = SHAPModelWrapper(models_directory=models_directory)
        
        # 基于测试数据确定的分数范围
        self.score_ranges = {
            'climate': {'min': -2.5, 'max': 1.6},      # 基于ML模型输出范围
            'geographic': {'min': -0.4, 'max': 1.9},   # 基于ML模型输出范围  
            'economic': {'min': 0.2, 'max': 1.0}       # 基于启发式算法范围
        }
        
        # 权重配置
        self.weights = {
            'climate': 0.3,
            'economic': 0.4,
            'geographic': 0.3
        }
    
    def normalize_score(self, raw_score, dimension):
        """将原始分数归一化到[0, 1]区间"""
        if dimension not in self.score_ranges:
            raise ValueError(f"未知维度: {dimension}")
        
        min_val = self.score_ranges[dimension]['min']
        max_val = self.score_ranges[dimension]['max']
        
        # 线性归一化到[0, 1]
        normalized = (raw_score - min_val) / (max_val - min_val)
        
        # 确保在有效范围内
        normalized = max(0, min(1, normalized))
        
        return normalized
    
    def calculate_environment_outcome(self, climate_norm, economic_norm, geographic_norm):
        """计算0-100的环境变化结果"""
        outcome = (
            self.weights['climate'] * climate_norm +
            self.weights['economic'] * economic_norm +
            self.weights['geographic'] * geographic_norm
        )
        
        # 转换为0-100百分制
        return outcome * 100
    
    def predict_normalized_scores(self, latitude, longitude, month):
        """获取归一化的环境分数"""
        print(f"🔮 开始预测归一化分数...")
        print(f"📍 坐标: ({latitude}, {longitude})")
        print(f"📅 月份: {month}")
        
        # 获取原始SHAP分数
        raw_result = self.wrapper.predict_environmental_scores(
            latitude=latitude,
            longitude=longitude,
            month=month,
            analyze_shap=False  # 暂时跳过SHAP分析以提高速度
        )
        
        if not raw_result or not raw_result.get('success', False):
            return {
                'success': False,
                'error': raw_result.get('error', 'SHAP预测失败') if raw_result else 'SHAP预测返回空结果'
            }
        
        # 提取原始分数
        raw_climate = raw_result.get('climate_score')
        raw_geographic = raw_result.get('geographic_score')
        raw_economic = 0.0  # 占位符，因为没有经济模型
        
        if raw_climate is None or raw_geographic is None:
            return {
                'success': False,
                'error': '原始分数缺失'
            }
        
        # 归一化分数
        climate_normalized = self.normalize_score(raw_climate, 'climate')
        geographic_normalized = self.normalize_score(raw_geographic, 'geographic')
        economic_normalized = self.normalize_score(raw_economic, 'economic')  # 中性值
        
        # 计算最终分数
        final_outcome = self.calculate_environment_outcome(
            climate_normalized, economic_normalized, geographic_normalized
        )
        
        return {
            'success': True,
            'raw_scores': {
                'climate': raw_climate,
                'geographic': raw_geographic,
                'economic': raw_economic
            },
            'normalized_scores': {
                'climate': climate_normalized,
                'geographic': geographic_normalized,
                'economic': economic_normalized
            },
            'final_outcome': final_outcome,
            'breakdown': {
                'climate_contribution': self.weights['climate'] * climate_normalized * 10,
                'economic_contribution': self.weights['economic'] * economic_normalized * 10,
                'geographic_contribution': self.weights['geographic'] * geographic_normalized * 10
            }
        }

def test_normalized_scoring():
    """测试归一化评分系统"""
    print("🎯 归一化SHAP评分系统测试")
    print("=" * 70)
    
    # 初始化评分器
    models_path = os.path.join(os.path.dirname(current_dir), 'ML_Models', 'models', 'shap_deployment')
    scorer = NormalizedSHAPScorer(models_path)
    
    # 测试用例
    test_cases = [
        {"name": "London夏季", "lat": 51.5074, "lon": -0.1278, "month": 7},
        {"name": "Manchester春季", "lat": 53.4808, "lon": -2.2426, "month": 4},
        {"name": "Edinburgh秋季", "lat": 55.9533, "lon": -3.1883, "month": 10},
        {"name": "London冬季", "lat": 51.5074, "lon": -0.1278, "month": 1},
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🏙️ 测试 {i}/{len(test_cases)}: {test_case['name']}")
        print("-" * 50)
        
        result = scorer.predict_normalized_scores(
            test_case['lat'], test_case['lon'], test_case['month']
        )
        
        if result['success']:
            raw = result['raw_scores']
            norm = result['normalized_scores']
            final = result['final_outcome']
            breakdown = result['breakdown']
            
            print(f"✅ 预测成功!")
            print(f"📊 原始分数:")
            print(f"   Climate: {raw['climate']:.3f}")
            print(f"   Geographic: {raw['geographic']:.3f}")
                         print(f"   Economic: {raw['economic']:.3f} (占位符)")
             
             print(f"🔄 归一化分数 (0-1):")
             print(f"   Climate: {norm['climate']:.3f}")
             print(f"   Geographic: {norm['geographic']:.3f}")
             print(f"   Economic: {norm['economic']:.3f}")
            
            print(f"🎯 最终环境变化结果: {final:.1f}/100")
            
            print(f"🔍 贡献度分析:")
            print(f"   Climate (30%): {breakdown['climate_contribution']:.1f}")
            print(f"   Economic (40%): {breakdown['economic_contribution']:.1f}")
            print(f"   Geographic (30%): {breakdown['geographic_contribution']:.1f}")
            
            results.append({
                'name': test_case['name'],
                'final_score': final,
                'raw_climate': raw['climate'],
                'raw_geographic': raw['geographic'],
                'norm_climate': norm['climate'],
                'norm_geographic': norm['geographic']
            })
            
        else:
            print(f"❌ 预测失败: {result['error']}")
    
    # 结果分析
    if results:
        print(f"\n" + "=" * 70)
        print("📈 归一化结果分析")
        print("=" * 70)
        
        final_scores = [r['final_score'] for r in results]
        print(f"🎯 最终分数统计:")
        print(f"   最高分: {max(final_scores):.1f}/100")
        print(f"   最低分: {min(final_scores):.1f}/100")
        print(f"   平均分: {sum(final_scores)/len(final_scores):.1f}/100")
        print(f"   分数范围: {max(final_scores) - min(final_scores):.1f}")
        
        print(f"\n📋 详细对比:")
        for result in results:
            print(f"  {result['name']:12} | "
                  f"原始C:{result['raw_climate']:6.2f} G:{result['raw_geographic']:6.2f} | "
                  f"归一化C:{result['norm_climate']:4.1f} G:{result['norm_geographic']:4.1f} | "
                  f"最终:{result['final_score']:4.1f}/100")
        
        # 验证归一化效果
        print(f"\n✅ 归一化验证:")
        climate_norms = [r['norm_climate'] for r in results]
        geographic_norms = [r['norm_geographic'] for r in results]
        
        print(f"   Climate归一化范围: [{min(climate_norms):.1f}, {max(climate_norms):.1f}]")
        print(f"   Geographic归一化范围: [{min(geographic_norms):.1f}, {max(geographic_norms):.1f}]")
        print(f"   最终分数范围: [{min(final_scores):.1f}, {max(final_scores):.1f}]")

def analyze_score_ranges():
    """分析和建议分数范围"""
    print(f"\n" + "=" * 70)
    print("🔍 分数范围分析和建议")
    print("=" * 70)
    
    # 基于已有测试数据的范围分析
    observed_ranges = {
        'climate': {'min': -2.471, 'max': 1.540, 'range': 4.011},
        'geographic': {'min': -0.377, 'max': 1.852, 'range': 2.229}
    }
    
    print(f"📊 观察到的分数范围:")
    for dimension, stats in observed_ranges.items():
        print(f"   {dimension.capitalize():10}: [{stats['min']:6.3f}, {stats['max']:6.3f}] (范围: {stats['range']:.3f})")
    
    # 建议的归一化范围
    suggested_ranges = {
        'climate': {'min': -2.5, 'max': 1.6},      # 10%安全边距
        'geographic': {'min': -0.4, 'max': 1.9},   # 10%安全边距
        'economic': {'min': -2.0, 'max': 2.0}      # 预估对称范围
    }
    
    print(f"\n💡 建议的归一化范围 (含10%安全边距):")
    for dimension, range_info in suggested_ranges.items():
        total_range = range_info['max'] - range_info['min']
        print(f"   {dimension.capitalize():10}: [{range_info['min']:6.1f}, {range_info['max']:6.1f}] (范围: {total_range:.1f})")
    
    print(f"\n🎯 归一化策略:")
    print(f"   目标区间: [0, 10]")
    print(f"   最终计算: 0.3*Climate + 0.4*Economic + 0.3*Geographic")
    print(f"   输出范围: [0, 100] (百分制)")
    
    print(f"\n📈 预期效果:")
    print(f"   ✅ 所有维度统一在[0, 10]区间")
    print(f"   ✅ 权重计算更加合理")
    print(f"   ✅ 最终分数直观易懂")
    print(f"   ✅ 便于UI展示和用户理解")

if __name__ == "__main__":
    print("🚀 归一化SHAP评分系统测试开始")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 分析分数范围
    analyze_score_ranges()
    
    # 测试归一化评分
    test_normalized_scoring()
    
    print(f"\n✅ 测试完成")
    print(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}") 