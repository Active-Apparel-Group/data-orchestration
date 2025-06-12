#!/usr/bin/env python3
"""
Simple check of RHYTHM order vs shipped data
"""
import sys
import pandas as pd
from pathlib import Path

# Add the src directory to Python path
script_dir = Path(__file__).parent
src_dir = script_dir / "src"
sys.path.insert(0, str(src_dir))

def simple_rhythm_check():
    print("=== Simple RHYTHM Data Check ===")
    
    try:
        from audit_pipeline.config import load_env, get_connection
        import pandas as pd
        load_env()
        
        # Helper function to execute raw SQL
        def execute_raw_sql(query, db_key):
            with get_connection(db_key) as conn:
                return pd.read_sql(query, conn)
        
        print("1. Checking shipped data for RHYTHM PO 19200...")
        shipped_check = execute_raw_sql("""
            SELECT "Customer PO", Style, Color, Size, COUNT(*) as count
            FROM shipped 
            WHERE Customer LIKE '%RHYTHM%' AND "Customer PO" = '19200' AND Style LIKE '%CLA24SW-BB04-BLK%'
            GROUP BY "Customer PO", Style, Color, Size
            ORDER BY count DESC
            LIMIT 5
        """, 'wah')
        print(f"Found {len(shipped_check)} shipped record groups:")
        print(shipped_check)
        
        print("\n2. Checking order data for RHYTHM...")
        order_check = execute_raw_sql("""
            SELECT "CUSTOMER PO", "ALIAS/RELATED ITEM", COLOR, 
                   CASE WHEN "ALIAS/RELATED ITEM" LIKE '%CLA24SW-BB04-BLK%' THEN 'MATCH' ELSE 'NO_MATCH' END as has_cla
            FROM master_order_list 
            WHERE CUSTOMER LIKE '%RHYTHM%' AND "CUSTOMER PO" = '19200'
            LIMIT 10
        """, 'orders')
        print(f"Found {len(order_check)} order records:")
        print(order_check)
        
        if len(order_check) > 0:
            matches = order_check[order_check['has_cla'] == 'MATCH']
            print(f"\nOrder records with CLA24SW-BB04-BLK: {len(matches)}")
            if len(matches) > 0:
                print(matches)
        
        print("\n3. Summary:")
        print(f"   - Shipped records for PO 19200: {len(shipped_check)}")
        print(f"   - Order records for PO 19200: {len(order_check)}")
        if len(order_check) > 0:
            matches = order_check[order_check['has_cla'] == 'MATCH']
            print(f"   - Order records with expected style: {len(matches)}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    simple_rhythm_check()
