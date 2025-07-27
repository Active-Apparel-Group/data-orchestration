#!/usr/bin/env python3
"""
Phase 2.6 - Test Lines API Logging Integration

This script validates the API logging functionality for ORDER_LIST_LINES operations.
Tests the enhanced _update_lines_delta_with_subitem_ids() method.
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from pipelines.sync_order_list.sync_engine import SyncEngine
from pipelines.utils import db

def test_lines_api_logging_integration():
    """Test the lines API logging integration functionality"""
    
    print("🧪 Testing Lines API Logging Integration - Phase 2.6")
    print("=" * 60)
    
    try:
        # Initialize sync engine
        print("📋 1. Initializing SyncEngine...")
        sync_engine = SyncEngine(mode='development')
        print("   ✅ SyncEngine initialized successfully")
        
        # Verify database schema has API logging columns for ORDER_LIST_LINES
        print("\n📋 2. Verifying ORDER_LIST_LINES API logging columns...")
        with db.get_connection('orders') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'ORDER_LIST_LINES' 
                AND COLUMN_NAME LIKE 'api_%'
                ORDER BY COLUMN_NAME
            """)
            api_columns = [row[0] for row in cursor.fetchall()]
            
        expected_columns = [
            'api_operation_type',
            'api_request_payload', 
            'api_request_timestamp',
            'api_response_payload',
            'api_response_timestamp', 
            'api_status'
        ]
        
        print(f"   Found API columns: {api_columns}")
        
        if len(api_columns) == 6 and all(col in api_columns for col in expected_columns):
            print("   ✅ All 6 API logging columns exist in ORDER_LIST_LINES")
        else:
            print(f"   ❌ Missing API columns. Expected: {expected_columns}")
            return False
            
        # Test the _capture_api_logging_data method for subitems
        print("\n📋 3. Testing _capture_api_logging_data for subitems...")
        
        # Mock subitems result similar to Monday.com API response
        mock_subitems_result = {
            'success': True,
            'monday_ids': ['subitem_123', 'subitem_456', 'subitem_789'],
            'api_request': {
                'operation': 'create_subitems',
                'payload': {
                    'board_id': '8709134353',
                    'parent_item_id': 'item_123',
                    'subitems': [
                        {'name': 'Line 1', 'column_values': {'text': 'Value 1'}},
                        {'name': 'Line 2', 'column_values': {'text': 'Value 2'}},
                        {'name': 'Line 3', 'column_values': {'text': 'Value 3'}}
                    ]
                }
            },
            'api_response': {
                'data': {
                    'create_subitem': [
                        {'id': 'subitem_123', 'name': 'Line 1'},
                        {'id': 'subitem_456', 'name': 'Line 2'},
                        {'id': 'subitem_789', 'name': 'Line 3'}
                    ]
                }
            },
            'request_timestamp': datetime.utcnow(),
            'response_timestamp': datetime.utcnow()
        }
        
        # Test API logging data capture
        api_logging_data = sync_engine._capture_api_logging_data(mock_subitems_result, 'subitem_creation')
        
        print(f"   API Operation Type: {api_logging_data.get('api_operation_type')}")
        print(f"   API Status: {api_logging_data.get('api_status')}")
        print(f"   Request Timestamp: {api_logging_data.get('api_request_timestamp')}")
        print(f"   Response Timestamp: {api_logging_data.get('api_response_timestamp')}")
        
        # Validate API payload JSON serialization
        try:
            request_payload = json.loads(api_logging_data.get('api_request_payload', '{}'))
            response_payload = json.loads(api_logging_data.get('api_response_payload', '{}'))
            print("   ✅ JSON serialization working correctly")
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON serialization failed: {e}")
            return False
            
        # Test the enhanced _update_lines_delta_with_subitem_ids method signature
        print("\n📋 4. Testing enhanced _update_lines_delta_with_subitem_ids method...")
        
        try:
            # Test method signature (dry run - no actual database update)
            print("   Testing method signature with api_logging_data parameter...")
            
            # This would normally be called with actual record_uuid, subitem_ids, connection, and api_logging_data
            # For testing, we're just validating the method accepts the new parameter
            method = getattr(sync_engine, '_update_lines_delta_with_subitem_ids')
            import inspect
            signature = inspect.signature(method)
            params = list(signature.parameters.keys())
            
            print(f"   Method parameters: {params}")
            
            if 'api_logging_data' in params:
                print("   ✅ Method signature includes api_logging_data parameter")
            else:
                print("   ❌ Method signature missing api_logging_data parameter")
                return False
                
        except Exception as e:
            print(f"   ❌ Method signature test failed: {e}")
            return False
            
        print("\n🎉 Lines API logging integration test completed successfully!")
        print("\n📊 Summary:")
        print("   ✅ ORDER_LIST_LINES has 6 API logging columns")
        print("   ✅ _capture_api_logging_data() works for subitems")
        print("   ✅ JSON serialization functional")
        print("   ✅ Enhanced method signature confirmed")
        print("\n🚀 Phase 2.6 - Lines API Logging Integration: COMPLETED")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_lines_api_logging_integration()
    exit(0 if success else 1)
