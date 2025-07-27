#!/usr/bin/env python3
"""
Phase 2.6 - Test Lines API Logging Integration (Fixed Imports)
"""

import sys
from pathlib import Path
import json
import inspect
from datetime import datetime

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def main():
    print("🧪 Testing Lines API Logging Integration - Phase 2.6")
    print("=" * 60)
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        try:
            # Test 1: Verify ORDER_LIST_LINES API logging columns
            print("\n📋 1. Verifying ORDER_LIST_LINES API logging columns...")
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
            
            # Test 2: Test SyncEngine import and method signature
            print("\n📋 2. Testing SyncEngine method signature...")
            
            # Import SyncEngine using working pattern
            from src.pipelines.sync_order_list.sync_engine import SyncEngine
            
            # Initialize with config path and environment
            sync_engine = SyncEngine(config_path, config.environment)
            print("   ✅ SyncEngine initialized successfully")
            
            # Check method signature
            method = getattr(sync_engine, '_update_lines_delta_with_subitem_ids')
            signature = inspect.signature(method)
            params = list(signature.parameters.keys())
            
            print(f"   Method parameters: {params}")
            
            if 'api_logging_data' in params:
                print("   ✅ Method signature includes api_logging_data parameter")
            else:
                print("   ❌ Method signature missing api_logging_data parameter")
                return False
            
            # Test 3: Test _capture_api_logging_data method
            print("\n📋 3. Testing _capture_api_logging_data for subitems...")
            
            # Mock request and response data
            mock_request_data = [
                {'name': 'Line 1', 'column_values': {'text': 'Value 1'}},
                {'name': 'Line 2', 'column_values': {'text': 'Value 2'}}
            ]
            
            mock_response_data = {
                'data': {
                    'create_subitem': [
                        {'id': 'subitem_123', 'name': 'Line 1'},
                        {'id': 'subitem_456', 'name': 'Line 2'}
                    ]
                }
            }
            
            # Test API logging data capture with correct signature
            api_logging_data = sync_engine._capture_api_logging_data(
                'subitem_creation', 
                mock_request_data, 
                mock_response_data
            )
            
            print(f"   API Operation Type: {api_logging_data.get('api_operation_type')}")
            print(f"   API Status: {api_logging_data.get('api_status')}")
            
            # Validate JSON serialization
            try:
                request_payload = json.loads(api_logging_data.get('api_request_payload', '{}'))
                response_payload = json.loads(api_logging_data.get('api_response_payload', '{}'))
                print("   ✅ JSON serialization working correctly")
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON serialization failed: {e}")
                return False
            
            print("\n🎉 Lines API logging integration test completed successfully!")
            print("\n📊 Summary:")
            print("   ✅ ORDER_LIST_LINES has 6 API logging columns")
            print("   ✅ SyncEngine method signature enhanced")
            print("   ✅ _capture_api_logging_data() works for subitems")
            print("   ✅ JSON serialization functional")
            print("\n🚀 Phase 2.6 - Lines API Logging Integration: COMPLETED")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            cursor.close()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
