#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Geographic模型训练器
使用LSTM训练Geographic预测模型
"""

import os
import pickle
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
import logging
from typing import Dict, Any, Tuple
from tqdm import tqdm

# TensorFlow/Keras imports
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam

from .training_config import TrainingConfig

class GeographicTrainer:
    """Geographic模型训练器"""
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.model = None
        self.scaler = StandardScaler()
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def load_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """加载训练数据"""
        self.logger.info(f"📊 加载训练数据: {self.config.data_cache_path}")
        
        try:
            with open(self.config.data_cache_path, 'rb') as f:
                data = pickle.load(f)
            
            X = data['X']
            y_geographic = data['y_geographic']
            
            self.logger.info(f"✅ 数据加载成功: X={X.shape}, y_geographic={y_geographic.shape}")
            return X, y_geographic
            
        except Exception as e:
            self.logger.error(f"❌ 数据加载失败: {e}")
            raise
    
    def prepare_data(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """准备训练数据"""
        self.logger.info("🔧 准备训练数据...")
        
        # 数据分割
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=self.config.test_size, random_state=self.config.random_state
        )
        
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=self.config.val_size/(1-self.config.test_size), 
            random_state=self.config.random_state
        )
        
        # 特征标准化
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        X_test_scaled = self.scaler.transform(X_test)
        
        # 重塑数据为LSTM格式 (samples, timesteps, features)
        # 对于LSTM，我们将每个样本作为一个时间步
        X_train_reshaped = X_train_scaled.reshape(X_train_scaled.shape[0], 1, X_train_scaled.shape[1])
        X_val_reshaped = X_val_scaled.reshape(X_val_scaled.shape[0], 1, X_val_scaled.shape[1])
        X_test_reshaped = X_test_scaled.reshape(X_test_scaled.shape[0], 1, X_test_scaled.shape[1])
        
        self.logger.info(f"✅ 数据准备完成:")
        self.logger.info(f"   训练集: {X_train_reshaped.shape}")
        self.logger.info(f"   验证集: {X_val_reshaped.shape}")
        self.logger.info(f"   测试集: {X_test_reshaped.shape}")
        
        return X_train_reshaped, X_val_reshaped, X_test_reshaped, y_train, y_val, y_test
    
    def build_model(self, input_shape: Tuple[int, int]) -> Sequential:
        """构建LSTM模型"""
        self.logger.info("🏗️ 构建LSTM Geographic模型...")
        
        model = Sequential([
            LSTM(
                units=self.config.geographic_model_params['units'],
                dropout=self.config.geographic_model_params['dropout'],
                recurrent_dropout=self.config.geographic_model_params['recurrent_dropout'],
                return_sequences=self.config.geographic_model_params['return_sequences'],
                input_shape=input_shape
            ),
            Dense(32, activation='relu'),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(1, activation='linear')
        ])
        
        # 编译模型
        model.compile(
            optimizer=Adam(learning_rate=self.config.learning_rate),
            loss='mse',
            metrics=['mae']
        )
        
        self.logger.info("✅ LSTM模型构建完成")
        return model
    
    def train_model(self, X_train: np.ndarray, y_train: np.ndarray, 
                   X_val: np.ndarray, y_val: np.ndarray) -> Sequential:
        """训练LSTM模型"""
        self.logger.info("🧠 开始训练LSTM Geographic模型...")
        
        # 构建模型
        self.model = self.build_model((X_train.shape[1], X_train.shape[2]))
        
        # 设置回调函数
        callbacks = [
            EarlyStopping(
                monitor='val_loss',
                patience=self.config.early_stopping_patience,
                restore_best_weights=True,
                verbose=1
            ),
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-7,
                verbose=1
            )
        ]
        
        # 训练模型
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=self.config.max_epochs,
            batch_size=self.config.batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        self.logger.info("✅ Geographic模型训练完成")
        return self.model
    
    def evaluate_model(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """评估模型性能"""
        self.logger.info("📊 评估Geographic模型性能...")
        
        if self.model is None:
            raise ValueError("模型未训练，请先调用train_model方法")
        
        # 预测
        y_pred = self.model.predict(X_test).flatten()
        
        # 计算指标
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mse)
        
        metrics = {
            'mse': mse,
            'mae': mae,
            'r2': r2,
            'rmse': rmse
        }
        
        self.logger.info("📈 Geographic模型性能指标:")
        for metric, value in metrics.items():
            self.logger.info(f"   {metric}: {value:.4f}")
        
        return metrics
    
    def save_model(self, model_path: str, scaler_path: str):
        """保存模型和缩放器"""
        self.logger.info(f"💾 保存Geographic模型到: {model_path}")
        
        # 创建输出目录
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # 保存模型
        self.model.save(model_path)
        
        # 保存缩放器
        joblib.dump(self.scaler, scaler_path)
        
        self.logger.info("✅ Geographic模型保存完成")
    
    def train_and_evaluate(self) -> Dict[str, Any]:
        """完整的训练和评估流程"""
        self.logger.info("🚀 开始Geographic模型训练流程...")
        
        try:
            # 1. 加载数据
            X, y = self.load_data()
            
            # 2. 准备数据
            X_train, X_val, X_test, y_train, y_val, y_test = self.prepare_data(X, y)
            
            # 3. 训练模型
            self.train_model(X_train, y_train, X_val, y_val)
            
            # 4. 评估模型
            metrics = self.evaluate_model(X_test, y_test)
            
            # 5. 保存模型
            model_paths = self.config.get_model_paths()
            self.save_model(model_paths['geographic_model'], model_paths['feature_scaler'])
            
            # 6. 返回结果
            result = {
                'model_type': 'LSTM',
                'target': 'geographic',
                'metrics': metrics,
                'model_path': model_paths['geographic_model'],
                'scaler_path': model_paths['feature_scaler']
            }
            
            self.logger.info("🎉 Geographic模型训练流程完成!")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Geographic模型训练失败: {e}")
            raise 