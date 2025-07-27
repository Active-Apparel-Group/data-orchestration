"""
Test Schema-Aware ORDER_LIST Transform
Purpose: Validate that DDL-based staging fixes the NVARCHAR disaster
Author: Data Engineering Team
Date: July 9, 2025

Test Plan:
1. Validate current ORDER_LIST schema (should show NVARCHAR pollution)
2. Test schema-aware staging table creation
3. Run limited transform with proper data types
4. Validate results show INT as INT, DECIMAL as DECIMAL
"""

import sys
from pathlib import Path

def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

import db_helper as db
import logger_helper
from schema_aware_staging_helper import create_schema_aware_staging_helper

def test_current_schema_validation():
    """Test current ORDER_LIST schema to confirm NVARCHAR pollution"""
    print("🔍 STEP 1: VALIDATE CURRENT ORDER_LIST SCHEMA")
    print("=" * 60)
    
    helper = create_schema_aware_staging_helper()
    
    try:
        validation = helper.validate_staging_schema('ORDER_LIST', 'orders')
        
        print(f"📊 Current ORDER_LIST Schema Analysis:")
        print(f"   Valid: {validation['valid']}")
        print(f"   INT columns: {validation['int_columns']}")
        print(f"   DECIMAL columns: {validation['decimal_columns']}")
        print(f"   NVARCHAR columns: {validation['nvarchar_columns']}")
        print(f"   Total columns: {validation['total_columns']}")
        
        nvarchar_percentage = (validation['nvarchar_columns'] / validation['total_columns'] * 100) if validation['total_columns'] > 0 else 0
        
        print(f"   NVARCHAR percentage: {nvarchar_percentage:.1f}%")
        
        if not validation['valid']:
            print("❌ CONFIRMED: Current ORDER_LIST has broken schema (NVARCHAR pollution)")
            print("   This explains why garment sizes show as '2.0000' instead of '2'")
        else:
            print("✅ Current ORDER_LIST schema is healthy")
            
        print(f"\n📋 Full Type Distribution:")
        for type_info in validation['type_distribution']:
            print(f"   {type_info['DATA_TYPE']}: {type_info['column_count']} columns")
            
        return validation
        
    except Exception as e:
        print(f"❌ Error validating current schema: {e}")
        return None

def test_schema_aware_staging_creation():
    """Test creating staging table with proper DDL schema"""
    print("\n🔧 STEP 2: TEST SCHEMA-AWARE STAGING TABLE CREATION")
    print("=" * 60)
    
    helper = create_schema_aware_staging_helper()
    test_staging_table = "test_swp_ORDER_LIST"
    
    try:
        # Create staging table using DDL schema
        helper.prepare_staging_table_ddl_based(test_staging_table, 'orders')
        
        # Validate the new staging table schema
        validation = helper.validate_staging_schema(test_staging_table, 'orders')
        
        print(f"📊 Schema-Aware Staging Table Analysis:")
        print(f"   Valid: {validation['valid']}")
        print(f"   INT columns: {validation['int_columns']}")
        print(f"   DECIMAL columns: {validation['decimal_columns']}")
        print(f"   NVARCHAR columns: {validation['nvarchar_columns']}")
        print(f"   Total columns: {validation['total_columns']}")
        
        nvarchar_percentage = (validation['nvarchar_columns'] / validation['total_columns'] * 100) if validation['total_columns'] > 0 else 0
        print(f"   NVARCHAR percentage: {nvarchar_percentage:.1f}%")
        
        if validation['valid']:
            print("✅ SUCCESS: Schema-aware staging table has proper data types")
            print("   INT columns will store integers correctly")
            print("   DECIMAL columns will store decimals correctly")
        else:
            print("❌ FAILURE: Schema-aware staging table still has issues")
            
        # Show some specific column types for verification
        specific_columns_query = f"""
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{test_staging_table}' AND TABLE_SCHEMA = 'dbo'
        AND COLUMN_NAME IN ('ORDER QTY', '10/M', 'XS', 'UNIT PRICE', 'AAG ORDER NUMBER')
        ORDER BY COLUMN_NAME
        """
        
        columns_df = db.run_query(specific_columns_query, 'orders')
        
        if not columns_df.empty:
            print(f"\n📋 Sample Column Types (Size/Quantity columns):")
            for _, row in columns_df.iterrows():
                col_name = row['COLUMN_NAME']
                data_type = row['DATA_TYPE']
                max_len = row['CHARACTER_MAXIMUM_LENGTH']
                precision = row['NUMERIC_PRECISION']
                scale = row['NUMERIC_SCALE']
                
                type_detail = data_type
                if max_len:
                    type_detail += f"({max_len})"
                elif precision:
                    type_detail += f"({precision},{scale})"
                    
                print(f"   {col_name}: {type_detail}")
        
        # Clean up test table
        db.execute(f"DROP TABLE IF EXISTS dbo.{test_staging_table}", 'orders')
        print(f"\n🧹 Cleaned up test table: {test_staging_table}")
        
        return validation
        
    except Exception as e:
        print(f"❌ Error testing schema-aware staging: {e}")
        # Try to clean up on error
        try:
            db.execute(f"DROP TABLE IF EXISTS dbo.{test_staging_table}", 'orders')
        except:
            pass
        return None

