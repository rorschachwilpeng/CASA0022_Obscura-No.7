"""
Story Generator for Environmental Change Index Framework

Converts SHAP analysis results into human-readable natural language explanations,
creating compelling narratives about environmental changes and their causes.
Uses Deepseek LLM API for intelligent story generation.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass
import logging
from datetime import datetime
import json
import requests
import time
import os

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

class DeepseekAPIClient:
    """Client for Deepseek LLM API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.max_retries = 3
        self.retry_delay = 1
    
    def generate_story(self, prompt: str, max_tokens: int = 800, 
                      temperature: float = 0.7) -> str:
        """
        Generate story using Deepseek LLM API.
        
        Args:
            prompt: The prompt for story generation
            max_tokens: Maximum tokens in response
            temperature: Creativity level (0.0-1.0)
            
        Returns:
            Generated story text
        """
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional environmental scientist and technical writer. You can transform complex environmental data analysis results into clear, engaging, and accurate English narratives. Your writing style should be professional yet accessible, combining scientific rigor with readability."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result['choices'][0]['message']['content'].strip()
                else:
                    logger.warning(f"API request failed with status {response.status_code}: {response.text}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (2 ** attempt))
                    else:
                        raise Exception(f"API request failed: {response.status_code}")
                        
            except Exception as e:
                logger.error(f"API call attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                else:
                    raise e
        
        raise Exception("All API call attempts failed")

class StoryGenerator:
    """
    Natural Language Story Generator for Environmental Analysis.
    
    Converts technical SHAP analysis results into engaging, understandable
    narratives about environmental changes and their causal factors using
    Deepseek LLM API.
    """
    
    def __init__(self, api_key: str = None):
        """Initialize Story Generator with LLM API."""
        # Try to get API key from parameter or environment variable
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        
        if self.api_key:
            try:
                self.llm_client = DeepseekAPIClient(self.api_key)
                self.use_llm = True
                logger.info("StoryGenerator initialized with Deepseek LLM API")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM client: {e}. Falling back to template mode.")
                self.use_llm = False
        else:
            logger.info("No Deepseek API key found, using template mode")
            self.use_llm = False
        
        # Fallback templates for when LLM is unavailable
        self.story_templates = self._initialize_templates()
        self.narrative_patterns = self._initialize_narrative_patterns()
        self.environmental_vocabulary = self._initialize_vocabulary()
        
        logger.info("StoryGenerator initialized")
    
    def generate_comprehensive_story(self, shap_result, feature_analysis_report,
                                   decomposition_report, location: str = "the analyzed region") -> EnvironmentalStory:
        """
        Generate comprehensive environmental change story using LLM.
        
        Args:
            shap_result: SHAPResult object
            feature_analysis_report: AnalysisReport from FeatureAnalyzer
            decomposition_report: DecompositionReport from CausalDecomposer
            location: Name of the location being analyzed
            
        Returns:
            Complete EnvironmentalStory object
        """
        logger.info(f"Generating comprehensive environmental story for {location}")
        
        if self.use_llm:
            return self._generate_story_with_llm(
                shap_result, feature_analysis_report, decomposition_report, location
            )
        else:
            return self._generate_story_with_template(
                shap_result, feature_analysis_report, decomposition_report, location
            )
    
    def _generate_story_with_llm(self, shap_result, feature_analysis_report,
                               decomposition_report, location: str) -> EnvironmentalStory:
        """Generate story using LLM API."""
        # Prepare data summary for LLM
        data_summary = self._prepare_data_summary(
            shap_result, feature_analysis_report, decomposition_report, location
        )
        
        # Generate different story elements using LLM
        story_elements = []
        
        # 1. Generate Introduction
        intro_prompt = self._create_introduction_prompt(data_summary, location)
        intro_content = self.llm_client.generate_story(intro_prompt, max_tokens=80)
        story_elements.append(StoryElement(
            element_type='introduction',
            content=intro_content,
            confidence=0.9,
            data_source='llm_generated'
        ))
        
        # 2. Generate Main Findings
        main_findings_prompt = self._create_main_findings_prompt(data_summary, location)
        main_findings_content = self.llm_client.generate_story(main_findings_prompt, max_tokens=120)
        story_elements.append(StoryElement(
            element_type='main_finding',
            content=main_findings_content,
            confidence=0.85,
            data_source='llm_generated'
        ))
        
        # 3. Generate Feature Analysis
        feature_prompt = self._create_feature_analysis_prompt(data_summary, location)
        feature_content = self.llm_client.generate_story(feature_prompt, max_tokens=80)
        story_elements.append(StoryElement(
            element_type='supporting_detail',
            content=feature_content,
            confidence=0.8,
            data_source='llm_generated'
        ))
        
        # 4. Generate Risk Analysis
        risk_prompt = self._create_risk_analysis_prompt(data_summary, location)
        risk_content = self.llm_client.generate_story(risk_prompt, max_tokens=80)
        story_elements.append(StoryElement(
            element_type='supporting_detail',
            content=risk_content,
            confidence=0.8,
            data_source='llm_generated'
        ))
        
        # 5. Generate Conclusion and Recommendations
        conclusion_prompt = self._create_conclusion_prompt(data_summary, location)
        conclusion_content = self.llm_client.generate_story(conclusion_prompt, max_tokens=80)
        story_elements.append(StoryElement(
            element_type='conclusion',
            content=conclusion_content,
            confidence=0.85,
            data_source='llm_generated'
        ))
        
        # Generate title and summary using LLM
        title_prompt = self._create_title_prompt(data_summary, location)
        title = self.llm_client.generate_story(title_prompt, max_tokens=30, temperature=0.5)
        
        summary_prompt = self._create_summary_prompt(story_elements, location)
        summary = self.llm_client.generate_story(summary_prompt, max_tokens=100, temperature=0.5)
        
        # Extract key insights using LLM
        insights_prompt = self._create_insights_prompt(data_summary, location)
        insights_text = self.llm_client.generate_story(insights_prompt, max_tokens=80, temperature=0.5)
        key_insights = [insight.strip() for insight in insights_text.split('\n') if insight.strip()][:3]
        
        # Calculate confidence and create metadata
        confidence_level = self._calculate_story_confidence(story_elements)
        metadata = self._create_metadata(shap_result, story_elements, location, 'llm_generated')
        
        return EnvironmentalStory(
            title=title.strip().strip('"').strip("'"),
            summary=summary,
            story_elements=story_elements,
            key_insights=key_insights,
            confidence_level=confidence_level,
            metadata=metadata
        )
    
    def _generate_story_with_template(self, shap_result, feature_analysis_report,
                                    decomposition_report, location: str) -> EnvironmentalStory:
        """Generate story using template mode (fallback)."""
        logger.info("Using template mode for story generation")
        
        # Generate story elements using original template methods
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
        if hasattr(decomposition_report, 'causal_chains'):
            causal_stories = self._generate_causal_chain_stories(decomposition_report.causal_chains)
            story_elements.extend(causal_stories)
        
        # 5. Risk and protection narrative
        risk_narrative = self._generate_risk_narrative(
            getattr(decomposition_report, 'risk_factors', []), 
            getattr(decomposition_report, 'protective_factors', [])
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
        metadata = self._create_metadata(shap_result, story_elements, location, 'template_generated')
        
        return EnvironmentalStory(
            title=title,
            summary=summary,
            story_elements=story_elements,
            key_insights=key_insights,
            confidence_level=confidence_level,
            metadata=metadata
        )
     
    def _create_metadata(self, shap_result, story_elements: List[StoryElement], 
                        location: str, generation_method: str) -> Dict[str, Any]:
        """Create metadata for the story."""
        return {
            'generation_timestamp': datetime.now().isoformat(),
            'generation_method': generation_method,
            'location': location,
            'analysis_scope': {
                'feature_count': len(shap_result.feature_names),
                'sample_count': len(shap_result.shap_values),
                'model_type': getattr(shap_result, 'model_metadata', {}).get('model_type', 'unknown')
            },
            'story_statistics': {
                'element_count': len(story_elements),
                'word_count': sum(len(elem.content.split()) for elem in story_elements),
                'confidence_distribution': self._get_confidence_distribution(story_elements)
            },
            'llm_info': {
                'api_used': 'deepseek' if generation_method == 'llm_generated' else 'none',
                'api_available': self.use_llm
            }
        }
     
    def _prepare_data_summary(self, shap_result, feature_analysis_report, 
                            decomposition_report, location: str) -> Dict[str, Any]:
        """Prepare structured data summary for LLM prompts."""
        summary = {
            'location': location,
            'feature_count': len(shap_result.feature_names),
            'sample_count': len(shap_result.shap_values),
            'top_features': [],
            'score_changes': {},
            'risk_factors': [],
            'protective_factors': [],
            'causal_chains': [],
            'primary_drivers': []
        }
        
        # Top important features
        if hasattr(feature_analysis_report, 'critical_features'):
            summary['top_features'] = feature_analysis_report.critical_features[:5]
        
        # Score decompositions
        if hasattr(decomposition_report, 'score_decompositions'):
            for score_type, decomp in decomposition_report.score_decompositions.items():
                summary['score_changes'][score_type] = {
                    'change': decomp.total_change,
                    'baseline': decomp.baseline_value,
                    'predicted': decomp.predicted_value
                }
        
        # Risk and protective factors
        if hasattr(decomposition_report, 'risk_factors'):
            summary['risk_factors'] = decomposition_report.risk_factors[:3]
        if hasattr(decomposition_report, 'protective_factors'):
            summary['protective_factors'] = decomposition_report.protective_factors[:3]
        
        # Primary drivers
        if hasattr(decomposition_report, 'primary_drivers'):
            summary['primary_drivers'] = [
                driver.factor_name for driver in decomposition_report.primary_drivers[:3]
            ]
        
        # Causal chains
        if hasattr(decomposition_report, 'causal_chains') and decomposition_report.causal_chains:
            summary['causal_chains'] = [
                {
                    'trigger': chain.trigger_factors[:2],
                    'outcomes': chain.outcome_factors[:2],
                    'confidence': chain.confidence
                }
                for chain in decomposition_report.causal_chains[:2]
            ]
        
        return summary
    
    def _create_introduction_prompt(self, data_summary: Dict[str, Any], location: str) -> str:
        """Create prompt for introduction section."""
        return f"""
Please generate a brief introduction for the following environmental analysis:

Analysis Location: {location}
Data Size: {data_summary['feature_count']} environmental indicators, {data_summary['sample_count']} data points
Analysis Method: SHAP analysis

Generate a concise opening (30-40 words):
- Professional and clear
- Mention SHAP analysis
- In English
"""
    
    def _create_main_findings_prompt(self, data_summary: Dict[str, Any], location: str) -> str:
        """Create prompt for main findings section."""
        score_info = ""
        if 'final' in data_summary['score_changes']:
            final_change = data_summary['score_changes']['final']['change']
            score_info = f"Overall environmental change index: {final_change:+.2f}"
        
        drivers_info = ""
        if data_summary['primary_drivers']:
            drivers_info = f"Primary drivers: {', '.join(data_summary['primary_drivers'][:3])}"
        
        return f"""
Please generate the main findings for {location}:

{score_info}
{drivers_info}
Key features: {', '.join(data_summary['top_features'][:3]) if data_summary['top_features'] else 'Analysis in progress'}

Generate concise main findings (40-60 words):
- Summarize overall environmental situation
- Mention key drivers
- Professional tone
- In English
"""
    
    def _create_feature_analysis_prompt(self, data_summary: Dict[str, Any], location: str) -> str:
        """Create prompt for feature analysis section."""
        features_list = ', '.join(data_summary['top_features'][:3]) if data_summary['top_features'] else 'Feature analysis in progress'
        
        return f"""
Please generate feature analysis for {location}:

Key features: {features_list}
Risk factors: {', '.join(data_summary['risk_factors'][:2]) if data_summary['risk_factors'] else 'Assessment in progress'}

Generate brief feature analysis (30-40 words):
- Explain key feature impacts
- Mention risk factors
- Concise and clear
- In English
"""
    
    def _create_risk_analysis_prompt(self, data_summary: Dict[str, Any], location: str) -> str:
        """Create prompt for risk analysis section."""
        risk_factors = ', '.join(data_summary['risk_factors'][:2]) if data_summary['risk_factors'] else 'No significant risks'
        protective_factors = ', '.join(data_summary['protective_factors'][:2]) if data_summary['protective_factors'] else 'No significant protection'
        
        return f"""
Please generate risk analysis for {location}:

Risk factors: {risk_factors}
Protective factors: {protective_factors}

Generate brief risk assessment (30-40 words):
- Assess risk level
- Mention protective factors
- Balanced analysis
- In English
"""
    
    def _create_conclusion_prompt(self, data_summary: Dict[str, Any], location: str) -> str:
        """Create prompt for conclusion section."""
        overall_trend = "change in progress"
        if 'final' in data_summary['score_changes']:
            change = data_summary['score_changes']['final']['change']
            if change > 0.2:
                overall_trend = "environmental pressure increasing"
            elif change < -0.2:
                overall_trend = "environmental conditions improving"
            else:
                overall_trend = "environmental conditions relatively stable"
        
        return f"""
Please generate conclusion for {location}:

Overall trend: {overall_trend}
Key findings: {', '.join(data_summary['top_features'][:2]) if data_summary['top_features'] else 'Multiple factors'}

Generate brief conclusion (30-40 words):
- Summarize key results
- Provide 1-2 recommendations
- Forward-looking
- In English
"""
    
    def _create_title_prompt(self, data_summary: Dict[str, Any], location: str) -> str:
        """Create prompt for title generation."""
        return f"""
Please generate an attractive title for the following environmental analysis report:

Location: {location}
Analysis Type: Environmental Change Index Analysis
Main Focus: {', '.join(data_summary['top_features'][:2]) if data_summary['top_features'] else 'Environmental Change'}

Requirements:
- Title length 10-20 words
- Highlight location and analysis topic
- Professional and readable
- Only return the title, no other content
- In English
"""
    
    def _create_summary_prompt(self, story_elements: List[StoryElement], location: str) -> str:
        """Create prompt for summary generation."""
        key_content = []
        for element in story_elements:
            if element.element_type in ['main_finding', 'conclusion']:
                # Get first sentence
                first_sentence = element.content.split('.')[0] + '.'
                key_content.append(first_sentence)
        
        content_text = ' '.join(key_content[:2])
        
        return f"""
Please generate a concise summary for {location}:

Key Content: {content_text}

Requirements:
- Summary length 40-50 words
- Summarize the most important findings
- Professional tone
- In English
"""
    
    def _create_insights_prompt(self, data_summary: Dict[str, Any], location: str) -> str:
        """Create prompt for key insights generation."""
        return f"""
Please extract 3 key insights for {location}:

Important Features: {', '.join(data_summary['top_features'][:3]) if data_summary['top_features'] else 'Analysis in progress'}
Primary Drivers: {', '.join(data_summary['primary_drivers'][:2]) if data_summary['primary_drivers'] else 'Identification in progress'}

Requirements:
- One insight per line
- 10-15 words per line
- Most important findings only
- Concise and clear
- In English
- Format: One insight per line, no numbering
"""
    
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