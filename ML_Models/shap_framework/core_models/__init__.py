"""
Core Models Module

Contains the main prediction models for the SHAP Environmental Change Index Framework.

Architecture:
- TimeSeriesPredictor: Base class for time series prediction
- ClimateModel: Predicts Climate Score from meteorological variables
- GeographicModel: Predicts Geographic Score from geospatial variables  
- ScoreCalculator: Computes Economic Score and final Environment Change Outcome
- OutcomePredictor: Main predictor that coordinates all models
"""

from .time_series_predictor import TimeSeriesPredictor, ModelConfig, PredictionResult
from .climate_model import ClimateModel
from .geographic_model import GeographicModel
from .score_calculator import ScoreCalculator, ScoreWeights, EnvironmentalOutcome
from .outcome_predictor import OutcomePredictor, PredictionConfig, ComprehensivePrediction

__all__ = [
    "TimeSeriesPredictor",
    "ModelConfig",
    "PredictionResult",
    "ClimateModel", 
    "GeographicModel",
    "ScoreCalculator",
    "ScoreWeights",
    "EnvironmentalOutcome",
    "OutcomePredictor",
    "PredictionConfig",
    "ComprehensivePrediction"
] 