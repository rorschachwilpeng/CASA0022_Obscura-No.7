#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
66特征模型训练脚本 - 优化版本
- 实时进度条显示数据收集进度
- 数据收集完成后立即保存，训练前加载
- 支持小规模验证模式
"""

import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime
import joblib
import json
import pickle
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

# 进度条
from tqdm import tqdm

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
api_dir = os.path.join(project_root, 'api')
sys.path.insert(0, project_root)
sys.path.insert(0, api_dir)

# ML相关库
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler

# 深度学习相关库
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout, Conv1D, MaxPooling1D, Flatten
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    TF_AVAILABLE = True
    print("✅ TensorFlow可用")
except ImportError:
    TF_AVAILABLE = False
    print("❌ TensorFlow不可用，将跳过深度学习模型")

from utils.simplified_feature_engineer import get_simplified_feature_engineer

class OptimizedModelTrainer:
    """优化的66特征模型训练器"""
    
    def __init__(self, output_dir: str = "trained_models_66", cache_dir: str = "training_data_cache"):
        """初始化训练器"""
        self.output_dir = output_dir
        self.cache_dir = cache_dir
        self.feature_engineer = get_simplified_feature_engineer()
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        print(f"OptimizedModelTrainer初始化完成")
        print(f"输出目录: {self.output_dir}")
        print(f"缓存目录: {self.cache_dir}")
    
    def get_cache_filename(self, n_samples: int) -> str:
        """根据样本数生成缓存文件名"""
        return os.path.join(self.cache_dir, f"training_data_{n_samples}_samples.pkl")
    
    def load_cached_data(self, n_samples: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """从缓存加载训练数据"""
        cache_file = self.get_cache_filename(n_samples)
        
        if os.path.exists(cache_file):
            print(f"📁 发现缓存数据: {cache_file}")
            try:
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                
                X = cached_data['X']
                y_climate = cached_data['y_climate']
                y_geographic = cached_data['y_geographic']
                
                print(f"✅ 缓存数据加载成功:")
                print(f"   特征形状: {X.shape}")
                print(f"   Climate标签范围: [{y_climate.min():.3f}, {y_climate.max():.3f}]")
                print(f"   Geographic标签范围: [{y_geographic.min():.3f}, {y_geographic.max():.3f}]")
                print(f"   缓存时间: {cached_data.get('timestamp', 'Unknown')}")
                
                return X, y_climate, y_geographic
                
            except Exception as e:
                print(f"⚠️ 缓存数据加载失败: {e}")
                print("将重新生成数据...")
                return None, None, None
        else:
            print(f"📂 未发现{n_samples}样本的缓存数据，将重新生成...")
            return None, None, None
    
    def save_data_to_cache(self, X: np.ndarray, y_climate: np.ndarray, y_geographic: np.ndarray, n_samples: int):
        """保存数据到缓存"""
        cache_file = self.get_cache_filename(n_samples)
        
        try:
            cache_data = {
                'X': X,
                'y_climate': y_climate,
                'y_geographic': y_geographic,
                'timestamp': datetime.now().isoformat(),
                'n_samples': X.shape[0],
                'n_features': X.shape[1],
                'sampling_strategy': 'hybrid_70_30'
            }
            
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            
            print(f"💾 数据已缓存到: {cache_file}")
            print(f"   文件大小: {os.path.getsize(cache_file) / 1024 / 1024:.2f} MB")
            
        except Exception as e:
            print(f"⚠️ 数据缓存失败: {e}")
    
    def generate_coordinates(self, n_samples: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """生成混合策略采样坐标"""
        print(f"⚖️ 生成混合策略坐标: {n_samples} 样本")
        print("   策略: 70%城市密集 + 30%全英随机")
        
        np.random.seed(42)  # 固定种子以确保可重现性
        
        # 分配比例：70%城市密集，30%全英随机
        city_samples = int(n_samples * 0.7)
        random_samples = n_samples - city_samples
        
        latitudes = []
        longitudes = []
        months = []
        
        # 城市密集部分 (70%)
        samples_per_city = city_samples // 3
        remaining_city = city_samples % 3
        
        city_centers = {
            'London': {'lat': 51.5074, 'lon': -0.1278},
            'Manchester': {'lat': 53.4808, 'lon': -2.2426},
            'Edinburgh': {'lat': 55.9533, 'lon': -3.1883}
        }
        
        print(f"   🏙️ 城市密集采样: {city_samples}个样本")
        for i, (city, center) in enumerate(city_centers.items()):
            city_sample_count = samples_per_city + (1 if i < remaining_city else 0)
            
            # 在城市周围密集采样 (标准差约20-30km)
            city_lats = np.random.normal(center['lat'], 0.2, city_sample_count)
            city_lons = np.random.normal(center['lon'], 0.3, city_sample_count)
            city_months = np.random.randint(1, 13, city_sample_count)
            
            latitudes.extend(city_lats)
            longitudes.extend(city_lons)
            months.extend(city_months)
            
            print(f"     {city}: {city_sample_count}个样本 (±20-30km范围)")
        
        # 全英随机部分 (30%)
        print(f"   🌍 全英随机采样: {random_samples}个样本")
        random_lats = np.random.uniform(50.0, 60.0, random_samples)
        random_lons = np.random.uniform(-6.0, 2.0, random_samples)
        random_months = np.random.randint(1, 13, random_samples)
        
        latitudes.extend(random_lats)
        longitudes.extend(random_lons)
        months.extend(random_months)
        
        return np.array(latitudes), np.array(longitudes), np.array(months)
    
    def collect_training_data(self, n_samples: int = 50) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """收集训练数据（带进度条）"""
        
        # 检查缓存
        X_cached, y_climate_cached, y_geo_cached = self.load_cached_data(n_samples)
        if X_cached is not None:
            return X_cached, y_climate_cached, y_geo_cached
        
        # 生成采样坐标
        latitudes, longitudes, months = self.generate_coordinates(n_samples)
        
        # 初始化数据收集
        X = []
        y_climate = []
        y_geographic = []
        failed_samples = []
        
        print(f"\n🚀 开始收集{n_samples}个样本的训练数据...")
        print(f"📡 预计API调用次数: {n_samples * 5} (每样本5次)")
        
        # 使用tqdm创建进度条
        with tqdm(total=n_samples, desc="🌍 收集样本", 
                 bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]") as pbar:
            
            for i, (lat, lon, month) in enumerate(zip(latitudes, longitudes, months)):
                try:
                    # 更新进度条描述
                    pbar.set_description(f"🌍 样本 {i+1}/{n_samples} (API调用中...)")
                    
                    # 生成66特征
                    features = self.feature_engineer.prepare_features_for_prediction(lat, lon, month, 66)
                    
                    # 生成合成标签
                    climate_features = features[:44]  # 前44个是滞后特征
                    climate_score = np.tanh(np.mean(climate_features[:11]) / 100) * 2  # 标准化到[-2, 2]
                    
                    geo_features = features[44:]  # 后22个是变化率特征
                    geographic_score = np.tanh(np.mean(geo_features) * 0.5) * 1.5  # 标准化到[-1.5, 1.5]
                    
                    X.append(features)
                    y_climate.append(climate_score)
                    y_geographic.append(geographic_score)
                    
                    # 更新进度条描述为成功
                    pbar.set_description(f"✅ 样本 {i+1}/{n_samples} (完成)")
                    
                except Exception as e:
                    failed_samples.append((i, lat, lon, month, str(e)))
                    pbar.set_description(f"❌ 样本 {i+1}/{n_samples} (失败)")
                    tqdm.write(f"   ⚠️ 跳过样本 {i+1}: {e}")
                
                # 更新进度条
                pbar.update(1)
                
                # 每10个样本显示一次统计
                if (i + 1) % 10 == 0:
                    success_rate = (len(X) / (i + 1)) * 100
                    tqdm.write(f"   📊 进度统计: 成功 {len(X)}/{i+1} ({success_rate:.1f}%)")
        
        # 转换为numpy数组
        X = np.array(X) if X else np.array([]).reshape(0, 66)
        y_climate = np.array(y_climate) if y_climate else np.array([])
        y_geographic = np.array(y_geographic) if y_geographic else np.array([])
        
        # 数据收集总结
        print(f"\n✅ 数据收集完成:")
        print(f"   📊 成功样本: {len(X)}/{n_samples} ({len(X)/n_samples*100:.1f}%)")
        print(f"   📊 失败样本: {len(failed_samples)}")
        print(f"   📊 特征形状: {X.shape}")
        
        if len(X) > 0:
            print(f"   📊 Climate标签范围: [{y_climate.min():.3f}, {y_climate.max():.3f}]")
            print(f"   📊 Geographic标签范围: [{y_geographic.min():.3f}, {y_geographic.max():.3f}]")
        
        if failed_samples:
            print(f"\n⚠️ 失败样本详情:")
            for idx, lat, lon, month, error in failed_samples[:5]:  # 只显示前5个
                print(f"   样本{idx+1}: ({lat:.3f}, {lon:.3f}, 月份{month}) - {error}")
            if len(failed_samples) > 5:
                print(f"   ... 还有 {len(failed_samples)-5} 个失败样本")
        
        # 立即保存数据到缓存
        if len(X) > 0:
            print(f"\n💾 立即保存数据到缓存...")
            self.save_data_to_cache(X, y_climate, y_geographic, n_samples)
        else:
            print(f"\n❌ 没有成功收集到数据，跳过缓存保存")
        
        return X, y_climate, y_geographic
    
    def train_single_model(self, model_type: str, X_train: np.ndarray, y_train: np.ndarray,
                          X_val: np.ndarray, y_val: np.ndarray, target_name: str,
                          fast_mode: bool = True) -> Tuple[Any, Dict]:
        """训练单个模型（可选快速模式）"""
        
        if model_type == 'RandomForest':
            return self._train_rf(X_train, y_train, target_name, fast_mode)
        elif model_type == 'LSTM':
            return self._train_lstm(X_train, y_train, X_val, y_val, target_name, fast_mode)
        elif model_type == '1D-CNN':
            return self._train_cnn1d(X_train, y_train, X_val, y_val, target_name, fast_mode)
        else:
            raise ValueError(f"未知模型类型: {model_type}")
    
    def _train_rf(self, X_train: np.ndarray, y_train: np.ndarray, target_name: str, fast_mode: bool) -> Tuple[Any, Dict]:
        """训练Random Forest模型"""
        print(f"🌲 训练Random Forest模型 - {target_name}")
        
        if fast_mode:
            rf_config = {
                'n_estimators': 10,  # 快速模式：减少树的数量
                'max_depth': 5,      # 快速模式：减少深度
                'min_samples_split': 5,
                'min_samples_leaf': 2,
                'random_state': 42,
                'n_jobs': -1
            }
            print("   🚀 快速模式：使用较小的参数")
        else:
            rf_config = {
                'n_estimators': 100,
                'max_depth': 20,
                'min_samples_split': 5,
                'min_samples_leaf': 2,
                'random_state': 42,
                'n_jobs': -1
            }
        
        model = RandomForestRegressor(**rf_config)
        model.fit(X_train, y_train)
        
        # 特征重要性
        feature_names = self.feature_engineer.get_feature_names()
        feature_importance = dict(zip(feature_names, model.feature_importances_))
        
        metadata = {
            'model_type': 'RandomForest',
            'config': rf_config,
            'feature_importance': feature_importance,
            'n_features': X_train.shape[1],
            'n_samples': X_train.shape[0],
            'fast_mode': fast_mode
        }
        
        print(f"   ✅ Random Forest训练完成")
        return model, metadata
    
    def _train_lstm(self, X_train: np.ndarray, y_train: np.ndarray,
                   X_val: np.ndarray, y_val: np.ndarray, target_name: str, fast_mode: bool) -> Tuple[Any, Dict]:
        """训练LSTM模型"""
        print(f"🧠 训练LSTM模型 - {target_name}")
        
        if not TF_AVAILABLE:
            raise RuntimeError("TensorFlow不可用，无法训练LSTM模型")
        
        # 重塑数据
        X_train_lstm = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)
        X_val_lstm = X_val.reshape(X_val.shape[0], X_val.shape[1], 1)
        
        if fast_mode:
            # 快速模式：更小的网络和更少的训练轮数
            model = Sequential([
                LSTM(16, return_sequences=False, input_shape=(66, 1)),
                Dense(8, activation='relu'),
                Dense(1, activation='linear')
            ])
            epochs = 5
            print("   🚀 快速模式：使用较小的网络和更少训练轮数")
        else:
            model = Sequential([
                LSTM(64, return_sequences=True, input_shape=(66, 1)),
                Dropout(0.2),
                LSTM(32, return_sequences=False),
                Dropout(0.2),
                Dense(16, activation='relu'),
                Dense(1, activation='linear')
            ])
            epochs = 50
        
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse', metrics=['mae'])
        
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=3 if fast_mode else 10, restore_best_weights=True)
        ]
        
        history = model.fit(
            X_train_lstm, y_train,
            validation_data=(X_val_lstm, y_val),
            epochs=epochs,
            batch_size=16 if fast_mode else 32,
            callbacks=callbacks,
            verbose=0
        )
        
        metadata = {
            'model_type': 'LSTM',
            'epochs_trained': len(history.history['loss']),
            'final_loss': float(history.history['loss'][-1]),
            'final_val_loss': float(history.history['val_loss'][-1]),
            'fast_mode': fast_mode
        }
        
        print(f"   ✅ LSTM训练完成，训练了{metadata['epochs_trained']}轮")
        return model, metadata
    
    def _train_cnn1d(self, X_train: np.ndarray, y_train: np.ndarray,
                    X_val: np.ndarray, y_val: np.ndarray, target_name: str, fast_mode: bool) -> Tuple[Any, Dict]:
        """训练1D CNN模型"""
        print(f"🔍 训练Deep 1D-CNN模型 - {target_name}")
        
        if not TF_AVAILABLE:
            raise RuntimeError("TensorFlow不可用，无法训练CNN模型")
        
        # 重塑数据
        X_train_cnn = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)
        X_val_cnn = X_val.reshape(X_val.shape[0], X_val.shape[1], 1)
        
        if fast_mode:
            # 快速模式：更简单的网络
            model = Sequential([
                Conv1D(filters=16, kernel_size=3, activation='relu', input_shape=(66, 1)),
                MaxPooling1D(pool_size=2),
                Conv1D(filters=8, kernel_size=3, activation='relu'),
                Flatten(),
                Dense(16, activation='relu'),
                Dense(1, activation='linear')
            ])
            epochs = 5
            print("   🚀 快速模式：使用较简单的网络")
        else:
            model = Sequential([
                Conv1D(filters=64, kernel_size=3, activation='relu', input_shape=(66, 1)),
                MaxPooling1D(pool_size=2),
                Conv1D(filters=32, kernel_size=3, activation='relu'),
                MaxPooling1D(pool_size=2),
                Conv1D(filters=16, kernel_size=3, activation='relu'),
                Flatten(),
                Dense(50, activation='relu'),
                Dropout(0.3),
                Dense(25, activation='relu'),
                Dense(1, activation='linear')
            ])
            epochs = 50
        
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse', metrics=['mae'])
        
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=3 if fast_mode else 10, restore_best_weights=True)
        ]
        
        history = model.fit(
            X_train_cnn, y_train,
            validation_data=(X_val_cnn, y_val),
            epochs=epochs,
            batch_size=16 if fast_mode else 32,
            callbacks=callbacks,
            verbose=0
        )
        
        metadata = {
            'model_type': '1D-CNN',
            'epochs_trained': len(history.history['loss']),
            'final_loss': float(history.history['loss'][-1]),
            'final_val_loss': float(history.history['val_loss'][-1]),
            'fast_mode': fast_mode
        }
        
        print(f"   ✅ 1D-CNN训练完成，训练了{metadata['epochs_trained']}轮")
        return model, metadata
    
    def evaluate_model(self, model, X_test: np.ndarray, y_test: np.ndarray, model_type: str) -> Dict:
        """评估模型性能"""
        
        # 预测
        if model_type in ['LSTM', '1D-CNN']:
            X_test_reshaped = X_test.reshape(X_test.shape[0], X_test.shape[1], 1)
            y_pred = model.predict(X_test_reshaped, verbose=0).flatten()
        else:  # RF
            y_pred = model.predict(X_test)
        
        # 计算指标
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        metrics = {
            'MSE': float(mse),
            'RMSE': float(rmse),
            'MAE': float(mae),
            'R2': float(r2)
        }
        
        print(f"     📊 RMSE: {rmse:.4f}, R²: {r2:.4f}, MAE: {mae:.4f}")
        return metrics

def main(n_samples: int = 20, fast_mode: bool = True):
    """主训练流程"""
    print("🚀 开始66特征模型训练（优化版本）")
    print("=" * 80)
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 样本数量: {n_samples}")
    print(f"⚡ 快速模式: {'开启' if fast_mode else '关闭'}")
    
    # 初始化训练器
    trainer = OptimizedModelTrainer()
    
    # 阶段1：数据收集
    print(f"\n" + "=" * 60)
    print("🗂️ 阶段1: 数据收集")
    print("=" * 60)
    
    X, y_climate, y_geographic = trainer.collect_training_data(n_samples=n_samples)
    
    if len(X) == 0:
        print("❌ 没有成功收集到数据，终止训练")
        return None
    
    # 阶段2：数据分割
    print(f"\n" + "=" * 60)
    print("🔄 阶段2: 数据分割")
    print("=" * 60)
    
    if len(X) < 10:
        print("⚠️ 样本数量太少，使用简单分割")
        # 简单分割
        split_idx = int(len(X) * 0.7)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_climate_train, y_climate_test = y_climate[:split_idx], y_climate[split_idx:]
        y_geo_train, y_geo_test = y_geographic[:split_idx], y_geographic[split_idx:]
        
        # 验证集就用训练集
        X_val, y_climate_val, y_geo_val = X_train, y_climate_train, y_geo_train
    else:
        # 正常分割
        X_train, X_test, y_climate_train, y_climate_test, y_geo_train, y_geo_test = train_test_split(
            X, y_climate, y_geographic, test_size=0.3, random_state=42)
        
        X_train, X_val, y_climate_train, y_climate_val, y_geo_train, y_geo_val = train_test_split(
            X_train, y_climate_train, y_geo_train, test_size=0.3, random_state=42)
    
    print(f"   训练集: {X_train.shape[0]} 样本")
    print(f"   验证集: {X_val.shape[0]} 样本")
    print(f"   测试集: {X_test.shape[0]} 样本")
    
    # 标准化
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    # 阶段3：模型训练
    print(f"\n" + "=" * 60)
    print("🤖 阶段3: 模型训练")
    print("=" * 60)
    
    # 要训练的模型类型
    model_types = ['RandomForest']
    if TF_AVAILABLE:
        model_types.extend(['LSTM', '1D-CNN'])
    
    # 目标变量
    targets = {
        'climate': (y_climate_train, y_climate_val, y_climate_test),
        'geographic': (y_geo_train, y_geo_val, y_geo_test)
    }
    
    results = {}
    
    for target_name, (y_train, y_val, y_test) in targets.items():
        print(f"\n🎯 训练 {target_name.upper()} 模型")
        results[target_name] = {}
        
        for model_type in model_types:
            print(f"\n   🔧 {model_type} - {target_name}")
            
            try:
                # 选择数据
                if model_type == 'RandomForest':
                    X_train_use, X_val_use, X_test_use = X_train, X_val, X_test
                else:
                    X_train_use, X_val_use, X_test_use = X_train_scaled, X_val_scaled, X_test_scaled
                
                # 训练模型
                model, metadata = trainer.train_single_model(
                    model_type, X_train_use, y_train, X_val_use, y_val, target_name, fast_mode
                )
                
                # 评估模型
                metrics = trainer.evaluate_model(model, X_test_use, y_test, model_type)
                
                results[target_name][model_type] = {
                    'metrics': metrics,
                    'metadata': metadata
                }
                
                print(f"     ✅ {model_type} 完成")
                
            except Exception as e:
                print(f"     ❌ {model_type} 失败: {e}")
                results[target_name][model_type] = {'error': str(e)}
    
    # 结果总结
    print(f"\n" + "=" * 80)
    print("📊 训练结果总结")
    print("=" * 80)
    
    for target_name, target_results in results.items():
        print(f"\n🎯 {target_name.upper()} 模型:")
        for model_type, result in target_results.items():
            if 'error' in result:
                print(f"   {model_type:>12}: ❌ {result['error']}")
            else:
                metrics = result['metrics']
                print(f"   {model_type:>12}: R²={metrics['R2']:.3f}, RMSE={metrics['RMSE']:.3f}")
    
    print(f"\n⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎉 小规模验证完成！")
    
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='66特征模型训练 - 优化版本')
    parser.add_argument('--samples', type=int, default=20, help='样本数量 (默认: 20)')
    parser.add_argument('--full', action='store_true', help='完整模式（关闭快速模式）')
    
    args = parser.parse_args()
    
    # 运行训练
    results = main(n_samples=args.samples, fast_mode=not args.full) 