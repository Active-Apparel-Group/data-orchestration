"""
Test script to demonstrate null value handling with actual NULL scenarios
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

def test_null_scenarios():
    """Test different null scenarios to show update behavior"""
    
    print("🧪 Testing Null Value Scenarios in Update Logic")
    print("=" * 60)
    
    # Create test data with different null combinations
    test_scenarios = [
        {
            'scenario': 'Both FOB and ETA have values',
            'monday_item_id': 123456,
            'AAG ORDER NUMBER': 'TEST-001',
            'Customer FOB (USD)': 15.50,
            'ETA CUSTOMER WAREHOUSE DATE': pd.Timestamp('2025-07-15')
        },
        {
            'scenario': 'FOB has value, ETA is NULL',
            'monday_item_id': 123457,
            'AAG ORDER NUMBER': 'TEST-002',
            'Customer FOB (USD)': 12.75,
            'ETA CUSTOMER WAREHOUSE DATE': None
        },
        {
            'scenario': 'FOB is NULL, ETA has value',
            'monday_item_id': 123458,
            'AAG ORDER NUMBER': 'TEST-003',
            'Customer FOB (USD)': None,
            'ETA CUSTOMER WAREHOUSE DATE': pd.Timestamp('2025-08-01')
        },
        {
            'scenario': 'Both FOB and ETA are NULL',
            'monday_item_id': 123459,
            'AAG ORDER NUMBER': 'TEST-004',
            'Customer FOB (USD)': None,
            'ETA CUSTOMER WAREHOUSE DATE': None
        },
        {
            'scenario': 'FOB is 0.0 (not null), ETA is NULL',
            'monday_item_id': 123460,
            'AAG ORDER NUMBER': 'TEST-005',
            'Customer FOB (USD)': 0.0,
            'ETA CUSTOMER WAREHOUSE DATE': None
        }
    ]
    
    # Column mapping from the TOML file
    column_mapping = {
        "text_mkp6sfqv": "AAG ORDER NUMBER",
        "numeric_mkp4q1rv": "Customer FOB (USD)",
        "date_mkp44k3t": "ETA CUSTOMER WAREHOUSE DATE"
    }
    
    for i, scenario_data in enumerate(test_scenarios, 1):
        print(f"\n🔬 Scenario {i}: {scenario_data['scenario']}")
        print(f"   FOB: {scenario_data['Customer FOB (USD)']} (is null: {pd.isna(scenario_data['Customer FOB (USD)']) if scenario_data['Customer FOB (USD)'] is not None else True})")
        print(f"   ETA: {scenario_data['ETA CUSTOMER WAREHOUSE DATE']} (is null: {pd.isna(scenario_data['ETA CUSTOMER WAREHOUSE DATE']) if scenario_data['ETA CUSTOMER WAREHOUSE DATE'] is not None else True})")
        
        # Simulate the update logic from update_boards.py line 320
        column_updates = {}
        for monday_column_id, source_column in column_mapping.items():
            if source_column in scenario_data and pd.notna(scenario_data[source_column]):
                column_updates[monday_column_id] = str(scenario_data[source_column])
                print(f"   ✅ WILL UPDATE {monday_column_id}: {scenario_data[source_column]}")
            else:
                print(f"   ❌ SKIP {monday_column_id}: {source_column} is null/missing")
        
        print(f"   📤 Final Update Payload: {column_updates}")
        
        # Show what would be sent to Monday.com
        if column_updates:
            print(f"   🚀 Monday.com GraphQL will receive: {len(column_updates)} field(s)")
        else:
            print(f"   ⚠️  NO UPDATES - All values are null, no GraphQL call would be made")

def test_real_null_query():
    """Test a modified query that forces some null values"""
    
    print("\n\n🔍 Testing Real Database Query with Forced Nulls")
    print("=" * 60)
    
    # Modified query that creates null scenarios
    query = """
    WITH
    -- 1) Pull in the ORDERS_UNIFIED values we care about
    ou AS (
        SELECT
            [AAG ORDER NUMBER],
            [CUSTOMER STYLE],
            -- Force some FOB values to be null for testing
            CASE 
                WHEN [AAG ORDER NUMBER] LIKE 'RYD%' THEN NULL
                ELSE CAST([FINAL FOB (USD)] AS DECIMAL(18,2))
            END AS new_fob,
            -- Force some ETA values to be null for testing  
            CASE 
                WHEN [AAG ORDER NUMBER] LIKE 'BAD%' THEN NULL
                ELSE TRY_CAST([ETA CUSTOMER WAREHOUSE DATE] AS DATE)
            END AS new_eta
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

        -- Project the new values (some will be null)
        c.new_fob            AS [Customer FOB (USD)],
        c.new_eta            AS [ETA CUSTOMER WAREHOUSE DATE],

        -- For auditing you can still include the olds
        c.old_fob,
        c.old_eta

    FROM candidates c
    WHERE (c.new_fob != c.old_fob OR c.new_eta != c.old_eta)
       OR (c.old_fob IS NULL OR c.old_eta IS NULL)
       OR (c.new_fob IS NULL OR c.new_eta IS NULL)  -- Include null scenarios
    ORDER BY c.[Item ID]
    """
    
    try:
        with db.get_connection('orders') as conn:
            df = pd.read_sql(query, conn)
            
            print(f"📊 Found {len(df)} records (including null scenarios)")
            
            column_mapping = {
                "text_mkp6sfqv": "AAG ORDER NUMBER", 
                "numeric_mkp4q1rv": "Customer FOB (USD)",
                "date_mkp44k3t": "ETA CUSTOMER WAREHOUSE DATE"
            }
            
            for idx, row in df.iterrows():
                print(f"\n🔢 Record {idx + 1}:")
                print(f"   Order: {row['AAG ORDER NUMBER']}")
                print(f"   FOB: {row['Customer FOB (USD)']} (null: {pd.isna(row['Customer FOB (USD)'])})")
                print(f"   ETA: {row['ETA CUSTOMER WAREHOUSE DATE']} (null: {pd.isna(row['ETA CUSTOMER WAREHOUSE DATE'])})")
                
                # Apply the same logic as update_boards.py
                column_updates = {}
                for monday_column_id, source_column in column_mapping.items():
                    if source_column in row and pd.notna(row[source_column]):
                        column_updates[monday_column_id] = str(row[source_column])
                        print(f"   ✅ WILL UPDATE {monday_column_id}")
                    else:
                        print(f"   ❌ SKIP {monday_column_id} (null)")
                
                print(f"   📤 Updates: {len(column_updates)} field(s)")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_null_scenarios()
    test_real_null_query()
