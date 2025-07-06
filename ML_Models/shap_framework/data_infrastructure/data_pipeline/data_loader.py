"""
Data Loader for SHAP Environmental Change Index Framework

Handles loading and preprocessing of environmental data from three UK cities.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
import logging
from dataclasses import dataclass

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DataConfig:
    """Configuration for data loading and processing."""
    base_path: str = "environmental_prediction_framework"
    cities: List[str] = None
    
    def __post_init__(self):
        if self.cities is None:
            self.cities = ["London", "Manchester", "Edinburgh"]

class DataLoader:
    """
    Unified data loader for three UK cities' environmental data.
    
    Handles loading data from:
    - Meteorological climate factors (7 variables)
    - Geospatial topographic factors (4 variables)  
    - Human activities socioeconomic factors (3 variables)
    """
    
    def __init__(self, config: Optional[DataConfig] = None):
        """
        Initialize DataLoader with configuration.
        
        Args:
            config: DataConfig object with loading parameters
        """
        self.config = config or DataConfig()
        self.base_path = Path(self.config.base_path)
        self.cities = self.config.cities
        
        # Data storage
        self.meteorological_data = {}
        self.geospatial_data = {}
        self.socioeconomic_data = {}
        
        # Feature definitions with actual column name mappings
        self.meteorological_features = {
            "temperature": "temperature",
            "humidity": "humidity", 
            "wind_speed": "wind_speed",
            "precipitation": "precipitation",
            "atmospheric_pressure": "atmospheric_pressure",
            "solar_radiation": "evapotranspiration",  # Actual column name in file
            "NO2": "NO2"
        }
        
        self.geospatial_features = {
            "soil_temperature_0_7cm": "soil_temp",  # Actual column name
            "soil_moisture_7_28cm": "soil_moisture",  # Actual column name
            "reference_evapotranspiration": "et0",  # Actual column name
            "urban_flood_risk": "river_discharge_max"  # Actual column name
        }
        
        self.socioeconomic_features = {
            "life_expectancy": "life_expectancy",
            "population_growth_rate": "population_growth_rate",
            "railway_infrastructure": "railway_infrastructure"
        }
        
        logger.info(f"DataLoader initialized for cities: {self.cities}")
    
    def load_meteorological_data(self) -> Dict[str, pd.DataFrame]:
        """
        Load meteorological climate data for all cities.
        
        Returns:
            Dictionary with meteorological data for each city
        """
        logger.info("Loading meteorological climate data...")
        
        # File mappings for meteorological data
        file_mappings = {
            "temperature": "temperature/temperature_data.csv",
            "humidity": "humidity/humidity_data.csv", 
            "wind_speed": "wind_speed/wind_speed_data.csv",
            "precipitation": "precipitation/precipitation_data.csv",
            "atmospheric_pressure": "atmospheric_pressure/pressure_data.csv",
            "solar_radiation": "solar_radiation/evapotranspiration_data.csv",
            "NO2": "NO2/NO2_data.csv"
        }
        
        meteorological_path = self.base_path / "meteorological_climate_factors"
        
        for feature_key, file_path in file_mappings.items():
            full_path = meteorological_path / file_path
            
            if full_path.exists():
                try:
                    df = pd.read_csv(full_path)
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)
                    
                    # Get the actual column name for this feature
                    column_suffix = self.meteorological_features[feature_key]
                    
                    # Store data for each city
                    for city in self.cities:
                        city_col = f"{city}_{column_suffix}"
                        if city_col in df.columns:
                            if city not in self.meteorological_data:
                                self.meteorological_data[city] = {}
                            self.meteorological_data[city][feature_key] = df[city_col]
                    
                    logger.info(f"Loaded {feature_key} data: {len(df)} records")
                    
                except Exception as e:
                    logger.error(f"Error loading {feature_key} data: {str(e)}")
            else:
                logger.warning(f"File not found: {full_path}")
        
        return self.meteorological_data
    
    def load_geospatial_data(self) -> Dict[str, pd.DataFrame]:
        """
        Load geospatial topographic data for all cities.
        
        Returns:
            Dictionary with geospatial data for each city
        """
        logger.info("Loading geospatial topographic data...")
        
        # File mappings for geospatial data
        file_mappings = {
            "soil_temperature_0_7cm": "geology_soil/soil_temperature_0_7cm_data.csv",
            "soil_moisture_7_28cm": "vegetation_water_health/soil_moisture_7_28cm_data.csv",
            "reference_evapotranspiration": "hydrological_network/reference_evapotranspiration_data.csv",
            "urban_flood_risk": "urban_flood_risk/urban_flood_risk_data.csv"
        }
        
        geospatial_path = self.base_path / "geospatial_topographic_factors"
        
        for feature_key, file_path in file_mappings.items():
            full_path = geospatial_path / file_path
            
            if full_path.exists():
                try:
                    df = pd.read_csv(full_path)
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)
                    
                    # Get the actual column name for this feature
                    column_suffix = self.geospatial_features[feature_key]
                    
                    # Store data for each city
                    for city in self.cities:
                        city_col = f"{city}_{column_suffix}"
                        if city_col in df.columns:
                            if city not in self.geospatial_data:
                                self.geospatial_data[city] = {}
                            self.geospatial_data[city][feature_key] = df[city_col]
                    
                    logger.info(f"Loaded {feature_key} data: {len(df)} records")
                    
                except Exception as e:
                    logger.error(f"Error loading {feature_key} data: {str(e)}")
            else:
                logger.warning(f"File not found: {full_path}")
        
        return self.geospatial_data
    
    def load_socioeconomic_data(self) -> Dict[str, pd.DataFrame]:
        """
        Load human activities socioeconomic data for all cities.
        
        Returns:
            Dictionary with socioeconomic data for each city
        """
        logger.info("Loading socioeconomic data...")
        
        # File mappings for socioeconomic data
        file_mappings = {
            "life_expectancy": "life_expectancy/life_expectancy_data.csv",
            "population_growth_rate": "population_distribution/population_growth_rates.csv",
            "railway_infrastructure": "rail_infrastructure/railway_infrastructure_data.csv"
        }
        
        socioeconomic_path = self.base_path / "human_activities_socioeconomic_factors"
        
        for feature_key, file_path in file_mappings.items():
            full_path = socioeconomic_path / file_path
            
            if full_path.exists():
                try:
                    df = pd.read_csv(full_path)
                    
                    # Handle different date formats for socioeconomic data
                    if 'Year' in df.columns:
                        df['date'] = pd.to_datetime(df['Year'], format='%Y')
                    elif 'date' in df.columns:
                        df['date'] = pd.to_datetime(df['date'])
                    
                    df.set_index('date', inplace=True)
                    
                    # Get the actual column name for this feature
                    column_suffix = self.socioeconomic_features[feature_key]
                    
                    # Store data for each city
                    for city in self.cities:
                        city_col = f"{city}_{column_suffix}"
                        if city_col in df.columns:
                            if city not in self.socioeconomic_data:
                                self.socioeconomic_data[city] = {}
                            self.socioeconomic_data[city][feature_key] = df[city_col]
                    
                    logger.info(f"Loaded {feature_key} data: {len(df)} records")
                    
                except Exception as e:
                    logger.error(f"Error loading {feature_key} data: {str(e)}")
            else:
                logger.warning(f"File not found: {full_path}")
        
        return self.socioeconomic_data
    
    def load_all_data(self) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        Load all environmental data for all cities.
        
        Returns:
            Dictionary with all data organized by city and data type
        """
        logger.info("Loading all environmental data...")
        
        # Load all data types
        self.load_meteorological_data()
        self.load_geospatial_data()
        self.load_socioeconomic_data()
        
        # Combine data by city
        all_data = {}
        for city in self.cities:
            all_data[city] = {
                'meteorological': self.meteorological_data.get(city, {}),
                'geospatial': self.geospatial_data.get(city, {}),
                'socioeconomic': self.socioeconomic_data.get(city, {})
            }
        
        logger.info(f"Data loading completed for {len(self.cities)} cities")
        return all_data
    
    def get_city_dataframe(self, city: str) -> pd.DataFrame:
        """
        Get combined dataframe for a specific city.
        
        Args:
            city: City name
            
        Returns:
            Combined dataframe with all features for the city
        """
        if city not in self.cities:
            raise ValueError(f"City {city} not in configured cities: {self.cities}")
        
        # Collect all data for the city
        city_data = []
        
        # Add meteorological data
        if city in self.meteorological_data:
            for feature, series in self.meteorological_data[city].items():
                city_data.append(series.rename(f"meteorological_{feature}"))
        
        # Add geospatial data
        if city in self.geospatial_data:
            for feature, series in self.geospatial_data[city].items():
                city_data.append(series.rename(f"geospatial_{feature}"))
        
        # Add socioeconomic data
        if city in self.socioeconomic_data:
            for feature, series in self.socioeconomic_data[city].items():
                city_data.append(series.rename(f"socioeconomic_{feature}"))
        
        # Combine all data
        if city_data:
            combined_df = pd.concat(city_data, axis=1)
            combined_df.sort_index(inplace=True)
            return combined_df
        else:
            logger.warning(f"No data found for city: {city}")
            return pd.DataFrame()
    
    def get_data_summary(self) -> Dict[str, Dict[str, int]]:
        """
        Get summary statistics of loaded data.
        
        Returns:
            Dictionary with data summary by city and data type
        """
        summary = {}
        
        for city in self.cities:
            summary[city] = {
                'meteorological_features': len(self.meteorological_data.get(city, {})),
                'geospatial_features': len(self.geospatial_data.get(city, {})),
                'socioeconomic_features': len(self.socioeconomic_data.get(city, {}))
            }
        
        return summary 