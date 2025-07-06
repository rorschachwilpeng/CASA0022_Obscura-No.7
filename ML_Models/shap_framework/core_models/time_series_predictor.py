"""
Time Series Predictor Base Class

Provides the foundation for all time series prediction models in the SHAP framework.
Supports multiple algorithms and provides standardized interfaces.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.svm import SVR
import joblib
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ModelConfig:
    """Configuration for time series models."""
    algorithm: str = "random_forest"  # random_forest, gradient_boosting, linear, ridge, lasso, svr
    target_variable: str = "temperature"  # Which variable to predict for score calculation
    feature_selection: bool = True
    max_features: int = 20
    validation_splits: int = 5
    test_size: float = 0.2
    random_state: int = 42
    hyperparameters: Dict[str, Any] = None

@dataclass
class PredictionResult:
    """Container for prediction results."""
    predictions: np.ndarray
    actuals: np.ndarray
    scores: Dict[str, float]
    feature_importance: Dict[str, float]
    model_metadata: Dict[str, Any]

class TimeSeriesPredictor(ABC):
    """
    Abstract base class for time series prediction models.
    
    Provides standardized interface for:
    - Model training and validation
    - Prediction generation
    - Performance evaluation
    - Feature importance analysis
    """
    
    def __init__(self, config: Optional[ModelConfig] = None, city: str = "", model_type: str = ""):
        """
        Initialize TimeSeriesPredictor.
        
        Args:
            config: ModelConfig object
            city: City name (London, Manchester, Edinburgh)
            model_type: Type of model (climate, geographic)
        """
        self.config = config or ModelConfig()
        self.city = city
        self.model_type = model_type
        self.model = None
        self.feature_selector = None
        self.is_trained = False
        self.feature_names = []
        self.target_name = ""
        self.training_history = []
        
        # Performance metrics
        self.validation_scores = {}
        self.feature_importance = {}
        
        logger.info(f"TimeSeriesPredictor initialized for {city} {model_type} model")
    
    def _create_model(self) -> Any:
        """Create the underlying ML model based on configuration."""
        algorithm = self.config.algorithm.lower()
        hyperparams = self.config.hyperparameters or {}
        
        if algorithm == "random_forest":
            return RandomForestRegressor(
                n_estimators=hyperparams.get('n_estimators', 100),
                max_depth=hyperparams.get('max_depth', None),
                min_samples_split=hyperparams.get('min_samples_split', 2),
                min_samples_leaf=hyperparams.get('min_samples_leaf', 1),
                random_state=self.config.random_state,
                n_jobs=-1
            )
        elif algorithm == "gradient_boosting":
            return GradientBoostingRegressor(
                n_estimators=hyperparams.get('n_estimators', 100),
                max_depth=hyperparams.get('max_depth', 3),
                learning_rate=hyperparams.get('learning_rate', 0.1),
                subsample=hyperparams.get('subsample', 1.0),
                random_state=self.config.random_state
            )
        elif algorithm == "linear":
            return LinearRegression()
        elif algorithm == "ridge":
            return Ridge(
                alpha=hyperparams.get('alpha', 1.0),
                random_state=self.config.random_state
            )
        elif algorithm == "lasso":
            return Lasso(
                alpha=hyperparams.get('alpha', 1.0),
                random_state=self.config.random_state
            )
        elif algorithm == "svr":
            return SVR(
                kernel=hyperparams.get('kernel', 'rbf'),
                C=hyperparams.get('C', 1.0),
                epsilon=hyperparams.get('epsilon', 0.1)
            )
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
    
    def _select_features(self, X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
        """Select most important features for prediction."""
        if not self.config.feature_selection or len(X.columns) <= self.config.max_features:
            return X
        
        # Use RandomForestRegressor for feature selection
        from sklearn.feature_selection import SelectFromModel
        
        selector_model = RandomForestRegressor(
            n_estimators=50, 
            random_state=self.config.random_state,
            n_jobs=-1
        )
        
        self.feature_selector = SelectFromModel(
            selector_model, 
            max_features=self.config.max_features
        )
        
        X_selected = self.feature_selector.fit_transform(X, y)
        selected_features = X.columns[self.feature_selector.get_support()]
        
        logger.info(f"Selected {len(selected_features)} features from {len(X.columns)}")
        
        return X[selected_features]
    
    def _calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Calculate performance metrics."""
        return {
            'mse': mean_squared_error(y_true, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'mae': mean_absolute_error(y_true, y_pred),
            'r2': r2_score(y_true, y_pred),
            'mape': np.mean(np.abs((y_true - y_pred) / y_true)) * 100 if np.all(y_true != 0) else np.inf
        }
    
    def _extract_feature_importance(self) -> Dict[str, float]:
        """Extract feature importance from trained model."""
        if not self.is_trained or self.model is None:
            return {}
        
        importance_dict = {}
        
        if hasattr(self.model, 'feature_importances_'):
            # Tree-based models
            for i, importance in enumerate(self.model.feature_importances_):
                feature_name = self.feature_names[i] if i < len(self.feature_names) else f"feature_{i}"
                importance_dict[feature_name] = float(importance)
        elif hasattr(self.model, 'coef_'):
            # Linear models
            coef = self.model.coef_
            if coef.ndim == 1:
                for i, coef_val in enumerate(coef):
                    feature_name = self.feature_names[i] if i < len(self.feature_names) else f"feature_{i}"
                    importance_dict[feature_name] = float(abs(coef_val))
        
        # Normalize importance scores
        if importance_dict:
            total_importance = sum(importance_dict.values())
            if total_importance > 0:
                importance_dict = {k: v/total_importance for k, v in importance_dict.items()}
        
        return importance_dict
    
    def train(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """
        Train the time series prediction model.
        
        Args:
            X: Feature matrix
            y: Target variable
            
        Returns:
            Training performance metrics
        """
        logger.info(f"Training {self.city} {self.model_type} model with {X.shape[0]} samples, {X.shape[1]} features")
        
        # Store feature and target names
        self.feature_names = list(X.columns)
        self.target_name = y.name if hasattr(y, 'name') and y.name else self.config.target_variable
        
        # Feature selection
        X_selected = self._select_features(X, y)
        self.feature_names = list(X_selected.columns)
        
        # Create and train model
        self.model = self._create_model()
        
        # Perform time series cross-validation
        tscv = TimeSeriesSplit(n_splits=self.config.validation_splits)
        cv_scores = cross_val_score(
            self.model, X_selected, y, 
            cv=tscv, scoring='neg_mean_squared_error'
        )
        
        # Train on full dataset
        self.model.fit(X_selected, y)
        self.is_trained = True
        
        # Calculate performance metrics
        y_pred = self.model.predict(X_selected)
        train_metrics = self._calculate_metrics(y.values, y_pred)
        
        # Store validation scores
        self.validation_scores = {
            'cv_rmse_mean': np.sqrt(-cv_scores.mean()),
            'cv_rmse_std': np.sqrt(cv_scores.std()),
            'train_rmse': train_metrics['rmse'],
            'train_r2': train_metrics['r2']
        }
        
        # Extract feature importance
        self.feature_importance = self._extract_feature_importance()
        
        # Store training history
        self.training_history.append({
            'timestamp': pd.Timestamp.now(),
            'samples': len(X),
            'features': len(self.feature_names),
            'metrics': train_metrics,
            'cv_scores': cv_scores
        })
        
        logger.info(f"Training completed. CV RMSE: {self.validation_scores['cv_rmse_mean']:.4f} ± {self.validation_scores['cv_rmse_std']:.4f}")
        
        return train_metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Generate predictions for input features.
        
        Args:
            X: Feature matrix
            
        Returns:
            Prediction array
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Apply feature selection if used during training
        if self.feature_selector is not None:
            X_selected = X[self.feature_names]
        else:
            # Ensure we have the same features as training
            missing_features = set(self.feature_names) - set(X.columns)
            if missing_features:
                raise ValueError(f"Missing features: {missing_features}")
            X_selected = X[self.feature_names]
        
        predictions = self.model.predict(X_selected)
        
        logger.info(f"Generated {len(predictions)} predictions")
        return predictions
    
    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> PredictionResult:
        """
        Evaluate model performance on test data.
        
        Args:
            X: Test feature matrix
            y: Test target variable
            
        Returns:
            PredictionResult object
        """
        predictions = self.predict(X)
        metrics = self._calculate_metrics(y.values, predictions)
        
        result = PredictionResult(
            predictions=predictions,
            actuals=y.values,
            scores=metrics,
            feature_importance=self.feature_importance,
            model_metadata={
                'city': self.city,
                'model_type': self.model_type,
                'algorithm': self.config.algorithm,
                'feature_count': len(self.feature_names),
                'training_samples': len(self.training_history[-1]['metrics']) if self.training_history else 0
            }
        )
        
        logger.info(f"Evaluation completed. R²: {metrics['r2']:.4f}, RMSE: {metrics['rmse']:.4f}")
        
        return result
    
    @abstractmethod
    def calculate_score(self, predictions: np.ndarray, baseline_stats: Dict[str, float]) -> float:
        """
        Calculate domain-specific score from predictions.
        
        Args:
            predictions: Model predictions
            baseline_stats: Historical baseline statistics
            
        Returns:
            Calculated score (Climate Score or Geographic Score)
        """
        pass
    
    def save_model(self, file_path: str):
        """Save the trained model to disk."""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        model_data = {
            'model': self.model,
            'feature_selector': self.feature_selector,
            'config': self.config,
            'feature_names': self.feature_names,
            'target_name': self.target_name,
            'feature_importance': self.feature_importance,
            'validation_scores': self.validation_scores,
            'training_history': self.training_history,
            'city': self.city,
            'model_type': self.model_type
        }
        
        joblib.dump(model_data, file_path)
        logger.info(f"Model saved to {file_path}")
    
    def load_model(self, file_path: str):
        """Load a trained model from disk."""
        model_data = joblib.load(file_path)
        
        self.model = model_data['model']
        self.feature_selector = model_data.get('feature_selector')
        self.config = model_data['config']
        self.feature_names = model_data['feature_names']
        self.target_name = model_data['target_name']
        self.feature_importance = model_data['feature_importance']
        self.validation_scores = model_data['validation_scores']
        self.training_history = model_data['training_history']
        self.city = model_data['city']
        self.model_type = model_data['model_type']
        self.is_trained = True
        
        logger.info(f"Model loaded from {file_path}")
    
    def get_model_summary(self) -> Dict[str, Any]:
        """Get a summary of the model."""
        return {
            'city': self.city,
            'model_type': self.model_type,
            'algorithm': self.config.algorithm,
            'is_trained': self.is_trained,
            'feature_count': len(self.feature_names),
            'target_variable': self.target_name,
            'validation_scores': self.validation_scores,
            'top_features': dict(sorted(self.feature_importance.items(), 
                                      key=lambda x: x[1], reverse=True)[:5]) if self.feature_importance else {},
            'training_history_count': len(self.training_history)
        } 