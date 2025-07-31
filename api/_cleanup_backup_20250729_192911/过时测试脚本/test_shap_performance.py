#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SHAP框架性能测试
测量单次预测的完整运行时间和各个组件的耗时
"""

import sys
import os
import time
from datetime import datetime

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from ML_Models.models.shap_deployment.shap_model_wrapper import SHAPModelWrapper

def measure_prediction_time():
    print("⏱️ SHAP框架性能测试")
    print("=" * 60)
    
    # 初始化模型
    print("🔧 初始化SHAP模型包装器...")
    init_start = time.time()
    models_path = os.path.join(project_root, 'ML_Models', 'models', 'shap_deployment')
    wrapper = SHAPModelWrapper(models_directory=models_path)
    init_time = time.time() - init_start
    print(f"✅ 模型初始化完成: {init_time:.3f}秒")
    
    # 测试参数
    test_cases = [
        {"name": "London", "lat": 51.5074, "lon": -0.1278, "month": 7},
        {"name": "Manchester", "lat": 53.4808, "lon": -2.2426, "month": 4},
        {"name": "Edinburgh", "lat": 55.9533, "lon": -3.1883, "month": 10}
    ]
    
    print(f"\n📊 测试用例: {len(test_cases)} 个城市")
    print("=" * 60)
    
    all_times = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🏙️ 测试 {i}/{len(test_cases)}: {test_case['name']}")
        print(f"📍 坐标: ({test_case['lat']}, {test_case['lon']})")
        print(f"📅 月份: {test_case['month']}")
        print("-" * 40)
        
        # 开始计时
        start_time = time.time()
        
        # 分步骤计时
        step_times = {}
        
        try:
            # 步骤1: 特征工程
            step_start = time.time()
            print("🔄 步骤1: 开始特征工程...")
            
            # 调用预测函数
            result = wrapper.predict_environmental_scores(
                latitude=test_case['lat'],
                longitude=test_case['lon'],
                month=test_case['month'],
                analyze_shap=True
            )
            
            total_time = time.time() - start_time
            all_times.append(total_time)
            
            print(f"⏱️ 总耗时: {total_time:.3f}秒")
            
            if result and result.get('success', False):
                climate_score = result.get('climate_score', 'N/A')
                geographic_score = result.get('geographic_score', 'N/A')
                final_score = result.get('final_score', 'N/A')
                
                print(f"✅ 预测成功!")
                print(f"   Climate Score: {climate_score}")
                print(f"   Geographic Score: {geographic_score}")
                print(f"   Final Score: {final_score}")
            else:
                print(f"❌ 预测失败")
                if result:
                    print(f"   错误: {result.get('error', 'Unknown')}")
                    
        except Exception as e:
            total_time = time.time() - start_time
            all_times.append(total_time)
            print(f"❌ 异常发生: {e}")
            print(f"⏱️ 异常前耗时: {total_time:.3f}秒")
        
        # 间隔
        if i < len(test_cases):
            print("⏳ 等待1秒...")
            time.sleep(1)
    
    # 性能统计
    print(f"\n" + "=" * 60)
    print("📈 性能统计分析")
    print("=" * 60)
    
    if all_times:
        avg_time = sum(all_times) / len(all_times)
        min_time = min(all_times)
        max_time = max(all_times)
        
        print(f"🔢 测试次数: {len(all_times)}")
        print(f"⏱️ 平均耗时: {avg_time:.3f}秒")
        print(f"🚀 最快时间: {min_time:.3f}秒")
        print(f"🐌 最慢时间: {max_time:.3f}秒")
        print(f"📊 时间范围: {max_time - min_time:.3f}秒")
        
        # 详细时间记录
        print(f"\n📋 详细时间记录:")
        for i, (test_case, exec_time) in enumerate(zip(test_cases, all_times), 1):
            print(f"  {i}. {test_case['name']}: {exec_time:.3f}秒")
        
        # 性能评估
        print(f"\n🎯 性能评估:")
        if avg_time < 10:
            print(f"  ✅ 性能良好 (平均 < 10秒)")
        elif avg_time < 30:
            print(f"  ⚠️ 性能中等 (平均 10-30秒)")
        else:
            print(f"  ❌ 性能较慢 (平均 > 30秒)")
        
        # 优化建议
        print(f"\n💡 优化建议:")
        if avg_time > 20:
            print(f"  🔧 考虑缓存API响应")
            print(f"  🔧 优化特征工程算法")
            print(f"  🔧 并行处理历史数据")
        elif avg_time > 10:
            print(f"  🔧 可以考虑轻微优化")
        else:
            print(f"  🎉 当前性能已经很好!")
    
    else:
        print(f"❌ 没有有效的性能数据")

def measure_component_breakdown():
    """详细测量各个组件的耗时"""
    print(f"\n" + "=" * 60)
    print("🔍 组件耗时详细分析")
    print("=" * 60)
    
    # 导入组件
    from utils.real_time_environmental_data_collector import get_environmental_collector
    from utils.real_time_feature_engineer import get_feature_engineer
    
    collector = get_environmental_collector()
    feature_engineer = get_feature_engineer()
    
    # 测试参数
    lat, lon, month = 51.5074, -0.1278, 7
    
    print(f"📍 测试坐标: London ({lat}, {lon})")
    print(f"📅 测试月份: {month}")
    print("-" * 40)
    
    # 组件1: 环境数据收集
    print(f"\n🌍 组件1: 环境数据收集")
    start_time = time.time()
    try:
        env_data = collector.get_current_environmental_data(lat, lon)
        env_time = time.time() - start_time
        print(f"✅ 环境数据收集: {env_time:.3f}秒")
        print(f"   获取变量数: {len(env_data)}")
    except Exception as e:
        env_time = time.time() - start_time
        print(f"❌ 环境数据收集失败: {env_time:.3f}秒")
        print(f"   错误: {e}")
    
    # 组件2: 历史数据收集
    print(f"\n📚 组件2: 历史数据收集")
    start_time = time.time()
    try:
        hist_data = collector.get_historical_lag_data(lat, lon)
        hist_time = time.time() - start_time
        print(f"✅ 历史数据收集: {hist_time:.3f}秒")
        print(f"   历史节点数: {len(hist_data)}")
    except Exception as e:
        hist_time = time.time() - start_time
        print(f"❌ 历史数据收集失败: {hist_time:.3f}秒")
        print(f"   错误: {e}")
    
    # 组件3: 移动平均数据
    print(f"\n📈 组件3: 移动平均数据")
    start_time = time.time()
    try:
        ma_data = collector.get_moving_average_data(lat, lon)
        ma_time = time.time() - start_time
        print(f"✅ 移动平均数据: {ma_time:.3f}秒")
        print(f"   窗口数: {len(ma_data)}")
    except Exception as e:
        ma_time = time.time() - start_time
        print(f"❌ 移动平均数据失败: {ma_time:.3f}秒")
        print(f"   错误: {e}")
    
    # 组件4: 特征工程
    print(f"\n🔧 组件4: 特征工程")
    start_time = time.time()
    try:
        features = feature_engineer.prepare_features_for_prediction(lat, lon, month, 375)
        feature_time = time.time() - start_time
        print(f"✅ 特征工程: {feature_time:.3f}秒")
        print(f"   特征数量: {len(features)}")
    except Exception as e:
        feature_time = time.time() - start_time
        print(f"❌ 特征工程失败: {feature_time:.3f}秒")
        print(f"   错误: {e}")
    
    # 总结组件耗时
    try:
        total_component_time = env_time + hist_time + ma_time + feature_time
        print(f"\n📊 组件耗时总结:")
        print(f"  🌍 环境数据: {env_time:.3f}秒 ({env_time/total_component_time*100:.1f}%)")
        print(f"  📚 历史数据: {hist_time:.3f}秒 ({hist_time/total_component_time*100:.1f}%)")
        print(f"  📈 移动平均: {ma_time:.3f}秒 ({ma_time/total_component_time*100:.1f}%)")
        print(f"  🔧 特征工程: {feature_time:.3f}秒 ({feature_time/total_component_time*100:.1f}%)")
        print(f"  📝 总计: {total_component_time:.3f}秒")
    except:
        print(f"❌ 无法计算组件耗时总结")

if __name__ == "__main__":
    print("🚀 SHAP框架性能测试开始")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 主要性能测试
    measure_prediction_time()
    
    # 组件级性能分析
    measure_component_breakdown()
    
    print(f"\n✅ 性能测试完成")
    print(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}") 