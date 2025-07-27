"""
Check Current ORDER_LIST Data Structure
======================================

Check what's currently in ORDER_LIST to understand the backwards logic issue.
"""

import sys
from pathlib import Path

def find_repo_root():
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current.parent.parent / "pipelines" / "utils").exists():
            return current.parent.parent
        current = current.parent
    raise RuntimeError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

from sql_test_helper import create_sql_tester
import logger_helper

def check_current_data():
    """Check current ORDER_LIST data structure"""
    
    logger = logger_helper.get_logger(__name__)
    tester = create_sql_tester('orders')
    
    print("🔍 CHECKING CURRENT ORDER_LIST DATA STRUCTURE")
    print("=" * 60)
    
    # Check current data
    sql = """
    SELECT TOP 5 
        [CUSTOMER NAME],
        [SOURCE_CUSTOMER_NAME],
        [_SOURCE_TABLE]
    FROM [ORDER_LIST]
    WHERE [_SOURCE_TABLE] LIKE '%ACTIVELY_BLACK%'
    """
    
    result = tester.test_query("Current ORDER_LIST Data", sql)
    
    if result['success']:
        print(f"✅ Query successful - found {result['row_count']} rows")
        print(f"\n📊 CURRENT DATA STRUCTURE:")
        
        for i, row in enumerate(result['data_sample']):
            print(f"\n   Record {i+1}:")
            print(f"   CUSTOMER NAME: '{row['CUSTOMER NAME']}'")
            print(f"   SOURCE_CUSTOMER_NAME: '{row['SOURCE_CUSTOMER_NAME']}'")
            print(f"   _SOURCE_TABLE: '{row['_SOURCE_TABLE']}'")
            print("   " + "-" * 40)
        
        print(f"\n🐛 PROBLEM IDENTIFIED:")
        print(f"   - CUSTOMER NAME should contain CANONICAL customer names")
        print(f"   - SOURCE_CUSTOMER_NAME should contain RAW source names") 
        print(f"   - But they appear to be BACKWARDS!")
        
    else:
        print(f"❌ Query failed: {result.get('errors', [])}")
    
    # Also check a few more customers to confirm pattern
    sql2 = """
    SELECT TOP 10
        [CUSTOMER NAME],
        [SOURCE_CUSTOMER_NAME],
        [_SOURCE_TABLE]
    FROM [ORDER_LIST]
    WHERE [_SOURCE_TABLE] IN (
        'xGREYSON_ORDER_LIST_RAW',
        'xJOHNNIE_O_ORDER_LIST_RAW', 
        'xTRACKSMITH_ORDER_LIST_RAW'
    )
    """
    
    result2 = tester.test_query("Multiple Customer Check", sql2)
    
    if result2['success']:
        print(f"\n🔍 CHECKING MULTIPLE CUSTOMERS:")
        print(f"Found {result2['row_count']} rows across different customers")
        
        for i, row in enumerate(result2['data_sample'][:5]):
            print(f"   {row['_SOURCE_TABLE']} → CUSTOMER: '{row['CUSTOMER NAME']}' | SOURCE: '{row['SOURCE_CUSTOMER_NAME']}'")
    
    return result

if __name__ == "__main__":
    check_current_data()
