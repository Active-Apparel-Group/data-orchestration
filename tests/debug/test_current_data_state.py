"""
Test Current Data State
=======================

Check what's actually in ORDER_LIST table using sql_test_helper
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

def test_current_data():
    """Test current data in ORDER_LIST"""
    
    tester = create_sql_tester('orders')
    
    print("🔍 CURRENT ORDER_LIST DATA STATE:")
    print("=" * 50)
    
    # Check WHITE_FOX data
    sql = '''
    SELECT TOP 5 
        [CUSTOMER NAME],
        [SOURCE_CUSTOMER_NAME],
        [_SOURCE_TABLE]
    FROM [ORDER_LIST]
    WHERE [_SOURCE_TABLE] LIKE '%WHITE_FOX%'
    '''
    
    result = tester.test_query("WHITE_FOX Data Check", sql)
    
    if result['success']:
        print(f"✅ Found {result['row_count']} WHITE_FOX records")
        print("\nSample data:")
        for i, row in enumerate(result['data_sample']):
            print(f"  Record {i+1}:")
            print(f"    CUSTOMER NAME: '{row['CUSTOMER NAME']}'")
            print(f"    SOURCE_CUSTOMER_NAME: '{row['SOURCE_CUSTOMER_NAME']}'")
            print(f"    _SOURCE_TABLE: '{row['_SOURCE_TABLE']}'")
            print("    ---")
    else:
        print(f"❌ Query failed: {result.get('errors', 'Unknown error')}")
    
    # Check GREYSON data for comparison
    sql2 = '''
    SELECT TOP 3
        [CUSTOMER NAME],
        [SOURCE_CUSTOMER_NAME],
        [_SOURCE_TABLE]
    FROM [ORDER_LIST]
    WHERE [_SOURCE_TABLE] LIKE '%GREYSON%'
    '''
    
    result2 = tester.test_query("GREYSON Data Check", sql2)
    
    if result2['success']:
        print(f"\n✅ Found {result2['row_count']} GREYSON records")
        print("\nSample data:")
        for i, row in enumerate(result2['data_sample']):
            print(f"  Record {i+1}:")
            print(f"    CUSTOMER NAME: '{row['CUSTOMER NAME']}'")
            print(f"    SOURCE_CUSTOMER_NAME: '{row['SOURCE_CUSTOMER_NAME']}'")
            print(f"    _SOURCE_TABLE: '{row['_SOURCE_TABLE']}'")
            print("    ---")
    else:
        print(f"❌ Query failed: {result2.get('errors', 'Unknown error')}")
    
    # Check what's in RAW table CUSTOMER NAME column
    sql3 = '''
    SELECT TOP 3 [CUSTOMER NAME] 
    FROM [xWHITE_FOX_ORDER_LIST_RAW]
    '''
    
    result3 = tester.test_query("RAW WHITE_FOX CUSTOMER NAME", sql3)
    
    if result3['success']:
        print(f"\n🔍 RAW TABLE CUSTOMER NAME VALUES:")
        for i, row in enumerate(result3['data_sample']):
            print(f"  RAW Record {i+1}: '{row['CUSTOMER NAME']}'")
    else:
        print(f"❌ RAW Query failed: {result3.get('errors', 'Unknown error')}")

    # Check GREYSON RAW table too
    sql4 = '''
    SELECT TOP 3 [CUSTOMER NAME] 
    FROM [xGREYSON_ORDER_LIST_RAW]
    '''
    
    result4 = tester.test_query("RAW GREYSON CUSTOMER NAME", sql4)
    
    if result4['success']:
        print(f"\n🔍 RAW GREYSON CUSTOMER NAME VALUES:")
        for i, row in enumerate(result4['data_sample']):
            print(f"  RAW Record {i+1}: '{row['CUSTOMER NAME']}'")
    else:
        print(f"❌ RAW Query failed: {result4.get('errors', 'Unknown error')}")

if __name__ == "__main__":
    test_current_data()
