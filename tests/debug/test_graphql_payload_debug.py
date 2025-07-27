#!/usr/bin/env python3
"""
Debug the exact GraphQL payload being sent to Monday.com for UPDATE operations
"""

import sys
import json
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.monday_api_client import MondayAPIClient

logger = logger.get_logger(__name__)

# Monkey patch the MondayAPIClient to capture the GraphQL query
original_make_api_call = None

def capture_graphql_call(self, query, variables=None):
    print("🔍 CAPTURED GRAPHQL CALL:")
    print("=" * 60)
    print("QUERY:")
    print(query)
    print("\nVARIABLES:")
    print(json.dumps(variables, indent=2) if variables else "None")
    print("=" * 60)
    
    # Call the original method
    return original_make_api_call(self, query, variables)

def main():
    global original_make_api_call
    
    print("🔍 GraphQL Payload Debug for UPDATE Operations")
    
    # Config
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Initialize Monday.com client
    client = MondayAPIClient(config_path)
    
    # Monkey patch to capture GraphQL calls
    original_make_api_call = client._make_api_call
    client._make_api_call = lambda query, variables=None: capture_graphql_call(client, query, variables)
    
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
    
    print("\n📝 Test record for UPDATE:")
    for key, value in test_record.items():
        print(f"   {key}: {value}")
    
    print("\n🚀 Executing UPDATE to capture GraphQL payload...")
    
    try:
        # This will trigger the GraphQL call and our capture function
        result = client.execute('update_items', [test_record], dry_run=False)
        
        print(f"\n📊 Result: {result}")
        
    except Exception as e:
        print(f"💥 Exception during UPDATE: {e}")
        logger.exception("UPDATE failed with exception")

if __name__ == "__main__":
    main()
