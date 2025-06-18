#!/usr/bin/env python3
"""
Debug script to show all actual columns in the Customer Master Schedule DataFrame
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

def show_all_columns():
    """Show all columns in the DataFrame"""
    print("🔍 Showing ALL columns in Customer Master Schedule DataFrame...")
    
    # Fetch and process data
    items, board_name = fetch_board_data_with_pagination()
    print(f"✅ Fetched {len(items)} items from board '{board_name}'")
    
    df = process_items(items)
    df = prepare_for_database(df)
    
    print(f"\n📊 DataFrame has {len(df.columns)} columns:")
    print(f"📊 DataFrame shape: {df.shape}")
    
    # Group columns by data type
    column_info = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        non_null = df[col].notnull().sum()
        sample_val = df[col].dropna().iloc[0] if non_null > 0 else None
        column_info.append((col, dtype, non_null, sample_val))
    
    # Sort by data type for easier reading
    column_info.sort(key=lambda x: (x[1], x[0]))
    
    current_dtype = None
    for col, dtype, non_null, sample in column_info:
        if dtype != current_dtype:
            print(f"\n📁 {dtype.upper()} COLUMNS:")
            current_dtype = dtype
        
        sample_str = str(sample)[:30] + "..." if len(str(sample)) > 30 else str(sample)
        print(f"   {col:<35} | {non_null:>3} values | ex: {sample_str}")
    
    # Look for columns with "QTY" or numeric-sounding names
    print(f"\n🔢 COLUMNS WITH POTENTIALLY NUMERIC NAMES:")
    numeric_pattern_columns = [col for col in df.columns if any(keyword in col.upper() for keyword in 
                                                               ['QTY', 'QUANTITY', 'AMOUNT', 'COUNT', 'NUMBER', 'TOTAL', 'LEAD', 'TIME'])]
    
    for col in numeric_pattern_columns:
        dtype = str(df[col].dtype)
        non_null = df[col].notnull().sum()
        sample_val = df[col].dropna().iloc[0] if non_null > 0 else None
        sample_str = str(sample_val)[:30] + "..." if len(str(sample_val)) > 30 else str(sample_val)
        print(f"   {col:<35} | {dtype:<10} | {non_null:>3} values | ex: {sample_str}")

if __name__ == "__main__":
    show_all_columns()
