"""
Score Calculator for SHAP Environmental Change Index Framework

Calculates Economic Score and combines all scores into final Environment Change Outcome.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ScoreWeights:
    """Weight configuration for score calculation."""
    climate_weight: float = 0.3
    geographic_weight: float = 0.3
    economic_weight: float = 0.4
    
    def __post_init__(self):
        """Validate weights sum to 1.0."""
        total = self.climate_weight + self.geographic_weight + self.economic_weight
        if not np.isclose(total, 1.0):
            raise ValueError(f"Weights must sum to 1.0, got {total}")

@dataclass
class EnvironmentalOutcome:
    """Container for environmental change outcome results."""
    final_score: float
    climate_score: float
    geographic_score: float
    economic_score: float
    confidence_score: float
    risk_level: str
    trend_direction: str
    component_contributions: Dict[str, float]
    prediction_metadata: Dict[str, Any]

class ScoreCalculator:
    """
    Score Calculator for the SHAP Environmental Change Index Framework.
    
    Responsibilities:
    1. Calculate Economic Score from socio-economic factors
    2. Combine Climate, Geographic, and Economic scores
    3. Generate final Environment Change Outcome
    4. Provide score analysis and interpretations
    """
    
    def __init__(self, city: str, weights: Optional[ScoreWeights] = None):
        """
        Initialize ScoreCalculator.
        
        Args:
            city: City name (London, Manchester, Edinburgh)
            weights: ScoreWeights object for score combination
        """
        self.city = city
        self.weights = weights or ScoreWeights()
        
        # Economic variables (socio-economic factors)
        self.economic_variables = [
            'socioeconomic_life_expectancy',
            'socioeconomic_population_distribution',
            'socioeconomic_rail_infrastructure'
        ]
        
        # Economic score calculation parameters
        self.economic_baseline = {}
        self.economic_weights_internal = {
            'socioeconomic_life_expectancy': 0.5,      # 50% - most important
            'socioeconomic_population_distribution': 0.3,  # 30% - population impact
            'socioeconomic_rail_infrastructure': 0.2   # 20% - infrastructure impact
        }
        
        # Risk level thresholds
        self.risk_thresholds = {
            'low': (-0.5, 0.5),
            'moderate': (-1.0, 1.0),
            'high': (-2.0, 2.0),
            'critical': (-float('inf'), float('inf'))
        }
        
        logger.info(f"ScoreCalculator initialized for {city}")
    
    def calculate_economic_baseline(self, historical_data: pd.DataFrame):
        """
        Calculate baseline statistics for economic variables.
        
        Args:
            historical_data: Historical data containing economic variables
        """
        logger.info("Calculating economic baseline statistics")
        
        self.economic_baseline = {}
        
        for var in self.economic_variables:
            if var in historical_data.columns:
                var_data = historical_data[var].dropna()
                if len(var_data) > 0:
                    self.economic_baseline[var] = {
                        'mean': var_data.mean(),
                        'std': var_data.std(),
                        'median': var_data.median(),
                        'q25': var_data.quantile(0.25),
                        'q75': var_data.quantile(0.75),
                        'min': var_data.min(),
                        'max': var_data.max(),
                        'trend': self._calculate_trend(var_data)
                    }
        
        logger.info(f"Economic baseline calculated for {len(self.economic_baseline)} variables")
    
    def _calculate_trend(self, data: pd.Series) -> float:
        """Calculate trend slope for a time series."""
        if len(data) < 2:
            return 0.0
        
        # Simple linear trend calculation
        x = np.arange(len(data))
        coeffs = np.polyfit(x, data.values, 1)
        return coeffs[0]  # Return slope
    
    def calculate_economic_score(self, current_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate Economic Score from socio-economic factors.
        
        Economic Score = weighted average of standardized economic indicators
        
        Args:
            current_data: Current economic data
            
        Returns:
            Dictionary with Economic Score and component analysis
        """
        logger.info("Calculating Economic Score")
        
        if not self.economic_baseline:
            logger.warning("No economic baseline available, using raw values")
            return self._calculate_raw_economic_score(current_data)
        
        component_scores = {}
        weighted_scores = []
        
        for var in self.economic_variables:
            if var in current_data.columns and var in self.economic_baseline:
                # Get current value (use latest available)
                current_values = current_data[var].dropna()
                if len(current_values) > 0:
                    current_value = current_values.iloc[-1]  # Latest value
                    
                    # Calculate standardized score
                    baseline_stats = self.economic_baseline[var]
                    baseline_mean = baseline_stats['mean']
                    baseline_std = baseline_stats['std']
                    
                    if baseline_std > 0:
                        standardized_score = (current_value - baseline_mean) / baseline_std
                    else:
                        standardized_score = 0.0
                    
                    # Apply economic interpretation
                    # For life expectancy and infrastructure: higher is better
                    # For population distribution: depends on context, assume moderate growth is best
                    if var == 'socioeconomic_life_expectancy':
                        economic_impact = standardized_score  # Higher is better
                    elif var == 'socioeconomic_rail_infrastructure':
                        economic_impact = standardized_score  # Higher is better
                    elif var == 'socioeconomic_population_distribution':
                        # Population growth: moderate positive is best, extreme in either direction is concerning
                        economic_impact = standardized_score if abs(standardized_score) < 1.5 else -abs(standardized_score)
                    else:
                        economic_impact = standardized_score
                    
                    component_scores[var] = {
                        'raw_value': current_value,
                        'baseline_mean': baseline_mean,
                        'standardized_score': standardized_score,
                        'economic_impact': economic_impact,
                        'weight': self.economic_weights_internal[var]
                    }
                    
                    # Add to weighted score
                    weighted_scores.append(economic_impact * self.economic_weights_internal[var])
        
        # Calculate final Economic Score
        if weighted_scores:
            economic_score = sum(weighted_scores)
        else:
            logger.warning("No economic data available for score calculation")
            economic_score = 0.0
        
        # Calculate confidence based on data availability
        data_availability = len(component_scores) / len(self.economic_variables)
        confidence_score = min(1.0, data_availability + 0.2)  # Boost confidence slightly
        
        # Assess economic trend
        trend_scores = [comp['economic_impact'] for comp in component_scores.values()]
        if trend_scores:
            avg_trend = np.mean(trend_scores)
            if avg_trend > 0.2:
                trend_direction = 'improving'
            elif avg_trend < -0.2:
                trend_direction = 'declining'
            else:
                trend_direction = 'stable'
        else:
            trend_direction = 'unknown'
        
        result = {
            'economic_score': economic_score,
            'component_scores': component_scores,
            'confidence_score': confidence_score,
            'trend_direction': trend_direction,
            'data_availability': data_availability,
            'score_interpretation': self._interpret_economic_score(economic_score),
            'contributing_factors': len(component_scores)
        }
        
        logger.info(f"Economic Score calculated: {economic_score:.4f} (confidence: {confidence_score:.2f})")
        
        return result
    
    def _calculate_raw_economic_score(self, current_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate economic score without baseline (fallback method)."""
        logger.info("Calculating raw Economic Score (no baseline)")
        
        raw_scores = []
        component_scores = {}
        
        for var in self.economic_variables:
            if var in current_data.columns:
                var_data = current_data[var].dropna()
                if len(var_data) > 0:
                    # Use normalized values (0-1 scale)
                    var_min, var_max = var_data.min(), var_data.max()
                    if var_max > var_min:
                        normalized = (var_data.iloc[-1] - var_min) / (var_max - var_min)
                    else:
                        normalized = 0.5
                    
                    # Convert to -1 to 1 scale
                    score = (normalized - 0.5) * 2
                    
                    component_scores[var] = {
                        'raw_value': var_data.iloc[-1],
                        'normalized_score': score,
                        'weight': self.economic_weights_internal[var]
                    }
                    
                    raw_scores.append(score * self.economic_weights_internal[var])
        
        economic_score = sum(raw_scores) if raw_scores else 0.0
        
        return {
            'economic_score': economic_score,
            'component_scores': component_scores,
            'confidence_score': 0.5,  # Lower confidence without baseline
            'trend_direction': 'unknown',
            'data_availability': len(component_scores) / len(self.economic_variables),
            'score_interpretation': self._interpret_economic_score(economic_score),
            'contributing_factors': len(component_scores)
        }
    
    def _interpret_economic_score(self, score: float) -> str:
        """Interpret Economic Score value."""
        if score > 0.5:
            return 'Strong positive economic conditions'
        elif score > 0.2:
            return 'Moderate positive economic conditions'
        elif score > -0.2:
            return 'Stable economic conditions'
        elif score > -0.5:
            return 'Moderate economic challenges'
        else:
            return 'Significant economic challenges'
    
    def calculate_final_outcome(self, climate_score: float, geographic_score: float, 
                               economic_score: float, metadata: Optional[Dict] = None) -> EnvironmentalOutcome:
        """
        Calculate final Environment Change Outcome.
        
        Args:
            climate_score: Climate Score from ClimateModel
            geographic_score: Geographic Score from GeographicModel
            economic_score: Economic Score from this calculator
            metadata: Additional metadata for the prediction
            
        Returns:
            EnvironmentalOutcome object
        """
        logger.info("Calculating final Environment Change Outcome")
        
        # Calculate weighted final score
        final_score = (
            climate_score * self.weights.climate_weight +
            geographic_score * self.weights.geographic_weight +
            economic_score * self.weights.economic_weight
        )
        
        # Calculate component contributions
        component_contributions = {
            'climate': climate_score * self.weights.climate_weight,
            'geographic': geographic_score * self.weights.geographic_weight,
            'economic': economic_score * self.weights.economic_weight
        }
        
        # Determine risk level
        risk_level = self._determine_risk_level(final_score)
        
        # Determine trend direction
        trend_direction = self._determine_trend_direction(climate_score, geographic_score, economic_score)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(climate_score, geographic_score, economic_score, metadata)
        
        # Create outcome object
        outcome = EnvironmentalOutcome(
            final_score=final_score,
            climate_score=climate_score,
            geographic_score=geographic_score,
            economic_score=economic_score,
            confidence_score=confidence_score,
            risk_level=risk_level,
            trend_direction=trend_direction,
            component_contributions=component_contributions,
            prediction_metadata=metadata or {}
        )
        
        logger.info(f"Final Environment Change Outcome: {final_score:.4f} ({risk_level} risk, {trend_direction})")
        
        return outcome
    
    def _determine_risk_level(self, final_score: float) -> str:
        """Determine risk level from final score."""
        abs_score = abs(final_score)
        
        if abs_score <= 0.5:
            return 'low'
        elif abs_score <= 1.0:
            return 'moderate'
        elif abs_score <= 2.0:
            return 'high'
        else:
            return 'critical'
    
    def _determine_trend_direction(self, climate_score: float, geographic_score: float, economic_score: float) -> str:
        """Determine overall trend direction."""
        scores = [climate_score, geographic_score, economic_score]
        avg_score = np.mean(scores)
        
        if avg_score > 0.2:
            return 'improving'
        elif avg_score < -0.2:
            return 'deteriorating'
        else:
            return 'stable'
    
    def _calculate_confidence_score(self, climate_score: float, geographic_score: float, 
                                  economic_score: float, metadata: Optional[Dict] = None) -> float:
        """Calculate confidence score for the prediction."""
        # Base confidence from score consistency
        scores = [climate_score, geographic_score, economic_score]
        score_std = np.std(scores)
        consistency_score = max(0, 1 - score_std / 2)  # Lower std = higher confidence
        
        # Adjust based on metadata if available
        if metadata:
            # Data quality factors
            data_quality = metadata.get('data_quality', 0.8)
            model_performance = metadata.get('model_performance', 0.8)
            
            # Combine factors
            confidence_score = (consistency_score * 0.4 + data_quality * 0.3 + model_performance * 0.3)
        else:
            confidence_score = consistency_score
        
        return min(1.0, max(0.0, confidence_score))
    
    def analyze_outcome_drivers(self, outcome: EnvironmentalOutcome) -> Dict[str, Any]:
        """
        Analyze the main drivers of the environmental outcome.
        
        Args:
            outcome: EnvironmentalOutcome object
            
        Returns:
            Analysis of outcome drivers
        """
        # Rank components by absolute contribution
        contributions = outcome.component_contributions
        ranked_components = sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)
        
        # Identify primary driver
        primary_driver = ranked_components[0][0] if ranked_components else None
        primary_contribution = ranked_components[0][1] if ranked_components else 0
        
        # Calculate dominance (how much the primary driver dominates)
        total_abs_contribution = sum(abs(v) for v in contributions.values())
        dominance = abs(primary_contribution) / (total_abs_contribution + 1e-8)
        
        # Assess balance between components
        score_balance = np.std(list(contributions.values()))
        balance_interpretation = 'balanced' if score_balance < 0.3 else 'imbalanced'
        
        analysis = {
            'primary_driver': primary_driver,
            'primary_contribution': primary_contribution,
            'dominance_score': dominance,
            'component_ranking': ranked_components,
            'balance_score': score_balance,
            'balance_interpretation': balance_interpretation,
            'risk_factors': self._identify_risk_factors(outcome),
            'improvement_opportunities': self._identify_improvement_opportunities(outcome)
        }
        
        logger.info(f"Outcome drivers analysis: primary driver is {primary_driver} with {dominance:.2f} dominance")
        
        return analysis
    
    def _identify_risk_factors(self, outcome: EnvironmentalOutcome) -> List[str]:
        """Identify risk factors from outcome."""
        risk_factors = []
        
        if outcome.climate_score < -0.5:
            risk_factors.append('Significant climate deterioration')
        if outcome.geographic_score < -0.5:
            risk_factors.append('Geographic/environmental degradation')
        if outcome.economic_score < -0.5:
            risk_factors.append('Economic challenges')
        if outcome.confidence_score < 0.6:
            risk_factors.append('High prediction uncertainty')
        if outcome.risk_level in ['high', 'critical']:
            risk_factors.append('Overall high risk level')
        
        return risk_factors
    
    def _identify_improvement_opportunities(self, outcome: EnvironmentalOutcome) -> List[str]:
        """Identify improvement opportunities from outcome."""
        opportunities = []
        
        # Find weakest component
        contributions = outcome.component_contributions
        weakest_component = min(contributions.items(), key=lambda x: x[1])
        
        if weakest_component[1] < -0.2:
            if weakest_component[0] == 'climate':
                opportunities.append('Climate adaptation and mitigation measures')
            elif weakest_component[0] == 'geographic':
                opportunities.append('Geographic/environmental restoration')
            elif weakest_component[0] == 'economic':
                opportunities.append('Economic development initiatives')
        
        # Overall improvement suggestions
        if outcome.final_score < 0:
            opportunities.append('Comprehensive environmental improvement strategy')
        
        return opportunities
    
    def get_score_summary(self) -> Dict[str, Any]:
        """Get a summary of the score calculator configuration."""
        return {
            'city': self.city,
            'weights': {
                'climate_weight': self.weights.climate_weight,
                'geographic_weight': self.weights.geographic_weight,
                'economic_weight': self.weights.economic_weight
            },
            'economic_variables': self.economic_variables,
            'economic_baseline_available': bool(self.economic_baseline),
            'risk_thresholds': self.risk_thresholds
        } 