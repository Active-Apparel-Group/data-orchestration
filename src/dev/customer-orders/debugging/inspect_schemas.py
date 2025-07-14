#!/usr/bin/env python3
"""
Schema Inspector - Check staging table columns
"""

import sys
from pathlib import Path

# Add project paths
current_dir = Path(__file__).parent
repo_root = current_dir.parent.parent
sys.path.insert(0, str(repo_root / "utils"))

from db_helper import run_query

def inspect_schemas():
    """Inspect current staging table schemas"""
    
    # Check main staging table columns
    print("=== STG_MON_CustMasterSchedule Columns ===")
    main_columns = run_query('''
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule'
        ORDER BY ORDINAL_POSITION
    ''', 'orders')
    
    for _, row in main_columns.iterrows():
        col_name = row['COLUMN_NAME']
        data_type = row['DATA_TYPE']
        nullable = row['IS_NULLABLE']
        print(f"{col_name:<30} {data_type:<15} {nullable}")
    
    print("\n=== STG_MON_CustMasterSchedule_Subitems Columns ===")
    subitems_columns = run_query('''
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule_Subitems'
        ORDER BY ORDINAL_POSITION
    ''', 'orders')
    
    for _, row in subitems_columns.iterrows():
        col_name = row['COLUMN_NAME']
        data_type = row['DATA_TYPE']
        nullable = row['IS_NULLABLE']
        print(f"{col_name:<30} {data_type:<15} {nullable}")

if __name__ == "__main__":
    inspect_schemas()
