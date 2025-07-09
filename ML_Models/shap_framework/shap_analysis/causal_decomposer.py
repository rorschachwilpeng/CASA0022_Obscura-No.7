"""
Causal Decomposer for Environmental Change Index Framework

Analyzes the causal contribution of different factors to environmental change scores,
providing detailed breakdown of Climate, Geographic, and Economic score components.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class CausalFactor:
    """Represents a causal factor contributing to score changes."""
    factor_name: str
    contribution: float
    confidence: float
    direction: str  # 'positive', 'negative', 'neutral'
    category: str   # 'climate', 'geographic', 'economic'
    related_features: List[str]

@dataclass
class ScoreDecomposition:
    """Decomposition of a specific score component."""
    score_type: str  # 'climate', 'geographic', 'economic', 'final'
    baseline_value: float
    predicted_value: float
    total_change: float
    factor_contributions: List[CausalFactor]
    uncertainty_range: Tuple[float, float]

@dataclass
class CausalChain:
    """Represents a causal chain of environmental changes."""
    trigger_factors: List[str]
    intermediate_factors: List[str]
    outcome_factors: List[str]
    chain_strength: float
    confidence: float

@dataclass
class DecompositionReport:
    """Complete causal decomposition report."""
    score_decompositions: Dict[str, ScoreDecomposition]
    causal_chains: List[CausalChain]
    primary_drivers: List[CausalFactor]
    secondary_effects: List[CausalFactor]
    risk_factors: List[str]
    protective_factors: List[str]
    summary_insights: Dict[str, Any]

class CausalDecomposer:
    """
    Causal Analysis and Score Decomposition for Environmental Framework.
    
    Analyzes the causal relationships between environmental factors and
    decomposes score changes into interpretable components.
    """
    
    def __init__(self):
        """Initialize Causal Decomposer."""
        self.environmental_categories = {
            'climate': {
                'atmospheric': ['pressure', 'humidity', 'NO2'],
                'precipitation': ['precipitation', 'solar_radiation'],
                'thermal': ['temperature'],
                'wind': ['wind_speed']
            },
            'geographic': {
                'soil': ['soil_temperature', 'soil_moisture'],
                'water': ['reference_evapotranspiration'],
                'risk': ['urban_flood_risk']
            },
            'socioeconomic': {
                'health': ['life_expectancy'],
                'demographics': ['population_growth'],
                'infrastructure': ['railway_infrastructure']
            }
        }
        
        # Known causal relationships in environmental systems
        self.causal_relationships = {
            'temperature': {
                'directly_affects': ['soil_temperature', 'reference_evapotranspiration', 'humidity'],
                'indirectly_affects': ['soil_moisture', 'urban_flood_risk'],
                'feedback_loops': ['humidity', 'precipitation']
            },
            'precipitation': {
                'directly_affects': ['soil_moisture', 'urban_flood_risk', 'humidity'],
                'indirectly_affects': ['soil_temperature', 'life_expectancy'],
                'feedback_loops': ['humidity', 'temperature']
            },
            'urban_flood_risk': {
                'directly_affects': ['life_expectancy', 'population_growth'],
                'indirectly_affects': ['railway_infrastructure'],
                'feedback_loops': []
            }
        }
        
        logger.info("CausalDecomposer initialized")
    
    def decompose_scores(self, shap_result, baseline_data: Dict[str, float],
                        predicted_data: Dict[str, float]) -> Dict[str, ScoreDecomposition]:
        """
        Decompose score changes into causal factor contributions.
        
        Args:
            shap_result: SHAPResult object from SHAPExplainer
            baseline_data: Historical baseline values for each score component
            predicted_data: Predicted values for each score component
            
        Returns:
            Dictionary of score decompositions by score type
        """
        logger.info("Decomposing score contributions by causal factors")
        
        decompositions = {}
        
        # Decompose each score type
        for score_type in ['climate', 'geographic', 'economic']:
            if score_type in baseline_data and score_type in predicted_data:
                decomposition = self._decompose_single_score(
                    score_type, shap_result, 
                    baseline_data[score_type], 
                    predicted_data[score_type]
                )
                decompositions[score_type] = decomposition
        
        # Decompose final score if available
        if 'final' in baseline_data and 'final' in predicted_data:
            final_decomposition = self._decompose_final_score(
                shap_result, baseline_data['final'], predicted_data['final'],
                decompositions
            )
            decompositions['final'] = final_decomposition
        
        logger.info(f"Completed decomposition for {len(decompositions)} score types")
        return decompositions
    
    def identify_causal_chains(self, shap_result, 
                             min_chain_strength: float = 0.1) -> List[CausalChain]:
        """
        Identify causal chains in environmental changes.
        
        Args:
            shap_result: SHAPResult object
            min_chain_strength: Minimum strength threshold for causal chains
            
        Returns:
            List of identified causal chains
        """
        logger.info("Identifying causal chains in environmental factors")
        
        feature_names = shap_result.feature_names
        shap_values = shap_result.shap_values
        feature_importance = shap_result.feature_importance
        
        causal_chains = []
        
        # Analyze each potential trigger factor
        for trigger_feature in feature_names:
            if feature_importance[trigger_feature] < 0.05:  # Skip low-importance features
                continue
            
            # Find features this trigger might causally affect
            affected_features = self._find_causally_affected_features(
                trigger_feature, feature_names
            )
            
            if not affected_features:
                continue
            
            # Calculate chain strength
            chain_strength = self._calculate_chain_strength(
                trigger_feature, affected_features, shap_values, feature_names
            )
            
            if chain_strength >= min_chain_strength:
                # Classify features in the chain
                intermediate_factors, outcome_factors = self._classify_chain_factors(
                    trigger_feature, affected_features, feature_importance
                )
                
                # Calculate confidence
                confidence = self._calculate_chain_confidence(
                    [trigger_feature] + intermediate_factors + outcome_factors,
                    shap_values, feature_names
                )
                
                chain = CausalChain(
                    trigger_factors=[trigger_feature],
                    intermediate_factors=intermediate_factors,
                    outcome_factors=outcome_factors,
                    chain_strength=chain_strength,
                    confidence=confidence
                )
                
                causal_chains.append(chain)
        
        # Sort by chain strength
        causal_chains.sort(key=lambda c: c.chain_strength, reverse=True)
        
        logger.info(f"Identified {len(causal_chains)} causal chains")
        return causal_chains[:10]  # Return top 10 chains
    
    def analyze_score_drivers(self, shap_result, 
                            score_decompositions: Dict[str, ScoreDecomposition]) -> Tuple[List[CausalFactor], List[CausalFactor]]:
        """
        Identify primary drivers and secondary effects in score changes.
        
        Args:
            shap_result: SHAPResult object
            score_decompositions: Score decomposition results
            
        Returns:
            Tuple of (primary_drivers, secondary_effects)
        """
        logger.info("Analyzing primary drivers and secondary effects")
        
        all_factors = []
        
        # Collect all causal factors from decompositions
        for score_type, decomposition in score_decompositions.items():
            all_factors.extend(decomposition.factor_contributions)
        
        # Sort by contribution magnitude
        all_factors.sort(key=lambda f: abs(f.contribution), reverse=True)
        
        # Classify as primary or secondary based on contribution and confidence
        primary_threshold = 0.1  # Top 10% contribution
        confidence_threshold = 0.7
        
        primary_drivers = []
        secondary_effects = []
        
        for factor in all_factors:
            if (abs(factor.contribution) >= primary_threshold and 
                factor.confidence >= confidence_threshold):
                primary_drivers.append(factor)
            else:
                secondary_effects.append(factor)
        
        logger.info(f"Identified {len(primary_drivers)} primary drivers and {len(secondary_effects)} secondary effects")
        return primary_drivers[:10], secondary_effects[:20]  # Top 10 primary, top 20 secondary
    
    def identify_risk_factors(self, shap_result, 
                            causal_chains: List[CausalChain]) -> Tuple[List[str], List[str]]:
        """
        Identify risk factors and protective factors.
        
        Args:
            shap_result: SHAPResult object
            causal_chains: Identified causal chains
            
        Returns:
            Tuple of (risk_factors, protective_factors)
        """
        logger.info("Identifying risk and protective factors")
        
        feature_importance = shap_result.feature_importance
        shap_values = shap_result.shap_values
        feature_names = shap_result.feature_names
        
        risk_factors = []
        protective_factors = []
        
        # Analyze each feature's risk profile
        for i, feature in enumerate(feature_names):
            feature_shap = shap_values[:, i]
            
            # Calculate risk indicators
            mean_impact = np.mean(feature_shap)
            volatility = np.std(feature_shap)
            extreme_events = np.sum(np.abs(feature_shap) > 2 * np.std(feature_shap))
            
            # Classify as risk or protective factor
            if mean_impact > 0 and volatility > np.mean([np.std(shap_values[:, j]) for j in range(len(feature_names))]):
                # High positive impact with high volatility = risk factor
                risk_factors.append(feature)
            elif mean_impact < -0.05 and feature_importance[feature] > 0.02:
                # Consistent negative impact = protective factor
                protective_factors.append(feature)
        
        # Filter by involvement in causal chains
        chain_features = set()
        for chain in causal_chains:
            chain_features.update(chain.trigger_factors + chain.intermediate_factors + chain.outcome_factors)
        
        risk_factors = [f for f in risk_factors if f in chain_features]
        protective_factors = [f for f in protective_factors if f in chain_features]
        
        logger.info(f"Identified {len(risk_factors)} risk factors and {len(protective_factors)} protective factors")
        return risk_factors, protective_factors
    
    def generate_decomposition_report(self, shap_result, baseline_data: Dict[str, float],
                                    predicted_data: Dict[str, float]) -> DecompositionReport:
        """
        Generate comprehensive causal decomposition report.
        
        Args:
            shap_result: SHAPResult object
            baseline_data: Historical baseline values
            predicted_data: Predicted values
            
        Returns:
            Complete DecompositionReport
        """
        logger.info("Generating comprehensive causal decomposition report")
        
        # Run all analyses
        score_decompositions = self.decompose_scores(shap_result, baseline_data, predicted_data)
        causal_chains = self.identify_causal_chains(shap_result)
        primary_drivers, secondary_effects = self.analyze_score_drivers(shap_result, score_decompositions)
        risk_factors, protective_factors = self.identify_risk_factors(shap_result, causal_chains)
        
        # Generate summary insights
        summary_insights = self._generate_summary_insights(
            score_decompositions, causal_chains, primary_drivers, 
            secondary_effects, risk_factors, protective_factors
        )
        
        return DecompositionReport(
            score_decompositions=score_decompositions,
            causal_chains=causal_chains,
            primary_drivers=primary_drivers,
            secondary_effects=secondary_effects,
            risk_factors=risk_factors,
            protective_factors=protective_factors,
            summary_insights=summary_insights
        )
    
    # Helper methods
    def _decompose_single_score(self, score_type: str, shap_result, 
                              baseline_value: float, predicted_value: float) -> ScoreDecomposition:
        """Decompose a single score component."""
        # Get relevant features for this score type
        relevant_features = self._get_relevant_features(score_type, shap_result.feature_names)
        
        # Calculate factor contributions
        factor_contributions = []
        
        for feature in relevant_features:
            if feature in shap_result.feature_names:
                feature_idx = shap_result.feature_names.index(feature)
                
                # Calculate contribution
                shap_contribution = np.mean(shap_result.shap_values[:, feature_idx])
                confidence = self._calculate_factor_confidence(
                    shap_result.shap_values[:, feature_idx]
                )
                
                # Determine direction
                if shap_contribution > 0.01:
                    direction = 'positive'
                elif shap_contribution < -0.01:
                    direction = 'negative'
                else:
                    direction = 'neutral'
                
                # Find related features
                related_features = self._find_related_features(feature, relevant_features)
                
                factor = CausalFactor(
                    factor_name=feature,
                    contribution=float(shap_contribution),
                    confidence=confidence,
                    direction=direction,
                    category=score_type,
                    related_features=related_features
                )
                
                factor_contributions.append(factor)
        
        # Sort by contribution magnitude
        factor_contributions.sort(key=lambda f: abs(f.contribution), reverse=True)
        
        # Calculate uncertainty range
        total_change = predicted_value - baseline_value
        uncertainty_range = self._calculate_uncertainty_range(
            total_change, factor_contributions
        )
        
        return ScoreDecomposition(
            score_type=score_type,
            baseline_value=baseline_value,
            predicted_value=predicted_value,
            total_change=total_change,
            factor_contributions=factor_contributions,
            uncertainty_range=uncertainty_range
        )
    
    def _decompose_final_score(self, shap_result, baseline_value: float, 
                             predicted_value: float, 
                             component_decompositions: Dict[str, ScoreDecomposition]) -> ScoreDecomposition:
        """Decompose the final combined score."""
        # Aggregate factors from component scores
        all_factors = []
        for decomposition in component_decompositions.values():
            all_factors.extend(decomposition.factor_contributions)
        
        # Weight factors by their component score importance
        component_weights = {'climate': 0.3, 'geographic': 0.3, 'economic': 0.4}
        
        weighted_factors = []
        for factor in all_factors:
            weight = component_weights.get(factor.category, 1.0)
            weighted_contribution = factor.contribution * weight
            
            weighted_factor = CausalFactor(
                factor_name=factor.factor_name,
                contribution=weighted_contribution,
                confidence=factor.confidence,
                direction=factor.direction,
                category=factor.category,
                related_features=factor.related_features
            )
            weighted_factors.append(weighted_factor)
        
        # Sort and deduplicate
        weighted_factors.sort(key=lambda f: abs(f.contribution), reverse=True)
        
        total_change = predicted_value - baseline_value
        uncertainty_range = (total_change * 0.8, total_change * 1.2)  # ±20% uncertainty
        
        return ScoreDecomposition(
            score_type='final',
            baseline_value=baseline_value,
            predicted_value=predicted_value,
            total_change=total_change,
            factor_contributions=weighted_factors[:15],  # Top 15 factors
            uncertainty_range=uncertainty_range
        )
    
    def _get_relevant_features(self, score_type: str, feature_names: List[str]) -> List[str]:
        """Get features relevant to a specific score type."""
        if score_type not in self.environmental_categories:
            return feature_names
        
        relevant_keywords = []
        for subcategory, keywords in self.environmental_categories[score_type].items():
            relevant_keywords.extend(keywords)
        
        relevant_features = []
        for feature in feature_names:
            if any(keyword in feature.lower() for keyword in relevant_keywords):
                relevant_features.append(feature)
        
        return relevant_features
    
    def _calculate_factor_confidence(self, shap_values: np.ndarray) -> float:
        """Calculate confidence in a factor's contribution."""
        # Confidence based on consistency across samples
        mean_abs_shap = np.mean(np.abs(shap_values))
        std_shap = np.std(shap_values)
        
        if mean_abs_shap > 0:
            consistency = 1 - (std_shap / mean_abs_shap)
            return max(0.0, min(1.0, consistency))
        else:
            return 0.0
    
    def _find_related_features(self, feature: str, all_features: List[str]) -> List[str]:
        """Find features related to the given feature."""
        related = []
        
        # Check known causal relationships
        if feature in self.causal_relationships:
            relationships = self.causal_relationships[feature]
            for related_feature in (relationships.get('directly_affects', []) + 
                                  relationships.get('indirectly_affects', [])):
                if any(related_feature in f.lower() for f in all_features):
                    related.extend([f for f in all_features if related_feature in f.lower()])
        
        # Check feature name similarity
        feature_base = feature.split('_')[0].lower()
        for other_feature in all_features:
            if (other_feature != feature and 
                feature_base in other_feature.lower()):
                related.append(other_feature)
        
        return list(set(related))
    
    def _calculate_uncertainty_range(self, total_change: float, 
                                   factors: List[CausalFactor]) -> Tuple[float, float]:
        """Calculate uncertainty range for score change."""
        # Uncertainty based on factor confidence
        total_confidence = np.mean([f.confidence for f in factors]) if factors else 0.5
        uncertainty_factor = 1 - total_confidence
        
        uncertainty = abs(total_change) * uncertainty_factor
        
        return (total_change - uncertainty, total_change + uncertainty)
    
    def _find_causally_affected_features(self, trigger_feature: str, 
                                       all_features: List[str]) -> List[str]:
        """Find features that might be causally affected by trigger feature."""
        affected = []
        
        # Check known causal relationships
        if trigger_feature in self.causal_relationships:
            relationships = self.causal_relationships[trigger_feature]
            for affected_feature in (relationships.get('directly_affects', []) + 
                                   relationships.get('indirectly_affects', [])):
                matching_features = [f for f in all_features if affected_feature in f.lower()]
                affected.extend(matching_features)
        
        # Check by category relationships
        trigger_category = self._get_feature_category(trigger_feature)
        for feature in all_features:
            if feature != trigger_feature:
                feature_category = self._get_feature_category(feature)
                if self._has_causal_relationship(trigger_category, feature_category):
                    affected.append(feature)
        
        return list(set(affected))
    
    def _get_feature_category(self, feature: str) -> str:
        """Get the category of a feature."""
        for category, subcategories in self.environmental_categories.items():
            for keywords in subcategories.values():
                if any(keyword in feature.lower() for keyword in keywords):
                    return category
        return 'other'
    
    def _has_causal_relationship(self, category1: str, category2: str) -> bool:
        """Check if two categories have potential causal relationships."""
        causal_pairs = [
            ('climate', 'geographic'),
            ('climate', 'socioeconomic'),
            ('geographic', 'socioeconomic')
        ]
        
        return ((category1, category2) in causal_pairs or 
                (category2, category1) in causal_pairs)
    
    def _calculate_chain_strength(self, trigger: str, affected: List[str],
                                shap_values: np.ndarray, feature_names: List[str]) -> float:
        """Calculate the strength of a causal chain."""
        if not affected:
            return 0.0
        
        trigger_idx = feature_names.index(trigger) if trigger in feature_names else -1
        if trigger_idx == -1:
            return 0.0
        
        trigger_shap = shap_values[:, trigger_idx]
        
        correlations = []
        for affected_feature in affected:
            if affected_feature in feature_names:
                affected_idx = feature_names.index(affected_feature)
                affected_shap = shap_values[:, affected_idx]
                
                # Calculate correlation
                correlation = np.corrcoef(trigger_shap, affected_shap)[0, 1]
                if not np.isnan(correlation):
                    correlations.append(abs(correlation))
        
        return np.mean(correlations) if correlations else 0.0
    
    def _classify_chain_factors(self, trigger: str, affected: List[str],
                              feature_importance: Dict[str, float]) -> Tuple[List[str], List[str]]:
        """Classify factors in causal chain as intermediate or outcome."""
        # Sort affected features by importance
        affected_with_importance = [
            (f, feature_importance.get(f, 0)) for f in affected
        ]
        affected_with_importance.sort(key=lambda x: x[1], reverse=True)
        
        # Top half are intermediate, bottom half are outcomes
        mid_point = len(affected_with_importance) // 2
        
        intermediate = [f for f, _ in affected_with_importance[:mid_point]]
        outcome = [f for f, _ in affected_with_importance[mid_point:]]
        
        return intermediate, outcome
    
    def _calculate_chain_confidence(self, chain_features: List[str],
                                  shap_values: np.ndarray, feature_names: List[str]) -> float:
        """Calculate confidence in a causal chain."""
        if len(chain_features) < 2:
            return 0.0
        
        # Get SHAP values for chain features
        chain_indices = [
            feature_names.index(f) for f in chain_features 
            if f in feature_names
        ]
        
        if len(chain_indices) < 2:
            return 0.0
        
        # Calculate consistency of direction
        chain_shap = shap_values[:, chain_indices]
        correlations = []
        
        for i in range(len(chain_indices) - 1):
            correlation = np.corrcoef(chain_shap[:, i], chain_shap[:, i + 1])[0, 1]
            if not np.isnan(correlation):
                correlations.append(abs(correlation))
        
        return np.mean(correlations) if correlations else 0.0
    
    def _generate_summary_insights(self, score_decompositions: Dict[str, ScoreDecomposition],
                                 causal_chains: List[CausalChain],
                                 primary_drivers: List[CausalFactor],
                                 secondary_effects: List[CausalFactor],
                                 risk_factors: List[str],
                                 protective_factors: List[str]) -> Dict[str, Any]:
        """Generate summary insights from causal analysis."""
        insights = {}
        
        # Overall change magnitude
        if 'final' in score_decompositions:
            final_change = score_decompositions['final'].total_change
            insights['overall_change_magnitude'] = abs(final_change)
            insights['overall_change_direction'] = 'increase' if final_change > 0 else 'decrease'
        
        # Dominant categories
        category_contributions = defaultdict(list)
        for driver in primary_drivers:
            category_contributions[driver.category].append(abs(driver.contribution))
        
        insights['dominant_categories'] = {
            category: np.sum(contributions) 
            for category, contributions in category_contributions.items()
        }
        
        # Risk assessment
        insights['risk_level'] = 'high' if len(risk_factors) > 3 else 'moderate' if len(risk_factors) > 1 else 'low'
        insights['protection_level'] = 'high' if len(protective_factors) > 2 else 'moderate' if len(protective_factors) > 0 else 'low'
        
        # Causal complexity
        avg_chain_length = np.mean([
            len(chain.trigger_factors) + len(chain.intermediate_factors) + len(chain.outcome_factors)
            for chain in causal_chains
        ]) if causal_chains else 0
        
        insights['causal_complexity'] = 'high' if avg_chain_length > 5 else 'moderate' if avg_chain_length > 3 else 'low'
        
        # Key recommendations
        insights['key_recommendations'] = self._generate_key_recommendations(
            primary_drivers, risk_factors, protective_factors
        )
        
        return insights
    
    def _generate_key_recommendations(self, primary_drivers: List[CausalFactor],
                                    risk_factors: List[str],
                                    protective_factors: List[str]) -> List[str]:
        """Generate key recommendations based on causal analysis."""
        recommendations = []
        
        if primary_drivers:
            top_driver = primary_drivers[0]
            recommendations.append(
                f"Primary driver '{top_driver.factor_name}' shows {top_driver.direction} impact - "
                f"monitor closely and consider targeted interventions"
            )
        
        if risk_factors:
            recommendations.append(
                f"High-risk factors identified: {', '.join(risk_factors[:3])} - "
                f"implement risk mitigation strategies"
            )
        
        if protective_factors:
            recommendations.append(
                f"Protective factors available: {', '.join(protective_factors[:2])} - "
                f"strengthen these positive influences"
            )
        
        # Category-specific recommendations
        climate_drivers = [d for d in primary_drivers if d.category == 'climate']
        if climate_drivers:
            recommendations.append(
                "Climate factors are primary drivers - focus on meteorological monitoring and climate adaptation"
            )
        
        return recommendations[:5]  # Top 5 recommendations 