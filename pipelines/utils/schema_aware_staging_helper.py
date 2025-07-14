"""
Schema-Aware Staging Helper
Purpose: Fix ORDER_LIST schema disaster by creating staging tables from DDL, not DataFrame
Author: Data Engineering Team  
Date: July 9, 2025

Key Innovation:
- Creates `swp_ORDER_LIST` from proper DDL schema, not from broken production table
- Maintains atomicity while enforcing correct data types
- Prevents NVARCHAR pollution from spreading to staging tables
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import time

# --- repo utils path setup ----------------------------------------------------
def find_repo_root() -> Path:
    """Find repository root by looking for pipelines/utils folder"""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current.parent.parent / "pipelines" / "utils").exists():
            return current.parent.parent
        current = current.parent
    raise RuntimeError("Could not find repository root with utils/ folder")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))  # Only use pipelines/utils for Kestra compatibility

import db_helper as db  # noqa: E402
import logger_helper  # noqa: E402
import staging_helper  # noqa: E402

# Set staging mode for ORDER_LIST processing (clean data allows fast mode)
staging_helper.set_staging_mode('fast')

logger = logger_helper.get_logger(__name__)

class SchemaAwareStagingHelper:
    """
    Enhanced staging helper that creates tables from DDL schema, not DataFrame dtypes
    
    Benefits:
    - Enforces proper column types from canonical DDL
    - Prevents NVARCHAR pollution
    - Maintains atomic swap capabilities
    - Zero data type conversion issues
    """
    
    def __init__(self, ddl_file_path: Optional[str] = None):
        """
        Initialize with path to DDL file containing proper schema
        
        Args:
            ddl_file_path: Path to SQL file with CREATE TABLE statement
        """
        self.ddl_file_path = ddl_file_path or str(repo_root / "db" / "ddl" / "tables" / "orders" / "dbo_order_list.sql")
        self.logger = logger_helper.get_logger(__name__)
    
    def load_ddl_schema(self) -> str:
        """Load CREATE TABLE DDL from file"""
        ddl_path = Path(self.ddl_file_path)
        if not ddl_path.exists():
            raise FileNotFoundError(f"DDL file not found: {ddl_path}")
        
        with open(ddl_path, 'r', encoding='utf-8') as f:
            ddl_content = f.read()
        
        self.logger.info(f"Loaded DDL schema from: {ddl_path}")
        return ddl_content
    
    def create_swp_table_from_ddl(self, staging_table_name: str, db_name: str) -> None:
        """
        Create staging table (swp_ORDER_LIST) using proper DDL schema
        
        This fixes the core issue: instead of copying broken production table structure,
        we create staging table with correct data types from canonical DDL
        """
        start_time = time.time()
        
        # Drop existing staging table if exists
        drop_sql = f"DROP TABLE IF EXISTS dbo.{staging_table_name}"
        db.execute(drop_sql, db_name)
        
        # Load DDL and modify for staging table
        ddl_content = self.load_ddl_schema()
        
        # Replace table name in DDL
        staging_ddl = ddl_content.replace(
            "CREATE TABLE [dbo].[ORDER_LIST]",
            f"CREATE TABLE [dbo].[{staging_table_name}]"
        )
        
        # Remove primary key constraint for staging (causes issues with bulk inserts)
        staging_ddl = staging_ddl.replace(
            "[ID] INT IDENTITY(1,1) PRIMARY KEY,",
            "[ID] INT IDENTITY(1,1),"
        )
        
        # Execute DDL to create staging table with proper schema
        db.execute(staging_ddl, db_name)
        
        duration = time.time() - start_time
        self.logger.info(f"[SUCCESS] Created {staging_table_name} with proper DDL schema ({duration:.2f}s)")
        
        # Validate schema creation
        schema_validation = self.validate_staging_schema(staging_table_name, db_name)
        if schema_validation['valid']:
            self.logger.info(f"[SUCCESS] Schema validation passed: {schema_validation['int_columns']} INT columns, {schema_validation['decimal_columns']} DECIMAL columns")
        else:
            self.logger.error(f"[ERROR] Schema validation failed: {schema_validation['errors']}")
            raise RuntimeError("Staging table schema validation failed")
    
    def validate_staging_schema(self, table_name: str, db_name: str) -> Dict[str, Any]:
        """Validate that staging table has correct schema (INT, DECIMAL, not NVARCHAR)"""
        schema_query = f"""
        SELECT 
            DATA_TYPE,
            COUNT(*) as column_count
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table_name}' AND TABLE_SCHEMA = 'dbo'
        GROUP BY DATA_TYPE
        ORDER BY DATA_TYPE
        """
        
        schema_df = db.run_query(schema_query, db_name)
        
        int_columns = schema_df[schema_df['DATA_TYPE'] == 'int']['column_count'].sum()
        decimal_columns = schema_df[schema_df['DATA_TYPE'] == 'decimal']['column_count'].sum()
        nvarchar_columns = schema_df[schema_df['DATA_TYPE'] == 'nvarchar']['column_count'].sum()
        total_columns = schema_df['column_count'].sum()
        
        # Schema is valid if we have proper distribution of types
        valid = (int_columns > 0 and decimal_columns > 0 and 
                nvarchar_columns < total_columns * 0.8)  # Less than 80% NVARCHAR
        
        return {
            'valid': valid,
            'int_columns': int_columns,
            'decimal_columns': decimal_columns, 
            'nvarchar_columns': nvarchar_columns,
            'total_columns': total_columns,
            'type_distribution': schema_df.to_dict('records'),
            'errors': [] if valid else [f"Schema appears to be mostly NVARCHAR ({nvarchar_columns}/{total_columns})"]
        }
    
    def prepare_staging_table_ddl_based(
        self,
        staging_table: str,
        db_name: str
    ) -> None:
        """
        Enhanced prepare_staging_table that uses DDL schema instead of DataFrame dtypes
        
        This is the core fix for the NVARCHAR disaster
        """
        self.logger.info(f"[PROCESS] Creating {staging_table} with DDL-based schema (not DataFrame dtypes)")
        self.create_swp_table_from_ddl(staging_table, db_name)
    
    def load_to_staging_table_enhanced(
        self,
        df: pd.DataFrame,
        staging_table: str,
        db_name: str,
        batch_size: int = 1000
    ) -> None:
        """
        Enhanced load that handles type conversion for proper schema
        
        Since staging table now has correct types, we need to ensure DataFrame
        data is compatible
        """
        if df.empty:
            self.logger.warning("No data to load")
            return
        
        self.logger.info(f"[LOADING] Loading {len(df)} rows to {staging_table} with proper type handling")
        
        # Use existing staging_helper load function - it handles the data conversion
        staging_helper.load_to_staging_table(df, staging_table, db_name, batch_size)
        
        # Validate loaded data
        count_query = f"SELECT COUNT(*) as row_count FROM dbo.{staging_table}"
        result = db.run_query(count_query, db_name)
        loaded_rows = result.iloc[0]['row_count']
        
        self.logger.info(f"[SUCCESS] Loaded {loaded_rows} rows to {staging_table}")
        
        if loaded_rows != len(df):
            self.logger.warning(f"[WARNING] Row count mismatch: Expected {len(df)}, Loaded {loaded_rows}")
    
    def atomic_swap_tables_enhanced(
        self,
        staging_table: str,
        production_table: str,
        db_name: str
    ) -> None:
        """
        Enhanced atomic swap with schema validation
        
        Before swapping, validate that staging table has proper schema
        """
        start_time = time.time()
        
        # Pre-swap validation
        staging_validation = self.validate_staging_schema(staging_table, db_name)
        if not staging_validation['valid']:
            raise RuntimeError(f"Cannot swap tables - staging schema invalid: {staging_validation['errors']}")
        
        self.logger.info(f"[SUCCESS] Pre-swap validation passed - staging table has proper schema")
        self.logger.info(f"   INT columns: {staging_validation['int_columns']}, DECIMAL columns: {staging_validation['decimal_columns']}")
        
        # Perform atomic swap using existing function
        staging_helper.atomic_swap_tables(staging_table, production_table, db_name)
        
        # Post-swap validation
        production_validation = self.validate_staging_schema(production_table, db_name)
        
        duration = time.time() - start_time
        
        if production_validation['valid']:
            self.logger.info(f"[SUCCESS] Atomic swap successful with proper schema preservation ({duration:.2f}s)")
            self.logger.info(f"   Production table now has: INT columns: {production_validation['int_columns']}, DECIMAL columns: {production_validation['decimal_columns']}")
        else:
            self.logger.error(f"[ERROR] Atomic swap completed but schema validation failed: {production_validation['errors']}")

# Factory function for easy usage
def create_schema_aware_staging_helper(ddl_file_path: Optional[str] = None) -> SchemaAwareStagingHelper:
    """Factory function to create schema-aware staging helper"""
    return SchemaAwareStagingHelper(ddl_file_path)

# Enhanced pipeline functions that use DDL-based schema
def prepare_staging_table_from_ddl(
    staging_table: str,
    db_name: str,
    ddl_file_path: Optional[str] = None
) -> None:
    """
    Create staging table from DDL file instead of DataFrame dtypes
    
    This is the main function to use instead of staging_helper.prepare_staging_table
    when you need proper schema enforcement
    """
    helper = create_schema_aware_staging_helper(ddl_file_path)
    helper.prepare_staging_table_ddl_based(staging_table, db_name)

def enhanced_pipeline_with_proper_schema(
    df: pd.DataFrame,
    staging_table: str,
    production_table: str,
    db_name: str,
    ddl_file_path: Optional[str] = None,
    batch_size: int = 1000
) -> Dict[str, Any]:
    """
    Complete pipeline with DDL-based schema enforcement
    
    Args:
        df: Data to load
        staging_table: Name of staging table (e.g., 'swp_ORDER_LIST')
        production_table: Name of production table (e.g., 'ORDER_LIST')
        db_name: Database name
        ddl_file_path: Path to DDL file (optional)
        batch_size: Batch size for loading
    
    Returns:
        Result dictionary with success status and metrics
    """
    start_time = time.time()
    helper = create_schema_aware_staging_helper(ddl_file_path)
    
    try:
        # Step 1: Create staging table with proper DDL schema
        helper.prepare_staging_table_ddl_based(staging_table, db_name)
        
        # Step 2: Load data with type handling
        helper.load_to_staging_table_enhanced(df, staging_table, db_name, batch_size)
        
        # Step 3: Atomic swap with validation
        helper.atomic_swap_tables_enhanced(staging_table, production_table, db_name)
        
        duration = time.time() - start_time
        
        return {
            'success': True,
            'rows_processed': len(df),
            'duration': duration,
            'message': 'Pipeline completed successfully with proper schema enforcement'
        }
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Enhanced pipeline failed: {e}")
        
        return {
            'success': False,
            'error': str(e),
            'duration': duration,
            'message': 'Pipeline failed - staging table preserved for debugging'
        }

class StagingTableManager:
    """
    Wrapper class that provides the exact interface expected by order_list_transform_sql.py
    
    This class bridges the gap between the new server-side optimized code and the existing
    schema-aware staging infrastructure
    """
    
    def __init__(self, ddl_file_path: Optional[str] = None):
        """Initialize with DDL file path"""
        self.helper = create_schema_aware_staging_helper(ddl_file_path)
        self.logger = logger_helper.get_logger(__name__)
    
    def create_staging_table_from_ddl(
        self, 
        staging_table: str, 
        ddl_file_path: str, 
        db_name: str
    ) -> None:
        """
        Create staging table from DDL file - matches the interface expected by _sql.py
        
        Args:
            staging_table: Name of staging table (e.g., 'swp_ORDER_LIST')
            ddl_file_path: Path to DDL file
            db_name: Database name
        """
        self.logger.info(f"Creating staging table {staging_table} from DDL: {ddl_file_path}")
        
        # Update helper's DDL path
        self.helper.ddl_file_path = ddl_file_path
        
        # CRITICAL FIX: Always drop and recreate staging table to ensure clean state
        try:
            drop_sql = f"DROP TABLE IF EXISTS [dbo].[{staging_table}]"
            db.execute(drop_sql, db_name)
            self.logger.info(f"Dropped existing staging table: {staging_table}")
        except Exception as e:
            self.logger.warning(f"Could not drop staging table (may not exist): {e}")
        
        # Create staging table using DDL
        self.helper.create_swp_table_from_ddl(staging_table, db_name)
        
        # Verify the table is empty and ready
        count_query = f"SELECT COUNT(*) as row_count FROM [dbo].[{staging_table}]"
        count_result = db.run_query(count_query, db_name)
        row_count = count_result.iloc[0]['row_count'] if not count_result.empty else 0
        
        if row_count == 0:
            self.logger.info(f"SUCCESS: Created clean {staging_table} with proper DDL schema (0 rows)")
        else:
            self.logger.warning(f"WARNING: {staging_table} created but has {row_count} rows (should be 0)")
            # Try to clear it
            try:
                truncate_sql = f"TRUNCATE TABLE [dbo].[{staging_table}]"
                db.execute(truncate_sql, db_name)
                self.logger.info(f"Truncated {staging_table} to ensure clean state")
            except Exception as e:
                self.logger.error(f"Could not truncate {staging_table}: {e}")
    
    def atomic_swap_tables(
        self, 
        staging_table: str, 
        production_table: str, 
        db_name: str
    ) -> Dict[str, Any]:
        """
        Perform atomic swap between staging and production tables
        
        Args:
            staging_table: Name of staging table
            production_table: Name of production table  
            db_name: Database name
            
        Returns:
            Result dictionary with success status
        """
        self.logger.info(f"Atomic swap: {staging_table} -> {production_table}")
        
        try:
            # Use the enhanced atomic swap with validation
            self.helper.atomic_swap_tables_enhanced(staging_table, production_table, db_name)
            
            self.logger.info(f"SUCCESS: Atomic swap completed successfully")
            return {"success": True, "message": "Atomic swap completed"}
            
        except Exception as e:
            self.logger.error(f"ERROR: Atomic swap failed: {e}")
            return {"success": False, "error": str(e)}
    
    def load_to_staging_table_enhanced(
        self,
        df: pd.DataFrame,
        staging_table: str,
        db_name: str,
        batch_size: int = 1000
    ) -> None:
        """
        Load DataFrame to staging table with enhanced type handling
        
        Args:
            df: DataFrame to load
            staging_table: Name of staging table
            db_name: Database name
            batch_size: Batch size for loading
        """
        self.helper.load_to_staging_table_enhanced(df, staging_table, db_name, batch_size)

if __name__ == "__main__":
    # Test the schema-aware helper
    helper = create_schema_aware_staging_helper()
    
    # Test schema validation
    try:
        validation = helper.validate_staging_schema('ORDER_LIST', 'orders')
        self.logger.info("📊 Current ORDER_LIST schema validation:")
        self.logger.info(f"   Valid: {validation['valid']}")
        self.logger.info(f"   INT columns: {validation['int_columns']}")
        self.logger.info(f"   DECIMAL columns: {validation['decimal_columns']}")
        self.logger.info(f"   NVARCHAR columns: {validation['nvarchar_columns']}")
        self.logger.info(f"   Total columns: {validation['total_columns']}")
        
        if not validation['valid']:
            self.logger.info("❌ Current ORDER_LIST has broken schema (too much NVARCHAR)")
            self.logger.info("✅ Schema-aware staging helper will fix this on next deploy")
        
    except Exception as e:
        self.logger.info(f"Error validating schema: {e}")
    
    # Test the new StagingTableManager
    self.logger.info("\n🔧 Testing StagingTableManager interface:")
    try:
        manager = StagingTableManager()
        self.logger.info("✅ StagingTableManager created successfully")
        self.logger.info("   Available methods:")
        self.logger.info("   - create_staging_table_from_ddl()")
        self.logger.info("   - atomic_swap_tables()")
        self.logger.info("   - load_to_staging_table_enhanced()")
        
    except Exception as e:
        self.logger.info(f"❌ StagingTableManager test failed: {e}")
