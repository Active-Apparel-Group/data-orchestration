#!/usr/bin/env python3
"""
Check Group Name Column Population
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

def main():
    print("🔍 CHECKING GROUP_NAME COLUMN POPULATION:")
    print()
    
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)

    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Check if group_name exists and is populated
        cursor.execute(f"""
            SELECT TOP 5 
                [CUSTOMER NAME], 
                [AAG SEASON],
                group_name,
                CASE 
                    WHEN group_name IS NULL THEN 'NULL'
                    WHEN group_name = '' THEN 'EMPTY'
                    ELSE 'POPULATED'
                END as group_name_status
            FROM {config.target_table}
            WHERE [CUSTOMER NAME] IN ('ACTIVELY BLACK', 'AESCAPE')
            ORDER BY [CUSTOMER NAME]
        """)
        
        print("Sample group_name values:")
        for row in cursor.fetchall():
            print(f"  Customer: {row[0]}, Season: {row[1]}, group_name: '{row[2]}', Status: {row[3]}")
        
        # Check overall group_name population stats
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total_records,
                COUNT(group_name) as populated_group_names,
                COUNT(*) - COUNT(group_name) as null_group_names
            FROM {config.target_table}
            WHERE [CUSTOMER NAME] IN ('ACTIVELY BLACK', 'AESCAPE')
        """)
        
        row = cursor.fetchone()
        print(f"\n📊 Group name statistics:")
        print(f"  Total records: {row[0]}")
        print(f"  Populated group_name: {row[1]}")
        print(f"  NULL group_name: {row[2]}")
        
        cursor.close()

if __name__ == "__main__":
    main()
