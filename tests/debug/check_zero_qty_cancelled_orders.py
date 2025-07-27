#!/usr/bin/env python3
"""
Check Zero Quantity and Cancelled Orders - Task 19.14.3 Debug
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
    print("🧪 Checking Zero Quantity and Cancelled Orders...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Check headers without lines - should be zero qty or cancelled
        print("\n📊 Headers without corresponding lines:")
        query = """
        SELECT 
            h.[AAG ORDER NUMBER],
            h.[CUSTOMER NAME],
            h.[PO NUMBER],
            h.[ORDER TYPE],
            h.[TOTAL QTY],
            CASE 
                WHEN h.[TOTAL QTY] = 0 THEN 'ZERO_QTY'
                WHEN h.[ORDER TYPE] = 'CANCELLED' THEN 'CANCELLED'
                ELSE 'OTHER'
            END as reason_no_lines
        FROM ORDER_LIST_V2 h
        LEFT JOIN ORDER_LIST_LINES l ON h.record_uuid = l.record_uuid
        WHERE l.record_uuid IS NULL
        AND h.[CUSTOMER NAME] = 'GREYSON CLOTHIERS' 
        AND h.[PO NUMBER] = '4755'
        ORDER BY h.[AAG ORDER NUMBER]
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        zero_qty_count = 0
        cancelled_count = 0
        other_count = 0
        
        for row in results:
            aag_order, customer, po, order_type, total_qty, reason = row
            print(f"  {aag_order}: {order_type}, Total QTY: {total_qty}, Reason: {reason}")
            
            if reason == 'ZERO_QTY':
                zero_qty_count += 1
            elif reason == 'CANCELLED':
                cancelled_count += 1
            else:
                other_count += 1
        
        print(f"\n📈 Summary:")
        print(f"  Headers without lines: {len(results)}")
        print(f"  Zero quantity: {zero_qty_count}")
        print(f"  Cancelled orders: {cancelled_count}")
        print(f"  Other reasons: {other_count}")
        
        # Verify total counts
        print(f"\n🔍 Verification:")
        cursor.execute("SELECT COUNT(*) FROM ORDER_LIST_V2 WHERE [CUSTOMER NAME] = 'GREYSON CLOTHIERS' AND [PO NUMBER] = '4755'")
        total_headers = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(DISTINCT h.record_uuid) 
            FROM ORDER_LIST_V2 h
            JOIN ORDER_LIST_LINES l ON h.record_uuid = l.record_uuid
            WHERE h.[CUSTOMER NAME] = 'GREYSON CLOTHIERS' AND h.[PO NUMBER] = '4755'
        """)
        headers_with_lines = cursor.fetchone()[0]
        
        print(f"  Total headers: {total_headers}")
        print(f"  Headers with lines: {headers_with_lines}")
        print(f"  Headers without lines: {total_headers - headers_with_lines}")
        
        if zero_qty_count + cancelled_count == (total_headers - headers_with_lines):
            print("  ✅ All headers without lines are zero qty or cancelled!")
        else:
            print("  ❌ Some headers without lines are not zero qty or cancelled!")
        
        cursor.close()

if __name__ == "__main__":
    main()