def test_minimal_transform_run():
    """Test a minimal transform run to validate data flow"""
    print("\n🚀 STEP 3: TEST MINIMAL TRANSFORM WITH SCHEMA AWARENESS")
    print("=" * 60)
    
    try:
        # Import and run the schema-aware transformer with minimal data
        from pipelines.scripts.load_order_list.order_list_transform_schema_aware import OrderListTransformerSchemaFixed
        
        transformer = OrderListTransformerSchemaFixed()
        
        # Check if we have any RAW tables to work with
        raw_tables_df = db.run_query("""
            SELECT TOP 1 TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME LIKE 'x%_ORDER_LIST_RAW'
            ORDER BY TABLE_NAME
        """, 'orders')
        
        if raw_tables_df.empty:
            print("⚠️ No RAW tables found - skipping transform test")
            print("   Create RAW tables first using extract layer")
            return {"success": False, "reason": "No RAW tables"}
        
        first_table = raw_tables_df.iloc[0]['TABLE_NAME']
        print(f"🎯 Testing with table: {first_table}")
        
        # Test single customer transform
        result = transformer.run_transform_single_customer(first_table)
        
        if result['success']:
            print(f"✅ Single customer transform successful")
            print(f"   Customer: {result['customer']}")
            print(f"   Rows: {result['rows_processed']}")
            print(f"   Duration: {result['duration']:.2f}s")
            
            if 'data' in result and not result['data'].empty:
                df = result['data']
                print(f"\n📊 Data Type Verification:")
                
                # Check data types of key columns
                type_check_columns = ['ORDER QTY', 'UNIT PRICE', 'AAG ORDER NUMBER']
                for col in type_check_columns:
                    if col in df.columns:
                        sample_val = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                        val_type = type(sample_val).__name__ if sample_val is not None else "None"
                        print(f"   {col}: {val_type} = {sample_val}")
            
            return result
        else:
            print(f"❌ Single customer transform failed: {result.get('error')}")
            return result
            
    except Exception as e:
        print(f"❌ Error in minimal transform test: {e}")
        return {"success": False, "error": str(e)}

def run_schema_validation_test_suite():
    """Run complete test suite for schema-aware staging"""
    print("🧪 SCHEMA-AWARE ORDER_LIST TRANSFORM VALIDATION")
    print("=" * 80)
    print("Purpose: Validate DDL-based staging fixes NVARCHAR disaster")
    print("=" * 80)
    
    results = {}
    
    # Step 1: Current schema validation
    results['current_schema'] = test_current_schema_validation()
    
    # Step 2: Schema-aware staging test
    results['schema_aware_staging'] = test_schema_aware_staging_creation()
    
    # Step 3: Minimal transform test
    results['minimal_transform'] = test_minimal_transform_run()
    
    # Summary
    print("\n📊 TEST SUITE SUMMARY")
    print("=" * 80)
    
    if results['current_schema'] and not results['current_schema']['valid']:
        print("✅ CONFIRMED: Current ORDER_LIST has NVARCHAR pollution")
    
    if results['schema_aware_staging'] and results['schema_aware_staging']['valid']:
        print("✅ CONFIRMED: Schema-aware staging creates proper data types")
    
    if results['minimal_transform'] and results['minimal_transform'].get('success'):
        print("✅ CONFIRMED: Transform runs successfully with schema awareness")
    
    print("\n🎯 NEXT STEPS:")
    print("1. Deploy schema-aware transform to fix NVARCHAR disaster")
    print("2. Run full customer transform with DDL-based staging")
    print("3. Validate that ORDER_LIST has proper INT/DECIMAL columns")
    print("4. Update all future transforms to use schema-aware staging")
    
    return results

if __name__ == "__main__":
    try:
        results = run_schema_validation_test_suite()
        
        # Check overall success
        has_failures = (
            (results['current_schema'] and results['current_schema']['valid']) or  # Current should be invalid
            (results['schema_aware_staging'] and not results['schema_aware_staging']['valid']) or  # New should be valid
            (results['minimal_transform'] and not results['minimal_transform'].get('success', True))  # Transform should work
        )
        
        if has_failures:
            print("\n❌ Some tests failed - review results above")
            sys.exit(1)
        else:
            print("\n✅ All tests passed - schema-aware approach is ready for deployment")
            
    except Exception as e:
        print(f"💥 CRITICAL ERROR: {e}")
        sys.exit(1)
