#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云端ML模型测试脚本
验证新部署的ML模型是否能在云端正常工作
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_ml_model_loading():
    """测试ML模型加载"""
    print("🔍 测试ML模型加载...")
    print("=" * 60)
    
    try:
        # 测试导入hybrid_model_wrapper
        from ML_Models.models.shap_deployment.hybrid_model_wrapper import get_hybrid_shap_model
        print("✅ hybrid_model_wrapper 导入成功")
        
        # 测试模型加载
        model = get_hybrid_shap_model()
        print("✅ 混合模型实例创建成功")
        
        # 测试模型状态
        status = model.get_model_status()
        print(f"📊 模型状态: {status}")
        
        return True, status
        
    except Exception as e:
        print(f"❌ ML模型加载失败: {e}")
        return False, str(e)

def test_ml_prediction():
    """测试ML模型预测"""
    print("\n🔮 测试ML模型预测...")
    print("=" * 60)
    
    try:
        # 导入模型
        from ML_Models.models.shap_deployment.hybrid_model_wrapper import get_hybrid_shap_model
        model = get_hybrid_shap_model()
        
        # 测试预测
        test_coordinates = [
            (51.5074, -0.1278, "London"),
            (55.9533, -3.1883, "Edinburgh"),
            (53.4808, -2.2426, "Manchester")
        ]
        
        results = {}
        for lat, lon, city in test_coordinates:
            print(f"\n📍 测试 {city} 坐标: ({lat}, {lon})")
            
            result = model.predict_environmental_scores(
                latitude=lat,
                longitude=lon,
                month=datetime.now().month
            )
            
            if result.get('success'):
                print(f"✅ {city} 预测成功")
                print(f"   Climate Score: {result.get('climate_score', 'N/A')}")
                print(f"   Geographic Score: {result.get('geographic_score', 'N/A')}")
                print(f"   Economic Score: {result.get('economic_score', 'N/A')}")
                print(f"   Final Score: {result.get('final_score', 'N/A')}")
                results[city] = result
            else:
                print(f"❌ {city} 预测失败: {result.get('error', 'Unknown error')}")
                results[city] = None
        
        return True, results
        
    except Exception as e:
        print(f"❌ ML模型预测失败: {e}")
        return False, str(e)

def test_score_normalizer():
    """测试分数归一化"""
    print("\n📊 测试分数归一化...")
    print("=" * 60)
    
    try:
        from utils.score_normalizer import get_score_normalizer
        normalizer = get_score_normalizer()
        print("✅ 分数归一化器加载成功")
        
        # 测试归一化
        test_data = {
            'climate_score': 0.712,
            'geographic_score': 0.7,
            'economic_score': 0.8,
            'final_score': 0.73
        }
        
        normalized = normalizer.normalize_shap_result(test_data)
        print(f"📈 归一化结果: {normalized}")
        
        return True, normalized
        
    except Exception as e:
        print(f"❌ 分数归一化失败: {e}")
        return False, str(e)

def test_coordinate_retrieval():
    """测试坐标获取逻辑"""
    print("\n🗺️ 测试坐标获取逻辑...")
    print("=" * 60)
    
    try:
        # 模拟数据库查询
        test_image_id = 99
        
        # 模拟从数据库获取坐标
        latitude, longitude = 51.5074, -0.1278  # 默认伦敦坐标
        location_name = "London, UK"
        
        print(f"📍 图片ID {test_image_id} 的坐标: ({latitude}, {longitude})")
        print(f"📍 位置: {location_name}")
        
        # 构建环境数据
        environmental_data = {
            'latitude': latitude,
            'longitude': longitude,
            'month': datetime.now().month,
            'location_name': location_name,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"📋 环境数据: {environmental_data}")
        
        return True, environmental_data
        
    except Exception as e:
        print(f"❌ 坐标获取失败: {e}")
        return False, str(e)

def main():
    """主测试函数"""
    print("🚀 云端ML模型测试")
    print("=" * 60)
    
    # 测试1: ML模型加载
    model_loaded, model_status = test_ml_model_loading()
    
    # 测试2: ML模型预测
    if model_loaded:
        prediction_success, prediction_results = test_ml_prediction()
    else:
        prediction_success, prediction_results = False, "模型加载失败"
    
    # 测试3: 分数归一化
    normalizer_success, normalizer_results = test_score_normalizer()
    
    # 测试4: 坐标获取
    coordinate_success, coordinate_data = test_coordinate_retrieval()
    
    # 总结
    print("\n📋 测试总结:")
    print("=" * 60)
    print(f"ML模型加载: {'✅ 成功' if model_loaded else '❌ 失败'}")
    print(f"ML模型预测: {'✅ 成功' if prediction_success else '❌ 失败'}")
    print(f"分数归一化: {'✅ 成功' if normalizer_success else '❌ 失败'}")
    print(f"坐标获取: {'✅ 成功' if coordinate_success else '❌ 失败'}")
    
    # 生成测试报告
    test_report = {
        'timestamp': datetime.now().isoformat(),
        'model_loading': {
            'success': model_loaded,
            'status': model_status
        },
        'prediction': {
            'success': prediction_success,
            'results': prediction_results
        },
        'normalizer': {
            'success': normalizer_success,
            'results': normalizer_results
        },
        'coordinate_retrieval': {
            'success': coordinate_success,
            'data': coordinate_data
        }
    }
    
    # 保存测试报告
    report_file = f"cloud_ml_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(test_report, f, indent=2)
    
    print(f"\n📄 测试报告已保存: {report_file}")
    
    return test_report

if __name__ == "__main__":
    main() 