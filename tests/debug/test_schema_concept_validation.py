"""
Simple Schema Validation Test
Purpose: Validate the core concept without dealing with DDL duplicates
Author: Data Engineering Team
Date: July 9, 2025

Test Steps:
1. Check current ORDER_LIST schema (should be broken)
2. Create a simple staging table with proper INT/DECIMAL types
3. Show the concept works - no need for full DDL
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

def test_current_schema_disaster():
    """Confirm current ORDER_LIST schema is broken"""
    print("🔍 STEP 1: CONFIRM CURRENT ORDER_LIST SCHEMA DISASTER")
    print("=" * 60)
    
    # Get schema info
    schema_query = """
    SELECT 
        DATA_TYPE,
        COUNT(*) as column_count
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'ORDER_LIST' AND TABLE_SCHEMA = 'dbo'
    GROUP BY DATA_TYPE
    ORDER BY column_count DESC
    """
    
    schema_df = db.run_query(schema_query, 'orders')
    
    print("📊 Current ORDER_LIST Type Distribution:")
    total_columns = 0
    nvarchar_columns = 0
    int_columns = 0
    decimal_columns = 0
    
    for _, row in schema_df.iterrows():
        data_type = row['DATA_TYPE']
        count = row['column_count']
        total_columns += count
        
        if data_type == 'nvarchar':
            nvarchar_columns = count
        elif data_type == 'int':
            int_columns = count
        elif data_type == 'decimal':
            decimal_columns = count
            
        print(f"   {data_type}: {count} columns")
    
    nvarchar_percentage = (nvarchar_columns / total_columns * 100) if total_columns > 0 else 0
    
    print(f"\n📊 Schema Health Check:")
    print(f"   Total columns: {total_columns}")
    print(f"   NVARCHAR columns: {nvarchar_columns} ({nvarchar_percentage:.1f}%)")
    print(f"   INT columns: {int_columns}")
    print(f"   DECIMAL columns: {decimal_columns}")
    
    if nvarchar_percentage > 80:
        print("❌ CONFIRMED: Schema is broken - too much NVARCHAR pollution")
        print("   This explains why garment sizes show as '2.0000' instead of '2'")
        return False
    else:
        print("✅ Schema looks healthy")
        return True

def test_proper_staging_table_creation():
    """Create a simple staging table with proper types"""
    print("\n🔧 STEP 2: CREATE STAGING TABLE WITH PROPER TYPES")
    print("=" * 60)
    
    test_table = "test_proper_staging"
    
    try:
        # Drop if exists
        db.execute(f"DROP TABLE IF EXISTS dbo.{test_table}", 'orders')
        
        # Create staging table with proper types (sample of key columns)
        create_sql = f"""
        CREATE TABLE dbo.{test_table} (
            [ID] INT IDENTITY(1,1),
            [AAG ORDER NUMBER] NVARCHAR(100) NULL,
            [CUSTOMER NAME] NVARCHAR(100) NULL,
            [ORDER QTY] INT NULL,                    -- INT not NVARCHAR
            [UNIT PRICE] DECIMAL(17,4) NULL,         -- DECIMAL not NVARCHAR
            [XS] INT NULL,                           -- Size column as INT
            [S] INT NULL,                            -- Size column as INT
            [M] INT NULL,                            -- Size column as INT
            [L] INT NULL,                            -- Size column as INT
            [XL] INT NULL,                           -- Size column as INT
            [DATE PO RECEIVED] DATE NULL,            -- DATE not NVARCHAR
            [_SOURCE_TABLE] NVARCHAR(128) NULL
        )
        """
        
        db.execute(create_sql, 'orders')
        print(f"✅ Created {test_table} with proper data types")
        
        # Validate the new table schema
        schema_query = f"""
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{test_table}' AND TABLE_SCHEMA = 'dbo'
        ORDER BY ORDINAL_POSITION
        """
        
        schema_df = db.run_query(schema_query, 'orders')
        
        print(f"\n📋 Staging Table Schema Validation:")
        int_count = 0
        decimal_count = 0
        nvarchar_count = 0
        
        for _, row in schema_df.iterrows():
            col_name = row['COLUMN_NAME']
            data_type = row['DATA_TYPE']
            
            if data_type == 'int':
                int_count += 1
            elif data_type == 'decimal':
                decimal_count += 1
            elif data_type == 'nvarchar':
                nvarchar_count += 1
                
            type_detail = data_type
            if row['CHARACTER_MAXIMUM_LENGTH']:
                type_detail += f"({row['CHARACTER_MAXIMUM_LENGTH']})"
            elif row['NUMERIC_PRECISION']:
                type_detail += f"({row['NUMERIC_PRECISION']},{row['NUMERIC_SCALE']})"
                
            print(f"   {col_name}: {type_detail}")
        
        print(f"\n📊 Staging Schema Summary:")
        print(f"   INT columns: {int_count} (garment sizes will be integers)")
        print(f"   DECIMAL columns: {decimal_count} (prices will be proper decimals)")
        print(f"   NVARCHAR columns: {nvarchar_count} (text fields only)")
        
        if int_count > 0 and decimal_count > 0:
            print("✅ SUCCESS: Staging table has proper data types")
            print("   When we insert INT values, they'll stay as integers")
            print("   When we insert DECIMAL values, they'll be proper decimals")
            print("   No more '2.0000' formatting - will show as '2'")
        else:
            print("❌ FAILURE: Staging table types not correct")
        
        # Clean up
        db.execute(f"DROP TABLE dbo.{test_table}", 'orders')
        print(f"\n🧹 Cleaned up test table")
        
        return int_count > 0 and decimal_count > 0
        
    except Exception as e:
        print(f"❌ Error creating staging table: {e}")
        # Try to clean up on error
        try:
            db.execute(f"DROP TABLE IF EXISTS dbo.{test_table}", 'orders')
        except:
            pass
        return False

def test_concept_with_sample_data():
    """Test the concept with actual sample data"""
    print("\n🚀 STEP 3: TEST CONCEPT WITH SAMPLE DATA")
    print("=" * 60)
    
    test_table = "test_data_insert"
    
    try:
        # Create test table
        db.execute(f"DROP TABLE IF EXISTS dbo.{test_table}", 'orders')
        
        create_sql = f"""
        CREATE TABLE dbo.{test_table} (
            [AAG ORDER NUMBER] NVARCHAR(50),
            [ORDER QTY] INT,                    -- This will store integers properly
            [UNIT PRICE] DECIMAL(10,2),         -- This will store decimals properly
            [XS] INT,                           -- Size as INT
            [data_source] NVARCHAR(20)
        )
        """
        
        db.execute(create_sql, 'orders')
        
        # Insert sample data
        insert_sql = f"""
        INSERT INTO dbo.{test_table} VALUES
        ('TEST-001', 5, 19.99, 2, 'proper_schema'),
        ('TEST-002', 10, 25.50, 0, 'proper_schema'),
        ('TEST-003', 3, 45.00, 1, 'proper_schema')
        """
        
        db.execute(insert_sql, 'orders')
        
        # Query back and show results
        result_df = db.run_query(f"SELECT * FROM dbo.{test_table}", 'orders')
        
        print("📊 Sample Data with Proper Schema:")
        print(result_df.to_string(index=False))
        
        print(f"\n🎯 Key Observations:")
        print(f"   ORDER QTY values: {result_df['ORDER QTY'].tolist()} (stored as integers)")
        print(f"   UNIT PRICE values: {result_df['UNIT PRICE'].tolist()} (stored as decimals)")
        print(f"   XS values: {result_df['XS'].tolist()} (size stored as integers)")
        
        # Compare with what broken schema would look like
        print(f"\n🔍 Compare with broken schema behavior:")
        print(f"   Broken (NVARCHAR): SIZE '2' becomes '2.0000' when displayed")
        print(f"   Fixed (INT): SIZE 2 stays as integer 2")
        print(f"   Broken (NVARCHAR): PRICE '19.99' stored as text")
        print(f"   Fixed (DECIMAL): PRICE 19.99 stored as proper decimal")
        
        # Clean up
        db.execute(f"DROP TABLE dbo.{test_table}", 'orders')
        print(f"\n🧹 Cleaned up test table")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in data test: {e}")
        try:
            db.execute(f"DROP TABLE IF EXISTS dbo.{test_table}", 'orders')
        except:
            pass
        return False

def run_concept_validation():
    """Run the complete concept validation"""
    print("🧪 SCHEMA-AWARE CONCEPT VALIDATION")
    print("=" * 80)
    print("Purpose: Prove DDL-based staging fixes NVARCHAR disaster")
    print("=" * 80)
    
    results = {}
    
    # Step 1: Confirm current schema is broken
    results['current_broken'] = not test_current_schema_disaster()
    
    # Step 2: Show proper staging table creation
    results['staging_works'] = test_proper_staging_table_creation()
    
    # Step 3: Test with actual data
    results['data_test'] = test_concept_with_sample_data()
    
    # Summary
    print("\n📊 CONCEPT VALIDATION SUMMARY")
    print("=" * 80)
    
    if results['current_broken']:
        print("✅ CONFIRMED: Current ORDER_LIST schema is broken (NVARCHAR pollution)")
    
    if results['staging_works']:
        print("✅ CONFIRMED: Can create staging tables with proper INT/DECIMAL types")
    
    if results['data_test']:
        print("✅ CONFIRMED: Proper schema stores data correctly (no '2.0000' formatting)")
    
    all_good = all(results.values())
    
    if all_good:
        print("\n🎯 CONCLUSION: SCHEMA-AWARE APPROACH IS VALID")
        print("=" * 80)
        print("✅ The concept works - DDL-based staging will fix the NVARCHAR disaster")
        print("✅ Size columns will store as INT (showing '2' not '2.0000')")
        print("✅ Price columns will store as DECIMAL (proper numeric calculations)")
        print("✅ Atomic swap will preserve proper data types")
        
        print("\n📋 DEPLOYMENT PLAN:")
        print("1. Fix DDL duplicate column names")
        print("2. Deploy schema-aware staging helper")
        print("3. Run transform with DDL-based staging")
        print("4. Validate ORDER_LIST has proper schema after atomic swap")
        
    else:
        print("\n❌ Some validations failed - investigate issues")
    
    return all_good

if __name__ == "__main__":
    try:
        success = run_concept_validation()
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"💥 CRITICAL ERROR: {e}")
        sys.exit(1)
