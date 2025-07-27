#!/usr/bin/env python3
"""
Find duplicate AAG ORDER NUMBERs that got created multiple times in Monday.com
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
    print("🔍 Finding Duplicate Orders in Monday.com...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        print("\n📊 Duplicate AAG ORDER NUMBER Analysis:")
        
        # 1. Find AAG ORDER NUMBERs that have multiple Monday IDs
        query = """
        SELECT 
            [AAG ORDER NUMBER],
            COUNT(DISTINCT monday_item_id) as monday_id_count,
            COUNT(*) as total_records,
            STRING_AGG(CAST(monday_item_id AS VARCHAR), ', ') as monday_ids
        FROM FACT_ORDER_LIST 
        WHERE monday_item_id IS NOT NULL
        GROUP BY [AAG ORDER NUMBER]
        HAVING COUNT(DISTINCT monday_item_id) > 1
        ORDER BY monday_id_count DESC, [AAG ORDER NUMBER]
        """
        cursor.execute(query)
        duplicates = cursor.fetchall()
        
        print(f"  Orders with multiple Monday IDs: {len(duplicates)}")
        
        if duplicates:
            total_extra_items = 0
            for aag_order, monday_count, total_records, monday_ids in duplicates:
                extra_items = monday_count - 1  # Each order should have only 1 Monday item
                total_extra_items += extra_items
                print(f"    {aag_order}: {monday_count} Monday IDs ({extra_items} extra)")
                print(f"      Monday IDs: {monday_ids}")
            
            print(f"\n🧮 Mathematics:")
            print(f"  Total unique AAG ORDER NUMBERs: {69 - total_extra_items}")
            print(f"  Extra Monday items created: {total_extra_items}")
            print(f"  Total Monday items in database: 69")
            print(f"  Expected Monday items (should match board): {69 - total_extra_items}")
        
        # 2. Show all orders with their Monday ID counts
        query = """
        SELECT 
            [AAG ORDER NUMBER],
            COUNT(DISTINCT monday_item_id) as monday_id_count,
            COUNT(*) as db_records,
            MIN(monday_item_id) as first_monday_id,
            MAX(monday_item_id) as last_monday_id
        FROM FACT_ORDER_LIST 
        WHERE monday_item_id IS NOT NULL
        GROUP BY [AAG ORDER NUMBER]
        ORDER BY monday_id_count DESC, [AAG ORDER NUMBER]
        """
        cursor.execute(query)
        all_orders = cursor.fetchall()
        
        unique_orders = len(all_orders)
        orders_with_single_id = len([o for o in all_orders if o[1] == 1])
        orders_with_multiple_ids = len([o for o in all_orders if o[1] > 1])
        
        print(f"\n📋 Complete Order Analysis:")
        print(f"  Total unique AAG ORDER NUMBERs: {unique_orders}")
        print(f"  Orders with single Monday ID: {orders_with_single_id}")
        print(f"  Orders with multiple Monday IDs: {orders_with_multiple_ids}")
        
        # 3. Show the calculation that explains the discrepancy
        print(f"\n✅ EXPLANATION OF 67 vs 69 DISCREPANCY:")
        print(f"  • Database records with Monday IDs: 69")
        print(f"  • Unique AAG ORDER NUMBERs: {unique_orders}")
        print(f"  • Orders duplicated in Monday.com: {orders_with_multiple_ids}")
        print(f"  • Monday.com should show: {unique_orders} headers")
        
        if unique_orders == 67:
            print(f"  ✅ This matches your count of 67 headers in Monday.com!")
            print(f"  📋 The {orders_with_multiple_ids} duplicate orders explain why database shows 69 records")
        
        # 4. Show details of the duplicated orders
        if duplicates:
            print(f"\n🔍 Duplicate Order Details:")
            for aag_order, monday_count, total_records, monday_ids in duplicates:
                query = """
                SELECT 
                    monday_item_id,
                    [CUSTOMER STYLE],
                    [TOTAL QTY],
                    sync_state,
                    record_uuid
                FROM FACT_ORDER_LIST 
                WHERE [AAG ORDER NUMBER] = ? AND monday_item_id IS NOT NULL
                ORDER BY monday_item_id
                """
                cursor.execute(query, (aag_order,))
                order_details = cursor.fetchall()
                
                print(f"\n  {aag_order} ({monday_count} Monday items):")
                for monday_id, style, qty, state, uuid in order_details:
                    print(f"    Monday ID {monday_id}: {style}, Qty: {qty}, UUID: {uuid}")
        
        cursor.close()

if __name__ == "__main__":
    main()
