#!/usr/bin/env python3
"""
Check sync status and validate Monday.com item creation success
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
    print("🔍 Checking Sync Status and Monday.com Creation Success...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        print("\n📊 Sync Status Analysis:")
        
        # 1. Check sync_state distribution
        query = """
        SELECT 
            sync_state,
            COUNT(*) as count
        FROM FACT_ORDER_LIST 
        WHERE monday_item_id IS NOT NULL
        GROUP BY sync_state
        ORDER BY count DESC
        """
        cursor.execute(query)
        sync_states = cursor.fetchall()
        print("  Sync State Distribution:")
        for state, count in sync_states:
            print(f"    {state}: {count} records")
        
        # 2. Check for any failed creations or missing IDs
        query = """
        SELECT 
            sync_state,
            monday_item_id,
            [CUSTOMER NAME],
            [PO NUMBER],
            [AAG ORDER NUMBER]
        FROM FACT_ORDER_LIST 
        WHERE monday_item_id IS NULL OR sync_state != 'COMPLETED'
        ORDER BY [AAG ORDER NUMBER]
        """
        cursor.execute(query)
        failed_records = cursor.fetchall()
        print(f"\n  Records without Monday IDs or incomplete sync: {len(failed_records)}")
        if failed_records:
            for state, monday_id, customer, po, aag_order in failed_records[:10]:
                print(f"    {customer} - {aag_order}: {state} (Monday ID: {monday_id})")
        
        # 3. Check Monday item IDs to see if they look valid
        query = """
        SELECT 
            monday_item_id,
            [CUSTOMER NAME],
            [PO NUMBER],
            [AAG ORDER NUMBER],
            sync_state
        FROM FACT_ORDER_LIST 
        WHERE monday_item_id IS NOT NULL
        ORDER BY CAST(monday_item_id AS BIGINT)
        """
        cursor.execute(query)
        monday_records = cursor.fetchall()
        print(f"\n📋 Monday Item ID Analysis:")
        print(f"  Total records with Monday IDs: {len(monday_records)}")
        
        # Show first and last few IDs to check range
        if monday_records:
            print("  First 5 Monday IDs:")
            for monday_id, customer, po, aag_order, state in monday_records[:5]:
                print(f"    {monday_id}: {customer} - {aag_order} ({state})")
            
            print("  Last 5 Monday IDs:")
            for monday_id, customer, po, aag_order, state in monday_records[-5:]:
                print(f"    {monday_id}: {customer} - {aag_order} ({state})")
        
        # 4. Check if the Monday IDs are in the expected range for the production board
        query = """
        SELECT 
            MIN(CAST(monday_item_id AS BIGINT)) as min_id,
            MAX(CAST(monday_item_id AS BIGINT)) as max_id,
            COUNT(DISTINCT monday_item_id) as unique_count
        FROM FACT_ORDER_LIST 
        WHERE monday_item_id IS NOT NULL
        """
        cursor.execute(query)
        id_range = cursor.fetchone()
        min_id, max_id, unique_count = id_range
        print(f"\n🔢 Monday ID Range Analysis:")
        print(f"  Minimum ID: {min_id}")
        print(f"  Maximum ID: {max_id}")
        print(f"  Unique IDs: {unique_count}")
        print(f"  ID Range Span: {max_id - min_id}")
        
        # 5. Check for any pattern in the 2 missing headers (if 67 vs 69)
        # Let's see if any items might not have been created in Monday
        query = """
        SELECT 
            [AAG ORDER NUMBER],
            monday_item_id,
            sync_state,
            [TOTAL QTY],
            [CUSTOMER STYLE]
        FROM FACT_ORDER_LIST 
        WHERE monday_item_id IS NOT NULL
        ORDER BY [AAG ORDER NUMBER]
        """
        cursor.execute(query)
        all_records = cursor.fetchall()
        
        print(f"\n🎯 Key Insight:")
        print(f"  Database shows {len(all_records)} records with Monday IDs")
        print(f"  You report only 67 headers visible in Monday.com")
        print(f"  Discrepancy: {len(all_records) - 67} records")
        
        if len(all_records) == 69 and len(all_records) - 67 == 2:
            print(f"\n🔍 Investigating the 2 'missing' headers...")
            print(f"  Possible explanations:")
            print(f"    1. Items created but not visible (permissions/filters)")
            print(f"    2. Items created in wrong board or group")
            print(f"    3. API returned success but creation actually failed")
            print(f"    4. Items archived or moved after creation")
        
        cursor.close()

if __name__ == "__main__":
    main()
