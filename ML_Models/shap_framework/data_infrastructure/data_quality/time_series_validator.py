"""
Time Series Validator for Environmental Data

Handles time series specific validation including temporal consistency, 
seasonality patterns, and trend analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TimeSeriesValidationResult:
    """Container for time series validation results."""
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

class TimeSeriesValidator:
    """
    Time series validator for environmental data.
    
    Validates:
    - Temporal consistency
    - Seasonal patterns
    - Trend reasonableness
    - Data frequency
    - Time gaps
    """
    
    def __init__(self):
        """Initialize TimeSeriesValidator."""
        self.expected_frequency = 'M'  # Monthly data expected
        logger.info("TimeSeriesValidator initialized")
    
    def validate_time_series(self, city_dataframes: Dict[str, pd.DataFrame]) -> TimeSeriesValidationResult:
        """
        Validate time series data for all cities.
        
        Args:
            city_dataframes: Dictionary of DataFrames by city
            
        Returns:
            TimeSeriesValidationResult object
        """
        logger.info("Validating time series data")
        
        result = TimeSeriesValidationResult(
            passed=True,
            score=1.0,
            issues=[],
            details={}
        )
        
        try:
            for city, df in city_dataframes.items():
                city_result = self._validate_city_time_series(df, city)
                result.details[city] = city_result
                
                if not city_result['passed']:
                    result.passed = False
                    result.issues.extend([f"{city}: {issue}" for issue in city_result['issues']])
                
                result.score = min(result.score, city_result['score'])
            
            logger.info(f"Time series validation completed. Score: {result.score:.3f}")
            
        except Exception as e:
            result.passed = False
            result.score = 0.0
            result.issues.append(f"Time series validation failed: {str(e)}")
            logger.error(f"Time series validation error: {str(e)}")
        
        return result
    
    def _validate_city_time_series(self, df: pd.DataFrame, city: str) -> Dict[str, Any]:
        """Validate time series for a single city."""
        city_result = {
            'passed': True,
            'score': 1.0,
            'issues': [],
            'temporal_consistency': {},
            'frequency_analysis': {},
            'seasonality_check': {},
            'trend_analysis': {},
            'gap_analysis': {}
        }
        
        if df.empty or not isinstance(df.index, pd.DatetimeIndex):
            city_result['passed'] = False
            city_result['score'] = 0.0
            city_result['issues'].append("Invalid or missing time index")
            return city_result
        
        # 1. Temporal consistency check
        temporal_result = self._check_temporal_consistency(df)
        city_result['temporal_consistency'] = temporal_result
        if not temporal_result['consistent']:
            city_result['issues'].extend(temporal_result['issues'])
            city_result['score'] -= 0.2
        
        # 2. Frequency analysis
        frequency_result = self._analyze_frequency(df)
        city_result['frequency_analysis'] = frequency_result
        if not frequency_result['correct_frequency']:
            city_result['issues'].extend(frequency_result['issues'])
            city_result['score'] -= 0.1
        
        # 3. Gap analysis
        gap_result = self._analyze_gaps(df)
        city_result['gap_analysis'] = gap_result
        if gap_result['significant_gaps'] > 0:
            city_result['issues'].append(f"Found {gap_result['significant_gaps']} significant time gaps")
            city_result['score'] -= 0.15
        
        # 4. Seasonality check
        seasonality_result = self._check_seasonality(df)
        city_result['seasonality_check'] = seasonality_result
        if not seasonality_result['reasonable_seasonality']:
            city_result['issues'].extend(seasonality_result['issues'])
            city_result['score'] -= 0.1
        
        # 5. Trend analysis
        trend_result = self._analyze_trends(df)
        city_result['trend_analysis'] = trend_result
        if not trend_result['reasonable_trends']:
            city_result['issues'].extend(trend_result['issues'])
            city_result['score'] -= 0.1
        
        # Update passed status
        city_result['passed'] = city_result['score'] >= 0.7
        
        return city_result
    
    def _check_temporal_consistency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check temporal consistency of the time series."""
        result = {
            'consistent': True,
            'issues': [],
            'time_range': (df.index.min(), df.index.max()),
            'total_duration': (df.index.max() - df.index.min()).days,
            'is_sorted': df.index.is_monotonic_increasing,
            'has_duplicates': df.index.has_duplicates
        }
        
        # Check if index is sorted
        if not result['is_sorted']:
            result['consistent'] = False
            result['issues'].append("Time index is not sorted")
        
        # Check for duplicate timestamps
        if result['has_duplicates']:
            result['consistent'] = False
            duplicate_count = df.index.duplicated().sum()
            result['issues'].append(f"Found {duplicate_count} duplicate timestamps")
        
        # Check reasonable time range (should span multiple years for environmental data)
        if result['total_duration'] < 365:  # Less than 1 year
            result['consistent'] = False
            result['issues'].append("Time series too short (less than 1 year)")
        
        return result
    
    def _analyze_frequency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze time series frequency."""
        result = {
            'correct_frequency': True,
            'issues': [],
            'inferred_frequency': None,
            'expected_frequency': self.expected_frequency,
            'frequency_consistency': 0.0
        }
        
        try:
            # Infer frequency
            inferred_freq = pd.infer_freq(df.index)
            result['inferred_frequency'] = inferred_freq
            
            # Check if it matches expected frequency
            if inferred_freq != self.expected_frequency:
                result['correct_frequency'] = False
                result['issues'].append(
                    f"Frequency mismatch: expected {self.expected_frequency}, got {inferred_freq}"
                )
            
            # Calculate frequency consistency
            if len(df) > 1:
                time_diffs = df.index[1:] - df.index[:-1]
                mode_diff = time_diffs.mode()[0] if len(time_diffs.mode()) > 0 else None
                
                if mode_diff:
                    consistent_intervals = (time_diffs == mode_diff).sum()
                    result['frequency_consistency'] = consistent_intervals / len(time_diffs)
                    
                    if result['frequency_consistency'] < 0.9:
                        result['correct_frequency'] = False
                        result['issues'].append(
                            f"Inconsistent time intervals: {result['frequency_consistency']:.1%} consistency"
                        )
        
        except Exception as e:
            result['correct_frequency'] = False
            result['issues'].append(f"Frequency analysis failed: {str(e)}")
        
        return result
    
    def _analyze_gaps(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze gaps in time series."""
        result = {
            'total_gaps': 0,
            'significant_gaps': 0,
            'max_gap_days': 0,
            'gap_locations': [],
            'gap_summary': {}
        }
        
        if len(df) < 2:
            return result
        
        # Calculate time differences
        time_diffs = df.index[1:] - df.index[:-1]
        
        # Expected interval (assume monthly for environmental data)
        expected_interval = timedelta(days=30)  # Approximately 1 month
        
        # Find gaps (intervals > 1.5 * expected)
        gap_threshold = expected_interval * 1.5
        gaps = time_diffs > gap_threshold
        
        result['total_gaps'] = gaps.sum()
        
        if result['total_gaps'] > 0:
            gap_durations = time_diffs[gaps]
            result['max_gap_days'] = gap_durations.max().days
            
            # Significant gaps (> 3 months)
            significant_gap_threshold = timedelta(days=90)
            significant_gaps = gap_durations > significant_gap_threshold
            result['significant_gaps'] = significant_gaps.sum()
            
            # Gap locations
            gap_indices = np.where(gaps)[0]
            result['gap_locations'] = [
                {
                    'start': df.index[i],
                    'end': df.index[i + 1],
                    'duration_days': time_diffs[i].days
                }
                for i in gap_indices[:5]  # Show first 5 gaps
            ]
            
            # Gap summary
            result['gap_summary'] = {
                'mean_gap_days': gap_durations.mean().days,
                'median_gap_days': gap_durations.median().days,
                'std_gap_days': gap_durations.std().days
            }
        
        return result
    
    def _check_seasonality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check for reasonable seasonal patterns."""
        result = {
            'reasonable_seasonality': True,
            'issues': [],
            'seasonal_patterns': {},
            'seasonal_strength': {}
        }
        
        try:
            # Focus on environmental variables that should show seasonality
            seasonal_vars = [col for col in df.columns if any(var in col.lower() for var in 
                           ['temperature', 'humidity', 'solar', 'precipitation'])]
            
            for var in seasonal_vars:
                if var in df.columns:
                    seasonal_analysis = self._analyze_variable_seasonality(df[var], var)
                    result['seasonal_patterns'][var] = seasonal_analysis
                    
                    # Check if seasonality is reasonable
                    if seasonal_analysis['seasonal_strength'] < 0.1:
                        result['issues'].append(f"{var}: weak seasonal pattern detected")
                        result['reasonable_seasonality'] = False
                    
                    if seasonal_analysis['seasonal_strength'] > 0.9:
                        result['issues'].append(f"{var}: unusually strong seasonal pattern")
        
        except Exception as e:
            result['reasonable_seasonality'] = False
            result['issues'].append(f"Seasonality check failed: {str(e)}")
        
        return result
    
    def _analyze_variable_seasonality(self, series: pd.Series, var_name: str) -> Dict[str, Any]:
        """Analyze seasonality for a single variable."""
        result = {
            'seasonal_strength': 0.0,
            'monthly_means': {},
            'seasonal_range': 0.0,
            'peak_month': None,
            'trough_month': None
        }
        
        try:
            # Calculate monthly means
            monthly_data = series.groupby(series.index.month).mean()
            result['monthly_means'] = monthly_data.to_dict()
            
            # Calculate seasonal strength (range / mean)
            if series.mean() != 0:
                result['seasonal_range'] = monthly_data.max() - monthly_data.min()
                result['seasonal_strength'] = result['seasonal_range'] / abs(series.mean())
            
            # Find peak and trough months
            result['peak_month'] = monthly_data.idxmax()
            result['trough_month'] = monthly_data.idxmin()
            
        except Exception as e:
            logger.warning(f"Seasonality analysis failed for {var_name}: {str(e)}")
        
        return result
    
    def _analyze_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trends in the data."""
        result = {
            'reasonable_trends': True,
            'issues': [],
            'trend_analysis': {},
            'extreme_trends': []
        }
        
        try:
            for col in df.select_dtypes(include=[np.number]).columns:
                trend_info = self._calculate_trend(df[col], col)
                result['trend_analysis'][col] = trend_info
                
                # Check for extreme trends
                if abs(trend_info['slope']) > trend_info['reasonable_slope_threshold']:
                    result['extreme_trends'].append(col)
                    result['issues'].append(f"{col}: extreme trend detected (slope: {trend_info['slope']:.4f})")
                    result['reasonable_trends'] = False
        
        except Exception as e:
            result['reasonable_trends'] = False
            result['issues'].append(f"Trend analysis failed: {str(e)}")
        
        return result
    
    def _calculate_trend(self, series: pd.Series, col_name: str) -> Dict[str, Any]:
        """Calculate trend for a single series."""
        result = {
            'slope': 0.0,
            'r_squared': 0.0,
            'p_value': 1.0,
            'reasonable_slope_threshold': 0.1,
            'trend_direction': 'stable'
        }
        
        try:
            # Remove NaN values
            clean_series = series.dropna()
            
            if len(clean_series) < 10:  # Need at least 10 points for trend analysis
                return result
            
            # Create time variable (days since start)
            time_var = (clean_series.index - clean_series.index[0]).days
            
            # Calculate linear trend
            coeffs = np.polyfit(time_var, clean_series.values, 1)
            slope = coeffs[0]
            
            # Calculate R-squared
            predicted = np.polyval(coeffs, time_var)
            ss_res = np.sum((clean_series.values - predicted) ** 2)
            ss_tot = np.sum((clean_series.values - np.mean(clean_series.values)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            
            result['slope'] = slope
            result['r_squared'] = r_squared
            
            # Determine trend direction
            if abs(slope) < 1e-6:
                result['trend_direction'] = 'stable'
            elif slope > 0:
                result['trend_direction'] = 'increasing'
            else:
                result['trend_direction'] = 'decreasing'
            
            # Set reasonable slope threshold based on variable type
            if 'temperature' in col_name.lower():
                result['reasonable_slope_threshold'] = 0.01  # 0.01°C per day = 3.65°C per year
            elif 'humidity' in col_name.lower():
                result['reasonable_slope_threshold'] = 0.05  # 5% per year
            elif 'precipitation' in col_name.lower():
                result['reasonable_slope_threshold'] = 0.1   # More variable
            else:
                result['reasonable_slope_threshold'] = 0.1   # Default
        
        except Exception as e:
            logger.warning(f"Trend calculation failed for {col_name}: {str(e)}")
        
        return result 