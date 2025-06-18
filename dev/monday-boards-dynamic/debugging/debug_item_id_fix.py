#!/usr/bin/env python3
"""
Debug script to check Item ID values after the fix
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

def debug_item_id_values():
    """Debug the Item ID values in the DataFrame"""
    print("🔍 Debugging Item ID values after fix...")
    
    # Fetch data from Monday.com (TEST_MODE = True)
    items, board_name = fetch_board_data_with_pagination()
    print(f"✅ Fetched {len(items)} items from board '{board_name}'")
    
    # Process items to DataFrame
    df = process_items(items)
    print(f"✅ Created DataFrame with {len(df)} rows and {len(df.columns)} columns")
    
    # Check Item ID column before prepare_for_database
    print("\n🔍 Item ID values BEFORE prepare_for_database():")
    print(f"   Column name: 'Item ID'")
    print(f"   Data type: {df['Item ID'].dtype}")
    print(f"   Sample values: {df['Item ID'].head().tolist()}")
    print(f"   Value types: {[type(x) for x in df['Item ID'].head().tolist()]}")
    
    # Prepare for database
    df = prepare_for_database(df)
    
    # Check Item ID column after prepare_for_database
    print("\n🔍 Item ID values AFTER prepare_for_database():")
    print(f"   Column name: 'Item ID'")
    print(f"   Data type: {df['Item ID'].dtype}")
    print(f"   Sample values: {df['Item ID'].head().tolist()}")
    print(f"   Value types: {[type(x) for x in df['Item ID'].head().tolist()]}")
    
    # Check for any None/NaN values
    null_count = df['Item ID'].isnull().sum()
    print(f"   Null values: {null_count}")
    
    if null_count > 0:
        print("   ⚠️  Found null values in Item ID!")
        print(f"   Null indices: {df[df['Item ID'].isnull()].index.tolist()}")

if __name__ == "__main__":
    debug_item_id_values()
