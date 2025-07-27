#!/usr/bin/env python3
"""
🎯 VERIFY MONDAY SUBITEMS - Check if the "failed" subitems actually exist on Monday.com
Test if the issue is with API logging vs actual operation failure
"""

import sys
from pathlib import Path
import asyncio

# Legacy transition support pattern
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.monday_api_client import MondayAPIClient

logger = logger.get_logger(__name__)

async def verify_monday_subitems():
    print("🎯 Verifying Monday.com Subitems...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Get the "failed" records with their Monday subitem IDs
        query = """
        SELECT 
            line_uuid,
            size_code,
            monday_subitem_id,
            api_status
        FROM ORDER_LIST_LINES 
        WHERE api_operation_type = 'subitem_creation'
        AND api_status = 'ERROR'
        AND monday_subitem_id IS NOT NULL
        ORDER BY size_code
        """
        
        cursor.execute(query)
        records = cursor.fetchall()
        
        if not records:
            print("❌ No 'failed' records with Monday subitem IDs found")
            return
        
        print(f"\n📋 'Failed' Records with Monday IDs:")
        monday_ids_to_check = []
        for record in records:
            print(f"   UUID: {record[0][:8]}... | Size: {record[1]} | Monday ID: {record[2]} | Status: {record[3]}")
            monday_ids_to_check.append(str(record[2]))
        
        # Initialize Monday API client
        api_client = MondayAPIClient(config_path)
        
        print(f"\n🔍 Checking if these subitems exist on Monday.com...")
        
        # Build a query to check if these subitems exist
        # Use Monday.com's items query to verify existence
        query_template = """
        query CheckSubitems {
          items(ids: [%s]) {
            id
            name
            board {
              id
              name
            }
            parent_item {
              id
              name
            }
            column_values {
              id
              text
              value
            }
          }
        }
        """ % ', '.join(monday_ids_to_check)
        
        try:
            print(f"🚨 Making API call to verify subitem existence...")
            
            # Make the API call
            response = await api_client._make_api_call(query_template, {})
            
            print(f"✅ API Response received:")
            print(f"   Response keys: {list(response.keys())}")
            
            if 'data' in response and 'items' in response['data']:
                found_items = response['data']['items']
                print(f"   Found {len(found_items)} out of {len(monday_ids_to_check)} subitems")
                
                # Map found items by ID
                found_ids = set()
                for item in found_items:
                    if item:  # item might be null if not found
                        item_id = item.get('id')
                        item_name = item.get('name', 'Unknown')
                        parent_id = item.get('parent_item', {}).get('id') if item.get('parent_item') else 'None'
                        print(f"   ✅ Found: ID {item_id} | Name: {item_name} | Parent: {parent_id}")
                        found_ids.add(item_id)
                
                # Check which IDs were not found
                missing_ids = set(monday_ids_to_check) - found_ids
                if missing_ids:
                    print(f"\n❌ Missing subitems:")
                    for missing_id in missing_ids:
                        print(f"   - ID {missing_id}")
                else:
                    print(f"\n🎉 ALL SUBITEMS EXIST ON MONDAY.COM!")
                    print(f"   The 'ERROR' status is likely an API logging bug, not actual failure!")
                    
            elif 'errors' in response:
                print(f"❌ API Errors:")
                for error in response['errors']:
                    print(f"   - {error.get('message', 'Unknown error')}")
            else:
                print(f"❌ Unexpected response structure: {response}")
                
        except Exception as e:
            print(f"❌ API verification failed: {e}")
            logger.exception("Monday subitem verification error")
        
        cursor.close()

def main():
    asyncio.run(verify_monday_subitems())

if __name__ == "__main__":
    main()
