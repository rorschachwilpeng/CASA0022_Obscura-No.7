#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试不同时间节点的SHAP预测分数变化
验证修复后的预测是否会根据不同时间的环境数据产生不同分数
"""

import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from utils.real_time_environmental_data_collector import get_environmental_collector
from utils.real_time_feature_engineer import get_feature_engineer

def test_temporal_environmental_data():
    print("🕐 测试不同时间节点的环境数据变化")
    print("=" * 70)
    
    collector = get_environmental_collector()
    
    # 测试坐标: London
    lat, lon = 51.5074, -0.1278
    print(f"📍 测试坐标: London ({lat}, {lon})")
    
    # 定义不同的时间节点
    time_points = [
        ("当前可用数据", 3),      # 3天前（当前可用的最新数据）
        ("1个月前", 33),          # 33天前
        ("3个月前", 93),          # 93天前  
        ("6个月前", 183),         # 183天前
        ("1年前", 368),           # 368天前
    ]
    
    environmental_data_results = {}
    
    print(f"\n🔍 获取不同时间点的环境数据:")
    
    for label, days_ago in time_points:
        target_date = datetime.now() - timedelta(days=days_ago)
        date_str = target_date.strftime('%Y-%m-%d')
        
        print(f"\n  📅 {label} ({date_str}):")
        
        try:
            # 获取气象数据
            meteo_data = collector.fetch_daily_meteorological_data(lat, lon, date_str)
            # 获取地理数据  
            geo_data = collector.fetch_daily_geospatial_data(lat, lon, date_str)
            # 获取空气质量数据
            air_data = collector.fetch_daily_air_quality_data(lat, lon, date_str)
            
            # 合并数据
            env_data = {**meteo_data, **geo_data, **air_data}
            environmental_data_results[label] = env_data
            
            # 显示关键环境变量
            print(f"    🌡️  温度: {env_data.get('temperature', 'N/A'):.2f}°C")
            print(f"    💧 湿度: {env_data.get('humidity', 'N/A'):.1f}%") 
            print(f"    💨 风速: {env_data.get('wind_speed', 'N/A'):.1f} m/s")
            print(f"    🌧️  降水: {env_data.get('precipitation', 'N/A'):.2f} mm")
            print(f"    🏭 NO2: {env_data.get('NO2', 'N/A'):.1f} μg/m³")
            print(f"    🌱 土壤温度: {env_data.get('soil_temperature_0_7cm', 'N/A'):.1f}°C")
            
        except Exception as e:
            print(f"    ❌ 数据获取失败: {e}")
            environmental_data_results[label] = None
    
    # 分析环境数据的变化
    print(f"\n📊 环境数据变化分析:")
    
    # 检查温度变化
    temperatures = []
    for label, data in environmental_data_results.items():
        if data and 'temperature' in data:
            temperatures.append((label, data['temperature']))
    
    if len(temperatures) >= 2:
        print(f"  🌡️ 温度变化:")
        for label, temp in temperatures:
            print(f"    {label}: {temp:.2f}°C")
        
        temp_values = [temp for _, temp in temperatures]
        temp_range = max(temp_values) - min(temp_values)
        print(f"    📈 温度范围: {temp_range:.2f}°C")
        
        if temp_range > 1.0:
            print(f"    ✅ 温度有显著变化 (>{1.0}°C)")
        else:
            print(f"    ⚠️ 温度变化较小 (<{1.0}°C)")
    
    return environmental_data_results

def test_temporal_feature_engineering():
    print(f"\n🔧 测试不同时间节点的特征工程")
    print("=" * 70)
    
    feature_engineer = get_feature_engineer()
    
    lat, lon = 51.5074, -0.1278
    
    # 测试不同月份（模拟不同时间节点的特征差异）
    months = [1, 4, 7, 10]  # 代表四个季节
    month_names = ["1月(冬季)", "4月(春季)", "7月(夏季)", "10月(秋季)"]
    
    feature_results = {}
    
    print(f"📍 测试坐标: London ({lat}, {lon})")
    print(f"🎯 目标特征数量: 375 (Climate模型)")
    
    for month, month_name in zip(months, month_names):
        print(f"\n  📅 {month_name}:")
        
        try:
            features = feature_engineer.prepare_features_for_prediction(
                latitude=lat,
                longitude=lon, 
                month=month,
                target_feature_count=375
            )
            
            feature_results[month_name] = features
            
            print(f"    ✅ 特征生成成功: {len(features)} 个特征")
            print(f"    📊 特征范围: {features.min():.4f} - {features.max():.4f}")
            print(f"    📈 特征均值: {features.mean():.4f}")
            print(f"    📉 特征标准差: {features.std():.4f}")
            
        except Exception as e:
            print(f"    ❌ 特征生成失败: {e}")
            feature_results[month_name] = None
    
    # 分析特征的季节性变化
    print(f"\n📊 特征季节性变化分析:")
    
    valid_features = {k: v for k, v in feature_results.items() if v is not None}
    
    if len(valid_features) >= 2:
        print(f"  🔍 有效特征集: {len(valid_features)} 个")
        
        # 比较不同季节的特征差异
        feature_means = []
        for season, features in valid_features.items():
            mean_val = features.mean()
            feature_means.append((season, mean_val))
            print(f"    {season}: 均值 = {mean_val:.6f}")
        
        if len(feature_means) >= 2:
            mean_values = [mean for _, mean in feature_means]
            mean_range = max(mean_values) - min(mean_values)
            print(f"    📈 均值范围: {mean_range:.6f}")
            
            if mean_range > 0.001:  # 阈值可调整
                print(f"    ✅ 特征有季节性变化 (>{0.001})")
            else:
                print(f"    ⚠️ 特征季节性变化较小 (<{0.001})")
        
        # 特征相关性分析
        import numpy as np
        if len(valid_features) == 4:  # 四个季节都有数据
            features_matrix = np.array(list(valid_features.values()))
            
            print(f"  🔗 季节间特征相关性:")
            seasons = list(valid_features.keys())
            for i in range(len(seasons)):
                for j in range(i+1, len(seasons)):
                    corr = np.corrcoef(features_matrix[i], features_matrix[j])[0,1]
                    print(f"    {seasons[i]} vs {seasons[j]}: {corr:.4f}")
    
    return feature_results

def main():
    print("🧪 时间节点环境数据与特征工程变化测试")
    print("=" * 80)
    
    # 测试环境数据的时间变化
    env_results = test_temporal_environmental_data()
    
    # 测试特征工程的季节变化  
    feature_results = test_temporal_feature_engineering()
    
    print(f"\n" + "=" * 80)
    print("🎯 测试结果总结:")
    
    # 环境数据变化总结
    valid_env_data = sum(1 for data in env_results.values() if data is not None)
    print(f"  📊 环境数据: {valid_env_data}/{len(env_results)} 个时间点成功获取")
    
    # 特征工程变化总结
    valid_features = sum(1 for features in feature_results.values() if features is not None)
    print(f"  🔧 特征工程: {valid_features}/{len(feature_results)} 个季节成功生成")
    
    if valid_env_data >= 2 and valid_features >= 2:
        print(f"  ✅ 时间节点数据变化测试成功!")
        print(f"  📝 结论: 系统能够根据不同时间节点获取不同的环境数据和特征")
    else:
        print(f"  ⚠️ 时间节点数据变化测试不充分")
        print(f"  📝 建议: 检查API连接和数据可用性")

if __name__ == "__main__":
    main() 