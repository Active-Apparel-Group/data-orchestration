#!/usr/bin/env python3
"""
🎯 SINGLE SUBITEM TEST - Isolate the exact issue
Test creating just ONE subitem with the exact data from the failed batch operation
"""

import sys
from pathlib import Path
import json
import asyncio

# Legacy transition support pattern
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

async def test_single_subitem():
    print("🎯 Single Subitem Creation Test...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Get the exact failed record data
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Get one specific failed record
        failed_query = """
        SELECT TOP 1
            line_uuid,
            monday_subitem_id,
            api_request_payload,
            qty,
            size_code
        FROM ORDER_LIST_LINES 
        WHERE api_operation_type = 'subitem_creation'
        AND api_status = 'ERROR'
        AND monday_subitem_id = 9701867431
        """
        
        cursor.execute(failed_query)
        failed_record = cursor.fetchone()
        
        if not failed_record:
            print("❌ No specific failed record found")
            return
        
        print(f"📋 Testing with failed record:")
        print(f"   Line UUID: {failed_record[0]}")
        print(f"   Monday Subitem ID: {failed_record[1]}")
        print(f"   Quantity: {failed_record[3]}")
        print(f"   Size Code: {failed_record[4]}")
        
        # Parse the original request payload
        request_payload = json.loads(failed_record[2]) if failed_record[2] else []
        if request_payload:
            original_record = request_payload[0]  # Get the first record from the batch
            
            print(f"\n📤 Original Record Data:")
            print(f"   Parent Item ID: {original_record.get('parent_item_id')}")
            print(f"   Size Code: {original_record.get('size_code')}")
            print(f"   Quantity: {original_record.get('qty')}")
            print(f"   Action Type: {original_record.get('action_type')}")
            
            # Now test creating this single subitem manually using GraphQL
            print(f"\n🔧 Manual GraphQL Test...")
            
            # Import here to avoid circular dependencies
            from src.pipelines.sync_order_list.monday_api_client import MondayAPIClient
            
            api_client = MondayAPIClient(config_path)
            api_client.dry_run = False  # We want to see the real API call
            
            # Test the single record
            single_record = {
                'parent_item_id': original_record.get('parent_item_id'),
                'size_code': original_record.get('size_code'),
                'qty': original_record.get('qty'),
                'action_type': 'INSERT'
            }
            
            try:
                # Build the GraphQL query for a single subitem
                query_data = api_client._build_graphql_query('create_subitems', [single_record])
                
                print(f"✅ GraphQL Query Built:")
                print(f"   Variables: {list(query_data['variables'].keys())}")
                
                # Show the exact GraphQL query
                print(f"\n📝 GraphQL Query:")
                print(query_data['query'][:200] + "..." if len(query_data['query']) > 200 else query_data['query'])
                
                print(f"\n📝 Variables:")
                for key, value in query_data['variables'].items():
                    if key == 'columnValues':
                        print(f"   {key}: {value}")
                    else:
                        print(f"   {key}: {value}")
                
                # Test the actual API call
                print(f"\n🚨 MAKING REAL API CALL...")
                response = await api_client._make_api_call(
                    query_data['query'], 
                    query_data['variables']
                )
                
                print(f"✅ API Response:")
                print(f"   Keys: {list(response.keys())}")
                
                if 'data' in response:
                    print(f"   Data keys: {list(response['data'].keys()) if response['data'] else 'None'}")
                    
                if 'errors' in response:
                    print(f"❌ API Errors:")
                    for error in response['errors']:
                        print(f"     - {error.get('message', 'Unknown error')}")
                        if 'path' in error:
                            print(f"       Path: {error['path']}")
                        if 'extensions' in error:
                            print(f"       Code: {error['extensions'].get('code', 'Unknown')}")
                
                # Parse the successful response
                if response.get('data') and 'create_subitem' in response['data']:
                    subitem_data = response['data']['create_subitem']
                    if subitem_data:
                        print(f"✅ Subitem Created Successfully!")
                        print(f"   New Subitem ID: {subitem_data.get('id')}")
                        print(f"   Name: {subitem_data.get('name')}")
                    else:
                        print(f"❌ Subitem creation returned null")
                        
            except Exception as e:
                print(f"❌ Test Failed: {e}")
                logger.exception("Single subitem test error")
        
        cursor.close()

def main():
    asyncio.run(test_single_subitem())

if __name__ == "__main__":
    main()
