"""
Climate Model for SHAP Environmental Change Index Framework

Predicts Climate Score from meteorological variables (temperature, humidity, wind speed, 
precipitation, atmospheric pressure, solar radiation, NO2).
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
import logging
from .time_series_predictor import TimeSeriesPredictor, ModelConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClimateModel(TimeSeriesPredictor):
    """
    Climate Model for predicting Climate Score from meteorological variables.
    
    Uses 7 meteorological variables:
    - Temperature
    - Humidity  
    - Wind Speed
    - Precipitation
    - Atmospheric Pressure
    - Solar Radiation
    - NO2 concentration
    """
    
    def __init__(self, city: str, config: Optional[ModelConfig] = None):
        """
        Initialize ClimateModel.
        
        Args:
            city: City name (London, Manchester, Edinburgh)
            config: ModelConfig object
        """
        # Default configuration for climate models
        default_config = ModelConfig(
            algorithm="random_forest",
            target_variable="meteorological_temperature",  # Primary climate indicator
            feature_selection=True,
            max_features=15,
            validation_splits=5,
            hyperparameters={
                'n_estimators': 150,
                'max_depth': 10,
                'min_samples_split': 5,
                'min_samples_leaf': 2
            }
        )
        
        # Override with provided config
        if config:
            for key, value in config.__dict__.items():
                if value is not None:
                    setattr(default_config, key, value)
        
        super().__init__(config=default_config, city=city, model_type="climate")
        
        # Climate-specific variables
        self.climate_variables = [
            'meteorological_temperature',
            'meteorological_humidity', 
            'meteorological_wind_speed',
            'meteorological_precipitation',
            'meteorological_atmospheric_pressure',
            'meteorological_solar_radiation',
            'meteorological_NO2'
        ]
        
        # Historical baseline for score calculation
        self.baseline_stats = {}
        
        logger.info(f"ClimateModel initialized for {city}")
    
    def prepare_features(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare features and target for climate prediction.
        
        Args:
            data: Input DataFrame with environmental data
            
        Returns:
            Tuple of (features, target)
        """
        # Extract climate features
        available_climate_vars = [var for var in self.climate_variables if var in data.columns]
        
        if not available_climate_vars:
            raise ValueError(f"No climate variables found in data. Expected: {self.climate_variables}")
        
        logger.info(f"Using {len(available_climate_vars)} climate variables: {available_climate_vars}")
        
        # Features: all available variables except the target
        target_var = self.config.target_variable
        if target_var not in available_climate_vars:
            # Default to temperature if target not available
            target_var = 'meteorological_temperature'
            if target_var not in available_climate_vars:
                target_var = available_climate_vars[0]
        
        feature_vars = [var for var in available_climate_vars if var != target_var]
        
        # Add time-based features if they exist (sorted for consistency)
        time_features = sorted([col for col in data.columns if any(time_term in col.lower() for time_term in 
                        ['year', 'month', 'quarter', 'season', 'day', 'time'])])
        
        # Add lag and trend features if they exist (sorted for consistency)
        lag_features = sorted([col for col in data.columns if 'lag_' in col.lower()])
        trend_features = sorted([col for col in data.columns if any(trend_term in col.lower() for trend_term in 
                         ['trend', 'slope', 'change', 'ma_', 'moving'])])
        
        # Add interaction features for climate variables (sorted for consistency)
        interaction_features = sorted([col for col in data.columns if 'interaction' in col.lower() and 
                              any(climate_var.split('_')[-1] in col for climate_var in self.climate_variables)])
        
        # Combine all features in a consistent order
        all_features = feature_vars + time_features + lag_features + trend_features + interaction_features
        available_features = [feat for feat in all_features if feat in data.columns]
        
        # Ensure consistent ordering by sorting the final feature list
        available_features = sorted(available_features)
        
        X = data[available_features].copy()
        y = data[target_var].copy()
        
        # Store target variable name
        self.target_name = target_var
        
        logger.info(f"Prepared features: {len(X.columns)} features, target: {target_var}")
        logger.info(f"Feature categories: {len(feature_vars)} climate, {len(time_features)} time, "
                   f"{len(lag_features)} lag, {len(trend_features)} trend, {len(interaction_features)} interaction")
        
        return X, y
    
    def calculate_baseline_stats(self, historical_data: pd.DataFrame):
        """
        Calculate baseline statistics from historical data for score calculation.
        
        Args:
            historical_data: Historical environmental data
        """
        logger.info("Calculating baseline statistics for Climate Score")
        
        self.baseline_stats = {}
        
        # Calculate baseline for each climate variable
        for var in self.climate_variables:
            if var in historical_data.columns:
                var_data = historical_data[var].dropna()
                if len(var_data) > 0:
                    self.baseline_stats[var] = {
                        'mean': var_data.mean(),
                        'std': var_data.std(),
                        'median': var_data.median(),
                        'q25': var_data.quantile(0.25),
                        'q75': var_data.quantile(0.75),
                        'min': var_data.min(),
                        'max': var_data.max()
                    }
        
        # Calculate overall climate baseline (using temperature as primary indicator)
        primary_var = self.config.target_variable
        if primary_var in self.baseline_stats:
            self.baseline_stats['overall'] = self.baseline_stats[primary_var].copy()
        elif 'meteorological_temperature' in self.baseline_stats:
            self.baseline_stats['overall'] = self.baseline_stats['meteorological_temperature'].copy()
        else:
            # Use first available variable
            first_var = next(iter(self.baseline_stats.keys()))
            self.baseline_stats['overall'] = self.baseline_stats[first_var].copy()
        
        logger.info(f"Baseline statistics calculated for {len(self.baseline_stats)} variables")
    
    def calculate_score(self, predictions: np.ndarray, baseline_stats: Optional[Dict[str, float]] = None) -> float:
        """
        Calculate Climate Score from model predictions.
        
        Climate Score = (predicted_mean - baseline_mean) / baseline_std
        
        Args:
            predictions: Model predictions for climate variable
            baseline_stats: Historical baseline statistics (optional, uses stored if not provided)
            
        Returns:
            Climate Score (standardized change from baseline)
        """
        if baseline_stats is None:
            if not self.baseline_stats or 'overall' not in self.baseline_stats:
                logger.warning("No baseline statistics available, using simple mean")
                return float(np.mean(predictions))
            baseline_stats = self.baseline_stats['overall']
        
        # Calculate predicted mean
        predicted_mean = np.mean(predictions)
        
        # Calculate standardized score
        baseline_mean = baseline_stats.get('mean', 0)
        baseline_std = baseline_stats.get('std', 1)
        
        if baseline_std == 0:
            logger.warning("Baseline standard deviation is 0, using unstandardized score")
            climate_score = predicted_mean - baseline_mean
        else:
            climate_score = (predicted_mean - baseline_mean) / baseline_std
        
        logger.info(f"Climate Score calculated: {climate_score:.4f} "
                   f"(predicted: {predicted_mean:.4f}, baseline: {baseline_mean:.4f})")
        
        return float(climate_score)
    
    def predict_climate_score(self, features: pd.DataFrame, 
                            time_horizon: Optional[int] = None) -> Dict[str, Any]:
        """
        Predict Climate Score for given features.
        
        Args:
            features: Input features
            time_horizon: Number of time steps to predict (optional)
            
        Returns:
            Dictionary with predictions and Climate Score
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Generate predictions
        predictions = self.predict(features)
        
        # Calculate Climate Score
        climate_score = self.calculate_score(predictions)
        
        # Calculate confidence metrics
        if hasattr(self.model, 'predict') and len(predictions) > 1:
            prediction_std = np.std(predictions)
            prediction_range = np.max(predictions) - np.min(predictions)
        else:
            prediction_std = 0.0
            prediction_range = 0.0
        
        result = {
            'climate_score': climate_score,
            'predictions': predictions,
            'prediction_mean': np.mean(predictions),
            'prediction_std': prediction_std,
            'prediction_range': prediction_range,
            'confidence_score': max(0, 1 - prediction_std / (self.baseline_stats.get('overall', {}).get('std', 1) + 1e-8)),
            'target_variable': self.target_name,
            'feature_count': len(features.columns),
            'sample_count': len(predictions)
        }
        
        logger.info(f"Climate Score prediction completed: {climate_score:.4f}")
        
        return result
    
    def analyze_climate_factors(self, features: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze climate factor contributions to the prediction.
        
        Args:
            features: Input features
            
        Returns:
            Analysis of climate factor contributions
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before analysis")
        
        # Get feature importance
        climate_importance = {}
        for feature, importance in self.feature_importance.items():
            # Check if feature is related to climate variables
            for climate_var in self.climate_variables:
                var_name = climate_var.split('_')[-1]  # Get variable name (e.g., 'temperature')
                if var_name in feature.lower():
                    climate_importance[climate_var] = climate_importance.get(climate_var, 0) + importance
                    break
        
        # Sort by importance
        sorted_importance = dict(sorted(climate_importance.items(), key=lambda x: x[1], reverse=True))
        
        # Calculate relative contributions
        total_importance = sum(sorted_importance.values())
        relative_contributions = {}
        if total_importance > 0:
            relative_contributions = {k: v/total_importance for k, v in sorted_importance.items()}
        
        # Identify key drivers
        top_factors = list(sorted_importance.keys())[:3]
        
        analysis = {
            'climate_factor_importance': sorted_importance,
            'relative_contributions': relative_contributions,
            'top_climate_factors': top_factors,
            'climate_complexity_score': len([v for v in sorted_importance.values() if v > 0.1]),
            'primary_driver': top_factors[0] if top_factors else None,
            'driver_dominance': relative_contributions.get(top_factors[0], 0) if top_factors else 0
        }
        
        logger.info(f"Climate factors analysis: top factors are {top_factors}")
        
        return analysis
    
    def get_climate_summary(self) -> Dict[str, Any]:
        """Get a summary of the climate model."""
        summary = self.get_model_summary()
        
        climate_specific = {
            'climate_variables': self.climate_variables,
            'baseline_available': bool(self.baseline_stats),
            'primary_target': self.config.target_variable,
            'climate_feature_count': len([f for f in self.feature_names 
                                        if any(var.split('_')[-1] in f.lower() 
                                              for var in self.climate_variables)])
        }
        
        summary.update(climate_specific)
        return summary 