#!/usr/bin/env python3
"""
Check Zero Quantity and Cancelled Orders - Task 19.14.3 Fix
===========================================================
Check if headers without lines have [TOTAL QTY] = 0 or [ORDER_TYPE] = 'CANCELLED'
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def main():
    print("🔍 Checking Zero Quantity and Cancelled Orders...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list_development.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # 1. Check all headers
        cursor.execute("""
        SELECT 
            [AAG ORDER NUMBER],
            [CUSTOMER NAME],
            [PO NUMBER],
            [ORDER_TYPE],
            [TOTAL QTY],
            CASE 
                WHEN [TOTAL QTY] = 0 THEN 'ZERO_QTY'
                WHEN [ORDER_TYPE] = 'CANCELLED' THEN 'CANCELLED'
                ELSE 'NORMAL'
            END as status
        FROM ORDER_LIST_V2
        WHERE [CUSTOMER NAME] = 'GREYSON CLOTHIERS' AND [PO NUMBER] = '4755'
        ORDER BY [AAG ORDER NUMBER]
        """)
        
        headers = cursor.fetchall()
        print(f"\n📊 All Headers Analysis ({len(headers)} total):")
        
        zero_qty_count = 0
        cancelled_count = 0
        normal_count = 0
        
        for header in headers:
            aag_order, customer, po, order_type, total_qty, status = header
            print(f"  {aag_order}: {order_type} | QTY={total_qty} | Status={status}")
            
            if status == 'ZERO_QTY':
                zero_qty_count += 1
            elif status == 'CANCELLED':
                cancelled_count += 1
            else:
                normal_count += 1
        
        print(f"\n📈 Summary:")
        print(f"  Zero Quantity: {zero_qty_count}")
        print(f"  Cancelled: {cancelled_count}")
        print(f"  Normal: {normal_count}")
        print(f"  Total: {len(headers)}")
        
        # 2. Check headers without lines
        cursor.execute("""
        SELECT 
            h.[AAG ORDER NUMBER],
            h.[ORDER_TYPE],
            h.[TOTAL QTY],
            CASE 
                WHEN h.[TOTAL QTY] = 0 THEN 'ZERO_QTY'
                WHEN h.[ORDER_TYPE] = 'CANCELLED' THEN 'CANCELLED'
                ELSE 'NORMAL'
            END as status
        FROM ORDER_LIST_V2 h
        LEFT JOIN ORDER_LIST_LINES l ON h.record_uuid = l.record_uuid
        WHERE h.[CUSTOMER NAME] = 'GREYSON CLOTHIERS' 
        AND h.[PO NUMBER] = '4755'
        AND l.record_uuid IS NULL
        ORDER BY h.[AAG ORDER NUMBER]
        """)
        
        headers_without_lines = cursor.fetchall()
        print(f"\n🚫 Headers WITHOUT Lines ({len(headers_without_lines)} total):")
        
        if headers_without_lines:
            zero_no_lines = 0
            cancelled_no_lines = 0
            normal_no_lines = 0
            
            for header in headers_without_lines:
                aag_order, order_type, total_qty, status = header
                print(f"  {aag_order}: {order_type} | QTY={total_qty} | Status={status}")
                
                if status == 'ZERO_QTY':
                    zero_no_lines += 1
                elif status == 'CANCELLED':
                    cancelled_no_lines += 1
                else:
                    normal_no_lines += 1
            
            print(f"\n🎯 Headers Without Lines Analysis:")
            print(f"  Zero Quantity: {zero_no_lines}")
            print(f"  Cancelled: {cancelled_no_lines}")
            print(f"  Normal (Should have lines): {normal_no_lines}")
            
            if normal_no_lines == 0:
                print("✅ ALL headers without lines are either ZERO QTY or CANCELLED - This is CORRECT!")
            else:
                print("❌ Some normal orders don't have lines - This needs investigation!")
        else:
            print("✅ All headers have lines!")
        
        # 3. Check headers with lines
        cursor.execute("""
        SELECT 
            h.[AAG ORDER NUMBER],
            h.[ORDER_TYPE],
            h.[TOTAL QTY],
            COUNT(l.line_uuid) as line_count
        FROM ORDER_LIST_V2 h
        JOIN ORDER_LIST_LINES l ON h.record_uuid = l.record_uuid
        WHERE h.[CUSTOMER NAME] = 'GREYSON CLOTHIERS' 
        AND h.[PO NUMBER] = '4755'
        GROUP BY h.[AAG ORDER NUMBER], h.[ORDER_TYPE], h.[TOTAL QTY]
        ORDER BY h.[AAG ORDER NUMBER]
        """)
        
        headers_with_lines = cursor.fetchall()
        print(f"\n✅ Headers WITH Lines ({len(headers_with_lines)} total):")
        
        for header in headers_with_lines[:5]:  # Show first 5
            aag_order, order_type, total_qty, line_count = header
            print(f"  {aag_order}: {order_type} | QTY={total_qty} | Lines={line_count}")
        
        if len(headers_with_lines) > 5:
            print(f"  ... and {len(headers_with_lines) - 5} more")
        
        cursor.close()
        
        print(f"\n🎯 CONCLUSION:")
        print(f"  Total headers: {len(headers)}")
        print(f"  Headers with lines: {len(headers_with_lines)}")
        print(f"  Headers without lines: {len(headers_without_lines)}")
        print(f"  Expected validation: {len(headers_with_lines)}/{len(headers)} should match")

if __name__ == "__main__":
    main()
