#!/usr/bin/env python3
"""
🔬 BATCH SUBITEM DEBUG - Analyze why batch operations fail
Compare single vs batch GraphQL queries and responses
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

async def debug_batch_processing():
    print("🔬 Batch Subitem Processing Debug...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Get the exact failed batch data
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Get the original failed batch records
        failed_query = """
        SELECT TOP 1
            api_request_payload
        FROM ORDER_LIST_LINES 
        WHERE api_operation_type = 'subitem_creation'
        AND api_status = 'ERROR'
        AND api_request_payload IS NOT NULL
        """
        
        cursor.execute(failed_query)
        failed_record = cursor.fetchone()
        
        if not failed_record:
            print("❌ No failed batch record found")
            return
        
        # Parse the original batch payload
        batch_records = json.loads(failed_record[0]) if failed_record[0] else []
        
        if not batch_records:
            print("❌ No batch records found in payload")
            return
            
        print(f"📋 Original Batch Analysis:")
        print(f"   Records in batch: {len(batch_records)}")
        
        # Show first few records
        for i, record in enumerate(batch_records[:3]):
            print(f"   Record {i+1}:")
            print(f"     Parent ID: {record.get('parent_item_id')}")
            print(f"     Size: {record.get('size_code')}")
            print(f"     Qty: {record.get('qty')}")
        
        # Test with Monday API client
        from src.pipelines.sync_order_list.monday_api_client import MondayAPIClient
        
        api_client = MondayAPIClient(config_path)
        api_client.dry_run = False  # We want real API calls
        
        print(f"\n🧪 Testing Single vs Batch Processing...")
        
        # Test 1: Single subitem (we know this works)
        print(f"\n🔸 TEST 1: Single Subitem Creation")
        single_record = batch_records[0]  # Use first record from failed batch
        
        try:
            single_query = api_client._build_graphql_query('create_subitems', [single_record])
            
            print(f"✅ Single Query Built:")
            print(f"   Variables: {list(single_query['variables'].keys())}")
            print(f"   Query length: {len(single_query['query'])} chars")
            
            # Show key parts of single query
            print(f"\n📝 Single Query Structure:")
            query_lines = single_query['query'].split('\n')
            mutation_line = next((line for line in query_lines if 'mutation' in line.lower()), '')
            print(f"   Mutation: {mutation_line.strip()}")
            
            create_subitem_line = next((line for line in query_lines if 'create_subitem(' in line), '')
            print(f"   Call: {create_subitem_line.strip()}")
            
        except Exception as e:
            print(f"❌ Single query failed: {e}")
        
        # Test 2: Batch subitems (2 records - smaller batch)
        print(f"\n🔸 TEST 2: Small Batch (2 records)")
        small_batch = batch_records[:2]
        
        try:
            batch_query = api_client._build_graphql_query('create_subitems', small_batch)
            
            print(f"✅ Batch Query Built:")
            print(f"   Variables: {list(batch_query['variables'].keys())}")
            print(f"   Query length: {len(batch_query['query'])} chars")
            
            # Show key parts of batch query
            print(f"\n📝 Batch Query Structure:")
            query_lines = batch_query['query'].split('\n')
            mutation_line = next((line for line in query_lines if 'mutation' in line.lower()), '')
            print(f"   Mutation: {mutation_line.strip()}")
            
            # Count create_subitem calls
            create_calls = [line for line in query_lines if 'create_subitem_' in line and ':' in line]
            print(f"   Create calls: {len(create_calls)}")
            for call in create_calls:
                print(f"     {call.strip()}")
            
            # Show variables structure
            print(f"\n📝 Batch Variables:")
            for key, value in batch_query['variables'].items():
                if 'columnValues' in key:
                    print(f"   {key}: {value}")
                else:
                    print(f"   {key}: {value}")
            
        except Exception as e:
            print(f"❌ Batch query build failed: {e}")
            logger.exception("Batch query error")
        
        # Test 3: Full batch (original 5 records)
        print(f"\n🔸 TEST 3: Full Batch ({len(batch_records)} records)")
        
        try:
            full_batch_query = api_client._build_graphql_query('create_subitems', batch_records)
            
            print(f"✅ Full Batch Query Built:")
            print(f"   Variables: {len(full_batch_query['variables'])} total")
            print(f"   Query length: {len(full_batch_query['query'])} chars")
            
            # Check for potential issues
            query_text = full_batch_query['query']
            
            # Check if query is too long
            if len(query_text) > 8000:
                print(f"⚠️  WARNING: Query very long ({len(query_text)} chars) - may hit limits")
            
            # Check for duplicate parent IDs
            parent_ids = [record.get('parent_item_id') for record in batch_records]
            unique_parents = set(parent_ids)
            if len(unique_parents) < len(parent_ids):
                print(f"⚠️  WARNING: Duplicate parent IDs detected")
                print(f"   Total records: {len(parent_ids)}")
                print(f"   Unique parents: {len(unique_parents)}")
            
            # Test the actual API call with small batch first
            print(f"\n🚨 TESTING SMALL BATCH API CALL...")
            
            small_response = await api_client._make_api_call(
                batch_query['query'], 
                batch_query['variables']
            )
            
            print(f"✅ Small Batch API Response:")
            print(f"   Keys: {list(small_response.keys())}")
            
            if 'data' in small_response:
                data_keys = list(small_response['data'].keys()) if small_response['data'] else []
                print(f"   Data keys: {data_keys}")
                
                # Check each subitem creation result
                for key in data_keys:
                    result = small_response['data'][key]
                    if result:
                        print(f"   {key}: SUCCESS (ID: {result.get('id')})")
                    else:
                        print(f"   {key}: FAILED (null response)")
                        
            if 'errors' in small_response:
                print(f"❌ Small Batch API Errors:")
                for error in small_response['errors']:
                    print(f"     - {error.get('message', 'Unknown error')}")
                    if 'extensions' in error:
                        print(f"       Code: {error['extensions'].get('code', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ Full batch test failed: {e}")
            logger.exception("Full batch error")
        
        cursor.close()

def main():
    asyncio.run(debug_batch_processing())

if __name__ == "__main__":
    main()
