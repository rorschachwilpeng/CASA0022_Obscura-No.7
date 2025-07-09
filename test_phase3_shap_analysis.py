"""
Phase 3 SHAP Analysis System Test Suite

Tests the SHAP interpretation and explanation system for the Environmental Change Index Framework.

Tests:
1. SHAP Explainer functionality
2. Feature Analyzer capabilities
3. Causal Decomposer analysis
4. Story Generator narratives
5. End-to-end workflow
"""

import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime
import logging
import warnings
warnings.filterwarnings('ignore')

# Add the shap_analysis module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from shap_framework.core_models.climate_model import ClimateModel
    from shap_framework.core_models.geographic_model import GeographicModel
    from shap_framework.core_models.score_calculator import ScoreCalculator
    from shap_framework.data_infrastructure.data_pipeline.data_loader import DataLoader
    from shap_framework.data_infrastructure.data_pipeline.data_preprocessor import DataPreprocessor
    from shap_framework.data_infrastructure.data_pipeline.feature_engineer import FeatureEngineer
    
    # SHAP Analysis modules
    from shap_framework.shap_analysis.shap_explainer import SHAPExplainer, SHAPConfig
    from shap_framework.shap_analysis.feature_analyzer import FeatureAnalyzer
    from shap_framework.shap_analysis.causal_decomposer import CausalDecomposer
    from shap_framework.shap_analysis.story_generator import StoryGenerator
    
    IMPORTS_SUCCESSFUL = True
