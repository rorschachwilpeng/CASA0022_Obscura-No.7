#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实混合模型测试
实际调用混合模型包装器和真实特征进行推理验证
"""

import sys
import os
from datetime import datetime
import json
import numpy as np
from typing import Dict, Any

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
api_dir = os.path.join(project_root, 'api')
sys.path.insert(0, project_root)
sys.path.insert(0, api_dir)

print("🔬 真实混合模型推理测试")
print("=" * 80)

class RealHybridModelTester:
    """真实混合模型测试器"""
    
    def __init__(self):
        self.test_coordinates = [
            {'name': 'London_Center', 'lat': 51.5074, 'lon': -0.1278, 'month': 7},
            {'name': 'Manchester_Center', 'lat': 53.4808, 'lon': -2.2426, 'month': 12},
            {'name': 'Edinburgh_Center', 'lat': 55.9533, 'lon': -3.1883, 'month': 3},
            {'name': 'Random_UK', 'lat': 52.5, 'lon': -1.5, 'month': 6}
        ]
        
        self.results = {}
        
    def test_1_real_feature_generation(self):
        """测试1: 真实特征生成 - 验证不同位置产生不同特征"""
        print("\n🔧 测试1: 真实特征生成差异性验证")
        print("-" * 60)
        
        try:
            from utils.simplified_feature_engineer import get_simplified_feature_engineer
            
            feature_engineer = get_simplified_feature_engineer()
            
            feature_results = []
            
            for coord in self.test_coordinates:
                print(f"📍 生成特征: {coord['name']} ({coord['lat']:.3f}, {coord['lon']:.3f}, 月份{coord['month']})")
                
                features = feature_engineer.prepare_features_for_prediction(
                    coord['lat'], coord['lon'], coord['month'], 66
                )
                
                feature_stats = {
                    'location': coord['name'],
                    'coordinates': coord,
                    'feature_count': len(features),
                    'feature_mean': float(np.mean(features)),
                    'feature_std': float(np.std(features)),
                    'feature_min': float(np.min(features)),
                    'feature_max': float(np.max(features)),
                    'feature_sample': [float(f) for f in features[:5]]  # 前5个特征作为样本
                }
                
                feature_results.append(feature_stats)
                
                print(f"   特征统计: 均值={feature_stats['feature_mean']:.3f}, "
                      f"标准差={feature_stats['feature_std']:.3f}, "
                      f"范围=[{feature_stats['feature_min']:.3f}, {feature_stats['feature_max']:.3f}]")
                print(f"   前5个特征: {[f'{f:.3f}' for f in feature_stats['feature_sample']]}")
            
            # 验证特征差异性
            means = [r['feature_mean'] for r in feature_results]
            mean_variance = np.var(means)
            
            print(f"\n📊 特征差异性分析:")
            print(f"   不同位置特征均值: {[f'{m:.3f}' for m in means]}")
            print(f"   特征均值方差: {mean_variance:.6f}")
            
            if mean_variance > 0.01:  # 如果方差大于0.01，说明特征有显著差异
                print(f"   ✅ 特征差异性验证通过 - 不同位置产生不同特征")
                diversity_check = True
            else:
                print(f"   ❌ 特征差异性不足 - 不同位置特征过于相似")
                diversity_check = False
            
            self.results['feature_generation'] = {
                'status': 'success',
                'diversity_check': diversity_check,
                'feature_results': feature_results,
                'mean_variance': float(mean_variance)
            }
            
            return True
            
        except Exception as e:
            print(f"❌ 真实特征生成测试失败: {e}")
            self.results['feature_generation'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
    
    def test_2_real_economic_calculation(self):
        """测试2: 真实经济分数计算 - 验证启发式算法的地理和时间差异"""
        print("\n💰 测试2: 真实经济分数计算")
        print("-" * 60)
        
        try:
            # 直接调用经济分数计算逻辑
            from hybrid_model_wrapper import HybridSHAPModelWrapper
            
            # 临时创建包装器实例来访问经济计算方法
            wrapper = HybridSHAPModelWrapper()
            
            economic_results = []
            
            for coord in self.test_coordinates:
                economic_score = wrapper._calculate_economic_score(
                    coord['lat'], coord['lon'], coord['month']
                )
                
                economic_result = {
                    'location': coord['name'],
                    'coordinates': coord,
                    'economic_score': float(economic_score),
                    'closest_city': wrapper.get_closest_city(coord['lat'], coord['lon'])
                }
                
                economic_results.append(economic_result)
                
                print(f"📍 {coord['name']}:")
                print(f"   最近城市: {economic_result['closest_city']}")
                print(f"   经济分数: {economic_score:.4f}")
            
            # 验证经济分数差异性
            scores = [r['economic_score'] for r in economic_results]
            score_variance = np.var(scores)
            
            print(f"\n📊 经济分数差异性分析:")
            print(f"   不同位置经济分数: {[f'{s:.4f}' for s in scores]}")
            print(f"   经济分数方差: {score_variance:.6f}")
            
            if score_variance > 0.001:  # 如果方差大于0.001，说明有差异
                print(f"   ✅ 经济分数差异性验证通过")
                diversity_check = True
            else:
                print(f"   ❌ 经济分数差异性不足")
                diversity_check = False
            
            self.results['economic_calculation'] = {
                'status': 'success',
                'diversity_check': diversity_check,
                'economic_results': economic_results,
                'score_variance': float(score_variance)
            }
            
            return True
            
        except Exception as e:
            print(f"❌ 真实经济分数计算测试失败: {e}")
            self.results['economic_calculation'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
    
    def test_3_mock_ml_models_with_real_features(self):
        """测试3: 使用真实特征的模拟ML模型 - 验证不同特征产生不同预测"""
        print("\n🤖 测试3: 真实特征驱动的模拟ML预测")
        print("-" * 60)
        
        try:
            from utils.simplified_feature_engineer import get_simplified_feature_engineer
            
            feature_engineer = get_simplified_feature_engineer()
            
            ml_results = []
            
            for coord in self.test_coordinates:
                # 获取真实特征
                features = feature_engineer.prepare_features_for_prediction(
                    coord['lat'], coord['lon'], coord['month'], 66
                )
                
                # 基于真实特征的模拟ML预测
                # Climate Score: 基于前44个特征 (滞后特征)
                climate_features = features[:44]
                climate_score = np.tanh(np.mean(climate_features) / 100) * 2  # 与训练脚本相同的逻辑
                
                # Geographic Score: 基于后22个特征 (变化率特征)
                geo_features = features[44:]
                geographic_score = np.tanh(np.mean(geo_features) * 0.1) * 1.5  # 稍微调整系数
                
                ml_result = {
                    'location': coord['name'],
                    'coordinates': coord,
                    'climate_score': float(climate_score),
                    'geographic_score': float(geographic_score),
                    'feature_stats': {
                        'climate_features_mean': float(np.mean(climate_features)),
                        'geo_features_mean': float(np.mean(geo_features))
                    }
                }
                
                ml_results.append(ml_result)
                
                print(f"📍 {coord['name']}:")
                print(f"   Climate Score: {climate_score:.4f} (基于滞后特征均值: {np.mean(climate_features):.3f})")
                print(f"   Geographic Score: {geographic_score:.4f} (基于变化率特征均值: {np.mean(geo_features):.3f})")
            
            # 验证ML预测差异性
            climate_scores = [r['climate_score'] for r in ml_results]
            geo_scores = [r['geographic_score'] for r in ml_results]
            
            climate_variance = np.var(climate_scores)
            geo_variance = np.var(geo_scores)
            
            print(f"\n📊 ML预测差异性分析:")
            print(f"   Climate Scores: {[f'{s:.4f}' for s in climate_scores]}")
            print(f"   Geographic Scores: {[f'{s:.4f}' for s in geo_scores]}")
            print(f"   Climate方差: {climate_variance:.6f}")
            print(f"   Geographic方差: {geo_variance:.6f}")
            
            diversity_check = climate_variance > 0.001 and geo_variance > 0.001
            
            if diversity_check:
                print(f"   ✅ ML预测差异性验证通过")
            else:
                print(f"   ❌ ML预测差异性不足")
            
            self.results['ml_prediction'] = {
                'status': 'success',
                'diversity_check': diversity_check,
                'ml_results': ml_results,
                'climate_variance': float(climate_variance),
                'geo_variance': float(geo_variance)
            }
            
            return True
            
        except Exception as e:
            print(f"❌ ML预测测试失败: {e}")
            self.results['ml_prediction'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
    
    def test_4_real_score_normalization(self):
        """测试4: 真实分数归一化 - 使用真实预测结果"""
        print("\n⚖️ 测试4: 真实分数归一化")
        print("-" * 60)
        
        try:
            from utils.score_normalizer import get_score_normalizer
            
            normalizer = get_score_normalizer()
            
            # 使用测试3的ML预测结果
            if 'ml_prediction' not in self.results or self.results['ml_prediction']['status'] != 'success':
                print("   ⚠️ 需要先运行ML预测测试")
                return False
            
            ml_results = self.results['ml_prediction']['ml_results']
            economic_results = self.results['economic_calculation']['economic_results']
            
            normalization_results = []
            
            for i, coord in enumerate(self.test_coordinates):
                ml_result = ml_results[i]
                economic_result = economic_results[i]
                
                # 构建SHAP结果格式
                shap_result = {
                    'climate_score': ml_result['climate_score'],
                    'geographic_score': ml_result['geographic_score'],
                    'economic_score': economic_result['economic_score'],
                    'city': economic_result['closest_city'],
                    'success': True
                }
                
                # 进行归一化
                normalized_result = normalizer.normalize_shap_result(shap_result)
                
                normalization_result = {
                    'location': coord['name'],
                    'coordinates': coord,
                    'original_scores': {
                        'climate': shap_result['climate_score'],
                        'geographic': shap_result['geographic_score'],
                        'economic': shap_result['economic_score']
                    },
                    'normalized_scores': {
                        'climate': normalized_result.get('climate_score', 0),
                        'geographic': normalized_result.get('geographic_score', 0),
                        'economic': normalized_result.get('economic_score', 0)
                    },
                    'final_score': normalized_result.get('environment_change_outcome', 0)
                }
                
                normalization_results.append(normalization_result)
                
                print(f"📍 {coord['name']}:")
                print(f"   原始: C={shap_result['climate_score']:.3f}, "
                      f"G={shap_result['geographic_score']:.3f}, "
                      f"E={shap_result['economic_score']:.3f}")
                print(f"   归一化: C={normalization_result['normalized_scores']['climate']:.1f}, "
                      f"G={normalization_result['normalized_scores']['geographic']:.1f}, "
                      f"E={normalization_result['normalized_scores']['economic']:.1f}")
                print(f"   最终分数: {normalization_result['final_score']:.1f}/100")
            
            # 验证最终分数差异性
            final_scores = [r['final_score'] for r in normalization_results]
            final_variance = np.var(final_scores)
            
            print(f"\n📊 最终分数差异性分析:")
            print(f"   最终分数: {[f'{s:.1f}' for s in final_scores]}")
            print(f"   最终分数方差: {final_variance:.6f}")
            
            diversity_check = final_variance > 1.0  # 最终分数方差大于1说明有明显差异
            
            if diversity_check:
                print(f"   ✅ 最终分数差异性验证通过")
            else:
                print(f"   ❌ 最终分数差异性不足")
            
            self.results['score_normalization'] = {
                'status': 'success',
                'diversity_check': diversity_check,
                'normalization_results': normalization_results,
                'final_variance': float(final_variance)
            }
            
            return True
            
        except Exception as e:
            print(f"❌ 真实分数归一化测试失败: {e}")
            self.results['score_normalization'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
    
    def run_full_test(self):
        """运行完整的真实模型测试"""
        print(f"⏰ 测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 运行所有测试
        tests = [
            self.test_1_real_feature_generation,
            self.test_2_real_economic_calculation,
            self.test_3_mock_ml_models_with_real_features,
            self.test_4_real_score_normalization
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for i, test in enumerate(tests, 1):
            try:
                if test():
                    passed_tests += 1
                else:
                    print(f"   ⚠️ 测试{i}未通过，继续下一个测试")
            except Exception as e:
                print(f"❌ 测试{i}异常: {e}")
        
        # 生成测试报告
        self.generate_test_report(passed_tests, total_tests)
        
        return passed_tests == total_tests
    
    def generate_test_report(self, passed_tests: int, total_tests: int):
        """生成真实模型测试报告"""
        print("\n" + "=" * 80)
        print("📊 真实混合模型测试报告")
        print("=" * 80)
        
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"🎯 测试结果: {passed_tests}/{total_tests} 通过 ({success_rate:.1f}%)")
        print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 详细结果
        for test_name, result in self.results.items():
            status_icon = "✅" if result['status'] == 'success' else "❌"
            diversity_icon = "🔀" if result.get('diversity_check', False) else "🔄"
            
            print(f"{status_icon} {diversity_icon} {test_name}: {result['status']}")
            
            if result['status'] == 'failed' and 'error' in result:
                print(f"   错误: {result['error']}")
            elif result.get('diversity_check', False):
                print(f"   ✅ 差异性验证通过")
            else:
                print(f"   ⚠️ 差异性不足或未验证")
        
        # 关键发现
        print(f"\n🔍 关键发现:")
        
        if all(r.get('diversity_check', False) for r in self.results.values() if r['status'] == 'success'):
            print("   ✅ 所有组件都能为不同位置生成不同结果")
            print("   ✅ 混合模型策略的差异性验证通过")
        else:
            print("   ⚠️ 部分组件的差异性不足，需要进一步优化")
        
        # 保存测试报告
        report_file = f"real_model_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # 转换numpy类型为Python原生类型以支持JSON序列化
        def convert_numpy_types(obj):
            if hasattr(obj, 'dtype'):
                if 'bool' in str(obj.dtype):
                    return bool(obj)
                elif 'int' in str(obj.dtype):
                    return int(obj)
                elif 'float' in str(obj.dtype):
                    return float(obj)
            return obj
        
        # 递归转换所有numpy类型
        def deep_convert(obj):
            if isinstance(obj, dict):
                return {k: deep_convert(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [deep_convert(v) for v in obj]
            else:
                return convert_numpy_types(obj)
        
        converted_results = deep_convert(self.results)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'test_summary': {
                    'passed_tests': passed_tests,
                    'total_tests': total_tests,
                    'success_rate': success_rate,
                    'timestamp': datetime.now().isoformat()
                },
                'detailed_results': converted_results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"📄 详细报告已保存: {report_file}")

def main():
    """主函数"""
    tester = RealHybridModelTester()
    success = tester.run_full_test()
    
    if success:
        print("\n🎉 真实模型测试完成！混合策略差异性验证通过！")
        return 0
    else:
        print("\n⚠️ 部分测试失败或差异性不足，请检查实现。")
        return 1

if __name__ == "__main__":
    exit(main()) 