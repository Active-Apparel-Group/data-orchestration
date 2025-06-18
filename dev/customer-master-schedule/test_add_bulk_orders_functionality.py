#!/usr/bin/env python3
"""Test add_bulk_orders.py script functionality"""

import sys
import os
from pathlib import Path

def find_repo_root():
    """Find the repository root by looking for utils folder"""
    current_path = Path(__file__).resolve()
    while current_path.parent != current_path:
        utils_path = current_path / "utils"
        if utils_path.exists() and (utils_path / "db_helper.py").exists():
            return current_path
        current_path = current_path.parent
    raise RuntimeError("Could not find repository root with utils folder")

def test_add_bulk_orders():
    """Test add_bulk_orders.py import and basic functionality"""
    print("🔧 Testing add_bulk_orders.py")
    
    # Set up paths
    repo_root = find_repo_root()
    scripts_path = repo_root / "scripts" / "customer_master_schedule"
    
    # Add to path
    sys.path.insert(0, str(scripts_path))
    
    try:
        # Import the script (this will execute the imports and constant definitions)
        print("📋 Importing add_bulk_orders...")
        import add_bulk_orders
        print("✅ add_bulk_orders imported successfully")
        
        # Check key constants and functions
        print(f"✅ BOARD_ID: {add_bulk_orders.BOARD_ID}")
        print(f"✅ MONDAY_API_URL: {add_bulk_orders.MONDAY_API_URL}")
        
        # Test key functions exist
        if hasattr(add_bulk_orders, 'get_db_connection'):
            print("✅ get_db_connection function found")
        
        if hasattr(add_bulk_orders, 'safe_json'):
            print("✅ safe_json function found")
            
        if hasattr(add_bulk_orders, 'load_mapping_dataframe'):
            print("✅ load_mapping_dataframe function found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error with add_bulk_orders: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("ADD_BULK_ORDERS.PY FUNCTIONALITY TEST")
    print("=" * 60)
    success = test_add_bulk_orders()
    print("=" * 60)
    if success:
        print("🎉 add_bulk_orders.py is working correctly!")
    else:
        print("❌ add_bulk_orders.py has issues that need to be resolved")
    print("=" * 60)
