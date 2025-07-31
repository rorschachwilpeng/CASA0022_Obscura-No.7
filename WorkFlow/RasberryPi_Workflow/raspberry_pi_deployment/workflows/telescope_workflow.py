#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi Telescope Workflow
Raspberry Pi Virtual Telescope Workflow - Real Hardware Version
"""

import sys
import os
import json
import time
import logging
import random
from datetime import datetime
from typing import Dict, Any, Optional

# Add parent directory to path for importing core modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import core modules
try:
    from core.coordinate_calculator import CoordinateCalculator
    from core.weather_client import WeatherClient  
    from core.cloud_api_client import CloudAPIClient
    from core.config_manager import ConfigManager
    from core.progress_display import ProgressDisplay
    from core.maps_client import MapsClient
    from core.raspberry_pi_hardware import RaspberryPiHardware
except ImportError:
    # Fallback import path
    sys.path.insert(0, os.path.join(parent_dir, 'core'))
    from coordinate_calculator import CoordinateCalculator
    from weather_client import WeatherClient
    from cloud_api_client import CloudAPIClient
    from config_manager import ConfigManager
    from progress_display import ProgressDisplay
    from maps_client import MapsClient
    from raspberry_pi_hardware import RaspberryPiHardware

class RaspberryPiTelescopeWorkflow:
    """Raspberry Pi Virtual Telescope Workflow"""
    
    def __init__(self, config_path='config/config.json'):
        """Initialize workflow"""
        self.config_manager = ConfigManager(config_path)
        self.progress = ProgressDisplay()
        
        # Initialize core components
        self.coord_calc = CoordinateCalculator(self.config_manager.config)
        
        # Initialize Open-Meteo client (no API key required)
        from core.open_meteo_client import OpenMeteoClient
        self.weather_client = OpenMeteoClient()
        print("🌤️ Open-Meteo client initialized (免费API，无需密钥)")
        
        # Initialize map client
        google_maps_key = self.config_manager.get('google_maps_api_key')
        if google_maps_key:
            self.maps_client = MapsClient(google_maps_key)
            print("🗺️ Google Maps client initialized")
        else:
            self.maps_client = None
            print("⚠️ Google Maps API key not configured, map functionality will be skipped")
        
        # Initialize cloud client with maps client for building information
        self.cloud_client = CloudAPIClient(self.config_manager, maps_client=self.maps_client)
        
        # Initialize hardware interface
        self.hardware = RaspberryPiHardware(self.config_manager.config)
        
        # Session data
        self.session_data = {
            'workflow_id': f"pi_telescope_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'start_time': datetime.now(),
            'device_type': 'raspberry_pi',
            'hardware_status': self.hardware.get_hardware_status()
        }
        
        self.last_result = None
        self.logger = logging.getLogger(__name__)
        
        print("🍓 Raspberry Pi Virtual Telescope initialized")
        print(f"📊 Hardware Status: {self._format_hardware_status()}")
    
    def _format_hardware_status(self) -> str:
        """Format hardware status display"""
        status = self.hardware.get_hardware_status()
        indicators = []
        
        if status['hardware_available']:
            indicators.append("🍓 Pi")
        else:
            indicators.append("💻 Sim")
            
        if status['encoder_available']:
            indicators.append("🎛️ Encoder")
        if status['compass_available']:
            indicators.append("🧭 Compass")
        if status['button_available']:
            indicators.append("🔘 Button")
            
        return " | ".join(indicators)
    
    def run_telescope_session(self, hardware_params=None) -> Dict[str, Any]:
        """Run complete telescope session
        
        Args:
            hardware_params: Optional hardware parameters from exhibition controller
                            {distance_km, direction_degrees, time_offset_years}
        """
        print("\n🔭 Starting Obscura No.7 Virtual Telescope")
        print("=" * 60)
        
        # Store hardware parameters for use in workflow
        self._provided_hardware_params = hardware_params
        
        try:
            if hardware_params:
                print(f"📊 Using provided parameters: distance={hardware_params['distance_km']}km, "
                     f"direction={hardware_params['direction_degrees']}°, "
                     f"time_offset={hardware_params['time_offset_years']}years")
            else:
                # Show welcome message only when collecting parameters interactively
                self._show_welcome_message()
            
            # Run 6-step workflow
            result = self._execute_workflow()
            
            # Show completion message
            self._show_completion_message(result)
            
            return result
            
        except KeyboardInterrupt:
            print("\n⏹️ User interrupted telescope session")
            return {'success': False, 'error': 'User interrupted'}
        except Exception as e:
            self.logger.error(f"Workflow failed: {e}")
            print(f"\n❌ Workflow failed: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            self.hardware.cleanup()
    
    def _show_welcome_message(self):
        """Show welcome message"""
        print("🌟 Welcome to Obscura No.7 Virtual Telescope")
        print("📡 This device will help you explore future environmental possibilities")
        print()
        print("🎮 Operating Instructions:")
        if self.hardware.hardware_available:
            print("   📐 Turn encoder to set distance")
            print("   🔘 Press button to confirm selection")
            print("   🧭 Compass sensor will automatically read direction")
        else:
            print("   ⌨️ Use keyboard to input parameters")
        print()
        print("⏳ Preparing to start exploration...")
        time.sleep(2)
    
    def _execute_workflow(self) -> Dict[str, Any]:
        """Execute 6-step workflow"""
        workflow_result = {}
        
        # Initialize progress display
        self.progress.init_workflow(
            title="🔭 Obscura No.7 Virtual Telescope Workflow",
            total_steps=7,  # Increased to 7 steps, including map generation
            workflow_id=self.session_data['workflow_id']
        )
        
        # Step 1: Hardware Data Collection
        with self.progress.step(1, "Hardware Data Collection", "Reading user input from encoder and compass sensor") as step:
            hardware_data = self._collect_hardware_input()
            workflow_result['hardware_input'] = hardware_data
            step.success("Hardware data collection completed")
        
        # Step 2: Coordinate Calculation
        with self.progress.step(2, "Coordinate Calculation", "Calculating target coordinates based on distance and direction") as step:
            coordinates = self._calculate_target_coordinates(hardware_data)
            workflow_result['coordinates'] = coordinates
            self._show_coordinates_result(coordinates)
            step.success("Coordinate calculation completed")
        
        # Step 3: Environmental Data Acquisition
        with self.progress.step(3, "Environmental Data Acquisition", "Calling Open-Meteo API to get real environmental data") as step:
            weather_data = self._get_environmental_data(coordinates)
            workflow_result['weather_data'] = weather_data
            self._show_weather_summary(weather_data)
            step.success("Real environmental data acquisition completed")
        
        # Step 4: AI Art Prediction
        with self.progress.step(4, "AI Art Prediction", "Using machine learning models to predict art style") as step:
            ml_features = self._prepare_ml_features(coordinates, weather_data)
            style_prediction = self._predict_art_style(ml_features, coordinates)
            workflow_result['style_prediction'] = style_prediction
            self._show_prediction_result(style_prediction)
            step.success("AI art prediction completed")
        
        # Step 5: Map Generation
        with self.progress.step(5, "Map Generation", "Using Google Maps API to generate location map") as step:
            map_info = self._generate_location_map(coordinates, hardware_data)
            workflow_result['map_info'] = map_info
            if map_info and map_info.get('success'):
                step.success("Map generation completed")
            else:
                step.warning("Map generation failed or skipped")
        
        # Step 6: Image Generation
        with self.progress.step(6, "AI Image Generation", "Using AI to generate artwork") as step:
            image_path = self._generate_artwork(style_prediction, weather_data, coordinates)
            workflow_result['generated_image'] = image_path
            step.success(f"Image generation completed: {os.path.basename(image_path)}")
        
        # Step 7: Cloud Synchronization
        with self.progress.step(7, "Cloud Synchronization", "Uploading images and data to exhibition website") as step:
            sync_result = self._sync_to_cloud(workflow_result)
            workflow_result['sync_result'] = sync_result
            if sync_result and sync_result.get('success'):
                step.success("Cloud synchronization completed")
            else:
                step.warning("Cloud synchronization failed or skipped")
        
        # Complete workflow
        self.progress.complete_workflow(success=True)
        
        # Save results
        final_result = self._save_workflow_result(workflow_result)
        
        return final_result
    
    def _collect_hardware_input(self) -> Dict[str, float]:
        """Collect hardware input data - using provided parameters or hardware input"""
        
        # 🔧 修复：优先使用提供的硬件参数
        if hasattr(self, '_provided_hardware_params') and self._provided_hardware_params:
            params = self._provided_hardware_params
            print(f"\n✅ Using provided hardware parameters:")
            print(f"   📏 Distance: {params['distance_km']} km")
            print(f"   🧭 Direction: {params['direction_degrees']}°")
            print(f"   ⏰ Time offset: {params['time_offset_years']} years")
            
            return {
                'distance_km': params['distance_km'],
                'direction_degrees': params['direction_degrees'],
                'time_offset_years': params['time_offset_years']
            }
        else:
            # 如果没有提供参数，使用原来的硬件读取方式
            print("\n🎮 Three-parameter synchronized setup...")
            
            # Use new three-parameter synchronized input system
            distance, direction, time_offset = self.hardware.read_three_parameter_input(timeout=120)
            
            return {
                'distance_km': distance,
                'direction_degrees': direction,
                'time_offset_years': time_offset
            }
    
    def _calculate_target_coordinates(self, hardware_data: Dict) -> Dict:
        """Calculate target coordinates"""
        base_lat = self.config_manager.get('telescope_settings.base_latitude', 51.5074)
        base_lon = self.config_manager.get('telescope_settings.base_longitude', -0.1278)
        
        target_coords = self.coord_calc.calculate_target_coordinates(
            base_lat, base_lon,
            hardware_data['distance_km'] * 1000,  # Convert to meters
            hardware_data['direction_degrees']
        )
        
        return {
            'latitude': target_coords['latitude'],
            'longitude': target_coords['longitude'],
            'distance_km': hardware_data['distance_km'],
            'direction_degrees': hardware_data['direction_degrees'],
            'formatted_coords': f"{target_coords['latitude']:.6f}, {target_coords['longitude']:.6f}"
        }
    
    def _get_environmental_data(self, coordinates: Dict) -> Dict:
        """Get environmental data using Open-Meteo API"""
        if self.weather_client:
            weather_data = self.weather_client.get_current_environmental_data(
                coordinates['latitude'],
                coordinates['longitude']
            )
            if weather_data:
                return weather_data
        
        # If API is unavailable or fails, create fallback weather data
        print("⚠️ Using fallback weather data")
        return self._create_fallback_weather_data(
            coordinates['latitude'],
            coordinates['longitude']
        )
    
    def _prepare_ml_features(self, coordinates: Dict, weather_data: Dict) -> Dict:
        """Prepare ML features"""
        # Handle case where weather_data is None (API failure)
        if weather_data is None:
            print("⚠️ No weather data available, using default values for ML features")
            current_weather = {}
        else:
            # Double-check weather_data is not None before calling .get()
            current_weather = weather_data.get('current_weather', {}) if weather_data is not None else {}
            # Handle case where current_weather itself is None
            if current_weather is None:
                print("⚠️ Current weather data is None, using default values")
                current_weather = {}
        
        return {
            'latitude': coordinates['latitude'],
            'longitude': coordinates['longitude'],
            'temperature': current_weather.get('temperature', 15),
            'humidity': current_weather.get('humidity', 60),
            'pressure': current_weather.get('pressure', 1013),
            'wind_speed': current_weather.get('wind_speed', 5),
            'weather_main': current_weather.get('weather_main', 'Clear'),
            'weather_description': current_weather.get('weather_description', 'clear sky')
        }
    
    def _predict_art_style(self, ml_features: Dict, location_info: Dict) -> Dict:
        """Predict art style"""
        return self.cloud_client.predict_art_style(ml_features, location_info)
    
    def _generate_location_map(self, coordinates: Dict, hardware_data: Dict) -> Optional[Dict]:
        """Generate location map
        
        Args:
            coordinates: Coordinate information
            hardware_data: Hardware input data
            
        Returns:
            Dict: Map information including address, map file path, etc.
        """
        if not self.maps_client:
            print("⚠️ Google Maps client not initialized, skipping map generation")
            return None
        
        try:
            lat = coordinates['latitude']
            lon = coordinates['longitude']
            distance = hardware_data['distance_km'] * 1000  # Convert to meters
            
            print(f"🗺️ Generating location map: {lat:.4f}, {lon:.4f}")
            
            # Get location information
            location_info = self.maps_client.get_location_info(lat, lon)
            print(f"📍 Location: {location_info}")
            
            # Get detailed location information
            location_details = self.maps_client.get_location_details(lat, lon)
            
            # Generate static map
            map_image = self.maps_client.get_static_map(lat, lon, distance, 800, 600)
            
            map_file_path = None
            if map_image:
                # Save map image
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                direction_name = self.maps_client.get_direction_name(hardware_data['direction_degrees'])
                distance_str = self.maps_client.format_distance(distance)
                
                map_filename = f"telescope_map_{distance_str}_{direction_name}_{timestamp}.png"
                map_file_path = os.path.join('outputs', 'images', map_filename)
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(map_file_path), exist_ok=True)
                map_image.save(map_file_path)
                print(f"💾 Map saved: {map_filename}")
            
            return {
                'success': True,
                'coordinates': {
                    'latitude': lat,
                    'longitude': lon
                },
                'location_info': location_info,
                'location_details': location_details,
                'map_image_path': map_file_path,
                'distance_meters': distance,
                'direction_degrees': hardware_data['direction_degrees'],
                'direction_name': self.maps_client.get_direction_name(hardware_data['direction_degrees'])
            }
            
        except Exception as e:
            print(f"❌ Map generation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'coordinates': coordinates
            }
    
    def _generate_artwork(self, style_prediction: Dict, weather_data: Dict, location_info: Dict) -> str:
        """Generate artwork - ensure valid path is returned"""
        try:
            # Handle case where weather_data is None
            if weather_data is None:
                print("⚠️ No weather data available, using default values for artwork generation")
                weather_data = {'current_weather': {'weather_main': 'Clear', 'weather_description': 'clear sky'}}
            
            image_path = self.cloud_client.generate_artwork(style_prediction, weather_data, location_info)
            
            # Ensure valid path is returned
            if not image_path:
                print("⚠️ Image generation returned empty path, creating placeholder")
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'telescope_placeholder_{timestamp}.txt'
                image_path = os.path.join('outputs', 'images', filename)
                
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                with open(image_path, 'w', encoding='utf-8') as f:
                    f.write(f"Telescope session {timestamp}\nImage generation failed")
            
            # Verify file exists
            if not os.path.exists(image_path):
                print(f"⚠️ Generated file does not exist: {image_path}")
                # Create placeholder
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'telescope_missing_{timestamp}.txt'
                image_path = os.path.join('outputs', 'images', filename)
                
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                with open(image_path, 'w', encoding='utf-8') as f:
                    f.write(f"Telescope session {timestamp}\nGenerated file was missing")
            
            return image_path
            
        except Exception as e:
            print(f"❌ Image generation exception: {e}")
            # Create error placeholder
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'telescope_error_{timestamp}.txt'
            image_path = os.path.join('outputs', 'images', filename)
            
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            with open(image_path, 'w', encoding='utf-8') as f:
                f.write(f"Telescope session {timestamp}\nError: {str(e)}")
            
            return image_path

    def _sync_to_cloud(self, workflow_result: Dict) -> Dict:
        """Sync to cloud"""
        if not workflow_result.get('generated_image'):
            return None
        
        # Build upload metadata
        metadata = {
            'coordinates': workflow_result.get('coordinates', {}),
            'weather': workflow_result.get('weather_data', {}),
            'style': workflow_result.get('style_prediction', {}),
            'hardware_input': workflow_result.get('hardware_input', {}),
            'map_info': workflow_result.get('map_info', {}),  # 包含地理位置信息
            'timestamp': datetime.now().isoformat(),
            'device_type': 'raspberry_pi',
            'workflow_id': self.session_data['workflow_id']
        }
        
        return self.cloud_client.upload_to_website(
            workflow_result['generated_image'],
            metadata
        )
    
    def _save_workflow_result(self, workflow_result: Dict) -> Dict:
        """Save workflow results"""
        final_result = {
            'workflow_id': self.session_data['workflow_id'],
            'timestamp': datetime.now().isoformat(),
            'device_type': 'raspberry_pi',
            'hardware_status': self.session_data['hardware_status'],
            'success': True,
            'execution_time': (datetime.now() - self.session_data['start_time']).total_seconds(),
            'data': workflow_result
        }
        
        # Save to file
        output_dir = 'outputs/workflow_results'
        os.makedirs(output_dir, exist_ok=True)
        
        result_file = os.path.join(output_dir, f"{self.session_data['workflow_id']}.json")
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(final_result, f, indent=2, ensure_ascii=False, default=str)
        
        self.last_result = final_result
        return final_result
    
    def _show_coordinates_result(self, coordinates: Dict):
        """Display coordinate calculation results"""
        self.progress.show_coordinates(
            coordinates['latitude'],
            coordinates['longitude'],
            coordinates['distance_km'] * 1000,  # Convert to meters
            coordinates['direction_degrees']
        )
    
    def _show_weather_summary(self, weather_data: Dict):
        """Display weather summary"""
        if weather_data is None:
            print("⚠️ No weather data available to display")
            return
        
        # Ensure weather_data is not None before proceeding
        try:
            current_weather = weather_data.get('current_weather', {}) if weather_data else {}
            if current_weather:
                print(f"🌤️ Weather: {current_weather.get('weather_description', 'N/A')}")
                print(f"🌡️ Temperature: {current_weather.get('temperature', 'N/A')}°C")
                print(f"💨 Wind: {current_weather.get('wind_speed', 'N/A')} km/h")
        except AttributeError as e:
            print(f"⚠️ Error displaying weather summary: {e}")
            print("⚠️ Using default weather display")
            return
        self.progress.show_weather_summary(weather_data)
    
    def _show_prediction_result(self, prediction: Dict):
        """Display AI prediction results"""
        if prediction is not None:
            self.progress.show_ml_prediction(prediction)
        else:
            print("⚠️ No prediction result to display (prediction is None)")
    
    def _show_completion_message(self, result: Dict):
        """Display completion message"""
        print("\n" + "=" * 60)
        print("🎯 Telescope session completed!")
        
        # Safe execution time display
        try:
            exec_time = result.get('execution_time', 0) if result else 0
            print(f"⏱️ Execution time: {exec_time:.1f} seconds")
        except (AttributeError, TypeError) as e:
            print(f"⏱️ Execution time: N/A")
        
        # Safe image display
        try:
            if result and result.get('data') and result['data'] and result['data'].get('generated_image'):
                image_path = result['data']['generated_image']
                print(f"🎨 Generated image: {os.path.basename(image_path)}")
        except (AttributeError, TypeError, KeyError) as e:
            print("🎨 Generated image: N/A")
        
        # Safe sync result display - more robust checking
        try:
            if (result and 
                isinstance(result, dict) and 
                result.get('data') and 
                isinstance(result['data'], dict)):
                
                sync_result = result['data'].get('sync_result')
                if (sync_result and 
                    isinstance(sync_result, dict) and 
                    sync_result.get('success')):
                    
                    # Check for image URL in sync result
                    image_data = sync_result.get('image_data')
                    if (image_data and 
                        isinstance(image_data, dict) and 
                        image_data.get('image') and 
                        isinstance(image_data['image'], dict) and 
                        image_data['image'].get('url')):
                        print(f"🌐 Image URL: {image_data['image']['url']}")
        except (AttributeError, TypeError, KeyError) as e:
            pass  # Silent fail for sync result display
        
        print("\n🔭 Thank you for using Obscura No.7 Virtual Telescope!")

    def _create_fallback_weather_data(self, lat, lon):
        """Create fallback weather data"""
        import random
        
        return {
            'coordinates': {'lat': lat, 'lon': lon},
            'timestamp': datetime.now().isoformat(),
            'current_weather': {
                'temperature': 15.0 + random.uniform(-5, 15),
                'feels_like': 15.0 + random.uniform(-5, 15),
                'humidity': random.randint(40, 80),
                'pressure': random.randint(990, 1030),
                'wind_speed': random.uniform(0, 10),
                'wind_direction': random.randint(0, 360),
                'visibility': random.uniform(5, 15),
                'cloud_cover': random.randint(0, 100),
                'weather_main': random.choice(['Clear', 'Clouds', 'Rain']),
                'weather_description': random.choice(['Clear', 'Cloudy', 'Light Rain']),
                'weather_id': random.choice([800, 801, 500]),  # Clear, Few clouds, Light rain
                'location_name': 'Simulated Location',
                'country': 'UK'
            },
            'forecast': {
                'daily': [{
                    'temperature_max': 20.0 + random.uniform(-5, 10),
                    'temperature_min': 10.0 + random.uniform(-5, 10),
                    'humidity': random.randint(40, 80),
                    'pressure': random.randint(990, 1030)
                } for _ in range(5)]
            },
            'air_quality': {
                'aqi': random.randint(1, 3),
                'aqi_description': random.choice(['Excellent', 'Good', 'Moderate']),
                'pm2_5': random.randint(5, 25),
                'pm10': random.randint(10, 50),
                'no2': random.randint(10, 40),
                'o3': random.randint(40, 100)
            },
            'data_quality': {
                'score': 60,
                'level': 'simulated',
                'issues': ['Using simulated data - API call failed']
            }
        }

def main():
    """Main function"""
    print("🍓 Raspberry Pi Obscura No.7 Virtual Telescope")
    print("=" * 60)
    
    try:
        # Create workflow instance
        workflow = RaspberryPiTelescopeWorkflow()
        
        # Run telescope session
        result = workflow.run_telescope_session()
        
        # Display final status with robust error handling
        try:
            if result and isinstance(result, dict) and result.get('success'):
                print("\n✅ Session completed successfully")
            else:
                error_msg = 'Unknown error'
                if result and isinstance(result, dict):
                    error_msg = result.get('error', 'Unknown error')
                elif result is None:
                    error_msg = 'Workflow returned None'
                print(f"\n❌ Session failed: {error_msg}")
        except (AttributeError, TypeError) as e:
            print(f"\n⚠️ Error displaying final status")
            print("⚠️ Session may have completed, but status display failed")
            
    except KeyboardInterrupt:
        print("\n⏹️ Program interrupted by user")
    except Exception as e:
        print(f"\n💥 Program exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 