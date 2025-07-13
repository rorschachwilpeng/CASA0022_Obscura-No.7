"""
Exhibition State Machine for Obscura No.7 Virtual Telescope
Manages the continuous loop workflow for gallery exhibition mode.

State Flow:
🎮 Parameter Input → ⚡ Data Fetching Confirmation → 🔄 Processing → 
🖼️ Result Display → 👆 Waiting for Interaction → 🔄 Reset
"""

import time
import logging
from enum import Enum
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

class ExhibitionState(Enum):
    """Exhibition states for the virtual telescope workflow"""
    CITY_SELECTION = "city_selection"
    PARAMETER_INPUT = "parameter_input"
    DATA_FETCH_CONFIRMATION = "data_fetch_confirmation"
    PROCESSING = "processing"
    RESULT_DISPLAY = "result_display"
    WAITING_INTERACTION = "waiting_interaction"
    RESET = "reset"
    ERROR = "error"
    SHUTDOWN = "shutdown"

@dataclass
class StateContext:
    """Context data shared between states"""
    # City selection
    selected_city: str = ""
    city_coordinates: Dict[str, float] = field(default_factory=dict)
    
    # User input parameters
    distance_km: float = 25.0
    angle_degrees: float = 0.0
    time_offset_years: int = 0
    
    # Processing results
    environmental_data: Optional[Dict[str, Any]] = None
    shap_prediction: Optional[Dict[str, Any]] = None
    generated_image_path: Optional[str] = None
    
    # State management
    current_state: ExhibitionState = ExhibitionState.CITY_SELECTION
    previous_state: Optional[ExhibitionState] = None
    state_start_time: float = field(default_factory=time.time)
    error_message: str = ""
    
    # Interaction flags
    user_confirmed: bool = False
    touch_detected: bool = False
    reset_requested: bool = False
    shutdown_requested: bool = False
    
    # Configuration
    auto_reset_timeout: float = 300.0  # 5 minutes
    processing_timeout: float = 180.0  # 3 minutes

