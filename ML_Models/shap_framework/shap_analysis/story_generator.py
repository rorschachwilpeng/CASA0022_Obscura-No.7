"""
Story Generator for Environmental Change Index Framework

Converts SHAP analysis results into human-readable natural language explanations,
creating compelling narratives about environmental changes and their causes.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

@dataclass
class StoryTemplate:
    """Template for generating specific types of stories."""
    story_type: str
    template: str
    required_data: List[str]
    confidence_threshold: float

@dataclass
class StoryElement:
    """Individual element of a story."""
    element_type: str  # 'introduction', 'main_finding', 'supporting_detail', 'conclusion'
    content: str
    confidence: float
    data_source: str

@dataclass
class EnvironmentalStory:
    """Complete environmental change story."""
    title: str
    summary: str
    story_elements: List[StoryElement]
    key_insights: List[str]
    confidence_level: str
    metadata: Dict[str, Any]

class StoryGenerator:
    """
    Natural Language Story Generator for Environmental Analysis.
    
    Converts technical SHAP analysis results into engaging, understandable
    narratives about environmental changes and their causal factors.
    """
    
    def __init__(self):
        """Initialize Story Generator."""
        self.story_templates = self._initialize_templates()
        self.narrative_patterns = self._initialize_narrative_patterns()
        self.environmental_vocabulary = self._initialize_vocabulary()
        
        logger.info("StoryGenerator initialized")
    
    def generate_comprehensive_story(self, shap_result, feature_analysis_report,
                                   decomposition_report, location: str = "the analyzed region") -> EnvironmentalStory:
        """
        Generate comprehensive environmental change story.
        
        Args:
            shap_result: SHAPResult object
            feature_analysis_report: AnalysisReport from FeatureAnalyzer
            decomposition_report: DecompositionReport from CausalDecomposer
            location: Name of the location being analyzed
            
        Returns:
            Complete EnvironmentalStory object
        """
        logger.info(f"Generating comprehensive environmental story for {location}")
        
        # Generate story elements
        story_elements = []
        
        # 1. Introduction
        intro = self._generate_introduction(shap_result, location)
        story_elements.append(intro)
        
        # 2. Main findings
        main_findings = self._generate_main_findings(decomposition_report)
        story_elements.extend(main_findings)
        
        # 3. Feature analysis narrative
        feature_narrative = self._generate_feature_narrative(feature_analysis_report)
        story_elements.extend(feature_narrative)
        
        # 4. Causal chain stories
        causal_stories = self._generate_causal_chain_stories(decomposition_report.causal_chains)
        story_elements.extend(causal_stories)
        
        # 5. Risk and protection narrative
        risk_narrative = self._generate_risk_narrative(
            decomposition_report.risk_factors, 
            decomposition_report.protective_factors
        )
        story_elements.append(risk_narrative)
        
        # 6. Conclusion and recommendations
        conclusion = self._generate_conclusion(decomposition_report)
        story_elements.append(conclusion)
        
        # Generate title and summary
        title = self._generate_title(decomposition_report, location)
        summary = self._generate_summary(story_elements)
        
        # Extract key insights
        key_insights = self._extract_key_insights(
            shap_result, feature_analysis_report, decomposition_report
        )
        
        # Calculate overall confidence
        confidence_level = self._calculate_story_confidence(story_elements)
        
        # Create metadata
        metadata = {
            'generation_timestamp': datetime.now().isoformat(),
            'location': location,
            'analysis_scope': {
                'feature_count': len(shap_result.feature_names),
                'sample_count': len(shap_result.shap_values),
                'model_type': shap_result.model_metadata.get('model_type', 'unknown')
            },
            'story_statistics': {
                'element_count': len(story_elements),
                'word_count': sum(len(elem.content.split()) for elem in story_elements),
                'confidence_distribution': self._get_confidence_distribution(story_elements)
            }
        }
        
        return EnvironmentalStory(
            title=title,
            summary=summary,
            story_elements=story_elements,
            key_insights=key_insights,
            confidence_level=confidence_level,
            metadata=metadata
        )
    
    def generate_score_explanation(self, score_decomposition, score_type: str) -> str:
        """
        Generate explanation for a specific score component.
        
        Args:
            score_decomposition: ScoreDecomposition object
            score_type: Type of score ('climate', 'geographic', 'economic', 'final')
            
        Returns:
            Natural language explanation of the score
        """
        logger.info(f"Generating explanation for {score_type} score")
        
        change = score_decomposition.total_change
        baseline = score_decomposition.baseline_value
        predicted = score_decomposition.predicted_value
        
        # Determine change direction and magnitude
        if abs(change) < 0.1:
            change_description = "remains relatively stable"
            magnitude = "minimal"
        elif abs(change) < 0.5:
            change_description = "shows moderate change"
            magnitude = "moderate"
        else:
            change_description = "experiences significant change"
            magnitude = "substantial"
        
        direction = "increases" if change > 0 else "decreases"
        
        # Get top contributing factors
        top_factors = score_decomposition.factor_contributions[:3]
        
        # Generate explanation
        explanation = f"The {score_type} score {change_description}, "
        explanation += f"{direction} by {abs(change):.2f} points "
        explanation += f"from a baseline of {baseline:.2f} to {predicted:.2f}. "
        
        if top_factors:
            explanation += f"This {magnitude} change is primarily driven by "
            
            factor_descriptions = []
            for factor in top_factors:
                impact_type = "positive" if factor.contribution > 0 else "negative"
                factor_descriptions.append(
                    f"{factor.factor_name} (showing {impact_type} impact of {abs(factor.contribution):.3f})"
                )
            
            if len(factor_descriptions) == 1:
                explanation += factor_descriptions[0]
            elif len(factor_descriptions) == 2:
                explanation += f"{factor_descriptions[0]} and {factor_descriptions[1]}"
            else:
                explanation += f"{', '.join(factor_descriptions[:-1])}, and {factor_descriptions[-1]}"
            
            explanation += ". "
        
        # Add uncertainty information
        uncertainty_range = score_decomposition.uncertainty_range
        uncertainty_width = uncertainty_range[1] - uncertainty_range[0]
        
        if uncertainty_width > abs(change) * 0.5:
            explanation += "However, there is considerable uncertainty in this prediction, "
            explanation += f"with the actual change potentially ranging from {uncertainty_range[0]:.2f} to {uncertainty_range[1]:.2f}."
        else:
            explanation += f"The prediction confidence is relatively high, "
            explanation += f"with uncertainty range of ±{uncertainty_width/2:.2f}."
        
        return explanation
    
    def generate_feature_story(self, feature_name: str, shap_result, 
                             feature_analysis_report) -> str:
        """
        Generate story for a specific feature's impact.
        
        Args:
            feature_name: Name of the feature
            shap_result: SHAPResult object
            feature_analysis_report: AnalysisReport object
            
        Returns:
            Natural language story about the feature
        """
        if feature_name not in shap_result.feature_names:
            return f"Feature '{feature_name}' not found in the analysis."
        
        feature_idx = shap_result.feature_names.index(feature_name)
        feature_shap = shap_result.shap_values[:, feature_idx]
        importance = shap_result.feature_importance[feature_name]
        
        # Get feature category
        categorized_features = feature_analysis_report.feature_importance
        feature_category = self._get_feature_category_from_name(feature_name)
        
        # Generate story
        story = f"The feature '{self._humanize_feature_name(feature_name)}' "
        
        # Importance description
        if importance > 0.1:
            story += "plays a crucial role in environmental changes, "
        elif importance > 0.05:
            story += "has a moderate influence on environmental patterns, "
        else:
            story += "provides subtle but measurable effects, "
        
        story += f"accounting for {importance*100:.1f}% of the overall model's decision-making process. "
        
        # Impact pattern analysis
        mean_impact = np.mean(feature_shap)
        impact_consistency = 1 - (np.std(feature_shap) / (np.mean(np.abs(feature_shap)) + 1e-8))
        
        if mean_impact > 0.01:
            story += "On average, this factor tends to push environmental conditions toward higher risk levels"
        elif mean_impact < -0.01:
            story += "Generally, this factor contributes to environmental stability and lower risk conditions"
        else:
            story += "The factor shows mixed effects, sometimes increasing and sometimes decreasing environmental risks"
        
        if impact_consistency > 0.7:
            story += " with high consistency across different scenarios."
        elif impact_consistency > 0.4:
            story += " with moderate variability depending on conditions."
        else:
            story += " with significant variability across different environmental contexts."
        
        # Category context
        category_context = self._get_category_context(feature_category)
        if category_context:
            story += f" {category_context}"
        
        return story
    
    def generate_comparison_story(self, shap_results: Dict[str, Any], 
                                locations: List[str]) -> str:
        """
        Generate comparative story across multiple locations.
        
        Args:
            shap_results: Dictionary of SHAP results by location
            locations: List of location names
            
        Returns:
            Comparative analysis story
        """
        logger.info(f"Generating comparison story for {len(locations)} locations")
        
        if len(locations) < 2:
            return "Comparison requires at least two locations."
        
        story = f"Comparing environmental change patterns across {', '.join(locations[:-1])} and {locations[-1]}, "
        story += "we observe distinct regional variations in environmental risk factors and their impacts.\n\n"
        
        # Find common high-importance features
        common_features = self._find_common_important_features(shap_results)
        
        if common_features:
            story += f"Several factors consistently show high importance across all regions: "
            story += f"{', '.join([self._humanize_feature_name(f) for f in common_features[:3]])}. "
            story += "These represent universal environmental drivers that affect all analyzed areas.\n\n"
        
        # Identify unique characteristics of each location
        for location in locations:
            if location in shap_results:
                unique_factors = self._find_unique_high_impact_factors(
                    shap_results[location], shap_results, location
                )
                
                if unique_factors:
                    story += f"{location} shows distinctive patterns in {', '.join(unique_factors[:2])}, "
                    story += "indicating region-specific environmental challenges or advantages.\n"
        
        story += "\nThese regional differences highlight the importance of localized environmental monitoring and targeted intervention strategies."
        
        return story
    
    # Helper methods for story generation
    def _generate_introduction(self, shap_result, location: str) -> StoryElement:
        """Generate introduction story element."""
        content = f"Environmental analysis of {location} reveals complex patterns of change "
        content += f"across {len(shap_result.feature_names)} environmental indicators. "
        content += f"Using advanced machine learning interpretability techniques, we analyzed "
        content += f"{len(shap_result.shap_values)} data points to understand the driving forces "
        content += "behind environmental changes in this region."
        
        return StoryElement(
            element_type='introduction',
            content=content,
            confidence=0.9,
            data_source='model_metadata'
        )
    
    def _generate_main_findings(self, decomposition_report) -> List[StoryElement]:
        """Generate main findings story elements."""
        elements = []
        
        # Overall change summary
        if 'final' in decomposition_report.score_decompositions:
            final_score = decomposition_report.score_decompositions['final']
            change = final_score.total_change
            
            if abs(change) > 0.5:
                severity = "significant"
                urgency = "requiring immediate attention"
            elif abs(change) > 0.2:
                severity = "moderate"
                urgency = "warranting careful monitoring"
            else:
                severity = "minor"
                urgency = "suggesting stable conditions"
            
            direction = "deterioration" if change > 0 else "improvement"
            
            content = f"The analysis reveals {severity} environmental {direction}, "
            content += f"with an overall change index of {change:+.2f}, {urgency}. "
            
            # Top driving factors
            top_drivers = decomposition_report.primary_drivers[:3]
            if top_drivers:
                content += f"The primary drivers of this change are "
                driver_names = [self._humanize_feature_name(d.factor_name) for d in top_drivers]
                content += f"{', '.join(driver_names[:-1])} and {driver_names[-1]}."
            
            elements.append(StoryElement(
                element_type='main_finding',
                content=content,
                confidence=0.85,
                data_source='score_decomposition'
            ))
        
        return elements
    
    def _generate_feature_narrative(self, feature_analysis_report) -> List[StoryElement]:
        """Generate feature analysis narrative."""
        elements = []
        
        # Critical features story
        critical_features = feature_analysis_report.critical_features[:5]
        if critical_features:
            content = "Several environmental factors stand out as particularly influential: "
            feature_descriptions = []
            
            for feature in critical_features:
                humanized = self._humanize_feature_name(feature)
                category = self._get_feature_category_from_name(feature)
                feature_descriptions.append(f"{humanized} ({category} indicator)")
            
            content += f"{', '.join(feature_descriptions)}. "
            content += "These factors require prioritized monitoring and management attention."
            
            elements.append(StoryElement(
                element_type='supporting_detail',
                content=content,
                confidence=0.8,
                data_source='feature_analysis'
            ))
        
        # Feature interactions story
        top_interactions = feature_analysis_report.top_interactions[:3]
        if top_interactions:
            content = "Notable interactions between environmental factors include "
            
            interaction_descriptions = []
            for interaction in top_interactions:
                feat1 = self._humanize_feature_name(interaction.feature_1)
                feat2 = self._humanize_feature_name(interaction.feature_2)
                interaction_type = interaction.interaction_type
                
                if interaction_type == 'synergistic':
                    desc = f"{feat1} and {feat2} working together to amplify effects"
                elif interaction_type == 'antagonistic':
                    desc = f"{feat1} and {feat2} counteracting each other's influence"
                else:
                    desc = f"{feat1} and {feat2} showing complex interdependencies"
                
                interaction_descriptions.append(desc)
            
            content += f"{'; '.join(interaction_descriptions)}. "
            content += "Understanding these interactions is crucial for effective environmental management."
            
            elements.append(StoryElement(
                element_type='supporting_detail',
                content=content,
                confidence=0.75,
                data_source='feature_interactions'
            ))
        
        return elements
    
    def _generate_causal_chain_stories(self, causal_chains) -> List[StoryElement]:
        """Generate stories for causal chains."""
        elements = []
        
        # Focus on the strongest causal chain
        if causal_chains:
            strongest_chain = causal_chains[0]
            
            trigger = self._humanize_feature_name(strongest_chain.trigger_factors[0])
            
            content = f"A particularly important causal pathway begins with changes in {trigger}, "
            
            if strongest_chain.intermediate_factors:
                intermediates = [self._humanize_feature_name(f) for f in strongest_chain.intermediate_factors[:2]]
                content += f"which subsequently influences {' and '.join(intermediates)}, "
            
            if strongest_chain.outcome_factors:
                outcomes = [self._humanize_feature_name(f) for f in strongest_chain.outcome_factors[:2]]
                content += f"ultimately affecting {' and '.join(outcomes)}. "
            
            content += f"This causal chain shows {strongest_chain.confidence:.0%} confidence, "
            content += "indicating a reliable pattern that can guide intervention strategies."
            
            elements.append(StoryElement(
                element_type='supporting_detail',
                content=content,
                confidence=strongest_chain.confidence,
                data_source='causal_analysis'
            ))
        
        return elements
    
    def _generate_risk_narrative(self, risk_factors: List[str], 
                               protective_factors: List[str]) -> StoryElement:
        """Generate risk and protection narrative."""
        content = ""
        
        if risk_factors:
            risk_names = [self._humanize_feature_name(f) for f in risk_factors[:3]]
            content += f"Key risk factors identified include {', '.join(risk_names)}, "
            content += "which contribute to environmental vulnerability and require mitigation strategies. "
        
        if protective_factors:
            protection_names = [self._humanize_feature_name(f) for f in protective_factors[:2]]
            content += f"Conversely, {', '.join(protection_names)} serve as protective factors, "
            content += "helping to buffer against environmental changes and should be strengthened. "
        
        if not content:
            content = "The analysis shows a balanced environmental system without extreme risk or protective factors."
        
        confidence = 0.7 if (risk_factors or protective_factors) else 0.5
        
        return StoryElement(
            element_type='supporting_detail',
            content=content,
            confidence=confidence,
            data_source='risk_analysis'
        )
    
    def _generate_conclusion(self, decomposition_report) -> StoryElement:
        """Generate conclusion story element."""
        insights = decomposition_report.summary_insights
        recommendations = insights.get('key_recommendations', [])
        
        content = "In conclusion, this environmental analysis reveals "
        
        # Overall assessment
        risk_level = insights.get('risk_level', 'moderate')
        complexity = insights.get('causal_complexity', 'moderate')
        
        content += f"{risk_level} risk levels with {complexity} causal complexity. "
        
        # Top recommendation
        if recommendations:
            content += f"The primary recommendation is: {recommendations[0]} "
        
        # Future outlook
        if insights.get('overall_change_direction') == 'increase':
            content += "Continued monitoring and proactive intervention measures are essential "
            content += "to address the identified environmental challenges."
        else:
            content += "The positive trends identified provide opportunities for reinforcing "
            content += "beneficial environmental patterns through targeted policies."
        
        return StoryElement(
            element_type='conclusion',
            content=content,
            confidence=0.8,
            data_source='summary_insights'
        )
    
    def _generate_title(self, decomposition_report, location: str) -> str:
        """Generate story title."""
        insights = decomposition_report.summary_insights
        change_direction = insights.get('overall_change_direction', 'change')
        risk_level = insights.get('risk_level', 'moderate')
        
        if change_direction == 'increase' and risk_level == 'high':
            return f"Environmental Risk Assessment: {location} Faces Significant Challenges"
        elif change_direction == 'decrease' and risk_level == 'low':
            return f"Environmental Progress: {location} Shows Positive Trends"
        elif risk_level == 'high':
            return f"Environmental Alert: {location} Requires Immediate Attention"
        else:
            return f"Environmental Analysis: Understanding Change Patterns in {location}"
    
    def _generate_summary(self, story_elements: List[StoryElement]) -> str:
        """Generate story summary."""
        # Extract key points from each element
        key_points = []
        
        for element in story_elements:
            if element.element_type in ['main_finding', 'conclusion']:
                # Extract first sentence as key point
                first_sentence = element.content.split('.')[0] + '.'
                key_points.append(first_sentence)
        
        if len(key_points) >= 2:
            return ' '.join(key_points[:2])
        elif key_points:
            return key_points[0]
        else:
            return "Environmental analysis reveals complex patterns requiring detailed investigation."
    
    def _extract_key_insights(self, shap_result, feature_analysis_report, 
                            decomposition_report) -> List[str]:
        """Extract key insights from analysis."""
        insights = []
        
        # Top feature insight
        if feature_analysis_report.critical_features:
            top_feature = self._humanize_feature_name(feature_analysis_report.critical_features[0])
            insights.append(f"Most critical factor: {top_feature}")
        
        # Change magnitude insight
        if 'final' in decomposition_report.score_decompositions:
            change = decomposition_report.score_decompositions['final'].total_change
            insights.append(f"Overall change magnitude: {abs(change):.2f}")
        
        # Risk level insight
        risk_level = decomposition_report.summary_insights.get('risk_level', 'unknown')
        insights.append(f"Risk assessment: {risk_level.capitalize()} risk level")
        
        # Causal complexity insight
        if decomposition_report.causal_chains:
            chain_count = len(decomposition_report.causal_chains)
            insights.append(f"Causal complexity: {chain_count} significant causal pathways identified")
        
        # Category dominance insight
        category_importance = decomposition_report.summary_insights.get('dominant_categories', {})
        if category_importance:
            top_category = max(category_importance.items(), key=lambda x: x[1])
            insights.append(f"Dominant category: {top_category[0].capitalize()} factors")
        
        return insights[:5]  # Return top 5 insights
    
    def _calculate_story_confidence(self, story_elements: List[StoryElement]) -> str:
        """Calculate overall story confidence level."""
        if not story_elements:
            return 'low'
        
        avg_confidence = np.mean([elem.confidence for elem in story_elements])
        
        if avg_confidence >= 0.8:
            return 'high'
        elif avg_confidence >= 0.6:
            return 'moderate'
        else:
            return 'low'
    
    def _get_confidence_distribution(self, story_elements: List[StoryElement]) -> Dict[str, int]:
        """Get distribution of confidence levels."""
        distribution = {'high': 0, 'moderate': 0, 'low': 0}
        
        for element in story_elements:
            if element.confidence >= 0.8:
                distribution['high'] += 1
            elif element.confidence >= 0.6:
                distribution['moderate'] += 1
            else:
                distribution['low'] += 1
        
        return distribution
    
    def _humanize_feature_name(self, feature_name: str) -> str:
        """Convert technical feature names to human-readable format."""
        # Handle common patterns
        humanized = feature_name.replace('_', ' ').title()
        
        # Specific replacements
        replacements = {
            'NO2': 'Nitrogen Dioxide',
            'Ma ': 'Moving Average ',
            'Lag ': 'Lagged ',
            'Trend ': 'Trend in ',
            'Rolling ': 'Rolling Average ',
        }
        
        for old, new in replacements.items():
            humanized = humanized.replace(old, new)
        
        return humanized
    
    def _get_feature_category_from_name(self, feature_name: str) -> str:
        """Determine feature category from name."""
        climate_keywords = ['pressure', 'humidity', 'temperature', 'precipitation', 'wind', 'NO2', 'solar']
        geographic_keywords = ['soil', 'flood', 'evapotranspiration', 'moisture']
        socioeconomic_keywords = ['life', 'population', 'railway', 'infrastructure', 'economic']
        
        feature_lower = feature_name.lower()
        
        if any(keyword in feature_lower for keyword in climate_keywords):
            return 'climate'
        elif any(keyword in feature_lower for keyword in geographic_keywords):
            return 'geographic'
        elif any(keyword in feature_lower for keyword in socioeconomic_keywords):
            return 'socioeconomic'
        else:
            return 'derived'
    
    def _get_category_context(self, category: str) -> str:
        """Get contextual information about feature categories."""
        contexts = {
            'climate': "As a climate-related factor, this plays a fundamental role in environmental system dynamics.",
            'geographic': "This geographic factor reflects the physical characteristics and constraints of the landscape.",
            'socioeconomic': "Being a socioeconomic indicator, this factor represents human activities and their environmental impacts.",
            'derived': "This derived feature captures complex patterns and temporal relationships in the data."
        }
        
        return contexts.get(category, "")
    
    def _find_common_important_features(self, shap_results: Dict[str, Any]) -> List[str]:
        """Find features that are important across all locations."""
        if len(shap_results) < 2:
            return []
        
        # Get top features for each location
        location_top_features = {}
        for location, result in shap_results.items():
            if hasattr(result, 'feature_importance'):
                top_features = sorted(
                    result.feature_importance.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:10]
                location_top_features[location] = [f[0] for f in top_features]
        
        # Find intersection
        if location_top_features:
            common_features = set(list(location_top_features.values())[0])
            for features in list(location_top_features.values())[1:]:
                common_features = common_features.intersection(set(features))
            
            return list(common_features)
        
        return []
    
    def _find_unique_high_impact_factors(self, location_result, all_results: Dict[str, Any], 
                                       location: str) -> List[str]:
        """Find factors that are uniquely important in a specific location."""
        if not hasattr(location_result, 'feature_importance'):
            return []
        
        # Get top features for this location
        location_top = set([
            f for f, imp in sorted(location_result.feature_importance.items(), 
                                 key=lambda x: x[1], reverse=True)[:5]
        ])
        
        # Get top features for other locations
        other_top_features = set()
        for other_location, result in all_results.items():
            if other_location != location and hasattr(result, 'feature_importance'):
                other_top = [
                    f for f, imp in sorted(result.feature_importance.items(), 
                                         key=lambda x: x[1], reverse=True)[:5]
                ]
                other_top_features.update(other_top)
        
        # Find unique features
        unique_features = location_top - other_top_features
        
        return list(unique_features)
    
    def _initialize_templates(self) -> Dict[str, StoryTemplate]:
        """Initialize story templates."""
        templates = {
            'risk_assessment': StoryTemplate(
                story_type='risk_assessment',
                template="The environmental risk assessment for {location} indicates {risk_level} risk conditions...",
                required_data=['risk_factors', 'risk_level'],
                confidence_threshold=0.7
            ),
            'causal_explanation': StoryTemplate(
                story_type='causal_explanation',
                template="Analysis reveals that {primary_driver} is the primary driver of environmental changes...",
                required_data=['primary_drivers', 'causal_chains'],
                confidence_threshold=0.6
            ),
            'trend_analysis': StoryTemplate(
                story_type='trend_analysis',
                template="Environmental trends show {direction} patterns with {magnitude} changes...",
                required_data=['score_decompositions', 'trend_direction'],
                confidence_threshold=0.8
            )
        }
        
        return templates
    
    def _initialize_narrative_patterns(self) -> Dict[str, List[str]]:
        """Initialize narrative patterns for story generation."""
        patterns = {
            'opening_phrases': [
                "Environmental analysis reveals",
                "The data indicates",
                "Our investigation shows",
                "Research findings demonstrate"
            ],
            'transition_phrases': [
                "Furthermore",
                "Additionally",
                "In contrast",
                "Building on this"
            ],
            'conclusion_phrases': [
                "In summary",
                "These findings suggest",
                "The analysis concludes",
                "Moving forward"
            ]
        }
        
        return patterns
    
    def _initialize_vocabulary(self) -> Dict[str, List[str]]:
        """Initialize environmental vocabulary for rich descriptions."""
        vocabulary = {
            'severity_levels': {
                'low': ['minimal', 'slight', 'modest', 'limited'],
                'moderate': ['noticeable', 'considerable', 'substantial', 'meaningful'],
                'high': ['significant', 'major', 'critical', 'severe']
            },
            'change_directions': {
                'positive': ['improvement', 'enhancement', 'progress', 'advancement'],
                'negative': ['deterioration', 'decline', 'degradation', 'worsening'],
                'neutral': ['stability', 'equilibrium', 'balance', 'consistency']
            },
            'environmental_terms': {
                'climate': ['atmospheric', 'meteorological', 'climatic', 'weather-related'],
                'geographic': ['topographical', 'landscape', 'terrain', 'geographical'],
                'ecological': ['environmental', 'ecological', 'ecosystem', 'natural']
            }
        }
        
        return vocabulary 