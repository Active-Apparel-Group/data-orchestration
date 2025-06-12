#!/usr/bin/env python3
"""
Quick debug script to check RHYTHM order data structure
"""
import sys
import pandas as pd
from pathlib import Path

# Add the src directory to Python path for module imports
script_dir = Path(__file__).parent
src_dir = script_dir / "src"
sys.path.insert(0, str(src_dir))

from audit_pipeline.config import load_env, run_sql

def check_rhythm_data():
    print("=== Checking RHYTHM Data Structure ===")
    
    # Load environment
    load_env()
    
    # Check master order list for RHYTHM with PO 19200
    print("Checking master order list...")
    try:
        query = """
        SELECT DISTINCT 
            "CUSTOMER PO", 
            CUSTOMER,
            STYLE,
            "ALIAS/RELATED ITEM",
            COLOR,
            SIZE,
            "UNIT OF MEASURE"
        FROM master_order_list 
        WHERE CUSTOMER LIKE '%RHYTHM%' AND "CUSTOMER PO" = '19200'
        LIMIT 10
        """
        orders = run_sql(query)
        
        if len(orders) > 0:
            print(f"✅ Found {len(orders)} RHYTHM orders for PO 19200")
            print("Columns:", list(orders.columns))
            print("\nSample records:")
            print(orders)
            
            # Check if CLA24SW-BB04-BLK appears in ALIAS/RELATED ITEM
            if 'ALIAS/RELATED ITEM' in orders.columns:
                matching_alias = orders[orders['ALIAS/RELATED ITEM'].str.contains('CLA24SW-BB04-BLK', na=False)]
                print(f"\nRecords with CLA24SW-BB04-BLK in ALIAS/RELATED ITEM: {len(matching_alias)}")
                if len(matching_alias) > 0:
                    print(matching_alias[['CUSTOMER PO', 'ALIAS/RELATED ITEM', 'COLOR']])
        else:
            print("❌ No RHYTHM orders found for PO 19200")
            
            # Try broader search
            all_rhythm = run_sql("SELECT DISTINCT \"CUSTOMER PO\", CUSTOMER FROM master_order_list WHERE CUSTOMER LIKE '%RHYTHM%' LIMIT 10")
            print(f"Found {len(all_rhythm)} total RHYTHM records with POs:")
            print(all_rhythm)
            
    except Exception as e:
        print(f"❌ Error querying master order list: {e}")
    
    # Check shipped data structure
    print("\n=== Checking Shipped Data ===")
    try:
        shipped_query = """
        SELECT DISTINCT 
            "Customer PO",
            Customer,
            Style,
            Color,
            Size
        FROM shipped 
        WHERE Customer LIKE '%RHYTHM%' AND "Customer PO" = '19200'
        LIMIT 5
        """
        shipped = run_sql(shipped_query)
        
        if len(shipped) > 0:
            print(f"✅ Found {len(shipped)} shipped records for RHYTHM PO 19200")
            print("Columns:", list(shipped.columns))
            print(shipped)
        else:
            print("❌ No shipped records found for RHYTHM PO 19200")
            
    except Exception as e:
        print(f"❌ Error querying shipped: {e}")

if __name__ == "__main__":
    check_rhythm_data()
