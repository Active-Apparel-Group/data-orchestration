#!/usr/bin/env python3
"""
Test UPDATE with correct database column names (not Monday column IDs)
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.monday_api_client import MondayAPIClient

logger = logger.get_logger(__name__)

def main():
    print("🔍 Fixed UPDATE Test with Database Column Names")
    
    # Config
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Initialize Monday.com client
    client = MondayAPIClient(config_path)
    
    # Target item to update
    item_id = 9671361253
    print(f"🎯 Target Monday.com item: {item_id}")
    
    # Test record with DATABASE COLUMN NAMES (not Monday column IDs)
    test_record = {
        'monday_item_id': item_id,           # Special field for UPDATE
        'AAG SEASON': '2025 SPRING',         # Database column name
        'AAG ORDER NUMBER': 'GRE-04305',    # Database column name  
        'CUSTOMER NAME': 'GREYSON'          # Database column name
    }
    
    print("\n📝 Test record with DATABASE column names:")
    for key, value in test_record.items():
        print(f"   {key}: {value}")
    
    print("\n🚀 Executing UPDATE with correct column names...")
    
    try:
        result = client.execute('update_items', [test_record], dry_run=False)
        
        print("\n📊 UPDATE API call result:")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Records processed: {result.get('records_processed', 0)}")
        print(f"   Monday IDs: {result.get('monday_ids', [])}")
        print(f"   Operation type: {result.get('operation_type', 'unknown')}")
        print(f"   Errors: {result.get('errors', None)}")
        
        if result.get('success'):
            print("✅ UPDATE API call completed successfully")
            
            # Now check if the value actually changed
            print("\n🔍 Verifying Monday.com item after UPDATE...")
            
            import asyncio
            
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
                            return True
                        else:
                            print(f"   ❌ FAILED: Expected '2025 SPRING', got '{current_value}'")
                            return False
                        break
            else:
                print("   ❌ Failed to retrieve item for verification")
                return False
                
        else:
            print("❌ UPDATE API call failed")
            print(f"   Error details: {result.get('errors', 'No error details')}")
            return False
    
    except Exception as e:
        print(f"💥 Exception during UPDATE: {e}")
        logger.exception("UPDATE API call failed with exception")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 UPDATE operation completed successfully!")
    else:
        print("\n❌ UPDATE operation failed")
