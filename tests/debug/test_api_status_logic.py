#!/usr/bin/env python3
"""
Test API Status Logic - Debug the exact status determination behavior
"""

import sys
import json
from pathlib import Path

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

def test_api_status_logic():
    """Test the exact API status determination logic"""
    
    print("🧪 Testing API Status Determination Logic...")
    
    # Test cases based on real responses
    test_cases = [
        {
            'name': 'Header Response (should be SUCCESS)',
            'response': {"success": True, "records_processed": 1, "monday_ids": [9702050042], "operation_type": "create_item"},
            'expected': 'SUCCESS'
        },
        {
            'name': 'Line Response (should be SUCCESS)', 
            'response': {"data": {"create_subitem_0": {"id": "9702050104", "name": "Size L"}}},
            'expected': 'SUCCESS'
        },
        {
            'name': 'Failed Header Response (should be ERROR)',
            'response': {"success": False, "error": "Failed to create item"},
            'expected': 'ERROR'
        },
        {
            'name': 'GraphQL Error Response (should be ERROR)',
            'response': {"errors": [{"message": "Item not found"}]},
            'expected': 'ERROR'
        },
        {
            'name': 'Empty Data Response (should be ERROR)',
            'response': {"data": None},
            'expected': 'ERROR'
        }
    ]
    
    print(f"\n📋 Testing {len(test_cases)} cases:\n")
    
    for i, case in enumerate(test_cases, 1):
        response_data = case['response']
        expected = case['expected']
        
        # Apply the exact same logic from sync_engine.py
        api_status = 'SUCCESS'
        
        # Check for explicit success field (single operations)
        if 'success' in response_data and response_data.get('success') is False:
            api_status = 'ERROR'
        # Check for errors field (GraphQL responses)
        elif 'errors' in response_data:
            api_status = 'ERROR'
        # Check for explicit error field (custom error responses)
        elif 'error' in response_data:
            api_status = 'ERROR'
        # Check for successful GraphQL data responses (batch operations)
        elif 'data' in response_data:
            # For GraphQL responses with data, consider successful unless data is empty/null
            if response_data['data'] is None or not response_data['data']:
                api_status = 'ERROR'
            # else: api_status remains 'SUCCESS'
        
        # Check result
        status_icon = "✅" if api_status == expected else "❌"
        print(f"{status_icon} Test {i}: {case['name']}")
        print(f"   Response: {json.dumps(response_data)}")
        print(f"   Expected: {expected}, Got: {api_status}")
        
        if api_status != expected:
            print(f"   🚨 MISMATCH! Expected {expected} but got {api_status}")
            
            # Debug the logic step by step
            print(f"   🔍 Debug Steps:")
            print(f"      'success' in response_data: {'success' in response_data}")
            if 'success' in response_data:
                print(f"      response_data.get('success'): {response_data.get('success')}")
                print(f"      response_data.get('success') is False: {response_data.get('success') is False}")
            print(f"      'errors' in response_data: {'errors' in response_data}")
            print(f"      'error' in response_data: {'error' in response_data}")
            print(f"      'data' in response_data: {'data' in response_data}")
            
        print()

if __name__ == "__main__":
    test_api_status_logic()
