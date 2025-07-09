"""
Feature Analyzer for Environmental Change Index Framework

Provides advanced feature importance analysis, interaction effects,
and clustering of feature behaviors for environmental prediction models.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass
import logging
from collections import defaultdict

# Scientific computing imports
try:
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    from scipy.stats import pearsonr, spearmanr
    from scipy.cluster.hierarchy import linkage, fcluster
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("Scikit-learn not available for advanced analysis")

logger = logging.getLogger(__name__)

@dataclass
class FeatureGroup:
    """Represents a group of related features."""
    name: str
    features: List[str]
    importance_score: float
    interaction_strength: float
    category: str  # 'climate', 'geographic', 'time_based', etc.

@dataclass
class FeatureInteraction:
    """Represents interaction between two features."""
    feature_1: str
    feature_2: str
    interaction_strength: float
    correlation: float
    interaction_type: str  # 'synergistic', 'antagonistic', 'independent'

@dataclass
class AnalysisReport:
    """Complete feature analysis report."""
    feature_importance: Dict[str, float]
    feature_groups: List[FeatureGroup]
    top_interactions: List[FeatureInteraction]
    redundant_features: List[str]
    critical_features: List[str]
    stability_metrics: Dict[str, float]
    recommendations: List[str]

class FeatureAnalyzer:
    """
    Advanced Feature Analysis for Environmental Models.
    
    Analyzes feature importance, interactions, groupings, and provides
    insights for model interpretation and optimization.
    """
    
    def __init__(self):
        """Initialize Feature Analyzer."""
        self.feature_categories = {
            'climate': [
                'pressure', 'humidity', 'NO2', 'precipitation', 
                'solar_radiation', 'temperature', 'wind_speed'
            ],
            'geographic': [
                'soil_temperature', 'reference_evapotranspiration',
                'urban_flood_risk', 'soil_moisture'
            ],
            'socioeconomic': [
                'life_expectancy', 'population_growth', 'railway_infrastructure'
            ],
            'time_based': [
                'lag_', 'ma_', 'trend_', 'seasonal_', 'rolling_'
            ]
        }
        logger.info("FeatureAnalyzer initialized")
    
    def analyze_feature_importance(self, shap_result, 
                                 importance_threshold: float = 0.01) -> Dict[str, Any]:
        """
        Comprehensive feature importance analysis.
        
        Args:
            shap_result: SHAPResult object from SHAPExplainer
            importance_threshold: Minimum importance to consider feature significant
            
        Returns:
            Dictionary with detailed importance analysis
        """
        logger.info("Analyzing feature importance patterns")
        
        feature_importance = shap_result.feature_importance
        shap_values = shap_result.shap_values
        feature_names = shap_result.feature_names
        
        # Basic importance statistics
        importance_stats = self._calculate_importance_statistics(feature_importance)
        
        # Categorize features by importance
        critical_features = [
            f for f, imp in feature_importance.items() 
            if imp >= importance_stats['q75']
        ]
        
        moderate_features = [
            f for f, imp in feature_importance.items()
            if importance_stats['q25'] <= imp < importance_stats['q75']
        ]
        
        low_importance_features = [
            f for f, imp in feature_importance.items()
            if imp < importance_threshold
        ]
        
        # Stability analysis (variance of SHAP values across samples)
        stability_metrics = self._analyze_feature_stability(shap_values, feature_names)
        
        # Group features by category
        categorized_features = self._categorize_features(feature_names)
        
        # Category-wise importance
        category_importance = self._calculate_category_importance(
            feature_importance, categorized_features
        )
        
        return {
            'importance_statistics': importance_stats,
            'feature_rankings': {
                'critical_features': critical_features,
                'moderate_features': moderate_features,
                'low_importance_features': low_importance_features
            },
            'stability_metrics': stability_metrics,
            'categorized_features': categorized_features,
            'category_importance': category_importance,
            'feature_count_by_category': {
                cat: len(features) for cat, features in categorized_features.items()
            }
        }
    
    def analyze_feature_interactions(self, shap_result, 
                                   top_k: int = 20) -> Dict[str, Any]:
        """
        Analyze feature interactions and dependencies.
        
        Args:
            shap_result: SHAPResult object
            top_k: Number of top interactions to analyze
            
        Returns:
            Interaction analysis results
        """
        logger.info("Analyzing feature interactions")
        
        feature_names = shap_result.feature_names
        shap_values = shap_result.shap_values
        
        # Calculate pairwise interactions
        interactions = []
        
        for i in range(len(feature_names)):
            for j in range(i + 1, len(feature_names)):
                feature_1 = feature_names[i]
                feature_2 = feature_names[j]
                
                # Calculate interaction metrics
                interaction_strength = self._calculate_interaction_strength(
                    shap_values[:, i], shap_values[:, j]
                )
                
                correlation = self._calculate_feature_correlation(
                    shap_values[:, i], shap_values[:, j]
                )
                
                interaction_type = self._classify_interaction_type(
                    shap_values[:, i], shap_values[:, j], correlation
                )
                
                interactions.append(FeatureInteraction(
                    feature_1=feature_1,
                    feature_2=feature_2,
                    interaction_strength=interaction_strength,
                    correlation=correlation,
                    interaction_type=interaction_type
                ))
        
        # Sort interactions by strength
        interactions.sort(key=lambda x: x.interaction_strength, reverse=True)
        top_interactions = interactions[:top_k]
        
        # Analyze interaction patterns
        interaction_patterns = self._analyze_interaction_patterns(interactions)
        
        # Cross-category interactions
        cross_category_interactions = self._find_cross_category_interactions(
            top_interactions
        )
        
        return {
            'top_interactions': top_interactions,
            'interaction_patterns': interaction_patterns,
            'cross_category_interactions': cross_category_interactions,
            'interaction_summary': {
                'total_interactions': len(interactions),
                'strong_interactions': len([i for i in interactions if i.interaction_strength > 0.1]),
                'synergistic_count': len([i for i in interactions if i.interaction_type == 'synergistic']),
                'antagonistic_count': len([i for i in interactions if i.interaction_type == 'antagonistic'])
            }
        }
    
    def identify_feature_groups(self, shap_result, 
                              n_groups: int = 5) -> List[FeatureGroup]:
        """
        Identify groups of features with similar behavior patterns.
        
        Args:
            shap_result: SHAPResult object
            n_groups: Number of feature groups to identify
            
        Returns:
            List of FeatureGroup objects
        """
        if not SKLEARN_AVAILABLE:
            logger.warning("Scikit-learn required for feature grouping")
            return self._create_category_based_groups(shap_result)
        
        logger.info("Identifying feature groups using clustering")
        
        shap_values = shap_result.shap_values
        feature_names = shap_result.feature_names
        feature_importance = shap_result.feature_importance
        
        # Transpose SHAP values to cluster features by their behavior patterns
        feature_patterns = shap_values.T  # Shape: (n_features, n_samples)
        
        # Apply clustering
        kmeans = KMeans(n_clusters=n_groups, random_state=42)
        cluster_labels = kmeans.fit_predict(feature_patterns)
        
        # Create feature groups
        groups = []
        for group_id in range(n_groups):
            group_features = [
                feature_names[i] for i in range(len(feature_names))
                if cluster_labels[i] == group_id
            ]
            
            if not group_features:
                continue
            
            # Calculate group importance and interaction strength
            group_importance = np.mean([
                feature_importance[f] for f in group_features
            ])
            
            group_interaction_strength = self._calculate_group_interaction_strength(
                group_features, shap_values, feature_names
            )
            
            # Determine group category
            group_category = self._determine_group_category(group_features)
            
            group = FeatureGroup(
                name=f"Group_{group_id}_{group_category}",
                features=group_features,
                importance_score=group_importance,
                interaction_strength=group_interaction_strength,
                category=group_category
            )
            
            groups.append(group)
        
        # Sort groups by importance
        groups.sort(key=lambda g: g.importance_score, reverse=True)
        
        logger.info(f"Identified {len(groups)} feature groups")
        return groups
    
    def find_redundant_features(self, shap_result, 
                              correlation_threshold: float = 0.8,
                              importance_threshold: float = 0.01) -> List[str]:
        """
        Identify potentially redundant features.
        
        Args:
            shap_result: SHAPResult object
            correlation_threshold: Correlation threshold for redundancy
            importance_threshold: Minimum importance to consider
            
        Returns:
            List of potentially redundant feature names
        """
        logger.info("Identifying redundant features")
        
        shap_values = shap_result.shap_values
        feature_names = shap_result.feature_names
        feature_importance = shap_result.feature_importance
        
        redundant_features = []
        
        for i in range(len(feature_names)):
            for j in range(i + 1, len(feature_names)):
                feature_1 = feature_names[i]
                feature_2 = feature_names[j]
                
                # Skip if either feature is already identified as redundant
                if feature_1 in redundant_features or feature_2 in redundant_features:
                    continue
                
                # Calculate correlation between SHAP values
                correlation = abs(self._calculate_feature_correlation(
                    shap_values[:, i], shap_values[:, j]
                ))
                
                if correlation >= correlation_threshold:
                    # Keep the more important feature
                    imp_1 = feature_importance[feature_1]
                    imp_2 = feature_importance[feature_2]
                    
                    if imp_1 < imp_2:
                        redundant_features.append(feature_1)
                    else:
                        redundant_features.append(feature_2)
        
        # Also add features with very low importance
        low_importance_features = [
            f for f, imp in feature_importance.items()
            if imp < importance_threshold and f not in redundant_features
        ]
        
        redundant_features.extend(low_importance_features)
        
        logger.info(f"Identified {len(redundant_features)} potentially redundant features")
        return list(set(redundant_features))
    
    def generate_analysis_report(self, shap_result) -> AnalysisReport:
        """
        Generate comprehensive feature analysis report.
        
        Args:
            shap_result: SHAPResult object
            
        Returns:
            Complete AnalysisReport object
        """
        logger.info("Generating comprehensive feature analysis report")
        
        # Run all analyses
        importance_analysis = self.analyze_feature_importance(shap_result)
        interaction_analysis = self.analyze_feature_interactions(shap_result)
        feature_groups = self.identify_feature_groups(shap_result)
        redundant_features = self.find_redundant_features(shap_result)
        
        # Extract key information
        critical_features = importance_analysis['feature_rankings']['critical_features']
        stability_metrics = importance_analysis['stability_metrics']
        top_interactions = interaction_analysis['top_interactions']
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            importance_analysis, interaction_analysis, feature_groups, redundant_features
        )
        
        return AnalysisReport(
            feature_importance=shap_result.feature_importance,
            feature_groups=feature_groups,
            top_interactions=top_interactions,
            redundant_features=redundant_features,
            critical_features=critical_features,
            stability_metrics=stability_metrics,
            recommendations=recommendations
        )
    
    # Helper methods
    def _calculate_importance_statistics(self, feature_importance: Dict[str, float]) -> Dict[str, float]:
        """Calculate descriptive statistics for feature importance."""
        values = list(feature_importance.values())
        return {
            'mean': np.mean(values),
            'std': np.std(values),
            'min': np.min(values),
            'max': np.max(values),
            'q25': np.percentile(values, 25),
            'q50': np.percentile(values, 50),
            'q75': np.percentile(values, 75)
        }
    
    def _analyze_feature_stability(self, shap_values: np.ndarray, 
                                 feature_names: List[str]) -> Dict[str, float]:
        """Analyze stability of feature importance across samples."""
        stability_metrics = {}
        
        for i, feature in enumerate(feature_names):
            feature_shap = shap_values[:, i]
            
            # Coefficient of variation as stability metric
            mean_abs_shap = np.mean(np.abs(feature_shap))
            std_shap = np.std(feature_shap)
            
            if mean_abs_shap > 0:
                cv = std_shap / mean_abs_shap
            else:
                cv = 0
            
            stability_metrics[feature] = float(cv)
        
        return stability_metrics
    
    def _categorize_features(self, feature_names: List[str]) -> Dict[str, List[str]]:
        """Categorize features based on name patterns."""
        categorized = defaultdict(list)
        
        for feature in feature_names:
            assigned = False
            
            # Check each category
            for category, keywords in self.feature_categories.items():
                if any(keyword in feature.lower() for keyword in keywords):
                    categorized[category].append(feature)
                    assigned = True
                    break
            
            if not assigned:
                categorized['other'].append(feature)
        
        return dict(categorized)
    
    def _calculate_category_importance(self, feature_importance: Dict[str, float],
                                     categorized_features: Dict[str, List[str]]) -> Dict[str, float]:
        """Calculate importance score for each feature category."""
        category_importance = {}
        
        for category, features in categorized_features.items():
            if features:
                importance_scores = [feature_importance.get(f, 0) for f in features]
                category_importance[category] = float(np.mean(importance_scores))
            else:
                category_importance[category] = 0.0
        
        return category_importance
    
    def _calculate_interaction_strength(self, shap_1: np.ndarray, 
                                      shap_2: np.ndarray) -> float:
        """Calculate interaction strength between two features."""
        # Use mutual variation as interaction strength
        variance_product = np.var(shap_1) * np.var(shap_2)
        if variance_product > 0:
            covariance = np.cov(shap_1, shap_2)[0, 1]
            interaction_strength = abs(covariance) / np.sqrt(variance_product)
        else:
            interaction_strength = 0.0
        
        return float(interaction_strength)
    
    def _calculate_feature_correlation(self, shap_1: np.ndarray, 
                                     shap_2: np.ndarray) -> float:
        """Calculate correlation between SHAP values of two features."""
        try:
            correlation, _ = pearsonr(shap_1, shap_2)
            return float(correlation) if not np.isnan(correlation) else 0.0
        except:
            return 0.0
    
    def _classify_interaction_type(self, shap_1: np.ndarray, shap_2: np.ndarray,
                                 correlation: float) -> str:
        """Classify the type of interaction between features."""
        if abs(correlation) < 0.1:
            return 'independent'
        elif correlation > 0.5:
            return 'synergistic'
        elif correlation < -0.5:
            return 'antagonistic'
        else:
            return 'moderate'
    
    def _analyze_interaction_patterns(self, interactions: List[FeatureInteraction]) -> Dict[str, Any]:
        """Analyze patterns in feature interactions."""
        return {
            'strongest_interaction': interactions[0] if interactions else None,
            'avg_interaction_strength': np.mean([i.interaction_strength for i in interactions]),
            'interaction_types': {
                interaction_type: len([i for i in interactions if i.interaction_type == interaction_type])
                for interaction_type in ['synergistic', 'antagonistic', 'independent', 'moderate']
            }
        }
    
    def _find_cross_category_interactions(self, interactions: List[FeatureInteraction]) -> List[FeatureInteraction]:
        """Find interactions between features from different categories."""
        categorized = self._categorize_features(
            list(set([i.feature_1 for i in interactions] + [i.feature_2 for i in interactions]))
        )
        
        # Create feature to category mapping
        feature_to_category = {}
        for category, features in categorized.items():
            for feature in features:
                feature_to_category[feature] = category
        
        # Find cross-category interactions
        cross_category = []
        for interaction in interactions:
            cat1 = feature_to_category.get(interaction.feature_1, 'other')
            cat2 = feature_to_category.get(interaction.feature_2, 'other')
            
            if cat1 != cat2:
                cross_category.append(interaction)
        
        return cross_category
    
    def _calculate_group_interaction_strength(self, group_features: List[str],
                                            shap_values: np.ndarray,
                                            feature_names: List[str]) -> float:
        """Calculate average interaction strength within a feature group."""
        if len(group_features) < 2:
            return 0.0
        
        feature_indices = [feature_names.index(f) for f in group_features if f in feature_names]
        
        if len(feature_indices) < 2:
            return 0.0
        
        interaction_strengths = []
        for i in range(len(feature_indices)):
            for j in range(i + 1, len(feature_indices)):
                idx1, idx2 = feature_indices[i], feature_indices[j]
                strength = self._calculate_interaction_strength(
                    shap_values[:, idx1], shap_values[:, idx2]
                )
                interaction_strengths.append(strength)
        
        return float(np.mean(interaction_strengths)) if interaction_strengths else 0.0
    
    def _determine_group_category(self, group_features: List[str]) -> str:
        """Determine the primary category of a feature group."""
        categorized = self._categorize_features(group_features)
        
        # Find the category with the most features
        max_count = 0
        primary_category = 'mixed'
        
        for category, features in categorized.items():
            if len(features) > max_count:
                max_count = len(features)
                primary_category = category
        
        return primary_category
    
    def _create_category_based_groups(self, shap_result) -> List[FeatureGroup]:
        """Create feature groups based on categories when clustering is not available."""
        feature_names = shap_result.feature_names
        feature_importance = shap_result.feature_importance
        categorized = self._categorize_features(feature_names)
        
        groups = []
        for category, features in categorized.items():
            if not features:
                continue
            
            group_importance = np.mean([feature_importance[f] for f in features])
            
            group = FeatureGroup(
                name=f"Category_{category}",
                features=features,
                importance_score=group_importance,
                interaction_strength=0.0,  # Cannot calculate without clustering
                category=category
            )
            groups.append(group)
        
        return sorted(groups, key=lambda g: g.importance_score, reverse=True)
    
    def _generate_recommendations(self, importance_analysis: Dict,
                                interaction_analysis: Dict,
                                feature_groups: List[FeatureGroup],
                                redundant_features: List[str]) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        # Critical features recommendation
        critical_features = importance_analysis['feature_rankings']['critical_features']
        if critical_features:
            recommendations.append(
                f"Focus monitoring on {len(critical_features)} critical features: {', '.join(critical_features[:3])}..."
            )
        
        # Redundant features recommendation
        if redundant_features:
            recommendations.append(
                f"Consider removing {len(redundant_features)} redundant features to improve model efficiency"
            )
        
        # Top interactions recommendation
        top_interactions = interaction_analysis['top_interactions'][:3]
        if top_interactions:
            recommendations.append(
                f"Key feature interactions to monitor: {top_interactions[0].feature_1} ↔ {top_interactions[0].feature_2}"
            )
        
        # Category importance recommendation
        category_importance = importance_analysis['category_importance']
        if category_importance:
            top_category = max(category_importance.items(), key=lambda x: x[1])
            recommendations.append(
                f"'{top_category[0]}' category shows highest impact - prioritize data quality in this area"
            )
        
        # Feature stability recommendation
        stability_metrics = importance_analysis['stability_metrics']
        unstable_features = [f for f, cv in stability_metrics.items() if cv > 2.0]
        if unstable_features:
            recommendations.append(
                f"Monitor {len(unstable_features)} unstable features that show high variance across predictions"
            )
        
        return recommendations 