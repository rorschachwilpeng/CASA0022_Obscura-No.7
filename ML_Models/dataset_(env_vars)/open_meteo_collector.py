#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Open-Meteo API 历史气象数据收集器
获取伦敦过去3年的平均温度和降水量数据
"""

import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from datetime import datetime, timedelta
import os

class OpenMeteoCollector:
    def __init__(self):
        """初始化Open-Meteo数据收集器"""
        
        # 伦敦坐标
        self.latitude = 51.5085
        self.longitude = -0.1257
        self.location_name = "London, UK"
        
        # 设置API客户端（带缓存和重试机制）
        print("🔧 初始化Open-Meteo API客户端...")
        cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        self.openmeteo = openmeteo_requests.Client(session=retry_session)
        
        # API URL
        self.url = "https://archive-api.open-meteo.com/v1/archive"
        
        print(f"📍 目标位置: {self.location_name}")
        print(f"📐 坐标: {self.latitude}°N, {self.longitude}°E")
        
    def calculate_date_range(self, years=3):
        """计算过去N年的日期范围"""
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=years*365)
        
        print(f"📅 数据时间范围: {start_date} 至 {end_date}")
        print(f"⏱️ 总天数: {(end_date - start_date).days} 天")
        
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
    
    def collect_weather_data(self, years=3):
        """收集历史气象数据"""
        
        print("🌤️ 开始收集历史气象数据...")
        print("=" * 60)
        
        # 计算日期范围
        start_date, end_date = self.calculate_date_range(years)
        
        # API参数设置
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "start_date": start_date,
            "end_date": end_date,
            "daily": [
                "temperature_2m_mean",      # 日平均温度
                "precipitation_sum",        # 日降水量总和
                "temperature_2m_max",       # 日最高温度
                "temperature_2m_min",       # 日最低温度
                "relative_humidity_2m_mean", # 日平均湿度
                "wind_speed_10m_max",       # 日最大风速
                "sunshine_duration",        # 日照时长
                "soil_temperature_0_to_7cm",    # 表层土壤温度 (城市热岛)
                "soil_temperature_28_to_100cm", # 深层土壤温度 (水文稳定)
                "soil_temperature_7_to_28cm",   # 根系层土壤温度 (生态健康)
                "soil_moisture_0_to_7cm",       # 表层土壤湿度 (径流风险)
                "soil_moisture_28_to_100cm",    # 深层土壤湿度 (地下水位)
                "soil_moisture_7_to_28cm"       # 根系层土壤湿度 (生态系统)
            ],
            "timezone": "Europe/London"  # 使用伦敦时区
        }
        
        try:
            print("🔄 向Open-Meteo API发送请求...")
            print(f"   请求参数: {list(params['daily'])}")
            
            # 发送API请求
            responses = self.openmeteo.weather_api(self.url, params=params)
            
            # 处理响应
            response = responses[0]
            
            print("✅ API请求成功!")
            print(f"📊 返回坐标: {response.Latitude():.4f}°N {response.Longitude():.4f}°E")
            print(f"🏔️ 海拔高度: {response.Elevation():.1f} m")
            print(f"🕐 时区: {response.Timezone()} ({response.TimezoneAbbreviation()})")
            print(f"⏰ UTC偏移: {response.UtcOffsetSeconds()} 秒")
            
            # 处理每日数据
            daily = response.Daily()
            
            # 创建时间序列
            daily_data = {
                "date": pd.date_range(
                    start=pd.to_datetime(daily.Time(), unit="s", utc=True),
                    end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
                    freq=pd.Timedelta(seconds=daily.Interval()),
                    inclusive="left"
                ).tz_convert('Europe/London')  # 转换为伦敦时区
            }
            
            # 提取各气象变量
            variables = [
                ("temperature_2m_mean", "平均温度"),
                ("precipitation_sum", "降水量"),
                ("temperature_2m_max", "最高温度"),
                ("temperature_2m_min", "最低温度"),
                ("relative_humidity_2m_mean", "平均湿度"),
                ("wind_speed_10m_max", "最大风速"),
                ("sunshine_duration", "日照时长"),
                ("soil_temperature_0_to_7cm", "表层土壤温度"),
                ("soil_temperature_28_to_100cm", "深层土壤温度"),
                ("soil_temperature_7_to_28cm", "根系层土壤温度"),
                ("soil_moisture_0_to_7cm", "表层土壤湿度"),
                ("soil_moisture_28_to_100cm", "深层土壤湿度"),
                ("soil_moisture_7_to_28cm", "根系层土壤湿度")
            ]
            
            for i, (var_name, var_desc) in enumerate(variables):
                try:
                    values = daily.Variables(i).ValuesAsNumpy()
                    daily_data[var_name] = values
                    print(f"   ✓ {var_desc} ({var_name}): {len(values)} 个数据点")
                except Exception as e:
                    print(f"   ⚠️ 无法获取 {var_desc}: {e}")
                    daily_data[var_name] = None
            
            # 创建DataFrame
            df = pd.DataFrame(data=daily_data)
            
            # 数据质量检查
            print(f"\n📈 数据质量报告:")
            print(f"   总记录数: {len(df)}")
            print(f"   日期范围: {df['date'].min().date()} 至 {df['date'].max().date()}")
            
            for var_name, var_desc in variables:
                if var_name in df.columns and df[var_name].notna().any():
                    valid_count = df[var_name].notna().sum()
                    print(f"   {var_desc}: {valid_count}/{len(df)} 有效数据 ({valid_count/len(df)*100:.1f}%)")
            
            return df
            
        except Exception as e:
            print(f"❌ 数据收集失败: {e}")
            return None
    
    def analyze_data(self, df):
        """分析收集到的数据"""
        
        if df is None or df.empty:
            print("❌ 没有数据可分析")
            return
        
        print("\n" + "=" * 60)
        print("📊 数据统计分析")
        print("=" * 60)
        
        # 温度分析
        if 'temperature_2m_mean' in df.columns:
            temp_mean = df['temperature_2m_mean']
            print(f"🌡️ 温度统计 (°C):")
            print(f"   平均温度: {temp_mean.mean():.2f}°C")
            print(f"   最低记录: {temp_mean.min():.2f}°C")
            print(f"   最高记录: {temp_mean.max():.2f}°C")
            print(f"   标准差: {temp_mean.std():.2f}°C")
        
        # 降水分析
        if 'precipitation_sum' in df.columns:
            precip = df['precipitation_sum']
            print(f"\n🌧️ 降水统计:")
            print(f"   总降水量: {precip.sum():.1f} mm")
            print(f"   平均日降水: {precip.mean():.2f} mm")
            print(f"   最大日降水: {precip.max():.1f} mm")
            print(f"   降水天数: {(precip > 0.1).sum()} 天")
        
        # 土壤湿度分析
        if 'soil_moisture_0_to_7cm' in df.columns:
            soil_moisture = df['soil_moisture_0_to_7cm']
            print(f"\n💧 土壤湿度统计 (表层0-7cm):")
            print(f"   平均湿度: {soil_moisture.mean():.3f} m³/m³")
            print(f"   湿度范围: {soil_moisture.min():.3f} - {soil_moisture.max():.3f}")
            print(f"   饱和天数: {(soil_moisture > 0.4).sum()} 天 (>40%含水量)")
            print(f"   干旱天数: {(soil_moisture < 0.1).sum()} 天 (<10%含水量)")
        
        # 按年份统计
        df['year'] = df['date'].dt.year
        # 构建年度统计的字典
        agg_dict = {
            'temperature_2m_mean': ['mean', 'min', 'max'],
            'precipitation_sum': ['sum', 'mean', 'max']
        }
        
        # 如果有土壤湿度数据，添加到统计中
        if 'soil_moisture_0_to_7cm' in df.columns:
            agg_dict['soil_moisture_0_to_7cm'] = ['mean', 'min', 'max']
        
        yearly_stats = df.groupby('year').agg(agg_dict).round(3)
        
        print(f"\n📅 年度统计:")
        print(yearly_stats)
    
    def save_data(self, df, filename=None):
        """保存数据到CSV文件"""
        
        if df is None or df.empty:
            print("❌ 没有数据可保存")
            return False
        
        # 创建输出目录
        os.makedirs('outputs', exist_ok=True)
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"london_environment_3years_{timestamp}.csv"
        
        filepath = os.path.join('outputs', filename)
        
        try:
            # 准备保存的数据
            save_df = df.copy()
            save_df['date'] = save_df['date'].dt.strftime('%Y-%m-%d')
            
            # 保存到CSV
            save_df.to_csv(filepath, index=False)
            
            print(f"\n💾 数据保存成功!")
            print(f"   文件路径: {filepath}")
            print(f"   数据维度: {save_df.shape[0]} 行 x {save_df.shape[1]} 列")
            print(f"   文件大小: {os.path.getsize(filepath) / 1024:.2f} KB")
            
            return True
            
        except Exception as e:
            print(f"❌ 保存失败: {e}")
            return False
    
    def run_full_workflow(self, years=3):
        """运行完整的数据收集工作流程"""
        
        print("🚀 启动Open-Meteo历史数据收集工作流程")
        print("=" * 60)
        print(f"🎯 目标: 收集过去{years}年伦敦环境数据")
        print("📋 数据类型: 气象数据(温度,降水,湿度,风速) + 土壤数据(分层温度&湿度)")
        print("=" * 60)
        
        # 1. 数据收集
        df = self.collect_weather_data(years)
        
        if df is not None:
            # 2. 数据分析
            self.analyze_data(df)
            
            # 3. 保存数据
            self.save_data(df)
            
            # 4. 数据预览
            print(f"\n📋 数据预览 (前5行):")
            print(df.head())
            
            print(f"\n🎉 数据收集完成! 共获取 {len(df)} 天的环境数据")
            return True
        else:
            print("😞 数据收集失败")
            return False

def main():
    """主函数"""
    
    print("Open-Meteo API 伦敦历史环境数据收集器")
    print("=" * 60)
    
    # 创建收集器实例
    collector = OpenMeteoCollector()
    
    # 运行数据收集
    success = collector.run_full_workflow(years=3)
    
    if success:
        print("\n✅ 任务完成!")
        print("📂 数据已保存在 outputs/ 目录下")
    else:
        print("\n❌ 任务失败")

if __name__ == "__main__":
    main() 