#!/usr/bin/env python3
"""
Check Validation Bug - Analyze why Task 19.14.3 validation is failing
"""

import sys
from pathlib import Path

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def main():
    print("🔍 Checking Validation Bug...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        print("\n📊 DATASET ANALYSIS:")
        print("=" * 50)
        
        # Check all records in ORDER_LIST_V2
        cursor.execute("""
            SELECT 
                [CUSTOMER NAME],
                [PO NUMBER],
                COUNT(*) as record_count,
                STRING_AGG(CAST([AAG ORDER NUMBER] AS VARCHAR), ', ') as order_numbers
            FROM ORDER_LIST_V2 
            GROUP BY [CUSTOMER NAME], [PO NUMBER]
            ORDER BY COUNT(*) DESC
        """)
        
        all_records = cursor.fetchall()
        print(f"All customer/PO combinations in ORDER_LIST_V2:")
        total_records = 0
        for row in all_records:
            customer, po, count, orders = row
            total_records += count
            print(f"  {customer} | PO: {po} | Records: {count}")
            if count <= 3:  # Show order numbers for small groups
                print(f"    Orders: {orders}")
        
        print(f"\nTotal records in ORDER_LIST_V2: {total_records}")
        
        print("\n🎯 VALIDATION FILTER TEST:")
        print("=" * 50)
        
        # Check what the validation query actually finds
        cursor.execute("""
            SELECT 
                COUNT(*) as total_count,
                SUM(CASE WHEN action_type IS NOT NULL THEN 1 ELSE 0 END) as action_type_count,
                SUM(CASE WHEN sync_state IS NOT NULL THEN 1 ELSE 0 END) as sync_state_count
            FROM ORDER_LIST_V2 
            WHERE [CUSTOMER NAME] = 'GREYSON' 
            AND [PO NUMBER] = '4755'
        """)
        
        validation_result = cursor.fetchone()
        if validation_result:
            total, action_type, sync_state = validation_result
            print(f"GREYSON + PO 4755 records: {total}")
            print(f"  action_type populated: {action_type}/{total}")
            print(f"  sync_state populated: {sync_state}/{total}")
        
        print("\n🔍 ALL RECORDS CHECK:")
        print("=" * 50)
        
        # Check all records without filter
        cursor.execute("""
            SELECT 
                COUNT(*) as total_count,
                SUM(CASE WHEN action_type IS NOT NULL THEN 1 ELSE 0 END) as action_type_count,
                SUM(CASE WHEN sync_state IS NOT NULL THEN 1 ELSE 0 END) as sync_state_count
            FROM ORDER_LIST_V2
        """)
        
        all_result = cursor.fetchone()
        if all_result:
            total, action_type, sync_state = all_result
            print(f"ALL records: {total}")
            print(f"  action_type populated: {action_type}/{total}")
            print(f"  sync_state populated: {sync_state}/{total}")
        
        print("\n📋 LINES TABLE CHECK:")
        print("=" * 50)
        
        # Check lines table
        cursor.execute("""
            SELECT 
                COUNT(*) as total_lines,
                COUNT(DISTINCT record_uuid) as unique_records,
                SUM(CASE WHEN action_type IS NOT NULL THEN 1 ELSE 0 END) as action_type_count,
                SUM(CASE WHEN sync_state IS NOT NULL THEN 1 ELSE 0 END) as sync_state_count
            FROM ORDER_LIST_LINES
        """)
        
        lines_result = cursor.fetchone()
        if lines_result:
            total_lines, unique_records, action_type, sync_state = lines_result
            print(f"Total lines: {total_lines}")
            print(f"Unique records: {unique_records}")
            print(f"  action_type populated: {action_type}/{total_lines}")
            print(f"  sync_state populated: {sync_state}/{total_lines}")
        
        print("\n💡 DIAGNOSIS:")
        print("=" * 50)
        print("The validation is filtering by GREYSON + PO 4755, but:")
        print("1. The merge processed ALL 69 records")
        print("2. The validation only checks a subset")
        print("3. This causes the 'sync consistency' check to fail")
        print("\nSOLUTION: Update validation to check ALL records, not just test subset!")
        
        cursor.close()

if __name__ == "__main__":
    main()
