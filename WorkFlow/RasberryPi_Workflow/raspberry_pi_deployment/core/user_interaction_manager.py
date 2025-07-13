"""
User Interaction Manager for Obscura No.7 Virtual Telescope
Handles hardware inputs, touch screen events, and timeout management.

Features:
- Hardware encoder input processing (distance and angle)
- Touch screen event handling
- Button debouncing
- Timeout-based auto-reset
- Input validation and smoothing
"""

import time
import logging
import threading
from typing import Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass
from collections import deque
import math

# Hardware interface imports (graceful fallback for non-RPi environments)
try:
    import gpiozero
    from gpiozero import RotaryEncoder, Button as GPIOButton, LED
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logging.warning("GPIO libraries not available - hardware input disabled")

@dataclass
class InteractionSettings:
    """Configuration settings for user interaction"""
    # Hardware settings
    distance_encoder_pin_a: int = 17
    distance_encoder_pin_b: int = 18
    angle_encoder_pin_a: int = 22
    angle_encoder_pin_b: int = 23
    fetch_button_pin: int = 24
    reset_button_pin: int = 25
    status_led_pin: int = 26
    
    # Interaction settings
    encoder_steps_per_unit: float = 4.0  # Steps per km/degree
    debounce_time: float = 0.2  # Button debounce time in seconds
    input_timeout: float = 30.0  # Seconds before auto-confirming parameters
    auto_reset_timeout: float = 300.0  # Seconds before auto-reset
    
    # Value ranges
    distance_min: float = 1.0
    distance_max: float = 50.0
    distance_default: float = 25.0
    angle_min: float = 0.0
    angle_max: float = 360.0
    angle_default: float = 0.0
    time_offset_min: int = -50
    time_offset_max: int = 50
    time_offset_default: int = 0
    
    # Input smoothing
    encoder_smoothing_samples: int = 3
    touch_sensitivity: float = 10.0  # Minimum distance for touch detection

class InputState:
    """Tracks current input state and changes"""
    
    def __init__(self):
        self.distance_km: float = 25.0
        self.angle_degrees: float = 0.0
        self.time_offset_years: int = 0
        
        # Change tracking
        self.distance_changed: bool = False
        self.angle_changed: bool = False
        self.time_offset_changed: bool = False
        
        # Button states
        self.fetch_button_pressed: bool = False
        self.reset_button_pressed: bool = False
        
        # Touch events
        self.touch_detected: bool = False
        self.touch_position: Optional[Tuple[float, float]] = None
        
        # Timestamps
        self.last_input_time: float = time.time()
        self.last_change_time: float = time.time()
        
        # Threading lock
        self.lock = threading.Lock()
    
    def update_parameter(self, param_name: str, value: float):
        """Update a parameter and mark it as changed"""
        with self.lock:
            if param_name == 'distance':
                if abs(self.distance_km - value) > 0.1:  # Minimum change threshold
                    self.distance_km = value
                    self.distance_changed = True
                    self.last_change_time = time.time()
            elif param_name == 'angle':
                if abs(self.angle_degrees - value) > 1.0:  # Minimum change threshold
                    self.angle_degrees = value
                    self.angle_changed = True
                    self.last_change_time = time.time()
            elif param_name == 'time_offset':
                if abs(self.time_offset_years - value) > 0.5:  # Minimum change threshold
                    self.time_offset_years = int(value)
                    self.time_offset_changed = True
                    self.last_change_time = time.time()
            
            self.last_input_time = time.time()
    
    def get_changes(self) -> Dict[str, bool]:
        """Get dictionary of parameter changes and reset flags"""
        with self.lock:
            changes = {
                'distance': self.distance_changed,
                'angle': self.angle_changed,
                'time_offset': self.time_offset_changed
            }
            # Reset change flags
            self.distance_changed = False
            self.angle_changed = False
            self.time_offset_changed = False
            return changes
    
    def get_current_values(self) -> Dict[str, float]:
        """Get current parameter values"""
        with self.lock:
            return {
                'distance_km': self.distance_km,
                'angle_degrees': self.angle_degrees,
                'time_offset_years': self.time_offset_years
            }

