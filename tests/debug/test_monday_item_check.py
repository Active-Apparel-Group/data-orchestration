#!/usr/bin/env python3
"""
Check Monday.com item directly to see if UPDATE worked
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
    print("🔍 Monday.com Item Direct Check")
    
    # Config
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Initialize Monday.com client
    client = MondayAPIClient(config_path)
    
    # Check the item directly
    item_id = 9671361253
    print(f"📞 Querying Monday.com item: {item_id}")
    
    # Query Monday.com using GraphQL
    query = f"""
    query {{
        items(ids: [{item_id}]) {{
            id
            name
            column_values {{
                id
                text
                type
                value
            }}
        }}
    }}
    """
    
    import asyncio
    
    async def query_item():
        result = await client._make_api_call(query)
        return result
    
    response = asyncio.run(query_item())
    
    if response.get('success') and response.get('data', {}).get('items'):
        item = response['data']['items'][0]
        
        print(f"✅ Item {item_id} retrieved:")
        print(f"   Name: '{item.get('name', 'Unknown')}'")
        
        # Get column values
        column_values = item.get('column_values', [])
        
        for col in column_values:
            col_id = col.get('id')
            col_value = col.get('text', 'None')
            col_type = col.get('type')
            
            # Focus on AAG SEASON dropdown
            if col_id == 'dropdown_mkr58de6':
                print(f"   🎯 AAG SEASON ({col_id}): '{col_value}' (type: {col_type})")
                
                if col_value == '2025 SPRING':
                    print("   ✅ SUCCESS: Monday.com shows '2025 SPRING' - UPDATE worked!")
                elif col_value == '2025 FALL':
                    print("   ❌ Monday.com still shows '2025 FALL' - UPDATE may have failed")
                else:
                    print(f"   ⚠️  Unexpected value: '{col_value}'")
    else:
        print(f"❌ Failed to retrieve item {item_id}")

if __name__ == "__main__":
    main()
