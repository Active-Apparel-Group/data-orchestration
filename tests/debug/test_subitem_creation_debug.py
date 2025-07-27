#!/usr/bin/env python3
"""
🔬 SUBITEM CREATION DEBUG - Detailed Analysis
Test why subitem creation operations are failing with empty response payloads
"""

import sys
from pathlib import Path

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.monday_api_client import MondayAPIClient
import json

logger = logger.get_logger(__name__)

def main():
    print("🔬 Subitem Creation Debug Analysis...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Get one of the failed subitem records to analyze
        failed_query = """
        SELECT TOP 1
            line_uuid,
            monday_subitem_id,
            api_request_payload,
            api_response_payload,
            api_status
        FROM ORDER_LIST_LINES 
        WHERE api_operation_type = 'subitem_creation'
        AND api_status = 'ERROR'
        ORDER BY api_request_timestamp DESC
        """
        
        cursor.execute(failed_query)
        failed_record = cursor.fetchone()
        
        if not failed_record:
            print("❌ No failed subitem creation records found")
            return
            
        print(f"\n📋 Failed Record Analysis:")
        print(f"   Line UUID: {failed_record[0]}")
        print(f"   Monday Subitem ID: {failed_record[1]}")
        print(f"   Status: {failed_record[4]}")
        
        # Parse the request payload to see what was sent
        try:
            request_payload = json.loads(failed_record[2]) if failed_record[2] else []
            print(f"\n📤 Request Payload Analysis:")
            print(f"   Records in payload: {len(request_payload)}")
            
            if request_payload:
                first_record = request_payload[0]
                print(f"   First record keys: {list(first_record.keys())}")
                print(f"   Parent Item ID: {first_record.get('parent_item_id')}")
                print(f"   Size Code: {first_record.get('size_code')}")
                print(f"   Quantity: {first_record.get('qty')}")
                
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse request payload: {e}")
        
        # Now let's test the Monday API client directly
        print(f"\n🧪 Testing Monday API Client...")
        
        # Initialize Monday API client with config path (not config object)
        api_client = MondayAPIClient(config_path)
        
        # Get the parent item that should exist
        parent_item_id = request_payload[0].get('parent_item_id') if request_payload else None
        
        if parent_item_id:
            print(f"🔍 Testing with parent item ID: {parent_item_id}")
            
            # Create a simple test subitem record
            test_record = {
                'parent_item_id': parent_item_id,
                'size_code': 'TEST',
                'qty': 1,
                'action_type': 'INSERT'
            }
            
            try:
                # Test building the GraphQL query
                query_data = api_client._build_graphql_query('create_subitems', [test_record])
                
                print(f"\n📝 GraphQL Query Built Successfully:")
                print(f"   Variables keys: {list(query_data['variables'].keys())}")
                print(f"   Parent Item ID: {query_data['variables'].get('parentItemId')}")
                print(f"   Item Name: {query_data['variables'].get('itemName')}")
                
                # Check if column values are properly formatted
                column_values_str = query_data['variables'].get('columnValues', '{}')
                try:
                    column_values = json.loads(column_values_str)
                    print(f"   Column Values: {len(column_values)} columns")
                    for col_id, value in column_values.items():
                        print(f"     {col_id}: {value}")
                except:
                    print(f"   Column Values (raw): {column_values_str}")
                
                # Test the actual API call (DRY RUN)
                print(f"\n🔥 Testing API Call (DRY RUN)...")
                
                api_client.dry_run = True  # Enable dry run mode
                response = api_client._execute_single([test_record], 'create_subitems')
                
                print(f"✅ Dry Run Response:")
                print(f"   Success: {response.get('success', False)}")
                print(f"   Records Processed: {response.get('records_processed', 0)}")
                print(f"   Monday IDs: {response.get('monday_ids', [])}")
                print(f"   Operation Type: {response.get('operation_type', 'unknown')}")
                
            except Exception as e:
                print(f"❌ API Client Test Failed: {e}")
                logger.exception("API client test error")
        
        cursor.close()

if __name__ == "__main__":
    main()
