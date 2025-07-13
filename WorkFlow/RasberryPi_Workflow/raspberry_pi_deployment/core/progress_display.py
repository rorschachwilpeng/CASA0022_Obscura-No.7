#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Progress Display Module
Provides elegant progress indication and status updates for telescope workflow
"""

import time
import sys
from datetime import datetime
from enum import Enum

class ProgressStatus(Enum):
    """Progress Status Enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"

class ProgressDisplay:
    def __init__(self):
        """Initialize Progress Display"""
        self.steps = []
        self.current_step = 0
        self.start_time = None
        self.colors = {
            'reset': '\033[0m',
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'purple': '\033[95m',
            'cyan': '\033[96m',
            'white': '\033[97m',
            'bold': '\033[1m',
            'dim': '\033[2m'
        }
        self.emojis = {
            'telescope': '🔭',
            'coordinates': '📍',
            'weather': '🌤️',
            'ai': '🤖',
            'image': '🎨',
            'upload': '☁️',
            'success': '✅',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️',
            'loading': '⏳',
            'rocket': '🚀'
        }
    
    def init_workflow(self, title="Workflow", total_steps=6, workflow_id=""):
        """Initialize workflow display"""
        self.total_steps = total_steps
        self.current_step = 0
        self.start_time = datetime.now()
        self.workflow_id = workflow_id
        
        print(f"{self.emojis['telescope']} {self._colorize(title, 'bold')}")
        print("=" * 60)
        print(f"📅 Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Total steps: {total_steps}")
        if workflow_id:
            print(f"🆔 Workflow ID: {workflow_id}")
        print()
    
    def setup_workflow(self, steps):
        """Setup workflow steps"""
        self.steps = steps
        self.current_step = 0
        self.start_time = datetime.now()
        
        print(f"{self.emojis['telescope']} {self._colorize('Obscura No.7 Virtual Telescope Workflow', 'bold')}")
        print("=" * 60)
        print(f"📅 Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Total steps: {len(steps)}")
        print()
        
        # Display all steps overview
        for i, step in enumerate(steps, 1):
            status_icon = "○"
            color = 'dim'
            print(f"  {status_icon} {self._colorize(f'{i}. {step}', color)}")
        print()
    
    def step(self, step_number, step_name, description=""):
        """Create step context manager"""
        return StepContext(self, step_name, step_number, description)
    
    def start_step(self, step_name, description=""):
        """Start new step"""
        self.current_step += 1
        
        # Update previous step status (if exists)
        if self.current_step > 1:
            self._update_step_status(self.current_step - 1, ProgressStatus.SUCCESS)
        
        total_steps = getattr(self, 'total_steps', len(getattr(self, 'steps', [])))
        print(f"{self.emojis['loading']} {self._colorize(f'Step {self.current_step}/{total_steps}: {step_name}', 'bold')}")
        if description:
            print(f"   {self._colorize(description, 'dim')}")
        
        return StepContext(self, step_name)
    
    def update_step_progress(self, message, status=ProgressStatus.RUNNING):
        """Update current step progress"""
        icon = self._get_status_icon(status)
        color = self._get_status_color(status)
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        print(f"   {icon} [{timestamp}] {self._colorize(message, color)}")
    
    def complete_workflow(self, success=True):
        """Complete workflow"""
        if success and self.current_step > 0:
            self._update_step_status(self.current_step, ProgressStatus.SUCCESS)
        
        end_time = datetime.now()
        duration = end_time - self.start_time if self.start_time else None
        
        print("\n" + "=" * 60)
        if success:
            print(f"{self.emojis['success']} {self._colorize('Workflow completed successfully!', 'green', 'bold')}")
        else:
            print(f"{self.emojis['error']} {self._colorize('Workflow execution failed', 'red', 'bold')}")
        
        print(f"🕐 End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        if duration:
            print(f"⏱️ Total duration: {self._format_duration(duration)}")
        print()
    
    def show_error(self, error_message, details=None):
        """Show error information"""
        print(f"\n{self.emojis['error']} {self._colorize('Error', 'red', 'bold')}")
        print(f"   {self._colorize(error_message, 'red')}")
        if details:
            print(f"   {self._colorize('Details:', 'dim')}")
            for line in str(details).split('\n'):
                if line.strip():
                    print(f"   {self._colorize(f'  {line}', 'dim')}")
        print()
    
    def show_warning(self, warning_message):
        """Show warning information"""
        print(f"{self.emojis['warning']} {self._colorize(f'Warning: {warning_message}', 'yellow')}")
    
    def show_info(self, info_message):
        """Show information"""
        print(f"{self.emojis['info']} {self._colorize(info_message, 'cyan')}")
    
    def show_coordinates(self, lat, lon, distance, direction):
        """Show coordinates information"""
        print(f"{self.emojis['coordinates']} {self._colorize('Target Coordinates Calculation Result:', 'bold')}")
        print(f"   📍 Latitude: {self._colorize(f'{lat:.6f}', 'green')}")
        print(f"   📍 Longitude: {self._colorize(f'{lon:.6f}', 'green')}")
        print(f"   📏 Distance: {self._colorize(f'{distance/1000:.1f} km', 'blue')}")
        print(f"   🧭 Direction: {self._colorize(f'{direction:.1f}°', 'blue')}")
    
    def show_weather_summary(self, weather_data):
        """Show weather data summary"""
        if not weather_data or not weather_data.get('current_weather'):
            self.show_warning("No weather data to display")
            return
        
        current = weather_data['current_weather']
        print(f"{self.emojis['weather']} {self._colorize('Environmental Data Summary:', 'bold')}")
        temp_text = f'{current.get("temperature", "N/A")}°C'
        humidity_text = f'{current.get("humidity", "N/A")}%'
        pressure_text = f'{current.get("pressure", "N/A")} hPa'
        wind_text = f'{current.get("wind_speed", "N/A")} m/s'
        
        print(f"   🌡️ Temperature: {self._colorize(temp_text, 'green')}")
        print(f"   💧 Humidity: {self._colorize(humidity_text, 'blue')}")
        print(f"   📊 Pressure: {self._colorize(pressure_text, 'blue')}")
        print(f"   💨 Wind Speed: {self._colorize(wind_text, 'blue')}")
        print(f"   ☁️ Weather: {self._colorize(current.get('weather_description', 'N/A'), 'cyan')}")
        
        # Air Quality
        if weather_data.get('air_quality'):
            aqi = weather_data['air_quality']
            aqi_color = 'green' if aqi.get('aqi', 3) <= 2 else 'yellow' if aqi.get('aqi', 3) <= 3 else 'red'
            print(f"   🫁 Air Quality: {self._colorize(aqi.get('aqi_description', 'N/A'), aqi_color)}")
    
    def show_ml_prediction(self, prediction_result):
        """Show ML prediction results"""
        print(f"{self.emojis['ai']} {self._colorize('AI Art Prediction Results:', 'bold')}")
        if prediction_result and isinstance(prediction_result, dict):
            print(f"   🎯 Prediction Type: {self._colorize(prediction_result.get('prediction_type', 'N/A'), 'green')}")
            confidence_text = f'{prediction_result.get("confidence", 0)*100:.1f}%'
            print(f"   📊 Confidence: {self._colorize(confidence_text, 'blue')}")
            print(f"   🎨 Style Recommendation: {self._colorize(prediction_result.get('style_recommendation', 'N/A'), 'purple')}")
        else:
            print(f"   {self._colorize('Prediction failed or no results', 'red')}")
    
    def show_progress_bar(self, current, total, prefix="Progress", bar_length=40):
        """Show progress bar"""
        percent = current / total
        filled_length = int(bar_length * percent)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        print(f"\r   {prefix}: |{bar}| {percent*100:.1f}% ({current}/{total})", end='', flush=True)
        
        if current == total:
            print()  # New line
    
    def _colorize(self, text, *colors):
        """Add color to text"""
        color_codes = ''.join(self.colors.get(color, '') for color in colors)
        return f"{color_codes}{text}{self.colors['reset']}"
    
    def _get_status_icon(self, status):
        """Get status icon"""
        icons = {
            ProgressStatus.PENDING: "○",
            ProgressStatus.RUNNING: "●",
            ProgressStatus.SUCCESS: "✓",
            ProgressStatus.ERROR: "✗",
            ProgressStatus.WARNING: "⚠"
        }
        return icons.get(status, "○")
    
    def _get_status_color(self, status):
        """Get status color"""
        colors = {
            ProgressStatus.PENDING: 'dim',
            ProgressStatus.RUNNING: 'blue',
            ProgressStatus.SUCCESS: 'green',
            ProgressStatus.ERROR: 'red',
            ProgressStatus.WARNING: 'yellow'
        }
        return colors.get(status, 'white')
    
    def _update_step_status(self, step_index, status):
        """Update step status (not displayed in overview, internal record only)"""
        pass  # In the simplified version, we don't redraw the entire step list
    
    def _format_duration(self, duration):
        """Format duration"""
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

class StepContext:
    """Step Context Manager"""
    def __init__(self, display, step_name, step_number=None, description=""):
        self.display = display
        self.step_name = step_name
        self.step_number = step_number
        self.description = description
        self.step_start_time = datetime.now()
        
        # Auto start step when entering context
        if step_number:
            self.display.current_step = step_number
            total_steps = getattr(self.display, 'total_steps', 6)
            print(f"{self.display.emojis['loading']} {self.display._colorize(f'Step {step_number}/{total_steps}: {step_name}', 'bold')}")
            if description:
                print(f"   {self.display._colorize(description, 'dim')}")
    
    def update(self, message, status=ProgressStatus.RUNNING):
        """Update step progress"""
        self.display.update_step_progress(message, status)
    
    def success(self, message=""):
        """Mark step as successful"""
        if message:
            self.display.update_step_progress(message, ProgressStatus.SUCCESS)
    
    def error(self, message="", details=None):
        """Mark step as failed"""
        if message:
            self.display.update_step_progress(message, ProgressStatus.ERROR)
        if details:
            self.display.show_error(message, details)
    
    def warning(self, message=""):
        """Show step warning"""
        if message:
            self.display.update_step_progress(message, ProgressStatus.WARNING)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error("Step execution failed", f"{exc_type.__name__}: {exc_val}")
            return False
        return True

if __name__ == "__main__":
    # Test cases
    print("🎨 Progress Display Test")
    print("=" * 40)
    
    # Simulate workflow
    progress = ProgressDisplay()
    
    workflow_steps = [
        "Hardware Data Collection",
        "Coordinate Calculation",
        "Environmental Data Acquisition",
        "AI Art Prediction",
        "Image Generation",
        "Cloud Upload"
    ]
    
    progress.setup_workflow(workflow_steps)
    
    # Simulate step 1
    with progress.start_step("Hardware Data Collection", "Reading data from compass sensor and encoder") as step:
        step.update("Initializing compass sensor...")
        time.sleep(0.5)
        step.update("Reading direction data: 92.5°")
        step.update("Reading distance data: 5.2km")
        step.success("Hardware data collection completed")
    
    time.sleep(0.3)
    
    # Simulate step 2
    with progress.start_step("Coordinate Calculation", "Calculating target coordinates based on distance and direction") as step:
        step.update("Calculating target coordinates...")
        time.sleep(0.3)
        progress.show_coordinates(51.5074, -0.0556, 5200, 92.5)
        step.success("Coordinate calculation completed")
    
    time.sleep(0.3)
    
    # Simulate step 3
    with progress.start_step("Environmental Data Acquisition", "Calling OpenWeather API") as step:
        step.update("Connecting to OpenWeather API...")
        step.update("Getting current weather data...")
        step.update("Getting air quality data...")
        
        # Mock weather data
        mock_weather = {
            'current_weather': {
                'temperature': 15.2,
                'humidity': 65,
                'pressure': 1013,
                'wind_speed': 3.5,
                'weather_description': 'Cloudy'
            },
            'air_quality': {
                'aqi': 2,
                'aqi_description': 'Good'
            }
        }
        progress.show_weather_summary(mock_weather)
        step.success("Environmental data acquisition completed")
    
    time.sleep(0.3)
    
    # Simulate step 4
    with progress.start_step("AI Art Prediction", "Using machine learning model to generate art style") as step:
        step.update("Preparing ML input features...")
        step.update("Calling prediction model...")
        
        # Mock prediction result
        mock_prediction = {
            'prediction_type': 'Impressionist Landscape',
            'confidence': 0.87,
            'style_recommendation': 'Warm tones, soft brushstrokes'
        }
        progress.show_ml_prediction(mock_prediction)
        step.success("AI prediction completed")
    
    time.sleep(0.3)
    
    # Simulate progress bar
    with progress.start_step("Image Generation", "Generating artwork") as step:
        step.update("Starting image generation...")
        for i in range(11):
            progress.show_progress_bar(i, 10, "Generation Progress")
            time.sleep(0.1)
        step.success("Image generation completed")
    
    time.sleep(0.3)
    
    # Complete workflow
    progress.complete_workflow(success=True)
    
    # Test error display
    print("\n" + "="*40)
    print("🚨 Error Handling Test")
    progress.show_error("Network connection failed", "ConnectionError: Failed to establish connection to api.example.com")
    progress.show_warning("API quota approaching")
    progress.show_info("System will retry in 30 seconds")
    
    print("\n✅ Progress display test completed")
