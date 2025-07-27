#!/usr/bin/env python3
"""
Debug Test: Query MON_Boards_Groups Table

Direct query to understand the board_id filtering issue.
Check what groups exist for which boards.

Author: Data Orchestration Team  
Created: 2025-01-27
"""

import sys
from pathlib import Path

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def main():
    print("🔍 DEBUG: Querying MON_Boards_Groups Table...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        print("\n📋 Step 1: Check if MON_Boards_Groups table exists")
        check_table_existence(cursor)
        
        print("\n📋 Step 2: Query all records in MON_Boards_Groups")
        query_all_groups(cursor)
        
        print("\n📋 Step 3: Query by specific board IDs")
        query_by_board_ids(cursor, config)
        
        print("\n📋 Step 4: Test group filtering logic")
        test_group_filtering(cursor, config)
        
        cursor.close()

def check_table_existence(cursor):
    """Check if MON_Boards_Groups table exists."""
    try:
        table_check_query = """
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME = 'MON_Boards_Groups'
        """
        cursor.execute(table_check_query)
        table_exists = cursor.fetchone()[0]
        
        if table_exists > 0:
            print("✅ MON_Boards_Groups table exists")
        else:
            print("❌ MON_Boards_Groups table does NOT exist")
            return False
            
        # Check table structure
        structure_query = """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'MON_Boards_Groups'
        ORDER BY ORDINAL_POSITION
        """
        cursor.execute(structure_query)
        columns = cursor.fetchall()
        
        print("📊 Table structure:")
        for col in columns:
            print(f"  {col[0]} ({col[1]}) - Nullable: {col[2]}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error checking table existence: {e}")
        return False

def query_all_groups(cursor):
    """Query all records in MON_Boards_Groups."""
    try:
        all_groups_query = """
        SELECT board_id, group_id, group_name, created_date
        FROM MON_Boards_Groups
        ORDER BY board_id, group_name
        """
        cursor.execute(all_groups_query)
        all_groups = cursor.fetchall()
        
        print(f"📊 Total groups in MON_Boards_Groups: {len(all_groups)}")
        
        if all_groups:
            print("📋 Sample records:")
            for i, group in enumerate(all_groups[:10]):  # Show first 10
                print(f"  {i+1}. Board: {group[0]}, Group ID: {group[1]}, Name: '{group[2]}', Created: {group[3]}")
            
            if len(all_groups) > 10:
                print(f"  ... and {len(all_groups) - 10} more records")
                
            # Group by board_id
            board_counts = {}
            for group in all_groups:
                board_id = group[0]
                board_counts[board_id] = board_counts.get(board_id, 0) + 1
            
            print("📊 Groups per board:")
            for board_id, count in board_counts.items():
                print(f"  Board {board_id}: {count} groups")
        else:
            print("⚠️  No groups found in MON_Boards_Groups table")
            
    except Exception as e:
        print(f"❌ Error querying all groups: {e}")

def query_by_board_ids(cursor, config):
    """Query groups by specific board IDs from config."""
    try:
        # Get board IDs from config
        dev_board_id = config.config_dict.get('monday', {}).get('development', {}).get('board_id')
        prod_board_id = config.config_dict.get('monday', {}).get('production', {}).get('board_id')
        
        print(f"🔧 Config board IDs:")
        print(f"  Development: {dev_board_id}")
        print(f"  Production: {prod_board_id}")
        
        for board_name, board_id in [("Development", dev_board_id), ("Production", prod_board_id)]:
            if board_id:
                board_query = """
                SELECT group_id, group_name, created_date
                FROM MON_Boards_Groups
                WHERE board_id = ?
                ORDER BY group_name
                """
                cursor.execute(board_query, [str(board_id)])
                board_groups = cursor.fetchall()
                
                print(f"📊 {board_name} board ({board_id}): {len(board_groups)} groups")
                
                if board_groups:
                    for i, group in enumerate(board_groups[:5]):  # Show first 5
                        print(f"  {i+1}. ID: {group[0]}, Name: '{group[1]}', Created: {group[2]}")
                    
                    if len(board_groups) > 5:
                        print(f"  ... and {len(board_groups) - 5} more groups")
                else:
                    print(f"  ⚠️  No groups found for {board_name} board")
            else:
                print(f"  ❌ No {board_name} board ID in config")
                
    except Exception as e:
        print(f"❌ Error querying by board IDs: {e}")

def test_group_filtering(cursor, config):
    """Test the exact group filtering logic used by GroupCreationManager."""
    try:
        # Test with realistic group names
        test_groups = ["GREYSON 2025 FALL", "JOHNNIE O 2025 SPRING", "TRACKSMITH 2025 SUMMER"]
        dev_board_id = config.config_dict.get('monday', {}).get('development', {}).get('board_id')
        prod_board_id = config.config_dict.get('monday', {}).get('production', {}).get('board_id')
        
        print(f"🧪 Testing group filtering with: {test_groups}")
        
        for board_name, board_id in [("Development", dev_board_id), ("Production", prod_board_id)]:
            if board_id:
                print(f"\n🔍 Testing {board_name} board ({board_id}):")
                
                # Exact same query as GroupCreationManager.filter_existing_groups
                placeholders = ','.join(['?' for _ in test_groups])
                filter_query = f"""
                SELECT [group_name] 
                FROM [MON_Boards_Groups] 
                WHERE [board_id] = ? 
                  AND [group_name] IN ({placeholders})
                """
                
                params = [str(board_id)] + test_groups
                print(f"📝 Query: {filter_query}")
                print(f"📝 Params: {params}")
                
                cursor.execute(filter_query, params)
                existing_groups = cursor.fetchall()
                existing_group_names = {row[0] for row in existing_groups}
                
                new_groups = [name for name in test_groups if name not in existing_group_names]
                
                print(f"📊 Results for {board_name}:")
                print(f"  Existing groups: {list(existing_group_names)}")
                print(f"  New groups: {new_groups}")
                print(f"  Filtering result: {len(new_groups)} new out of {len(test_groups)} total")
                
                if existing_group_names:
                    print(f"  ⚠️  Found existing groups in {board_name} board!")
                else:
                    print(f"  ✅ No existing groups in {board_name} board (correct for filtering)")
                    
    except Exception as e:
        print(f"❌ Error testing group filtering: {e}")

if __name__ == "__main__":
    main()
