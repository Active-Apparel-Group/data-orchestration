#!/usr/bin/env python3
"""
Debug MON_Boards_Groups Query - Board-Specific Filtering Validation
"""

import sys
from pathlib import Path

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent ## <-- Adjusted for correct path to root>
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def main():
    print("🧪 MON_Boards_Groups Board Filtering Debug")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Test 1: Count all groups
        cursor.execute("SELECT COUNT(*) FROM MON_Boards_Groups")
        total_groups = cursor.fetchone()[0]
        print(f"📊 Total groups in table: {total_groups}")
        
        # Test 2: Count groups by board
        cursor.execute("""
            SELECT board_id, COUNT(*) as group_count 
            FROM MON_Boards_Groups 
            GROUP BY board_id 
            ORDER BY board_id
        """)
        board_counts = cursor.fetchall()
        
        print("\n📋 Groups by Board:")
        for board_id, count in board_counts:
            board_type = "Development" if board_id == "9609317401" else "Production" if board_id == "9200517329" else "Other"
            print(f"   Board {board_id} ({board_type}): {count} groups")
        
        # Test 3: Check specific filtering behavior
        dev_board = "9609317401"
        cursor.execute("""
            SELECT DISTINCT group_name
            FROM MON_Boards_Groups 
            WHERE board_id = ?
            ORDER BY group_name
        """, (dev_board,))
        dev_groups = cursor.fetchall()
        
        print(f"\n🔍 Development Board Groups (showing first 5):")
        for i, (group_title,) in enumerate(dev_groups[:5]):
            print(f"   {i+1}. {group_title}")
        
        # Test 4: Verify filtering works
        test_query = """
            SELECT COUNT(*) 
            FROM MON_Boards_Groups 
            WHERE board_id = ? AND group_name LIKE '%GREYSON%'
        """
        cursor.execute(test_query, (dev_board,))
        greyson_count = cursor.fetchone()[0]
        print(f"\n✅ GREYSON groups in dev board: {greyson_count}")
        
        cursor.close()

if __name__ == "__main__":
    main()