class ExhibitionStateMachine:
    """
    State machine for managing the exhibition workflow.
    Handles state transitions and executes state-specific logic.
    """
    
    def __init__(self):
        self.context = StateContext()
        
        # Available cities with fixed coordinates
        self.cities = {
            "London": {"latitude": 51.5074, "longitude": -0.1278, "timezone": "Europe/London"},
            "Edinburgh": {"latitude": 55.9533, "longitude": -3.1883, "timezone": "Europe/London"},
            "Manchester": {"latitude": 53.4808, "longitude": -2.2426, "timezone": "Europe/London"}
        }
        
        self.state_handlers: Dict[ExhibitionState, Callable] = {
            ExhibitionState.CITY_SELECTION: self._handle_city_selection,
            ExhibitionState.PARAMETER_INPUT: self._handle_parameter_input,
            ExhibitionState.DATA_FETCH_CONFIRMATION: self._handle_data_fetch_confirmation,
            ExhibitionState.PROCESSING: self._handle_processing,
            ExhibitionState.RESULT_DISPLAY: self._handle_result_display,
            ExhibitionState.WAITING_INTERACTION: self._handle_waiting_interaction,
            ExhibitionState.RESET: self._handle_reset,
            ExhibitionState.ERROR: self._handle_error,
            ExhibitionState.SHUTDOWN: self._handle_shutdown
        }
        
        # Callbacks for external integrations
        self.callbacks = {
            'on_state_change': None,
            'on_city_selected': None,
            'on_parameter_update': None,
            'on_data_fetch_trigger': None,
            'on_processing_start': None,
            'on_result_ready': None,
            'on_error': None,
            'on_reset': None
        }
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Exhibition State Machine initialized")
    
    def set_callback(self, event: str, callback: Callable):
        """Set callback function for specific events"""
        if event in self.callbacks:
            self.callbacks[event] = callback
        else:
            raise ValueError(f"Unknown callback event: {event}")
    
    def transition_to(self, new_state: ExhibitionState, reason: str = ""):
        """Transition to a new state with logging"""
        if new_state == self.context.current_state:
            return
        
        old_state = self.context.current_state
        self.context.previous_state = old_state
        self.context.current_state = new_state
        self.context.state_start_time = time.time()
        
        self.logger.info(f"State transition: {old_state.value} → {new_state.value}")
        if reason:
            self.logger.info(f"Transition reason: {reason}")
        
        # Trigger callback
        if self.callbacks['on_state_change']:
            self.callbacks['on_state_change'](old_state, new_state, self.context)
    
    def update_parameters(self, distance_km: float, angle_degrees: float, time_offset_years: int):
        """Update user input parameters"""
        self.context.distance_km = max(1.0, min(50.0, distance_km))
        self.context.angle_degrees = angle_degrees % 360
        self.context.time_offset_years = max(-50, min(50, time_offset_years))
        
        self.logger.info(f"Parameters updated: distance={self.context.distance_km}km, "
                        f"angle={self.context.angle_degrees}°, offset={self.context.time_offset_years}y")
        
        if self.callbacks['on_parameter_update']:
            self.callbacks['on_parameter_update'](self.context)
    
    def trigger_data_fetch(self):
        """User confirmed data fetching"""
        if self.context.current_state == ExhibitionState.DATA_FETCH_CONFIRMATION:
            self.context.user_confirmed = True
            self.logger.info("Data fetch confirmed by user")
    
    def select_city(self, city_name: str):
        """User selected a city"""
        if city_name in self.cities:
            self.context.selected_city = city_name
            self.context.city_coordinates = self.cities[city_name].copy()
            self.logger.info(f"City selected: {city_name}")
            
            if self.callbacks['on_city_selected']:
                self.callbacks['on_city_selected'](city_name, self.context.city_coordinates)
            
            # Transition to parameter input after city selection
            if self.context.current_state == ExhibitionState.CITY_SELECTION:
                self.transition_to(ExhibitionState.PARAMETER_INPUT, f"City {city_name} selected")
        else:
            self.logger.warning(f"Unknown city: {city_name}")

    def trigger_touch(self):
        """User touched the screen"""
        self.context.touch_detected = True
        self.logger.info("Touch interaction detected")
    
    def request_reset(self):
        """Request system reset"""
        self.context.reset_requested = True
        self.logger.info("Reset requested")
    
    def request_shutdown(self):
        """Request system shutdown"""
        self.context.shutdown_requested = True
        self.logger.info("Shutdown requested")
    
    def set_processing_result(self, environmental_data: Dict[str, Any], 
                            shap_prediction: Dict[str, Any], 
                            image_path: str):
        """Set the results from processing workflow"""
        self.context.environmental_data = environmental_data
        self.context.shap_prediction = shap_prediction
        self.context.generated_image_path = image_path
        self.logger.info(f"Processing results set: image={image_path}")
    
    def set_error(self, error_message: str):
        """Set error state with message"""
        self.context.error_message = error_message
        self.transition_to(ExhibitionState.ERROR, f"Error: {error_message}")
    
    def step(self) -> bool:
        """
        Execute one step of the state machine.
        Returns False if shutdown is requested.
        """
        # Check for global shutdown request
        if self.context.shutdown_requested:
            self.transition_to(ExhibitionState.SHUTDOWN)
            return False
        
        # Check for global reset request
        if self.context.reset_requested and self.context.current_state != ExhibitionState.RESET:
            self.transition_to(ExhibitionState.RESET)
        
        # Execute current state handler
        try:
            current_handler = self.state_handlers.get(self.context.current_state)
            if current_handler:
                current_handler()
            else:
                self.logger.error(f"No handler for state: {self.context.current_state}")
                self.set_error(f"Invalid state: {self.context.current_state}")
        
        except Exception as e:
            self.logger.error(f"Error in state {self.context.current_state}: {e}")
            self.set_error(str(e))
        
        return self.context.current_state != ExhibitionState.SHUTDOWN
    
    def _handle_city_selection(self):
        """Handle city selection state"""
        # In this state, the system waits for user to select a city
        # This is handled by the GUI interface calling select_city()
        pass
    
    def _handle_parameter_input(self):
        """Handle parameter input state"""
        # In this state, the system waits for parameter updates and confirmation
        # This is typically handled by the GUI interface
        pass
    
    def _handle_data_fetch_confirmation(self):
        """Handle data fetch confirmation state"""
        # Wait for user to confirm data fetching
        if self.context.user_confirmed:
            self.context.user_confirmed = False
            self.transition_to(ExhibitionState.PROCESSING, "User confirmed data fetch")
            
            if self.callbacks['on_data_fetch_trigger']:
                self.callbacks['on_data_fetch_trigger'](self.context)
        
        # Check timeout
        if time.time() - self.context.state_start_time > 60.0:  # 1 minute timeout
            self.transition_to(ExhibitionState.PARAMETER_INPUT, "Confirmation timeout")
    
    def _handle_processing(self):
        """Handle processing state"""
        # Check if processing is complete (results are set)
        if (self.context.environmental_data is not None and 
            self.context.shap_prediction is not None and 
            self.context.generated_image_path is not None):
            
            self.transition_to(ExhibitionState.RESULT_DISPLAY, "Processing completed")
            
            if self.callbacks['on_result_ready']:
                self.callbacks['on_result_ready'](self.context)
        
        # Check timeout
        elif time.time() - self.context.state_start_time > self.context.processing_timeout:
            self.set_error("Processing timeout")
    
    def _handle_result_display(self):
        """Handle result display state"""
        # Auto-transition to waiting for interaction after 5 seconds
        if time.time() - self.context.state_start_time > 5.0:
            self.transition_to(ExhibitionState.WAITING_INTERACTION, "Display timeout")
    
    def _handle_waiting_interaction(self):
        """Handle waiting for interaction state"""
        # Check for touch interaction
        if self.context.touch_detected:
            self.context.touch_detected = False
            self.transition_to(ExhibitionState.RESET, "User touch detected")
        
        # Auto-reset after timeout
        elif time.time() - self.context.state_start_time > self.context.auto_reset_timeout:
            self.transition_to(ExhibitionState.RESET, "Auto-reset timeout")
    
    def _handle_reset(self):
        """Handle reset state"""
        # Clear all context data except configuration
        self.context.selected_city = ""
        self.context.city_coordinates = {}
        self.context.environmental_data = None
        self.context.shap_prediction = None
        self.context.generated_image_path = None
        self.context.error_message = ""
        self.context.user_confirmed = False
        self.context.touch_detected = False
        self.context.reset_requested = False
        
        # Reset to default parameters
        self.context.distance_km = 25.0
        self.context.angle_degrees = 0.0
        self.context.time_offset_years = 0
        
        self.logger.info("System reset completed")
        
        if self.callbacks['on_reset']:
            self.callbacks['on_reset'](self.context)
        
        # Transition back to city selection
        self.transition_to(ExhibitionState.CITY_SELECTION, "Reset completed")
    
    def _handle_error(self):
        """Handle error state"""
        # Log error and wait for manual reset
        if self.callbacks['on_error']:
            self.callbacks['on_error'](self.context.error_message, self.context)
        
        # Auto-reset after 30 seconds in error state
        if time.time() - self.context.state_start_time > 30.0:
            self.transition_to(ExhibitionState.RESET, "Auto-reset from error")
    
    def _handle_shutdown(self):
        """Handle shutdown state"""
        self.logger.info("System shutdown initiated")
        # Cleanup tasks would go here
    
    def get_available_cities(self) -> Dict[str, Dict[str, float]]:
        """Get available cities and their coordinates"""
        return self.cities.copy()

    def get_state_info(self) -> Dict[str, Any]:
        """Get current state information for display"""
        return {
            'current_state': self.context.current_state.value,
            'state_duration': time.time() - self.context.state_start_time,
            'selected_city': self.context.selected_city,
            'city_coordinates': self.context.city_coordinates,
            'parameters': {
                'distance_km': self.context.distance_km,
                'angle_degrees': self.context.angle_degrees,
                'time_offset_years': self.context.time_offset_years
            },
            'has_results': self.context.generated_image_path is not None,
            'error_message': self.context.error_message
        }
    
    def run_continuous(self, step_delay: float = 0.1):
        """
        Run the state machine in continuous mode.
        This is the main loop for exhibition mode.
        """
        self.logger.info("Starting continuous exhibition mode")
        
        try:
            while True:
                if not self.step():
                    break
                time.sleep(step_delay)
        
        except KeyboardInterrupt:
            self.logger.info("Exhibition mode interrupted by user")
        except Exception as e:
            self.logger.error(f"Fatal error in exhibition mode: {e}")
        finally:
            self.logger.info("Exhibition mode ended")

# Example usage and testing
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create state machine
    sm = ExhibitionStateMachine()
    
    # Example callback functions
    def on_state_change(old_state, new_state, context):
        print(f"State changed: {old_state.value} → {new_state.value}")
    
    def on_parameter_update(context):
        print(f"Parameters: {context.distance_km}km, {context.angle_degrees}°, {context.time_offset_years}y")
    
    # Set callbacks
    sm.set_callback('on_state_change', on_state_change)
    sm.set_callback('on_parameter_update', on_parameter_update)
    
    # Test parameter updates
    sm.update_parameters(30.0, 45.0, -5)
    
    # Test state transitions
    sm.transition_to(ExhibitionState.DATA_FETCH_CONFIRMATION)
    sm.trigger_data_fetch()
    
    # Run a few steps
    for i in range(5):
        if not sm.step():
            break
        time.sleep(1)
    
    print("State machine test completed") 