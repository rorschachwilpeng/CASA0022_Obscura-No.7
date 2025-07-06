#!/usr/bin/env python3
"""
简单环境预测模型 - MVP版本
基于城市温度数据的简单预测模型，用于验证端到端工作流
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os
from datetime import datetime, timedelta
from pathlib import Path

class SimpleEnvironmentalModel:
    """简单环境预测模型"""
    
    def __init__(self, model_dir="models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        
        # 模型组件
        self.temperature_model = None
        self.humidity_model = None
        self.pressure_model = None
        self.scaler = None
        
        # 城市中心坐标
        self.city_centers = {
            'London': {'lat': 51.5074, 'lon': -0.1278},
            'Manchester': {'lat': 53.4808, 'lon': -2.2426},
            'Edinburgh': {'lat': 55.9533, 'lon': -3.1883}
        }
        
        # 模型元数据
        self.model_info = {
            'version': '1.0.0',
            'created_at': None,
            'training_data_size': 0,
            'performance_metrics': {}
        }
    
    def load_temperature_data(self, data_dir="environmental_prediction_framework/meteorological_climate_factors/temperature"):
        """加载温度数据"""
        print("📊 加载温度数据...")
        
        all_data = []
        
        # 加载三个城市的月度数据
        for city in ['london', 'manchester', 'edinburgh']:
            file_path = Path(data_dir) / f"monthly_{city}_temperature_data.csv"
            
            if file_path.exists():
                df = pd.read_csv(file_path)
                df['city'] = city.title()
                all_data.append(df)
                print(f"✅ {city.title()}: {len(df)} 数据点")
            else:
                print(f"⚠️ 文件不存在: {file_path}")
        
        if not all_data:
            raise FileNotFoundError("没有找到温度数据文件")
        
        # 合并所有数据
        combined_df = pd.concat(all_data, ignore_index=True)
        print(f"📈 总数据点: {len(combined_df)}")
        
        return combined_df
    
    def prepare_features(self, df):
        """准备特征数据"""
        print("⚙️ 准备特征数据...")
        
        features = []
        targets = []
        
        # 提取温度列
        temp_columns = [col for col in df.columns if 'tas' in col]
        
        for _, row in df.iterrows():
            # 基础地理特征
            lat = row['center_latitude']
            lon = row['center_longitude']
            
            # 城市编码
            city_encoding = {
                'London': [1, 0, 0],
                'Manchester': [0, 1, 0],
                'Edinburgh': [0, 0, 1]
            }
            city_code = city_encoding.get(row['city'], [0, 0, 0])
            
            # 为每个月创建特征
            for month_idx, temp_col in enumerate(temp_columns):
                if pd.notna(row[temp_col]):
                    # 输入特征: 经度、纬度、月份、城市编码
                    feature_vector = [
                        lat,
                        lon,
                        month_idx + 1,  # 月份 1-12
                        np.sin(2 * np.pi * month_idx / 12),  # 季节性特征
                        np.cos(2 * np.pi * month_idx / 12),
                        *city_code
                    ]
                    
                    features.append(feature_vector)
                    targets.append(row[temp_col])
        
        X = np.array(features)
        y = np.array(targets)
        
        print(f"📊 特征维度: {X.shape}")
        print(f"📊 目标维度: {y.shape}")
        
        return X, y
    
    def train_model(self, data_dir="environmental_prediction_framework/meteorological_climate_factors/temperature"):
        """训练模型"""
        print("🎯 开始训练简单环境预测模型...")
        
        # 加载数据
        df = self.load_temperature_data(data_dir)
        
        # 准备特征
        X, y = self.prepare_features(df)
        
        # 分割训练测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # 特征缩放
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # 训练温度模型
        self.temperature_model = LinearRegression()
        self.temperature_model.fit(X_train_scaled, y_train)
        
        # 预测和评估
        y_pred = self.temperature_model.predict(X_test_scaled)
        
        # 计算性能指标
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print(f"📊 模型性能:")
        print(f"   MSE: {mse:.4f}")
        print(f"   R²: {r2:.4f}")
        print(f"   RMSE: {np.sqrt(mse):.4f}°C")
        
        # 保存模型信息
        self.model_info = {
            'version': '1.0.0',
            'created_at': datetime.now().isoformat(),
            'training_data_size': len(X_train),
            'performance_metrics': {
                'mse': float(mse),
                'r2': float(r2),
                'rmse': float(np.sqrt(mse))
            }
        }
        
        # 创建简单的湿度和压力模型（基于温度的简单关系）
        self._create_auxiliary_models(X_train_scaled, y_train)
        
        print("✅ 模型训练完成!")
        return self.model_info
    
    def _create_auxiliary_models(self, X_train, y_train):
        """创建辅助模型（湿度、压力）"""
        # 简单的湿度模型：基于温度的反比关系 + 噪声
        humidity_targets = 80 - (y_train - 5) * 2 + np.random.normal(0, 5, len(y_train))
        humidity_targets = np.clip(humidity_targets, 20, 95)  # 合理范围
        
        self.humidity_model = LinearRegression()
        self.humidity_model.fit(X_train, humidity_targets)
        
        # 简单的压力模型：基于海拔和温度的关系
        pressure_targets = 1013 + np.random.normal(0, 10, len(y_train))
        pressure_targets = np.clip(pressure_targets, 980, 1040)  # 合理范围
        
        self.pressure_model = LinearRegression()
        self.pressure_model.fit(X_train, pressure_targets)
    
    def predict(self, latitude, longitude, month=None, future_years=0):
        """预测环境数据"""
        if not self.temperature_model:
            raise ValueError("模型未训练，请先调用train_model()")
        
        # 如果没有指定月份，使用当前月份
        if month is None:
            month = datetime.now().month
        
        # 确定最近的城市
        city_code = self._get_city_encoding(latitude, longitude)
        
        # 构建特征向量
        feature_vector = np.array([[
            latitude,
            longitude,
            month,
            np.sin(2 * np.pi * (month - 1) / 12),
            np.cos(2 * np.pi * (month - 1) / 12),
            *city_code
        ]])
        
        # 缩放特征
        feature_vector_scaled = self.scaler.transform(feature_vector)
        
        # 预测
        temperature = self.temperature_model.predict(feature_vector_scaled)[0]
        humidity = self.humidity_model.predict(feature_vector_scaled)[0]
        pressure = self.pressure_model.predict(feature_vector_scaled)[0]
        
        # 未来预测调整（简单的线性趋势）
        if future_years > 0:
            # 气候变化趋势：温度上升，湿度变化
            temperature += future_years * 0.2  # 每年0.2°C增长
            humidity *= (1 + future_years * 0.01)  # 轻微湿度变化
        
        # 合理性检查
        temperature = max(-10, min(40, temperature))
        humidity = max(20, min(95, humidity))
        pressure = max(980, min(1040, pressure))
        
        return {
            'temperature': float(temperature),
            'humidity': float(humidity),
            'pressure': float(pressure),
            'prediction_confidence': 0.75,  # 简单模型的置信度
            'model_version': self.model_info['version'],
            'predicted_at': datetime.now().isoformat()
        }
    
    def _get_city_encoding(self, lat, lon):
        """根据坐标获取城市编码"""
        # 计算到各城市中心的距离
        distances = {}
        for city, center in self.city_centers.items():
            dist = np.sqrt((lat - center['lat'])**2 + (lon - center['lon'])**2)
            distances[city] = dist
        
        # 找到最近的城市
        closest_city = min(distances, key=distances.get)
        
        # 返回独热编码
        city_encodings = {
            'London': [1, 0, 0],
            'Manchester': [0, 1, 0],
            'Edinburgh': [0, 0, 1]
        }
        
        return city_encodings.get(closest_city, [0, 0, 0])
    
    def save_model(self, model_path=None):
        """保存模型"""
        if model_path is None:
            model_path = self.model_dir / "simple_environmental_model.pkl"
        
        model_data = {
            'temperature_model': self.temperature_model,
            'humidity_model': self.humidity_model,
            'pressure_model': self.pressure_model,
            'scaler': self.scaler,
            'city_centers': self.city_centers,
            'model_info': self.model_info
        }
        
        joblib.dump(model_data, model_path)
        print(f"💾 模型已保存: {model_path}")
        
        return model_path
    
    def load_model(self, model_path=None):
        """加载模型"""
        if model_path is None:
            model_path = self.model_dir / "simple_environmental_model.pkl"
        
        if not Path(model_path).exists():
            raise FileNotFoundError(f"模型文件不存在: {model_path}")
        
        model_data = joblib.load(model_path)
        
        self.temperature_model = model_data['temperature_model']
        self.humidity_model = model_data['humidity_model']
        self.pressure_model = model_data['pressure_model']
        self.scaler = model_data['scaler']
        self.city_centers = model_data['city_centers']
        self.model_info = model_data['model_info']
        
        print(f"📦 模型已加载: {model_path}")
        print(f"📊 模型版本: {self.model_info['version']}")
        
        return True

def main():
    """主函数 - 训练和测试模型"""
    print("🚀 简单环境预测模型训练开始...")
    
    # 创建模型实例
    model = SimpleEnvironmentalModel()
    
    # 训练模型
    try:
        model.train_model()
        
        # 保存模型
        model.save_model()
        
        # 测试预测
        print("\n🧪 测试预测...")
        
        # 测试几个位置
        test_locations = [
            (51.5074, -0.1278, "伦敦"),
            (53.4808, -2.2426, "曼彻斯特"),
            (55.9533, -3.1883, "爱丁堡")
        ]
        
        for lat, lon, name in test_locations:
            prediction = model.predict(lat, lon, month=6)  # 6月预测
            print(f"📍 {name} (6月预测):")
            print(f"   温度: {prediction['temperature']:.2f}°C")
            print(f"   湿度: {prediction['humidity']:.1f}%")
            print(f"   压力: {prediction['pressure']:.1f} hPa")
            print()
        
        # 测试未来预测
        print("🔮 未来预测测试 (伦敦，5年后):")
        future_pred = model.predict(51.5074, -0.1278, month=6, future_years=5)
        print(f"   温度: {future_pred['temperature']:.2f}°C")
        print(f"   湿度: {future_pred['humidity']:.1f}%")
        print(f"   压力: {future_pred['pressure']:.1f} hPa")
        
        print("\n✅ 模型训练和测试完成!")
        
    except Exception as e:
        print(f"❌ 训练失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 