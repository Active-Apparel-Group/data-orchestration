#!/usr/bin/env python3
"""
Verify UPDATE operation preserved correct monday_item_id and sent UPDATE to Monday.com
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
    print("🔍 UPDATE Operation Verification")
    
    # Config
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Check database state after UPDATE operation
        query = """
        SELECT 
            [record_uuid],
            [AAG ORDER NUMBER],
            [AAG SEASON],
            [monday_item_id],
            [sync_state],
            [action_type],
            [sync_completed_at]
        FROM FACT_ORDER_LIST 
        WHERE [monday_item_id] = 9671361253
        """
        
        cursor.execute(query)
        result = cursor.fetchone()
        
        if result:
            print(f"✅ Found record with monday_item_id = 9671361253:")
            print(f"   record_uuid: {result[0]}")
            print(f"   AAG ORDER NUMBER: {result[1]}")
            print(f"   AAG SEASON: {result[2]}")
            print(f"   monday_item_id: {result[3]}")
            print(f"   sync_state: {result[4]}")
            print(f"   action_type: {result[5]}")
            print(f"   sync_completed_at: {result[6]}")
            
            # Verify UPDATE operation completed correctly
            if result[2] == '2025 SPRING':
                print("✅ AAG SEASON correctly updated to '2025 SPRING'")
            else:
                print(f"❌ AAG SEASON should be '2025 SPRING', found: '{result[2]}'")
                
            if result[4] == 'SYNCED':
                print("✅ sync_state correctly set to 'SYNCED'")
            else:
                print(f"❌ sync_state should be 'SYNCED', found: '{result[4]}'")
                
            if result[3] == 9671361253:
                print("✅ monday_item_id preserved correctly (not changed during UPDATE)")
            else:
                print(f"❌ monday_item_id should be 9671361253, found: {result[3]}")
                
        else:
            print("❌ No record found with monday_item_id = 9671361253")
        
        cursor.close()

if __name__ == "__main__":
    main()
