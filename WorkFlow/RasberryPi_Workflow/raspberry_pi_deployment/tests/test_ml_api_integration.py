#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi ML API Integration Test
Test calling website ML prediction API from Raspberry Pi
"""

import os
import sys
import requests
import json
from datetime import datetime
import time

# Add core directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

def test_ml_api_integration():
    """Test ML API integration functionality"""
    
    print("=" * 60)
    print("🔬 Raspberry Pi ML API Integration Test")
    print("=" * 60)
    
    # Configure test parameters
    test_locations = [
        {
            'name': 'London',
            'latitude': 51.5074,
            'longitude': -0.1278,
            'expected_temp_range': (8, 18)  # Approximate temperature range
        },
        {
            'name': 'Manchester',
            'latitude': 53.4808,
            'longitude': -2.2426,
            'expected_temp_range': (7, 16)
        },
        {
            'name': 'Edinburgh',
            'latitude': 55.9533,
            'longitude': -3.1883,
            'expected_temp_range': (6, 15)
        }
    ]
    
    # Test different website URLs
    test_urls = [
        'https://your-app.onrender.com',  # Replace with actual URL
        'http://localhost:5000',  # Local testing
        'https://obscura-no7.onrender.com'  # Possible URL
    ]
    
    successful_tests = 0
    total_tests = 0
    
    # Test each URL
    for base_url in test_urls:
        print(f"\n🌐 Testing API URL: {base_url}")
        print("-" * 50)
        
        # First test health check
        try:
            health_response = requests.get(f"{base_url}/health", timeout=10)
            if health_response.status_code == 200:
                print("✅ Health check passed")
            else:
                print(f"⚠️ Health check failed: {health_response.status_code}")
                continue
        except Exception as e:
            print(f"❌ Cannot connect to {base_url}: {e}")
            continue
        
        # Test each location
        for location in test_locations:
            total_tests += 1
            
            print(f"\n📍 Testing location: {location['name']}")
            print(f"   Coordinates: {location['latitude']}, {location['longitude']}")
            
            try:
                # Build prediction request
                prediction_data = {
                    'latitude': location['latitude'],
                    'longitude': location['longitude'],
                    'month': datetime.now().month,
                    'future_years': 0
                }
                
                # Send prediction request
                start_time = time.time()
                response = requests.post(
                    f"{base_url}/api/v1/ml/predict",
                    json=prediction_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Validate response structure
                    if 'prediction' in result and 'model_info' in result:
                        prediction = result['prediction']
                        model_info = result['model_info']
                        
                        print(f"✅ Prediction successful (time: {response_time:.2f}s)")
                        print(f"   🌡️ Temperature: {prediction.get('temperature', 'N/A')}°C")
                        print(f"   💧 Humidity: {prediction.get('humidity', 'N/A')}%")
                        print(f"   🌀 Pressure: {prediction.get('pressure', 'N/A')} hPa")
                        print(f"   🤖 Model confidence: {model_info.get('confidence', 'N/A')}")
                        print(f"   📊 Model type: {model_info.get('model_type', 'N/A')}")
                        
                        # Validate temperature range
                        temp = prediction.get('temperature')
                        if temp is not None:
                            min_temp, max_temp = location['expected_temp_range']
                            if min_temp <= temp <= max_temp:
                                print(f"   ✅ Temperature within reasonable range")
                            else:
                                print(f"   ⚠️ Temperature exceeds expected range ({min_temp}-{max_temp}°C)")
                        
                        successful_tests += 1
                        
                    else:
                        print(f"❌ Response format error: {result}")
                        
                else:
                    print(f"❌ Prediction failed: {response.status_code}")
                    try:
                        error_data = response.json()
                        print(f"   Error message: {error_data.get('error', 'Unknown error')}")
                    except:
                        print(f"   Error message: {response.text}")
                
            except Exception as e:
                print(f"❌ Request exception: {e}")
        
        # If this URL has successful tests, use it
        if successful_tests > 0:
            print(f"\n🎉 Found working API URL: {base_url}")
            working_url = base_url
            break
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results Summary")
    print("=" * 60)
    print(f"Total tests: {total_tests}")
    print(f"Successful tests: {successful_tests}")
    print(f"Success rate: {(successful_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
    
    if successful_tests > 0:
        print(f"✅ API integration test passed!")
        return True
    else:
        print(f"❌ API integration test failed!")
        return False

def test_cloud_api_client():
    """Test CloudAPIClient environmental prediction functionality"""
    
    print("\n" + "=" * 60)
    print("🔧 CloudAPIClient Environmental Prediction Test")
    print("=" * 60)
    
    try:
        # Import CloudAPIClient
        from core.cloud_api_client import CloudAPIClient
        
        # Create client instance (using default configuration)
        client = CloudAPIClient()
        
        # Test environmental prediction
        print("\n📍 Testing London environmental prediction...")
        
        prediction_result = client.predict_environmental_data(
            latitude=51.5074,
            longitude=-0.1278,
            month=datetime.now().month,
            future_years=0
        )
        
        if prediction_result:
            print("✅ Environmental prediction successful")
            print(f"   Prediction result: {prediction_result}")
            
            # Test integration with art style prediction
            print("\n🎨 Testing art style prediction integration...")
            
            weather_features = {
                'temperature': 15.0,
                'humidity': 65.0,
                'pressure': 1013.0
            }
            
            location_info = {
                'latitude': 51.5074,
                'longitude': -0.1278,
                'city': 'London'
            }
            
            style_prediction = client.predict_art_style(weather_features, location_info)
            
            if style_prediction:
                print("✅ Art style prediction successful")
                print(f"   Prediction result: {style_prediction}")
                return True
            else:
                print("❌ Art style prediction failed")
                return False
        else:
            print("❌ Environmental prediction failed")
            return False
            
    except Exception as e:
        print(f"❌ CloudAPIClient test failed: {e}")
        return False

def main():
    """Main function"""
    print(f"🚀 Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Direct API calls
    api_test_result = test_ml_api_integration()
    
    # Test 2: CloudAPIClient integration
    client_test_result = test_cloud_api_client()
    
    print("\n" + "=" * 60)
    print("🏁 Overall Test Results")
    print("=" * 60)
    
    if api_test_result and client_test_result:
        print("✅ All tests passed! Raspberry Pi ML API integration successful!")
        print("\n🎯 Next steps:")
        print("  1. Update website_api_url in config.json")
        print("  2. Run complete workflow test on Raspberry Pi")
        print("  3. Verify end-to-end data flow")
    else:
        print("❌ Some tests failed, please check:")
        print("  - Is the website running normally")
        print("  - Is the ML API correctly deployed")
        print("  - Is network connection working")
        print("  - Are API keys correctly configured")
    
    print(f"\n🏁 End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 