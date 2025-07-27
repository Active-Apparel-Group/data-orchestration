"""
Check available tables and real GREYSON data
"""
import sys
from pathlib import Path

# Add utils path
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root / "utils"))

import db_helper as db
import pandas as pd

# Check tables
with db.get_connection('dms') as conn:
    tables_df = pd.read_sql("""
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_TYPE = 'BASE TABLE' 
    AND TABLE_NAME LIKE '%ORDER%'
    """, conn)
    
    print("Available ORDER tables:")
    for table in tables_df['TABLE_NAME']:
        print(f"  - {table}")
    
    # Check staging tables
    stg_df = pd.read_sql("""
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_TYPE = 'BASE TABLE' 
    AND TABLE_NAME LIKE 'stg_%'
    """, conn)
    
    print("\nAvailable staging tables:")
    for table in stg_df['TABLE_NAME']:
        print(f"  - {table}")
