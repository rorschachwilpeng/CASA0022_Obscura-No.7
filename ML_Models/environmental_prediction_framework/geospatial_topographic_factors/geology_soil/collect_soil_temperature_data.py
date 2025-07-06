#!/usr/bin/env python3
"""
Soil Temperature (0-7cm) Data Collector for Geology & Soil Analysis

收集伦敦、曼切斯特、爱丁堡的土壤温度数据 (0-7cm深度)
数据源：Open-Meteo Historical Weather API
时间范围：1991-2025
输出格式：CSV (每日数据)
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
import sys
import os

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 城市坐标信息
CITIES = {
    'London': {'lat': 51.5085, 'lon': -0.1257},
    'Manchester': {'lat': 53.4794, 'lon': -2.2453},
    'Edinburgh': {'lat': 55.9533, 'lon': -3.1883}
}

def collect_soil_temperature_data(city_name, lat, lon, start_date, end_date):
    """
    收集指定城市的土壤温度数据 (0-7cm) （分段获取）
    
    Args:
        city_name: 城市名称
        lat: 纬度
        lon: 经度
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
    
    Returns:
        DataFrame: 包含每日土壤温度数据
    """
    
    from datetime import datetime
    
    # 解析日期
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    
    # 当前日期，避免请求未来数据
    current_dt = datetime.now()
    if end_dt > current_dt:
        end_dt = current_dt
        logger.warning(f"{city_name}: 调整结束日期到当前时间 {end_dt.strftime('%Y-%m-%d')}")
    
    logger.info(f"正在收集 {city_name} 的土壤温度数据 (0-7cm)...")
    logger.info(f"时间范围: {start_dt.strftime('%Y-%m-%d')} 到 {end_dt.strftime('%Y-%m-%d')}")
    
    all_data = []
    
    # 按年分段获取数据
    current_year = start_dt.year
    while current_year <= end_dt.year:
        
        # 确定当前年份的开始和结束日期
        year_start = max(start_dt, datetime(current_year, 1, 1))
        year_end = min(end_dt, datetime(current_year, 12, 31))
        
        year_start_str = year_start.strftime('%Y-%m-%d')
        year_end_str = year_end.strftime('%Y-%m-%d')
        
        logger.info(f"  获取 {city_name} {current_year}年数据: {year_start_str} 到 {year_end_str}")
        
        # 构建API请求
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            'latitude': lat,
            'longitude': lon,
            'start_date': year_start_str,
            'end_date': year_end_str,
            'hourly': 'soil_temperature_0_to_7cm',
            'timezone': 'UTC'
        }
        
        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            
            if 'hourly' in data and data['hourly']:
                hourly_data = data['hourly']
                
                # 转换为DataFrame
                year_df = pd.DataFrame({
                    'datetime': pd.to_datetime(hourly_data['time']),
                    'soil_temperature_0_to_7cm': hourly_data['soil_temperature_0_to_7cm']
                })
                
                # 过滤掉空值
                year_df = year_df.dropna()
                all_data.append(year_df)
                
                logger.info(f"    {current_year}年数据收集完成: {len(year_df)} 条记录")
            else:
                logger.warning(f"    {current_year}年无数据")
            
            # 添加延时避免API限制
            time.sleep(1)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"    {current_year}年API请求失败: {e}")
        except Exception as e:
            logger.error(f"    {current_year}年数据处理错误: {e}")
        
        current_year += 1
    
    # 合并所有年份数据
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # 转换为每日数据
        combined_df['date'] = combined_df['datetime'].dt.date
        daily_df = combined_df.groupby('date')['soil_temperature_0_to_7cm'].mean().reset_index()
        
        logger.info(f"{city_name} 总数据收集完成: {len(daily_df)} 条每日记录")
        return daily_df
    else:
        logger.error(f"{city_name} 没有收集到任何数据")
        return None

def merge_city_data(city_data_dict):
    """
    合并多个城市的数据为统一格式
    
    Args:
        city_data_dict: 包含各城市数据的字典
    
    Returns:
        DataFrame: 合并后的数据，格式为 date, London_soil_temp, Manchester_soil_temp, Edinburgh_soil_temp
    """
    
    if not city_data_dict:
        logger.error("没有有效的城市数据进行合并")
        return None
    
    # 获取所有日期的并集
    all_dates = set()
    for city_df in city_data_dict.values():
        if city_df is not None:
            all_dates.update(city_df['date'])
    
    if not all_dates:
        logger.error("没有找到有效的日期数据")
        return None
    
    # 创建完整的日期范围
    date_range = pd.DataFrame({'date': sorted(all_dates)})
    
    # 逐个合并城市数据
    merged_df = date_range.copy()
    
    for city_name, city_df in city_data_dict.items():
        if city_df is not None:
            # 重命名列
            city_df_renamed = city_df.copy()
            city_df_renamed = city_df_renamed.rename(columns={
                'soil_temperature_0_to_7cm': f'{city_name}_soil_temp'
            })
            
            # 合并数据
            merged_df = merged_df.merge(
                city_df_renamed[['date', f'{city_name}_soil_temp']], 
                on='date', 
                how='left'
            )
        else:
            # 如果该城市数据缺失，创建空列
            merged_df[f'{city_name}_soil_temp'] = np.nan
            logger.warning(f"{city_name} 数据缺失，使用NaN填充")
    
    logger.info(f"数据合并完成: {len(merged_df)} 条记录")
    return merged_df

def main():
    """主函数"""
    
    logger.info("开始收集土壤温度数据 (0-7cm)...")
    
    # 设置时间范围 (完整历史数据)
    start_date = "1991-01-01"
    end_date = "2025-12-31"
    
    # 收集各城市数据
    city_data = {}
    
    for city_name, coords in CITIES.items():
        logger.info(f"\n处理城市: {city_name}")
        
        # 添加延时避免API限制
        if city_name != 'London':  # 第一个城市不需要延时
            time.sleep(2)
        
        city_df = collect_soil_temperature_data(
            city_name, 
            coords['lat'], 
            coords['lon'], 
            start_date, 
            end_date
        )
        
        city_data[city_name] = city_df
    
    # 合并数据
    logger.info("\n开始合并城市数据...")
    merged_data = merge_city_data(city_data)
    
    if merged_data is not None:
        # 输出文件路径
        output_file = 'soil_temperature_0_7cm_data.csv'
        
        # 保存数据
        merged_data.to_csv(output_file, index=False)
        logger.info(f"数据已保存到: {output_file}")
        
        # 显示数据摘要
        logger.info("\n=== 数据摘要 ===")
        logger.info(f"总记录数: {len(merged_data)}")
        logger.info(f"日期范围: {merged_data['date'].min()} 到 {merged_data['date'].max()}")
        
        # 显示各城市数据统计
        for city in ['London', 'Manchester', 'Edinburgh']:
            col_name = f'{city}_soil_temp'
            if col_name in merged_data.columns:
                valid_count = merged_data[col_name].notna().sum()
                if valid_count > 0:
                    mean_val = merged_data[col_name].mean()
                    min_val = merged_data[col_name].min()
                    max_val = merged_data[col_name].max()
                    logger.info(f"{city}: {valid_count} 条记录, 平均值: {mean_val:.2f}°C, 范围: {min_val:.2f}°C-{max_val:.2f}°C")
                else:
                    logger.warning(f"{city}: 无有效数据")
        
        # 显示前几行数据
        logger.info("\n=== 数据预览 ===")
        print(merged_data.head())
        
        logger.info("\n土壤温度数据收集完成!")
        
    else:
        logger.error("数据收集失败!")
        sys.exit(1)

if __name__ == "__main__":
    main() 