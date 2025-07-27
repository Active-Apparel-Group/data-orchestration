"""
List available tables in the orders database
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

# Import project utilities
import db_helper as db

print("Available tables in orders database:")
with db.get_connection('orders') as conn:
    df = pd.read_sql("""
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_TYPE = 'BASE TABLE'
    ORDER BY TABLE_NAME
    """, conn)
    
    for table in df['TABLE_NAME']:
        print(f"  - {table}")

print("\nAvailable tables in dms database:")
try:
    with db.get_connection('dms') as conn:
        df = pd.read_sql("""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        AND TABLE_NAME IN ('ORDERS_UNIFIED', 'ORDER_LIST')
        ORDER BY TABLE_NAME
        """, conn)
        
        for table in df['TABLE_NAME']:
            print(f"  - {table}")
except Exception as e:
    print(f"Error connecting to dms database: {e}")
