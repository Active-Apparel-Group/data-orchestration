#!/usr/bin/env python3
"""
Debug Post-SQL Validation Issue
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

def main():
    print("🔍 DEBUGGING POST-SQL VALIDATION:")
    print()
    
    # Config and connection
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)

    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Check what's in source table
        cursor.execute("SELECT COUNT(*), COUNT(DISTINCT CUSTOMER), COUNT(DISTINCT [CUSTOMER PO]) FROM swp_ORDER_LIST_SYNC")
        row = cursor.fetchone()
        print(f"Source table: {row[0]} total records, {row[1]} customers, {row[2]} POs")
        
        # Check customers specifically
        cursor.execute("""
            SELECT CUSTOMER, [CUSTOMER PO], COUNT(*) as records
            FROM swp_ORDER_LIST_SYNC 
            WHERE CUSTOMER IN ('ACTIVELY BLACK', 'AESCAPE')
            GROUP BY CUSTOMER, [CUSTOMER PO]
            ORDER BY CUSTOMER, [CUSTOMER PO]
        """)
        print("\nCustomer/PO breakdown:")
        for row in cursor.fetchall():
            print(f"  {row[0]} PO {row[1]}: {row[2]} records")
        
        # Check what the validation query is actually looking for
        cursor.execute("""
            SELECT COUNT(*) as processed_records
            FROM swp_ORDER_LIST_SYNC 
            WHERE CUSTOMER IN ('ACTIVELY BLACK', 'AESCAPE')
            AND [CUSTOMER PO] IN ('AB0001', '1191')
        """)
        result = cursor.fetchone()[0]
        print(f"\n🎯 Validation query result: {result} processed records")
        
        # Check if there are any records at all
        cursor.execute("SELECT TOP 3 CUSTOMER, [CUSTOMER PO] FROM swp_ORDER_LIST_SYNC")
        print("\nSample records:")
        for row in cursor.fetchall():
            print(f"  Customer: {row[0]}, PO: {row[1]}")
        
        # Check for data type issues
        cursor.execute("""
            SELECT CUSTOMER, [CUSTOMER PO], COUNT(*) as records
            FROM swp_ORDER_LIST_SYNC 
            GROUP BY CUSTOMER, [CUSTOMER PO]
            ORDER BY CUSTOMER, [CUSTOMER PO]
        """)
        print("\nAll Customer/PO combinations:")
        for row in cursor.fetchall():
            print(f"  '{row[0]}' PO '{row[1]}': {row[2]} records")
        
        cursor.close()

if __name__ == "__main__":
    main()
