"""
Debug: Check Transform Database State
Purpose: Check if staging tables exist and validate raw tables from Milestone 1
"""
import sys
from pathlib import Path

def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

import db_helper as db

def main():
    print("🔍 CHECKING TRANSFORM DATABASE STATE")
    print("=" * 50)
    
    with db.get_connection('orders') as conn:
        cursor = conn.cursor()
        
        # Check if ORDER_LIST_STAGING exists
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'ORDER_LIST_STAGING'
        """)
        staging_exists = cursor.fetchone()[0]
        print(f"ORDER_LIST_STAGING exists: {bool(staging_exists)}")
        
        # Check if ORDER_LIST_TRANSFORM_ERRORS exists
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'ORDER_LIST_TRANSFORM_ERRORS'
        """)
        errors_exists = cursor.fetchone()[0]
        print(f"ORDER_LIST_TRANSFORM_ERRORS exists: {bool(errors_exists)}")
        
        # List all raw tables
        cursor.execute("""
            SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME LIKE 'x%_ORDER_LIST_RAW'
            ORDER BY TABLE_NAME
        """)
        raw_tables = [row[0] for row in cursor.fetchall()]
        print(f"\nRaw tables found: {len(raw_tables)}")
        for i, table in enumerate(raw_tables):
            if i < 10:  # Show first 10
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  - {table}: {count:,} rows")
            elif i == 10:
                print(f"  ... and {len(raw_tables) - 10} more tables")
                break
        
        # Check if stored procedure exists
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.ROUTINES 
            WHERE ROUTINE_NAME = 'TransformOrderListTables' 
            AND ROUTINE_TYPE = 'PROCEDURE'
        """)
        proc_exists = cursor.fetchone()[0]
        print(f"\nTransformOrderListTables procedure exists: {bool(proc_exists)}")
        
        print("\n✅ Database state check complete")

if __name__ == "__main__":
    main()
