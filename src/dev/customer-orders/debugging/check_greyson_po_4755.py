#!/usr/bin/env python3
"""
Check for GREYSON PO 4755 data availability
"""

import sys
from pathlib import Path

# Standard import pattern - use this in ALL scripts
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

# Import from utils/ - PRODUCTION PATTERN
import db_helper as db

def check_greyson_po_4755():
    print("=" * 60)
    print("GREYSON PO 4755 DATA AVAILABILITY CHECK")
    print("=" * 60)
    
    # Check for GREYSON PO 4755 in ORDERS_UNIFIED
    greyson_query = """
    SELECT 
        [CUSTOMER NAME],
        [PO NUMBER],
        [AAG ORDER NUMBER],
        [STYLE],
        [COLOR],
        [TOTAL QTY],
        [ORDER DATE PO RECEIVED]
    FROM ORDERS_UNIFIED 
    WHERE [CUSTOMER NAME] like 'GREYSON%' 
      AND [PO NUMBER] = '4755'
    ORDER BY [AAG ORDER NUMBER]
    """
    
    print("\n1. CHECKING ORDERS_UNIFIED FOR GREYSON PO 4755")
    print("-" * 50)
    try:
        results = db.run_query("ORDERS", greyson_query)
        if not results.empty:
            print(f"   ✅ Found {len(results)} records for GREYSON PO 4755")
            print("\n   📊 Sample data:")
            for _, row in results.head(5).iterrows():
                print(f"   • Order: {row['AAG ORDER NUMBER']}")
                print(f"     Style: {row['STYLE']} - {row['COLOR']}")
                print(f"     Qty: {row['TOTAL QTY']}")
                print(f"     Date: {row['ORDER DATE PO RECEIVED']}")
                print()
        else:
            print("   ❌ No records found for GREYSON PO 4755")
            
            # Check for any GREYSON records
            any_greyson_query = """
            SELECT DISTINCT [PO NUMBER], COUNT(*) as record_count
            FROM ORDERS_UNIFIED 
            WHERE [CUSTOMER NAME] = 'GREYSON'
            GROUP BY [PO NUMBER]
            ORDER BY COUNT(*) DESC
            """
            
            print("\n   🔍 Available GREYSON PO Numbers:")
            greyson_pos = db.run_query("ORDERS", any_greyson_query)
            if not greyson_pos.empty:
                for _, row in greyson_pos.head(10).iterrows():
                    print(f"   • PO {row['PO NUMBER']}: {row['record_count']} orders")
            else:
                print("   ❌ No GREYSON records found at all")
                
    except Exception as e:
        print(f"   ❌ Query error: {e}")
    
    # Check what customers and POs we do have
    print("\n2. AVAILABLE TEST DATA")
    print("-" * 25)
    try:
        available_query = """
        SELECT TOP 10
            [CUSTOMER NAME],
            [PO NUMBER],
            COUNT(*) as order_count
        FROM ORDERS_UNIFIED 
        WHERE [CUSTOMER NAME] IN ('GREYSON', 'ACTIVELY BLACK', 'PELOTON')
        GROUP BY [CUSTOMER NAME], [PO NUMBER]
        ORDER BY COUNT(*) DESC
        """
        
        available_data = db.run_query("ORDERS", available_query)
        if not available_data.empty:
            print("   📊 Available test data (top 10):")
            for _, row in available_data.iterrows():
                print(f"   • {row['CUSTOMER NAME']} PO {row['PO NUMBER']}: {row['order_count']} orders")
        else:
            print("   ❌ No test data available")
            
    except Exception as e:
        print(f"   ❌ Query error: {e}")

if __name__ == "__main__":
    check_greyson_po_4755()
