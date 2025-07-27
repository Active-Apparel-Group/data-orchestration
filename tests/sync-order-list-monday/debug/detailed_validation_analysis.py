#!/usr/bin/env python3
"""
Detailed Validation Bug Analysis - Find exactly what's failing
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
    print("🕵️ DETAILED VALIDATION BUG ANALYSIS")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Get the exact validation query from the test
        test_customer = "GREYSON CLOTHIERS"
        test_po = "4755"
        
        print(f"\n🎯 TEST PARAMETERS:")
        print(f"  Customer: '{test_customer}'")
        print(f"  PO: '{test_po}'")
        
        print(f"\n📋 ALL HEADERS DATA:")
        cursor.execute("""
            SELECT 
                [CUSTOMER NAME],
                [PO NUMBER],
                [AAG ORDER NUMBER],
                action_type,
                sync_state
            FROM ORDER_LIST_V2 
            ORDER BY [CUSTOMER NAME], [PO NUMBER], [AAG ORDER NUMBER]
        """)
        
        all_headers = cursor.fetchall()
        print(f"Total headers: {len(all_headers)}")
        
        customer_counts = {}
        po_counts = {}
        
        for row in all_headers:
            customer, po, order, action_type, sync_state = row
            
            # Count by customer
            if customer not in customer_counts:
                customer_counts[customer] = 0
            customer_counts[customer] += 1
            
            # Count by PO  
            if po not in po_counts:
                po_counts[po] = 0
            po_counts[po] += 1
            
            # Show first few records
            if len(all_headers) <= 10:
                print(f"  {customer} | {po} | {order} | {action_type} | {sync_state}")
        
        print(f"\n📊 CUSTOMER SUMMARY:")
        for customer, count in customer_counts.items():
            print(f"  '{customer}': {count} records")
            
        print(f"\n📊 PO SUMMARY:")  
        for po, count in po_counts.items():
            print(f"  '{po}': {count} records")
        
        print(f"\n🔍 EXACT VALIDATION QUERY:")
        consistency_query = """
            SELECT h.record_uuid, h.[AAG ORDER NUMBER], h.action_type, h.sync_state,
                   COUNT(l.record_uuid) as line_count,
                   SUM(CASE WHEN l.action_type = h.action_type THEN 1 ELSE 0 END) as matching_action_type,
                   SUM(CASE WHEN l.sync_state = h.sync_state THEN 1 ELSE 0 END) as matching_sync_state
            FROM ORDER_LIST_V2 h 
            LEFT JOIN ORDER_LIST_LINES l ON h.record_uuid = l.record_uuid
            WHERE h.[CUSTOMER NAME] = ? AND h.[PO NUMBER] = ?
            GROUP BY h.record_uuid, h.[AAG ORDER NUMBER], h.action_type, h.sync_state
        """
        
        cursor.execute(consistency_query, (test_customer, test_po))
        validation_results = cursor.fetchall()
        
        print(f"Validation query returned: {len(validation_results)} records")
        
        if validation_results:
            print("Records found by validation query:")
            for row in validation_results:
                record_uuid, order_num, action_type, sync_state, line_count, matching_action, matching_sync = row
                print(f"  {order_num} | {action_type} | {sync_state} | Lines: {line_count} | Match A/S: {matching_action}/{matching_sync}")
        else:
            print("❌ VALIDATION QUERY RETURNED NO RESULTS!")
            
            # Check exact matches
            print(f"\n🔍 CHECKING EXACT CUSTOMER MATCH:")
            cursor.execute("SELECT DISTINCT [CUSTOMER NAME] FROM ORDER_LIST_V2")
            customers = cursor.fetchall()
            for (customer,) in customers:
                print(f"  Database: '{customer}'")
                print(f"  Test:     '{test_customer}'")
                print(f"  Match:    {customer == test_customer}")
                
            print(f"\n🔍 CHECKING EXACT PO MATCH:")
            cursor.execute("SELECT DISTINCT [PO NUMBER] FROM ORDER_LIST_V2")
            pos = cursor.fetchall()
            for (po,) in pos:
                print(f"  Database: '{po}' (type: {type(po)})")
                print(f"  Test:     '{test_po}' (type: {type(test_po)})")
                print(f"  Match:    {po == test_po}")
        
        cursor.close()

if __name__ == "__main__":
    main()
