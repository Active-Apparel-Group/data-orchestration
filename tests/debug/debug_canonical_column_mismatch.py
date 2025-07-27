"""
Debug Canonical Column Mismatch Issue
=====================================

Use SQL test helper to diagnose the column count mismatch in canonical transformation.
This will help us understand why the INSERT statement fails.
"""

import sys
from pathlib import Path

# Add project paths
def find_repo_root():
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current.parent.parent / "pipelines" / "utils").exists():
            return current.parent.parent
        current = current.parent
    raise RuntimeError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

from sql_test_helper import create_sql_tester
import logger_helper

def debug_column_mismatch():
    """Debug the column mismatch issue between raw tables and staging table"""
    
    logger = logger_helper.get_logger(__name__)
    tester = create_sql_tester('orders')
    
    print("🔍 DEBUGGING CANONICAL COLUMN MISMATCH")
    print("=" * 60)
    
    # Step 1: Check staging table schema
    print("\n1️⃣ STAGING TABLE SCHEMA")
    print("-" * 30)
    
    staging_schema_query = """
    SELECT 
        COLUMN_NAME, 
        DATA_TYPE, 
        IS_NULLABLE,
        ORDINAL_POSITION
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'swp_ORDER_LIST' 
    ORDER BY ORDINAL_POSITION
    """
    
    staging_result = tester.test_query(
        "Staging Table Schema",
        staging_schema_query,
        expected_min_rows=400  # Should have 400+ columns
    )
    
    if staging_result['success']:
        print(f"✅ Staging table has {staging_result['row_count']} columns")
        print(f"   First 5 columns: {[row['COLUMN_NAME'] for row in staging_result['data_sample']]}")
    else:
        print(f"❌ Failed to get staging schema: {staging_result['errors']}")
        return
    
    # Step 2: Check a sample raw table schema
    print("\n2️⃣ SAMPLE RAW TABLE SCHEMA")
    print("-" * 30)
    
    sample_raw_query = """
    SELECT 
        COLUMN_NAME, 
        DATA_TYPE, 
        IS_NULLABLE,
        ORDINAL_POSITION
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'xACTIVELY_BLACK_ORDER_LIST_RAW'
    ORDER BY ORDINAL_POSITION
    """
    
    raw_result = tester.test_query(
        "Sample Raw Table Schema",
        sample_raw_query,
        expected_min_rows=50  # Should have 50+ columns
    )
    
    if raw_result['success']:
        print(f"✅ Raw table has {raw_result['row_count']} columns")
        print(f"   First 5 columns: {[row['COLUMN_NAME'] for row in raw_result['data_sample']]}")
        
        # Compare column counts
        staging_cols = staging_result['row_count']
        raw_cols = raw_result['row_count']
        print(f"\n📊 COLUMN COUNT COMPARISON:")
        print(f"   Staging table: {staging_cols} columns")
        print(f"   Raw table: {raw_cols} columns")
        print(f"   Difference: {staging_cols - raw_cols} columns")
        
    else:
        print(f"❌ Failed to get raw table schema: {raw_result['errors']}")
        return
    
    # Step 3: Check for key canonical columns
    print("\n3️⃣ CANONICAL CUSTOMER COLUMNS")
    print("-" * 30)
    
    canonical_columns_query = """
    SELECT TABLE_NAME, COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME IN ('swp_ORDER_LIST', 'xACTIVELY_BLACK_ORDER_LIST_RAW')
    AND COLUMN_NAME IN ('CUSTOMER NAME', 'SOURCE_CUSTOMER_NAME', '_SOURCE_TABLE')
    ORDER BY TABLE_NAME, COLUMN_NAME
    """
    
    canonical_result = tester.test_query(
        "Canonical Customer Columns",
        canonical_columns_query
    )
    
    if canonical_result['success']:
        print("✅ Canonical customer columns found:")
        for row in canonical_result['data_sample']:
            print(f"   {row['TABLE_NAME']}: {row['COLUMN_NAME']}")
    else:
        print(f"❌ Failed to check canonical columns: {canonical_result['errors']}")
    
    # Step 4: Check all available raw tables
    print("\n4️⃣ AVAILABLE RAW TABLES")
    print("-" * 30)
    
    raw_tables_query = """
    SELECT 
        TABLE_NAME,
        (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = t.TABLE_NAME) as COLUMN_COUNT
    FROM INFORMATION_SCHEMA.TABLES t
    WHERE TABLE_NAME LIKE '%_ORDER_LIST_RAW'
    ORDER BY TABLE_NAME
    """
    
    tables_result = tester.test_query(
        "Available Raw Tables",
        raw_tables_query,
        expected_min_rows=10  # Should have 10+ raw tables
    )
    
    if tables_result['success']:
        print(f"✅ Found {tables_result['row_count']} raw tables")
        print("   Sample tables and column counts:")
        for row in tables_result['data_sample']:
            print(f"   - {row['TABLE_NAME']}: {row['COLUMN_COUNT']} columns")
    else:
        print(f"❌ Failed to get raw tables: {tables_result['errors']}")
    
    # Step 5: Identify the specific issue
    print("\n5️⃣ DIAGNOSIS")
    print("-" * 30)
    
    if staging_result['success'] and raw_result['success']:
        if staging_result['row_count'] > raw_result['row_count']:
            print("🔍 ISSUE IDENTIFIED: Staging table has MORE columns than raw table")
            print("   This means our DDL has more columns than the source data")
            print("   Solution: Use column-wise matching in transformer")
            
        elif staging_result['row_count'] < raw_result['row_count']:
            print("🔍 ISSUE IDENTIFIED: Raw table has MORE columns than staging table")
            print("   This means source data has columns not in our DDL")
            print("   Solution: Update DDL or filter columns in transformer")
            
        else:
            print("🔍 ISSUE IDENTIFIED: Same column count but different structure")
            print("   This means column names or order don't match")
            print("   Solution: Use explicit column mapping in transformer")
    
    print("\n🎯 NEXT STEPS:")
    print("1. Fix canonical transformer to do explicit column mapping")
    print("2. Ensure INSERT only uses columns that exist in both tables")
    print("3. Use SELECT column1, column2, ... instead of SELECT *")
    
    return {
        'staging_columns': staging_result['row_count'] if staging_result['success'] else 0,
        'raw_columns': raw_result['row_count'] if raw_result['success'] else 0,
        'raw_tables_count': tables_result['row_count'] if tables_result['success'] else 0
    }

if __name__ == "__main__":
    try:
        results = debug_column_mismatch()
        print(f"\n✅ Debug completed successfully")
        print(f"   Staging columns: {results['staging_columns']}")
        print(f"   Sample raw columns: {results['raw_columns']}")
        print(f"   Total raw tables: {results['raw_tables_count']}")
    except Exception as e:
        print(f"\n❌ Debug failed: {e}")
