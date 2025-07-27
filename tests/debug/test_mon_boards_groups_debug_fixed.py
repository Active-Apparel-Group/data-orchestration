#!/usr/bin/env python3
"""
Debug MON_Boards_Groups Query - Board-Specific Filtering Validation

Test to directly query MON_Boards_Groups table and verify board_id filtering
is working correctly for group creation logic.

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

logger = logger.get_logger(__name__)

def main():
    print("🧪 Debug MON_Boards_Groups Query - Board-Specific Filtering Validation")
    print("=" * 80)
    
    # Setup connection
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    
    # Import here to avoid circular dependencies
    from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
    config = DeltaSyncConfig.from_toml(config_path)
    
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        print("\n📋 Test 1: Query ALL groups (no filtering)")
        query_all_groups(cursor)
        
        print("\n📋 Test 2: Query groups for Development Board (9609317401)")
        query_groups_by_board(cursor, "9609317401")
        
        print("\n📋 Test 3: Query groups for Production Board (9200517329)")
        query_groups_by_board(cursor, "9200517329")
        
        print("\n📋 Test 4: Check if test groups exist")
        test_group_names = [
            "GREYSON - SS25",
            "GREYSON - FW24", 
            "GREYSON - FALL WINTER 2024"
        ]
        check_test_groups(cursor, test_group_names)
        
        cursor.close()
    
    print("\n✅ MON_Boards_Groups debug query completed!")

def query_all_groups(cursor):
    """Query all groups to see what's in the table."""
    query = """
    SELECT 
        board_id,
        group_id,
        group_title,
        COUNT(*) as group_count
    FROM MON_Boards_Groups 
    GROUP BY board_id, group_id, group_title
    ORDER BY board_id, group_title
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    print(f"🔍 Total unique groups found: {len(results)}")
    
    # Group by board_id
    dev_groups = [r for r in results if r[0] == "9609317401"]
    prod_groups = [r for r in results if r[0] == "9200517329"]
    
    print(f"   📊 Development Board (9609317401): {len(dev_groups)} groups")
    print(f"   📊 Production Board (9200517329): {len(prod_groups)} groups")
    
    if dev_groups:
        print("\n   🔍 Development Board Groups:")
        for board_id, group_id, group_title, count in dev_groups[:5]:  # Show first 5
            print(f"      - {group_title} (ID: {group_id}, Count: {count})")
    
    if prod_groups:
        print("\n   🔍 Production Board Groups:")
        for board_id, group_id, group_title, count in prod_groups[:5]:  # Show first 5
            print(f"      - {group_title} (ID: {group_id}, Count: {count})")

def query_groups_by_board(cursor, board_id):
    """Query groups for a specific board_id."""
    query = """
    SELECT 
        group_id,
        group_title,
        COUNT(*) as group_count
    FROM MON_Boards_Groups 
    WHERE board_id = ?
    GROUP BY group_id, group_title
    ORDER BY group_title
    """
    
    cursor.execute(query, (board_id,))
    results = cursor.fetchall()
    
    print(f"🔍 Groups for board {board_id}: {len(results)} unique groups")
    
    for group_id, group_title, count in results[:10]:  # Show first 10
        print(f"   - {group_title} (ID: {group_id}, Count: {count})")

def check_test_groups(cursor, test_group_names):
    """Check if specific test groups exist and on which boards."""
    for group_name in test_group_names:
        print(f"\n🔍 Checking group: '{group_name}'")
        
        query = """
        SELECT 
            board_id,
            group_id,
            COUNT(*) as occurrences
        FROM MON_Boards_Groups 
        WHERE group_title = ?
        GROUP BY board_id, group_id
        ORDER BY board_id
        """
        
        cursor.execute(query, (group_name,))
        results = cursor.fetchall()
        
        if results:
            print(f"   ✅ Found {len(results)} board(s) with this group:")
            for board_id, group_id, count in results:
                board_type = "Development" if board_id == "9609317401" else "Production" if board_id == "9200517329" else "Unknown"
                print(f"      - Board {board_id} ({board_type}): Group ID {group_id} ({count} occurrences)")
        else:
            print(f"   ❌ Group not found in any board")

if __name__ == "__main__":
    main()
