"""
Main Data Validator for SHAP Environmental Change Index Framework

Coordinates all validation processes and generates comprehensive quality reports.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import json
from pathlib import Path

from .quality_checker import QualityChecker
from .time_series_validator import TimeSeriesValidator
from .cross_city_validator import CrossCityValidator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ValidationConfig:
    """Configuration for data validation."""
    # Quality thresholds
    min_data_completeness: float = 0.8  # 80% minimum data completeness
    max_missing_percentage: float = 0.2  # 20% maximum missing values
    outlier_detection_threshold: float = 3.0  # Z-score threshold
    
    # Time series validation
    check_time_consistency: bool = True
    check_seasonal_patterns: bool = True
    min_time_coverage: float = 0.9  # 90% time coverage required
    
    # Cross-city validation
    check_cross_city_consistency: bool = True
    max_cross_city_deviation: float = 0.3  # 30% max deviation between cities
    
    # Feature validation
    check_feature_distributions: bool = True
    check_feature_correlations: bool = True
    min_feature_variance: float = 0.01  # Minimum variance threshold
    
    # Business logic validation
    check_environmental_ranges: bool = True
    check_physical_constraints: bool = True
    
    # Reporting
    generate_detailed_report: bool = True
    save_validation_results: bool = True
    validation_output_dir: str = "validation_reports"

@dataclass
class ValidationResult:
    """Container for validation results."""
    passed: bool
    score: float  # 0-1 quality score
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

class DataValidator:
    """
    Main data validator that coordinates all validation processes.
    
    Performs comprehensive data quality checks including:
    - Data completeness and consistency
    - Time series validation
    - Cross-city consistency
    - Feature quality assessment
    - Environmental constraints validation
    """
    
    def __init__(self, config: Optional[ValidationConfig] = None):
        """
        Initialize DataValidator with configuration.
        
        Args:
            config: ValidationConfig object
        """
        self.config = config or ValidationConfig()
        
        # Initialize sub-validators
        self.quality_checker = QualityChecker()
        self.time_validator = TimeSeriesValidator()
        self.cross_city_validator = CrossCityValidator()
        
        # Validation history
        self.validation_history = []
        
        # Environmental constraints (reasonable ranges for UK)
        self.environmental_constraints = {
            'meteorological_temperature': (-20, 45),      # °C
            'meteorological_humidity': (0, 100),          # %
            'meteorological_wind_speed': (0, 150),        # km/h
            'meteorological_precipitation': (0, 300),     # mm/month
            'meteorological_atmospheric_pressure': (950, 1050),  # hPa
            'meteorological_solar_radiation': (0, 350),   # W/m²
            'meteorological_NO2': (0, 150),               # μg/m³
            'geospatial_soil_temperature_0_7cm': (-10, 35),  # °C
            'geospatial_soil_moisture_7_28cm': (0, 100),     # %
            'geospatial_reference_evapotranspiration': (0, 250),  # mm/month
            'geospatial_urban_flood_risk': (0, 800),      # m³/s
            'socioeconomic_life_expectancy': (70, 100),   # years
            'socioeconomic_population_growth_rate': (-0.1, 0.1),  # %
            'socioeconomic_railway_infrastructure': (0, 1000)  # index
        }
        
        logger.info("DataValidator initialized")
    
    def validate_raw_data(self, city_dataframes: Dict[str, pd.DataFrame]) -> ValidationResult:
        """
        Validate raw data from DataLoader.
        
        Args:
            city_dataframes: Dictionary of raw DataFrames by city
            
        Returns:
            ValidationResult object
        """
        logger.info("Validating raw data")
        
        result = ValidationResult(passed=True, score=1.0)
        
        try:
            # 1. Basic data structure validation
            structure_result = self._validate_data_structure(city_dataframes)
            self._merge_validation_results(result, structure_result)
            
            # 2. Data completeness validation
            completeness_result = self._validate_data_completeness(city_dataframes)
            self._merge_validation_results(result, completeness_result)
            
            # 3. Environmental constraints validation
            if self.config.check_environmental_ranges:
                constraints_result = self._validate_environmental_constraints(city_dataframes)
                self._merge_validation_results(result, constraints_result)
            
            # 4. Time series validation
            if self.config.check_time_consistency:
                time_result = self.time_validator.validate_time_series(city_dataframes)
                self._merge_validation_results(result, time_result)
            
            # 5. Cross-city consistency validation
            if self.config.check_cross_city_consistency:
                cross_city_result = self.cross_city_validator.validate_cross_city_consistency(city_dataframes)
                self._merge_validation_results(result, cross_city_result)
            
            # Calculate overall score
            result.score = self._calculate_overall_score(result)
            result.passed = result.score >= 0.7  # 70% minimum passing score
            
            logger.info(f"Raw data validation completed. Score: {result.score:.3f}")
            
        except Exception as e:
            result.passed = False
            result.score = 0.0
            result.errors.append(f"Validation failed with error: {str(e)}")
            logger.error(f"Raw data validation failed: {str(e)}")
        
        return result
    
    def validate_preprocessed_data(self, city_dataframes: Dict[str, pd.DataFrame]) -> ValidationResult:
        """
        Validate preprocessed data from DataPreprocessor.
        
        Args:
            city_dataframes: Dictionary of preprocessed DataFrames by city
            
        Returns:
            ValidationResult object
        """
        logger.info("Validating preprocessed data")
        
        result = ValidationResult(passed=True, score=1.0)
        
        try:
            # 1. Preprocessing quality validation
            preprocessing_result = self._validate_preprocessing_quality(city_dataframes)
            self._merge_validation_results(result, preprocessing_result)
            
            # 2. Data distribution validation
            distribution_result = self._validate_data_distributions(city_dataframes)
            self._merge_validation_results(result, distribution_result)
            
            # 3. Missing values validation
            missing_result = self._validate_missing_values(city_dataframes)
            self._merge_validation_results(result, missing_result)
            
            # 4. Outlier detection validation
            outlier_result = self._validate_outlier_handling(city_dataframes)
            self._merge_validation_results(result, outlier_result)
            
            # Calculate overall score
            result.score = self._calculate_overall_score(result)
            result.passed = result.score >= 0.8  # 80% minimum for preprocessed data
            
            logger.info(f"Preprocessed data validation completed. Score: {result.score:.3f}")
            
        except Exception as e:
            result.passed = False
            result.score = 0.0
            result.errors.append(f"Preprocessing validation failed with error: {str(e)}")
            logger.error(f"Preprocessed data validation failed: {str(e)}")
        
        return result
    
    def validate_engineered_features(self, city_dataframes: Dict[str, pd.DataFrame]) -> ValidationResult:
        """
        Validate engineered features from FeatureEngineer.
        
        Args:
            city_dataframes: Dictionary of feature-engineered DataFrames by city
            
        Returns:
            ValidationResult object
        """
        logger.info("Validating engineered features")
        
        result = ValidationResult(passed=True, score=1.0)
        
        try:
            # 1. Feature engineering quality validation
            engineering_result = self._validate_feature_engineering(city_dataframes)
            self._merge_validation_results(result, engineering_result)
            
            # 2. Feature correlation validation
            if self.config.check_feature_correlations:
                correlation_result = self._validate_feature_correlations(city_dataframes)
                self._merge_validation_results(result, correlation_result)
            
            # 3. Feature variance validation
            variance_result = self._validate_feature_variance(city_dataframes)
            self._merge_validation_results(result, variance_result)
            
            # 4. Feature distribution validation
            if self.config.check_feature_distributions:
                feature_dist_result = self._validate_feature_distributions(city_dataframes)
                self._merge_validation_results(result, feature_dist_result)
            
            # Calculate overall score
            result.score = self._calculate_overall_score(result)
            result.passed = result.score >= 0.75  # 75% minimum for engineered features
            
            logger.info(f"Feature engineering validation completed. Score: {result.score:.3f}")
            
        except Exception as e:
            result.passed = False
            result.score = 0.0
            result.errors.append(f"Feature engineering validation failed with error: {str(e)}")
            logger.error(f"Feature engineering validation failed: {str(e)}")
        
        return result
    
    def _validate_data_structure(self, city_dataframes: Dict[str, pd.DataFrame]) -> ValidationResult:
        """Validate basic data structure."""
        result = ValidationResult(passed=True, score=1.0)
        
        if not city_dataframes:
            result.passed = False
            result.score = 0.0
            result.errors.append("No data provided for validation")
            return result
        
        # Check expected cities
        expected_cities = ['London', 'Manchester', 'Edinburgh']
        missing_cities = [city for city in expected_cities if city not in city_dataframes]
        if missing_cities:
            result.warnings.append(f"Missing data for cities: {missing_cities}")
            result.score -= 0.2
        
        # Check DataFrame structure
        for city, df in city_dataframes.items():
            if df.empty:
                result.errors.append(f"Empty DataFrame for city: {city}")
                result.score -= 0.3
            elif not isinstance(df.index, pd.DatetimeIndex):
                result.warnings.append(f"Non-datetime index for city: {city}")
                result.score -= 0.1
        
        result.details['data_structure'] = {
            'cities_found': list(city_dataframes.keys()),
            'expected_cities': expected_cities,
            'missing_cities': missing_cities
        }
        
        return result
    
    def _validate_data_completeness(self, city_dataframes: Dict[str, pd.DataFrame]) -> ValidationResult:
        """Validate data completeness."""
        result = ValidationResult(passed=True, score=1.0)
        
        completeness_scores = {}
        
        for city, df in city_dataframes.items():
            if df.empty:
                completeness_scores[city] = 0.0
                continue
            
            # Calculate completeness score
            total_cells = df.size
            non_null_cells = df.count().sum()
            completeness = non_null_cells / total_cells if total_cells > 0 else 0.0
            completeness_scores[city] = completeness
            
            # Check against threshold
            if completeness < self.config.min_data_completeness:
                result.warnings.append(
                    f"Data completeness for {city}: {completeness:.1%} "
                    f"(below threshold: {self.config.min_data_completeness:.1%})"
                )
                result.score -= 0.2
        
        overall_completeness = np.mean(list(completeness_scores.values()))
        result.details['data_completeness'] = {
            'overall_completeness': overall_completeness,
            'city_completeness': completeness_scores,
            'threshold': self.config.min_data_completeness
        }
        
        return result
    
    def _validate_environmental_constraints(self, city_dataframes: Dict[str, pd.DataFrame]) -> ValidationResult:
        """Validate environmental data constraints."""
        result = ValidationResult(passed=True, score=1.0)
        
        violations = {}
        
        for city, df in city_dataframes.items():
            city_violations = {}
            
            for column in df.columns:
                if column in self.environmental_constraints:
                    min_val, max_val = self.environmental_constraints[column]
                    
                    # Check for violations
                    below_min = (df[column] < min_val).sum()
                    above_max = (df[column] > max_val).sum()
                    
                    if below_min > 0 or above_max > 0:
                        city_violations[column] = {
                            'below_min': int(below_min),
                            'above_max': int(above_max),
                            'constraint_range': (min_val, max_val),
                            'actual_range': (df[column].min(), df[column].max())
                        }
            
            if city_violations:
                violations[city] = city_violations
                result.warnings.append(f"Environmental constraint violations in {city}: {len(city_violations)} features")
                result.score -= 0.1
        
        result.details['environmental_constraints'] = violations
        
        return result
    
    def _validate_preprocessing_quality(self, city_dataframes: Dict[str, pd.DataFrame]) -> ValidationResult:
        """Validate preprocessing quality (standardization, etc.)."""
        result = ValidationResult(passed=True, score=1.0)
        
        standardization_quality = {}
        
        for city, df in city_dataframes.items():
            # Check if data is standardized (mean ≈ 0, std ≈ 1)
            means = df.mean()
            stds = df.std()
            
            mean_check = (np.abs(means) < 0.1).all()
            std_check = (np.abs(stds - 1.0) < 0.1).all()
            
            standardization_quality[city] = {
                'mean_check_passed': mean_check,
                'std_check_passed': std_check,
                'mean_values': means.to_dict(),
                'std_values': stds.to_dict()
            }
            
            if not mean_check:
                result.warnings.append(f"Standardization issue in {city}: means not close to 0")
                result.score -= 0.1
            
            if not std_check:
                result.warnings.append(f"Standardization issue in {city}: standard deviations not close to 1")
                result.score -= 0.1
        
        result.details['preprocessing_quality'] = standardization_quality
        
        return result
    
    def _validate_missing_values(self, city_dataframes: Dict[str, pd.DataFrame]) -> ValidationResult:
        """Validate missing value handling."""
        result = ValidationResult(passed=True, score=1.0)
        
        missing_analysis = {}
        
        for city, df in city_dataframes.items():
            missing_counts = df.isnull().sum()
            missing_percentage = missing_counts / len(df)
            
            # Check for excessive missing values
            excessive_missing = missing_percentage > self.config.max_missing_percentage
            
            missing_analysis[city] = {
                'missing_counts': missing_counts.to_dict(),
                'missing_percentages': missing_percentage.to_dict(),
                'excessive_missing_features': missing_counts[excessive_missing].index.tolist()
            }
            
            if excessive_missing.any():
                result.warnings.append(
                    f"Excessive missing values in {city}: {excessive_missing.sum()} features"
                )
                result.score -= 0.2
        
        result.details['missing_values'] = missing_analysis
        
        return result
    
    def _validate_data_distributions(self, city_dataframes: Dict[str, pd.DataFrame]) -> ValidationResult:
        """Validate data distributions."""
        result = ValidationResult(passed=True, score=1.0)
        
        distribution_analysis = {}
        
        for city, df in city_dataframes.items():
            # Calculate distribution statistics
            stats = {
                'skewness': df.skew().to_dict(),
                'kurtosis': df.kurtosis().to_dict(),
                'min_values': df.min().to_dict(),
                'max_values': df.max().to_dict()
            }
            
            # Check for extreme skewness (> 2 or < -2)
            extreme_skew = np.abs(df.skew()) > 2
            if extreme_skew.any():
                result.warnings.append(
                    f"Extreme skewness in {city}: {extreme_skew.sum()} features"
                )
                result.score -= 0.05
            
            distribution_analysis[city] = stats
        
        result.details['data_distributions'] = distribution_analysis
        
        return result
    
    def _validate_outlier_handling(self, city_dataframes: Dict[str, pd.DataFrame]) -> ValidationResult:
        """Validate outlier handling."""
        result = ValidationResult(passed=True, score=1.0)
        
        outlier_analysis = {}
        
        for city, df in city_dataframes.items():
            # Detect remaining outliers using Z-score
            z_scores = np.abs((df - df.mean()) / df.std())
            outliers = z_scores > self.config.outlier_detection_threshold
            
            outlier_counts = outliers.sum()
            outlier_percentages = outlier_counts / len(df)
            
            # Check for excessive outliers
            excessive_outliers = outlier_percentages > 0.05  # 5% threshold
            
            outlier_analysis[city] = {
                'outlier_counts': outlier_counts.to_dict(),
                'outlier_percentages': outlier_percentages.to_dict(),
                'excessive_outlier_features': outlier_counts[excessive_outliers].index.tolist()
            }
            
            if excessive_outliers.any():
                result.warnings.append(
                    f"Excessive outliers remaining in {city}: {excessive_outliers.sum()} features"
                )
                result.score -= 0.1
        
        result.details['outlier_handling'] = outlier_analysis
        
        return result
    
    def _validate_feature_engineering(self, city_dataframes: Dict[str, pd.DataFrame]) -> ValidationResult:
        """Validate feature engineering quality."""
        result = ValidationResult(passed=True, score=1.0)
        
        engineering_analysis = {}
        
        for city, df in city_dataframes.items():
            # Analyze feature types
            feature_types = {}
            for col in df.columns:
                if 'lag_' in col:
                    feature_types.setdefault('lag_features', []).append(col)
                elif '_ma_' in col:
                    feature_types.setdefault('moving_average_features', []).append(col)
                elif '_trend_' in col:
                    feature_types.setdefault('trend_features', []).append(col)
                elif '_seasonal_' in col:
                    feature_types.setdefault('seasonal_features', []).append(col)
                elif '_interaction' in col:
                    feature_types.setdefault('interaction_features', []).append(col)
                elif col in ['year', 'month', 'quarter', 'month_sin', 'month_cos']:
                    feature_types.setdefault('time_features', []).append(col)
                else:
                    feature_types.setdefault('original_features', []).append(col)
            
            engineering_analysis[city] = {
                'total_features': len(df.columns),
                'feature_types': {k: len(v) for k, v in feature_types.items()},
                'feature_type_details': feature_types
            }
            
            # Check for reasonable feature count
            if len(df.columns) < 10:
                result.warnings.append(f"Low feature count in {city}: {len(df.columns)} features")
                result.score -= 0.1
            elif len(df.columns) > 200:
                result.warnings.append(f"High feature count in {city}: {len(df.columns)} features")
                result.score -= 0.05
        
        result.details['feature_engineering'] = engineering_analysis
        
        return result
    
    def _validate_feature_correlations(self, city_dataframes: Dict[str, pd.DataFrame]) -> ValidationResult:
        """Validate feature correlations."""
        result = ValidationResult(passed=True, score=1.0)
        
        correlation_analysis = {}
        
        for city, df in city_dataframes.items():
            # Calculate correlation matrix
            corr_matrix = df.corr()
            
            # Find highly correlated features (> 0.95)
            high_corr_pairs = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    if abs(corr_matrix.iloc[i, j]) > 0.95:
                        high_corr_pairs.append((
                            corr_matrix.columns[i], 
                            corr_matrix.columns[j], 
                            corr_matrix.iloc[i, j]
                        ))
            
            correlation_analysis[city] = {
                'high_correlation_pairs': high_corr_pairs,
                'max_correlation': corr_matrix.abs().max().max(),
                'mean_correlation': corr_matrix.abs().mean().mean()
            }
            
            if len(high_corr_pairs) > 5:
                result.warnings.append(
                    f"Many highly correlated features in {city}: {len(high_corr_pairs)} pairs"
                )
                result.score -= 0.05
        
        result.details['feature_correlations'] = correlation_analysis
        
        return result
    
    def _validate_feature_variance(self, city_dataframes: Dict[str, pd.DataFrame]) -> ValidationResult:
        """Validate feature variance."""
        result = ValidationResult(passed=True, score=1.0)
        
        variance_analysis = {}
        
        for city, df in city_dataframes.items():
            # Calculate feature variances
            variances = df.var()
            
            # Find low variance features
            low_variance_features = variances[variances < self.config.min_feature_variance]
            
            variance_analysis[city] = {
                'low_variance_features': low_variance_features.to_dict(),
                'min_variance': variances.min(),
                'max_variance': variances.max(),
                'mean_variance': variances.mean()
            }
            
            if len(low_variance_features) > 0:
                result.warnings.append(
                    f"Low variance features in {city}: {len(low_variance_features)} features"
                )
                result.score -= 0.05
        
        result.details['feature_variance'] = variance_analysis
        
        return result
    
    def _validate_feature_distributions(self, city_dataframes: Dict[str, pd.DataFrame]) -> ValidationResult:
        """Validate feature distributions."""
        result = ValidationResult(passed=True, score=1.0)
        
        distribution_analysis = {}
        
        for city, df in city_dataframes.items():
            # Check for features with extreme distributions
            extreme_features = []
            
            for col in df.columns:
                # Check for constant features
                if df[col].nunique() <= 1:
                    extreme_features.append(f"{col}: constant")
                
                # Check for highly skewed features
                skewness = df[col].skew()
                if abs(skewness) > 5:
                    extreme_features.append(f"{col}: highly skewed ({skewness:.2f})")
            
            distribution_analysis[city] = {
                'extreme_features': extreme_features,
                'total_features': len(df.columns)
            }
            
            if len(extreme_features) > 0:
                result.warnings.append(
                    f"Extreme feature distributions in {city}: {len(extreme_features)} features"
                )
                result.score -= 0.05
        
        result.details['feature_distributions'] = distribution_analysis
        
        return result
    
    def _merge_validation_results(self, main_result: ValidationResult, sub_result: ValidationResult):
        """Merge validation results."""
        main_result.errors.extend(sub_result.errors)
        main_result.warnings.extend(sub_result.warnings)
        main_result.details.update(sub_result.details)
        
        # Update passed status
        if not sub_result.passed:
            main_result.passed = False
        
        # Update score (weighted average)
        main_result.score = (main_result.score + sub_result.score) / 2
    
    def _calculate_overall_score(self, result: ValidationResult) -> float:
        """Calculate overall validation score."""
        # Base score
        score = 1.0
        
        # Deduct for errors and warnings
        score -= len(result.errors) * 0.2
        score -= len(result.warnings) * 0.05
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))
    
    def generate_validation_report(self, result: ValidationResult, 
                                 validation_type: str = "general") -> Dict[str, Any]:
        """
        Generate comprehensive validation report.
        
        Args:
            result: ValidationResult object
            validation_type: Type of validation performed
            
        Returns:
            Dictionary with validation report
        """
        report = {
            'validation_type': validation_type,
            'timestamp': result.timestamp.isoformat(),
            'overall_result': {
                'passed': result.passed,
                'score': result.score,
                'grade': self._get_grade(result.score)
            },
            'summary': {
                'total_errors': len(result.errors),
                'total_warnings': len(result.warnings),
                'error_messages': result.errors,
                'warning_messages': result.warnings
            },
            'detailed_results': result.details
        }
        
        return report
    
    def _get_grade(self, score: float) -> str:
        """Convert score to grade."""
        if score >= 0.9:
            return 'A'
        elif score >= 0.8:
            return 'B'
        elif score >= 0.7:
            return 'C'
        elif score >= 0.6:
            return 'D'
        else:
            return 'F'
    
    def save_validation_report(self, report: Dict[str, Any], 
                             filename: Optional[str] = None) -> str:
        """
        Save validation report to file.
        
        Args:
            report: Validation report dictionary
            filename: Optional filename
            
        Returns:
            Path to saved report file
        """
        if not self.config.save_validation_results:
            return ""
        
        # Create output directory
        output_dir = Path(self.config.validation_output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"validation_report_{report['validation_type']}_{timestamp}.json"
        
        # Save report
        report_path = output_dir / filename
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Validation report saved to: {report_path}")
        return str(report_path)
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get summary of all validation results.
        
        Returns:
            Dictionary with validation summary
        """
        if not self.validation_history:
            return {"message": "No validation history available"}
        
        # Calculate summary statistics
        scores = [v.score for v in self.validation_history]
        
        summary = {
            'total_validations': len(self.validation_history),
            'average_score': np.mean(scores),
            'latest_score': scores[-1] if scores else 0,
            'trend': 'improving' if len(scores) > 1 and scores[-1] > scores[-2] else 'stable',
            'score_history': scores[-10:],  # Last 10 scores
            'latest_validation': self.validation_history[-1].timestamp.isoformat()
        }
        
        return summary 