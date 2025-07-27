#!/usr/bin/env python3
"""Debug hash column issue"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def main():
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)

    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        print("🔍 Checking v_order_list_nulls_to_delete records...")
        cursor.execute("SELECT TOP 3 record_uuid, hash_ord_3_10, [CUSTOMER NAME], [PO NUMBER] FROM [v_order_list_nulls_to_delete]")
        records = cursor.fetchall()
        
        print(f"Records to delete: {len(records)}")
        for i, (uuid, hash_val, customer, po) in enumerate(records):
            print(f"  {i+1}. UUID: {uuid}")
            print(f"      Hash: {hash_val}")
            print(f"      Customer: {customer}")
            print(f"      PO: {po}")
            print()
        
        # Check if these are the problematic nulls we want to delete
        print("🔍 Checking if these are truly null records...")
        cursor.execute("""
        SELECT TOP 3 
            [CUSTOMER NAME], 
            [PO NUMBER], 
            [CUSTOMER STYLE], 
            [TOTAL QTY],
            hash_ord_3_10
        FROM [v_order_list_nulls_to_delete]
        """)
        
        null_records = cursor.fetchall()
        for i, (customer, po, style, qty, hash_val) in enumerate(null_records):
            print(f"  {i+1}. Customer: {customer}")
            print(f"      PO: {po}")
            print(f"      Style: {style}")
            print(f"      Total QTY: {qty}")
            print(f"      Hash: {hash_val}")
            print()
        
        cursor.close()

if __name__ == "__main__":
    main()
