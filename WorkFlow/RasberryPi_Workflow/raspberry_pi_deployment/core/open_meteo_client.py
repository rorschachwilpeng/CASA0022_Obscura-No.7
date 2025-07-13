#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Open-Meteo Environmental Data Client
Replaces OpenWeather API with Open-Meteo APIs for comprehensive environmental data collection
Supports Historical Weather API + Flood API for complete environmental prediction framework
Uses official openmeteo-requests library with caching and retry mechanisms
"""

import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenMeteoClient:
    """
    Official Open-Meteo API client for comprehensive environmental data collection
    Integrates Historical Weather API and Flood API for SHAP prediction framework
    Uses openmeteo-requests with caching and automatic retry mechanisms
    """
    
    def __init__(self):
        """Initialize Open-Meteo client with official client and caching"""
        # Setup the Open-Meteo API client with cache and retry on error
        cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        self.openmeteo = openmeteo_requests.Client(session=retry_session)
        
        # API endpoints
        self.weather_api_url = "https://archive-api.open-meteo.com/v1/archive"
        self.flood_api_url = "https://flood-api.open-meteo.com/v1/flood"
        
        # Data mapping for environmental_prediction_framework compatibility
        self.data_mapping = {
            # Meteorological Climate Factors
            'temperature': 'temperature_2m',
            'humidity': 'relative_humidity_2m', 
            'wind_speed': 'wind_speed_10m',
            'pressure': 'surface_pressure',
            'solar_radiation': 'shortwave_radiation',
            'precipitation': 'precipitation',
            'sealevel_pressure': 'pressure_msl',
            
            # Geospatial Topographic Factors
            'evapotranspiration': 'et0_fao_evapotranspiration',
            'soil_temperature': 'soil_temperature_0_to_7cm',
            'soil_moisture': 'soil_moisture_7_to_28cm',
            'river_discharge': 'river_discharge_max'
        }
        
        logger.info("✅ Open-Meteo client initialized with caching and retry mechanisms")
        
    def get_current_environmental_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Get current environmental data for specified coordinates
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            
        Returns:
            Dict: Comprehensive environmental data compatible with SHAP framework
        """
        logger.info(f"🌍 Fetching environmental data for coordinates: {lat:.4f}, {lon:.4f}")
        
        try:
            # Get current date for historical data (Open-Meteo has 5-day delay)
            current_date = datetime.now()
            data_date = current_date - timedelta(days=7)  # Use data from 7 days ago
            date_str = data_date.strftime('%Y-%m-%d')
            
            # Fetch weather data and flood data
            logger.info(f"📅 Fetching data for date: {date_str}")
            weather_data = self._fetch_weather_data(lat, lon, date_str)
            flood_data = self._fetch_flood_data(lat, lon, date_str)
            
            # Combine and standardize data
            environmental_data = self._combine_environmental_data(
                weather_data, flood_data, lat, lon, data_date
            )
            
            # Validate data completeness
            data_quality = self._assess_data_quality(environmental_data)
            environmental_data['data_quality'] = data_quality
            
            logger.info(f"✅ Environmental data collection complete. Quality: {data_quality['level']}")
            return environmental_data
            
        except Exception as e:
            logger.error(f"❌ Error fetching environmental data: {e}")
            return self._create_fallback_data(lat, lon)
    
    def _fetch_weather_data(self, lat: float, lon: float, date: str) -> Dict[str, Any]:
        """Fetch meteorological and soil data from Historical Weather API"""
        logger.info("📡 Calling Open-Meteo Historical Weather API...")
        
        try:
            # Define all required weather variables
            hourly_vars = [
                "temperature_2m",
                "relative_humidity_2m", 
                "wind_speed_10m",
                "surface_pressure",
                "shortwave_radiation",
                "precipitation",
                "pressure_msl",
                "soil_temperature_0_to_7cm",
                "soil_moisture_7_to_28cm"
            ]
            
            daily_vars = [
                "et0_fao_evapotranspiration"
            ]
            
            params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": date,
                "end_date": date,
                "hourly": hourly_vars,
                "daily": daily_vars,
                "timezone": "auto"
            }
            
            # Use official openmeteo-requests client
            responses = self.openmeteo.weather_api(self.weather_api_url, params=params)
            
            if responses:
                response = responses[0]
                logger.info(f"✅ Weather data retrieved for {response.Latitude()}°N {response.Longitude()}°E")
                logger.info(f"📍 Elevation: {response.Elevation()} m asl")
                
                # Extract data into pandas-compatible format
                weather_data = {
                    'latitude': response.Latitude(),
                    'longitude': response.Longitude(),
                    'elevation': response.Elevation(),
                    'timezone': response.Timezone() + response.TimezoneAbbreviation(),
                    'utc_offset': response.UtcOffsetSeconds()
                }
                
                # Process hourly data
                if hasattr(response, 'Hourly') and response.Hourly():
                    hourly = response.Hourly()
                    hourly_data = {}
                    
                    for i, var in enumerate(hourly_vars):
                        if hourly.Variables(i):
                            values = hourly.Variables(i).ValuesAsNumpy()
                            hourly_data[var] = values.tolist() if hasattr(values, 'tolist') else list(values)
                    
                    # Create time index for hourly data
                    hourly_times = pd.date_range(
                        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                        freq=pd.Timedelta(seconds=hourly.Interval()),
                        inclusive="left"
                    )
                    
                    weather_data['hourly'] = hourly_data
                    weather_data['hourly_times'] = [t.isoformat() for t in hourly_times]
                
                # Process daily data
                if hasattr(response, 'Daily') and response.Daily():
                    daily = response.Daily()
                    daily_data = {}
                    
                    for i, var in enumerate(daily_vars):
                        if daily.Variables(i):
                            values = daily.Variables(i).ValuesAsNumpy()
                            daily_data[var] = values.tolist() if hasattr(values, 'tolist') else list(values)
                    
                    # Create time index for daily data
                    daily_times = pd.date_range(
                        start=pd.to_datetime(daily.Time(), unit="s", utc=True),
                        end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
                        freq=pd.Timedelta(seconds=daily.Interval()),
                        inclusive="left"
                    )
                    
                    weather_data['daily'] = daily_data
                    weather_data['daily_times'] = [t.isoformat() for t in daily_times]
                
                logger.info("✅ Weather data successfully processed")
                return weather_data
            else:
                logger.warning("⚠️ No weather data received")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Weather API call failed: {e}")
            return {}
    
    def _fetch_flood_data(self, lat: float, lon: float, date: str) -> Dict[str, Any]:
        """Fetch flood/river discharge data from Flood API"""
        logger.info("🌊 Calling Open-Meteo Flood API...")
        
        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": date,
                "end_date": date,
                "daily": "river_discharge_max"
            }
            
            # Use official openmeteo-requests client for flood API
            responses = self.openmeteo.weather_api(self.flood_api_url, params=params)
            
            if responses:
                response = responses[0]
                logger.info(f"✅ Flood data retrieved for {response.Latitude()}°N {response.Longitude()}°E")
                
                flood_data = {
                    'latitude': response.Latitude(),
                    'longitude': response.Longitude(),
                    'elevation': response.Elevation()
                }
                
                # Process daily flood data
                if hasattr(response, 'Daily') and response.Daily():
                    daily = response.Daily()
                    
                    if daily.Variables(0):
                        river_discharge_values = daily.Variables(0).ValuesAsNumpy()
                        
                        # Create time index
                        daily_times = pd.date_range(
                            start=pd.to_datetime(daily.Time(), unit="s", utc=True),
                            end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
                            freq=pd.Timedelta(seconds=daily.Interval()),
                            inclusive="left"
                        )
                        
                        flood_data['daily'] = {
                            'river_discharge_max': river_discharge_values.tolist() if hasattr(river_discharge_values, 'tolist') else list(river_discharge_values)
                        }
                        flood_data['daily_times'] = [t.isoformat() for t in daily_times]
                
                logger.info("✅ Flood data successfully processed")
                return flood_data
            else:
                logger.warning("⚠️ No flood data received")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Flood API call failed: {e}")
            return {}
    
    def _combine_environmental_data(self, weather_data: Dict, flood_data: Dict, 
                                  lat: float, lon: float, timestamp: datetime) -> Dict[str, Any]:
        """Combine weather and flood data into standardized format"""
        logger.info("🔄 Processing and standardizing environmental data...")
        
        # Extract latest hourly weather data
        current_weather = {}
        if weather_data.get('hourly'):
            hourly = weather_data['hourly']
            # Get the last available data point from each variable
            last_idx = -1
            
            current_weather = {
                'temperature': self._safe_get_value(hourly.get('temperature_2m'), last_idx),
                'humidity': self._safe_get_value(hourly.get('relative_humidity_2m'), last_idx),
                'wind_speed': self._safe_get_value(hourly.get('wind_speed_10m'), last_idx),
                'pressure': self._safe_get_value(hourly.get('surface_pressure'), last_idx),
                'solar_radiation': self._safe_get_value(hourly.get('shortwave_radiation'), last_idx),
                'precipitation': self._safe_get_value(hourly.get('precipitation'), last_idx),
                'sealevel_pressure': self._safe_get_value(hourly.get('pressure_msl'), last_idx),
                'soil_temperature_0_to_7cm': self._safe_get_value(hourly.get('soil_temperature_0_to_7cm'), last_idx),
                'soil_moisture_7_to_28cm': self._safe_get_value(hourly.get('soil_moisture_7_to_28cm'), last_idx),
                'weather_description': self._generate_weather_description(
                    self._safe_get_value(hourly.get('temperature_2m'), last_idx),
                    self._safe_get_value(hourly.get('precipitation'), last_idx)
                ),
                'timestamp': timestamp.isoformat()
            }
        
        # Extract daily data
        daily_data = {}
        if weather_data.get('daily'):
            daily = weather_data['daily']
            daily_data = {
                'evapotranspiration': self._safe_get_value(daily.get('et0_fao_evapotranspiration'), 0)
            }
        
        # Extract flood data
        flood_info = {}
        if flood_data.get('daily'):
            flood_daily = flood_data['daily']
            flood_info = {
                'river_discharge_max': self._safe_get_value(flood_daily.get('river_discharge_max'), 0)
            }
        
        # Combine all data in environmental_prediction_framework format
        environmental_data = {
            'coordinates': {'latitude': lat, 'longitude': lon},
            'timestamp': timestamp.isoformat(),
            'data_source': 'open_meteo_official',
            
            # Current weather conditions
            'current_weather': current_weather,
            
            # Meteorological climate factors
            'meteorological_climate_factors': {
                'temperature': current_weather.get('temperature'),
                'humidity': current_weather.get('humidity'),
                'wind_speed': current_weather.get('wind_speed'),
                'atmospheric_pressure': current_weather.get('pressure'),
                'solar_radiation': current_weather.get('solar_radiation'),
                'precipitation': current_weather.get('precipitation'),
                'sealevel_pressure': current_weather.get('sealevel_pressure')
                # NOTE: NO2 not available in Open-Meteo, would need separate Air Quality API
            },
            
            # Geospatial topographic factors
            'geospatial_topographic_factors': {
                'hydrological_network': {
                    'evapotranspiration': daily_data.get('evapotranspiration')
                },
                'geology_soil': {
                    'soil_temperature_0_to_7cm': current_weather.get('soil_temperature_0_to_7cm')
                },
                'vegetation_water_health': {
                    'soil_moisture_7_to_28cm': current_weather.get('soil_moisture_7_to_28cm')
                },
                'urban_flood_risk': {
                    'river_discharge_max': flood_info.get('river_discharge_max')
                }
            },
            
            # Raw API responses for debugging
            '_raw_data': {
                'weather_api_response': weather_data,
                'flood_api_response': flood_data
            }
        }
        
        return environmental_data
    
    def _safe_get_value(self, data_array: Optional[List], index: int) -> Optional[float]:
        """Safely extract value from data array"""
        if data_array and isinstance(data_array, list) and len(data_array) > abs(index):
            value = data_array[index]
            return value if value is not None else 0.0
        return None
    
    def _generate_weather_description(self, temperature: Optional[float], 
                                    precipitation: Optional[float]) -> str:
        """Generate weather description based on conditions"""
        if temperature is None:
            return "unknown conditions"
        
        # Temperature-based description
        if temperature < 0:
            temp_desc = "freezing"
        elif temperature < 10:
            temp_desc = "cold"
        elif temperature < 20:
            temp_desc = "cool"
        elif temperature < 30:
            temp_desc = "warm"
        else:
            temp_desc = "hot"
        
        # Precipitation-based description
        if precipitation is None or precipitation < 0.1:
            precip_desc = "clear"
        elif precipitation < 1.0:
            precip_desc = "light rain"
        elif precipitation < 5.0:
            precip_desc = "moderate rain"
        else:
            precip_desc = "heavy rain"
        
        return f"{precip_desc}, {temp_desc}"
    
    def _assess_data_quality(self, environmental_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess completeness and quality of environmental data"""
        score = 0
        issues = []
        total_fields = 11  # Number of key environmental factors
        
        # Check meteorological factors
        met_factors = environmental_data.get('meteorological_climate_factors', {})
        for factor in ['temperature', 'humidity', 'wind_speed', 'atmospheric_pressure', 
                      'solar_radiation', 'precipitation', 'sealevel_pressure']:
            if met_factors.get(factor) is not None:
                score += 10
            else:
                issues.append(f"Missing {factor}")
        
        # Check geospatial factors
        geo_factors = environmental_data.get('geospatial_topographic_factors', {})
        if geo_factors.get('hydrological_network', {}).get('evapotranspiration') is not None:
            score += 10
        else:
            issues.append("Missing evapotranspiration")
            
        if geo_factors.get('geology_soil', {}).get('soil_temperature_0_to_7cm') is not None:
            score += 10
        else:
            issues.append("Missing soil temperature")
            
        if geo_factors.get('vegetation_water_health', {}).get('soil_moisture_7_to_28cm') is not None:
            score += 10
        else:
            issues.append("Missing soil moisture")
            
        if geo_factors.get('urban_flood_risk', {}).get('river_discharge_max') is not None:
            score += 10
        else:
            issues.append("Missing river discharge data")
        
        # Determine quality level
        if score >= 90:
            level = 'excellent'
        elif score >= 70:
            level = 'good'
        elif score >= 50:
            level = 'acceptable'
        else:
            level = 'poor'
        
        return {
            'score': score,
            'level': level,
            'issues': issues,
            'data_source': 'open_meteo_official',
            'completeness': f"{len([i for i in issues if not i]) + (total_fields - len(issues))}/{total_fields}"
        }
    
    def _create_fallback_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """Create fallback simulated data when APIs fail"""
        logger.warning("⚠️ FALLBACK MODE: Using simulated environmental data")
        
        import random
        timestamp = datetime.now()
        
        # Generate realistic simulated values
        base_temp = 15.0 + random.uniform(-10, 15)  # Base temperature
        
        fallback_data = {
            'coordinates': {'latitude': lat, 'longitude': lon},
            'timestamp': timestamp.isoformat(),
            'data_source': 'simulated_fallback',
            
            'current_weather': {
                'temperature': base_temp,
                'humidity': random.uniform(40, 90),
                'wind_speed': random.uniform(0, 15),
                'pressure': random.uniform(990, 1030),
                'solar_radiation': random.uniform(0, 800) if 6 <= timestamp.hour <= 18 else 0,
                'precipitation': random.uniform(0, 5) if random.random() < 0.3 else 0,
                'sealevel_pressure': random.uniform(1000, 1025),
                'soil_temperature_0_to_7cm': base_temp + random.uniform(-2, 2),
                'soil_moisture_7_to_28cm': random.uniform(10, 40),
                'weather_description': 'simulated conditions',
                'timestamp': timestamp.isoformat()
            },
            
            'meteorological_climate_factors': {
                'temperature': base_temp,
                'humidity': random.uniform(40, 90),
                'wind_speed': random.uniform(0, 15),
                'atmospheric_pressure': random.uniform(990, 1030),
                'solar_radiation': random.uniform(0, 800) if 6 <= timestamp.hour <= 18 else 0,
                'precipitation': random.uniform(0, 5) if random.random() < 0.3 else 0,
                'sealevel_pressure': random.uniform(1000, 1025)
            },
            
            'geospatial_topographic_factors': {
                'hydrological_network': {
                    'evapotranspiration': random.uniform(2, 8)
                },
                'geology_soil': {
                    'soil_temperature_0_to_7cm': base_temp + random.uniform(-2, 2)
                },
                'vegetation_water_health': {
                    'soil_moisture_7_to_28cm': random.uniform(10, 40)
                },
                'urban_flood_risk': {
                    'river_discharge_max': random.uniform(5, 50)
                }
            },
            
            'data_quality': {
                'score': 60,
                'level': 'simulated',
                'issues': ['Using simulated data - API calls failed'],
                'data_source': 'simulated_fallback',
                'completeness': '11/11 (simulated)'
            }
        }
        
        return fallback_data
    
    def format_for_ml_model(self, environmental_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format environmental data for ML model input (SHAP framework compatibility)"""
        logger.info("🤖 Formatting data for ML model input...")
        
        if not environmental_data:
            logger.error("❌ No environmental data to format")
            return {}
        
        current = environmental_data.get('current_weather', {})
        met_factors = environmental_data.get('meteorological_climate_factors', {})
        geo_factors = environmental_data.get('geospatial_topographic_factors', {})
        
        # Create ML-ready feature set
        ml_features = {
            # Basic meteorological features
            'temperature': met_factors.get('temperature', 15.0),
            'humidity': met_factors.get('humidity', 50.0),
            'pressure': met_factors.get('atmospheric_pressure', 1013.0),
            'wind_speed': met_factors.get('wind_speed', 5.0),
            'solar_radiation': met_factors.get('solar_radiation', 200.0),
            'precipitation': met_factors.get('precipitation', 0.0),
            'sealevel_pressure': met_factors.get('sealevel_pressure', 1013.0),
            
            # Soil and environmental features
            'soil_temperature': geo_factors.get('geology_soil', {}).get('soil_temperature_0_to_7cm', 15.0),
            'soil_moisture': geo_factors.get('vegetation_water_health', {}).get('soil_moisture_7_to_28cm', 25.0),
            'evapotranspiration': geo_factors.get('hydrological_network', {}).get('evapotranspiration', 4.0),
            'river_discharge': geo_factors.get('urban_flood_risk', {}).get('river_discharge_max', 20.0),
            
            # Derived features
            'temperature_humidity_index': (met_factors.get('temperature', 15) + met_factors.get('humidity', 50)) / 2,
            'pressure_deviation': met_factors.get('atmospheric_pressure', 1013) - 1013.25,
            'is_precipitation': 1 if met_factors.get('precipitation', 0) > 0.1 else 0,
            
            # Temporal features
            'hour_of_day': datetime.now().hour,
            'day_of_year': datetime.now().timetuple().tm_yday,
            
            # Coordinates
            'latitude': environmental_data.get('coordinates', {}).get('latitude', 0.0),
            'longitude': environmental_data.get('coordinates', {}).get('longitude', 0.0),
            
            # Data quality indicator
            'data_quality_score': environmental_data.get('data_quality', {}).get('score', 60)
        }
        
        logger.info(f"✅ ML features prepared: {len(ml_features)} features")
        return ml_features

# Test and demonstration code
if __name__ == "__main__":
    print("🌍 Open-Meteo Official Environmental Data Client Test")
    print("=" * 60)
    
    # Initialize client
    client = OpenMeteoClient()
    
    # Test coordinates (London, UK)
    test_lat, test_lon = 51.5074, -0.1278
    print(f"📍 Test location: {test_lat}, {test_lon}")
    
    # Fetch environmental data
    print("\n🔄 Fetching comprehensive environmental data...")
    env_data = client.get_current_environmental_data(test_lat, test_lon)
    
    # Display results
    if env_data:
        print(f"\n📊 Data Quality: {env_data.get('data_quality', {}).get('level', 'unknown')}")
        print(f"📈 Quality Score: {env_data.get('data_quality', {}).get('score', 0)}/110")
        
        current = env_data.get('current_weather', {})
        print(f"\n🌡️ Temperature: {current.get('temperature', 'N/A')}°C")
        print(f"💧 Humidity: {current.get('humidity', 'N/A')}%")
        print(f"💨 Wind Speed: {current.get('wind_speed', 'N/A')} m/s")
        print(f"☀️ Solar Radiation: {current.get('solar_radiation', 'N/A')} W/m²")
        
        # Test ML formatting
        print("\n🤖 Testing ML model formatting...")
        ml_features = client.format_for_ml_model(env_data)
        print(f"✅ ML features: {len(ml_features)} parameters ready for SHAP model")
        
        # Display sample features
        sample_features = {k: v for k, v in list(ml_features.items())[:5]}
        for feature, value in sample_features.items():
            print(f"   {feature}: {value}")
    
    print("\n✅ Open-Meteo official client test completed!")
    print("🔗 Ready for integration with SHAP prediction framework") 