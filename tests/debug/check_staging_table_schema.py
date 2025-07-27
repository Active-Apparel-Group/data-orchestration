#!/usr/bin/env python3
"""
Check the actual schema of the staging table to diagnose column issues
"""

import sys
from pathlib import Path
import pandas as pd

# Add utils to path
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

from db_helper import get_connection

def check_staging_table_schema():
    """Check what columns exist in the staging table"""
    
    try:
        with get_connection('orders') as conn:
            # Check if table exists
            table_check = pd.read_sql("""
                SELECT COUNT(*) as table_count 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE table_name = 'STG_MON_CustMasterSchedule_Subitems'
            """, conn)
            
            if table_check['table_count'].iloc[0] == 0:
                print("❌ Table STG_MON_CustMasterSchedule_Subitems does not exist!")
                return
            
            print("✅ Table STG_MON_CustMasterSchedule_Subitems exists")
            
            # Get column information
            columns_info = pd.read_sql("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE table_name = 'STG_MON_CustMasterSchedule_Subitems'
                ORDER BY ordinal_position
            """, conn)
            
            print(f"\n📋 Table has {len(columns_info)} columns:")
            for _, col in columns_info.iterrows():
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f"DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"  - {col['column_name']} ({col['data_type']}) {nullable} {default}")
            
            print(f"\n🔍 Column names list:")
            column_names = columns_info['column_name'].tolist()
            print(column_names)
            
            # Check for specific columns we're trying to use
            required_columns = [
                'stg_order_qty_numeric',
                'stg_customer_batch', 
                'stg_source_order_number',
                'stg_source_style',
                'stg_source_color'
            ]
            
            print(f"\n🎯 Required columns check:")
            for col in required_columns:
                exists = col in column_names
                status = "✅" if exists else "❌"
                print(f"  {status} {col}")
            
    except Exception as e:
        print(f"❌ Error checking staging table: {e}")

if __name__ == "__main__":
    check_staging_table_schema()
