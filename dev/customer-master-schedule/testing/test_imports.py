#!/usr/bin/env python3
"""Test imports from customer_master_schedule directory"""

import sys
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

if __name__ == "__main__":
    print(f"Testing from: {Path(__file__).resolve()}")
    
    try:
        # Test repo root detection
        repo_root = find_repo_root()
        print(f"✅ Found repo root: {repo_root}")
        
        # Add utils to path
        sys.path.insert(0, str(repo_root / "utils"))
        
        # Test importing utils modules
        try:
            import db_helper as db
            print("✅ db_helper imported successfully")
        except Exception as e:
            print(f"❌ Failed to import db_helper: {e}")
            
        try:
            import mapping_helper as mapping
            print("✅ mapping_helper imported successfully")
        except Exception as e:
            print(f"❌ Failed to import mapping_helper: {e}")
        
        # Test importing local modules
        try:
            from order_mapping import (
                transform_orders_batch,
                create_staging_dataframe,
                get_monday_column_values_dict,
                transform_order_data,
                load_mapping_config,
                load_customer_mapping
            )
            print("✅ order_mapping imported successfully")
        except Exception as e:
            print(f"❌ Failed to import order_mapping: {e}")
        
        try:
            import order_queries
            print("✅ order_queries imported successfully")
        except Exception as e:
            print(f"❌ Failed to import order_queries: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
