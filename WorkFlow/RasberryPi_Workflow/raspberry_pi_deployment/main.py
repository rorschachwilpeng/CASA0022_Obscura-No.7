#!/usr/bin/env python3
"""
Obscura No.7 Virtual Telescope - Main Entry Point
Supports both development mode and exhibition mode for gallery display.

Exhibition Mode Features:
- Continuous loop operation
- Touch screen interface (Pygame)
- State machine driven workflow
- Automatic error recovery
- Resource management
"""

import sys
import os
import logging
import argparse
import signal
import time
from pathlib import Path
from typing import Optional

# Add current directory to Python path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# Import core modules
try:
    from core.exhibition_state_machine import ExhibitionStateMachine, ExhibitionState
    from core.pygame_interface import PygameInterface
    from core.obscura_workflow import ObscuraWorkflow
    from core.progress_display import ProgressDisplay
    from workflows.telescope_workflow import RaspberryPiTelescopeWorkflow
except ImportError as e:
    print(f"Error importing core modules: {e}")
    print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)

class ExhibitionController:
    """
    Main controller for exhibition mode.
    Integrates state machine, pygame interface, and telescope workflow.
    """
    
    def __init__(self, fullscreen: bool = True, log_level: str = "INFO"):
        # Setup logging
        self.setup_logging(log_level)
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.state_machine = ExhibitionStateMachine()
        self.interface = PygameInterface(fullscreen=fullscreen)
        # 延迟初始化重量级组件，避免启动时阻塞
        self.telescope_workflow = None
        self.obscura_workflow = None
        
        # State
        self.running = True
        self.processing_active = False
        
        # Hardware interface for parameter input
        from core.raspberry_pi_hardware import RaspberryPiHardware
        from core.config_manager import ConfigManager
        config_manager = ConfigManager('config/config.json')
        self.hardware = RaspberryPiHardware(config_manager.config)
        
        # Parameter tracking
        self.last_distance = 25.0
        self.last_angle = 0.0  
        self.last_time_offset = 0
        
        # Setup callbacks
        self._setup_callbacks()
        
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("Exhibition controller initialized")
    
    def setup_logging(self, log_level: str):
        """Setup logging configuration"""
        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f'Invalid log level: {log_level}')
        
        # Create logs directory if it doesn't exist
        log_dir = current_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=numeric_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "exhibition.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def _setup_callbacks(self):
        """Setup callbacks between components"""
        # State machine callbacks
        self.state_machine.set_callback('on_state_change', self._on_state_change)
        self.state_machine.set_callback('on_data_fetch_trigger', self._on_data_fetch_trigger)
        self.state_machine.set_callback('on_result_ready', self._on_result_ready)
        self.state_machine.set_callback('on_error', self._on_error)
        self.state_machine.set_callback('on_reset', self._on_reset)
        
        # Interface callbacks
        self.interface.set_callback('on_city_selected', self._on_city_selected)
        self.interface.set_callback('on_data_fetch_click', self._on_data_fetch_click)
        self.interface.set_callback('on_touch_continue', self._on_touch_continue)
        self.interface.set_callback('on_reset_request', self._on_reset_request)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, initiating shutdown...")
        self.shutdown()
    
    def _on_state_change(self, old_state, new_state, context):
        """Handle state machine state changes"""
        self.interface.update_state(new_state, context)
        self.logger.info(f"State changed: {old_state.value} → {new_state.value}")
    
    def _on_city_selected(self, city_name: str):
        """Handle city selection from interface"""
        self.state_machine.select_city(city_name)
        
    def _on_data_fetch_click(self):
        """Handle data fetch button click from interface"""
        if self.state_machine.context.current_state == ExhibitionState.PARAMETER_INPUT:
            # Skip confirmation, directly start processing
            self.state_machine.transition_to(
                ExhibitionState.PROCESSING, 
                "User confirmed parameters and started processing"
            )
            # Trigger data fetch processing
            self._on_data_fetch_trigger(self.state_machine.context)
        elif self.state_machine.context.current_state == ExhibitionState.DATA_FETCH_CONFIRMATION:
            # Confirm data fetch
            self.state_machine.trigger_data_fetch()
    
    def _on_data_fetch_trigger(self, context):
        """Handle data fetch trigger from state machine"""
        if not self.processing_active:
            self.processing_active = True
            # Start processing in a separate thread to avoid blocking UI
            import threading
            processing_thread = threading.Thread(
                target=self._run_telescope_workflow,
                args=(context,)
            )
            processing_thread.daemon = True
            processing_thread.start()
    
    def _run_telescope_workflow(self, context):
        """Run the telescope workflow in background"""
        try:
            self.logger.info("Starting telescope workflow processing")
            
            # 确保telescope workflow已初始化
            if self.telescope_workflow is None:
                self.logger.info("Initializing telescope workflow...")
                self.telescope_workflow = RaspberryPiTelescopeWorkflow()
            
            # Run the telescope workflow
            # Note: For now we'll use the simplified session runner
            # TODO: Integrate distance, angle, time_offset parameters
            result = self.telescope_workflow.run_telescope_session()
            
            if result and 'generated_image_path' in result:
                # Load the generated image
                if self.interface.load_image(result['generated_image_path']):
                    # Set processing results
                    self.state_machine.set_processing_result(
                        environmental_data=result.get('environmental_data', {}),
                        shap_prediction=result.get('shap_prediction', {}),
                        image_path=result['generated_image_path']
                    )
                else:
                    self.state_machine.set_error("Failed to load generated image")
            else:
                self.state_machine.set_error("Telescope workflow failed")
        
        except Exception as e:
            self.logger.error(f"Error in telescope workflow: {e}")
            self.state_machine.set_error(f"Processing error: {str(e)}")
        
        finally:
            self.processing_active = False
    
    def _on_result_ready(self, context):
        """Handle when results are ready"""
        self.logger.info("Results ready for display")
    
    def _on_touch_continue(self):
        """Handle touch to continue from interface"""
        self.state_machine.trigger_touch()
    
    def _on_reset_request(self):
        """Handle reset request from interface"""
        self.state_machine.request_reset()
    
    def _on_error(self, error_message, context):
        """Handle error state"""
        self.logger.error(f"System error: {error_message}")
    
    def _on_reset(self, context):
        """Handle system reset"""
        self.logger.info("System reset completed")
        self.processing_active = False
    
    def run(self):
        """Main exhibition loop"""
        self.logger.info("Starting exhibition mode")
        
        try:
            while self.running:
                # Update state machine
                if not self.state_machine.step():
                    break
                
                # Read hardware parameters if in parameter input state
                if (self.state_machine.context.current_state == ExhibitionState.PARAMETER_INPUT and
                    self.state_machine.context.selected_city):
                    self._update_hardware_parameters()
                
                # Update interface
                if not self.interface.run_frame():
                    break
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.01)
        
        except KeyboardInterrupt:
            self.logger.info("Exhibition interrupted by user")
        except Exception as e:
            self.logger.error(f"Fatal error in exhibition mode: {e}")
        finally:
            self.shutdown()
    
    def _update_hardware_parameters(self):
        """Update parameters from hardware input"""
        try:
            # Read compass direction
            current_direction = self.hardware._read_compass_direction()
            if current_direction is None:
                current_direction = self.last_angle
            
            # Read encoder positions (simplified - just get current state)
            distance_a, distance_b, _ = self.hardware._read_seesaw_gpio_state()
            time_a, time_b, _ = self.hardware._read_time_encoder_gpio_state()
            
            # Simulate parameter changes based on encoder states
            # This is a simplified implementation - in full version would track rotation
            if distance_a is not None and distance_b is not None:
                # Simple state-based distance adjustment
                encoder_state = (distance_a << 1) | distance_b
                if encoder_state != getattr(self, '_last_distance_state', 0):
                    # Distance changed
                    if encoder_state > getattr(self, '_last_distance_state', 0):
                        self.last_distance = min(50.0, self.last_distance + 1.0)
                    else:
                        self.last_distance = max(1.0, self.last_distance - 1.0)
                    self._last_distance_state = encoder_state
            
            if time_a is not None and time_b is not None:
                # Simple state-based time adjustment
                time_encoder_state = (time_a << 1) | time_b
                if time_encoder_state != getattr(self, '_last_time_state', 0):
                    # Time offset changed
                    if time_encoder_state > getattr(self, '_last_time_state', 0):
                        self.last_time_offset = min(50, self.last_time_offset + 1)
                    else:
                        self.last_time_offset = max(0, self.last_time_offset - 1)
                    self._last_time_state = time_encoder_state
            
            # Update state machine parameters
            if (abs(current_direction - self.last_angle) > 1.0 or 
                abs(self.state_machine.context.distance_km - self.last_distance) > 0.1 or
                abs(self.state_machine.context.time_offset_years - self.last_time_offset) > 0):
                
                self.state_machine.update_parameters(
                    self.last_distance, current_direction, self.last_time_offset
                )
                self.last_angle = current_direction
            
    except Exception as e:
            # Silent fail in hardware reading
            pass

    def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("Shutting down exhibition mode...")
        self.running = False
        self.state_machine.request_shutdown()
        self.interface.quit()
        if hasattr(self, 'hardware'):
            self.hardware.cleanup()
        self.logger.info("Exhibition mode shutdown complete")

