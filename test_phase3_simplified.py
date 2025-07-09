"""
Simplified Phase 3 SHAP Analysis Test

Tests core SHAP functionality with minimal dependencies.
"""

import sys
import os
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# Add paths
sys.path.append('.')
sys.path.append('ML_Models')

try:
    # Test basic SHAP import
    import shap
    print("✅ SHAP library imported successfully")
    
    # Test our SHAP modules
    from shap_framework.shap_analysis.shap_explainer import SHAPExplainer, SHAPConfig, SHAPResult
    from shap_framework.shap_analysis.feature_analyzer import FeatureAnalyzer
    from shap_framework.shap_analysis.causal_decomposer import CausalDecomposer
    from shap_framework.shap_analysis.story_generator import StoryGenerator
    
    print("✅ All SHAP analysis modules imported successfully")
    IMPORTS_OK = True
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    IMPORTS_OK = False

def create_mock_data():
    """Create mock environmental data for testing."""
    np.random.seed(42)
    
    # Create realistic environmental feature names
    feature_names = [
        'temperature_mean', 'humidity_avg', 'pressure_daily', 'precipitation_sum',
        'wind_speed_max', 'NO2_concentration', 'soil_temperature_0_7cm',
        'soil_moisture_7_28cm', 'urban_flood_risk_score', 'life_expectancy_years',
        'population_growth_rate', 'railway_density_km', 'lag_1_temperature',
        'ma_7_humidity', 'trend_precipitation'
    ]
    
    # Generate synthetic data
    n_samples = 100
    n_features = len(feature_names)
    
    # Create correlated features to simulate real environmental data
    data = np.random.randn(n_samples, n_features)
    
    # Add some correlations
    data[:, 1] = 0.7 * data[:, 0] + 0.3 * np.random.randn(n_samples)  # humidity correlated with temperature
    data[:, 6] = 0.8 * data[:, 0] + 0.2 * np.random.randn(n_samples)  # soil temp correlated with air temp
    
    X = pd.DataFrame(data, columns=feature_names)
    
    # Create mock target (environmental change score)
    y = (0.3 * data[:, 0] + 0.2 * data[:, 1] - 0.1 * data[:, 8] + 
         0.15 * data[:, 9] + 0.1 * np.random.randn(n_samples))
    
    return X, y

def test_shap_basic_functionality():
    """Test basic SHAP functionality with mock data."""
    print("\n🔍 Testing Basic SHAP Functionality...")
    
    try:
        # Create mock data
        X, y = create_mock_data()
        
        # Train a simple model
        from sklearn.ensemble import RandomForestRegressor
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        # Test SHAP explainer
        config = SHAPConfig(
            explainer_type="tree",
            background_samples=20,
            max_evals=50
        )
        
        explainer = SHAPExplainer(config)
        
        # Setup explainer
        explainer.setup_explainer(
            model=model,
            model_type="test",
            X_background=X.head(20),
            model_name="test_model"
        )
        
        # Generate explanations
        X_test = X.head(5)
        shap_result = explainer.explain_prediction(
            X_test, 
            model_name="test_model",
            return_interactions=False
        )
        
        # Validate results
        assert shap_result is not None
        assert hasattr(shap_result, 'shap_values')
        assert hasattr(shap_result, 'feature_importance')
        assert shap_result.shap_values.shape == (5, len(X.columns))
        
        print(f"   ✅ SHAP values generated: {shap_result.shap_values.shape}")
        print(f"   ✅ Feature importance calculated: {len(shap_result.feature_importance)} features")
        
        return True, shap_result
        
    except Exception as e:
        print(f"   ❌ Basic SHAP test failed: {str(e)}")
        return False, None

def test_feature_analyzer(shap_result):
    """Test Feature Analyzer with SHAP results."""
    print("\n📊 Testing Feature Analyzer...")
    
    try:
        analyzer = FeatureAnalyzer()
        
        # Test importance analysis
        importance_analysis = analyzer.analyze_feature_importance(shap_result)
        assert 'importance_statistics' in importance_analysis
        assert 'feature_rankings' in importance_analysis
        
        print(f"   ✅ Importance analysis completed")
        
        # Test interaction analysis
        interaction_analysis = analyzer.analyze_feature_interactions(shap_result, top_k=5)
        assert 'top_interactions' in interaction_analysis
        
        print(f"   ✅ Interaction analysis completed")
        
        # Generate report
        report = analyzer.generate_analysis_report(shap_result)
        assert hasattr(report, 'feature_importance')
        assert hasattr(report, 'recommendations')
        
        print(f"   ✅ Analysis report generated with {len(report.recommendations)} recommendations")
        
        return True, report
        
    except Exception as e:
        print(f"   ❌ Feature Analyzer test failed: {str(e)}")
        return False, None

