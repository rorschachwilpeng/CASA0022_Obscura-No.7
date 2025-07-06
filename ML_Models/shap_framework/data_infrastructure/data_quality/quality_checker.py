"""
Quality Checker for Basic Data Quality Validation

Handles fundamental data quality checks like completeness, consistency, and format validation.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QualityChecker:
    """
    Basic data quality checker for environmental data.
    
    Performs fundamental quality checks including:
    - Data type validation
    - Range checks
    - Completeness assessment
    - Format validation
    """
    
    def __init__(self):
        """Initialize QualityChecker."""
        logger.info("QualityChecker initialized")
    
    def check_data_types(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Check data types and identify type issues.
        
        Args:
            df: DataFrame to check
            
        Returns:
            Dictionary with data type analysis
        """
        type_analysis = {
            'data_types': df.dtypes.to_dict(),
            'numeric_columns': df.select_dtypes(include=[np.number]).columns.tolist(),
            'categorical_columns': df.select_dtypes(include=['object', 'category']).columns.tolist(),
            'datetime_columns': df.select_dtypes(include=['datetime64']).columns.tolist(),
            'issues': []
        }
        
        # Check for mixed types
        for col in df.columns:
            if df[col].dtype == 'object':
                # Try to identify if it should be numeric
                try:
                    pd.to_numeric(df[col], errors='raise')
                    type_analysis['issues'].append(f"{col}: appears numeric but stored as object")
                except:
                    pass
        
        return type_analysis
    
    def check_value_ranges(self, df: pd.DataFrame, 
                          expected_ranges: Optional[Dict[str, Tuple[float, float]]] = None) -> Dict[str, Any]:
        """
        Check if values are within expected ranges.
        
        Args:
            df: DataFrame to check
            expected_ranges: Dictionary of column -> (min, max) expected ranges
            
        Returns:
            Dictionary with range analysis
        """
        range_analysis = {
            'column_ranges': {},
            'violations': {},
            'statistics': {}
        }
        
        for col in df.select_dtypes(include=[np.number]).columns:
            col_min = df[col].min()
            col_max = df[col].max()
            
            range_analysis['column_ranges'][col] = (col_min, col_max)
            range_analysis['statistics'][col] = {
                'min': col_min,
                'max': col_max,
                'mean': df[col].mean(),
                'std': df[col].std(),
                'median': df[col].median()
            }
            
            # Check against expected ranges if provided
            if expected_ranges and col in expected_ranges:
                expected_min, expected_max = expected_ranges[col]
                violations = []
                
                if col_min < expected_min:
                    violations.append(f"Minimum value {col_min} below expected {expected_min}")
                
                if col_max > expected_max:
                    violations.append(f"Maximum value {col_max} above expected {expected_max}")
                
                if violations:
                    range_analysis['violations'][col] = violations
        
        return range_analysis
    
    def check_completeness(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Check data completeness.
        
        Args:
            df: DataFrame to check
            
        Returns:
            Dictionary with completeness analysis
        """
        total_cells = df.size
        
        completeness_analysis = {
            'total_cells': total_cells,
            'total_missing': df.isnull().sum().sum(),
            'overall_completeness': 1 - (df.isnull().sum().sum() / total_cells),
            'column_completeness': {},
            'column_missing_counts': {},
            'missing_patterns': {}
        }
        
        # Per-column completeness
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            completeness = 1 - (missing_count / len(df))
            
            completeness_analysis['column_completeness'][col] = completeness
            completeness_analysis['column_missing_counts'][col] = missing_count
        
        # Missing data patterns
        missing_patterns = df.isnull().sum()
        completeness_analysis['missing_patterns'] = missing_patterns.to_dict()
        
        return completeness_analysis
    
    def check_duplicates(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Check for duplicate records.
        
        Args:
            df: DataFrame to check
            
        Returns:
            Dictionary with duplicate analysis
        """
        duplicate_analysis = {
            'total_duplicates': df.duplicated().sum(),
            'duplicate_percentage': df.duplicated().sum() / len(df),
            'duplicate_indices': df[df.duplicated()].index.tolist()
        }
        
        # Check for duplicates based on index (timestamps)
        if isinstance(df.index, pd.DatetimeIndex):
            index_duplicates = df.index.duplicated().sum()
            duplicate_analysis['index_duplicates'] = index_duplicates
            duplicate_analysis['duplicate_timestamps'] = df.index[df.index.duplicated()].tolist()
        
        return duplicate_analysis
    
    def check_consistency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Check internal data consistency.
        
        Args:
            df: DataFrame to check
            
        Returns:
            Dictionary with consistency analysis
        """
        consistency_analysis = {
            'consistency_issues': [],
            'logical_constraints': {},
            'value_consistency': {}
        }
        
        # Check for logical constraints
        # Example: soil temperature should be related to air temperature
        if 'meteorological_temperature' in df.columns and 'geospatial_soil_temperature_0_7cm' in df.columns:
            temp_diff = df['meteorological_temperature'] - df['geospatial_soil_temperature_0_7cm']
            extreme_diff = (abs(temp_diff) > 20).sum()  # More than 20°C difference
            
            if extreme_diff > 0:
                consistency_analysis['consistency_issues'].append(
                    f"Large temperature differences between air and soil: {extreme_diff} cases"
                )
            
            consistency_analysis['logical_constraints']['temperature_consistency'] = {
                'extreme_differences': extreme_diff,
                'mean_difference': temp_diff.mean(),
                'std_difference': temp_diff.std()
            }
        
        # Check for value consistency within features
        for col in df.select_dtypes(include=[np.number]).columns:
            # Check for sudden jumps (change > 5 standard deviations)
            if len(df) > 1:
                changes = df[col].diff().abs()
                threshold = changes.std() * 5
                sudden_jumps = (changes > threshold).sum()
                
                if sudden_jumps > 0:
                    consistency_analysis['value_consistency'][col] = {
                        'sudden_jumps': sudden_jumps,
                        'max_change': changes.max(),
                        'mean_change': changes.mean()
                    }
        
        return consistency_analysis
    
    def check_format_consistency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Check format consistency.
        
        Args:
            df: DataFrame to check
            
        Returns:
            Dictionary with format analysis
        """
        format_analysis = {
            'index_format': {},
            'column_formats': {},
            'encoding_issues': []
        }
        
        # Check index format
        if isinstance(df.index, pd.DatetimeIndex):
            format_analysis['index_format'] = {
                'type': 'DatetimeIndex',
                'frequency': df.index.freq,
                'timezone': df.index.tz,
                'has_duplicates': df.index.has_duplicates,
                'is_monotonic': df.index.is_monotonic_increasing
            }
        else:
            format_analysis['index_format'] = {
                'type': str(type(df.index)),
                'has_duplicates': df.index.has_duplicates
            }
        
        # Check column formats
        for col in df.columns:
            col_info = {
                'dtype': str(df[col].dtype),
                'unique_values': df[col].nunique(),
                'sample_values': df[col].dropna().head(3).tolist()
            }
            
            # Check for encoding issues in string columns
            if df[col].dtype == 'object':
                try:
                    # Try to detect non-ASCII characters
                    sample_str = str(df[col].dropna().iloc[0]) if len(df[col].dropna()) > 0 else ""
                    if not sample_str.isascii():
                        format_analysis['encoding_issues'].append(f"{col}: contains non-ASCII characters")
                except:
                    pass
            
            format_analysis['column_formats'][col] = col_info
        
        return format_analysis
    
    def run_comprehensive_quality_check(self, df: pd.DataFrame, 
                                       expected_ranges: Optional[Dict[str, Tuple[float, float]]] = None) -> Dict[str, Any]:
        """
        Run comprehensive quality check.
        
        Args:
            df: DataFrame to check
            expected_ranges: Expected value ranges
            
        Returns:
            Comprehensive quality report
        """
        logger.info("Running comprehensive quality check")
        
        quality_report = {
            'data_overview': {
                'shape': df.shape,
                'memory_usage': df.memory_usage(deep=True).sum(),
                'column_count': len(df.columns),
                'row_count': len(df)
            }
        }
        
        try:
            # Run all checks
            quality_report['data_types'] = self.check_data_types(df)
            quality_report['value_ranges'] = self.check_value_ranges(df, expected_ranges)
            quality_report['completeness'] = self.check_completeness(df)
            quality_report['duplicates'] = self.check_duplicates(df)
            quality_report['consistency'] = self.check_consistency(df)
            quality_report['format_consistency'] = self.check_format_consistency(df)
            
            # Calculate overall quality score
            quality_score = self._calculate_quality_score(quality_report)
            quality_report['overall_quality_score'] = quality_score
            
            logger.info(f"Quality check completed. Overall score: {quality_score:.3f}")
            
        except Exception as e:
            logger.error(f"Quality check failed: {str(e)}")
            quality_report['error'] = str(e)
            quality_report['overall_quality_score'] = 0.0
        
        return quality_report
    
    def _calculate_quality_score(self, quality_report: Dict[str, Any]) -> float:
        """Calculate overall quality score (0-1)."""
        score = 1.0
        
        # Completeness factor (weight: 0.3)
        if 'completeness' in quality_report:
            completeness = quality_report['completeness']['overall_completeness']
            score *= (0.7 + 0.3 * completeness)
        
        # Consistency factor (weight: 0.2)
        if 'consistency' in quality_report:
            consistency_issues = len(quality_report['consistency']['consistency_issues'])
            score *= max(0.5, 1.0 - consistency_issues * 0.1)
        
        # Duplicate factor (weight: 0.2)
        if 'duplicates' in quality_report:
            duplicate_pct = quality_report['duplicates']['duplicate_percentage']
            score *= max(0.5, 1.0 - duplicate_pct)
        
        # Range violations factor (weight: 0.3)
        if 'value_ranges' in quality_report:
            violations = len(quality_report['value_ranges']['violations'])
            score *= max(0.5, 1.0 - violations * 0.05)
        
        return max(0.0, min(1.0, score)) 