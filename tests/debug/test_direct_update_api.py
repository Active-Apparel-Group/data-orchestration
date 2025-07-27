#!/usr/bin/env python3
"""
Test UPDATE API call directly to diagnose Monday.com UPDATE issues
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.monday_api_client import MondayAPIClient
import asyncio

logger = logger.get_logger(__name__)

def main():
    print("🔍 Direct UPDATE API Call Test")
    
    # Config
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Initialize Monday.com client
    client = MondayAPIClient(config_path)
    
    # Target item to update
    item_id = 9671361253
    print(f"🎯 Target Monday.com item: {item_id}")
    
    # Test record for UPDATE (simulating what SyncEngine sends)
    test_record = {
        'monday_item_id': item_id,
        'dropdown_mkr58de6': '2025 SPRING',  # AAG SEASON
        'text_mkr5wya6': 'GRE-04305',        # AAG ORDER NUMBER
        'dropdown_mkr542p2': 'GREYSON'       # CUSTOMER NAME
    }
    
    print("📝 Test record for UPDATE:")
    for key, value in test_record.items():
        print(f"   {key}: {value}")
    
    print("\n🚀 Executing direct UPDATE API call...")
    
    try:
        # Call update_items directly
        result = client.execute('update_items', [test_record], dry_run=False)
        
        print("📊 UPDATE API call result:")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Records processed: {result.get('records_processed', 0)}")
        print(f"   Monday IDs: {result.get('monday_ids', [])}")
        print(f"   Operation type: {result.get('operation_type', 'unknown')}")
        print(f"   Errors: {result.get('errors', None)}")
        
        if result.get('success'):
            print("✅ UPDATE API call completed successfully")
            
            # Now check if the value actually changed
            print("\n🔍 Verifying Monday.com item after UPDATE...")
            
            query = f"""
            query {{
                items(ids: [{item_id}]) {{
                    id
                    name
                    column_values {{
                        id
                        text
                        type
                    }}
                }}
            }}
            """
            
            async def verify_update():
                result = await client._make_api_call(query)
                return result
            
            response = asyncio.run(verify_update())
            
            if response.get('success') and response.get('data', {}).get('items'):
                item = response['data']['items'][0]
                
                # Find AAG SEASON column
                for col in item.get('column_values', []):
                    if col.get('id') == 'dropdown_mkr58de6':
                        current_value = col.get('text', 'None')
                        print(f"   AAG SEASON after UPDATE: '{current_value}'")
                        
                        if current_value == '2025 SPRING':
                            print("   ✅ SUCCESS: Value updated correctly!")
                        else:
                            print(f"   ❌ FAILED: Expected '2025 SPRING', got '{current_value}'")
                        break
            else:
                print("   ❌ Failed to retrieve item for verification")
                
        else:
            print("❌ UPDATE API call failed")
            print(f"   Error details: {result.get('errors', 'No error details')}")
    
    except Exception as e:
        print(f"💥 Exception during UPDATE: {e}")
        logger.exception("UPDATE API call failed with exception")

if __name__ == "__main__":
    main()
