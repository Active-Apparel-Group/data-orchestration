#!/usr/bin/env python3
"""
Debug GraphQL Generation - See exact query our code produces
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
    print("🔍 Debug GraphQL Generation for O/S Label...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Initialize Monday API client
    monday_client = MondayAPIClient(config_path)
    
    # Create test subitem data exactly like our pipeline does
    test_line_data = [{
        'parent_item_id': 9683248375,
        'line_uuid': 'test-uuid-1',
        'record_uuid': 'C6EB2400-560E-4722-A56B-9E35079F2ED0',
        'dropdown_mkrak7qp': 'O/S',  # This should trigger the issue
        'numeric_mkra7j8e': 1,
        'size_code': 'O/S'
    }]
    
    print(f"🎯 Test data: {test_line_data}")
    
    try:
        # Build the GraphQL query that our code would generate
        graphql_query = monday_client._build_graphql_query('create_subitems', test_line_data)
        
        print("=" * 80)
        print("🔧 GENERATED GRAPHQL QUERY:")
        print("=" * 80)
        print(f"Query: {graphql_query.get('query', 'No query found')}")
        print(f"Variables: {graphql_query.get('variables', 'No variables found')}")
        print("=" * 80)
        
        # Also test the column values building specifically
        column_values = monday_client._build_column_values(test_line_data[0])
        print(f"🎯 Column Values String: {column_values}")
        
    except Exception as e:
        print(f"❌ Error generating GraphQL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
