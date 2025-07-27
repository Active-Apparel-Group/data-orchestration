#!/usr/bin/env python3
"""
Test Sync Engine Group ID Fix - Validate group_id usage in sync engine
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def main():
    print("🔧 Testing Sync Engine Group ID Fix...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        print("\n📊 Testing Group ID Column Retrieval...")
        
        # Test headers columns include group_id
        from src.pipelines.sync_order_list.sync_engine import SyncEngine
        
        sync_engine = SyncEngine(config_path, environment="development")
        headers_columns = sync_engine._get_headers_columns()
        
        print(f"Headers columns count: {len(headers_columns)}")
        
        # Check if group_id is included
        group_id_found = any('[group_id]' in col for col in headers_columns)
        group_name_found = any('[group_name]' in col for col in headers_columns)
        
        print(f"✅ [group_id] in headers columns: {group_id_found}")
        print(f"✅ [group_name] in headers columns: {group_name_found}")
        
        if not group_id_found:
            print("❌ CRITICAL: group_id not found in headers columns!")
            return False
        
        print("\n🔍 Testing Database Query with Group ID...")
        
        # Test sample query to verify group_id is retrieved
        test_query = """
        SELECT TOP 5 
            record_uuid, group_name, group_id, item_name,
            monday_item_id, sync_state
        FROM FACT_ORDER_LIST 
        WHERE group_id IS NOT NULL
        ORDER BY created_at DESC
        """
        
        cursor.execute(test_query)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        print(f"Sample records with group_id: {len(results)}")
        print(f"Columns: {columns}")
        
        if results:
            print("\n📋 Sample Data:")
            for row in results[:3]:  # Show first 3 rows
                row_dict = dict(zip(columns, row))
                print(f"  UUID: {row_dict.get('record_uuid', 'N/A')[:8]}...")
                print(f"  Group Name: {row_dict.get('group_name', 'N/A')}")
                print(f"  Group ID: {row_dict.get('group_id', 'N/A')}")
                print(f"  Item Name: {row_dict.get('item_name', 'N/A')[:50]}...")
                print(f"  Monday Item ID: {row_dict.get('monday_item_id', 'N/A')}")
                print("  ---")
        
        print("\n🎯 Testing Group ID Method...")
        
        # Create a mock header row for testing
        if results:
            sample_row = results[0]
            row_dict = dict(zip(columns, sample_row))
            
            # Test the new _get_group_id_from_header method
            try:
                group_id = sync_engine._get_group_id_from_header(row_dict)
                print(f"✅ _get_group_id_from_header returned: {group_id}")
                
                if group_id and group_id != 'Unknown':
                    print("✅ Group ID method working correctly!")
                else:
                    print("⚠️  Group ID method returned fallback value")
                    
            except Exception as e:
                print(f"❌ Error testing group ID method: {e}")
                return False
        
        print("\n✅ Sync Engine Group ID Fix Validation Complete!")
        print("🚀 Ready for production testing with proper group distribution")
        
        cursor.close()
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
