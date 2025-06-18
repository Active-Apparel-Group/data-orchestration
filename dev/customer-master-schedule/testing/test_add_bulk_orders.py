#!/usr/bin/env python3
"""Test add_bulk_orders.py imports and basic functionality"""

import sys
import os
from pathlib import Path

def find_repo_root():
    """Find the repository root by looking for utils folder"""
    current_path = Path(__file__).resolve()
    while current_path.parent != current_path:  # Not at filesystem root
        utils_path = current_path / "utils"
        if utils_path.exists() and (utils_path / "db_helper.py").exists():
            return current_path
        current_path = current_path.parent
    raise RuntimeError("Could not find repository root with utils folder")

def test_imports():
    """Test all imports needed by add_bulk_orders.py"""
    print("🔧 Testing imports for add_bulk_orders.py")
    
    # Add utils to path using repository root method
    repo_root = find_repo_root()
    sys.path.insert(0, str(repo_root / "utils"))
    
    try:
        # Test utils imports
        import db_helper as db
        print("✅ db_helper imported successfully")
        
        import mapping_helper as mapping
        print("✅ mapping_helper imported successfully")
        
        # Test local module imports
        from order_mapping import (
            transform_orders_batch,
            create_staging_dataframe,
            get_monday_column_values_dict,
            transform_order_data,
            load_mapping_config,
            load_customer_mapping
        )
        print("✅ order_mapping imported successfully")
        
        import order_queries
        print("✅ order_queries imported successfully")
        
        # Test the centralized mapping system
        print("\n🔧 Testing centralized mapping system")
        board_config = mapping.get_board_config('customer_master_schedule')
        print(f"✅ Board config retrieved: {board_config}")
        
        board_id = board_config['board_id']
        print(f"✅ Board ID: {board_id}")
        
        # Test configuration loading
        config = db.load_config()
        print(f"✅ Configuration loaded successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_add_bulk_orders_constants():
    """Test that add_bulk_orders.py constants can be accessed"""
    print("\n🔧 Testing add_bulk_orders.py constants")
    
    try:
        # Import the module to check constants
        import add_bulk_orders
        
        print(f"✅ BOARD_ID: {add_bulk_orders.BOARD_ID}")
        print(f"✅ MONDAY_API_URL: {add_bulk_orders.MONDAY_API_URL}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error accessing add_bulk_orders constants: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING ADD_BULK_ORDERS.PY DEPENDENCIES")
    print("=" * 60)
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    # Test constants access
    if not test_add_bulk_orders_constants():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED - add_bulk_orders.py is ready to use!")
    else:
        print("❌ SOME TESTS FAILED - Please check the errors above")
    print("=" * 60)
