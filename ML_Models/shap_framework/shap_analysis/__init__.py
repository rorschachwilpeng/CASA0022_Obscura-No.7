"""
SHAP Analysis Module

Contains the SHAP interpretation and explanation components for the Environmental Change Index Framework.

Components:
- SHAPExplainer: Core SHAP analysis functionality
- FeatureAnalyzer: Feature importance and interaction analysis
- CausalDecomposer: Causal breakdown of score contributions
- StoryGenerator: Automated explanation text generation
"""

from .shap_explainer import SHAPExplainer
from .feature_analyzer import FeatureAnalyzer
from .causal_decomposer import CausalDecomposer
from .story_generator import StoryGenerator

__all__ = [
    "SHAPExplainer",
    "FeatureAnalyzer", 
    "CausalDecomposer",
    "StoryGenerator"
] 