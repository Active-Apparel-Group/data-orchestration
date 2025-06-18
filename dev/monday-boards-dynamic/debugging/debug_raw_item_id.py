#!/usr/bin/env python3
"""
Debug script to check what item["id"] actually returns from Monday.com API
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
from generated.get_board_MON_Customer_Master_Schedule import fetch_board_data_with_pagination
import pandas as pd

def debug_raw_item_id():
    """Debug the raw Item ID values from Monday.com API"""
    print("🔍 Debugging RAW Item ID from Monday.com API...")
    
    # Fetch data from Monday.com (TEST_MODE = True)
    items, board_name = fetch_board_data_with_pagination()
    print(f"✅ Fetched {len(items)} items from board '{board_name}'")
    
    # Check first few items
    print(f"\n🔍 Raw item['id'] values from Monday.com API:")
    for i, item in enumerate(items[:5]):
        raw_id = item["id"]
        print(f"   Item {i+1}: {repr(raw_id)} (type: {type(raw_id)})")
        
        # Try the conversion
        try:
            converted = int(raw_id)
            print(f"            -> int(): {converted} (type: {type(converted)})")
        except Exception as e:
            print(f"            -> int() FAILED: {e}")

if __name__ == "__main__":
    debug_raw_item_id()