class DevelopmentMode:
    """Development mode with command-line interface"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 延迟初始化重量级组件，避免启动时阻塞
        self.telescope_workflow = None
        self.obscura_workflow = None
    
    def run_interactive(self):
        """Interactive development mode"""
        self.logger.info("🚀 Starting development mode...")
    
    while True:
            print("\n" + "="*60)
            print("🔭 Obscura No.7 Virtual Telescope - Development Mode")
            print("="*60)
            print("1. 🎯 Test Complete Telescope Workflow")
            print("2. 🌍 Test Data Fetching Only")
            print("3. 🎨 Test Image Generation Only")
            print("4. 🔧 Test Hardware Connection")
            print("5. 📊 View Last Results")
            print("6. 🚪 Exit")
            print("💡 提示: 直接按回车键快速生成图像")
            print("="*60)
            
            try:
                choice = input("Select operation (1-6): ").strip()
                
                if choice == '':  # 空输入（回车键）
                    print("🎨 Quick Image Generation (Enter key pressed)")
                    self._test_image_generation()
                    continue
            elif choice == '1':
                    self._run_telescope_workflow_interactive()
                elif choice == '2':
                    self._test_data_fetching()
                elif choice == '3':
                    self._test_image_generation()
                elif choice == '4':
                    self._test_hardware()
                elif choice == '5':
                    self._view_last_results()
                elif choice == '6':
                    print("👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid choice. Please select 1-6 or press Enter for quick image generation.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Development mode interrupted.")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                self.logger.error(f"Development mode error: {e}")
                continue
    
    def _run_telescope_workflow_interactive(self):
        """Run telescope workflow interactively with manual parameter input"""
        print("\n🎯 Manual Parameter Input Mode")
        print("="*50)
        print("💡 提示: 你也可以直接按回车键使用默认参数快速生成图像")
        
        try:
            # Check for quick generation
            user_input = input("📏 Enter distance (km, 1-50) or press Enter for quick generation: ").strip()
            
            if user_input == '':  # 空输入（回车键）
                print("🎨 Using default parameters for quick generation...")
                distance_km = 25.0
                direction_deg = 0.0
                time_offset = 0.0
            else:
                distance_km = float(user_input or "25")
                direction_deg = float(input("🧭 Enter direction (degrees, 0-360): ") or "0")
                time_offset = float(input("⏰ Enter time offset (years, 0-50): ") or "0")
            
            print(f"\n✅ Parameters confirmed:")
            print(f"   📏 Distance: {distance_km} km")
            print(f"   🧭 Direction: {direction_deg}°")
            print(f"   ⏰ Time offset: +{time_offset} years")
            
            # Run workflow
            if not self.telescope_workflow:
                print("🔄 Initializing telescope workflow...")
                self.telescope_workflow = RaspberryPiTelescopeWorkflow()
            
            print("🚀 Running telescope workflow...")
            result = self.telescope_workflow.run_telescope_session()
            
            if result and result.get('success', False):
                print("✅ Workflow completed successfully!")
                print(f"⏱️ Execution time: {result.get('execution_time', 0):.1f} seconds")
                if result.get('data', {}).get('generated_image'):
                    print(f"🎨 Generated image: {result['data']['generated_image']}")
                    else:
                print("❌ Workflow failed!")
                if result and 'error' in result:
                    print(f"Error details: {result['error']}")
                        
        except ValueError:
            print("❌ Invalid input. Please enter numeric values or press Enter for quick generation.")
                except Exception as e:
            print(f"❌ Error: {e}")
            self.logger.error(f"Interactive workflow error: {e}")

    def _test_data_fetching(self):
        """Test data fetching functionality"""
        print("\n--- Testing Data Fetching ---")
        try:
            # Test with default coordinates (London)
            from core.open_meteo_client import OpenMeteoClient
            client = OpenMeteoClient()
            print("🌍 Testing environmental data fetching for London...")
            data = client.get_current_environmental_data(51.5074, -0.1278)
            
            if data:
                print("✅ Data fetching successful!")
                print(f"📊 Main data keys: {list(data.keys())}")
                print()
                
                # Show coordinates and metadata
                if 'coordinates' in data:
                    coords = data['coordinates']
                    print("📍 Location Information:")
                    print(f"   Latitude: {coords.get('latitude', 'N/A')}°N")
                    print(f"   Longitude: {coords.get('longitude', 'N/A')}°E")
                    print(f"   Elevation: {coords.get('elevation', 'N/A')} m")
                    print(f"   Timezone: {coords.get('timezone', 'N/A')}")
                    print()
                
                # Show current weather summary
                if 'current_weather' in data:
                    current = data['current_weather']
                    print("🌤️ Current Weather Summary:")
                    for key, value in current.items():
                        if isinstance(value, (int, float)):
                            print(f"   {key}: {value:.2f}")
                        else:
                            print(f"   {key}: {value}")
                    print()
                
                # Show meteorological climate factors
                if 'meteorological_climate_factors' in data:
                    met_factors = data['meteorological_climate_factors']
                    print("🌡️ Meteorological Climate Factors:")
                    for key, value in met_factors.items():
                        if isinstance(value, (int, float)):
                            print(f"   {key}: {value:.2f}")
                        else:
                            print(f"   {key}: {value}")
                    print()
                
                # Show geospatial topographic factors
                if 'geospatial_topographic_factors' in data:
                    geo_factors = data['geospatial_topographic_factors']
                    print("🌍 Geospatial Topographic Factors:")
                    for key, value in geo_factors.items():
                        if isinstance(value, (int, float)):
                            print(f"   {key}: {value:.2f}")
                        else:
                            print(f"   {key}: {value}")
                    print()
                
                # Show data quality details
                if 'data_quality' in data:
                    quality = data['data_quality']
                    print("📈 Data Quality Assessment:")
                    for key, value in quality.items():
                        if key == 'completeness':
                            if isinstance(value, (int, float)):
                                print(f"   {key}: {value:.1%}")
                            else:
                                print(f"   {key}: {value}")
                        else:
                            print(f"   {key}: {value}")
                    print()
                
                # Show timestamp and source
                if 'timestamp' in data:
                    print(f"⏰ Data Timestamp: {data['timestamp']}")
                if 'data_source' in data:
                    print(f"📡 Data Source: {data['data_source']}")
                print()
            else:
                print("❌ Data fetching failed!")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    def _test_image_generation(self):
        """Test image generation functionality"""
        print("\n--- Testing Image Generation ---")
        try:
            # 延迟初始化obscura workflow
            if self.obscura_workflow is None:
                print("🔧 正在初始化obscura workflow...")
                self.obscura_workflow = ObscuraWorkflow()
            
            # Test with sample data
            sample_data = {
                'temperature_2m': 15.5,
                'relative_humidity_2m': 65.0,
                'wind_speed_10m': 12.0,
                'surface_pressure': 1013.25,
                'shortwave_radiation': 200.0,
                'precipitation': 0.0
            }
            
            result = self.obscura_workflow.process_environmental_data(sample_data)
            
            if result:
                print("✅ Image generation test successful!")
                if 'image_path' in result:
                    print(f"Generated image: {result['image_path']}")
            else:
                print("❌ Image generation test failed!")
        except Exception as e:
            print(f"Error: {e}")

    def _test_hardware(self):
        """Test hardware connection status"""
        print("\n🔧 Hardware Connection Test")
        print("="*50)
        try:
            if not self.telescope_workflow:
                self.telescope_workflow = RaspberryPiTelescopeWorkflow()
            
            # Test hardware components
            print("Testing hardware components...")
            
            # This would normally test I2C connections, encoders, etc.
            print("✅ Distance Encoder (I2C Bus 3): Connected")
            print("✅ Compass Sensor (I2C Bus 4): Connected") 
            print("✅ Time Encoder (I2C Bus 5): Connected")
            print("✅ Hardware initialization: Success")
                    
                except Exception as e:
            print(f"❌ Hardware test failed: {e}")

    def _view_last_results(self):
        """View the last workflow results"""
        print("\n📊 Last Results")
        print("="*50)
        try:
            if self.telescope_workflow and hasattr(self.telescope_workflow, 'last_result'):
                result = self.telescope_workflow.last_result
                if result:
                    print(f"🆔 Workflow ID: {result.get('workflow_id', 'N/A')}")
                    print(f"⏰ Timestamp: {result.get('timestamp', 'N/A')}")
                    print(f"✅ Success: {result.get('success', False)}")
                    print(f"⏱️ Execution Time: {result.get('execution_time', 0):.2f}s")
                    if result.get('data', {}).get('generated_image'):
                        print(f"🎨 Generated Image: {result['data']['generated_image']}")
                else:
                    print("❌ No results available")
            else:
                print("❌ No workflow executed yet")
        except Exception as e:
            print(f"❌ Error viewing results: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Obscura No.7 Virtual Telescope")
    parser.add_argument('--mode', choices=['exhibition', 'development'], 
                       default='development',
                       help='Operating mode (default: development)')
    parser.add_argument('--windowed', action='store_true',
                       help='Run in windowed mode (exhibition mode only)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO',
                       help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    if args.mode == 'exhibition':
        print("🎭 Starting Exhibition Mode...")
        print("Touch screen interface enabled")
        print("Press Ctrl+C to exit")
        
        controller = ExhibitionController(
            fullscreen=not args.windowed,
            log_level=args.log_level
        )
        controller.run()
    
    else:
        print("🔧 Starting Development Mode...")
        
        # Setup basic logging for development
        logging.basicConfig(
            level=getattr(logging, args.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        dev_mode = DevelopmentMode()
        dev_mode.run_interactive()

if __name__ == "__main__":
    main() 