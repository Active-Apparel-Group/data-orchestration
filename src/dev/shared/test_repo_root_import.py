#!/usr/bin/env python3
"""
SIMPLE KESTRA TEST - Repository Root Import Pattern
Quick test to validate Option 2 import pattern works in Kestra
"""

import sys
from pathlib import Path

# NEW PATTERN: Find repository root, then find utils
def find_repo_root():
    """Find the repository root by looking for utils folder"""
    current_path = Path(__file__).resolve()
    while current_path.parent != current_path:  # Not at filesystem root
        utils_path = current_path / "utils"
        if utils_path.exists() and (utils_path / "db_helper.py").exists():
            return current_path
        current_path = current_path.parent
    raise RuntimeError("Could not find repository root with utils folder")

# Add utils to path using repository root method
repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

# Import db_helper using new pattern
import db_helper as db

def main():
    """Simple test that validates import and database connection"""
    print(f"Repository root found at: {repo_root}")
    print(f"Utils path: {repo_root / 'utils'}")
    
    # Simple database test
    try:
        # Test database connection with simple query
        test_result = db.run_query("SELECT GETDATE() as current_time", "test_connection")
        print(f"✅ Database connection successful!")
        print(f"Current time from database: {test_result}")
        
        # Test basic functionality
        if test_result is not None and len(test_result) > 0:
            print("✅ Import pattern working correctly!")
            return True
        else:
            print("❌ Database query returned no results")
            return False
            
    except Exception as e:
        print(f"❌ Error testing database connection: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 KESTRA TEST PASSED - Repository root import pattern works!")
        exit(0)
    else:
        print("\n💥 KESTRA TEST FAILED")
        exit(1)
