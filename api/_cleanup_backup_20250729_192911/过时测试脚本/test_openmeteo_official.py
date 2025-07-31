#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Open-Meteo官方库获取实时数据
验证能否获取当天的有效环境数据
"""

import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from datetime import datetime

def test_official_openmeteo_api():
    print("🧪 测试Open-Meteo官方库数据获取")
    print("=" * 60)
    
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)
    
    # 测试当天数据
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"📅 测试日期: {today}")
    
    # Make sure all required weather variables are listed here
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": 51.5085,
        "longitude": -0.1257,
        "start_date": today,
        "end_date": today,
        "hourly": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "precipitation"],
    }
    
    try:
        print("🌐 正在调用Open-Meteo API...")
        responses = openmeteo.weather_api(url, params=params)
        
        # Process first location
        response = responses[0]
        print(f"✅ API调用成功!")
        print(f"📍 坐标: {response.Latitude()}°N {response.Longitude()}°E")
        print(f"⛰️ 海拔: {response.Elevation()} m asl")
        print(f"🕐 时区偏移: {response.UtcOffsetSeconds()}s")
        
        # Process hourly data
        hourly = response.Hourly()
        hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
        hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()
        hourly_wind_speed_10m = hourly.Variables(2).ValuesAsNumpy()
        hourly_precipitation = hourly.Variables(3).ValuesAsNumpy()
        
        hourly_data = {"date": pd.date_range(
            start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
            end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
            freq = pd.Timedelta(seconds = hourly.Interval()),
            inclusive = "left"
        )}
        
        hourly_data["temperature_2m"] = hourly_temperature_2m
        hourly_data["relative_humidity_2m"] = hourly_relative_humidity_2m
        hourly_data["wind_speed_10m"] = hourly_wind_speed_10m
        hourly_data["precipitation"] = hourly_precipitation
        
        hourly_dataframe = pd.DataFrame(data = hourly_data)
        
        print(f"\n📊 获取到的小时数据:")
        print(f"总行数: {len(hourly_dataframe)}")
        print("\n前5行数据:")
        print(hourly_dataframe.head())
        
        print("\n后5行数据:")
        print(hourly_dataframe.tail())
        
        # 检查数据质量
        print(f"\n🔍 数据质量分析:")
        for col in ['temperature_2m', 'relative_humidity_2m', 'wind_speed_10m', 'precipitation']:
            valid_count = hourly_dataframe[col].notna().sum()
            total_count = len(hourly_dataframe)
            null_count = hourly_dataframe[col].isna().sum()
            print(f"  {col}: {valid_count}/{total_count} 有效数据, {null_count} 个null值")
            
            if valid_count > 0:
                print(f"    范围: {hourly_dataframe[col].min():.2f} - {hourly_dataframe[col].max():.2f}")
                print(f"    平均: {hourly_dataframe[col].mean():.2f}")
        
        # 检查是否有足够的有效数据
        temperature_valid = hourly_dataframe['temperature_2m'].notna().sum()
        humidity_valid = hourly_dataframe['relative_humidity_2m'].notna().sum()
        
        if temperature_valid >= 12 and humidity_valid >= 12:  # 至少12小时有效数据
            print(f"\n✅ 数据质量良好: 温度和湿度都有{min(temperature_valid, humidity_valid)}小时有效数据")
            return True
        else:
            print(f"\n⚠️ 数据质量不足: 温度{temperature_valid}小时, 湿度{humidity_valid}小时有效数据")
            return False
            
    except Exception as e:
        print(f"❌ API调用失败: {e}")
        return False

def test_historical_data():
    print("\n🕐 测试历史数据获取 (7天前)")
    print("=" * 60)
    
    cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)
    
    # 测试7天前的数据
    seven_days_ago = (datetime.now() - pd.Timedelta(days=7)).strftime('%Y-%m-%d')
    print(f"📅 测试日期: {seven_days_ago}")
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": 51.5085,
        "longitude": -0.1257,
        "start_date": seven_days_ago,
        "end_date": seven_days_ago,
        "hourly": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "precipitation"],
    }
    
    try:
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]
        
        hourly = response.Hourly()
        hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
        
        hourly_data = {"date": pd.date_range(
            start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
            end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
            freq = pd.Timedelta(seconds = hourly.Interval()),
            inclusive = "left"
        )}
        hourly_data["temperature_2m"] = hourly_temperature_2m
        
        df = pd.DataFrame(data = hourly_data)
        valid_count = df['temperature_2m'].notna().sum()
        
        print(f"✅ 历史数据: {valid_count}/24 小时有效数据")
        if valid_count >= 20:
            print("✅ 历史数据质量良好")
            return True
        else:
            print("⚠️ 历史数据质量不足")
            return False
            
    except Exception as e:
        print(f"❌ 历史数据获取失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Open-Meteo官方库测试开始\n")
    
    # 测试当天数据
    current_result = test_official_openmeteo_api()
    
    # 测试历史数据
    historical_result = test_historical_data()
    
    print("\n" + "=" * 60)
    print("🎯 测试结果总结:")
    print(f"  当天数据: {'✅ 成功' if current_result else '❌ 失败'}")
    print(f"  历史数据: {'✅ 成功' if historical_result else '❌ 失败'}")
    
    if current_result and historical_result:
        print("\n🎉 Open-Meteo官方库工作正常!")
        print("📝 建议: 将现有代码迁移到官方库")
    elif historical_result:
        print("\n⚠️ 当天数据不可用，但历史数据正常")
        print("📝 建议: 使用昨天或前天的数据作为'当前'数据")
    else:
        print("\n❌ 数据获取存在问题，需要进一步调查") 