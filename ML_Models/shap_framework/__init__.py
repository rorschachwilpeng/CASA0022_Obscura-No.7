"""
SHAP Environmental Change Index Framework

A comprehensive framework for environmental prediction with SHAP interpretability.
"""

__version__ = "1.0.0"
__author__ = "CASA0022_Obscura-No.7"

# Import core components
from .data_infrastructure.data_pipeline.data_loader import DataLoader
from .data_infrastructure.data_pipeline.data_preprocessor import DataPreprocessor
from .data_infrastructure.data_pipeline.feature_engineer import FeatureEngineer
from .data_infrastructure.data_quality.data_validator import DataValidator

__all__ = [
    "DataLoader",
    "DataPreprocessor",
    "FeatureEngineer",
    "DataValidator"
] 