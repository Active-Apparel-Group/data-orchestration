"""
Debug: Staging Table Creation Issue
Purpose: Test staging table creation in isolation to identify the problem
Date: July 10, 2025
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
from schema_aware_staging_helper import StagingTableManager

logger = logger_helper.get_logger(__name__)

def test_staging_table_creation():
    """Test staging table creation in isolation"""
    print("🔧 TESTING STAGING TABLE CREATION")
    print("=" * 60)
    
    # Configuration
    staging_table = "swp_ORDER_LIST"
    db_name = "orders"
    ddl_file_path = repo_root / "notebooks" / "db" / "ddl" / "updates" / "create_order_list_complete_fixed.sql"
    
    print(f"Staging table: {staging_table}")
    print(f"Database: {db_name}")
    print(f"DDL file: {ddl_file_path}")
    print(f"DDL file exists: {ddl_file_path.exists()}")
    
    if not ddl_file_path.exists():
        print(f"❌ DDL file not found: {ddl_file_path}")
        return
    
    # Step 1: Check if staging table already exists
    print(f"\n1️⃣ CHECKING EXISTING STAGING TABLE")
    print("-" * 40)
    
    try:
        check_query = f"""
            SELECT COUNT(*) as table_exists
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = '{staging_table}'
        """
        result = db.run_query(check_query, db_name)
        exists = result.iloc[0]['table_exists'] > 0 if not result.empty else False
        print(f"  {staging_table} exists: {exists}")
        
        if exists:
            # Get row count
            count_query = f"SELECT COUNT(*) as row_count FROM [dbo].[{staging_table}]"
            count_result = db.run_query(count_query, db_name)
            row_count = count_result.iloc[0]['row_count'] if not count_result.empty else 0
            print(f"  {staging_table} rows: {row_count:,}")
            
    except Exception as e:
        print(f"  ❌ Error checking existing table: {e}")
    
    # Step 2: Test StagingTableManager creation
    print(f"\n2️⃣ TESTING STAGING TABLE MANAGER")
    print("-" * 40)
    
    try:
        staging_manager = StagingTableManager()
        print(f"  ✅ StagingTableManager created successfully")
        
        # Test DDL loading
        ddl_content = staging_manager.helper.load_ddl_schema()
        print(f"  ✅ DDL loaded: {len(ddl_content)} characters")
        print(f"  DDL preview: {ddl_content[:200]}...")
        
    except Exception as e:
        print(f"  ❌ Error creating StagingTableManager: {e}")
        return
    
    # Step 3: Test staging table creation
    print(f"\n3️⃣ TESTING STAGING TABLE CREATION")
    print("-" * 40)
    
    try:
        print(f"  Creating staging table: {staging_table}")
        staging_manager.create_staging_table_from_ddl(
            staging_table=staging_table,
            ddl_file_path=str(ddl_file_path),
            db_name=db_name
        )
        print(f"  ✅ Staging table creation completed")
        
        # Verify creation
        verify_query = f"""
            SELECT COUNT(*) as table_exists
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = '{staging_table}'
        """
        verify_result = db.run_query(verify_query, db_name)
        created = verify_result.iloc[0]['table_exists'] > 0 if not verify_result.empty else False
        print(f"  ✅ Staging table verified: {created}")
        
        if created:
            # Get schema info
            schema_query = f"""
                SELECT DATA_TYPE, COUNT(*) as column_count
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = '{staging_table}'
                GROUP BY DATA_TYPE
                ORDER BY DATA_TYPE
            """
            schema_result = db.run_query(schema_query, db_name)
            print(f"  Schema breakdown:")
            for _, row in schema_result.iterrows():
                print(f"    {row['DATA_TYPE']}: {row['column_count']} columns")
        
    except Exception as e:
        print(f"  ❌ Error creating staging table: {e}")
        print(f"  Error type: {type(e).__name__}")
        import traceback
        print(f"  Traceback: {traceback.format_exc()}")
    
    # Step 4: Test simple INSERT
    print(f"\n4️⃣ TESTING SIMPLE INSERT")
    print("-" * 40)
    
    try:
        # Try a simple test insert
        test_insert = f"""
            INSERT INTO [{staging_table}] ([AAG ORDER NUMBER], [CUSTOMER NAME])
            VALUES ('TEST-001', 'TEST_CUSTOMER')
        """
        db.execute(test_insert, db_name)
        print(f"  ✅ Test INSERT successful")
        
        # Verify insert
        count_query = f"SELECT COUNT(*) as row_count FROM [dbo].[{staging_table}]"
        count_result = db.run_query(count_query, db_name)
        row_count = count_result.iloc[0]['row_count'] if not count_result.empty else 0
        print(f"  ✅ Staging table now has: {row_count} rows")
        
    except Exception as e:
        print(f"  ❌ Error with test INSERT: {e}")

if __name__ == "__main__":
    test_staging_table_creation()
