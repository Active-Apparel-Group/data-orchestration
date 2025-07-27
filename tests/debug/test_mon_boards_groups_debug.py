#!/usr/bin/import sys
from pathlib import Path

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))"
Debug MON_Boards_Groups Query - Board-Specific Filtering Validation

Test to directly query MON_Boards_Groups table and verify board_id filtering
is working correctly for group creation logic.

Author: Data Orchestration Team
Created: 2025-01-27
"""

import sys
from pathlib import Path

# Standard import pattern - use this in ALL scripts
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))
sys.path.insert(0, str(repo_root / "src"))

# Import from utils/ - PRODUCTION PATTERN
from db_helper import get_cursor_and_connection
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

def main():
    print("🧪 Debug MON_Boards_Groups Query - Board-Specific Filtering")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        print("\n📋 Step 1: Query ALL groups in MON_Boards_Groups")
        query_all_groups(cursor)
        
        print("\n📋 Step 2: Query groups by DEV board_id (9609317401)")
        query_groups_by_board(cursor, "9609317401", "DEVELOPMENT")
        
        print("\n📋 Step 3: Query groups by PROD board_id (9200517329)")
        query_groups_by_board(cursor, "9200517329", "PRODUCTION")
        
        print("\n📋 Step 4: Test specific group filtering scenario")
        test_group_filtering_scenario(cursor)
        
        cursor.close()

def query_all_groups(cursor):
    """Query all groups to see what's in the table."""
    print("🔍 Querying ALL groups in MON_Boards_Groups...")
    
    try:
        query = """
        SELECT [board_id], [group_id], [group_name], [created_date]
        FROM [MON_Boards_Groups] 
        ORDER BY [board_id], [group_name]
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        print(f"✅ Found {len(results)} total groups")
        
        if results:
            print("📊 Sample groups:")
            for i, row in enumerate(results[:10]):  # Show first 10
                board_id, group_id, group_name, created_date = row
                print(f"  {i+1}. Board: {board_id} | Group: '{group_name}' | ID: {group_id}")
            
            if len(results) > 10:
                print(f"  ... and {len(results) - 10} more groups")
                
            # Group by board_id
            board_counts = {}
            for row in results:
                board_id = row[0]
                board_counts[board_id] = board_counts.get(board_id, 0) + 1
            
            print(f"📊 Groups per board:")
            for board_id, count in board_counts.items():
                print(f"  Board {board_id}: {count} groups")
        else:
            print("❌ No groups found in MON_Boards_Groups table")
            
    except Exception as e:
        print(f"❌ Error querying all groups: {e}")

def query_groups_by_board(cursor, board_id: str, board_name: str):
    """Query groups for a specific board_id."""
    print(f"🔍 Querying groups for {board_name} board ({board_id})...")
    
    try:
        query = """
        SELECT [group_id], [group_name], [created_date]
        FROM [MON_Boards_Groups] 
        WHERE [board_id] = ?
        ORDER BY [group_name]
        """
        
        cursor.execute(query, [board_id])
        results = cursor.fetchall()
        
        print(f"✅ Found {len(results)} groups for {board_name} board")
        
        if results:
            print(f"📊 {board_name} board groups:")
            for i, row in enumerate(results[:10]):  # Show first 10
                group_id, group_name, created_date = row
                print(f"  {i+1}. '{group_name}' | ID: {group_id}")
            
            if len(results) > 10:
                print(f"  ... and {len(results) - 10} more groups")
        else:
            print(f"❌ No groups found for {board_name} board ({board_id})")
            
    except Exception as e:
        print(f"❌ Error querying {board_name} board groups: {e}")

def test_group_filtering_scenario(cursor):
    """Test the exact filtering scenario used in GroupCreationManager."""
    print("🔍 Testing GroupCreationManager filtering scenario...")
    
    # Test groups that might exist in different boards
    test_groups = ["GREYSON 2025 FALL", "JOHNNIE O 2025 SPRING", "TEST GROUP"]
    dev_board_id = "9609317401"
    prod_board_id = "9200517329"
    
    for board_id, board_name in [(dev_board_id, "DEV"), (prod_board_id, "PROD")]:
        print(f"\n🎯 Testing {board_name} board ({board_id})...")
        
        # Create parameterized query like GroupCreationManager does
        placeholders = ','.join(['?' for _ in test_groups])
        query = f"""
        SELECT [group_name] 
        FROM [MON_Boards_Groups] 
        WHERE [board_id] = ? 
          AND [group_name] IN ({placeholders})
        """
        
        try:
            params = [board_id] + test_groups
            cursor.execute(query, params)
            existing_groups = {row[0] for row in cursor.fetchall()}
            
            new_groups = [name for name in test_groups if name not in existing_groups]
            
            print(f"  📊 Test groups: {test_groups}")
            print(f"  ✅ Existing in {board_name}: {list(existing_groups)}")
            print(f"  🆕 New for {board_name}: {new_groups}")
            print(f"  📈 Filtering result: {len(new_groups)} new out of {len(test_groups)} total")
            
        except Exception as e:
            print(f"  ❌ Error testing {board_name} board: {e}")

if __name__ == "__main__":
    main()
