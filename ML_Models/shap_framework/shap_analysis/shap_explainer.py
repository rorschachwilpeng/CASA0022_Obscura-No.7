"""
SHAP Explainer for Environmental Change Index Framework

Core SHAP analysis functionality that provides model interpretability
for Climate and Geographic models.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass
import logging
import warnings
warnings.filterwarnings('ignore')

# SHAP library import with fallback
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logging.warning("SHAP library not available. Install with: pip install shap")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SHAPConfig:
    """Configuration for SHAP analysis."""
    explainer_type: str = "tree"  # tree, linear, kernel, permutation
    background_samples: int = 100
    max_evals: int = 500
    feature_selection: bool = True
    interaction_analysis: bool = True
    batch_size: int = 32

@dataclass
class SHAPResult:
    """Container for SHAP analysis results."""
    shap_values: np.ndarray
    expected_value: float
    feature_names: List[str]
    feature_importance: Dict[str, float]
    interaction_values: Optional[np.ndarray]
    explanation_data: Dict[str, Any]
    model_metadata: Dict[str, Any]

class SHAPExplainer:
    """
    SHAP Explainer for Environmental Change Index Framework.
    
    Provides comprehensive SHAP analysis for Climate and Geographic models,
    including feature importance, interaction effects, and explanation data.
    """
    
    def __init__(self, config: Optional[SHAPConfig] = None):
        """
        Initialize SHAP Explainer.
        
        Args:
            config: SHAPConfig object
        """
        self.config = config or SHAPConfig()
        self.explainers = {}
        self.background_data = {}
        self.explanation_cache = {}
        
        if not SHAP_AVAILABLE:
            logger.error("SHAP library is required for this functionality")
            raise ImportError("Please install SHAP: pip install shap")
        
        logger.info("SHAPExplainer initialized")
    
    def setup_explainer(self, model, model_type: str, X_background: pd.DataFrame, 
                       model_name: str = "default") -> None:
        """
        Set up SHAP explainer for a specific model.
        
        Args:
            model: Trained model object
            model_type: Type of model ('climate' or 'geographic')
            X_background: Background data for SHAP baseline
            model_name: Name identifier for the model
        """
        logger.info(f"Setting up SHAP explainer for {model_name} ({model_type})")
        
        # Store background data
        if len(X_background) > self.config.background_samples:
            # Sample background data for efficiency
            background_sample = X_background.sample(
                n=self.config.background_samples, 
                random_state=42
            )
        else:
            background_sample = X_background.copy()
        
        self.background_data[model_name] = background_sample
        
        # Choose appropriate explainer based on model type and configuration
        try:
            if self.config.explainer_type == "tree" and hasattr(model, 'feature_importances_'):
                # Tree-based models (RandomForest, GradientBoosting)
                explainer = shap.TreeExplainer(model)
                logger.info(f"Using TreeExplainer for {model_name}")
                
            elif self.config.explainer_type == "linear" and hasattr(model, 'coef_'):
                # Linear models
                explainer = shap.LinearExplainer(
                    model, background_sample.values
                )
                logger.info(f"Using LinearExplainer for {model_name}")
                
            else:
                # Fallback to KernelExplainer for any model
                explainer = shap.KernelExplainer(
                    model.predict, 
                    background_sample.values
                )
                logger.info(f"Using KernelExplainer for {model_name}")
            
            self.explainers[model_name] = {
                'explainer': explainer,
                'model': model,
                'model_type': model_type,
                'feature_names': list(X_background.columns)
            }
            
            logger.info(f"SHAP explainer setup completed for {model_name}")
            
        except Exception as e:
            logger.error(f"Error setting up SHAP explainer for {model_name}: {str(e)}")
            raise
    
    def explain_prediction(self, X: pd.DataFrame, model_name: str = "default",
                          return_interactions: bool = None) -> SHAPResult:
        """
        Generate SHAP explanations for predictions.
        
        Args:
            X: Input features to explain
            model_name: Name of the model to use
            return_interactions: Whether to compute interaction values
            
        Returns:
            SHAPResult object containing all explanation data
        """
        if model_name not in self.explainers:
            raise ValueError(f"Model {model_name} not found. Call setup_explainer() first.")
        
        logger.info(f"Generating SHAP explanations for {len(X)} samples using {model_name}")
        
        explainer_info = self.explainers[model_name]
        explainer = explainer_info['explainer']
        model = explainer_info['model']
        feature_names = explainer_info['feature_names']
        
        # Ensure X has the same features as training data
        X_aligned = X[feature_names].copy()
        
        try:
            # Generate SHAP values
            if isinstance(explainer, shap.TreeExplainer):
                shap_values = explainer.shap_values(X_aligned.values)
                expected_value = explainer.expected_value
                
                # Handle multi-output case
                if isinstance(shap_values, list):
                    shap_values = shap_values[0]
                if isinstance(expected_value, np.ndarray):
                    expected_value = expected_value[0]
                    
            elif isinstance(explainer, shap.LinearExplainer):
                shap_values = explainer.shap_values(X_aligned.values)
                expected_value = explainer.expected_value
                
            else:  # KernelExplainer
                shap_values = explainer.shap_values(
                    X_aligned.values, 
                    nsamples=min(self.config.max_evals, 100)
                )
                expected_value = explainer.expected_value
            
            # Calculate feature importance
            feature_importance = self._calculate_feature_importance(
                shap_values, feature_names
            )
            
            # Calculate interaction values if requested
            interaction_values = None
            if (return_interactions or 
                (return_interactions is None and self.config.interaction_analysis)):
                interaction_values = self._calculate_interactions(
                    explainer, X_aligned, model_name
                )
            
            # Generate explanation data
            explanation_data = self._generate_explanation_data(
                shap_values, expected_value, feature_names, X_aligned
            )
            
            # Create result object
            result = SHAPResult(
                shap_values=shap_values,
                expected_value=float(expected_value),
                feature_names=feature_names,
                feature_importance=feature_importance,
                interaction_values=interaction_values,
                explanation_data=explanation_data,
                model_metadata={
                    'model_name': model_name,
                    'model_type': explainer_info['model_type'],
                    'sample_count': len(X),
                    'feature_count': len(feature_names)
                }
            )
            
            logger.info(f"SHAP explanation completed for {model_name}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating SHAP explanations: {str(e)}")
            raise
    
    def _calculate_feature_importance(self, shap_values: np.ndarray, 
                                    feature_names: List[str]) -> Dict[str, float]:
        """Calculate aggregate feature importance from SHAP values."""
        # Mean absolute SHAP values across all samples
        importance_scores = np.mean(np.abs(shap_values), axis=0)
        
        # Normalize to sum to 1
        total_importance = np.sum(importance_scores)
        if total_importance > 0:
            importance_scores = importance_scores / total_importance
        
        return dict(zip(feature_names, importance_scores))
    
    def _calculate_interactions(self, explainer, X: pd.DataFrame, 
                              model_name: str) -> Optional[np.ndarray]:
        """Calculate SHAP interaction values if supported."""
        try:
            if hasattr(explainer, 'shap_interaction_values'):
                # Only calculate for a subset due to computational cost
                sample_size = min(len(X), 50)
                X_sample = X.head(sample_size)
                
                interaction_values = explainer.shap_interaction_values(X_sample.values)
                logger.info(f"Interaction values calculated for {sample_size} samples")
                return interaction_values
            else:
                logger.info("Interaction values not supported for this explainer type")
                return None
                
        except Exception as e:
            logger.warning(f"Could not calculate interaction values: {str(e)}")
            return None
    
    def _generate_explanation_data(self, shap_values: np.ndarray, expected_value: float,
                                 feature_names: List[str], X: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive explanation data."""
        n_samples, n_features = shap_values.shape
        
        # Per-sample explanations
        sample_explanations = []
        for i in range(n_samples):
            sample_shap = shap_values[i]
            sample_features = X.iloc[i]
            
            # Sort features by absolute SHAP value
            feature_impacts = [
                {
                    'feature': feature_names[j],
                    'value': float(sample_features.iloc[j]),
                    'shap_value': float(sample_shap[j]),
                    'impact': 'positive' if sample_shap[j] > 0 else 'negative',
                    'magnitude': abs(float(sample_shap[j]))
                }
                for j in range(n_features)
            ]
            
            # Sort by magnitude
            feature_impacts.sort(key=lambda x: x['magnitude'], reverse=True)
            
            sample_explanations.append({
                'sample_index': i,
                'prediction_contribution': float(np.sum(sample_shap) + expected_value),
                'baseline_value': float(expected_value),
                'total_shap_impact': float(np.sum(sample_shap)),
                'feature_impacts': feature_impacts[:10],  # Top 10 features
                'top_positive_features': [
                    f for f in feature_impacts if f['impact'] == 'positive'
                ][:5],
                'top_negative_features': [
                    f for f in feature_impacts if f['impact'] == 'negative'
                ][:5]
            })
        
        # Global explanations
        global_importance = np.mean(np.abs(shap_values), axis=0)
        global_feature_ranking = [
            {
                'feature': feature_names[i],
                'importance': float(global_importance[i]),
                'rank': i + 1
            }
            for i in np.argsort(global_importance)[::-1]
        ]
        
        return {
            'sample_explanations': sample_explanations,
            'global_feature_ranking': global_feature_ranking,
            'summary_stats': {
                'mean_absolute_shap': float(np.mean(np.abs(shap_values))),
                'max_absolute_shap': float(np.max(np.abs(shap_values))),
                'positive_impact_ratio': float(np.mean(shap_values > 0)),
                'feature_diversity': len(np.unique(np.argmax(np.abs(shap_values), axis=1)))
            }
        }
    
    def explain_models_comparison(self, X: pd.DataFrame, 
                                model_names: List[str]) -> Dict[str, SHAPResult]:
        """
        Compare SHAP explanations across multiple models.
        
        Args:
            X: Input features
            model_names: List of model names to compare
            
        Returns:
            Dictionary of SHAP results for each model
        """
        logger.info(f"Comparing SHAP explanations across {len(model_names)} models")
        
        results = {}
        for model_name in model_names:
            if model_name in self.explainers:
                results[model_name] = self.explain_prediction(X, model_name)
            else:
                logger.warning(f"Model {model_name} not found, skipping")
        
        return results
    
    def get_explainer_summary(self) -> Dict[str, Any]:
        """Get summary information about configured explainers."""
        summary = {
            'available_models': list(self.explainers.keys()),
            'config': {
                'explainer_type': self.config.explainer_type,
                'background_samples': self.config.background_samples,
                'max_evals': self.config.max_evals,
                'interaction_analysis': self.config.interaction_analysis
            },
            'model_details': {}
        }
        
        for name, info in self.explainers.items():
            summary['model_details'][name] = {
                'model_type': info['model_type'],
                'feature_count': len(info['feature_names']),
                'explainer_class': type(info['explainer']).__name__
            }
        
        return summary 