class HardwareInputHandler:
    """Handles hardware input from encoders and buttons"""
    
    def __init__(self, settings: InteractionSettings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Hardware components
        self.distance_encoder: Optional[RotaryEncoder] = None
        self.angle_encoder: Optional[RotaryEncoder] = None
        self.fetch_button: Optional[GPIOButton] = None
        self.reset_button: Optional[GPIOButton] = None
        self.status_led: Optional[LED] = None
        
        # Encoder position tracking
        self.distance_encoder_position = 0
        self.angle_encoder_position = 0
        
        # Input smoothing
        self.distance_history = deque(maxlen=settings.encoder_smoothing_samples)
        self.angle_history = deque(maxlen=settings.encoder_smoothing_samples)
        
        # Button debouncing
        self.last_fetch_press = 0
        self.last_reset_press = 0
        
        # Callbacks
        self.on_parameter_change: Optional[Callable] = None
        self.on_fetch_button: Optional[Callable] = None
        self.on_reset_button: Optional[Callable] = None
        
        # Initialize hardware if available
        if GPIO_AVAILABLE:
            self._init_hardware()
        else:
            self.logger.warning("Hardware input disabled - GPIO not available")
    
    def _init_hardware(self):
        """Initialize hardware components"""
        try:
            # Distance encoder
            self.distance_encoder = RotaryEncoder(
                self.settings.distance_encoder_pin_a,
                self.settings.distance_encoder_pin_b
            )
            self.distance_encoder.when_rotated = self._on_distance_encoder_change
            
            # Angle encoder
            self.angle_encoder = RotaryEncoder(
                self.settings.angle_encoder_pin_a,
                self.settings.angle_encoder_pin_b
            )
            self.angle_encoder.when_rotated = self._on_angle_encoder_change
            
            # Buttons
            self.fetch_button = GPIOButton(
                self.settings.fetch_button_pin,
                bounce_time=self.settings.debounce_time
            )
            self.fetch_button.when_pressed = self._on_fetch_button_press
            
            self.reset_button = GPIOButton(
                self.settings.reset_button_pin,
                bounce_time=self.settings.debounce_time
            )
            self.reset_button.when_pressed = self._on_reset_button_press
            
            # Status LED
            self.status_led = LED(self.settings.status_led_pin)
            
            self.logger.info("Hardware input initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize hardware: {e}")
            self.status_led = None
    
    def _on_distance_encoder_change(self):
        """Handle distance encoder rotation"""
        if self.distance_encoder:
            # Get encoder steps
            steps = self.distance_encoder.steps
            delta_steps = steps - self.distance_encoder_position
            self.distance_encoder_position = steps
            
            # Convert to distance change
            delta_distance = delta_steps / self.settings.encoder_steps_per_unit
            
            # Add to smoothing history
            self.distance_history.append(delta_distance)
            
            # Calculate smoothed change
            if len(self.distance_history) >= 2:
                smoothed_delta = sum(self.distance_history) / len(self.distance_history)
                
                if self.on_parameter_change:
                    self.on_parameter_change('distance', smoothed_delta)
    
    def _on_angle_encoder_change(self):
        """Handle angle encoder rotation"""
        if self.angle_encoder:
            # Get encoder steps
            steps = self.angle_encoder.steps
            delta_steps = steps - self.angle_encoder_position
            self.angle_encoder_position = steps
            
            # Convert to angle change
            delta_angle = delta_steps / self.settings.encoder_steps_per_unit
            
            # Add to smoothing history
            self.angle_history.append(delta_angle)
            
            # Calculate smoothed change
            if len(self.angle_history) >= 2:
                smoothed_delta = sum(self.angle_history) / len(self.angle_history)
                
                if self.on_parameter_change:
                    self.on_parameter_change('angle', smoothed_delta)
    
    def _on_fetch_button_press(self):
        """Handle fetch button press with debouncing"""
        current_time = time.time()
        if current_time - self.last_fetch_press > self.settings.debounce_time:
            self.last_fetch_press = current_time
            if self.on_fetch_button:
                self.on_fetch_button()
            self.logger.info("Fetch button pressed")
    
    def _on_reset_button_press(self):
        """Handle reset button press with debouncing"""
        current_time = time.time()
        if current_time - self.last_reset_press > self.settings.debounce_time:
            self.last_reset_press = current_time
            if self.on_reset_button:
                self.on_reset_button()
            self.logger.info("Reset button pressed")
    
    def set_status_led(self, state: bool):
        """Control status LED"""
        if self.status_led:
            if state:
                self.status_led.on()
            else:
                self.status_led.off()
    
    def cleanup(self):
        """Clean up hardware resources"""
        if self.status_led:
            self.status_led.close()
        if self.distance_encoder:
            self.distance_encoder.close()
        if self.angle_encoder:
            self.angle_encoder.close()
        if self.fetch_button:
            self.fetch_button.close()
        if self.reset_button:
            self.reset_button.close()

class TouchScreenHandler:
    """Handles touch screen events and gestures"""
    
    def __init__(self, settings: InteractionSettings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Touch state
        self.last_touch_time = 0
        self.last_touch_position: Optional[Tuple[float, float]] = None
        
        # Callbacks
        self.on_touch: Optional[Callable] = None
        self.on_swipe: Optional[Callable] = None
        self.on_long_press: Optional[Callable] = None
    
    def handle_touch_event(self, x: float, y: float, event_type: str = 'down'):
        """Process touch screen events"""
        current_time = time.time()
        
        if event_type == 'down':
            # Touch down event
            self.last_touch_position = (x, y)
            self.last_touch_time = current_time
            
            if self.on_touch:
                self.on_touch(x, y, 'down')
        
        elif event_type == 'up':
            # Touch up event
            if self.last_touch_position:
                # Calculate distance moved
                dx = x - self.last_touch_position[0]
                dy = y - self.last_touch_position[1]
                distance = math.sqrt(dx*dx + dy*dy)
                
                # Check for gestures
                touch_duration = current_time - self.last_touch_time
                
                if distance < self.settings.touch_sensitivity:
                    # Simple tap
                    if touch_duration > 1.0:  # Long press
                        if self.on_long_press:
                            self.on_long_press(x, y)
                    else:  # Short tap
                        if self.on_touch:
                            self.on_touch(x, y, 'tap')
                else:
                    # Swipe gesture
                    if self.on_swipe:
                        direction = math.atan2(dy, dx)
                        self.on_swipe(distance, direction, touch_duration)
                
                self.last_touch_position = None

class UserInteractionManager:
    """Main manager for all user interactions"""
    
    def __init__(self, settings: Optional[InteractionSettings] = None):
        self.settings = settings or InteractionSettings()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.input_state = InputState()
        self.hardware_handler = HardwareInputHandler(self.settings)
        self.touch_handler = TouchScreenHandler(self.settings)
        
        # Setup callbacks
        self._setup_callbacks()
        
        # External callbacks
        self.callbacks = {
            'on_parameter_change': None,
            'on_fetch_request': None,
            'on_reset_request': None,
            'on_touch_interaction': None,
            'on_timeout': None
        }
        
        # Timeout monitoring
        self.timeout_thread = None
        self.monitoring_active = True
        self._start_timeout_monitoring()
        
        self.logger.info("User interaction manager initialized")
    
    def _setup_callbacks(self):
        """Setup internal callbacks between components"""
        # Hardware callbacks
        self.hardware_handler.on_parameter_change = self._on_hardware_parameter_change
        self.hardware_handler.on_fetch_button = self._on_hardware_fetch_button
        self.hardware_handler.on_reset_button = self._on_hardware_reset_button
        
        # Touch callbacks
        self.touch_handler.on_touch = self._on_touch_event
        self.touch_handler.on_long_press = self._on_long_press
    
    def _on_hardware_parameter_change(self, param_name: str, delta: float):
        """Handle hardware parameter changes"""
        current_values = self.input_state.get_current_values()
        
        if param_name == 'distance':
            new_value = current_values['distance_km'] + delta
            new_value = max(self.settings.distance_min, 
                          min(self.settings.distance_max, new_value))
            self.input_state.update_parameter('distance', new_value)
        
        elif param_name == 'angle':
            new_value = current_values['angle_degrees'] + delta
            new_value = new_value % 360  # Wrap around at 360 degrees
            self.input_state.update_parameter('angle', new_value)
        
        # Notify external callback
        if self.callbacks['on_parameter_change']:
            self.callbacks['on_parameter_change'](
                self.input_state.get_current_values()
            )
    
    def _on_hardware_fetch_button(self):
        """Handle hardware fetch button press"""
        if self.callbacks['on_fetch_request']:
            self.callbacks['on_fetch_request']()
    
    def _on_hardware_reset_button(self):
        """Handle hardware reset button press"""
        self.reset_parameters()
        if self.callbacks['on_reset_request']:
            self.callbacks['on_reset_request']()
    
    def _on_touch_event(self, x: float, y: float, event_type: str):
        """Handle touch screen events"""
        if self.callbacks['on_touch_interaction']:
            self.callbacks['on_touch_interaction'](x, y, event_type)
    
    def _on_long_press(self, x: float, y: float):
        """Handle long press events (potential reset trigger)"""
        self.logger.info(f"Long press detected at ({x}, {y})")
        if self.callbacks['on_reset_request']:
            self.callbacks['on_reset_request']()
    
    def _start_timeout_monitoring(self):
        """Start timeout monitoring thread"""
        def monitor_timeouts():
            while self.monitoring_active:
                current_time = time.time()
                
                # Check for input timeout
                time_since_input = current_time - self.input_state.last_input_time
                if time_since_input > self.settings.input_timeout:
                    if self.callbacks['on_timeout']:
                        self.callbacks['on_timeout']('input_timeout')
                
                # Check for auto-reset timeout
                time_since_change = current_time - self.input_state.last_change_time
                if time_since_change > self.settings.auto_reset_timeout:
                    if self.callbacks['on_timeout']:
                        self.callbacks['on_timeout']('auto_reset')
                
                time.sleep(1.0)  # Check every second
        
        self.timeout_thread = threading.Thread(target=monitor_timeouts, daemon=True)
        self.timeout_thread.start()
    
    def set_callback(self, event: str, callback: Callable):
        """Set callback function for specific events"""
        if event in self.callbacks:
            self.callbacks[event] = callback
        else:
            raise ValueError(f"Unknown callback event: {event}")
    
    def update_parameters(self, distance_km: float, angle_degrees: float, time_offset_years: int):
        """Update parameters programmatically (e.g., from GUI)"""
        self.input_state.update_parameter('distance', distance_km)
        self.input_state.update_parameter('angle', angle_degrees)
        self.input_state.update_parameter('time_offset', time_offset_years)
    
    def get_current_parameters(self) -> Dict[str, float]:
        """Get current parameter values"""
        return self.input_state.get_current_values()
    
    def reset_parameters(self):
        """Reset all parameters to default values"""
        self.input_state.update_parameter('distance', self.settings.distance_default)
        self.input_state.update_parameter('angle', self.settings.angle_default)
        self.input_state.update_parameter('time_offset', self.settings.time_offset_default)
        
        self.logger.info("Parameters reset to defaults")
    
    def handle_pygame_event(self, pygame_event):
        """Handle pygame events (for touch screen integration)"""
        if pygame_event.type == pygame.MOUSEBUTTONDOWN:
            self.touch_handler.handle_touch_event(
                pygame_event.pos[0], pygame_event.pos[1], 'down'
            )
        elif pygame_event.type == pygame.MOUSEBUTTONUP:
            self.touch_handler.handle_touch_event(
                pygame_event.pos[0], pygame_event.pos[1], 'up'
            )
    
    def set_status_indicator(self, status: str):
        """Set status indicator (LED state)"""
        if status == 'ready':
            self.hardware_handler.set_status_led(True)
        elif status == 'processing':
            # Could implement blinking here
            self.hardware_handler.set_status_led(True)
        elif status == 'error':
            # Could implement fast blinking here
            self.hardware_handler.set_status_led(False)
        else:
            self.hardware_handler.set_status_led(False)
    
    def cleanup(self):
        """Clean up resources"""
        self.monitoring_active = False
        if self.timeout_thread:
            self.timeout_thread.join(timeout=2.0)
        
        self.hardware_handler.cleanup()
        self.logger.info("User interaction manager cleaned up")

# Example usage and testing
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create interaction manager
    interaction_manager = UserInteractionManager()
    
    # Example callback functions
    def on_parameter_change(values):
        print(f"Parameters changed: {values}")
    
    def on_fetch_request():
        print("Fetch data requested!")
    
    def on_reset_request():
        print("Reset requested!")
    
    def on_touch_interaction(x, y, event_type):
        print(f"Touch {event_type} at ({x}, {y})")
    
    def on_timeout(timeout_type):
        print(f"Timeout: {timeout_type}")
    
    # Set callbacks
    interaction_manager.set_callback('on_parameter_change', on_parameter_change)
    interaction_manager.set_callback('on_fetch_request', on_fetch_request)
    interaction_manager.set_callback('on_reset_request', on_reset_request)
    interaction_manager.set_callback('on_touch_interaction', on_touch_interaction)
    interaction_manager.set_callback('on_timeout', on_timeout)
    
    # Test parameter updates
    interaction_manager.update_parameters(30.0, 45.0, -5)
    
    print("User interaction manager test running...")
    print("Press Ctrl+C to exit")
    
    try:
        # Keep running to test hardware inputs
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        interaction_manager.cleanup() 