except ImportError as e:
    print(f"Import error: {e}")
    IMPORTS_SUCCESSFUL = False

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Phase3SHAPAnalysisTest:
    """Test suite for Phase 3 SHAP Analysis system."""
    
    def __init__(self):
        """Initialize test suite."""
        self.test_results = {}
        self.test_data = None
        self.models = {}
        self.shap_results = {}
        
        logger.info("Phase 3 SHAP Analysis Test Suite initialized")
    
    def run_all_tests(self):
        """Run complete Phase 3 test suite."""
        print("🧪 Running Phase 3: SHAP Analysis System Tests")
        print("=" * 60)
        
        if not IMPORTS_SUCCESSFUL:
            print("❌ Import test failed - cannot proceed with tests")
            return False
        
        try:
            # Test 1: Data Setup
            print("\n1️⃣ Setting up test data...")
            self.setup_test_data()
            
            # Test 2: Model Training (minimal for SHAP analysis)
            print("\n2️⃣ Training models for SHAP analysis...")
            self.train_test_models()
            
            # Test 3: SHAP Explainer
            print("\n3️⃣ Testing SHAP Explainer...")
            self.test_shap_explainer()
            
            # Test 4: Feature Analyzer
            print("\n4️⃣ Testing Feature Analyzer...")
            self.test_feature_analyzer()
            
            # Test 5: Causal Decomposer
            print("\n5️⃣ Testing Causal Decomposer...")
            self.test_causal_decomposer()
            
            # Test 6: Story Generator
            print("\n6️⃣ Testing Story Generator...")
            self.test_story_generator()
            
            # Test 7: End-to-End Workflow
            print("\n7️⃣ Testing End-to-End SHAP Workflow...")
            self.test_end_to_end_workflow()
            
            # Summary
            self.print_test_summary()
            
            return all(self.test_results.values())
            
        except Exception as e:
            logger.error(f"Test suite failed: {str(e)}")
            return False
    
    def setup_test_data(self):
        """Set up test data for SHAP analysis."""
        try:
            # Load and prepare data
            data_loader = DataLoader()
            cities = ['London', 'Manchester', 'Edinburgh']
            
            print("   📊 Loading data for cities...")
            raw_data = data_loader.load_data_for_cities(cities)
            
            # Preprocess data
            preprocessor = DataPreprocessor()
            print("   🔧 Preprocessing data...")
            preprocessed_data = preprocessor.preprocess_data(raw_data)
            
            # Engineer features
            feature_engineer = FeatureEngineer()
            print("   ⚙️ Engineering features...")
            
            # Use only most important features for faster testing
            important_features = feature_engineer.select_important_features(
                preprocessed_data, max_features=15
            )
            
            self.test_data = {
                'X': important_features,
                'raw_data': raw_data,
                'cities': cities
            }
            
            print(f"   ✅ Test data prepared: {len(important_features)} samples, {important_features.shape[1]} features")
            self.test_results['data_setup'] = True
            
        except Exception as e:
            print(f"   ❌ Data setup failed: {str(e)}")
            self.test_results['data_setup'] = False
    
    def train_test_models(self):
        """Train minimal models for SHAP testing."""
        try:
            X = self.test_data['X']
            
            # Train Climate Model
            print("   🌤️ Training Climate Model...")
            climate_model = ClimateModel()
            climate_features = [col for col in X.columns if any(keyword in col.lower() 
                              for keyword in ['pressure', 'humidity', 'temperature', 'precipitation', 'wind', 'NO2', 'solar'])]
            
            if climate_features:
                X_climate = X[climate_features]
                climate_model.train(X_climate)
                self.models['climate'] = {
                    'model': climate_model,
                    'features': X_climate,
                    'feature_names': climate_features
                }
            
            # Train Geographic Model
            print("   🗺️ Training Geographic Model...")
            geographic_model = GeographicModel()
            geographic_features = [col for col in X.columns if any(keyword in col.lower()
                                 for keyword in ['soil', 'flood', 'evapotranspiration', 'moisture'])]
            
            if geographic_features:
                X_geographic = X[geographic_features]
                geographic_model.train(X_geographic)
                self.models['geographic'] = {
                    'model': geographic_model,
                    'features': X_geographic,
                    'feature_names': geographic_features
                }
            
            print(f"   ✅ Models trained: {len(self.models)} models ready")
            self.test_results['model_training'] = True
            
        except Exception as e:
            print(f"   ❌ Model training failed: {str(e)}")
            self.test_results['model_training'] = False
    
    def test_shap_explainer(self):
        """Test SHAP Explainer functionality."""
        try:
            # Test with a model that has feature_importances_ (if available)
            test_passed = False
            
            for model_name, model_info in self.models.items():
                print(f"   🔍 Testing SHAP Explainer with {model_name} model...")
                
                # Initialize SHAP Explainer
                config = SHAPConfig(
                    explainer_type="tree",
                    background_samples=50,
                    max_evals=100
                )
                explainer = SHAPExplainer(config)
                
                # Setup explainer
                model = model_info['model'].model  # Get the actual sklearn model
                X_test = model_info['features'].head(20)  # Small sample for testing
                
                explainer.setup_explainer(
                    model=model,
                    model_type=model_name,
                    X_background=X_test,
                    model_name=model_name
                )
                
                # Generate explanations
                X_explain = model_info['features'].head(5)  # Very small sample
                shap_result = explainer.explain_prediction(
                    X_explain, 
                    model_name=model_name,
                    return_interactions=False  # Skip interactions for speed
                )
                
                # Validate results
                assert shap_result is not None
                assert hasattr(shap_result, 'shap_values')
                assert hasattr(shap_result, 'feature_importance')
                assert len(shap_result.feature_names) > 0
                
                print(f"   ✅ SHAP values shape: {shap_result.shap_values.shape}")
                print(f"   ✅ Feature importance calculated for {len(shap_result.feature_importance)} features")
                
                # Store result for other tests
                self.shap_results[model_name] = shap_result
                test_passed = True
                break  # Test with first working model
            
            self.test_results['shap_explainer'] = test_passed
            
        except Exception as e:
            print(f"   ❌ SHAP Explainer test failed: {str(e)}")
            self.test_results['shap_explainer'] = False
    
    def test_feature_analyzer(self):
        """Test Feature Analyzer functionality."""
        try:
            if not self.shap_results:
                print("   ⚠️ No SHAP results available, skipping Feature Analyzer test")
                self.test_results['feature_analyzer'] = False
                return
            
            # Get first available SHAP result
            shap_result = list(self.shap_results.values())[0]
            
            print("   📊 Testing Feature Analyzer...")
            analyzer = FeatureAnalyzer()
            
            # Test feature importance analysis
            print("   🔍 Analyzing feature importance...")
            importance_analysis = analyzer.analyze_feature_importance(shap_result)
            
            assert 'importance_statistics' in importance_analysis
            assert 'feature_rankings' in importance_analysis
            assert 'categorized_features' in importance_analysis
            
            print(f"   ✅ Critical features identified: {len(importance_analysis['feature_rankings']['critical_features'])}")
            
            # Test feature interactions (minimal)
            print("   🔗 Analyzing feature interactions...")
            interaction_analysis = analyzer.analyze_feature_interactions(shap_result, top_k=5)
            
            assert 'top_interactions' in interaction_analysis
            assert 'interaction_summary' in interaction_analysis
            
            print(f"   ✅ Top interactions found: {len(interaction_analysis['top_interactions'])}")
            
            # Test feature grouping
            print("   📦 Identifying feature groups...")
            feature_groups = analyzer.identify_feature_groups(shap_result, n_groups=3)
            
            assert len(feature_groups) > 0
            print(f"   ✅ Feature groups identified: {len(feature_groups)}")
            
            # Generate analysis report
            print("   📋 Generating analysis report...")
            analysis_report = analyzer.generate_analysis_report(shap_result)
            
            assert hasattr(analysis_report, 'feature_importance')
            assert hasattr(analysis_report, 'recommendations')
            
            print(f"   ✅ Analysis report generated with {len(analysis_report.recommendations)} recommendations")
            
            # Store for next tests
            self.feature_analysis_report = analysis_report
            
            self.test_results['feature_analyzer'] = True
            
        except Exception as e:
            print(f"   ❌ Feature Analyzer test failed: {str(e)}")
            self.test_results['feature_analyzer'] = False
    
    def test_causal_decomposer(self):
        """Test Causal Decomposer functionality."""
        try:
            if not self.shap_results:
                print("   ⚠️ No SHAP results available, skipping Causal Decomposer test")
                self.test_results['causal_decomposer'] = False
                return
            
            # Get first available SHAP result
            shap_result = list(self.shap_results.values())[0]
            
            print("   🔗 Testing Causal Decomposer...")
            decomposer = CausalDecomposer()
            
            # Mock baseline and predicted data
            baseline_data = {
                'climate': 0.0,
                'geographic': 0.0,
                'final': 0.0
            }
            
            predicted_data = {
                'climate': 0.15,
                'geographic': -0.05,
                'final': 0.08
            }
            
            # Test score decomposition
            print("   📊 Decomposing scores...")
            score_decompositions = decomposer.decompose_scores(
                shap_result, baseline_data, predicted_data
            )
            
            assert len(score_decompositions) > 0
            print(f"   ✅ Score decompositions created: {list(score_decompositions.keys())}")
            
            # Test causal chain identification
            print("   🔗 Identifying causal chains...")
            causal_chains = decomposer.identify_causal_chains(shap_result, min_chain_strength=0.05)
            
            print(f"   ✅ Causal chains identified: {len(causal_chains)}")
            
            # Test score drivers analysis
            print("   🎯 Analyzing score drivers...")
            primary_drivers, secondary_effects = decomposer.analyze_score_drivers(
                shap_result, score_decompositions
            )
            
            print(f"   ✅ Primary drivers: {len(primary_drivers)}, Secondary effects: {len(secondary_effects)}")
            
            # Generate decomposition report
            print("   📋 Generating decomposition report...")
            decomposition_report = decomposer.generate_decomposition_report(
                shap_result, baseline_data, predicted_data
            )
            
            assert hasattr(decomposition_report, 'score_decompositions')
            assert hasattr(decomposition_report, 'summary_insights')
            
            print(f"   ✅ Decomposition report generated")
            
            # Store for next tests
            self.decomposition_report = decomposition_report
            
            self.test_results['causal_decomposer'] = True
            
        except Exception as e:
            print(f"   ❌ Causal Decomposer test failed: {str(e)}")
            self.test_results['causal_decomposer'] = False
    
    def test_story_generator(self):
        """Test Story Generator functionality."""
        try:
            if not hasattr(self, 'feature_analysis_report') or not hasattr(self, 'decomposition_report'):
                print("   ⚠️ Required analysis reports not available, skipping Story Generator test")
                self.test_results['story_generator'] = False
                return
            
            # Get first available SHAP result
            shap_result = list(self.shap_results.values())[0]
            
            print("   📖 Testing Story Generator...")
            story_generator = StoryGenerator()
            
            # Test comprehensive story generation
            print("   📚 Generating comprehensive story...")
            comprehensive_story = story_generator.generate_comprehensive_story(
                shap_result=shap_result,
                feature_analysis_report=self.feature_analysis_report,
                decomposition_report=self.decomposition_report,
                location="London Test Region"
            )
            
            assert hasattr(comprehensive_story, 'title')
            assert hasattr(comprehensive_story, 'story_elements')
            assert len(comprehensive_story.story_elements) > 0
            
            print(f"   ✅ Story generated: '{comprehensive_story.title}'")
            print(f"   ✅ Story elements: {len(comprehensive_story.story_elements)}")
            print(f"   ✅ Key insights: {len(comprehensive_story.key_insights)}")
            
            # Test score explanation
            if 'final' in self.decomposition_report.score_decompositions:
                print("   📊 Testing score explanation...")
                score_explanation = story_generator.generate_score_explanation(
                    self.decomposition_report.score_decompositions['final'],
                    'final'
                )
                
                assert isinstance(score_explanation, str)
                assert len(score_explanation) > 50  # Should be substantial
                
                print(f"   ✅ Score explanation generated ({len(score_explanation)} characters)")
            
            # Test feature story
            if shap_result.feature_names:
                print("   🎯 Testing feature story...")
                feature_story = story_generator.generate_feature_story(
                    feature_name=shap_result.feature_names[0],
                    shap_result=shap_result,
                    feature_analysis_report=self.feature_analysis_report
                )
                
                assert isinstance(feature_story, str)
                assert len(feature_story) > 30
                
                print(f"   ✅ Feature story generated for {shap_result.feature_names[0]}")
            
            self.test_results['story_generator'] = True
            
        except Exception as e:
            print(f"   ❌ Story Generator test failed: {str(e)}")
            self.test_results['story_generator'] = False
    
    def test_end_to_end_workflow(self):
        """Test complete end-to-end SHAP analysis workflow."""
        try:
            print("   🔄 Testing end-to-end SHAP workflow...")
            
            # Check if all components are working
            required_components = [
                'shap_explainer', 'feature_analyzer', 
                'causal_decomposer', 'story_generator'
            ]
            
            components_working = all(
                self.test_results.get(comp, False) for comp in required_components
            )
            
            if not components_working:
                print("   ⚠️ Not all components passed individual tests")
                self.test_results['end_to_end'] = False
                return
            
            # Test integration
            if (hasattr(self, 'feature_analysis_report') and 
                hasattr(self, 'decomposition_report') and 
                self.shap_results):
                
                # Simulate complete workflow
                print("   🎯 Running complete analysis workflow...")
                
                # Get results
                shap_result = list(self.shap_results.values())[0]
                analysis_report = self.feature_analysis_report
                decomposition_report = self.decomposition_report
                
                # Generate final narrative
                story_generator = StoryGenerator()
                final_story = story_generator.generate_comprehensive_story(
                    shap_result, analysis_report, decomposition_report, "Test Location"
                )
                
                # Validate workflow output
                workflow_valid = (
                    final_story is not None and
                    len(final_story.story_elements) > 3 and
                    len(final_story.key_insights) > 2 and
                    final_story.confidence_level in ['low', 'moderate', 'high']
                )
                
                if workflow_valid:
                    print("   ✅ End-to-end workflow successful")
                    print(f"   📊 Final story confidence: {final_story.confidence_level}")
                    print(f"   📝 Total story elements: {len(final_story.story_elements)}")
                    
                self.test_results['end_to_end'] = workflow_valid
            else:
                print("   ⚠️ Missing required components for end-to-end test")
                self.test_results['end_to_end'] = False
            
        except Exception as e:
            print(f"   ❌ End-to-end workflow test failed: {str(e)}")
            self.test_results['end_to_end'] = False
    
    def print_test_summary(self):
        """Print comprehensive test summary."""
        print("\n" + "="*60)
        print("🧪 PHASE 3: SHAP ANALYSIS SYSTEM TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {total_tests - passed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\n📋 Detailed Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name.replace('_', ' ').title()}: {status}")
        
        # Overall assessment
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! Phase 3 SHAP Analysis System is fully functional!")
        elif passed_tests >= total_tests * 0.8:
            print("\n🟡 MOSTLY SUCCESSFUL! Minor issues to address.")
        else:
            print("\n🔴 SIGNIFICANT ISSUES DETECTED! Review failed components.")
        
        print("\n🔍 SHAP Analysis Capabilities Validated:")
        if self.test_results.get('shap_explainer', False):
            print("   • ✅ SHAP model interpretation")
        if self.test_results.get('feature_analyzer', False):
            print("   • ✅ Feature importance and interaction analysis")
        if self.test_results.get('causal_decomposer', False):
            print("   • ✅ Causal factor decomposition")
        if self.test_results.get('story_generator', False):
            print("   • ✅ Natural language explanations")
        if self.test_results.get('end_to_end', False):
            print("   • ✅ Complete workflow integration")
        
        print("\n🚀 Phase 3 Implementation Status: COMPLETE")

def main():
    """Run Phase 3 SHAP Analysis tests."""
    tester = Phase3SHAPAnalysisTest()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 Phase 3 ready for production use!")
        return 0
    else:
        print("\n⚠️ Phase 3 requires attention before deployment.")
        return 1

if __name__ == "__main__":
    exit(main()) 