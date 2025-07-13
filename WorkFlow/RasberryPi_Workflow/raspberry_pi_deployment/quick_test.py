#!/usr/bin/env python3
"""Quick test to reproduce the workflow error"""

import sys
import os
parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, parent_dir)

from workflows.telescope_workflow import RaspberryPiTelescopeWorkflow

def quick_test():
    """Run a minimal workflow to reproduce error"""
    print("🧪 Running quick workflow test...")
    
    # Create workflow
    workflow = RaspberryPiTelescopeWorkflow()
    
    # Mock the hardware input to speed up test
    original_collect = workflow._collect_hardware_input
    def mock_collect():
        return {
            'distance_km': 5.0,
            'direction_degrees': 90.0,
            'time_offset_years': 0
        }
    workflow._collect_hardware_input = mock_collect
    
    # Mock image generation to speed up test - FIXED: Generate real PNG
    original_generate = workflow._generate_artwork
    def mock_generate(style_prediction, weather_data, location_info):
        # Create a real minimal PNG file instead of fake text
        import tempfile
        import os
        
        # Create minimal valid PNG data (1x1 pixel transparent PNG)
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        
        # Ensure outputs/images directory exists
        output_dir = os.path.join('outputs', 'images')
        os.makedirs(output_dir, exist_ok=True)
        
        # Create file in the proper output directory with descriptive name
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'mock_telescope_art_{timestamp}.png'
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(png_data)
            
        print(f"🎨 Mock: Generated valid PNG file: {filename}")
        return filepath
        
    workflow._generate_artwork = mock_generate
    
    # Run the workflow
    try:
        result = workflow.run_telescope_session()
        print(f"🧪 Test completed with result: {type(result)}")
        return result
    except Exception as e:
        print(f"🧪 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    quick_test() 