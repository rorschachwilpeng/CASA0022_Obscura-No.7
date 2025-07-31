#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试不同时间节点下SHAP框架环境得分计算
验证修复后的系统能否根据不同时间的环境数据产生不同的得分
"""

import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from ML_Models.models.shap_deployment.shap_model_wrapper import SHAPModelWrapper
import time

def test_shap_temporal_scores():
    print("🕐 测试不同时间节点下SHAP环境得分计算")
    print("=" * 80)
    
    # 初始化SHAP模型包装器 (使用绝对路径)
    models_path = os.path.join(project_root, 'ML_Models', 'models', 'shap_deployment')
    wrapper = SHAPModelWrapper(models_directory=models_path)
    
    # 测试坐标和参数
    test_locations = [
        {"name": "London", "lat": 51.5074, "lon": -0.1278},
        {"name": "Manchester", "lat": 53.4808, "lon": -2.2426},
        {"name": "Edinburgh", "lat": 55.9533, "lon": -3.1883}
    ]
    
    # 测试不同的月份（代表不同时间节点/季节）
    test_months = [
        {"name": "冬季", "month": 1},
        {"name": "春季", "month": 4}, 
        {"name": "夏季", "month": 7},
        {"name": "秋季", "month": 10}
    ]
    
    print(f"🎯 测试配置:")
    print(f"  📍 测试城市: {', '.join([loc['name'] for loc in test_locations])}")
    print(f"  📅 测试季节: {', '.join([season['name'] for season in test_months])}")
    print(f"  🔍 分析方式: SHAP框架完整分析")
    
    all_results = []
    
    for location in test_locations:
        print(f"\n" + "=" * 60)
        print(f"📍 测试城市: {location['name']} ({location['lat']}, {location['lon']})")
        print("=" * 60)
        
        location_results = []
        
        for season in test_months:
            print(f"\n🗓️ {season['name']} (第{season['month']}月):")
            print("-" * 40)
            
            try:
                # 调用SHAP预测
                result = wrapper.predict_environmental_scores(
                    latitude=location['lat'],
                    longitude=location['lon'], 
                    month=season['month'],
                    analyze_shap=True  # 启用SHAP分析
                )
                
                if result and result.get('success', False):
                    # 提取得分
                    final_score = result.get('final_score', 0.0)
                    climate_score = result.get('climate_score', 0.0)
                    geographic_score = result.get('geographic_score', 0.0)
                    
                    # 注意：根据你的部署清单，没有经济模型
                    # 经济得分设为默认值或从其他地方计算
                    economic_score = result.get('economic_score', 0.0)
                    
                    # 显示结果
                    print(f"✅ SHAP分析成功")
                    print(f"Environment Change Outcome <-- {final_score:.6f}")
                    print(f"Climate Score: {climate_score:.6f}")
                    print(f"Economic Score: {economic_score:.6f}")
                    print(f"Geographic Score: {geographic_score:.6f}")
                    
                    # 记录结果
                    score_data = {
                        'location': location['name'],
                        'season': season['name'],
                        'month': season['month'],
                        'final_score': final_score,
                        'climate_score': climate_score,
                        'economic_score': economic_score,
                        'geographic_score': geographic_score,
                        'success': True
                    }
                    location_results.append(score_data)
                    all_results.append(score_data)
                    
                else:
                    print(f"❌ SHAP分析失败")
                    error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
                    print(f"错误信息: {error_msg}")
                    print(f"Environment Change Outcome <-- N/A")
                    print(f"Climate Score: N/A")
                    print(f"Economic Score: N/A") 
                    print(f"Geographic Score: N/A")
                    
                    # 记录失败结果
                    score_data = {
                        'location': location['name'],
                        'season': season['name'], 
                        'month': season['month'],
                        'error': error_msg,
                        'success': False
                    }
                    location_results.append(score_data)
                    all_results.append(score_data)
                
            except Exception as e:
                print(f"❌ 异常发生: {e}")
                print(f"Environment Change Outcome <-- ERROR")
                print(f"Climate Score: ERROR")
                print(f"Economic Score: ERROR")
                print(f"Geographic Score: ERROR")
                
                # 记录异常结果
                score_data = {
                    'location': location['name'],
                    'season': season['name'],
                    'month': season['month'], 
                    'error': str(e),
                    'success': False
                }
                location_results.append(score_data)
                all_results.append(score_data)
            
            # 短暂延迟避免API限制
            time.sleep(1)
        
        # 分析该城市的季节变化
        analyze_location_variation(location['name'], location_results)
    
    # 总体分析
    print(f"\n" + "=" * 80)
    print("🎯 总体测试结果分析")
    print("=" * 80)
    
    analyze_overall_results(all_results)

def analyze_location_variation(location_name, results):
    """分析单个城市的季节得分变化"""
    print(f"\n📊 {location_name} 季节变化分析:")
    
    successful_results = [r for r in results if r.get('success', False)]
    
    if len(successful_results) < 2:
        print(f"  ⚠️ 有效结果不足，无法分析变化 ({len(successful_results)}/4)")
        return
    
    # 提取得分
    final_scores = [r['final_score'] for r in successful_results]
    climate_scores = [r['climate_score'] for r in successful_results]
    geographic_scores = [r['geographic_score'] for r in successful_results]
    
    # 计算变化范围
    final_range = max(final_scores) - min(final_scores) if final_scores else 0
    climate_range = max(climate_scores) - min(climate_scores) if climate_scores else 0
    geographic_range = max(geographic_scores) - min(geographic_scores) if geographic_scores else 0
    
    print(f"  🎯 总得分变化: {min(final_scores):.6f} ~ {max(final_scores):.6f} (范围: {final_range:.6f})")
    print(f"  🌡️ 气候得分变化: {min(climate_scores):.6f} ~ {max(climate_scores):.6f} (范围: {climate_range:.6f})")
    print(f"  🗻 地理得分变化: {min(geographic_scores):.6f} ~ {max(geographic_scores):.6f} (范围: {geographic_range:.6f})")
    
    # 判断变化显著性
    if final_range > 0.001:  # 阈值可调整
        print(f"  ✅ 季节变化显著 (总得分范围 > 0.001)")
    else:
        print(f"  ⚠️ 季节变化较小 (总得分范围 <= 0.001)")

def analyze_overall_results(all_results):
    """分析所有测试结果"""
    
    successful_results = [r for r in all_results if r.get('success', False)]
    total_tests = len(all_results)
    successful_tests = len(successful_results)
    
    print(f"📈 测试统计:")
    print(f"  总测试数: {total_tests}")
    print(f"  成功测试: {successful_tests}")
    print(f"  成功率: {(successful_tests/total_tests*100):.1f}%")
    
    if successful_tests == 0:
        print(f"  ❌ 没有成功的测试，无法分析")
        return
    
    # 提取所有成功测试的得分
    all_final_scores = [r['final_score'] for r in successful_results]
    all_climate_scores = [r['climate_score'] for r in successful_results]
    all_geographic_scores = [r['geographic_score'] for r in successful_results]
    
    # 计算统计信息
    print(f"\n📊 得分统计分析:")
    print(f"  🎯 总得分:")
    print(f"    范围: {min(all_final_scores):.6f} ~ {max(all_final_scores):.6f}")
    print(f"    平均: {sum(all_final_scores)/len(all_final_scores):.6f}")
    print(f"    变化范围: {max(all_final_scores) - min(all_final_scores):.6f}")
    
    print(f"  🌡️ 气候得分:")
    print(f"    范围: {min(all_climate_scores):.6f} ~ {max(all_climate_scores):.6f}")
    print(f"    平均: {sum(all_climate_scores)/len(all_climate_scores):.6f}")
    print(f"    变化范围: {max(all_climate_scores) - min(all_climate_scores):.6f}")
    
    print(f"  🗻 地理得分:")
    print(f"    范围: {min(all_geographic_scores):.6f} ~ {max(all_geographic_scores):.6f}")
    print(f"    平均: {sum(all_geographic_scores)/len(all_geographic_scores):.6f}")
    print(f"    变化范围: {max(all_geographic_scores) - min(all_geographic_scores):.6f}")
    
    # 评估得分变化
    final_score_variance = max(all_final_scores) - min(all_final_scores)
    
    print(f"\n🔍 变化性评估:")
    if final_score_variance > 0.01:
        print(f"  ✅ 得分变化显著 (变化范围: {final_score_variance:.6f} > 0.01)")
        print(f"  📝 结论: SHAP预测分数问题已修复!")
    elif final_score_variance > 0.001:
        print(f"  ⚠️ 得分变化中等 (变化范围: {final_score_variance:.6f} > 0.001)")
        print(f"  📝 结论: SHAP预测有一定变化，但可能需要进一步优化")
    else:
        print(f"  ❌ 得分变化较小 (变化范围: {final_score_variance:.6f} <= 0.001)")
        print(f"  📝 结论: SHAP预测分数仍然缺乏足够变化")
    
    # 显示详细结果表格
    print(f"\n📋 详细结果表格:")
    print(f"{'城市':<12} {'季节':<8} {'总得分':<12} {'气候得分':<12} {'地理得分':<12} {'状态':<8}")
    print("-" * 80)
    
    for result in all_results:
        if result.get('success', False):
            print(f"{result['location']:<12} {result['season']:<8} {result['final_score']:<12.6f} {result['climate_score']:<12.6f} {result['geographic_score']:<12.6f} {'成功':<8}")
        else:
            error = result.get('error', 'Unknown')[:20]
            print(f"{result['location']:<12} {result['season']:<8} {'N/A':<12} {'N/A':<12} {'N/A':<12} {'失败':<8}")

if __name__ == "__main__":
    print("🧪 SHAP时间节点环境得分测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 目标: 验证不同时间节点下SHAP环境得分的变化性")
    print()
    
    test_shap_temporal_scores()
    
    print(f"\n✅ 测试完成")
    print(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}") 