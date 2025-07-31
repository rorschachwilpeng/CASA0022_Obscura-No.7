#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
采样策略对比实验
比较不同数据采样策略对模型性能的影响
"""

import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime
import joblib
import json
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
api_dir = os.path.join(project_root, 'api')
sys.path.insert(0, project_root)
sys.path.insert(0, api_dir)

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from utils.simplified_feature_engineer import get_simplified_feature_engineer

class SamplingStrategyComparator:
    """采样策略对比器"""
    
    def __init__(self):
        self.feature_engineer = get_simplified_feature_engineer()
        self.city_centers = {
            'London': {'lat': 51.5074, 'lon': -0.1278},
            'Manchester': {'lat': 53.4808, 'lon': -2.2426},
            'Edinburgh': {'lat': 55.9533, 'lon': -3.1883}
        }
        
    def strategy_1_broad_coverage(self, n_samples: int = 500) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        策略1：广度覆盖（当前方法）
        在整个英国范围内随机采样
        """
        print(f"🌍 策略1: 广度覆盖策略 - {n_samples}个随机样本")
        
        # 英国全境随机采样
        np.random.seed(42)
        latitudes = np.random.uniform(50.0, 60.0, n_samples)
        longitudes = np.random.uniform(-6.0, 2.0, n_samples)
        months = np.random.randint(1, 13, n_samples)
        
        return self._generate_features_and_labels(latitudes, longitudes, months, "策略1-广度")
    
    def strategy_2_city_focused(self, n_samples: int = 500) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        策略2：城市聚焦（深度策略）
        主要在三个目标城市周围密集采样
        """
        print(f"🏙️ 策略2: 城市聚焦策略 - {n_samples}个城市密集样本")
        
        np.random.seed(42)
        latitudes = []
        longitudes = []
        months = []
        
        # 每个城市分配样本数
        samples_per_city = n_samples // 3
        remaining = n_samples % 3
        
        for i, (city, center) in enumerate(self.city_centers.items()):
            city_samples = samples_per_city + (1 if i < remaining else 0)
            
            # 在城市周围50km范围内密集采样
            city_lats = np.random.normal(center['lat'], 0.3, city_samples)  # ~30km标准差
            city_lons = np.random.normal(center['lon'], 0.4, city_samples)  # ~40km标准差
            city_months = np.random.randint(1, 13, city_samples)
            
            latitudes.extend(city_lats)
            longitudes.extend(city_lons)
            months.extend(city_months)
            
            print(f"   {city}: {city_samples}个样本")
        
        return self._generate_features_and_labels(
            np.array(latitudes), np.array(longitudes), np.array(months), "策略2-深度"
        )
    
    def strategy_3_hybrid(self, n_samples: int = 500) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        策略3：混合策略
        城市密集采样 + 英国随机采样
        """
        print(f"⚖️ 策略3: 混合策略 - {n_samples}个混合样本")
        
        np.random.seed(42)
        
        # 分配比例：70%城市密集，30%全英随机
        city_samples = int(n_samples * 0.7)
        random_samples = n_samples - city_samples
        
        latitudes = []
        longitudes = []
        months = []
        
        # 城市密集部分
        samples_per_city = city_samples // 3
        for city, center in self.city_centers.items():
            city_lats = np.random.normal(center['lat'], 0.2, samples_per_city)
            city_lons = np.random.normal(center['lon'], 0.3, samples_per_city)
            city_months = np.random.randint(1, 13, samples_per_city)
            
            latitudes.extend(city_lats)
            longitudes.extend(city_lons)
            months.extend(city_months)
        
        # 全英随机部分
        random_lats = np.random.uniform(50.0, 60.0, random_samples)
        random_lons = np.random.uniform(-6.0, 2.0, random_samples)
        random_months = np.random.randint(1, 13, random_samples)
        
        latitudes.extend(random_lats)
        longitudes.extend(random_lons)
        months.extend(random_months)
        
        print(f"   城市密集: {city_samples}个样本 (70%)")
        print(f"   全英随机: {random_samples}个样本 (30%)")
        
        return self._generate_features_and_labels(
            np.array(latitudes), np.array(longitudes), np.array(months), "策略3-混合"
        )
    
    def _generate_features_and_labels(self, latitudes: np.ndarray, longitudes: np.ndarray, 
                                    months: np.ndarray, strategy_name: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """生成特征和标签"""
        X = []
        y_climate = []
        y_geographic = []
        
        n_samples = len(latitudes)
        
        for i, (lat, lon, month) in enumerate(zip(latitudes, longitudes, months)):
            if i % 100 == 0:
                print(f"   {strategy_name}: 生成样本 {i+1}/{n_samples}")
            
            try:
                # 生成66特征
                features = self.feature_engineer.prepare_features_for_prediction(lat, lon, month, 66)
                
                # 生成合成标签
                climate_features = features[:44]
                climate_score = np.tanh(np.mean(climate_features[:11]) / 100) * 2
                
                geo_features = features[44:]
                geographic_score = np.tanh(np.mean(geo_features) * 0.5) * 1.5
                
                X.append(features)
                y_climate.append(climate_score)
                y_geographic.append(geographic_score)
                
            except Exception as e:
                print(f"   ⚠️ {strategy_name}: 跳过样本 {i}: {e}")
                continue
        
        return np.array(X), np.array(y_climate), np.array(y_geographic)
    
    def train_and_evaluate_strategy(self, X: np.ndarray, y_climate: np.ndarray, 
                                  y_geographic: np.ndarray, strategy_name: str) -> Dict:
        """训练并评估单个策略"""
        print(f"\n🔧 训练{strategy_name}模型...")
        
        results = {}
        
        for target_name, y in [('climate', y_climate), ('geographic', y_geographic)]:
            print(f"   训练{target_name}模型...")
            
            # 数据分割
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # 训练Random Forest
            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=20,
                random_state=42,
                n_jobs=-1
            )
            model.fit(X_train, y_train)
            
            # 预测和评估
            y_pred = model.predict(X_test)
            
            metrics = {
                'MSE': float(mean_squared_error(y_test, y_pred)),
                'RMSE': float(np.sqrt(mean_squared_error(y_test, y_pred))),
                'MAE': float(mean_absolute_error(y_test, y_pred)),
                'R2': float(r2_score(y_test, y_pred)),
                'train_samples': X_train.shape[0],
                'test_samples': X_test.shape[0]
            }
            
            results[target_name] = metrics
            print(f"     {target_name}: RMSE={metrics['RMSE']:.4f}, R2={metrics['R2']:.4f}")
        
        return results
    
    def generate_city_specific_test_set(self, n_per_city: int = 50) -> Dict:
        """生成城市特定的测试集，用于评估不同策略在具体城市的表现"""
        print(f"\n🏙️ 生成城市特定测试集 (每城市{n_per_city}个样本)...")
        
        city_test_sets = {}
        
        for city, center in self.city_centers.items():
            print(f"   生成{city}测试数据...")
            
            # 在城市中心周围生成测试样本
            np.random.seed(123)  # 不同的种子确保独立性
            lats = np.random.normal(center['lat'], 0.1, n_per_city)  # 更小的范围
            lons = np.random.normal(center['lon'], 0.15, n_per_city)
            months = np.random.randint(1, 13, n_per_city)
            
            X_test, y_climate_test, y_geo_test = self._generate_features_and_labels(
                lats, lons, months, f"{city}测试集"
            )
            
            city_test_sets[city] = {
                'X': X_test,
                'y_climate': y_climate_test,
                'y_geographic': y_geo_test,
                'coordinates': list(zip(lats, lons, months))
            }
        
        return city_test_sets
    
    def run_comparison_experiment(self, n_samples: int = 300):
        """运行完整的对比实验"""
        print("🚀 开始采样策略对比实验")
        print("=" * 80)
        
        # 1. 生成三种策略的训练数据
        strategies = {}
        
        print("\n📊 生成训练数据...")
        strategies['广度覆盖'] = self.strategy_1_broad_coverage(n_samples)
        strategies['城市聚焦'] = self.strategy_2_city_focused(n_samples)
        strategies['混合策略'] = self.strategy_3_hybrid(n_samples)
        
        # 2. 训练和评估每种策略
        print("\n🔧 训练模型...")
        results = {}
        trained_models = {}
        
        for strategy_name, (X, y_climate, y_geo) in strategies.items():
            results[strategy_name] = self.train_and_evaluate_strategy(
                X, y_climate, y_geo, strategy_name
            )
            
            # 保存模型用于城市特定测试
            X_train, X_test, y_climate_train, y_climate_test = train_test_split(
                X, y_climate, test_size=0.2, random_state=42
            )
            _, _, y_geo_train, y_geo_test = train_test_split(
                X, y_geo, test_size=0.2, random_state=42
            )
            
            climate_model = RandomForestRegressor(n_estimators=100, random_state=42)
            geo_model = RandomForestRegressor(n_estimators=100, random_state=42)
            
            climate_model.fit(X_train, y_climate_train)
            geo_model.fit(X_train, y_geo_train)
            
            trained_models[strategy_name] = {
                'climate': climate_model,
                'geographic': geo_model
            }
        
        # 3. 城市特定性能测试
        print("\n🏙️ 城市特定性能测试...")
        city_test_sets = self.generate_city_specific_test_set(50)
        city_specific_results = {}
        
        for strategy_name, models in trained_models.items():
            city_specific_results[strategy_name] = {}
            
            for city, test_data in city_test_sets.items():
                city_results = {}
                
                for target_name in ['climate', 'geographic']:
                    model = models[target_name]
                    X_test = test_data['X']
                    y_test = test_data[f'y_{target_name}']
                    
                    y_pred = model.predict(X_test)
                    
                    city_results[target_name] = {
                        'RMSE': float(np.sqrt(mean_squared_error(y_test, y_pred))),
                        'R2': float(r2_score(y_test, y_pred))
                    }
                
                city_specific_results[strategy_name][city] = city_results
                print(f"   {strategy_name} - {city}: Climate R2={city_results['climate']['R2']:.3f}, "
                      f"Geographic R2={city_results['geographic']['R2']:.3f}")
        
        # 4. 生成对比报告
        comparison_report = {
            'experiment_info': {
                'n_samples': n_samples,
                'timestamp': datetime.now().isoformat(),
                'strategies_tested': list(strategies.keys())
            },
            'overall_performance': results,
            'city_specific_performance': city_specific_results
        }
        
        # 保存结果
        report_path = f"sampling_strategy_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(comparison_report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 完整报告已保存: {report_path}")
        
        # 5. 打印简要总结
        self._print_summary(results, city_specific_results)
        
        return comparison_report
    
    def _print_summary(self, overall_results: Dict, city_results: Dict):
        """打印对比总结"""
        print("\n" + "=" * 80)
        print("📋 实验总结")
        print("=" * 80)
        
        print("\n🌍 整体性能对比:")
        print("-" * 60)
        for strategy, metrics in overall_results.items():
            climate_r2 = metrics['climate']['R2']
            geo_r2 = metrics['geographic']['R2']
            print(f"{strategy:>12}: Climate R²={climate_r2:.3f} | Geographic R²={geo_r2:.3f}")
        
        print("\n🏙️ 城市特定性能对比:")
        print("-" * 60)
        for city in ['London', 'Manchester', 'Edinburgh']:
            print(f"\n{city}:")
            for strategy in city_results.keys():
                climate_r2 = city_results[strategy][city]['climate']['R2']
                geo_r2 = city_results[strategy][city]['geographic']['R2']
                print(f"  {strategy:>12}: Climate R²={climate_r2:.3f} | Geographic R²={geo_r2:.3f}")

def main():
    """主函数"""
    comparator = SamplingStrategyComparator()
    
    # 运行对比实验（使用较小的样本量以加快测试）
    print("开始采样策略对比实验...")
    print("注意：使用较小样本量(300)以加快实验速度")
    
    results = comparator.run_comparison_experiment(n_samples=300)
    return results

if __name__ == "__main__":
    main() 