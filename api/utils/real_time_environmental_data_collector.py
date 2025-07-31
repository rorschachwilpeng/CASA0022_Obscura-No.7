#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时环境数据获取器
用于获取11个环境变量的当前数据和历史数据，支持SHAP模型的特征工程
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import time
from typing import Dict, List, Optional, Tuple
import json

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealTimeEnvironmentalDataCollector:
    """实时环境数据收集器"""
    
    def __init__(self):
        """初始化数据收集器"""
        
        # API配置
        self.open_meteo_archive_url = "https://archive-api.open-meteo.com/v1/archive"
        self.open_meteo_forecast_url = "https://api.open-meteo.com/v1/forecast"
        self.open_meteo_flood_url = "https://flood-api.open-meteo.com/v1/flood"
        self.open_meteo_air_quality_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
        
        # 城市坐标
        self.cities = {
            'London': {'lat': 51.5085, 'lon': -0.1257},
            'Manchester': {'lat': 53.4794, 'lon': -2.2453},
            'Edinburgh': {'lat': 55.9533, 'lon': -3.1883}
        }
        
        # API参数映射 - 气象数据 (Archive API)
        self.meteorological_params = [
            'temperature_2m',           # 温度
            'relative_humidity_2m',     # 湿度
            'wind_speed_10m',          # 风速
            'precipitation',           # 降水
            'surface_pressure',        # 大气压
            'shortwave_radiation'      # 太阳辐射
        ]
        
        # 空气质量参数 (Air Quality API)
        self.air_quality_params = [
            'nitrogen_dioxide'         # NO2
        ]
        
        self.geospatial_hourly_params = [
            'soil_temperature_0_to_7cm',   # 土壤温度
            'soil_moisture_7_to_28cm'      # 土壤湿度
        ]
        
        self.geospatial_daily_params = [
            'et0_fao_evapotranspiration'   # 蒸散发
        ]
        
        # 滞后周期和移动平均窗口
        self.lag_periods = [1, 3, 6, 12]  # 月
        self.ma_windows = [3, 6, 12]      # 月
    
    def get_closest_city(self, latitude: float, longitude: float) -> str:
        """获取最近的城市"""
        min_distance = float('inf')
        closest_city = 'London'
        
        for city, coords in self.cities.items():
            distance = np.sqrt((latitude - coords['lat'])**2 + (longitude - coords['lon'])**2)
            if distance < min_distance:
                min_distance = distance
                closest_city = city
        
        return closest_city
    
    def fetch_daily_meteorological_data(self, lat: float, lon: float, date: str) -> Dict:
        """获取单日气象数据（小时级→日平均）"""
        
        try:
            base_url = self.open_meteo_archive_url
            # 手动构建查询字符串
            params_str = f"latitude={lat}&longitude={lon}&start_date={date}&end_date={date}&hourly={','.join(self.meteorological_params)}&timezone=UTC"
            
            response = requests.get(f"{base_url}?{params_str}", timeout=2)
            response.raise_for_status()
            
            data = response.json()
            
            if 'hourly' not in data or not data['hourly']:
                logger.warning(f"无气象数据: {date}")
                return self._get_default_meteorological_data()
            
            # 转换小时级数据为日平均
            hourly_data = data['hourly']
            df = pd.DataFrame({
                'datetime': pd.to_datetime(hourly_data['time']),
                **{param: hourly_data[param] for param in self.meteorological_params}
            })
            
            # 过滤有效数据
            df = df.dropna()
            
            if df.empty:
                logger.warning(f"气象数据为空: {date}")
                return self._get_default_meteorological_data()
            
            # 计算日统计值
            result = {
                'temperature': df['temperature_2m'].mean(),
                'humidity': df['relative_humidity_2m'].mean(),
                'wind_speed': df['wind_speed_10m'].mean(),
                'precipitation': df['precipitation'].sum(),  # 降水用累计
                'atmospheric_pressure': df['surface_pressure'].mean(),
                'solar_radiation': df['shortwave_radiation'].mean()
            }
            
            # 数据验证和清理
            result = self._validate_meteorological_data(result)
            
            logger.debug(f"气象数据获取成功: {date}")
            return result
            
        except Exception as e:
            logger.error(f"获取气象数据失败 {date}: {e}")
            return self._get_default_meteorological_data()
    
    def fetch_daily_geospatial_data(self, lat: float, lon: float, date: str) -> Dict:
        """获取单日地理数据"""
        
        try:
            base_url = self.open_meteo_archive_url
            # 手动构建查询字符串
            hourly_params_str = ",".join(self.geospatial_hourly_params)
            daily_params_str = ",".join(self.geospatial_daily_params)
            params_str = f"latitude={lat}&longitude={lon}&start_date={date}&end_date={date}&hourly={hourly_params_str}&daily={daily_params_str}&timezone=UTC"

            response = requests.get(f"{base_url}?{params_str}", timeout=2)
            response.raise_for_status()
            
            data = response.json()
            result = {}
            
            # 处理小时级土壤数据
            if 'hourly' in data and data['hourly']:
                hourly_data = data['hourly']
                df_hourly = pd.DataFrame({
                    'datetime': pd.to_datetime(hourly_data['time']),
                    **{param: hourly_data[param] for param in self.geospatial_hourly_params}
                })
                
                df_hourly = df_hourly.dropna()
                
                if not df_hourly.empty:
                    result['soil_temperature_0_7cm'] = df_hourly['soil_temperature_0_to_7cm'].mean()
                    result['soil_moisture_7_28cm'] = df_hourly['soil_moisture_7_to_28cm'].mean()
            
            # 处理日级蒸散发数据
            if 'daily' in data and data['daily']:
                daily_data = data['daily']
                if daily_data['et0_fao_evapotranspiration'] and daily_data['et0_fao_evapotranspiration'][0] is not None:
                    result['reference_evapotranspiration'] = daily_data['et0_fao_evapotranspiration'][0]
            
            # 获取洪水风险数据
            flood_data = self._fetch_flood_risk_data(lat, lon, date)
            result.update(flood_data)
            
            # 填充缺失数据
            result = self._validate_geospatial_data(result)
            
            logger.debug(f"地理数据获取成功: {date}")
            return result
            
        except Exception as e:
            logger.error(f"获取地理数据失败 {date}: {e}")
            return self._get_default_geospatial_data()
    
    def _fetch_flood_risk_data(self, lat: float, lon: float, date: str) -> Dict:
        """获取洪水风险数据"""
        
        try:
            params = {
                'latitude': lat,
                'longitude': lon,
                'start_date': date,
                'end_date': date,
                'daily': 'river_discharge_max',  # 保持不变，已经是单个字符串
                'timezone': 'UTC'
            }
            
            response = requests.get(self.open_meteo_flood_url, params=params, timeout=2)
            response.raise_for_status()
            
            data = response.json()
            
            if 'daily' in data and data['daily'] and data['daily']['river_discharge_max']:
                discharge = data['daily']['river_discharge_max'][0]
                if discharge is not None:
                    return {'urban_flood_risk': discharge}
            
            return {'urban_flood_risk': 1.0}  # 默认值
            
        except Exception as e:
            logger.warning(f"获取洪水数据失败 {date}: {e}")
            return {'urban_flood_risk': 1.0}
    
    def fetch_daily_air_quality_data(self, lat: float, lon: float, date: str) -> Dict:
        """获取指定日期的空气质量数据"""
        
        try:
            base_url = self.open_meteo_air_quality_url
            # 手动构建查询字符串
            params_str = f"latitude={lat}&longitude={lon}&start_date={date}&end_date={date}&hourly={','.join(self.air_quality_params)}&timezone=UTC"
            
            response = requests.get(f"{base_url}?{params_str}", timeout=2)
            response.raise_for_status()
            
            data = response.json()
            
            if 'hourly' not in data or not data['hourly']:
                logger.warning(f"无空气质量数据: {date}")
                return self._get_default_air_quality_data()
            
            # 转换小时级数据为日平均
            hourly_data = data['hourly']
            df = pd.DataFrame({
                'datetime': pd.to_datetime(hourly_data['time']),
                **{param: hourly_data[param] for param in self.air_quality_params}
            })
            
            # 过滤有效数据
            df = df.dropna()
            
            if df.empty:
                logger.warning(f"空气质量数据为空: {date}")
                return self._get_default_air_quality_data()
            
            # 计算日统计值
            result = {
                'NO2': df['nitrogen_dioxide'].mean() if not df['nitrogen_dioxide'].isna().all() else 15.0
            }
            
            # 数据验证和清理
            result = self._validate_air_quality_data(result)
            
            logger.info(f"空气质量数据获取成功: {date}")
            return result
            
        except Exception as e:
            logger.error(f"获取空气质量数据失败 {date}: {e}")
            return self._get_default_air_quality_data()
    
    def _get_default_air_quality_data(self) -> Dict:
        """获取默认空气质量数据"""
        return {
            'NO2': 15.0  # μg/m³
        }
    
    def _validate_air_quality_data(self, data: Dict) -> Dict:
        """验证和清理空气质量数据"""
        
        # NO2 合理范围检查
        if data['NO2'] < 0 or data['NO2'] > 200:
            data['NO2'] = 15.0
        
        return data
    
    def get_current_environmental_data(self, latitude: float, longitude: float) -> Dict:
        """获取当前环境数据 (使用3天前的数据，因为Open-Meteo有数据处理延迟)"""
        
        # Open-Meteo Archive API有3-5天数据处理延迟，使用3天前的日期确保数据可用性
        three_days_ago = datetime.now() - timedelta(days=3)
        today = three_days_ago.strftime('%Y-%m-%d')
        logger.info(f"获取环境数据日期: {today} (3天前，确保数据可用性)")
        
        # 获取气象数据
        meteo_data = self.fetch_daily_meteorological_data(latitude, longitude, today)
        
        # 获取地理数据
        geo_data = self.fetch_daily_geospatial_data(latitude, longitude, today)
        
        # 获取空气质量数据
        air_quality_data = self.fetch_daily_air_quality_data(latitude, longitude, today)
        
        # 合并数据
        environmental_data = {**meteo_data, **geo_data, **air_quality_data}
        
        logger.info(f"当前环境数据获取完成: {len(environmental_data)} 个变量")
        return environmental_data
    
    def get_historical_lag_data(self, latitude: float, longitude: float) -> Dict:
        """获取滞后特征所需的历史数据"""
        
        historical_data = {}
        
        for lag_months in self.lag_periods:
            # 计算历史日期
            target_date = datetime.now() - timedelta(days=lag_months * 30)
            date_str = target_date.strftime('%Y-%m-%d')
            
            logger.info(f"获取 {lag_months}个月前数据: {date_str}")
            
            # 获取气象数据
            meteo_data = self.fetch_daily_meteorological_data(latitude, longitude, date_str)
            geo_data = self.fetch_daily_geospatial_data(latitude, longitude, date_str)
            air_quality_data = self.fetch_daily_air_quality_data(latitude, longitude, date_str)
            
            historical_data[f'lag_{lag_months}'] = {**meteo_data, **geo_data, **air_quality_data}
            
            # 基于诊断结果，1秒间隔能达到100%成功率
            time.sleep(1.0)
        
        logger.info(f"历史数据获取完成: {len(self.lag_periods)} 个时间点")
        return historical_data
    
    def get_moving_average_data(self, latitude: float, longitude: float) -> Dict:
        """获取移动平均计算所需的时间序列数据"""
        
        ma_data = {}
        
        for window in self.ma_windows:
            logger.info(f"获取 {window}个月移动平均数据...")
            
            window_data = []
            
            # 获取过去N个月的数据
            for i in range(window):
                target_date = datetime.now() - timedelta(days=(i + 1) * 30)
                date_str = target_date.strftime('%Y-%m-%d')
                
                meteo_data = self.fetch_daily_meteorological_data(latitude, longitude, date_str)
                geo_data = self.fetch_daily_geospatial_data(latitude, longitude, date_str)
                air_quality_data = self.fetch_daily_air_quality_data(latitude, longitude, date_str)
                
                window_data.append({**meteo_data, **geo_data, **air_quality_data})
                time.sleep(1.0)  # 基于诊断结果优化间隔
            
            # 计算移动平均
            if window_data:
                ma_averages = {}
                for var_name in window_data[0].keys():
                    values = [d[var_name] for d in window_data if var_name in d and d[var_name] is not None]
                    ma_averages[var_name] = np.mean(values) if values else 0.0
                
                ma_data[f'ma_{window}'] = ma_averages
        
        logger.info(f"移动平均数据获取完成: {len(self.ma_windows)} 个窗口")
        return ma_data
    
    def _get_default_meteorological_data(self) -> Dict:
        """获取默认气象数据"""
        return {
            'temperature': 15.0,
            'humidity': 65.0,
            'wind_speed': 5.0,
            'precipitation': 1.0,
            'atmospheric_pressure': 1013.25,
            'solar_radiation': 200.0
        }
    
    def _get_default_geospatial_data(self) -> Dict:
        """获取默认地理数据"""
        return {
            'soil_temperature_0_7cm': 12.0,
            'soil_moisture_7_28cm': 0.3,
            'reference_evapotranspiration': 2.5,
            'urban_flood_risk': 1.0
        }
    
    def _validate_meteorological_data(self, data: Dict) -> Dict:
        """验证和清理气象数据"""
        
        # 数据范围验证
        ranges = {
            'temperature': (-50, 50),
            'humidity': (0, 100),
            'wind_speed': (0, 100),
            'precipitation': (0, 500),
            'atmospheric_pressure': (900, 1100),
            'solar_radiation': (0, 1500),
            'NO2': (0, 200)
        }
        
        validated_data = {}
        defaults = self._get_default_meteorological_data()
        
        for key, value in data.items():
            if key in ranges:
                min_val, max_val = ranges[key]
                if value is None or not (min_val <= value <= max_val):
                    validated_data[key] = defaults[key]
                    logger.warning(f"气象数据异常，使用默认值: {key}={value} -> {defaults[key]}")
                else:
                    validated_data[key] = value
            else:
                validated_data[key] = value
        
        return validated_data
    
    def _validate_geospatial_data(self, data: Dict) -> Dict:
        """验证和清理地理数据"""
        
        ranges = {
            'soil_temperature_0_7cm': (-20, 40),
            'soil_moisture_7_28cm': (0, 1),
            'reference_evapotranspiration': (0, 20),
            'urban_flood_risk': (0, 100)
        }
        
        validated_data = {}
        defaults = self._get_default_geospatial_data()
        
        for key, default_value in defaults.items():
            if key in data:
                value = data[key]
                if key in ranges:
                    min_val, max_val = ranges[key]
                    if value is None or not (min_val <= value <= max_val):
                        validated_data[key] = default_value
                        logger.warning(f"地理数据异常，使用默认值: {key}={value} -> {default_value}")
                    else:
                        validated_data[key] = value
                else:
                    validated_data[key] = value if value is not None else default_value
            else:
                validated_data[key] = default_value
        
        return validated_data


# 全局实例
_environmental_collector = None

def get_environmental_collector():
    """获取环境数据收集器单例"""
    global _environmental_collector
    if _environmental_collector is None:
        _environmental_collector = RealTimeEnvironmentalDataCollector()
    return _environmental_collector 