#!/usr/bin/env python3
"""
多时间尺度融合建模示例
将月度数据分解为：1)长期趋势 2)季节性模式
最终预测 = 趋势预测 + 季节性调整
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.pyplot as plt
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class MultiTimescaleModel:
    def __init__(self):
        self.trend_model = LinearRegression()  # 长期趋势模型
        self.seasonal_patterns = {}  # 季节性模式 {month: offset}
        self.baseline_temp = 0  # 基准温度
        
    def prepare_data(self, monthly_data):
        """
        准备训练数据：分离年度趋势和季节性模式
        
        Args:
            monthly_data: DataFrame with columns ['year', 'month', 'temperature']
        """
        # 1. 计算每年的年平均温度
        annual_temps = monthly_data.groupby('year')['temperature'].mean().reset_index()
        annual_temps['year_index'] = annual_temps['year'] - annual_temps['year'].min()
        
        # 2. 计算每个月相对于当年年均的偏移量
        monthly_data = monthly_data.merge(annual_temps[['year', 'temperature']], 
                                        on='year', suffixes=('', '_annual'))
        monthly_data['seasonal_offset'] = monthly_data['temperature'] - monthly_data['temperature_annual']
        
        return annual_temps, monthly_data
    
    def train(self, monthly_data):
        """
        训练双模型系统
        
        Args:
            monthly_data: DataFrame with columns ['year', 'month', 'temperature']
        """
        print("🔄 开始训练多时间尺度模型...")
        
        # 准备数据
        annual_temps, monthly_with_offset = self.prepare_data(monthly_data)
        
        # 训练长期趋势模型
        X_trend = annual_temps[['year_index']].values
        y_trend = annual_temps['temperature'].values
        self.trend_model.fit(X_trend, y_trend)
        
        # 计算季节性模式（每个月的平均偏移量）
        seasonal_stats = monthly_with_offset.groupby('month')['seasonal_offset'].agg(['mean', 'std'])
        for month in range(1, 13):
            if month in seasonal_stats.index:
                self.seasonal_patterns[month] = seasonal_stats.loc[month, 'mean']
            else:
                self.seasonal_patterns[month] = 0  # 如果某个月没有数据，偏移为0
        
        # 记录基准信息
        self.baseline_temp = annual_temps['temperature'].mean()
        self.base_year = annual_temps['year'].min()
        
        # 计算模型性能
        self._evaluate_model(annual_temps, monthly_with_offset)
        
    def _evaluate_model(self, annual_temps, monthly_with_offset):
        """评估模型性能"""
        # 趋势模型性能
        trend_pred = self.trend_model.predict(annual_temps[['year_index']].values)
        trend_r2 = r2_score(annual_temps['temperature'].values, trend_pred)
        
        # 组合模型性能
        monthly_pred = []
        monthly_actual = []
        
        for _, row in monthly_with_offset.iterrows():
            year_index = row['year'] - self.base_year
            trend_temp = self.trend_model.predict([[year_index]])[0]
            seasonal_offset = self.seasonal_patterns.get(row['month'], 0)
            final_pred = trend_temp + seasonal_offset
            
            monthly_pred.append(final_pred)
            monthly_actual.append(row['temperature'])
        
        combined_r2 = r2_score(monthly_actual, monthly_pred)
        
        print(f"📊 模型性能评估:")
        print(f"   长期趋势模型 R² = {trend_r2:.4f}")
        print(f"   组合模型 R² = {combined_r2:.4f}")
        print(f"   年温度变化趋势: {self.trend_model.coef_[0]:.4f}°C/年")
        
    def predict(self, target_year, target_month=None):
        """
        预测未来时间点的温度
        
        Args:
            target_year: 目标年份
            target_month: 目标月份 (1-12)，如果为None则返回年平均温度
            
        Returns:
            预测温度
        """
        # 计算年份索引
        year_index = target_year - self.base_year
        
        # 预测年平均温度
        annual_temp = self.trend_model.predict([[year_index]])[0]
        
        if target_month is None:
            return annual_temp
        
        # 添加季节性偏移
        seasonal_offset = self.seasonal_patterns.get(target_month, 0)
        final_temp = annual_temp + seasonal_offset
        
        return final_temp
    
    def predict_multiple(self, predictions_list):
        """
        批量预测
        
        Args:
            predictions_list: [(year, month), ...] 或 [(year, None), ...]
            
        Returns:
            预测结果列表
        """
        results = []
        for year, month in predictions_list:
            pred_temp = self.predict(year, month)
            results.append({
                'year': year,
                'month': month,
                'predicted_temperature': pred_temp,
                'prediction_type': 'monthly' if month else 'annual'
            })
        return results
    
    def get_seasonal_pattern(self):
        """返回季节性模式"""
        return self.seasonal_patterns
    
    def get_trend_info(self):
        """返回趋势信息"""
        return {
            'annual_warming_rate': self.trend_model.coef_[0],
            'baseline_year': self.base_year,
            'baseline_temp': self.baseline_temp
        }

def demo_multi_timescale_model():
    """演示多时间尺度模型"""
    print("🌡️  多时间尺度温度预测模型演示")
    print("=" * 50)
    
    # 创建模拟数据 (基于实际温度特征)
    np.random.seed(42)
    years = range(1991, 2021)  # 30年数据
    months = range(1, 13)
    
    # 模拟数据：长期趋势 + 季节性 + 噪声
    data = []
    base_temp = 10  # 基准温度
    warming_rate = 0.03  # 每年升温0.03°C
    
    # 季节性模式 (各月份相对年均的偏移)
    seasonal_pattern = {
        1: -3.5, 2: -2.8, 3: -0.5, 4: 2.1, 5: 5.8, 6: 8.1,
        7: 9.2, 8: 8.9, 9: 6.1, 10: 3.2, 11: 0.1, 12: -2.1
    }
    
    for year in years:
        year_trend = base_temp + warming_rate * (year - 1991)
        for month in months:
            seasonal_offset = seasonal_pattern[month]
            noise = np.random.normal(0, 0.5)  # 随机噪声
            temp = year_trend + seasonal_offset + noise
            data.append({
                'year': year,
                'month': month,
                'temperature': temp
            })
    
    df = pd.DataFrame(data)
    
    # 训练模型
    model = MultiTimescaleModel()
    model.train(df)
    
    print(f"\n📈 模型学习到的趋势信息:")
    trend_info = model.get_trend_info()
    print(f"   年升温率: {trend_info['annual_warming_rate']:.4f}°C/年")
    print(f"   基准年份: {trend_info['baseline_year']}")
    print(f"   基准温度: {trend_info['baseline_temp']:.2f}°C")
    
    print(f"\n🔄 季节性模式 (相对年均偏移):")
    seasonal = model.get_seasonal_pattern()
    month_names = ['', '1月', '2月', '3月', '4月', '5月', '6月', 
                   '7月', '8月', '9月', '10月', '11月', '12月']
    for month, offset in seasonal.items():
        print(f"   {month_names[month]}: {offset:+.2f}°C")
    
    # 预测示例
    print(f"\n🔮 预测示例:")
    predictions = [
        (2025, None),  # 2025年年平均
        (2025, 7),     # 2025年7月
        (2035, 1),     # 2035年1月
        (2050, 7),     # 2050年7月
        (2075, None),  # 2075年年平均
    ]
    
    results = model.predict_multiple(predictions)
    
    for result in results:
        year = result['year']
        month = result['month']
        temp = result['predicted_temperature']
        pred_type = result['prediction_type']
        
        if pred_type == 'annual':
            print(f"   {year}年年平均: {temp:.2f}°C")
        else:
            month_name = month_names[month]
            print(f"   {year}年{month_name}: {temp:.2f}°C")
    
    print(f"\n✨ 这就是多时间尺度融合建模的核心思想！")

if __name__ == "__main__":
    demo_multi_timescale_model() 