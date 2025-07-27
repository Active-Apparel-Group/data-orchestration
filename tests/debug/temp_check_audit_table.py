"""
Quick check for MON_UpdateAudit table in ORDERS database
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

print("Checking ORDERS database for Update-related objects...")

with db.get_connection('orders') as conn:
    print("\n1. All tables in ORDERS database:")
    all_tables = pd.read_sql("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES ORDER BY TABLE_NAME", conn)
    for table in all_tables['TABLE_NAME']:
        print(f"   {table}")
    
    print("\n2. Tables with 'Update' in name:")
    update_tables = pd.read_sql("""
        SELECT TABLE_NAME, TABLE_TYPE 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME LIKE '%Update%' 
        ORDER BY TABLE_NAME
    """, conn)
    print(update_tables)
    
    print("\n3. All procedures:")
    procedures = pd.read_sql("""
        SELECT ROUTINE_NAME 
        FROM INFORMATION_SCHEMA.ROUTINES 
        ORDER BY ROUTINE_NAME
    """, conn)
    for proc in procedures['ROUTINE_NAME']:
        print(f"   {proc}")
    
    print("\n4. Check if MON_UpdateAudit exists directly:")
    try:
        audit_check = pd.read_sql("SELECT COUNT(*) as record_count FROM MON_UpdateAudit", conn)
        print(f"   ✅ MON_UpdateAudit exists with {audit_check.iloc[0]['record_count']} records")
    except Exception as e:
        print(f"   ❌ MON_UpdateAudit not accessible: {e}")

print("\nDone!")
