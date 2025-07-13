#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug script to reproduce workflow error
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, parent_dir)

def test_workflow_completion():
    """Test the completion message functionality"""
    print("🧪 Testing workflow completion message...")
    
    # Import after path setup
    from workflows.telescope_workflow import RaspberryPiTelescopeWorkflow
    
    # Create workflow instance
    workflow = RaspberryPiTelescopeWorkflow()
    
    # Test different result scenarios
    test_cases = [
        {
            'name': 'Normal result',
            'result': {
                'workflow_id': 'test_123',
                'timestamp': datetime.now().isoformat(),
                'success': True,
                'execution_time': 53.5,
                'data': {
                    'generated_image': 'test_image.png',
                    'sync_result': {
                        'success': True,
                        'message': 'test'
                    }
                }
            }
        },
        {
            'name': 'Result with None sync_result',
            'result': {
                'workflow_id': 'test_123',
                'timestamp': datetime.now().isoformat(),
                'success': True,
                'execution_time': 53.5,
                'data': {
                    'generated_image': 'test_image.png',
                    'sync_result': None  # This might cause the error
                }
            }
        },
        {
            'name': 'Result with None data',
            'result': {
                'workflow_id': 'test_123',
                'timestamp': datetime.now().isoformat(),
                'success': True,
                'execution_time': 53.5,
                'data': None  # This might cause the error
            }
        },
        {
            'name': 'None result',
            'result': None  # This might cause the error
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*40}")
        print(f"🧪 Test {i}: {test_case['name']}")
        print(f"{'='*40}")
        
        try:
            workflow._show_completion_message(test_case['result'])
            print(f"✅ Test {i} passed")
        except Exception as e:
            print(f"❌ Test {i} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*40}")
    print("🧪 Testing completed")

if __name__ == "__main__":
    test_workflow_completion() 