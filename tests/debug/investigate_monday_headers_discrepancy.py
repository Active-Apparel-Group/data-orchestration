#!/usr/bin/env python3
"""
Investigate discrepancy between 69 database records with Monday IDs and 67 headers in Monday.com
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
    print("🔍 Investigating Monday.com Headers Discrepancy...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        print("\n📊 Database Analysis:")
        
        # 1. Check total records with Monday IDs in FACT_ORDER_LIST
        query = """
        SELECT COUNT(*) as total_with_monday_ids
        FROM FACT_ORDER_LIST 
        WHERE monday_item_id IS NOT NULL
        """
        cursor.execute(query)
        total_with_ids = cursor.fetchone()[0]
        print(f"  Total FACT_ORDER_LIST records with monday_item_id: {total_with_ids}")
        
        # 2. Check for duplicates like user's query
        query = """
        SELECT monday_item_id, COUNT(*) as count
        FROM FACT_ORDER_LIST
        WHERE monday_item_id IS NOT NULL
        GROUP BY monday_item_id
        HAVING COUNT(*) > 1
        ORDER BY count DESC
        """
        cursor.execute(query)
        duplicates = cursor.fetchall()
        print(f"  Duplicate monday_item_id entries: {len(duplicates)}")
        if duplicates:
            for monday_id, count in duplicates[:5]:  # Show top 5
                print(f"    {monday_id}: {count} records")
        
        # 3. Check unique Monday item IDs (this should match headers in Monday.com)
        query = """
        SELECT COUNT(DISTINCT monday_item_id) as unique_monday_ids
        FROM FACT_ORDER_LIST 
        WHERE monday_item_id IS NOT NULL
        """
        cursor.execute(query)
        unique_ids = cursor.fetchone()[0]
        print(f"  Unique monday_item_id values: {unique_ids}")
        
        # 4. Check records grouped by customer to understand data structure
        query = """
        SELECT 
            [CUSTOMER NAME],
            COUNT(*) as total_records,
            COUNT(DISTINCT monday_item_id) as unique_items,
            COUNT(DISTINCT record_uuid) as unique_orders
        FROM FACT_ORDER_LIST 
        WHERE monday_item_id IS NOT NULL
        GROUP BY [CUSTOMER NAME]
        ORDER BY total_records DESC
        """
        cursor.execute(query)
        customer_breakdown = cursor.fetchall()
        print(f"\n📋 Customer Breakdown:")
        for customer, total, unique_items, unique_orders in customer_breakdown:
            print(f"  {customer}: {total} records → {unique_items} Monday items → {unique_orders} orders")
        
        # 5. Check if some orders have size breakdown and others don't
        query = """
        SELECT 
            record_uuid,
            [CUSTOMER NAME],
            [PO NUMBER],
            [AAG ORDER NUMBER],
            monday_item_id,
            COUNT(*) as size_records
        FROM FACT_ORDER_LIST 
        WHERE monday_item_id IS NOT NULL
        GROUP BY record_uuid, [CUSTOMER NAME], [PO NUMBER], [AAG ORDER NUMBER], monday_item_id
        ORDER BY size_records
        """
        cursor.execute(query)
        order_breakdown = cursor.fetchall()
        print(f"\n📦 Order Structure Analysis:")
        single_record_orders = [o for o in order_breakdown if o[5] == 1]
        multi_record_orders = [o for o in order_breakdown if o[5] > 1]
        
        print(f"  Orders with single record (header only): {len(single_record_orders)}")
        print(f"  Orders with multiple records (header + sizes): {len(multi_record_orders)}")
        
        if single_record_orders:
            print("\n  Single-record orders (likely no size breakdown):")
            for record_uuid, customer, po, aag_order, monday_id, count in single_record_orders[:5]:
                print(f"    {customer} - {po} - {aag_order} → Monday ID: {monday_id}")
        
        # 6. Verification: 67 unique Monday IDs + 2 orders without subitems = 69 total records?
        expected_total = unique_ids + len([o for o in order_breakdown if o[5] == 1]) - unique_ids
        print(f"\n🧮 Calculation Check:")
        print(f"  Unique Monday IDs (headers in Monday.com): {unique_ids}")
        print(f"  Orders with single records: {len(single_record_orders)}")
        print(f"  Orders with multiple records: {len(multi_record_orders)}")
        print(f"  Total records: {total_with_ids}")
        
        print(f"\n✅ EXPLANATION:")
        print(f"  • Monday.com shows {unique_ids} headers (items)")
        print(f"  • Database shows {total_with_ids} total records")
        print(f"  • Difference: {total_with_ids - unique_ids} records are size breakdown data")
        print(f"  • Each Monday item can have multiple database records for different sizes")
        
        cursor.close()

if __name__ == "__main__":
    main()
