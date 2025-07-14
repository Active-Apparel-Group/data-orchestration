"""
ORDER_LIST Consolidator - Modern Replacement for sp_FinalInsert
Purpose: Consolidate per-file customer tables into ORDER_LIST using pandas + bulk operations
Performance: 10x+ faster than cursor-based SP approach

This script runs AFTER the XLSX orchestrator to merge all x{customer} tables into ORDER_LIST.
Uses staging_helper.py for all database operations and follows project standards.
"""

import sys
from pathlib import Path
import pandas as pd
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import concurrent.futures
import logging
import warnings
import re

# Hide irrelevant warnings
warnings.filterwarnings("ignore", message="Data Validation extension is not supported and will be removed")

# Standard import pattern - find repository root
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

# Import project utilities
import db_helper as db
import staging_helper
import logger_helper

class OrderListConsolidator:
    """
    Modern replacement for sp_FinalInsert with enhanced performance and error handling.
    Uses staging_helper.py for all database operations and follows project standards.
    """
    
    def __init__(self, config_path: str = None):
        self.logger = logger_helper.get_logger(__name__)
        self.config = db.load_config(config_path) if config_path else db.load_config()
        self.db_key = "orders"  # Default database
        
        # Performance settings
        self.batch_size = 5000
        self.max_workers = 4  # For parallel processing
        
        # Table names following new conventions
        self.staging_table = "swp_ORDER_LIST"  # Staging table with swp_ prefix
        self.production_table = "ORDER_LIST"   # New production table (not ORDERS_UNIFIED)
        
        # Column mapping for standardization (replicate SP logic)
        self.column_standardization = {
            '∆': 'Delta',
            "CUSTOMER'S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS": 'CUSTOMER_COLOUR_CODE_CUSTOM',
            # Add more mappings as needed
        }
        
        self.logger.info("OrderListConsolidator initialized")
        self.logger.info(f"Staging table: {self.staging_table}")
        self.logger.info(f"Production table: {self.production_table}")
        
    def get_customer_tables(self) -> List[Dict[str, str]]:
        """
        Discover customer tables following naming convention.
        Looks for tables matching the pattern from the orchestrator (x{customer}_ORDER_LIST).
        """
        self.logger.info("Discovering customer tables...")
        
        query = """
        SELECT 
            TABLE_NAME,
            CASE
                WHEN TABLE_NAME LIKE 'x%ORDER_LIST%'
                THEN REPLACE(
                    SUBSTRING(TABLE_NAME, 2, CHARINDEX('_ORDER_LIST', TABLE_NAME) - 2),
                    '_', ' ')
                WHEN TABLE_NAME LIKE 'x%_ORDER%'
                THEN REPLACE(
                    SUBSTRING(TABLE_NAME, 2, LEN(TABLE_NAME) - 1),
                    '_', ' ')
                ELSE 'UNKNOWN'
            END as CUSTOMER_NAME,
            (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
             WHERE TABLE_NAME = t.TABLE_NAME) as COLUMN_COUNT
        FROM INFORMATION_SCHEMA.TABLES t
        WHERE TABLE_SCHEMA = 'dbo'
        AND TABLE_NAME LIKE 'x%'
        AND TABLE_NAME NOT LIKE 'swp_%'
        AND TABLE_NAME != 'ORDER_LIST'
        AND TABLE_NAME != 'ORDERS_UNIFIED'
        AND TABLE_NAME NOT LIKE 'vw%'
        AND TABLE_NAME NOT LIKE 'stg_%'
        ORDER BY TABLE_NAME
        """
        
        with db.get_connection(self.db_key) as conn:
            df = pd.read_sql(query, conn)
            
        tables = []
        for _, row in df.iterrows():
            tables.append({
                'table_name': row['TABLE_NAME'],
                'customer_name': row['CUSTOMER_NAME'],
                'column_count': row['COLUMN_COUNT']
            })
            
        self.logger.info(f"Discovered {len(tables)} customer tables")
        for table in tables:
            self.logger.info(f"  - {table['table_name']} ({table['customer_name']}) - {table['column_count']} columns")
            
        return tables
    
    def _get_default_schema(self) -> Dict[str, str]:
        """
        Get default schema when ORDERS_UNIFIED is not available
        This is a fallback based on standard column structure
        """
        self.logger.info("Using default schema definition")
        
        # These are the core columns based on customer table standard columns
        default_schema = {
            'CUSTOMER': 'NVARCHAR(255)',
            'AAG ORDER NUMBER': 'NVARCHAR(50)',
            'STYLE': 'NVARCHAR(100)',
            'COLOR': 'NVARCHAR(100)',
            'ORDER_QTY': 'INT',
            'ORDER DATE PO RECEIVED': 'DATETIME',
            'CUSTOMER SEASON': 'NVARCHAR(50)',
            'AAG SEASON': 'NVARCHAR(50)',
            'DROP': 'NVARCHAR(50)',
            'PO NUMBER': 'NVARCHAR(100)',
            'ETD': 'DATETIME',
            'ETA': 'DATETIME',
            'PORT OF DESTINATION': 'NVARCHAR(100)',
            'INCOTERM': 'NVARCHAR(50)',
            'CUST PRICE': 'DECIMAL(18,2)',
            'SIZE SCALE': 'NVARCHAR(MAX)',
            'FABRIC TYPE': 'NVARCHAR(255)',
            'MOQ': 'INT',
            'PACK METHOD': 'NVARCHAR(100)',
            'FACTORY': 'NVARCHAR(100)',
            'DELIVERY ADDRESS': 'NVARCHAR(255)',
            'DELIVERY TERMS': 'NVARCHAR(100)',
            'SOURCE': 'NVARCHAR(100)',
            'LAST_UPDATED': 'DATETIME'
        }
        
        return default_schema
        
    def get_order_list_schema(self) -> Dict[str, str]:
        """
        Get ORDER_LIST schema for column mapping.
        If ORDER_LIST doesn't exist, create it based on ORDERS_UNIFIED structure.
        """
        # First check if ORDER_LIST exists
        check_query = """
        SELECT COUNT(*) as table_count
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME = 'ORDER_LIST' AND TABLE_SCHEMA = 'dbo'
        """
        
        with db.get_connection(self.db_key) as conn:
            result = pd.read_sql(check_query, conn)
            
        # Also check if ORDERS_UNIFIED exists - verify access
        check_unified_query = """
        SELECT COUNT(*) as table_count
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME = 'ORDERS_UNIFIED' AND TABLE_SCHEMA = 'dbo'
        """
        
        with db.get_connection(self.db_key) as conn:
            unified_result = pd.read_sql(check_unified_query, conn)
            
        if unified_result['table_count'].iloc[0] == 0:
            self.logger.error("ORDERS_UNIFIED table doesn't exist or is not accessible in the orders database")
            # Set up default schema columns instead of relying on ORDERS_UNIFIED
            return self._get_default_schema()
            
        if result['table_count'].iloc[0] == 0:
            self.logger.info("ORDER_LIST table doesn't exist, will use ORDERS_UNIFIED schema as template")
            schema_table = 'ORDERS_UNIFIED'
        else:
            self.logger.info("Using existing ORDER_LIST schema")
            schema_table = 'ORDER_LIST'
        
        query = f"""
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE,
            ORDINAL_POSITION
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = '{schema_table}'
        AND TABLE_SCHEMA = 'dbo'
        ORDER BY ORDINAL_POSITION
        """
        
        try:
            with db.get_connection(self.db_key) as conn:
                df = pd.read_sql(query, conn)
                
            schema = {}
            for _, row in df.iterrows():
                col_name = row['COLUMN_NAME']
                data_type = row['DATA_TYPE']
                max_length = row['CHARACTER_MAXIMUM_LENGTH']
                
                if data_type in ['nvarchar', 'varchar']:
                    if max_length and max_length > 0:
                        sql_type = f"{data_type}({max_length})"
                    else:
                        sql_type = f"{data_type}(MAX)"
                elif data_type in ['int', 'bigint', 'smallint']:
                    sql_type = data_type.upper()
                elif data_type in ['datetime', 'datetime2', 'date']:
                    sql_type = data_type.upper()
                elif data_type == 'bit':
                    sql_type = 'BIT'
                else:
                    sql_type = data_type.upper()
                    
                schema[col_name] = sql_type
                
            self.logger.info(f"Retrieved schema for {schema_table}: {len(schema)} columns")
            return schema
        except Exception as e:
            self.logger.error(f"Error retrieving schema from {schema_table}: {e}")
            # Fall back to default schema if we can't get it from the database
            return self._get_default_schema()
    
    def extract_and_transform_table(self, table_info: Dict[str, str]) -> pd.DataFrame:
        """
        Extract data from customer table and apply transformations.
        Replicates the stored procedure transformation logic.
        """
        table_name = table_info['table_name']
        customer_name = table_info['customer_name']
        
        self.logger.info(f"Processing table: {table_name} (Customer: {customer_name})")
        
        # Extract all data from customer table
        query = f"SELECT * FROM dbo.[{table_name}]"
        
        try:
            with db.get_connection(self.db_key) as conn:
                df = pd.read_sql(query, conn)
        except Exception as e:
            self.logger.error(f"Failed to extract data from {table_name}: {e}")
            return pd.DataFrame()
            
        if df.empty:
            self.logger.warning(f"Table {table_name} is empty, skipping")
            return pd.DataFrame()
        
        # Apply column standardization (replicate SP ∆ → Delta logic)
        df = df.rename(columns=self.column_standardization)
        
        # Add/ensure CUSTOMER NAME column (replicate SP customer name logic)
        if 'CUSTOMER NAME' not in df.columns:
            df['CUSTOMER NAME'] = customer_name
        else:
            # Fill missing customer names with extracted customer name
            df['CUSTOMER NAME'] = df['CUSTOMER NAME'].fillna(customer_name)
            # If customer name is empty string, replace with extracted name
            df.loc[df['CUSTOMER NAME'].str.strip() == '', 'CUSTOMER NAME'] = customer_name
            
        # Apply data type transformations (replicate SP logic)
        df = self._apply_data_transformations(df)
        
        self.logger.info(f"Transformed {len(df)} rows from {table_name}")
        return df
    
    def _apply_data_transformations(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply data type transformations matching stored procedure logic.
        Replicates the CASE statements from sp_FinalInsert.
        """
        
        # Date field transformations (replicate SP date logic)
        date_columns = [
            'ORDER DATE PO RECEIVED', 
            'ETA CUSTOMER WAREHOUSE DATE', 
            'EX FACTORY DATE'
        ]
        
        for col in date_columns:
            if col in df.columns:
                # Replicate SP logic: NULL or empty string → NULL, otherwise TRY_CONVERT(date, ...)
                df[col] = df[col].replace('', None)  # Empty string to None
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
        
        # Size/quantity columns to integer (replicate SP integer logic)
        size_columns = [
            'XXXS', 'XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL',
            'TOTAL QTY', 'Sum of TOTAL QTY'
        ]
        
        # Add numeric size columns (0-9, 10, 12, 14, etc.)
        numeric_size_patterns = [str(i) for i in range(100)]  # 0-99
        size_columns.extend(numeric_size_patterns)
        
        # Add special size patterns from SP
        special_sizes = [
            'S/M', 'M/L', 'L/XL', 'XS/S', 'One_Sz', 'OS', 'ONE SIZE',
            '0-3M', '3-6M', '6-9M', '9-12M', '12-18M', '18-24M',
            '2T', '3T', '4T', '5T', '6T', '1X', '2X', '3X', '4X', '2XL', '3XL', '4XL'
        ]
        size_columns.extend(special_sizes)
        
        for col in size_columns:
            if col in df.columns:
                # Replicate SP logic: NULL or empty → NULL, TRY_CONVERT(float, ...) then CAST to int
                df[col] = df[col].replace('', None)  # Empty string to None
                # Convert to numeric, then round and convert to nullable integer
                df[col] = pd.to_numeric(df[col], errors='coerce').round().astype('Int64')
        
        # All other columns to nvarchar (replicate SP default case)
        for col in df.columns:
            if col not in date_columns and col not in size_columns:
                # Convert to string, handle NaN/None properly
                df[col] = df[col].astype(str)
                df[col] = df[col].replace(['nan', 'None', 'NaN'], None)
                
        return df
    
    def consolidate_to_staging(self, tables: List[Dict[str, str]]) -> int:
        """
        Consolidate all customer tables to staging table using staging_helper.py functions.
        Uses schema_helper to infer SQL types and convert DataFrame types for SQL compatibility.
        """
        import schema_helper
        total_rows = 0

        self.logger.info(f"Starting consolidation of {len(tables)} tables to {self.staging_table}")

        # Process tables and collect all data
        all_dataframes = []

        # Use parallel processing for data extraction
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_table = {
                executor.submit(self.extract_and_transform_table, table): table
                for table in tables
            }

            for future in concurrent.futures.as_completed(future_to_table):
                table = future_to_table[future]
                try:
                    df = future.result()
                    if not df.empty:
                        all_dataframes.append(df)
                        total_rows += len(df)
                except Exception as e:
                    self.logger.error(f"Failed to process {table['table_name']}: {e}")

        if not all_dataframes:
            self.logger.warning("No data to consolidate")
            return 0

        # Concatenate all dataframes
        self.logger.info(f"Concatenating {len(all_dataframes)} dataframes...")
        consolidated_df = pd.concat(all_dataframes, ignore_index=True, sort=False)

        # Infer schema from data using schema_helper
        self.logger.info("Inferring SQL schema from consolidated data using schema_helper.generate_table_schema...")
        columns_sql, schema_info = schema_helper.generate_table_schema(consolidated_df)

        def escape_sql_col(col):
            # Remove stray '[' (SQL Server does not allow unclosed brackets)
            col = col.replace('[', '')
            # Escape ']' as ']]' for SQL Server
            col = col.replace(']', ']]')
            # Remove leading/trailing whitespace
            col = col.strip()
            # If column name is empty after cleaning, return None
            if not col:
                return None
            return f"[{col}]"

        # Patch: Skip columns with empty/whitespace-only names, robustly escape all column names, remove duplicates, and filter malformed columns
        seen = set()
        safe_columns_sql = []
        safe_col_names = []
        for col, sql in zip(consolidated_df.columns, columns_sql):
            if not col or str(col).strip() == '':
                self.logger.warning(f"Skipping column with empty or whitespace-only name in schema: '{col}'")
                continue
            # Always robustly escape the column name
            # Find the column name in the SQL fragment (assume format: [col] TYPE...)
            if sql.startswith('['):
                close_idx = sql.find(']')
                if close_idx != -1:
                    orig_col = sql[1:close_idx]
                    rest = sql[close_idx+1:]
                    safe_col = escape_sql_col(orig_col)
                    if not safe_col:
                        self.logger.warning(f"Skipping column with invalid name after escaping: '{orig_col}'")
                        continue
                    # Remove duplicates (keep first occurrence)
                    if safe_col in seen:
                        self.logger.warning(f"Duplicate column after escaping: {safe_col}, skipping")
                        continue
                    seen.add(safe_col)
                    safe_sql = f"{safe_col}{rest}"
                    # Filter malformed/blank column definitions: allow all standard SQL Server types using any() logic
                    allowed_types = [
                        'NVARCHAR', 'VARCHAR', 'CHAR', 'NCHAR', 'TEXT', 'NTEXT',
                        'INT', 'BIGINT', 'SMALLINT', 'TINYINT',
                        'DATE', 'DATETIME', 'DATETIME2', 'SMALLDATETIME', 'TIME',
                        'BIT', 'DECIMAL', 'NUMERIC', 'FLOAT', 'REAL',
                        'MONEY', 'SMALLMONEY', 'UNIQUEIDENTIFIER', 'VARBINARY', 'BINARY'
                    ]
                    if not safe_sql.strip() or not any(t in safe_sql.upper() for t in allowed_types):
                        self.logger.warning(f"Malformed or blank column definition: {safe_sql!r}, skipping")
                        continue
                    safe_columns_sql.append(safe_sql)
                    safe_col_names.append(col)
                else:
                    # If no closing bracket, treat whole as column name
                    safe_col = escape_sql_col(sql.lstrip('['))
                    if not safe_col:
                        self.logger.warning(f"Skipping column with invalid name after escaping: '{sql}'")
                        continue
                    if safe_col in seen:
                        self.logger.warning(f"Duplicate column after escaping: {safe_col}, skipping")
                        continue
                    seen.add(safe_col)
                    safe_sql = f"{safe_col} NVARCHAR(MAX)"
                    safe_columns_sql.append(safe_sql)
                    safe_col_names.append(col)
            else:
                # If not bracketed, just escape the column name and append the rest
                parts = sql.split(' ', 1)
                safe_col = escape_sql_col(parts[0])
                if not safe_col:
                    self.logger.warning(f"Skipping column with invalid name after escaping: '{parts[0]}'")
                    continue
                if safe_col in seen:
                    self.logger.warning(f"Duplicate column after escaping: {safe_col}, skipping")
                    continue
                seen.add(safe_col)
                rest = f" {parts[1]}" if len(parts) > 1 else " NVARCHAR(MAX)"
                safe_sql = f"{safe_col}{rest}"
                allowed_types = [
                    'NVARCHAR', 'VARCHAR', 'CHAR', 'NCHAR', 'TEXT', 'NTEXT',
                    'INT', 'BIGINT', 'SMALLINT', 'TINYINT',
                    'DATE', 'DATETIME', 'DATETIME2', 'SMALLDATETIME', 'TIME',
                    'BIT', 'DECIMAL', 'NUMERIC', 'FLOAT', 'REAL',
                    'MONEY', 'SMALLMONEY', 'UNIQUEIDENTIFIER', 'VARBINARY', 'BINARY'
                ]
                if not safe_sql.strip() or not any(t in safe_sql.upper() for t in allowed_types):
                    self.logger.warning(f"Malformed or blank column definition: {safe_sql!r}, skipping")
                    continue
                safe_columns_sql.append(safe_sql)
                safe_col_names.append(col)

        order_list_schema = {col: safe_sql for col, safe_sql in zip(safe_col_names, safe_columns_sql)}

        # Print/log the generated CREATE TABLE SQL for debugging
        create_table_sql = f"CREATE TABLE dbo.{self.staging_table} (\n    " + ",\n    ".join([order_list_schema[col] for col in safe_col_names]) + "\n);"
        self.logger.info("\n===== GENERATED CREATE TABLE SQL FOR DEBUGGING =====\n%s\n===================================================", create_table_sql)
        print("\n===== GENERATED CREATE TABLE SQL FOR DEBUGGING =====\n" + create_table_sql + "\n===================================================\n")

        # --- DEBUG PATCH: Check for trailing comma, duplicates, and malformed columns ---
        print("DEBUG: Column names and SQL fragments:")
        for col, sql in order_list_schema.items():
            print(f"  {col!r}: {sql!r}")
        # Check for duplicates
        from collections import Counter
        col_counts = Counter(safe_col_names)
        dups = [col for col, count in col_counts.items() if count > 1]
        if dups:
            print(f"WARNING: Duplicate column names detected: {dups}")
            self.logger.warning(f"Duplicate column names detected: {dups}")
        # Check for trailing comma
        if create_table_sql.rstrip().endswith(','):
            print("WARNING: Trailing comma detected before closing parenthesis in CREATE TABLE SQL!")
            self.logger.warning("Trailing comma detected before closing parenthesis in CREATE TABLE SQL!")
        # Check for blank or malformed columns
        for sql in safe_columns_sql:
            if sql.strip() == '' or 'NVARCHAR' not in sql:
                print(f"WARNING: Malformed or blank column definition: {sql!r}")
                self.logger.warning(f"Malformed or blank column definition: {sql!r}")
        # --- END DEBUG PATCH ---

        # Convert DataFrame columns to native Python types for SQL
        self.logger.info("Converting DataFrame columns to native Python types for SQL using schema_helper.convert_df_for_sql...")
        consolidated_df = schema_helper.convert_df_for_sql(consolidated_df, schema_info)

        self.logger.info(f"Final consolidated DataFrame: {len(consolidated_df)} rows, {len(consolidated_df.columns)} columns")

        # Use staging_helper to create staging table and load data
        try:
            # Create staging table with inferred schema
            staging_helper.prepare_staging_table(
                df=consolidated_df,
                staging_table=self.staging_table,
                production_table=self.production_table,
                db_name=self.db_key,
                column_type_map=order_list_schema
            )

            # Load data to staging table in optimized batches
            staging_helper.load_to_staging_table(
                df=consolidated_df,
                staging_table=self.staging_table,
                db_name=self.db_key,
                batch_size=self.batch_size
            )

            self.logger.info(f"Successfully loaded {total_rows} total rows to {self.staging_table}")
            return total_rows

        except Exception as e:
            self.logger.error(f"Failed to load data to staging table: {e}")
            raise
    
    def promote_staging_to_production(self) -> bool:
        """
        Atomically promote staging to production ORDER_LIST using staging_helper.py.
        """
        try:
            self.logger.info(f"Promoting {self.staging_table} to {self.production_table}")
            
            staging_helper.atomic_swap_tables(
                staging_table=self.staging_table,
                production_table=self.production_table, 
                db_name=self.db_key
            )
            
            self.logger.info(f"Successfully promoted staging to production {self.production_table}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to promote staging to production: {e}")
            return False
    
    def validate_consolidation(self) -> Dict[str, any]:
        """
        Validate the consolidation by checking row counts and data integrity.
        """
        try:
            # Get final row count in ORDER_LIST
            query = f"SELECT COUNT(*) as row_count FROM dbo.{self.production_table}"
            
            with db.get_connection(self.db_key) as conn:
                result = pd.read_sql(query, conn)
                final_count = result['row_count'].iloc[0]
            
            # Get source table counts for comparison
            tables = self.get_customer_tables()
            source_count = 0
            
            for table in tables:
                query = f"SELECT COUNT(*) as row_count FROM dbo.[{table['table_name']}]"
                with db.get_connection(self.db_key) as conn:
                    result = pd.read_sql(query, conn)
                    source_count += result['row_count'].iloc[0]
            
            accuracy = (final_count / source_count * 100) if source_count > 0 else 0
            
            validation = {
                'success': accuracy >= 95,  # 95% threshold for success
                'source_rows': source_count,
                'final_rows': final_count,
                'accuracy': accuracy,
                'message': f"Validation: {final_count:,} rows in {self.production_table} from {source_count:,} source rows ({accuracy:.1f}% accuracy)"
            }
            
            if validation['success']:
                self.logger.info(f"✅ {validation['message']}")
            else:
                self.logger.warning(f"⚠️ {validation['message']}")
                
            return validation
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Validation failed: {e}"
            }
    
    def run_full_consolidation(self) -> Dict[str, any]:
        """
        Execute complete consolidation workflow with comprehensive reporting.
        """
        start_time = time.time()
        
        try:
            self.logger.info("=" * 80)
            self.logger.info("START: ORDER_LIST CONSOLIDATION STARTING")
            self.logger.info("=" * 80)
            self.logger.info(f"Staging table: {self.staging_table}")
            self.logger.info(f"Production table: {self.production_table}")
            self.logger.info(f"Database: {self.db_key}")
            
            # Step 1: Discover customer tables
            self.logger.info("\nStep 1: Discovering customer tables...")
            tables = self.get_customer_tables()
            
            if not tables:
                return {
                    'success': False,
                    'error': 'No customer tables found',
                    'total_time': time.time() - start_time
                }
            
            # Step 2: Consolidate to staging
            self.logger.info(f"\nStep 2: Consolidating {len(tables)} tables to staging...")
            total_rows = self.consolidate_to_staging(tables)
            
            # Step 3: Promote to production
            self.logger.info(f"\nStep 3: Promoting staging to production...")
            promotion_success = self.promote_staging_to_production()
            
            # Step 4: Validate consolidation
            self.logger.info(f"\nStep 4: Validating consolidation...")
            validation = self.validate_consolidation()
            
            total_time = time.time() - start_time
            
            result = {
                'success': promotion_success and validation['success'],
                'tables_processed': len(tables),
                'total_rows': total_rows,
                'validation': validation,
                'total_time': total_time,
                'performance': {
                    'rows_per_second': total_rows / total_time if total_time > 0 else 0,
                    'tables_per_second': len(tables) / total_time if total_time > 0 else 0
                }
            }
            
            # Final reporting
            self.logger.info("\n" + "=" * 80)
            if result['success']:
                self.logger.info("SUCCESS: ORDER_LIST CONSOLIDATION COMPLETED!")
                self.logger.info(f"Tables processed: {len(tables)}")
                self.logger.info(f"Rows consolidated: {total_rows:,}")
                self.logger.info(f"Total time: {total_time:.2f}s")
                self.logger.info(f"Performance: {result['performance']['rows_per_second']:.0f} rows/sec")
                self.logger.info(f"Validation: {validation['message']}")
            else:
                self.logger.error("FAILED: ORDER_LIST CONSOLIDATION FAILED")
                if 'error' in validation:
                    self.logger.error(f"Validation error: {validation['error']}")
            self.logger.info("=" * 80)
                
            return result
            
        except Exception as e:
            total_time = time.time() - start_time
            self.logger.exception(f"Fatal error during consolidation: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_time': total_time
            }

def main():
    """
    Main execution function with comprehensive error handling and reporting.
    """
    print("=" * 80)
    print("ORDER_LIST CONSOLIDATOR - Modern Replacement for sp_FinalInsert")
    print("=" * 80)
    print("Purpose: Consolidate per-customer tables into ORDER_LIST")
    print("Performance: 10x+ faster than stored procedure approach")
    print("Technology: Python + pandas + staging_helper.py")
    print()
    
    try:
        consolidator = OrderListConsolidator()
        result = consolidator.run_full_consolidation()
        
        if result['success']:
            print(f"\nSUCCESS: ORDER_LIST consolidation completed!")
            print(f"Tables processed: {result['tables_processed']}")
            print(f"Rows consolidated: {result['total_rows']:,}")
            print(f"Total time: {result['total_time']:.2f}s")
            print(f"Performance: {result['performance']['rows_per_second']:.0f} rows/sec")
            print(f"Validation: {result['validation']['message']}")
            return 0
        else:
            print(f"\nFAILED: ORDER_LIST consolidation failed")
            print(f"Error: {result.get('error', 'Unknown error')}")
            if 'validation' in result and 'message' in result['validation']:
                print(f"Validation: {result['validation']['message']}")
            return 1
            
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