def test_causal_decomposer(shap_result):
    """Test Causal Decomposer functionality."""
    print("\n🔗 Testing Causal Decomposer...")
    
    try:
        decomposer = CausalDecomposer()
        
        # Mock baseline and predicted data
        baseline_data = {'climate': 0.0, 'geographic': 0.0, 'final': 0.0}
        predicted_data = {'climate': 0.15, 'geographic': -0.05, 'final': 0.08}
        
        # Test score decomposition
        score_decompositions = decomposer.decompose_scores(
            shap_result, baseline_data, predicted_data
        )
        
        print(f"   ✅ Score decompositions: {list(score_decompositions.keys())}")
        
        # Test causal chains
        causal_chains = decomposer.identify_causal_chains(shap_result, min_chain_strength=0.05)
        print(f"   ✅ Causal chains identified: {len(causal_chains)}")
        
        # Generate report
        report = decomposer.generate_decomposition_report(
            shap_result, baseline_data, predicted_data
        )
        
        print(f"   ✅ Decomposition report generated")
        
        return True, report
        
    except Exception as e:
        print(f"   ❌ Causal Decomposer test failed: {str(e)}")
        return False, None

def test_story_generator(shap_result, feature_report, decomposition_report):
    """Test Story Generator functionality."""
    print("\n📖 Testing Story Generator...")
    
    try:
        story_generator = StoryGenerator()
        
        # Test comprehensive story
        story = story_generator.generate_comprehensive_story(
            shap_result=shap_result,
            feature_analysis_report=feature_report,
            decomposition_report=decomposition_report,
            location="Test Environmental Region"
        )
        
        assert hasattr(story, 'title')
        assert hasattr(story, 'story_elements')
        assert len(story.story_elements) > 0
        
        print(f"   ✅ Story generated: '{story.title}'")
        print(f"   ✅ Story elements: {len(story.story_elements)}")
        print(f"   ✅ Confidence level: {story.confidence_level}")
        
        # Test score explanation
        if 'final' in decomposition_report.score_decompositions:
            score_explanation = story_generator.generate_score_explanation(
                decomposition_report.score_decompositions['final'], 'final'
            )
            assert len(score_explanation) > 50
            print(f"   ✅ Score explanation generated")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Story Generator test failed: {str(e)}")
        return False

def main():
    """Run simplified Phase 3 tests."""
    print("🧪 Phase 3 SHAP Analysis - Simplified Test Suite")
    print("=" * 55)
    
    if not IMPORTS_OK:
        print("❌ Cannot proceed - module imports failed")
        return False
    
    test_results = []
    
    # Test 1: Basic SHAP functionality
    shap_success, shap_result = test_shap_basic_functionality()
    test_results.append(shap_success)
    
    if not shap_success:
        print("❌ Cannot proceed - basic SHAP test failed")
        return False
    
    # Test 2: Feature Analyzer
    feature_success, feature_report = test_feature_analyzer(shap_result)
    test_results.append(feature_success)
    
    # Test 3: Causal Decomposer
    causal_success, decomposition_report = test_causal_decomposer(shap_result)
    test_results.append(causal_success)
    
    # Test 4: Story Generator
    if feature_success and causal_success:
        story_success = test_story_generator(shap_result, feature_report, decomposition_report)
        test_results.append(story_success)
    else:
        print("\n📖 Skipping Story Generator test - dependencies failed")
        test_results.append(False)
    
    # Summary
    print("\n" + "="*55)
    print("📊 TEST SUMMARY")
    print("="*55)
    
    test_names = ["SHAP Explainer", "Feature Analyzer", "Causal Decomposer", "Story Generator"]
    
    passed = sum(test_results)
    total = len(test_results)
    
    for i, (name, result) in enumerate(zip(test_names, test_results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL PHASE 3 TESTS PASSED!")
        print("✅ SHAP Analysis System is functional!")
    elif passed >= total * 0.75:
        print("🟡 Most tests passed - minor issues to resolve")
    else:
        print("🔴 Significant issues detected")
    
    print("\n🚀 Phase 3 SHAP Analysis System Status: " + ("READY" if passed >= 3 else "NEEDS ATTENTION"))
    
    return passed >= 3

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 