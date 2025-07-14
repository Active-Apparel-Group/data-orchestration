#!/usr/bin/env python3
"""
Debug script to check all numeric columns for type issues
"""

import os, sys
from pathlib import Path

# Find repository root and add utils to path
def find_repo_root():
    current_path = Path(__file__).resolve()
    while current_path.parent != current_path:
        utils_path = current_path / "utils"
        if utils_path.exists() and (utils_path / "db_helper.py").exists():
            return current_path
        current_path = current_path.parent
    raise RuntimeError("Could not find repository root with utils folder")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

# Import the same modules as the ETL script
from generated.get_board_MON_Customer_Master_Schedule import fetch_board_data_with_pagination, process_items, prepare_for_database
import pandas as pd
import numpy as np

def debug_all_numeric_columns():
    """Debug all numeric columns for type issues"""
    print("🔍 Debugging ALL numeric columns for SQL type issues...")
    
    # Fetch and process data
    items, board_name = fetch_board_data_with_pagination()
    print(f"✅ Fetched {len(items)} items from board '{board_name}'")
    
    df = process_items(items)
    df = prepare_for_database(df)
    
    # List of numeric columns from the script
    numeric_columns = [
        'BULK PO QTY', 'Fabric Lead Time', 'Precut Quantity', 'Item ID',
        'QTY WIP', 'QTY FG', 'QTY INVOICED', 'QTY FCST',
        'QTY WIP CUT', 'QTY WIP SEW', 'QTY WIP FIN', 'QTY SCRAP'
    ]
    
    print(f"\n🔍 Checking {len(numeric_columns)} numeric columns:")
    
    for col in numeric_columns:
        if col in df.columns:
            col_data = df[col]
            null_count = col_data.isnull().sum()
            non_null_count = col_data.notnull().sum()
            
            print(f"\n📊 {col}:")
            print(f"   Data type: {col_data.dtype}")
            print(f"   Non-null values: {non_null_count}")
            print(f"   Null values: {null_count}")
            
            if non_null_count > 0:
                # Check types of non-null values
                non_null_values = col_data.dropna()
                sample_values = non_null_values.head(3).tolist()
                value_types = [type(x) for x in sample_values]
                
                print(f"   Sample values: {sample_values}")
                print(f"   Value types: {value_types}")
                
                # Check for any string values that should be numeric
                string_count = sum(1 for x in non_null_values if isinstance(x, str))
                if string_count > 0:
                    print(f"   ⚠️  STRING VALUES FOUND: {string_count} out of {non_null_count}")
                    # Show some string examples
                    string_examples = [x for x in non_null_values[:10] if isinstance(x, str)]
                    print(f"   String examples: {string_examples[:3]}")
        else:
            print(f"\n📊 {col}: ❌ Not found in DataFrame")

if __name__ == "__main__":
    debug_all_numeric_columns()
