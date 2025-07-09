"""
Geographic Model for SHAP Environmental Change Index Framework

Predicts Geographic Score from geospatial variables (soil temperature, soil moisture, 
reference evapotranspiration, urban flood risk).
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
import logging
from .time_series_predictor import TimeSeriesPredictor, ModelConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeographicModel(TimeSeriesPredictor):
    """
    Geographic Model for predicting Geographic Score from geospatial variables.
    
    Uses 4 geospatial variables:
    - Soil Temperature (0-7cm)
    - Soil Moisture (7-28cm)
    - Reference Evapotranspiration
    - Urban Flood Risk
    """
    
    def __init__(self, city: str, config: Optional[ModelConfig] = None):
        """
        Initialize GeographicModel.
        
        Args:
            city: City name (London, Manchester, Edinburgh)
            config: ModelConfig object
        """
        # Default configuration for geographic models
        default_config = ModelConfig(
            algorithm="gradient_boosting",  # Often better for geospatial data
            target_variable="geospatial_soil_temperature_0_7cm",  # Primary geographic indicator
            feature_selection=True,
            max_features=12,
            validation_splits=5,
            hyperparameters={
                'n_estimators': 120,
                'max_depth': 8,
                'learning_rate': 0.1,
                'subsample': 0.8
            }
        )
        
        # Override with provided config
        if config:
            for key, value in config.__dict__.items():
                if value is not None:
                    setattr(default_config, key, value)
        
        super().__init__(config=default_config, city=city, model_type="geographic")
        
        # Geographic-specific variables
        self.geographic_variables = [
            'geospatial_soil_temperature_0_7cm',
            'geospatial_soil_moisture_7_28cm',
            'geospatial_reference_evapotranspiration',
            'geospatial_urban_flood_risk'
        ]
        
        # Geographic categories for analysis
        self.geographic_categories = {
            'soil_health': ['geospatial_soil_temperature_0_7cm', 'geospatial_soil_moisture_7_28cm'],
            'water_cycle': ['geospatial_reference_evapotranspiration'],
            'flood_risk': ['geospatial_urban_flood_risk']
        }
        
        # Historical baseline for score calculation
        self.baseline_stats = {}
        
        logger.info(f"GeographicModel initialized for {city}")
    
    def prepare_features(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare features and target for geographic prediction.
        
        Args:
            data: Input DataFrame with environmental data
            
        Returns:
            Tuple of (features, target)
        """
        # Extract geographic features
        available_geo_vars = [var for var in self.geographic_variables if var in data.columns]
        
        if not available_geo_vars:
            raise ValueError(f"No geographic variables found in data. Expected: {self.geographic_variables}")
        
        logger.info(f"Using {len(available_geo_vars)} geographic variables: {available_geo_vars}")
        
        # Features: all available variables except the target
        target_var = self.config.target_variable
        if target_var not in available_geo_vars:
            # Default to soil temperature if target not available
            target_var = 'geospatial_soil_temperature_0_7cm'
            if target_var not in available_geo_vars:
                target_var = available_geo_vars[0]
        
        feature_vars = [var for var in available_geo_vars if var != target_var]
        
        # Add relevant meteorological features (climate-geographic interactions)
        climate_features = sorted([col for col in data.columns if any(climate_term in col.lower() for climate_term in 
                           ['meteorological_temperature', 'meteorological_precipitation', 'meteorological_humidity'])])
        
        # Add time-based features (sorted for consistency)
        time_features = sorted([col for col in data.columns if any(time_term in col.lower() for time_term in 
                        ['year', 'month', 'quarter', 'season', 'day', 'time'])])
        
        # Add lag and trend features (sorted for consistency)
        lag_features = sorted([col for col in data.columns if 'lag_' in col.lower()])
        trend_features = sorted([col for col in data.columns if any(trend_term in col.lower() for trend_term in 
                         ['trend', 'slope', 'change', 'ma_', 'moving'])])
        
        # Add interaction features for geographic variables (sorted for consistency)
        interaction_features = sorted([col for col in data.columns if 'interaction' in col.lower() and 
                              any(geo_var.split('_')[-1] in col or geo_var.split('_')[-2] in col 
                                  for geo_var in self.geographic_variables)])
        
        all_features = (feature_vars + climate_features[:3] + time_features + 
                       lag_features + trend_features + interaction_features)
        available_features = [feat for feat in all_features if feat in data.columns]
        
        # Ensure consistent ordering by sorting the final feature list
        available_features = sorted(available_features)
        
        X = data[available_features].copy()
        y = data[target_var].copy()
        
        # Store target variable name
        self.target_name = target_var
        
        logger.info(f"Prepared features: {len(X.columns)} features, target: {target_var}")
        logger.info(f"Feature categories: {len(feature_vars)} geographic, {len(climate_features[:3])} climate, "
                   f"{len(time_features)} time, {len(lag_features)} lag, {len(trend_features)} trend")
        
        return X, y
    
    def calculate_baseline_stats(self, historical_data: pd.DataFrame):
        """
        Calculate baseline statistics from historical data for score calculation.
        
        Args:
            historical_data: Historical environmental data
        """
        logger.info("Calculating baseline statistics for Geographic Score")
        
        self.baseline_stats = {}
        
        # Calculate baseline for each geographic variable
        for var in self.geographic_variables:
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
        
        # Calculate category-level baselines
        for category, variables in self.geographic_categories.items():
            category_data = []
            for var in variables:
                if var in historical_data.columns:
                    var_data = historical_data[var].dropna()
                    if len(var_data) > 0:
                        # Normalize to 0-1 scale for aggregation
                        normalized = (var_data - var_data.min()) / (var_data.max() - var_data.min() + 1e-8)
                        category_data.extend(normalized.tolist())
            
            if category_data:
                category_series = pd.Series(category_data)
                self.baseline_stats[f'{category}_category'] = {
                    'mean': category_series.mean(),
                    'std': category_series.std(),
                    'median': category_series.median(),
                    'q25': category_series.quantile(0.25),
                    'q75': category_series.quantile(0.75)
                }
        
        # Calculate overall geographic baseline
        primary_var = self.config.target_variable
        if primary_var in self.baseline_stats:
            self.baseline_stats['overall'] = self.baseline_stats[primary_var].copy()
        elif 'geospatial_soil_temperature_0_7cm' in self.baseline_stats:
            self.baseline_stats['overall'] = self.baseline_stats['geospatial_soil_temperature_0_7cm'].copy()
        else:
            # Use first available variable
            first_var = next(iter([k for k in self.baseline_stats.keys() if not k.endswith('_category')]))
            self.baseline_stats['overall'] = self.baseline_stats[first_var].copy()
        
        logger.info(f"Baseline statistics calculated for {len(self.baseline_stats)} variables/categories")
    
    def calculate_score(self, predictions: np.ndarray, baseline_stats: Optional[Dict[str, float]] = None) -> float:
        """
        Calculate Geographic Score from model predictions.
        
        Geographic Score = (predicted_mean - baseline_mean) / baseline_std
        
        Args:
            predictions: Model predictions for geographic variable
            baseline_stats: Historical baseline statistics (optional, uses stored if not provided)
            
        Returns:
            Geographic Score (standardized change from baseline)
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
            geographic_score = predicted_mean - baseline_mean
        else:
            geographic_score = (predicted_mean - baseline_mean) / baseline_std
        
        logger.info(f"Geographic Score calculated: {geographic_score:.4f} "
                   f"(predicted: {predicted_mean:.4f}, baseline: {baseline_mean:.4f})")
        
        return float(geographic_score)
    
    def predict_geographic_score(self, features: pd.DataFrame) -> Dict[str, Any]:
        """
        Predict Geographic Score for given features.
        
        Args:
            features: Input features
            
        Returns:
            Dictionary with predictions and Geographic Score
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Generate predictions
        predictions = self.predict(features)
        
        # Calculate Geographic Score
        geographic_score = self.calculate_score(predictions)
        
        # Calculate confidence metrics
        if hasattr(self.model, 'predict') and len(predictions) > 1:
            prediction_std = np.std(predictions)
            prediction_range = np.max(predictions) - np.min(predictions)
        else:
            prediction_std = 0.0
            prediction_range = 0.0
        
        result = {
            'geographic_score': geographic_score,
            'predictions': predictions,
            'prediction_mean': np.mean(predictions),
            'prediction_std': prediction_std,
            'prediction_range': prediction_range,
            'confidence_score': max(0, 1 - prediction_std / (self.baseline_stats.get('overall', {}).get('std', 1) + 1e-8)),
            'target_variable': self.target_name,
            'feature_count': len(features.columns),
            'sample_count': len(predictions)
        }
        
        logger.info(f"Geographic Score prediction completed: {geographic_score:.4f}")
        
        return result
    
    def analyze_geographic_factors(self, features: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze geographic factor contributions to the prediction.
        
        Args:
            features: Input features
            
        Returns:
            Analysis of geographic factor contributions
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before analysis")
        
        # Get feature importance by geographic categories
        category_importance = {category: 0.0 for category in self.geographic_categories.keys()}
        individual_importance = {}
        
        for feature, importance in self.feature_importance.items():
            # Check which geographic variable/category this feature belongs to
            for geo_var in self.geographic_variables:
                var_keywords = geo_var.split('_')[1:]  # Skip 'geospatial'
                if any(keyword in feature.lower() for keyword in var_keywords):
                    individual_importance[geo_var] = individual_importance.get(geo_var, 0) + importance
                    
                    # Add to category importance
                    for category, variables in self.geographic_categories.items():
                        if geo_var in variables:
                            category_importance[category] += importance
                            break
                    break
        
        # Sort by importance
        sorted_individual = dict(sorted(individual_importance.items(), key=lambda x: x[1], reverse=True))
        sorted_category = dict(sorted(category_importance.items(), key=lambda x: x[1], reverse=True))
        
        # Calculate relative contributions
        total_individual = sum(sorted_individual.values())
        total_category = sum(sorted_category.values())
        
        relative_individual = {}
        relative_category = {}
        
        if total_individual > 0:
            relative_individual = {k: v/total_individual for k, v in sorted_individual.items()}
        if total_category > 0:
            relative_category = {k: v/total_category for k, v in sorted_category.items()}
        
        # Identify key drivers
        top_variables = list(sorted_individual.keys())[:2]
        top_categories = list(sorted_category.keys())[:2]
        
        analysis = {
            'geographic_variable_importance': sorted_individual,
            'geographic_category_importance': sorted_category,
            'relative_variable_contributions': relative_individual,
            'relative_category_contributions': relative_category,
            'top_geographic_variables': top_variables,
            'top_geographic_categories': top_categories,
            'geographic_complexity_score': len([v for v in sorted_individual.values() if v > 0.1]),
            'primary_driver_variable': top_variables[0] if top_variables else None,
            'primary_driver_category': top_categories[0] if top_categories else None,
            'category_dominance': relative_category.get(top_categories[0], 0) if top_categories else 0
        }
        
        logger.info(f"Geographic factors analysis: top variables are {top_variables}, top categories are {top_categories}")
        
        return analysis
    
    def assess_geographic_risk(self, predictions: np.ndarray) -> Dict[str, Any]:
        """
        Assess geographic risk levels based on predictions.
        
        Args:
            predictions: Model predictions
            
        Returns:
            Geographic risk assessment
        """
        if not self.baseline_stats:
            logger.warning("No baseline statistics available for risk assessment")
            return {'risk_level': 'unknown', 'risk_score': 0.5}
        
        # Calculate risk based on deviation from baseline
        baseline_stats = self.baseline_stats.get('overall', {})
        baseline_mean = baseline_stats.get('mean', 0)
        baseline_std = baseline_stats.get('std', 1)
        
        prediction_mean = np.mean(predictions)
        deviation = abs(prediction_mean - baseline_mean) / (baseline_std + 1e-8)
        
        # Risk categories
        if deviation < 0.5:
            risk_level = 'low'
            risk_score = 0.2
        elif deviation < 1.0:
            risk_level = 'moderate'
            risk_score = 0.5
        elif deviation < 2.0:
            risk_level = 'high'
            risk_score = 0.8
        else:
            risk_level = 'critical'
            risk_score = 1.0
        
        # Additional risk factors
        prediction_volatility = np.std(predictions) / (np.mean(predictions) + 1e-8)
        trend_direction = 'increasing' if prediction_mean > baseline_mean else 'decreasing'
        
        risk_assessment = {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'deviation_magnitude': deviation,
            'prediction_volatility': prediction_volatility,
            'trend_direction': trend_direction,
            'baseline_comparison': {
                'predicted_mean': prediction_mean,
                'baseline_mean': baseline_mean,
                'relative_change': (prediction_mean - baseline_mean) / (baseline_mean + 1e-8)
            }
        }
        
        logger.info(f"Geographic risk assessment: {risk_level} risk (score: {risk_score:.2f})")
        
        return risk_assessment
    
    def get_geographic_summary(self) -> Dict[str, Any]:
        """Get a summary of the geographic model."""
        summary = self.get_model_summary()
        
        geographic_specific = {
            'geographic_variables': self.geographic_variables,
            'geographic_categories': list(self.geographic_categories.keys()),
            'baseline_available': bool(self.baseline_stats),
            'primary_target': self.config.target_variable,
            'geographic_feature_count': len([f for f in self.feature_names 
                                           if any(var.split('_')[-1] in f.lower() or var.split('_')[-2] in f.lower()
                                                  for var in self.geographic_variables)])
        }
        
        summary.update(geographic_specific)
        return summary 