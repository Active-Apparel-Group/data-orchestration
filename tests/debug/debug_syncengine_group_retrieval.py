#!/usr/bin/env python3
"""
Debug SyncEngine Group Name Retrieval
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

def main():
    print("🔍 DEBUGGING SYNCENGINE GROUP NAME RETRIEVAL:")
    print()
    
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)

    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Check what SyncEngine actually retrieves
        print("📋 SyncEngine Query - What headers are retrieved:")
        sync_query = f"""
        SELECT TOP 5
            [CUSTOMER NAME],
            [AAG SEASON],
            [group_name],
            [item_name],
            [action_type],
            [sync_state]
        FROM {config.target_table}
        WHERE [CUSTOMER NAME] IN ('ACTIVELY BLACK', 'AESCAPE')
        AND [sync_state] = 'PENDING'
        ORDER BY [CUSTOMER NAME]
        """
        
        cursor.execute(sync_query)
        results = cursor.fetchall()
        
        if results:
            print("SyncEngine retrieval results:")
            for row in results:
                customer, season, group_name, item_name, action_type, sync_state = row
                group_status = "POPULATED" if group_name else "NULL/EMPTY"
                print(f"  Customer: {customer}, Season: {season}")
                print(f"    group_name: '{group_name}' ({group_status})")
                print(f"    item_name: '{item_name}'")
                print(f"    action_type: {action_type}, sync_state: {sync_state}")
                print()
        else:
            print("❌ No PENDING records found!")
            
        # Check sync_state distribution
        print("📊 Sync State Distribution:")
        cursor.execute(f"""
        SELECT [sync_state], COUNT(*) as count
        FROM {config.target_table}
        WHERE [CUSTOMER NAME] IN ('ACTIVELY BLACK', 'AESCAPE')
        GROUP BY [sync_state]
        ORDER BY [sync_state]
        """)
        
        for row in cursor.fetchall():
            sync_state, count = row
            print(f"  {sync_state}: {count} records")
        
        cursor.close()

if __name__ == "__main__":
    main()
