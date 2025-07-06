"""
Cross-City Validator for Environmental Data

Validates consistency and reasonableness across different cities.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CrossCityValidationResult:
    """Container for cross-city validation results."""
    passed: bool
    score: float
    issues: List[str]
    details: Dict[str, Any]
    
    # Add compatibility properties for main validator
    @property
    def errors(self) -> List[str]:
        """Extract error messages from issues."""
        return [issue for issue in self.issues if "error" in issue.lower()]
    
    @property
    def warnings(self) -> List[str]:
        """Extract warning messages from issues."""
        return [issue for issue in self.issues if "warning" in issue.lower() or issue not in self.errors]

class CrossCityValidator:
    """
    Cross-city validator for environmental data.
    
    Validates:
    - Structural consistency across cities
    - Reasonable value differences between cities
    - Correlation patterns
    - Feature completeness
    """
    
    def __init__(self):
        """Initialize CrossCityValidator."""
        self.expected_cities = ['London', 'Manchester', 'Edinburgh']
        logger.info("CrossCityValidator initialized")
    
    def validate_cross_city_consistency(self, city_dataframes: Dict[str, pd.DataFrame]) -> CrossCityValidationResult:
        """
        Validate consistency across cities.
        
        Args:
            city_dataframes: Dictionary of DataFrames by city
            
        Returns:
            CrossCityValidationResult object
        """
        logger.info("Validating cross-city consistency")
        
        result = CrossCityValidationResult(
            passed=True,
            score=1.0,
            issues=[],
            details={}
        )
        
        try:
            # 1. Structural consistency
            structural_result = self._validate_structural_consistency(city_dataframes)
            result.details['structural_consistency'] = structural_result
            if not structural_result['consistent']:
                result.issues.extend(structural_result['issues'])
                result.score -= 0.3
            
            # 2. Value range consistency
            range_result = self._validate_value_ranges(city_dataframes)
            result.details['value_ranges'] = range_result
            if not range_result['reasonable']:
                result.issues.extend(range_result['issues'])
                result.score -= 0.2
            
            # 3. Correlation consistency
            correlation_result = self._validate_correlations(city_dataframes)
            result.details['correlations'] = correlation_result
            if not correlation_result['consistent']:
                result.issues.extend(correlation_result['issues'])
                result.score -= 0.2
            
            # 4. Completeness consistency
            completeness_result = self._validate_completeness_consistency(city_dataframes)
            result.details['completeness'] = completeness_result
            if not completeness_result['consistent']:
                result.issues.extend(completeness_result['issues'])
                result.score -= 0.3
            
            result.passed = result.score >= 0.7
            logger.info(f"Cross-city validation completed. Score: {result.score:.3f}")
            
        except Exception as e:
            result.passed = False
            result.score = 0.0
            result.issues.append(f"Cross-city validation failed: {str(e)}")
            logger.error(f"Cross-city validation error: {str(e)}")
        
        return result
    
    def _validate_structural_consistency(self, city_dataframes: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Validate structural consistency across cities."""
        result = {
            'consistent': True,
            'issues': [],
            'shape_comparison': {},
            'column_comparison': {},
            'index_comparison': {}
        }
        
        if not city_dataframes:
            result['consistent'] = False
            result['issues'].append("No city data provided")
            return result
        
        # Compare shapes
        shapes = {city: df.shape for city, df in city_dataframes.items()}
        result['shape_comparison'] = shapes
        
        unique_shapes = set(shapes.values())
        if len(unique_shapes) > 1:
            result['consistent'] = False
            result['issues'].append(f"Inconsistent shapes across cities: {shapes}")
        
        # Compare columns
        column_sets = {city: set(df.columns) for city, df in city_dataframes.items()}
        result['column_comparison'] = {city: list(cols) for city, cols in column_sets.items()}
        
        if len(set(tuple(sorted(cols)) for cols in column_sets.values())) > 1:
            result['consistent'] = False
            result['issues'].append("Inconsistent columns across cities")
        
        # Compare index ranges
        index_ranges = {}
        for city, df in city_dataframes.items():
            if isinstance(df.index, pd.DatetimeIndex):
                index_ranges[city] = (df.index.min(), df.index.max())
            else:
                index_ranges[city] = (df.index.min(), df.index.max())
        
        result['index_comparison'] = index_ranges
        
        return result
    
    def _validate_value_ranges(self, city_dataframes: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Validate value ranges are reasonable across cities."""
        result = {
            'reasonable': True,
            'issues': [],
            'range_comparison': {},
            'extreme_differences': {}
        }
        
        if len(city_dataframes) < 2:
            return result
        
        # Get common columns
        common_columns = set.intersection(*[set(df.columns) for df in city_dataframes.values()])
        
        for col in common_columns:
            if all(df[col].dtype in ['float64', 'int64'] for df in city_dataframes.values()):
                # Calculate ranges for each city
                ranges = {}
                means = {}
                
                for city, df in city_dataframes.items():
                    ranges[city] = (df[col].min(), df[col].max())
                    means[city] = df[col].mean()
                
                result['range_comparison'][col] = {
                    'ranges': ranges,
                    'means': means
                }
                
                # Check for extreme differences
                mean_values = list(means.values())
                if len(mean_values) > 1:
                    max_mean = max(mean_values)
                    min_mean = min(mean_values)
                    
                    if max_mean != 0 and abs(max_mean - min_mean) / abs(max_mean) > 0.5:
                        result['extreme_differences'][col] = {
                            'max_mean': max_mean,
                            'min_mean': min_mean,
                            'relative_difference': abs(max_mean - min_mean) / abs(max_mean)
                        }
                        result['issues'].append(f"{col}: large mean difference across cities")
                        result['reasonable'] = False
        
        return result
    
    def _validate_correlations(self, city_dataframes: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Validate correlation patterns are similar across cities."""
        result = {
            'consistent': True,
            'issues': [],
            'correlation_comparison': {},
            'correlation_differences': {}
        }
        
        if len(city_dataframes) < 2:
            return result
        
        try:
            # Calculate correlation matrices for each city
            correlations = {}
            for city, df in city_dataframes.items():
                numeric_df = df.select_dtypes(include=[np.number])
                if len(numeric_df.columns) > 1:
                    correlations[city] = numeric_df.corr()
            
            result['correlation_comparison'] = {
                city: corr.to_dict() for city, corr in correlations.items()
            }
            
            # Compare correlations between cities
            if len(correlations) >= 2:
                cities = list(correlations.keys())
                for i in range(len(cities)):
                    for j in range(i + 1, len(cities)):
                        city1, city2 = cities[i], cities[j]
                        corr1, corr2 = correlations[city1], correlations[city2]
                        
                        # Find common columns
                        common_cols = list(set(corr1.columns) & set(corr2.columns))
                        
                        if len(common_cols) > 1:
                            # Calculate correlation difference
                            corr_diff = (corr1.loc[common_cols, common_cols] - 
                                       corr2.loc[common_cols, common_cols]).abs()
                            
                            max_diff = corr_diff.max().max()
                            mean_diff = corr_diff.mean().mean()
                            
                            comparison_key = f"{city1}_vs_{city2}"
                            result['correlation_differences'][comparison_key] = {
                                'max_difference': max_diff,
                                'mean_difference': mean_diff
                            }
                            
                            if max_diff > 0.5:
                                result['issues'].append(
                                    f"Large correlation difference between {city1} and {city2}: {max_diff:.3f}"
                                )
                                result['consistent'] = False
        
        except Exception as e:
            result['issues'].append(f"Correlation validation failed: {str(e)}")
            result['consistent'] = False
        
        return result
    
    def _validate_completeness_consistency(self, city_dataframes: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Validate data completeness is consistent across cities."""
        result = {
            'consistent': True,
            'issues': [],
            'completeness_comparison': {},
            'completeness_differences': {}
        }
        
        # Calculate completeness for each city
        for city, df in city_dataframes.items():
            total_cells = df.size
            missing_cells = df.isnull().sum().sum()
            completeness = 1 - (missing_cells / total_cells) if total_cells > 0 else 0
            
            result['completeness_comparison'][city] = {
                'overall_completeness': completeness,
                'missing_cells': missing_cells,
                'total_cells': total_cells,
                'column_completeness': (1 - df.isnull().sum() / len(df)).to_dict()
            }
        
        # Check for large differences in completeness
        completeness_values = [
            info['overall_completeness'] 
            for info in result['completeness_comparison'].values()
        ]
        
        if len(completeness_values) > 1:
            max_completeness = max(completeness_values)
            min_completeness = min(completeness_values)
            completeness_diff = max_completeness - min_completeness
            
            result['completeness_differences']['overall'] = {
                'max_completeness': max_completeness,
                'min_completeness': min_completeness,
                'difference': completeness_diff
            }
            
            if completeness_diff > 0.2:  # 20% difference
                result['issues'].append(
                    f"Large completeness difference across cities: {completeness_diff:.1%}"
                )
                result['consistent'] = False
        
        return result 