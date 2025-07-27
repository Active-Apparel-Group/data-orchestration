#!/usr/bin/env python3
"""
Quick schema check for ORDER_LIST vs ORDER_LIST_V2 differences
"""

import sys
from pathlib import Path

# Legacy transition support pattern (SAME AS WORKING TESTS)
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def check_table_schemas():
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Get ORDER_LIST columns
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'ORDER_LIST'
            ORDER BY ORDINAL_POSITION
        """)
        order_list_cols = cursor.fetchall()
        
        # Get ORDER_LIST_V2 columns  
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'ORDER_LIST_V2'
            ORDER BY ORDINAL_POSITION
        """)
        order_list_v2_cols = cursor.fetchall()
        
        print(f"ORDER_LIST columns: {len(order_list_cols)}")
        print(f"ORDER_LIST_V2 columns: {len(order_list_v2_cols)}")
        
        # Find differences
        ol_names = [col[0] for col in order_list_cols]
        ol_v2_names = [col[0] for col in order_list_v2_cols]
        
        only_in_ol = set(ol_names) - set(ol_v2_names)
        only_in_ol_v2 = set(ol_v2_names) - set(ol_names)
        
        print(f"\nColumns only in ORDER_LIST: {only_in_ol}")
        print(f"Columns only in ORDER_LIST_V2: {only_in_ol_v2}")
        
        # Check sync columns specifically
        sync_cols = [col for col in ol_v2_names if 'sync_' in col.lower() or 'action_type' in col.lower()]
        print(f"\nSync columns in ORDER_LIST_V2: {sync_cols}")
        
        cursor.close()

if __name__ == "__main__":
    check_table_schemas()
