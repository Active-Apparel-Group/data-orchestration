#!/usr/bin/env python3
"""Test the dependencies and imports for customer_master_schedule scripts"""

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

def test_script_imports():
    """Test imports for customer_master_schedule scripts"""
    print("🔧 Testing customer_master_schedule script dependencies")
    
    # Set up paths
    repo_root = find_repo_root()
    scripts_path = repo_root / "scripts" / "customer_master_schedule"
    utils_path = repo_root / "utils"
    
    # Add both to path
    sys.path.insert(0, str(utils_path))
    sys.path.insert(0, str(scripts_path))
    
    print(f"Repo root: {repo_root}")
    print(f"Scripts path: {scripts_path}")
    print(f"Utils path: {utils_path}")
    
    try:
        # Test order_mapping
        print("\n📋 Testing order_mapping.py...")
        import order_mapping
        print("✅ order_mapping imported successfully")
        
        # Test specific functions
        config = order_mapping.load_mapping_config()
        print(f"✅ Mapping config loaded: {type(config)}")
        
        customer_mapping = order_mapping.load_customer_mapping()
        print(f"✅ Customer mapping loaded: {type(customer_mapping)}")
        
    except Exception as e:
        print(f"❌ Error with order_mapping: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        # Test order_queries
        print("\n📊 Testing order_queries.py...")
        import order_queries
        print("✅ order_queries imported successfully")
        
    except Exception as e:
        print(f"❌ Error with order_queries: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        # Test utils modules
        print("\n⚙️ Testing utils modules...")
        import db_helper as db
        print("✅ db_helper imported successfully")
        
        import mapping_helper as mapping
        print("✅ mapping_helper imported successfully")
        
        # Test mapping system
        board_config = mapping.get_board_config('customer_master_schedule')
        print(f"✅ Board config: {board_config}")
        
    except Exception as e:
        print(f"❌ Error with utils: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("CUSTOMER MASTER SCHEDULE DEPENDENCY TEST")
    print("=" * 60)
    test_script_imports()
    print("=" * 60)
