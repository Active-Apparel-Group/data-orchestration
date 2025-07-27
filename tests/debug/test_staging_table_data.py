#!/usr/bin/env python3
"""
Test to inspect staging table data for MACK WELDON records
Uses existing database connection logic from our working code
"""

import sys
import os
import pandas as pd

# Add src to path using the same pattern as our working tests
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

def inspect_mack_weldon_records():
    """Inspect staging table records for MACK WELDON to check Title field and column mapping"""
    
    from customer_master_schedule.order_queries import get_database_connection
    
    print("🔍 INSPECTING STAGING TABLE DATA")
    print("=" * 60)
    
    try:
        conn = get_database_connection()
        if not conn:
            print("❌ Failed to get database connection")
            return
        
        print("✅ Database connection successful")
        
        # Query MACK WELDON records
        query = """
        SELECT 
            [Item ID],
            [Title],
            [CUSTOMER], 
            [AAG ORDER NUMBER],
            [STYLE],
            [COLOR],
            [CUSTOMER PRICE],
            [ORDER TYPE],
            [ORDER DATE PO RECEIVED]
        FROM MON_CustMasterSchedule 
        WHERE [CUSTOMER] LIKE 'MACK%'
        ORDER BY [Item ID] DESC
        """
        
        print("🔄 Running query for MACK WELDON records...")
        df = pd.read_sql(query, conn)
        
        print(f"📊 Found {len(df)} MACK WELDON records")
        print("\n📋 RECORD DETAILS:")
        print("=" * 80)
        
        for idx, row in df.iterrows():
            print(f"\n🔍 Record {idx + 1}:")
            print(f"   Item ID: {row['Item ID']}")
            print(f"   Title: '{row['Title']}' {'❌ MISSING' if pd.isna(row['Title']) or row['Title'] == '' else '✅ PRESENT'}")
            print(f"   Customer: {row['CUSTOMER']}")
            print(f"   Order: {row['AAG ORDER NUMBER']}")
            print(f"   Style: {row['STYLE']}")
            print(f"   Color: {row['COLOR']}")
            print(f"   Price: {row['CUSTOMER PRICE']}")
            print(f"   Order Type: {row['ORDER TYPE']}")
            print(f"   Order Date: {row['ORDER DATE PO RECEIVED']}")
            
            # Check if Title should be calculated
            style = row['STYLE'] if not pd.isna(row['STYLE']) else ""
            color = row['COLOR'] if not pd.isna(row['COLOR']) else ""
            order_num = row['AAG ORDER NUMBER'] if not pd.isna(row['AAG ORDER NUMBER']) else ""
            expected_title = f"{style} {color} {order_num}".strip()
            
            print(f"   Expected Title: '{expected_title}'")
            if pd.isna(row['Title']) or row['Title'] == '':
                print("   ❌ ISSUE: Title field is missing!")
            elif row['Title'] != expected_title:
                print(f"   ⚠️ MISMATCH: Title doesn't match expected format")
        
        # Check for missing columns by getting full record
        print(f"\n📊 FULL COLUMN ANALYSIS:")
        print("=" * 60)
        
        full_query = "SELECT TOP 1 * FROM MON_CustMasterSchedule WHERE [CUSTOMER] LIKE 'MACK%' ORDER BY [Item ID] DESC"
        full_df = pd.read_sql(full_query, conn)
        
        if not full_df.empty:
            print(f"📋 Total columns in table: {len(full_df.columns)}")
            
            # Check which columns have values vs are null/empty
            non_null_cols = []
            null_cols = []
            
            for col in full_df.columns:
                value = full_df.iloc[0][col]
                if pd.isna(value) or (isinstance(value, str) and value.strip() == ''):
                    null_cols.append(col)
                else:
                    non_null_cols.append(col)
            
            print(f"\n✅ COLUMNS WITH VALUES ({len(non_null_cols)}):")
            for col in non_null_cols:
                value = full_df.iloc[0][col]
                print(f"   {col}: {value}")
            
            print(f"\n❌ EMPTY/NULL COLUMNS ({len(null_cols)}):")
            for col in null_cols:
                print(f"   {col}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error inspecting staging table: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_mack_weldon_records()
