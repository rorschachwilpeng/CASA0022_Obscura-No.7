"""
Feature Engineering Pipeline for SHAP Environmental Change Index Framework

Handles feature engineering for time series environmental data.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
from sklearn.preprocessing import PolynomialFeatures
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest, f_regression
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FeatureEngineeringConfig:
    """Configuration for feature engineering."""
    # Time-based features
    create_time_features: bool = True
    create_lag_features: bool = True
    lag_periods: List[int] = None
    
    # Moving averages
    create_moving_averages: bool = True
    ma_windows: List[int] = None
    
    # Seasonal decomposition
    create_seasonal_features: bool = True
    seasonal_periods: List[int] = None
    
    # Polynomial features
    create_polynomial_features: bool = False
    poly_degree: int = 2
    
    # Feature selection
    apply_feature_selection: bool = True
    max_features: int = 50
    
    # Trend analysis
    create_trend_features: bool = True
    trend_window: int = 12
    
    def __post_init__(self):
        if self.lag_periods is None:
            self.lag_periods = [1, 3, 6, 12]  # 1, 3, 6, 12 months
        if self.ma_windows is None:
            self.ma_windows = [3, 6, 12]  # 3, 6, 12 months
        if self.seasonal_periods is None:
            self.seasonal_periods = [12]  # Annual seasonality

class FeatureEngineer:
    """
    Feature engineering pipeline for environmental time series data.
    
    Creates various types of features:
    - Time-based features (month, quarter, season)
    - Lag features (previous values)
    - Moving averages
    - Seasonal decomposition
    - Trend analysis
    - Polynomial features
    """
    
    def __init__(self, config: Optional[FeatureEngineeringConfig] = None):
        """
        Initialize FeatureEngineer with configuration.
        
        Args:
            config: FeatureEngineeringConfig object
        """
        self.config = config or FeatureEngineeringConfig()
        self.feature_names = []
        self.feature_importance = {}
        self.feature_selector = None
        
        logger.info("FeatureEngineer initialized")
    
    def create_time_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create time-based features from datetime index.
        
        Args:
            data: DataFrame with datetime index
            
        Returns:
            DataFrame with additional time features
        """
        if not self.config.create_time_features:
            return data
            
        logger.info("Creating time-based features")
        
        # Make a copy to avoid modifying original
        data_with_time = data.copy()
        
        # Extract time components
        data_with_time['year'] = data_with_time.index.year
        data_with_time['month'] = data_with_time.index.month
        data_with_time['quarter'] = data_with_time.index.quarter
        data_with_time['day_of_year'] = data_with_time.index.dayofyear
        
        # Create cyclical features for month (sine/cosine encoding)
        data_with_time['month_sin'] = np.sin(2 * np.pi * data_with_time['month'] / 12)
        data_with_time['month_cos'] = np.cos(2 * np.pi * data_with_time['month'] / 12)
        
        # Create season indicator
        data_with_time['season'] = data_with_time['month'].apply(self._get_season)
        
        # Create season dummy variables
        for season in ['Spring', 'Summer', 'Autumn', 'Winter']:
            data_with_time[f'season_{season}'] = (data_with_time['season'] == season).astype(int)
        
        # Remove the string season column
        data_with_time = data_with_time.drop('season', axis=1)
        
        time_features = ['year', 'month', 'quarter', 'day_of_year', 'month_sin', 'month_cos',
                        'season_Spring', 'season_Summer', 'season_Autumn', 'season_Winter']
        
        logger.info(f"Created {len(time_features)} time-based features")
        return data_with_time
    
    def _get_season(self, month: int) -> str:
        """Get season from month number."""
        if month in [12, 1, 2]:
            return 'Winter'
        elif month in [3, 4, 5]:
            return 'Spring'
        elif month in [6, 7, 8]:
            return 'Summer'
        else:
            return 'Autumn'
    
    def create_lag_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create lag features for time series data.
        
        Args:
            data: DataFrame with time series data
            
        Returns:
            DataFrame with lag features
        """
        if not self.config.create_lag_features:
            return data
            
        logger.info(f"Creating lag features with periods: {self.config.lag_periods}")
        
        data_with_lags = data.copy()
        
        # Get original feature columns (exclude already created time features)
        original_features = [col for col in data.columns 
                           if not col.startswith(('year', 'month', 'quarter', 'day_of_year', 
                                                'month_sin', 'month_cos', 'season_'))]
        
        # Create lag features
        for lag_period in self.config.lag_periods:
            for col in original_features:
                lag_col_name = f"{col}_lag_{lag_period}"
                data_with_lags[lag_col_name] = data[col].shift(lag_period)
        
        lag_features_count = len(original_features) * len(self.config.lag_periods)
        logger.info(f"Created {lag_features_count} lag features")
        
        return data_with_lags
    
    def create_moving_averages(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create moving average features.
        
        Args:
            data: DataFrame with time series data
            
        Returns:
            DataFrame with moving average features
        """
        if not self.config.create_moving_averages:
            return data
            
        logger.info(f"Creating moving averages with windows: {self.config.ma_windows}")
        
        data_with_ma = data.copy()
        
        # Get original feature columns
        original_features = [col for col in data.columns 
                           if not col.startswith(('year', 'month', 'quarter', 'day_of_year', 
                                                'month_sin', 'month_cos', 'season_')) 
                           and '_lag_' not in col]
        
        # Create moving averages
        for window in self.config.ma_windows:
            for col in original_features:
                ma_col_name = f"{col}_ma_{window}"
                data_with_ma[ma_col_name] = data[col].rolling(window=window).mean()
        
        ma_features_count = len(original_features) * len(self.config.ma_windows)
        logger.info(f"Created {ma_features_count} moving average features")
        
        return data_with_ma
    
    def create_trend_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create trend-based features.
        
        Args:
            data: DataFrame with time series data
            
        Returns:
            DataFrame with trend features
        """
        if not self.config.create_trend_features:
            return data
            
        logger.info(f"Creating trend features with window: {self.config.trend_window}")
        
        data_with_trend = data.copy()
        
        # Get original feature columns
        original_features = [col for col in data.columns 
                           if not col.startswith(('year', 'month', 'quarter', 'day_of_year', 
                                                'month_sin', 'month_cos', 'season_')) 
                           and '_lag_' not in col and '_ma_' not in col]
        
        # Create trend features
        for col in original_features:
            # Linear trend (slope over rolling window)
            trend_col_name = f"{col}_trend_{self.config.trend_window}"
            data_with_trend[trend_col_name] = data[col].rolling(window=self.config.trend_window).apply(
                lambda x: self._calculate_trend(x), raw=False
            )
            
            # Change from previous period
            change_col_name = f"{col}_change"
            data_with_trend[change_col_name] = data[col].pct_change()
            
            # Cumulative change
            cumchange_col_name = f"{col}_cumchange"
            data_with_trend[cumchange_col_name] = data[col].pct_change().cumsum()
        
        trend_features_count = len(original_features) * 3  # trend, change, cumchange
        logger.info(f"Created {trend_features_count} trend features")
        
        return data_with_trend
    
    def _calculate_trend(self, series: pd.Series) -> float:
        """Calculate linear trend (slope) of a time series."""
        if len(series) < 2:
            return 0.0
        
        x = np.arange(len(series))
        y = series.values
        
        # Remove NaN values
        mask = ~np.isnan(y)
        if mask.sum() < 2:
            return 0.0
            
        x_clean = x[mask]
        y_clean = y[mask]
        
        # Calculate slope
        slope = np.polyfit(x_clean, y_clean, 1)[0]
        return slope
    
    def create_seasonal_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create seasonal decomposition features.
        
        Args:
            data: DataFrame with time series data
            
        Returns:
            DataFrame with seasonal features
        """
        if not self.config.create_seasonal_features:
            return data
            
        logger.info(f"Creating seasonal features with periods: {self.config.seasonal_periods}")
        
        data_with_seasonal = data.copy()
        
        # Get original feature columns
        original_features = [col for col in data.columns 
                           if not col.startswith(('year', 'month', 'quarter', 'day_of_year', 
                                                'month_sin', 'month_cos', 'season_')) 
                           and '_lag_' not in col and '_ma_' not in col 
                           and '_trend_' not in col and '_change' not in col]
        
        # Create seasonal features
        for period in self.config.seasonal_periods:
            for col in original_features:
                # Seasonal mean (mean value for the same period in previous cycles)
                seasonal_col_name = f"{col}_seasonal_{period}"
                data_with_seasonal[seasonal_col_name] = data[col].rolling(window=period).mean()
                
                # Seasonal deviation (difference from seasonal mean)
                seasonal_dev_col_name = f"{col}_seasonal_dev_{period}"
                data_with_seasonal[seasonal_dev_col_name] = (
                    data[col] - data_with_seasonal[seasonal_col_name]
                )
        
        seasonal_features_count = len(original_features) * len(self.config.seasonal_periods) * 2
        logger.info(f"Created {seasonal_features_count} seasonal features")
        
        return data_with_seasonal
    
    def create_interaction_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create interaction features between meteorological and geospatial variables.
        
        Args:
            data: DataFrame with features
            
        Returns:
            DataFrame with interaction features
        """
        logger.info("Creating interaction features")
        
        data_with_interactions = data.copy()
        
        # Get meteorological and geospatial features
        meteorological_features = [col for col in data.columns if col.startswith('meteorological_')]
        geospatial_features = [col for col in data.columns if col.startswith('geospatial_')]
        
        # Create interactions between meteorological and geospatial features
        interaction_count = 0
        for met_feature in meteorological_features:
            for geo_feature in geospatial_features:
                # Only create interactions for original features (not derived)
                if ('_lag_' not in met_feature and '_ma_' not in met_feature and 
                    '_trend_' not in met_feature and '_change' not in met_feature and
                    '_seasonal_' not in met_feature and
                    '_lag_' not in geo_feature and '_ma_' not in geo_feature and 
                    '_trend_' not in geo_feature and '_change' not in geo_feature and
                    '_seasonal_' not in geo_feature):
                    
                    interaction_name = f"{met_feature}_{geo_feature}_interaction"
                    data_with_interactions[interaction_name] = (
                        data[met_feature] * data[geo_feature]
                    )
                    interaction_count += 1
        
        logger.info(f"Created {interaction_count} interaction features")
        return data_with_interactions
    
    def apply_feature_selection(self, data: pd.DataFrame, target: pd.Series) -> pd.DataFrame:
        """
        Apply feature selection to reduce dimensionality.
        
        Args:
            data: DataFrame with features
            target: Target variable
            
        Returns:
            DataFrame with selected features
        """
        if not self.config.apply_feature_selection:
            return data
            
        logger.info(f"Applying feature selection to keep top {self.config.max_features} features")
        
        # Remove rows with NaN target values
        mask = ~target.isna()
        data_clean = data.loc[mask].copy()
        target_clean = target.loc[mask]
        
        # Remove features with too many NaN values
        nan_threshold = 0.5  # Remove features with >50% NaN values
        features_to_keep = []
        for col in data_clean.columns:
            if data_clean[col].isna().sum() / len(data_clean) < nan_threshold:
                features_to_keep.append(col)
        
        data_filtered = data_clean[features_to_keep]
        
        # Fill remaining NaN values with median
        data_filtered = data_filtered.fillna(data_filtered.median())
        
        # Apply feature selection
        if len(features_to_keep) > self.config.max_features:
            selector = SelectKBest(score_func=f_regression, k=self.config.max_features)
            data_selected = selector.fit_transform(data_filtered, target_clean)
            
            # Get selected feature names
            selected_features = [features_to_keep[i] for i in selector.get_support(indices=True)]
            
            # Create DataFrame with selected features
            data_final = pd.DataFrame(data_selected, index=data_filtered.index, columns=selected_features)
            
            # Store feature importance scores
            self.feature_importance = dict(zip(features_to_keep, selector.scores_))
            self.feature_selector = selector
            
            logger.info(f"Selected {len(selected_features)} features from {len(features_to_keep)}")
        else:
            data_final = data_filtered
            logger.info(f"Kept all {len(features_to_keep)} features (below max_features threshold)")
        
        return data_final
    
    def engineer_features(self, data: pd.DataFrame, target: Optional[pd.Series] = None) -> pd.DataFrame:
        """
        Apply complete feature engineering pipeline.
        
        Args:
            data: Input DataFrame
            target: Target variable (for feature selection)
            
        Returns:
            DataFrame with engineered features
        """
        logger.info("Starting feature engineering pipeline")
        
        # Step 1: Create time-based features
        data_engineered = self.create_time_features(data)
        
        # Step 2: Create lag features
        data_engineered = self.create_lag_features(data_engineered)
        
        # Step 3: Create moving averages
        data_engineered = self.create_moving_averages(data_engineered)
        
        # Step 4: Create trend features
        data_engineered = self.create_trend_features(data_engineered)
        
        # Step 5: Create seasonal features
        data_engineered = self.create_seasonal_features(data_engineered)
        
        # Step 6: Create interaction features
        data_engineered = self.create_interaction_features(data_engineered)
        
        # Step 7: Handle missing values with time series interpolation
        data_engineered = self._interpolate_time_series_nans(data_engineered)
        
        # Step 8: Apply feature selection (if target is provided)
        if target is not None:
            data_engineered = self.apply_feature_selection(data_engineered, target)
        
        # Store feature names
        self.feature_names = list(data_engineered.columns)
        
        logger.info(f"Feature engineering completed: {len(self.feature_names)} features created")
        return data_engineered
    
    def get_feature_summary(self) -> Dict:
        """
        Get summary of feature engineering process.
        
        Returns:
            Dictionary with feature engineering statistics
        """
        summary = {
            'config': {
                'time_features': self.config.create_time_features,
                'lag_features': self.config.create_lag_features,
                'moving_averages': self.config.create_moving_averages,
                'trend_features': self.config.create_trend_features,
                'seasonal_features': self.config.create_seasonal_features,
                'feature_selection': self.config.apply_feature_selection
            },
            'total_features': len(self.feature_names),
            'feature_names': self.feature_names,
            'feature_importance': self.feature_importance
        }
        
        return summary 

    def _interpolate_time_series_nans(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        处理时序数据中的缺失值，使用线性插值和前后平均。
        
        Args:
            data: 包含NaN值的DataFrame
            
        Returns:
            处理后的DataFrame
        """
        logger.info("处理特征工程产生的缺失值...")
        
        data_filled = data.copy()
        
        # 首先统计每列的NaN数量
        nan_counts_before = data_filled.isna().sum()
        total_nans_before = nan_counts_before.sum()
        
        if total_nans_before == 0:
            logger.info("没有发现缺失值")
            return data_filled
        
        logger.info(f"发现 {total_nans_before} 个缺失值，开始插值处理...")
        
        # 对每一列进行时序插值
        for col in data_filled.columns:
            if data_filled[col].isna().any():
                # 方法1: 线性插值 (对时序数据最有效)
                data_filled[col] = data_filled[col].interpolate(method='linear')
                
                # 方法2: 对于开头和结尾仍然是NaN的，用前向和后向填充
                if data_filled[col].isna().any():
                    # 前向填充 (用前一个有效值填充)
                    data_filled[col] = data_filled[col].ffill()
                    
                    # 后向填充 (用后一个有效值填充)
                    if data_filled[col].isna().any():
                        data_filled[col] = data_filled[col].bfill()
                
                # 方法3: 如果还有NaN（整列都是NaN的情况），用列的中位数填充
                if data_filled[col].isna().any():
                    median_value = data_filled[col].median()
                    if pd.isna(median_value):
                        # 如果中位数也是NaN，用0填充
                        data_filled[col] = data_filled[col].fillna(0)
                    else:
                        data_filled[col] = data_filled[col].fillna(median_value)
        
        # 检查结果
        nan_counts_after = data_filled.isna().sum()
        total_nans_after = nan_counts_after.sum()
        
        logger.info(f"缺失值处理完成: {total_nans_before} → {total_nans_after}")
        
        if total_nans_after > 0:
            logger.warning(f"仍有 {total_nans_after} 个缺失值未能处理")
            # 显示哪些列还有缺失值
            remaining_nans = nan_counts_after[nan_counts_after > 0]
            if len(remaining_nans) > 0:
                logger.warning(f"剩余缺失值分布: {dict(remaining_nans.head(10))}")
        
        return data_filled 