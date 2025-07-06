"""
Data Preprocessor for SHAP Environmental Change Index Framework

Handles data preprocessing including outlier detection, missing value imputation,
feature scaling, and time series alignment.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.impute import SimpleImputer, KNNImputer
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PreprocessConfig:
    """Configuration for data preprocessing."""
    scaler_type: str = "standard"  # standard, minmax, robust
    imputation_strategy: str = "median"  # mean, median, mode, constant
    handle_outliers: bool = True
    outlier_threshold: float = 3.0  # Z-score threshold
    time_alignment: str = "inner"  # inner, outer, left
    
class DataPreprocessor:
    """
    Data preprocessor for standardizing environmental data across three cities.
    
    Handles:
    - Data standardization/normalization
    - Missing value imputation
    - Outlier detection and handling
    - Time series alignment
    - Feature scaling
    """
    
    def __init__(self, config: Optional[PreprocessConfig] = None):
        """
        Initialize DataPreprocessor with configuration.
        
        Args:
            config: PreprocessConfig object
        """
        self.config = config or PreprocessConfig()
        
        # Initialize scalers and imputers
        self.scalers = {}
        self.imputers = {}
        self.feature_stats = {}
        
        # Set up scaler class
        if self.config.scaler_type == "standard":
            self.scaler_class = StandardScaler
        elif self.config.scaler_type == "minmax":
            self.scaler_class = MinMaxScaler
        elif self.config.scaler_type == "robust":
            self.scaler_class = RobustScaler
        else:
            raise ValueError(f"Unknown scaler type: {self.config.scaler_type}")
            
        # Environmental constraints for UK cities (reasonable ranges)
        self.environmental_constraints = {
            'meteorological_temperature': (-20, 45),      # °C
            'meteorological_humidity': (0, 100),          # %
            'meteorological_wind_speed': (0, 150),        # km/h
            'meteorological_precipitation': (0, 300),     # mm/month
            'meteorological_atmospheric_pressure': (950, 1050),  # hPa
            'meteorological_solar_radiation': (0, 350),   # W/m²
            'meteorological_NO2': (0, 150),               # μg/m³
            'geospatial_soil_temperature_0_7cm': (-10, 35),  # °C
            'geospatial_soil_moisture_7_28cm': (0, 100),     # %
            'geospatial_reference_evapotranspiration': (0, 250),  # mm/month
            'geospatial_urban_flood_risk': (0, 800),      # m³/s
            'socioeconomic_life_expectancy': (70, 100),   # years
            'socioeconomic_population_growth_rate': (-0.1, 0.1),  # %
            'socioeconomic_railway_infrastructure': (0, 1000)  # index
        }
        
        logger.info(f"DataPreprocessor initialized with {self.config.scaler_type} scaler")
        
    def create_scaler(self, scaler_type: str):
        """Create a scaler instance."""
        if scaler_type == "standard":
            return StandardScaler()
        elif scaler_type == "minmax":
            return MinMaxScaler()
        elif scaler_type == "robust":
            return RobustScaler()
        else:
            raise ValueError(f"Unknown scaler type: {scaler_type}")
    
    def create_imputer(self, strategy: str):
        """Create an imputer instance."""
        if strategy in ['mean', 'median', 'most_frequent', 'constant']:
            return SimpleImputer(strategy=strategy)
        elif strategy == 'knn':
            return KNNImputer()
        else:
            raise ValueError(f"Unknown imputation strategy: {strategy}")
    
    def handle_environmental_outliers(self, data: pd.Series, column_name: str) -> pd.Series:
        """
        Handle outliers specifically for environmental data with domain knowledge.
        
        Args:
            data: Time series data
            column_name: Name of the column/variable
            
        Returns:
            Data with outliers handled
        """
        if column_name not in self.environmental_constraints:
            # Fall back to statistical outlier detection
            return self.handle_outliers(data)
        
        min_val, max_val = self.environmental_constraints[column_name]
        
        # Count violations
        below_min = (data < min_val).sum()
        above_max = (data > max_val).sum()
        
        if below_min > 0 or above_max > 0:
            logger.info(f"Environmental constraint violations in {column_name}: {below_min} below min, {above_max} above max")
            
            # Clip to environmental constraints
            data_cleaned = data.clip(min_val, max_val)
            
            # Additional statistical outlier detection within constraints
            # Check for values that are extreme even within the valid range
            constrained_data = data_cleaned[(data_cleaned >= min_val) & (data_cleaned <= max_val)]
            
            if len(constrained_data) > 10:  # Need sufficient data for statistical analysis
                q1 = constrained_data.quantile(0.25)
                q3 = constrained_data.quantile(0.75)
                iqr = q3 - q1
                
                # Use IQR method for additional outlier detection
                lower_fence = q1 - 1.5 * iqr
                upper_fence = q3 + 1.5 * iqr
                
                # Ensure fences are within environmental constraints
                lower_fence = max(lower_fence, min_val)
                upper_fence = min(upper_fence, max_val)
                
                # Apply additional clipping if needed
                statistical_outliers = ((data_cleaned < lower_fence) | (data_cleaned > upper_fence)).sum()
                if statistical_outliers > 0:
                    logger.info(f"Additional statistical outliers in {column_name}: {statistical_outliers}")
                    data_cleaned = data_cleaned.clip(lower_fence, upper_fence)
            
            return data_cleaned
        
        return data
    
    def detect_outliers(self, data: pd.Series, threshold: float = None) -> pd.Series:
        """
        Detect outliers using Z-score method.
        
        Args:
            data: Time series data
            threshold: Z-score threshold for outlier detection
            
        Returns:
            Boolean series indicating outliers
        """
        if threshold is None:
            threshold = self.config.outlier_threshold
            
        # Calculate Z-scores
        z_scores = np.abs((data - data.mean()) / data.std())
        outliers = z_scores > threshold
        
        if outliers.sum() > 0:
            logger.info(f"Detected {outliers.sum()} outliers (>{threshold} std devs)")
            
        return outliers
    
    def handle_outliers(self, data: pd.Series, method: str = "clip") -> pd.Series:
        """
        Handle outliers in the data.
        
        Args:
            data: Time series data
            method: Handling method - 'clip', 'remove', 'interpolate'
            
        Returns:
            Data with outliers handled
        """
        outliers = self.detect_outliers(data)
        
        if outliers.sum() == 0:
            return data
            
        if method == "clip":
            # Clip to 3 standard deviations
            mean = data.mean()
            std = data.std()
            lower_bound = mean - 3 * std
            upper_bound = mean + 3 * std
            data_cleaned = data.clip(lower_bound, upper_bound)
            
        elif method == "remove":
            # Set outliers to NaN
            data_cleaned = data.copy()
            data_cleaned[outliers] = np.nan
            
        elif method == "interpolate":
            # Interpolate outliers
            data_cleaned = data.copy()
            data_cleaned[outliers] = np.nan
            data_cleaned = data_cleaned.interpolate()
            
        else:
            raise ValueError(f"Unknown outlier handling method: {method}")
            
        logger.info(f"Handled {outliers.sum()} outliers using {method} method")
        return data_cleaned
    
    def impute_missing_values(self, data: pd.DataFrame, strategy: str = None) -> pd.DataFrame:
        """
        Impute missing values in the dataframe.
        
        Args:
            data: DataFrame with missing values
            strategy: Imputation strategy
            
        Returns:
            DataFrame with imputed values
        """
        if strategy is None:
            strategy = self.config.imputation_strategy
            
        # Check for missing values
        missing_count = data.isnull().sum().sum()
        if missing_count == 0:
            logger.info("No missing values found")
            return data
            
        logger.info(f"Imputing {missing_count} missing values using {strategy} strategy")
        
        # Create imputer for each column type
        data_imputed = data.copy()
        
        for column in data.columns:
            if data[column].isnull().sum() > 0:
                # Create column-specific imputer
                column_key = f"{column}_{strategy}"
                if column_key not in self.imputers:
                    self.imputers[column_key] = SimpleImputer(strategy=strategy)
                    
                # Fit and transform
                values = data[column].values.reshape(-1, 1)
                imputed_values = self.imputers[column_key].fit_transform(values)
                data_imputed[column] = imputed_values.flatten()
                
        return data_imputed
    
    def scale_features(self, data: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """
        Scale features using the configured scaler.
        
        Args:
            data: DataFrame to scale
            fit: Whether to fit the scaler or use existing fit
            
        Returns:
            Scaled DataFrame
        """
        logger.info(f"Scaling features using {self.config.scaler_type} scaler")
        
        data_scaled = data.copy()
        
        for column in data.columns:
            # Create column-specific scaler
            if column not in self.scalers:
                self.scalers[column] = self.scaler_class()
                
            values = data[column].values.reshape(-1, 1)
            
            if fit:
                scaled_values = self.scalers[column].fit_transform(values)
                # Store feature statistics
                self.feature_stats[column] = {
                    'mean': data[column].mean(),
                    'std': data[column].std(),
                    'min': data[column].min(),
                    'max': data[column].max()
                }
            else:
                scaled_values = self.scalers[column].transform(values)
                
            data_scaled[column] = scaled_values.flatten()
            
        return data_scaled
    
    def align_time_series(self, city_dataframes: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Align time series data across cities.
        
        Args:
            city_dataframes: Dictionary of DataFrames by city
            
        Returns:
            Dictionary of aligned DataFrames
        """
        logger.info("Aligning time series data across cities")
        
        if not city_dataframes:
            return {}
            
        # Find common time range
        date_ranges = []
        for city, df in city_dataframes.items():
            if not df.empty:
                date_ranges.append((df.index.min(), df.index.max()))
                
        if not date_ranges:
            logger.warning("No valid date ranges found")
            return city_dataframes
            
        # Determine alignment strategy
        if self.config.time_alignment == "inner":
            # Use intersection of all date ranges
            common_start = max([dr[0] for dr in date_ranges])
            common_end = min([dr[1] for dr in date_ranges])
        elif self.config.time_alignment == "outer":
            # Use union of all date ranges
            common_start = min([dr[0] for dr in date_ranges])
            common_end = max([dr[1] for dr in date_ranges])
        else:
            # Use first city's range as reference
            first_city = list(city_dataframes.keys())[0]
            common_start = city_dataframes[first_city].index.min()
            common_end = city_dataframes[first_city].index.max()
            
        logger.info(f"Common time range: {common_start} to {common_end}")
        
        # Align all DataFrames to common time range
        aligned_dataframes = {}
        for city, df in city_dataframes.items():
            if not df.empty:
                # Filter to common time range
                aligned_df = df.loc[common_start:common_end].copy()
                aligned_dataframes[city] = aligned_df
                logger.info(f"{city}: {len(aligned_df)} records after alignment")
            else:
                aligned_dataframes[city] = df
                
        return aligned_dataframes
    
    def preprocess_city_data(self, city_data: pd.DataFrame, city_name: str, 
                           fit_scalers: bool = True) -> pd.DataFrame:
        """
        Preprocess data for a single city.
        
        Args:
            city_data: DataFrame for the city
            city_name: Name of the city
            fit_scalers: Whether to fit scalers or use existing
            
        Returns:
            Preprocessed DataFrame
        """
        logger.info(f"Preprocessing data for {city_name}")
        
        if city_data.empty:
            logger.warning(f"Empty DataFrame for {city_name}")
            return city_data
            
        # Make a copy to avoid modifying original data
        processed_data = city_data.copy()
        
        # Step 1: Handle outliers using environmental constraints
        if self.config.handle_outliers:
            for column in processed_data.columns:
                if processed_data[column].dtype in ['float64', 'int64']:
                    processed_data[column] = self.handle_environmental_outliers(
                        processed_data[column], column
                    )
        
        # Step 2: Impute missing values
        processed_data = self.impute_missing_values(processed_data)
        
        # Step 3: Scale features
        processed_data = self.scale_features(processed_data, fit=fit_scalers)
        
        logger.info(f"Preprocessing completed for {city_name}: {processed_data.shape}")
        return processed_data
    
    def preprocess_all_cities(self, city_dataframes: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Preprocess data for all cities.
        
        Args:
            city_dataframes: Dictionary of DataFrames by city
            
        Returns:
            Dictionary of preprocessed DataFrames
        """
        logger.info("Starting preprocessing for all cities")
        
        # Step 1: Align time series
        aligned_data = self.align_time_series(city_dataframes)
        
        # Step 2: Fit scalers using all cities' data for global consistency
        self._fit_global_scalers(aligned_data)
        
        # Step 3: Preprocess each city using the global scalers
        preprocessed_data = {}
        for city, df in aligned_data.items():
            # All cities use the same fitted scalers
            preprocessed_data[city] = self.preprocess_city_data(
                df, city, fit_scalers=False
            )
            
        logger.info("Preprocessing completed for all cities")
        return preprocessed_data
    
    def _fit_global_scalers(self, city_dataframes: Dict[str, pd.DataFrame]):
        """
        Fit scalers using data from all cities for global consistency.
        
        Args:
            city_dataframes: Dictionary of aligned DataFrames by city
        """
        logger.info("Fitting global scalers using all cities' data")
        
        if not city_dataframes:
            return
            
        # Process each column independently for better control
        for column in city_dataframes[list(city_dataframes.keys())[0]].columns:
            if any(df[column].dtype in ['float64', 'int64'] for df in city_dataframes.values()):
                # Collect all valid (non-missing) values for this column across all cities
                all_values = []
                for city, df in city_dataframes.items():
                    if not df.empty and column in df.columns:
                        # Handle outliers first
                        if self.config.handle_outliers:
                            clean_data = self.handle_environmental_outliers(df[column], column)
                        else:
                            clean_data = df[column]
                        
                        # Only use non-missing values for fitting
                        valid_values = clean_data.dropna()
                        if len(valid_values) > 0:
                            all_values.extend(valid_values.tolist())
                
                if len(all_values) > 0:
                    # Convert to array for processing
                    combined_values = np.array(all_values)
                    
                    # Fit imputer with a strategy that works for this column
                    imputer = self.create_imputer(self.config.imputation_strategy)
                    
                    # Use the median of all valid values as the fill value
                    fill_value = np.median(combined_values)
                    
                    # Create a simple imputer with the calculated fill value
                    if self.config.imputation_strategy == 'constant':
                        imputer = SimpleImputer(strategy='constant', fill_value=fill_value)
                    else:
                        # For other strategies, fit on combined valid data
                        imputer.fit(combined_values.reshape(-1, 1))
                    
                    self.imputers[column] = imputer
                    
                    # Fit scaler on the combined valid data
                    scaler = self.create_scaler(self.config.scaler_type)
                    scaler.fit(combined_values.reshape(-1, 1))
                    self.scalers[column] = scaler
                    
                    # Store global statistics
                    self.feature_stats[column] = {
                        'mean': np.mean(combined_values),
                        'std': np.std(combined_values),
                        'min': np.min(combined_values),
                        'max': np.max(combined_values),
                        'valid_samples': len(combined_values),
                        'fill_value': fill_value
                    }
                    
                    logger.info(f"Fitted {column}: {len(combined_values)} valid samples, fill_value={fill_value:.4f}")
                
        logger.info(f"Global scalers fitted for {len(self.scalers)} features")
    
    def get_preprocessing_summary(self) -> Dict:
        """
        Get summary of preprocessing operations.
        
        Returns:
            Dictionary with preprocessing statistics
        """
        summary = {
            'config': {
                'scaler_type': self.config.scaler_type,
                'imputation_strategy': self.config.imputation_strategy,
                'outlier_handling': self.config.handle_outliers,
                'time_alignment': self.config.time_alignment
            },
            'scalers_fitted': len(self.scalers),
            'imputers_created': len(self.imputers),
            'feature_statistics': self.feature_stats
        }
        
        return summary
    
    def save_preprocessor_state(self, file_path: str):
        """
        Save the preprocessor state for later use.
        
        Args:
            file_path: Path to save the state
        """
        import pickle
        
        state = {
            'config': self.config,
            'scalers': self.scalers,
            'imputers': self.imputers,
            'feature_stats': self.feature_stats
        }
        
        with open(file_path, 'wb') as f:
            pickle.dump(state, f)
            
        logger.info(f"Preprocessor state saved to {file_path}")
    
    def load_preprocessor_state(self, file_path: str):
        """
        Load preprocessor state from file.
        
        Args:
            file_path: Path to load the state from
        """
        import pickle
        
        with open(file_path, 'rb') as f:
            state = pickle.load(f)
            
        self.config = state['config']
        self.scalers = state['scalers']
        self.imputers = state['imputers']
        self.feature_stats = state['feature_stats']
        
        logger.info(f"Preprocessor state loaded from {file_path}") 