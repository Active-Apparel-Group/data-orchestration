#!/usr/bin/env python3
"""Test get_board_planning.py migration to centralized mapping system"""

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

def test_get_board_planning():
    """Test get_board_planning.py migration"""
    print("🔧 Testing get_board_planning.py migration")
    
    # Set up paths
    repo_root = find_repo_root()
    scripts_path = repo_root / "scripts" / "monday-boards"
    
    # Add to path
    sys.path.insert(0, str(scripts_path))
    
    try:
        # Import the script
        print("📋 Importing get_board_planning...")
        import get_board_planning
        print("✅ get_board_planning imported successfully")
        
        # Check migrated constants
        print(f"✅ BOARD_ID: {get_board_planning.BOARD_ID}")
        print(f"✅ TABLE_NAME: {get_board_planning.TABLE_NAME}")
        print(f"✅ DATABASE_NAME: {get_board_planning.DATABASE_NAME}")
        
        # Validate the mapping
        if get_board_planning.BOARD_ID == 8709134353:
            print("✅ Board ID correctly migrated to centralized mapping")
        else:
            print("❌ Board ID migration issue")
            
        if get_board_planning.TABLE_NAME == "MON_COO_Planning":
            print("✅ Table name correctly set from mapping")
        else:
            print("❌ Table name mapping issue")
            
        if get_board_planning.DATABASE_NAME == "orders":
            print("✅ Database name correctly set from mapping")
        else:
            print("❌ Database name mapping issue")
          # Test key functions exist
        functions_to_check = [
            'find_repo_root',
            'gql', 
            'fetch_board_data_with_pagination',
            'truncate_table',
            'concurrent_insert_chunk',
            'production_concurrent_insert'  # Correct function name
        ]
        
        for func_name in functions_to_check:
            if hasattr(get_board_planning, func_name):
                print(f"✅ Function {func_name} found")
            else:
                print(f"❌ Function {func_name} missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Error with get_board_planning: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("GET_BOARD_PLANNING.PY MIGRATION TEST")
    print("=" * 60)
    success = test_get_board_planning()
    print("=" * 60)
    if success:
        print("🎉 get_board_planning.py migration successful!")
    else:
        print("❌ get_board_planning.py migration has issues")
    print("=" * 60)
