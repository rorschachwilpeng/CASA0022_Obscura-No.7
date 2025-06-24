#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境数据获取客户端
调用OpenWeather API获取当前和历史环境数据
"""

import requests
import json
import time
from datetime import datetime, timedelta

class WeatherClient:
    def __init__(self, api_key):
        """初始化天气客户端"""
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5"
        self.geo_url = "http://api.openweathermap.org/geo/1.0"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Obscura-No.7-Telescope/1.0'
        })
    
    def get_current_weather(self, lat, lon):
        """获取当前天气数据"""
        try:
            endpoint = f"{self.base_url}/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'zh_cn'
            }
            
            response = self._make_request('GET', endpoint, params)
            if response and response.status_code == 200:
                data = response.json()
                return self._format_current_weather(data)
            else:
                print(f"❌ 获取当前天气失败: {response.status_code if response else 'No response'}")
                return None
                
        except Exception as e:
            print(f"❌ 当前天气API错误: {e}")
            return None
    
    def get_weather_forecast(self, lat, lon, days=5):
        """获取天气预报"""
        try:
            endpoint = f"{self.base_url}/forecast"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'zh_cn'
            }
            
            response = self._make_request('GET', endpoint, params)
            if response and response.status_code == 200:
                data = response.json()
                return self._format_forecast_data(data, days)
            else:
                print(f"❌ 获取天气预报失败: {response.status_code if response else 'No response'}")
                return None
                
        except Exception as e:
            print(f"❌ 天气预报API错误: {e}")
            return None
    
    def get_air_quality(self, lat, lon):
        """获取空气质量数据"""
        try:
            endpoint = f"{self.base_url}/air_pollution"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key
            }
            
            response = self._make_request('GET', endpoint, params)
            if response and response.status_code == 200:
                data = response.json()
                return self._format_air_quality(data)
            else:
                print(f"❌ 获取空气质量失败: {response.status_code if response else 'No response'}")
                return None
                
        except Exception as e:
            print(f"❌ 空气质量API错误: {e}")
            return None
    
    def get_comprehensive_data(self, lat, lon):
        """获取综合环境数据"""
        print(f"🌤️ 获取坐标 ({lat:.4f}, {lon:.4f}) 的环境数据...")
        
        # 并行获取所有数据
        current_weather = self.get_current_weather(lat, lon)
        forecast = self.get_weather_forecast(lat, lon, days=5)
        air_quality = self.get_air_quality(lat, lon)
        
        # 组合数据
        comprehensive_data = {
            'coordinates': {'lat': lat, 'lon': lon},
            'timestamp': datetime.now().isoformat(),
            'current_weather': current_weather,
            'forecast': forecast,
            'air_quality': air_quality,
            'data_quality': self._assess_data_quality(current_weather, forecast, air_quality)
        }
        
        return comprehensive_data
    
    def format_for_ml_model(self, weather_data):
        """格式化天气数据为ML模型输入格式"""
        if not weather_data or not weather_data.get('current_weather'):
            return None
        
        current = weather_data['current_weather']
        forecast = weather_data.get('forecast', {})
        air_quality = weather_data.get('air_quality', {})
        
        # 提取ML模型需要的特征
        ml_features = {
            # 当前天气特征
            'temperature': current.get('temperature', 0),
            'humidity': current.get('humidity', 0),
            'pressure': current.get('pressure', 1013),
            'wind_speed': current.get('wind_speed', 0),
            'wind_direction': current.get('wind_direction', 0),
            'visibility': current.get('visibility', 10000),
            'cloud_cover': current.get('cloud_cover', 0),
            
            # 天气状况编码
            'weather_code': current.get('weather_id', 800),
            'is_clear': current.get('weather_main', '') == 'Clear',
            'is_cloudy': current.get('weather_main', '') in ['Clouds', 'Overcast'],
            'is_rainy': current.get('weather_main', '') in ['Rain', 'Drizzle'],
            'is_stormy': current.get('weather_main', '') in ['Thunderstorm'],
            
            # 时间特征
            'hour_of_day': datetime.now().hour,
            'day_of_year': datetime.now().timetuple().tm_yday,
            'season': self._get_season(),
            
            # 空气质量特征
            'aqi': air_quality.get('aqi', 2),
            'pm2_5': air_quality.get('pm2_5', 10),
            'pm10': air_quality.get('pm10', 20),
            'no2': air_quality.get('no2', 20),
            'o3': air_quality.get('o3', 60),
            
            # 预报趋势特征
            'temp_trend': self._calculate_temperature_trend(forecast),
            'pressure_trend': self._calculate_pressure_trend(forecast),
            'humidity_trend': self._calculate_humidity_trend(forecast),
        }
        
        return ml_features
    
    def _make_request(self, method, endpoint, params=None, timeout=10):
        """发起API请求"""
        try:
            if method.upper() == 'GET':
                response = self.session.get(endpoint, params=params, timeout=timeout)
            else:
                response = self.session.request(method, endpoint, params=params, timeout=timeout)
            
            return response
            
        except requests.exceptions.Timeout:
            print(f"⏰ API请求超时: {endpoint}")
            return None
        except requests.exceptions.ConnectionError:
            print(f"🌐 网络连接错误: {endpoint}")
            return None
        except Exception as e:
            print(f"❌ 请求错误: {e}")
            return None
    
    def _format_current_weather(self, data):
        """格式化当前天气数据"""
        try:
            return {
                'temperature': data['main']['temp'],
                'feels_like': data['main']['feels_like'],
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'visibility': data.get('visibility', 10000) / 1000,  # 转换为公里
                'wind_speed': data.get('wind', {}).get('speed', 0),
                'wind_direction': data.get('wind', {}).get('deg', 0),
                'cloud_cover': data.get('clouds', {}).get('all', 0),
                'weather_main': data['weather'][0]['main'],
                'weather_description': data['weather'][0]['description'],
                'weather_id': data['weather'][0]['id'],
                'location_name': data.get('name', 'Unknown'),
                'country': data.get('sys', {}).get('country', 'Unknown'),
                'sunrise': data.get('sys', {}).get('sunrise'),
                'sunset': data.get('sys', {}).get('sunset'),
                'timestamp': data.get('dt')
            }
        except KeyError as e:
            print(f"❌ 天气数据格式错误: {e}")
            return None
    
    def _format_forecast_data(self, data, days):
        """格式化预报数据"""
        try:
            forecasts = []
            for item in data['list'][:days*8]:  # 每天8个时间点（3小时间隔）
                forecast_item = {
                    'timestamp': item['dt'],
                    'datetime': datetime.fromtimestamp(item['dt']),
                    'temperature': item['main']['temp'],
                    'humidity': item['main']['humidity'],
                    'pressure': item['main']['pressure'],
                    'weather_main': item['weather'][0]['main'],
                    'weather_description': item['weather'][0]['description'],
                    'wind_speed': item.get('wind', {}).get('speed', 0),
                    'cloud_cover': item.get('clouds', {}).get('all', 0),
                    'rain_probability': item.get('pop', 0) * 100  # 降雨概率
                }
                forecasts.append(forecast_item)
            
            return {
                'forecasts': forecasts,
                'location': data.get('city', {}),
                'count': len(forecasts)
            }
        except KeyError as e:
            print(f"❌ 预报数据格式错误: {e}")
            return None
    
    def _format_air_quality(self, data):
        """格式化空气质量数据"""
        try:
            aqi_levels = {1: "优秀", 2: "良好", 3: "中等", 4: "较差", 5: "差"}
            components = data['list'][0]['components']
            
            return {
                'aqi': data['list'][0]['main']['aqi'],
                'aqi_description': aqi_levels.get(data['list'][0]['main']['aqi'], "未知"),
                'pm2_5': components.get('pm2_5', 0),
                'pm10': components.get('pm10', 0),
                'no2': components.get('no2', 0),
                'no': components.get('no', 0),
                'o3': components.get('o3', 0),
                'so2': components.get('so2', 0),
                'co': components.get('co', 0),
                'nh3': components.get('nh3', 0),
                'timestamp': data['list'][0]['dt']
            }
        except (KeyError, IndexError) as e:
            print(f"❌ 空气质量数据格式错误: {e}")
            return None
    
    def _assess_data_quality(self, current, forecast, air_quality):
        """评估数据质量"""
        quality_score = 0
        issues = []
        
        if current:
            quality_score += 40
        else:
            issues.append("缺少当前天气数据")
        
        if forecast:
            quality_score += 30
        else:
            issues.append("缺少天气预报数据")
        
        if air_quality:
            quality_score += 30
        else:
            issues.append("缺少空气质量数据")
        
        return {
            'score': quality_score,
            'level': 'excellent' if quality_score >= 90 else 'good' if quality_score >= 70 else 'poor',
            'issues': issues
        }
    
    def _get_season(self):
        """获取当前季节"""
        month = datetime.now().month
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'autumn'
    
    def _calculate_temperature_trend(self, forecast):
        """计算温度趋势"""
        if not forecast or not forecast.get('forecasts'):
            return 0
        
        forecasts = forecast['forecasts'][:8]  # 24小时内
        if len(forecasts) < 2:
            return 0
        
        temps = [f['temperature'] for f in forecasts]
        return (temps[-1] - temps[0]) / len(temps)
    
    def _calculate_pressure_trend(self, forecast):
        """计算气压趋势"""
        if not forecast or not forecast.get('forecasts'):
            return 0
        
        forecasts = forecast['forecasts'][:8]
        if len(forecasts) < 2:
            return 0
        
        pressures = [f['pressure'] for f in forecasts]
        return (pressures[-1] - pressures[0]) / len(pressures)
    
    def _calculate_humidity_trend(self, forecast):
        """计算湿度趋势"""
        if not forecast or not forecast.get('forecasts'):
            return 0
        
        forecasts = forecast['forecasts'][:8]
        if len(forecasts) < 2:
            return 0
        
        humidities = [f['humidity'] for f in forecasts]
        return (humidities[-1] - humidities[0]) / len(humidities)

if __name__ == "__main__":
    # 测试用例
    print("🌤️ 天气客户端测试")
    print("=" * 40)
    
    # 注意：需要有效的API密钥才能进行实际测试
    api_key = "your_openweather_api_key_here"
    client = WeatherClient(api_key)
    
    # 测试坐标（伦敦）
    test_lat, test_lon = 51.5074, -0.1278
    
    print(f"📍 测试位置: {test_lat}, {test_lon}")
    print("⚠️ 注意: 需要有效的OpenWeather API密钥才能获取真实数据")
    
    # 模拟数据结构展示
    print("\n📊 数据结构示例:")
    mock_data = {
        'coordinates': {'lat': test_lat, 'lon': test_lon},
        'timestamp': datetime.now().isoformat(),
        'current_weather': {
            'temperature': 15.2,
            'humidity': 65,
            'pressure': 1013,
            'wind_speed': 3.5,
            'weather_description': '多云'
        },
        'air_quality': {
            'aqi': 2,
            'pm2_5': 12,
            'aqi_description': '良好'
        }
    }
    
    print(json.dumps(mock_data, indent=2, ensure_ascii=False))
    
    # 测试ML格式转换
    ml_features = client.format_for_ml_model(mock_data)
    if ml_features:
        print(f"\n🤖 ML特征数量: {len(ml_features)}")
        print(f"主要特征: {list(ml_features.keys())[:10]}")
    
    print("\n✅ 天气客户端测试完成")
