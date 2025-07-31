#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
66特征模型训练脚本
支持LSTM、Random Forest、Deep 1D-CNN三种架构
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
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

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

class ModelTrainer:
    """66特征模型训练器"""
    
    def __init__(self, output_dir: str = "trained_models_66"):
        """初始化训练器"""
        self.output_dir = output_dir
        self.feature_engineer = get_simplified_feature_engineer()
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 模型配置
        self.models_config = {
            'lstm': {
                'name': 'LSTM',
                'description': 'Long Short-Term Memory Neural Network',
                'requires_tf': True
            },
            'rf': {
                'name': 'Random Forest',
                'description': 'Random Forest Regressor',
                'requires_tf': False
            },
            'cnn1d': {
                'name': 'Deep 1D-CNN',
                'description': '1D Convolutional Neural Network',
                'requires_tf': True
            }
        }
        
        print(f"ModelTrainer初始化完成，输出目录: {self.output_dir}")
    
    def generate_synthetic_training_data(self, n_samples: int = 1000) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        生成合成训练数据 (用于演示，实际应使用真实历史数据)
        
        Returns:
            X: 特征数据 (n_samples, 66)
            y_climate: Climate Score标签 (n_samples,)
            y_geographic: Geographic Score标签 (n_samples,)
        """
        print(f"🎲 生成合成训练数据: {n_samples} 样本")
        
        # 城市坐标范围 (英国)
        lat_range = (50.0, 60.0)
        lon_range = (-6.0, 2.0)
        
        # 生成随机坐标和月份
        np.random.seed(42)  # 固定种子以确保可重现性
        latitudes = np.random.uniform(lat_range[0], lat_range[1], n_samples)
        longitudes = np.random.uniform(lon_range[0], lon_range[1], n_samples)
        months = np.random.randint(1, 13, n_samples)
        
        X = []
        y_climate = []
        y_geographic = []
        
        for i, (lat, lon, month) in enumerate(zip(latitudes, longitudes, months)):
            if i % 100 == 0:
                print(f"   生成样本 {i+1}/{n_samples}")
            
            try:
                # 生成66特征
                features = self.feature_engineer.prepare_features_for_prediction(lat, lon, month, 66)
                
                # 生成合成标签 (基于特征的简单函数)
                # Climate Score: 基于温度、湿度、降水等气象因素
                climate_features = features[:44]  # 前44个是滞后特征
                climate_score = np.tanh(np.mean(climate_features[:11]) / 100) * 2  # 标准化到[-2, 2]
                
                # Geographic Score: 基于地理位置和土壤因素
                geo_features = features[44:]  # 后22个是变化率特征
                geographic_score = np.tanh(np.mean(geo_features) * 0.5) * 1.5  # 标准化到[-1.5, 1.5]
                
                X.append(features)
                y_climate.append(climate_score)
                y_geographic.append(geographic_score)
                
            except Exception as e:
                print(f"   ⚠️ 跳过样本 {i}: {e}")
                continue
        
        X = np.array(X)
        y_climate = np.array(y_climate)
        y_geographic = np.array(y_geographic)
        
        print(f"✅ 训练数据生成完成:")
        print(f"   特征形状: {X.shape}")
        print(f"   Climate标签范围: [{y_climate.min():.3f}, {y_climate.max():.3f}]")
        print(f"   Geographic标签范围: [{y_geographic.min():.3f}, {y_geographic.max():.3f}]")
        
        return X, y_climate, y_geographic
    
    def train_random_forest(self, X_train: np.ndarray, y_train: np.ndarray, 
                           target_name: str) -> Tuple[Any, Dict]:
        """训练Random Forest模型"""
        print(f"🌲 训练Random Forest模型 - {target_name}")
        
        # RF配置
        rf_config = {
            'n_estimators': 100,
            'max_depth': 20,
            'min_samples_split': 5,
            'min_samples_leaf': 2,
            'random_state': 42,
            'n_jobs': -1
        }
        
        # 训练模型
        model = RandomForestRegressor(**rf_config)
        model.fit(X_train, y_train)
        
        # 特征重要性
        feature_names = self.feature_engineer.get_feature_names()
        feature_importance = dict(zip(feature_names, model.feature_importances_))
        
        # 返回模型和元数据
        metadata = {
            'model_type': 'RandomForest',
            'config': rf_config,
            'feature_importance': feature_importance,
            'n_features': X_train.shape[1],
            'n_samples': X_train.shape[0]
        }
        
        print(f"   ✅ Random Forest训练完成")
        return model, metadata
    
    def train_lstm(self, X_train: np.ndarray, y_train: np.ndarray,
                   X_val: np.ndarray, y_val: np.ndarray, target_name: str) -> Tuple[Any, Dict]:
        """训练LSTM模型"""
        print(f"🧠 训练LSTM模型 - {target_name}")
        
        if not TF_AVAILABLE:
            raise RuntimeError("TensorFlow不可用，无法训练LSTM模型")
        
        # 重塑数据为LSTM格式 (samples, timesteps, features)
        # 将66个特征重组为时间序列：4个时间步 × 16.5个特征/步
        # 为了简化，我们使用 (samples, 66, 1) 格式
        X_train_lstm = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)
        X_val_lstm = X_val.reshape(X_val.shape[0], X_val.shape[1], 1)
        
        # LSTM架构
        model = Sequential([
            LSTM(64, return_sequences=True, input_shape=(66, 1)),
            Dropout(0.2),
            LSTM(32, return_sequences=False),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(1, activation='linear')
        ])
        
        # 编译模型
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        # 回调函数
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
            ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6)
        ]
        
        # 训练模型
        print(f"   训练LSTM...")
        history = model.fit(
            X_train_lstm, y_train,
            validation_data=(X_val_lstm, y_val),
            epochs=50,
            batch_size=32,
            callbacks=callbacks,
            verbose=0
        )
        
        # 元数据
        metadata = {
            'model_type': 'LSTM',
            'architecture': {
                'layers': ['LSTM(64)', 'Dropout(0.2)', 'LSTM(32)', 'Dropout(0.2)', 'Dense(16)', 'Dense(1)'],
                'optimizer': 'Adam(0.001)',
                'loss': 'mse'
            },
            'training_history': {
                'final_loss': float(history.history['loss'][-1]),
                'final_val_loss': float(history.history['val_loss'][-1]),
                'epochs_trained': len(history.history['loss'])
            },
            'n_features': X_train.shape[1],
            'n_samples': X_train.shape[0]
        }
        
        print(f"   ✅ LSTM训练完成，训练了{metadata['training_history']['epochs_trained']}轮")
        return model, metadata
    
    def train_cnn1d(self, X_train: np.ndarray, y_train: np.ndarray,
                    X_val: np.ndarray, y_val: np.ndarray, target_name: str) -> Tuple[Any, Dict]:
        """训练1D CNN模型"""
        print(f"🔍 训练Deep 1D-CNN模型 - {target_name}")
        
        if not TF_AVAILABLE:
            raise RuntimeError("TensorFlow不可用，无法训练CNN模型")
        
        # 重塑数据为CNN格式 (samples, features, channels)
        X_train_cnn = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)
        X_val_cnn = X_val.reshape(X_val.shape[0], X_val.shape[1], 1)
        
        # 1D CNN架构
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
        
        # 编译模型
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        # 回调函数
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
            ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6)
        ]
        
        # 训练模型
        print(f"   训练1D CNN...")
        history = model.fit(
            X_train_cnn, y_train,
            validation_data=(X_val_cnn, y_val),
            epochs=50,
            batch_size=32,
            callbacks=callbacks,
            verbose=0
        )
        
        # 元数据
        metadata = {
            'model_type': '1D-CNN',
            'architecture': {
                'layers': ['Conv1D(64,3)', 'MaxPool1D(2)', 'Conv1D(32,3)', 'MaxPool1D(2)', 
                          'Conv1D(16,3)', 'Flatten', 'Dense(50)', 'Dropout(0.3)', 'Dense(25)', 'Dense(1)'],
                'optimizer': 'Adam(0.001)',
                'loss': 'mse'
            },
            'training_history': {
                'final_loss': float(history.history['loss'][-1]),
                'final_val_loss': float(history.history['val_loss'][-1]),
                'epochs_trained': len(history.history['loss'])
            },
            'n_features': X_train.shape[1],
            'n_samples': X_train.shape[0]
        }
        
        print(f"   ✅ 1D CNN训练完成，训练了{metadata['training_history']['epochs_trained']}轮")
        return model, metadata
    
    def evaluate_model(self, model, X_test: np.ndarray, y_test: np.ndarray,
                      model_type: str, target_name: str) -> Dict:
        """评估模型性能"""
        print(f"📊 评估{model_type}模型性能 - {target_name}")
        
        # 预测
        if model_type in ['LSTM', '1D-CNN']:
            if model_type == 'LSTM':
                X_test_reshaped = X_test.reshape(X_test.shape[0], X_test.shape[1], 1)
            else:  # CNN
                X_test_reshaped = X_test.reshape(X_test.shape[0], X_test.shape[1], 1)
            y_pred = model.predict(X_test_reshaped, verbose=0).flatten()
        else:  # RF
            y_pred = model.predict(X_test)
        
        # 计算指标
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # 额外指标
        mape = np.mean(np.abs((y_test - y_pred) / (y_test + 1e-8))) * 100  # 避免除零
        
        metrics = {
            'MSE': float(mse),
            'RMSE': float(rmse),
            'MAE': float(mae),
            'R2': float(r2),
            'MAPE': float(mape),
            'predictions_range': {
                'min': float(y_pred.min()),
                'max': float(y_pred.max()),
                'mean': float(y_pred.mean()),
                'std': float(y_pred.std())
            },
            'true_range': {
                'min': float(y_test.min()),
                'max': float(y_test.max()),
                'mean': float(y_test.mean()),
                'std': float(y_test.std())
            }
        }
        
        print(f"   RMSE: {rmse:.4f}, R2: {r2:.4f}, MAE: {mae:.4f}")
        return metrics
    
    def save_model(self, model, metadata: Dict, model_type: str, target_name: str):
        """保存模型和元数据"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存模型
        if model_type in ['LSTM', '1D-CNN']:
            model_path = os.path.join(self.output_dir, f"{model_type}_{target_name}_{timestamp}.h5")
            model.save(model_path)
        else:  # RF
            model_path = os.path.join(self.output_dir, f"{model_type}_{target_name}_{timestamp}.joblib")
            joblib.dump(model, model_path)
        
        # 保存元数据
        metadata_path = os.path.join(self.output_dir, f"{model_type}_{target_name}_{timestamp}_metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"   💾 模型已保存: {model_path}")
        return model_path, metadata_path

def main():
    """主训练流程"""
    print("🚀 开始66特征模型训练")
    print("=" * 80)
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 初始化训练器
    trainer = ModelTrainer()
    
    # 生成训练数据
    print(f"\n" + "=" * 60)
    print("📊 准备训练数据")
    print("=" * 60)
    
    X, y_climate, y_geographic = trainer.generate_synthetic_training_data(n_samples=500)
    
    # 数据分割
    X_train, X_test, y_climate_train, y_climate_test = train_test_split(
        X, y_climate, test_size=0.2, random_state=42)
    
    _, _, y_geo_train, y_geo_test = train_test_split(
        X, y_geographic, test_size=0.2, random_state=42)
    
    # 进一步分割训练集以获得验证集
    X_train, X_val, y_climate_train, y_climate_val = train_test_split(
        X_train, y_climate_train, test_size=0.2, random_state=42)
    
    _, _, y_geo_train, y_geo_val = train_test_split(
        X_train, y_geo_train, test_size=0.2, random_state=42)
    
    print(f"训练集: {X_train.shape[0]} 样本")
    print(f"验证集: {X_val.shape[0]} 样本") 
    print(f"测试集: {X_test.shape[0]} 样本")
    
    # 标准化特征 (仅对深度学习模型)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    # 保存scaler
    scaler_path = os.path.join(trainer.output_dir, "feature_scaler.joblib")
    joblib.dump(scaler, scaler_path)
    print(f"特征标准化器已保存: {scaler_path}")
    
    # 训练结果存储
    training_results = {}
    
    # 要训练的目标
    targets = {
        'climate': (y_climate_train, y_climate_val, y_climate_test),
        'geographic': (y_geo_train, y_geo_val, y_geo_test)
    }
    
    for target_name, (y_train, y_val, y_test) in targets.items():
        print(f"\n" + "=" * 60)
        print(f"🎯 训练{target_name.upper()}模型")
        print("=" * 60)
        
        target_results = {}
        
        # 1. 训练Random Forest
        print(f"\n1️⃣ Random Forest - {target_name}")
        print("-" * 40)
        try:
            rf_model, rf_metadata = trainer.train_random_forest(X_train, y_train, target_name)
            rf_metrics = trainer.evaluate_model(rf_model, X_test, y_test, 'RandomForest', target_name)
            rf_model_path, rf_meta_path = trainer.save_model(rf_model, {**rf_metadata, 'metrics': rf_metrics}, 
                                                           'RandomForest', target_name)
            
            target_results['RandomForest'] = {
                'model_path': rf_model_path,
                'metadata_path': rf_meta_path,
                'metrics': rf_metrics,
                'metadata': rf_metadata
            }
            print(f"✅ Random Forest完成")
            
        except Exception as e:
            print(f"❌ Random Forest失败: {e}")
            target_results['RandomForest'] = {'error': str(e)}
        
        # 2. 训练LSTM
        print(f"\n2️⃣ LSTM - {target_name}")
        print("-" * 40)
        try:
            if TF_AVAILABLE:
                lstm_model, lstm_metadata = trainer.train_lstm(X_train_scaled, y_train, 
                                                             X_val_scaled, y_val, target_name)
                lstm_metrics = trainer.evaluate_model(lstm_model, X_test_scaled, y_test, 'LSTM', target_name)
                lstm_model_path, lstm_meta_path = trainer.save_model(lstm_model, 
                                                                   {**lstm_metadata, 'metrics': lstm_metrics}, 
                                                                   'LSTM', target_name)
                
                target_results['LSTM'] = {
                    'model_path': lstm_model_path,
                    'metadata_path': lstm_meta_path,
                    'metrics': lstm_metrics,
                    'metadata': lstm_metadata
                }
                print(f"✅ LSTM完成")
            else:
                print(f"⚠️ TensorFlow不可用，跳过LSTM")
                target_results['LSTM'] = {'error': 'TensorFlow not available'}
                
        except Exception as e:
            print(f"❌ LSTM失败: {e}")
            target_results['LSTM'] = {'error': str(e)}
        
        # 3. 训练1D CNN
        print(f"\n3️⃣ Deep 1D-CNN - {target_name}")
        print("-" * 40)
        try:
            if TF_AVAILABLE:
                cnn_model, cnn_metadata = trainer.train_cnn1d(X_train_scaled, y_train,
                                                            X_val_scaled, y_val, target_name)
                cnn_metrics = trainer.evaluate_model(cnn_model, X_test_scaled, y_test, '1D-CNN', target_name)
                cnn_model_path, cnn_meta_path = trainer.save_model(cnn_model,
                                                                 {**cnn_metadata, 'metrics': cnn_metrics},
                                                                 '1D-CNN', target_name)
                
                target_results['1D-CNN'] = {
                    'model_path': cnn_model_path,
                    'metadata_path': cnn_meta_path,
                    'metrics': cnn_metrics,
                    'metadata': cnn_metadata
                }
                print(f"✅ 1D-CNN完成")
            else:
                print(f"⚠️ TensorFlow不可用，跳过1D-CNN")
                target_results['1D-CNN'] = {'error': 'TensorFlow not available'}
                
        except Exception as e:
            print(f"❌ 1D-CNN失败: {e}")
            target_results['1D-CNN'] = {'error': str(e)}
        
        training_results[target_name] = target_results
    
    # 保存完整的训练结果
    results_path = os.path.join(trainer.output_dir, f"training_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(training_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n" + "=" * 80)
    print("🎉 模型训练完成!")
    print("=" * 80)
    print(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📄 完整结果已保存: {results_path}")
    
    return training_results

if __name__ == "__main__":
    results = main() 