"""
Debug Script: Customer Name Analysis
Purpose: Check actual customer names in database vs normalized names
"""
import sys
from pathlib import Path

# Add project root for imports
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
import pandas as pd

def debug_customer_names():
    """Debug customer names and normalization"""
    
    print("=== CUSTOMER NAME DEBUG ===")
    
    # 1. Check actual customer names in ORDERS_UNIFIED for PO 4755
    print("\n1. Checking customer names for PO 4755:")
    query_po = """
    SELECT DISTINCT 
        [CUSTOMER NAME],
        [PO NUMBER],
        COUNT(*) as record_count
    FROM [dbo].[ORDERS_UNIFIED]
    WHERE [PO NUMBER] = '4755'
    GROUP BY [CUSTOMER NAME], [PO NUMBER]
    """
    
    with db.get_connection('orders') as conn:
        df_po = pd.read_sql(query_po, conn)
    
    print(f"Customer names for PO 4755:")
    for _, row in df_po.iterrows():
        print(f"  Customer: '{row['CUSTOMER NAME']}' | Records: {row['record_count']}")
    
    # 2. Check all GREYSON-related customer names
    print("\n2. Checking all GREYSON-related names:")
    query_greyson = """
    SELECT DISTINCT 
        [CUSTOMER NAME],
        COUNT(*) as record_count
    FROM [dbo].[ORDERS_UNIFIED]
    WHERE [CUSTOMER NAME] LIKE '%GREYSON%' OR [CUSTOMER NAME] LIKE '%greyson%'
    GROUP BY [CUSTOMER NAME]
    ORDER BY record_count DESC
    """
    
    with db.get_connection('orders') as conn:
        df_greyson = pd.read_sql(query_greyson, conn)
    
    print(f"All GREYSON-related customer names:")
    for _, row in df_greyson.iterrows():
        print(f"  Customer: '{row['CUSTOMER NAME']}' | Records: {row['record_count']}")
    
    # 3. Test customer mapper normalization
    print("\n3. Testing customer mapper normalization:")
    try:
        from utils.customer_mapper import CustomerMapper
        mapper = CustomerMapper()
        
        test_names = ['GREYSON CLOTHIERS', 'greyson', 'GREYSON', 'Greyson Clothiers']
        for name in test_names:
            normalized = mapper.normalize_customer_name(name)
            print(f"  '{name}' -> '{normalized}'")
            
    except Exception as e:
        print(f"  Error testing mapper: {e}")
    
    # 4. Check snapshot table status
    print("\n4. Checking snapshot table:")
    query_snapshot = """
    SELECT COUNT(*) as snapshot_count
    FROM [dbo].[ORDERS_UNIFIED_SNAPSHOT]
    """
    
    with db.get_connection('orders') as conn:
        df_snapshot = pd.read_sql(query_snapshot, conn)
    
    print(f"Snapshot records: {df_snapshot.iloc[0]['snapshot_count']}")

if __name__ == "__main__":
    debug_customer_names()
