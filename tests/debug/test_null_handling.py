"""
Test script to demonstrate null value handling in update_boards.py
"""
import sys
from pathlib import Path
import pandas as pd

# Standard import pattern
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

import db_helper as db

def test_null_handling():
    """Test what happens with null values in the planning_update_fob query"""
    
    # Execute the query to see actual data with nulls
    query = """
    WITH
    -- 1) Pull in the ORDERS_UNIFIED values we care about
    ou AS (
        SELECT
            [AAG ORDER NUMBER],
            [CUSTOMER STYLE],
            CAST([FINAL FOB (USD)]       AS DECIMAL(18,2)) AS new_fob,
            TRY_CAST([ETA CUSTOMER WAREHOUSE DATE] AS DATE) AS new_eta
        FROM ORDERS_UNIFIED
    ),

    -- 2) Join MON_COO_Planning to ORDERS_UNIFIED, but only non-FORE orders
    candidates AS (
        SELECT
            mon.[Item ID],
            mon.[AAG ORDER NUMBER],
            mon.[Order Type],
            mon.[Customer FOB (USD)]            AS old_fob,
            ou.new_fob,
            mon.[ETA CUSTOMER WAREHOUSE DATE]   AS old_eta,
            ou.new_eta
        FROM MON_COO_Planning mon
        JOIN ou
          ON ou.[AAG ORDER NUMBER] = mon.[AAG ORDER NUMBER]
         AND ou.[CUSTOMER STYLE]    = mon.[STYLE CODE]
        WHERE LEFT(mon.[Order Type],4) <> 'FORE'
    )

    -- 3) Final select = only those rows where FOB or ETA differs
    SELECT TOP 5
        c.[Item ID] as monday_item_id,
        c.[AAG ORDER NUMBER],

        -- Project the new values
        c.new_fob            AS [Customer FOB (USD)],
        c.new_eta            AS [ETA CUSTOMER WAREHOUSE DATE],

        -- For auditing you can still include the olds
        c.old_fob,
        c.old_eta

    FROM candidates c
    WHERE (c.new_fob != c.old_fob OR c.new_eta != c.old_eta)
       OR (c.old_fob IS NULL OR c.old_eta IS NULL)
    ORDER BY c.[Item ID]
    """
    
    print("🔍 Testing Null Value Handling in Update Query")
    print("=" * 60)
    
    try:
        with db.get_connection('orders') as conn:
            df = pd.read_sql(query, conn)
            
            print(f"📊 Found {len(df)} records with FOB/ETA differences")
            print("\n📋 Sample Data (showing null handling):")
            
            for idx, row in df.iterrows():
                print(f"\n🔢 Record {idx + 1}:")
                print(f"   Item ID: {row['monday_item_id']}")
                print(f"   Order: {row['AAG ORDER NUMBER']}")
                print(f"   FOB (new): {row['Customer FOB (USD)']} (null: {pd.isna(row['Customer FOB (USD)'])})")
                print(f"   ETA (new): {row['ETA CUSTOMER WAREHOUSE DATE']} (null: {pd.isna(row['ETA CUSTOMER WAREHOUSE DATE'])})")
                
                # Simulate the update logic
                column_mapping = {
                    "text_mkp6sfqv": "AAG ORDER NUMBER",
                    "numeric_mkp4q1rv": "Customer FOB (USD)",
                    "date_mkp44k3t": "ETA CUSTOMER WAREHOUSE DATE"
                }
                
                column_updates = {}
                for monday_column_id, source_column in column_mapping.items():
                    if source_column in row and pd.notna(row[source_column]):
                        column_updates[monday_column_id] = str(row[source_column])
                        print(f"   ✅ WILL UPDATE {monday_column_id}: {row[source_column]}")
                    else:
                        print(f"   ❌ SKIP {monday_column_id}: {source_column} is null/missing")
                
                print(f"   📤 Final Update Payload: {column_updates}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_null_handling()
