#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenWeatherMap Statistical Data Collector for London
获取伦敦地区的历史统计气象数据
"""

import requests
import json
import pandas as pd
from datetime import datetime
import time
import os

class OpenWeatherStatCollector:
    def __init__(self, api_key):
        """
        初始化OpenWeatherMap统计数据收集器
        
        Args:
            api_key (str): OpenWeatherMap API密钥
        """
        self.api_key = api_key
        self.base_url = "https://history.openweathermap.org/data/2.5/aggregated"
        self.location = "London,GB"
        self.london_coords = {"lat": 51.5074, "lon": -0.1278}
        
    def test_api_connection(self):
        """测试API连接是否正常"""
        print("🔍 测试OpenWeatherMap统计API连接...")
        
        # 测试获取单日统计数据
        url = f"{self.base_url}/day"
        params = {
            'q': self.location,
            'month': 6,  # 6月
            'day': 1,    # 1号
            'appid': self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ API连接成功！")
                print(f"📊 返回数据示例: {json.dumps(data, indent=2)[:500]}...")
                return True
            else:
                print(f"❌ API请求失败: {response.status_code}")
                print(f"   错误信息: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 连接错误: {e}")
            return False
    
    def get_yearly_statistics(self):
        """获取全年365天的统计数据"""
        print("📅 获取伦敦全年气象统计数据...")
        
        url = f"{self.base_url}/year"
        params = {
            'q': self.location,
            'appid': self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 成功获取{len(data['result'])}天的统计数据")
                return data
            else:
                print(f"❌ 获取年度数据失败: {response.status_code}")
                print(f"   错误信息: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return None
    
    def get_monthly_statistics(self, month):
        """
        获取指定月份的统计数据
        
        Args:
            month (int): 月份 (1-12)
        """
        print(f"📊 获取{month}月份统计数据...")
        
        url = f"{self.base_url}/month"
        params = {
            'q': self.location,
            'month': month,
            'appid': self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 成功获取{month}月份数据")
                return data
            else:
                print(f"❌ 获取{month}月份数据失败: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return None
    
    def process_weather_data(self, raw_data):
        """
        处理原始气象数据，转换为DataFrame格式
        
        Args:
            raw_data (dict): API返回的原始数据
        """
        if not raw_data or 'result' not in raw_data:
            return None
        
        processed_data = []
        
        for day_data in raw_data['result']:
            day_record = {
                'month': day_data['month'],
                'day': day_data['day'],
                'date': f"{day_data['month']:02d}-{day_data['day']:02d}",
            }
            
            # 温度数据
            if 'temp' in day_data:
                temp_data = day_data['temp']
                day_record.update({
                    'temp_mean': temp_data.get('mean'),
                    'temp_min': temp_data.get('average_min'),
                    'temp_max': temp_data.get('average_max'),
                    'temp_record_min': temp_data.get('record_min'),
                    'temp_record_max': temp_data.get('record_max'),
                    'temp_std': temp_data.get('st_dev'),
                })
            
            # 湿度数据
            if 'humidity' in day_data:
                humidity_data = day_data['humidity']
                day_record.update({
                    'humidity_mean': humidity_data.get('mean'),
                    'humidity_min': humidity_data.get('min'),
                    'humidity_max': humidity_data.get('max'),
                    'humidity_std': humidity_data.get('st_dev'),
                })
            
            # 气压数据
            if 'pressure' in day_data:
                pressure_data = day_data['pressure']
                day_record.update({
                    'pressure_mean': pressure_data.get('mean'),
                    'pressure_min': pressure_data.get('min'),
                    'pressure_max': pressure_data.get('max'),
                    'pressure_std': pressure_data.get('st_dev'),
                })
            
            # 风速数据
            if 'wind' in day_data:
                wind_data = day_data['wind']
                day_record.update({
                    'wind_mean': wind_data.get('mean'),
                    'wind_min': wind_data.get('min'),
                    'wind_max': wind_data.get('max'),
                    'wind_std': wind_data.get('st_dev'),
                })
            
            # 降水数据
            if 'precipitation' in day_data:
                precip_data = day_data['precipitation']
                day_record.update({
                    'precipitation_mean': precip_data.get('mean'),
                    'precipitation_min': precip_data.get('min'),
                    'precipitation_max': precip_data.get('max'),
                    'precipitation_std': precip_data.get('st_dev'),
                })
            
            # 云量数据
            if 'clouds' in day_data:
                clouds_data = day_data['clouds']
                day_record.update({
                    'clouds_mean': clouds_data.get('mean'),
                    'clouds_min': clouds_data.get('min'),
                    'clouds_max': clouds_data.get('max'),
                    'clouds_std': clouds_data.get('st_dev'),
                })
            
            processed_data.append(day_record)
        
        return pd.DataFrame(processed_data)
    
    def save_data(self, data, filename=None):
        """保存数据到文件"""
        if data is None or data.empty:
            print("❌ 没有数据可保存")
            return False
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"london_weather_stats_{timestamp}.csv"
        
        # 确保目录存在
        os.makedirs('outputs', exist_ok=True)
        filepath = os.path.join('outputs', filename)
        
        try:
            data.to_csv(filepath, index=False)
            print(f"✅ 数据已保存到: {filepath}")
            print(f"📊 数据维度: {data.shape[0]} 行 x {data.shape[1]} 列")
            return True
        except Exception as e:
            print(f"❌ 保存失败: {e}")
            return False
    
    def run_full_collection(self):
        """运行完整的数据收集流程"""
        print("🚀 开始伦敦气象数据收集流程")
        print("=" * 60)
        
        # 1. 测试API连接
        if not self.test_api_connection():
            print("❌ API连接失败，终止数据收集")
            return False
        
        print("\n" + "=" * 60)
        
        # 2. 获取年度统计数据
        yearly_data = self.get_yearly_statistics()
        if yearly_data is None:
            print("❌ 无法获取年度数据")
            return False
        
        # 3. 处理数据
        print("\n🔄 处理数据格式...")
        df = self.process_weather_data(yearly_data)
        
        if df is not None:
            print("✅ 数据处理完成")
            print(f"📊 处理后数据维度: {df.shape}")
            print("\n📋 数据预览:")
            print(df.head())
            print(f"\n📈 数据列名: {list(df.columns)}")
            
            # 4. 保存数据
            self.save_data(df)
            
            # 5. 基本统计信息
            print("\n" + "=" * 60)
            print("📊 数据统计摘要:")
            if 'temp_mean' in df.columns:
                print(f"   温度范围: {df['temp_mean'].min():.2f}K - {df['temp_mean'].max():.2f}K")
            if 'humidity_mean' in df.columns:
                print(f"   湿度范围: {df['humidity_mean'].min():.1f}% - {df['humidity_mean'].max():.1f}%")
            if 'pressure_mean' in df.columns:
                print(f"   气压范围: {df['pressure_mean'].min():.1f}hPa - {df['pressure_mean'].max():.1f}hPa")
            
            return True
        else:
            print("❌ 数据处理失败")
            return False

def main():
    """主函数"""
    # API密钥
    API_KEY = "9a5b95af3b09cae239fea38a996a8094"
    
    # 创建数据收集器
    collector = OpenWeatherStatCollector(API_KEY)
    
    # 运行数据收集
    success = collector.run_full_collection()
    
    if success:
        print("\n🎉 数据收集完成！")
    else:
        print("\n😞 数据收集失败")

if __name__ == "__main__":
    main()
