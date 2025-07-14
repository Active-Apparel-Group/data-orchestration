"""
ORDER_LIST Transform - Production Schema-Aware Pipeline
Purpose: DDL-based staging to eliminate NVARCHAR pollution and maintain proper data types
Author: Data Engineering Team
Date: July 10, 2025

Key Innovation:
- Uses schema_aware_staging_helper to create staging tables from DDL, not DataFrame
- Maintains atomicity while enforcing correct data types
- Fixes the root cause: swp_ORDER_LIST created with proper schema
- ONE-TO-ONE canonical mapping: each customer column maps to exactly one DDL column
"""

import sys
import time
import re
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any

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
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

# Import pipeline utilities 
import db_helper as db                                                    # noqa: E402
import logger_helper                                                      # noqa: E402  
import transform_generator_order_lists                                    # noqa: E402
import schema_aware_staging_helper                                        # noqa: E402
import precision_transformer                                              # noqa: E402

# Import specific functions (maintaining existing usage)
from transform_generator_order_lists import set_select_names, load_yaml   # noqa: E402
from schema_aware_staging_helper import enhanced_pipeline_with_proper_schema  # noqa: E402
from precision_transformer import create_precision_transformer           # noqa: E402

class OrderListTransformer:
    """
    Production ORDER_LIST transformer with DDL-based schema preservation
    
    Key Features:
    - Creates swp_ORDER_LIST from DDL schema, not broken production table
    - Maintains atomic swap with proper data types
    - Zero NVARCHAR pollution
    - ONE-TO-ONE canonical mapping: each customer column → exactly one DDL column
    """
    
    def __init__(self):
        self.logger = logger_helper.get_logger(__name__)
        self.db_key = "orders"
        self.target_table = "ORDER_LIST"
        self.staging_table = "swp_ORDER_LIST"  # Schema-aware naming
        
        # Load YAML metadata using existing function
        yaml_path = repo_root / "pipelines" / "utils" / "order_list_schema.yml"
        self.metadata = load_yaml(yaml_path)
        
        # Path to DDL with proper schema
        self.ddl_file_path = repo_root / "db" / "ddl" / "tables" / "orders" / "dbo_order_list.sql"
        
        # Initialize precision transformer for handling INT/DECIMAL issues
        self.precision_transformer = create_precision_transformer()
        
        # Cache for problematic columns per table (smart transformation)
        self.problematic_columns_cache = {}
        
    def run_transform_server_side_optimized(self) -> Dict[str, Any]:
        """
        OPTIMIZED: Process all customers with server-side data cleaning
        No 41M cell Python processing - let SQL Server do the heavy lifting!
        """
        start_time = time.time()
        
        # Get all RAW tables
        raw_tables_df = db.run_query("""
            SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME LIKE 'x%_ORDER_LIST_RAW'
            ORDER BY TABLE_NAME
        """, self.db_key)
        
        if raw_tables_df.empty:
            return {"success": False, "error": "No RAW tables found"}
        
        self.logger.info(f"\n[OPTIMIZED] SERVER-SIDE PROCESSING: {len(raw_tables_df)} customer tables")
        self.logger.info(f"Strategy: Let SQL Server handle data cleaning, avoid 41M cell Python operations")
        self.logger.info(f"DDL Path: {self.ddl_file_path}")
        
        # Step 1: Create staging table from DDL
        from schema_aware_staging_helper import StagingTableManager
        staging_manager = StagingTableManager()
        
        self.logger.info(f"\n[STEP 1] Creating DDL-based staging table...")
        staging_manager.create_staging_table_from_ddl(
            staging_table=self.staging_table,
            ddl_file_path=str(self.ddl_file_path),
            db_name=self.db_key
        )
        self.logger.info(f"✅ Created {self.staging_table} with proper schema")
        
        # Step 2: Process each customer directly to staging using SQL
        successful_customers = []
        failed_customers = []
        total_rows = 0
        
        for idx, row in raw_tables_df.iterrows():
            table_name = row['TABLE_NAME']
            customer_name = table_name.replace('_ORDER_LIST_RAW', '').replace('x', '')
            
            try:
                self.logger.info(f"\n[CUSTOMER {idx+1}/{len(raw_tables_df)}] {customer_name}")
                
                # Generate OPTIMIZED SQL with server-side cleaning
                insert_sql = self.generate_direct_insert_sql(table_name)
                
                # Execute direct INSERT with server-side transforms
                result = db.execute(insert_sql, self.db_key)
                # Fallback: If rowcount is not available, query the staging table for new rows
                if hasattr(result, 'rowcount') and result.rowcount is not None:
                    rows_affected = result.rowcount
                else:
                    count_query = f"SELECT COUNT(*) AS cnt FROM [{self.staging_table}] WHERE [_SOURCE_TABLE] = '{table_name}'"
                    count_df = db.run_query(count_query, self.db_key)
                    rows_affected = int(count_df['cnt'].iloc[0]) if not count_df.empty else 0
                
                total_rows += rows_affected
                successful_customers.append(customer_name)
                self.logger.info(f"   ✅ Inserted {rows_affected} rows (server-side cleaned)")
                
            except Exception as e:
                self.logger.error(f"Failed to process {customer_name}: {e}")
                failed_customers.append(customer_name)
                self.logger.info(f"   ❌ Failed: {e}")
        
        # Step 3: Atomic swap
        if successful_customers:
            self.logger.info(f"\n[STEP 3] Atomic swap: {self.staging_table} → {self.target_table}")
            try:
                staging_manager.atomic_swap_tables(
                    staging_table=self.staging_table,
                    production_table=self.target_table,
                    db_name=self.db_key
                )
                self.logger.info(f"✅ Atomic swap completed successfully")
            except Exception as e:
                self.logger.error(f"Atomic swap failed: {e}")
                return {"success": False, "error": f"Atomic swap failed: {e}"}
        
        duration = time.time() - start_time
        
        return {
            "success": len(successful_customers) > 0,
            "total_customers_processed": len(successful_customers),
            "failed_customers": len(failed_customers),
            "total_rows": total_rows,
            "duration": duration,
            "successful_customers": successful_customers,
            "failed_customers": failed_customers,
            "server_side_optimized": True
        }
    
    def generate_direct_insert_sql(self, table_name: str) -> str:
        """
        Generate INSERT INTO ... SELECT with server-side data cleaning
        All transformations happen in SQL Server, not Python!
        """
        self.logger.info(f"Generating server-side INSERT for {table_name}")
        
        # Get table columns
        columns_df = db.run_query(f"""
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION
        """, self.db_key)
        table_columns = set(columns_df['COLUMN_NAME'].tolist())

        select_expressions = []
        
        # Process each YAML column with server-side transforms
        for col in self.metadata["columns"]:
            canonical_name = col["name"]
            candidates = [canonical_name] + col.get("aliases", [])
            
            # Find first match
            matched_column = None
            for candidate in candidates:
                if candidate in table_columns:
                    matched_column = candidate
                    break
            
            if matched_column:
                # Get server-side transform (already optimized for SQL)
                precision_transform = self.precision_transformer.get_precision_transform(canonical_name)
                
                if precision_transform:
                    # Handle alias mapping
                    if matched_column != canonical_name:
                        expr_with_alias = precision_transform.replace(f"[{canonical_name}]", f"[{matched_column}]")
                        select_expressions.append(expr_with_alias)
                    else:
                        select_expressions.append(precision_transform)
                else:
                    # Simple passthrough with NULL handling
                    select_expressions.append(f"""
                        CASE 
                            WHEN [{matched_column}] IN ('nan', 'none', 'null', '') THEN NULL
                            ELSE [{matched_column}]
                        END AS [{canonical_name}]
                    """)
            else:
                # No match - NULL with proper type
                rules = col.get("rules", [])
                if "int" in rules:
                    select_expressions.append(f"CAST(NULL AS INT) AS [{canonical_name}]")
                elif "decimal" in rules:
                    select_expressions.append(f"CAST(NULL AS DECIMAL(38,4)) AS [{canonical_name}]")
                elif "date" in rules:
                    select_expressions.append(f"CAST(NULL AS DATE) AS [{canonical_name}]")
                else:
                    select_expressions.append(f"CAST(NULL AS NVARCHAR(255)) AS [{canonical_name}]")

        # Build INSERT INTO ... SELECT statement
        column_list = ", ".join(f"[{col['name']}]" for col in self.metadata["columns"])
        column_list += ", [_SOURCE_TABLE]"
        
        select_list = ",\n                ".join(select_expressions)
        select_list += f",\n                '{table_name}' AS [_SOURCE_TABLE]"
        
        return f"""
            INSERT INTO [{self.staging_table}] ({column_list})
            SELECT 
                {select_list}
            FROM [dbo].[{table_name}]
            WHERE [AAG ORDER NUMBER] IS NOT NULL 
            AND LTRIM(RTRIM([AAG ORDER NUMBER])) != ''
        """
    
    def discover_raw_table_columns(self) -> List[str]:
        """Discover actual columns from first available RAW table"""
        raw_tables_df = db.run_query("""
            SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME LIKE 'x%_ORDER_LIST_RAW'
            ORDER BY TABLE_NAME
        """, self.db_key)
        
        if raw_tables_df.empty:
            self.logger.warning("No RAW tables found")
            return []
        
        # Get columns from first table
        first_table = raw_tables_df.iloc[0]['TABLE_NAME']
        columns_df = db.run_query(f"""
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = '{first_table}'
            ORDER BY ORDINAL_POSITION
        """, self.db_key)
        
        columns = columns_df['COLUMN_NAME'].tolist()
        self.logger.info(f"Discovered {len(columns)} columns from {first_table}")
        return columns
    
    def get_problematic_columns_for_table(self, table_name: str) -> Dict[str, Dict[str, Any]]:
        """
        Get columns that actually need transformation for this specific table
        Uses debug_precision_issues.py logic to identify INT/DECIMAL precision issues
        """
        if table_name in self.problematic_columns_cache:
            return self.problematic_columns_cache[table_name]
        
        problematic_columns = {}
        
        # Get columns for this table
        columns_df = db.run_query(f"""
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION
        """, self.db_key)
        existing_columns = set(columns_df['COLUMN_NAME'].tolist())
        
        # Check INT, DECIMAL, and DATE columns from schema
        for col_name, schema_type in self.precision_transformer.schema_types.items():
            if col_name not in existing_columns:
                continue
                
            # Check INT columns for decimal values
            if schema_type in ('INT', 'SMALLINT', 'TINYINT'):
                query = f"""
                    SELECT COUNT(CASE WHEN [{col_name}] LIKE '%.%' THEN 1 END) AS decimal_count
                    FROM [dbo].[{table_name}]
                    WHERE [{col_name}] IS NOT NULL
                """
                try:
                    df = db.run_query(query, self.db_key)
                    if not df.empty and df.iloc[0]['decimal_count'] > 0:
                        problematic_columns[col_name] = {
                            'type': schema_type,
                            'issue': 'decimal_in_int',
                            'transform': 'FLOOR(TRY_CAST([{col}] AS FLOAT))'
                        }
                except Exception as e:
                    self.logger.warning(f"Could not check {col_name} in {table_name}: {e}")
            
            # Check DECIMAL columns for precision issues
            elif schema_type.startswith('DECIMAL') or schema_type.startswith('NUMERIC'):
                # Extract precision info
                import re
                match = re.match(r'(DECIMAL|NUMERIC)\((\d+),(\d+)\)', schema_type)
                if match:
                    precision = int(match.group(2))
                    scale = int(match.group(3))
                    max_whole_digits = precision - scale
                    
                    query = f"""
                        WITH precision_check AS (
                            SELECT COUNT(*) AS issue_count
                            FROM [dbo].[{table_name}]
                            WHERE [{col_name}] IS NOT NULL 
                            AND (
                                LEN(LEFT(CAST(ABS(TRY_CAST([{col_name}] AS FLOAT)) AS VARCHAR(50)), 
                                    CHARINDEX('.', CAST(ABS(TRY_CAST([{col_name}] AS FLOAT)) AS VARCHAR(50)) + '.') - 1)) > {max_whole_digits}
                                OR 
                                LEN(SUBSTRING(CAST(TRY_CAST([{col_name}] AS FLOAT) AS VARCHAR(50)), 
                                    CHARINDEX('.', CAST(TRY_CAST([{col_name}] AS FLOAT) AS VARCHAR(50)) + '.') + 1, 50)) > {scale}
                            )
                        )
                        SELECT issue_count FROM precision_check
                    """
                    try:
                        df = db.run_query(query, self.db_key)
                        if not df.empty and df.iloc[0]['issue_count'] > 0:
                            problematic_columns[col_name] = {
                                'type': schema_type,
                                'issue': 'precision_overflow',
                                'transform': f'TRY_CAST([{{col}}] AS {schema_type})'
                            }
                    except Exception as e:
                        self.logger.warning(f"Could not check {col_name} precision in {table_name}: {e}")
            
            # Check DATE columns for invalid dates
            elif schema_type in ('DATE', 'DATETIME', 'DATETIME2'):
                query = f"""
                    SELECT COUNT(CASE WHEN TRY_CONVERT(DATE, [{col_name}], 120) IS NULL AND [{col_name}] IS NOT NULL THEN 1 END) AS invalid_dates
                    FROM [dbo].[{table_name}]
                    WHERE [{col_name}] IS NOT NULL
                """
                try:
                    df = db.run_query(query, self.db_key)
                    if not df.empty and df.iloc[0]['invalid_dates'] > 0:
                        problematic_columns[col_name] = {
                            'type': schema_type,
                            'issue': 'invalid_date',
                            'transform': 'TRY_CONVERT(DATE, NULLIF(LTRIM(RTRIM([{col}])), \'\'), 120)'
                        }
                except Exception as e:
                    self.logger.warning(f"Could not check {col_name} dates in {table_name}: {e}")
        
        # Cache result
        self.problematic_columns_cache[table_name] = problematic_columns
        
        if problematic_columns:
            self.logger.info(f"Found {len(problematic_columns)} problematic columns in {table_name}: {list(problematic_columns.keys())}")
        else:
            self.logger.info(f"No precision issues found in {table_name}")
        
        return problematic_columns
    
    def generate_transform_sql(self, table_name: str) -> str:
        """
        Generate SQL for a specific RAW table with ONE-TO-ONE canonical mapping
        
        Key principle: Each customer column maps to exactly ONE DDL column (canonical)
        No duplicates possible - each YAML column produces exactly one SELECT expression
        """
        self.logger.info(f"Processing customer table: {table_name}")
        
        columns_df = db.run_query(f"""
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION
        """, self.db_key)
        table_columns = set(columns_df['COLUMN_NAME'].tolist())

        select_expressions = []
        yaml_match_count = 0
        
        # ONE-TO-ONE MAPPING: Process each YAML column exactly once
        for col in self.metadata["columns"]:
            canonical_name = col["name"]  # This is our DDL column name
            candidates = [canonical_name] + col.get("aliases", [])
            
            # Find the FIRST match (canonical or alias) - this ensures ONE-TO-ONE mapping
            matched_column = None
            for candidate in candidates:
                if candidate in table_columns:
                    matched_column = candidate
                    break
            
            if matched_column:
                # We found a match - create exactly ONE SELECT expression for this DDL column
                precision_transform = self.precision_transformer.get_precision_transform(canonical_name)
                
                if precision_transform:
                    # Use precision transformer's optimized SQL
                    if matched_column != canonical_name:
                        # Handle alias: replace [canonical_name] with [matched_column]
                        expr_with_alias = precision_transform.replace(f"[{canonical_name}]", f"[{matched_column}]")
                        select_expressions.append(expr_with_alias)
                    else:
                        # Direct match: use as-is
                        select_expressions.append(precision_transform)
                else:
                    # No transformation needed - pass through as canonical
                    select_expressions.append(f"[{matched_column}] AS [{canonical_name}]")
                    
                yaml_match_count += 1
            else:
                # No match found - create NULL with proper type for DDL compatibility
                rules = col.get("rules", [])
                if "int" in rules:
                    select_expressions.append(f"CAST(NULL AS INT) AS [{canonical_name}]")
                elif "decimal" in rules:
                    select_expressions.append(f"CAST(NULL AS DECIMAL(38,4)) AS [{canonical_name}]")
                elif "date" in rules:
                    select_expressions.append(f"CAST(NULL AS DATE) AS [{canonical_name}]")
                else:
                    select_expressions.append(f"CAST(NULL AS NVARCHAR(255)) AS [{canonical_name}]")

        # Calculate matching statistics
        table_match_count = 0
        missing_columns = []
        for col in table_columns:
            is_found = any(
                col == canonical_name or col in col_meta.get("aliases", [])
                for col_meta in self.metadata["columns"] 
                for canonical_name in [col_meta["name"]]
            )
            if is_found:
                table_match_count += 1
            else:
                missing_columns.append(col)
        
        percent = (table_match_count / len(table_columns) * 100) if table_columns else 0
        self.logger.info(f"Table columns: {len(table_columns)}, Found in YAML: {table_match_count} ({percent:.1f}%)")
        
        if missing_columns:
            self.logger.warning(f"Missing from YAML metadata: {missing_columns}")

        # GUARANTEE: select_expressions has exactly len(self.metadata["columns"]) items
        # Each DDL column represented exactly once
        assert len(select_expressions) == len(self.metadata["columns"]), \
            f"CRITICAL: Expected {len(self.metadata['columns'])} expressions, got {len(select_expressions)}"

        return f"""
            SELECT 
                {','.join(select_expressions)},
                '{table_name}' AS _SOURCE_TABLE
            FROM [dbo].[{table_name}]
            WHERE [AAG ORDER NUMBER] IS NOT NULL 
            AND LTRIM(RTRIM([AAG ORDER NUMBER])) != ''
        """
    
    def run_transform_single_customer(self, table_name: str) -> Dict[str, Any]:
        """Transform a single customer's data with enhanced type handling"""
        start_time = time.time()
        customer_name = table_name.replace('_ORDER_LIST_RAW', '').replace('x', '')
        
        try:
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"PROCESSING: {customer_name}")
            self.logger.info(f"Table: {table_name}")
            self.logger.info(f"{'='*60}")
            
            # Generate SQL with ONE-TO-ONE canonical mapping
            transform_sql = self.generate_transform_sql(table_name)
            
            # Execute query and get DataFrame with proper types
            df = db.run_query(transform_sql, self.db_key)
            
            if df.empty:
                self.logger.info(f"WARNING: No valid data found for {customer_name}")
                return {"success": True, "rows_processed": 0, "customer": customer_name, "table": table_name}
            
            # VERIFICATION: DataFrame should have exactly the right number of columns
            expected_columns = len(self.metadata["columns"]) + 1  # +1 for _SOURCE_TABLE
            if len(df.columns) != expected_columns:
                self.logger.error(f"CRITICAL: Expected {expected_columns} columns, got {len(df.columns)}")
                self.logger.error(f"Columns: {list(df.columns)}")
                # Check for duplicates
                if df.columns.duplicated().any():
                    duplicates = df.columns[df.columns.duplicated()].tolist()
                    self.logger.error(f"Duplicate columns found: {duplicates}")
                    raise ValueError(f"Column count mismatch: expected {expected_columns}, got {len(df.columns)}")
            
            # Show sample data for verification
            self.logger.info(f"Sample data preview (first 3 rows):")
            key_columns = ['AAG ORDER NUMBER', 'DATE PO RECEIVED', 'CUSTOMER', 'STYLE', 'ORDER QTY']
            available_columns = [col for col in key_columns if col in df.columns]
            
            if available_columns:
                sample_data = df[available_columns].head(3)
                self.logger.info(sample_data.to_string(index=False))
                
                # Show data types for verification
                self.logger.info(f"\nData types verification:")
                for col in available_columns:
                    if col in df.columns:
                        sample_val = df[col].dropna().iloc[0] if not df[col].dropna().empty else "NULL"
                        self.logger.info(f"   {col}: {type(sample_val).__name__} = {sample_val}")
            
            duration = time.time() - start_time
            
            result = {
                "success": True,
                "rows_processed": len(df),
                "customer": customer_name,
                "table": table_name,
                "duration": duration,
                "performance": len(df) / duration if duration > 0 else 0,
                "data": df  # Pass data for aggregation
            }
            
            self.logger.info(f"SUCCESS: {customer_name}: {len(df)} rows processed in {duration:.2f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"Transform failed for {customer_name}: {e}")
            self.logger.info(f"ERROR: {customer_name}: Transform failed - {e}")
            return {"success": False, "error": str(e), "customer": customer_name, "table": table_name}
    
    def run_transform_all_customers_schema_aware(self) -> Dict[str, Any]:
        """Process all customers with optimized bulk loading"""
        start_time = time.time()
        
        # Get all RAW tables (FULL PRODUCTION RUN)
        raw_tables_df = db.run_query("""
            SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME LIKE 'x%_ORDER_LIST_RAW'
            ORDER BY TABLE_NAME
        """, self.db_key)
        
        if raw_tables_df.empty:
            return {"success": False, "error": "No RAW tables found"}
        
        self.logger.info(f"\n[PROCESSING] FULL PRODUCTION PROCESSING: {len(raw_tables_df)} customer tables")
        self.logger.info(f"Tables found: {', '.join(raw_tables_df['TABLE_NAME'].tolist())}")
        self.logger.info(f"DDL Path: {self.ddl_file_path}")
        
        all_data = []
        successful_customers = []
        failed_customers = []
        
        # Process each customer table individually
        for idx, row in raw_tables_df.iterrows():
            table_name = row['TABLE_NAME']
            result = self.run_transform_single_customer(table_name)
            
            if result["success"] and result.get("rows_processed", 0) > 0:
                successful_customers.append(result)
                if "data" in result:
                    all_data.append(result["data"])
            elif not result["success"]:
                failed_customers.append(result)
        
        # Consolidate and load using schema-aware pipeline
        total_rows = 0
        if all_data:
            self.logger.info(f"\n[CONSOLIDATION] PRODUCTION DATA CONSOLIDATION FROM {len(all_data)} CUSTOMERS")
            self.logger.info("=" * 80)
            
            # CRITICAL DEBUG: Inspect each DataFrame before concatenation
            self.logger.info(f"[DEBUG] INSPECTING {len(all_data)} DataFrames before concatenation...")
            for i, df in enumerate(all_data):
                customer_source = df['_SOURCE_TABLE'].iloc[0] if '_SOURCE_TABLE' in df.columns and not df.empty else f"DataFrame_{i}"
                customer_name = customer_source.replace('_ORDER_LIST_RAW', '').replace('x', '') if customer_source != f"DataFrame_{i}" else f"Unknown_{i}"
                
                self.logger.info(f"[DEBUG] DataFrame {i+1}: {customer_name}")
                self.logger.info(f"   Rows: {len(df)}, Columns: {len(df.columns)}")
                
                # Check for duplicates in this individual DataFrame
                if df.columns.duplicated().any():
                    duplicates = df.columns[df.columns.duplicated()].tolist()
                    unique_duplicates = list(set(duplicates))
                    self.logger.info(f"   ERROR: Individual DataFrame has duplicates: {unique_duplicates}")
                    
                    # Show which columns appear multiple times
                    from collections import Counter
                    col_counts = Counter(df.columns)
                    multiple_cols = {col: count for col, count in col_counts.items() if count > 1}
                    self.logger.info(f"   ERROR: Column frequencies: {multiple_cols}")
                    
                    # Critical error - should not happen with ONE-TO-ONE mapping
                    raise ValueError(f"Customer {customer_name}: Individual DataFrame has duplicate columns: {unique_duplicates}")
                
                # Show column sample for verification (first 10 columns)
                column_sample = list(df.columns)[:10]
                self.logger.info(f"   Columns (first 10): {column_sample}")
            
            # Check for column consistency across DataFrames
            self.logger.info(f"\n[DEBUG] CROSS-DATAFRAME COLUMN CONSISTENCY CHECK")
            if len(all_data) > 1:
                reference_columns = set(all_data[0].columns)
                for i, df in enumerate(all_data[1:], 1):
                    current_columns = set(df.columns)
                    if current_columns != reference_columns:
                        missing_in_current = reference_columns - current_columns
                        extra_in_current = current_columns - reference_columns
                        self.logger.info(f"   ERROR: DataFrame {i+1} column mismatch!")
                        if missing_in_current:
                            self.logger.info(f"   Missing: {list(missing_in_current)}")
                        if extra_in_current:
                            self.logger.info(f"   Extra: {list(extra_in_current)}")
                        raise ValueError(f"DataFrame {i+1}: Column structure inconsistent with reference DataFrame")
                
                self.logger.info(f"   SUCCESS: All {len(all_data)} DataFrames have identical column structure")
                self.logger.info(f"   Reference columns: {len(reference_columns)} columns")
            
            # SIMPLE CONCATENATION - no complex column logic since ONE-TO-ONE mapping guarantees consistency
            try:
                # Since we enforce ONE-TO-ONE mapping in generate_transform_sql(), 
                # all DataFrames should have identical column structure
                self.logger.info(f"[DEBUG] Attempting pandas concatenation...")
                consolidated_df = pd.concat(all_data, ignore_index=True, sort=False)
                self.logger.info(f"Successfully concatenated {len(all_data)} DataFrames")
                
                # Verify no duplicates (should be impossible with ONE-TO-ONE mapping)
                if consolidated_df.columns.duplicated().any():
                    duplicates = consolidated_df.columns[consolidated_df.columns.duplicated()].tolist()
                    self.logger.error(f"CRITICAL: Duplicates found despite ONE-TO-ONE mapping: {duplicates}")
                    raise ValueError("ONE-TO-ONE mapping violated - this should not happen")
                
            except Exception as concat_error:
                self.logger.error(f"DataFrame concatenation failed: {concat_error}")
                self.logger.info(f"[ERROR] Concatenation failed: {concat_error}")
                self.logger.info(f"[ERROR] This suggests the issue is in pandas concat(), not our DataFrames")
                self.logger.info(f"[SUGGESTION] Try run_transform_incremental_customers() to avoid concatenation")
                return {
                    "success": False, 
                    "error": f"Concatenation failed: {concat_error}",
                    "total_customers_processed": len(successful_customers),
                    "failed_customers": len(failed_customers),
                    "debug_info": f"Failed at concat step with {len(all_data)} DataFrames"
                }
            
            total_rows = len(consolidated_df)
            
            self.logger.info(f"[INFO] Consolidated DataFrame info:")
            self.logger.info(f"   Rows: {len(consolidated_df):,}")
            self.logger.info(f"   Columns: {len(consolidated_df.columns)}")
            
            # Show some sample data types to verify casting worked
            type_samples = {}
            for col in ['ORDER QTY', 'UNIT PRICE', 'DATE PO RECEIVED'][:3]:
                if col in consolidated_df.columns:
                    sample_val = consolidated_df[col].dropna().iloc[0] if not consolidated_df[col].dropna().empty else "NULL"
                    type_samples[col] = f"{type(sample_val).__name__} = {sample_val}"
            
            self.logger.info(f"   Sample types: {type_samples}")
            
            # Use schema-aware pipeline - with OPTIMIZED batch size for large datasets
            pipeline_result = enhanced_pipeline_with_proper_schema(
                df=consolidated_df,
                staging_table=self.staging_table,
                production_table=self.target_table,
                db_name=self.db_key,
                ddl_file_path=str(self.ddl_file_path),
                batch_size=5000  # INCREASED from 1000 to 5000 for better performance
            )
            
            if pipeline_result['success']:
                self.logger.info(f"[SUCCESS] SCHEMA-AWARE PIPELINE SUCCESS")
                self.logger.info(f"   {total_rows:,} rows loaded with proper data types")
                self.logger.info(f"   INT columns preserved as INT (not NVARCHAR)")
                self.logger.info(f"   DECIMAL columns preserved as DECIMAL (not NVARCHAR)")
                self.logger.info(f"   Atomic swap completed with correct schema")
            else:
                self.logger.info(f"[ERROR] SCHEMA-AWARE PIPELINE FAILED: {pipeline_result.get('error')}")
                return {"success": False, "error": pipeline_result.get('error')}
        
        duration = time.time() - start_time
        
        return {
            "success": len(successful_customers) > 0,
            "total_customers_processed": len(successful_customers),
            "failed_customers": len(failed_customers),
            "total_rows": total_rows,
            "duration": duration,
            "successful_customers": [c["customer"] for c in successful_customers],
            "failed_customers": [c["customer"] for c in failed_customers] if failed_customers else [],
            "schema_aware": True,
            "ddl_enforced": True,
            "one_to_one_mapping": True  # Guarantee provided
        }
    
    def run_transform_incremental_customers(self) -> Dict[str, Any]:
        """
        ALTERNATIVE APPROACH: Process customers incrementally to avoid massive DataFrame operations
        Each customer processed directly to staging table, then final swap
        """
        start_time = time.time()
        
        # Get all RAW tables
        raw_tables_df = db.run_query("""
            SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME LIKE 'x%_ORDER_LIST_RAW'
            ORDER BY TABLE_NAME
        """, self.db_key)
        
        if raw_tables_df.empty:
            return {"success": False, "error": "No RAW tables found"}
        
        self.logger.info(f"\n[INCREMENTAL] PROCESSING {len(raw_tables_df)} customers incrementally")
        self.logger.info(f"Strategy: Process each customer directly to staging, avoid massive DataFrame consolidation")
        
        # Create staging table once from DDL
        from schema_aware_staging_helper import StagingTableManager
        staging_manager = StagingTableManager()
        
        # Drop and recreate staging table with proper schema
        staging_manager.create_staging_table_from_ddl(
            staging_table=self.staging_table,
            ddl_file_path=str(self.ddl_file_path),
            db_name=self.db_key
        )
        
        successful_customers = []
        failed_customers = []
        total_rows = 0
        
        # Process each customer directly to staging table
        for idx, row in raw_tables_df.iterrows():
            table_name = row['TABLE_NAME']
            customer_name = table_name.replace('_ORDER_LIST_RAW', '').replace('x', '')
            
            try:
                self.logger.info(f"\n[CUSTOMER {idx+1}/{len(raw_tables_df)}] Processing {customer_name}")
                
                # Get transformed data for this customer
                result = self.run_transform_single_customer(table_name)
                
                if result["success"] and result.get("rows_processed", 0) > 0:
                    # Load this customer's data directly to staging table
                    customer_df = result["data"]
                    
                    # Use enhanced bulk insert with larger batch size
                    staging_manager.load_to_staging_table_enhanced(
                        df=customer_df,
                        staging_table=self.staging_table,
                        db_name=self.db_key,
                        batch_size=10000  # Large batch for single customer
                    )
                    
                    total_rows += len(customer_df)
                    successful_customers.append(result)
                    self.logger.info(f"   SUCCESS: {len(customer_df)} rows loaded to staging")
                    
                elif not result["success"]:
                    failed_customers.append(result)
                    self.logger.info(f"   FAILED: {result.get('error')}")
                
            except Exception as e:
                self.logger.error(f"Incremental processing failed for {customer_name}: {e}")
                failed_customers.append({"customer": customer_name, "error": str(e)})
        
        # Final atomic swap
        if successful_customers:
            self.logger.info(f"\n[SWAP] Performing atomic swap: {self.staging_table} -> {self.target_table}")
            try:
                # Atomic swap using DDL-based approach
                swap_result = staging_manager.atomic_swap_tables(
                    staging_table=self.staging_table,
                    production_table=self.target_table,
                    db_name=self.db_key
                )
                
                if swap_result['success']:
                    self.logger.info(f"[SUCCESS] Atomic swap completed successfully")
                else:
                    self.logger.info(f"[ERROR] Atomic swap failed: {swap_result.get('error')}")
                    return {"success": False, "error": swap_result.get('error')}
                    
            except Exception as e:
                self.logger.error(f"Atomic swap failed: {e}")
                return {"success": False, "error": f"Atomic swap failed: {e}"}
        
        duration = time.time() - start_time
        
        return {
            "success": len(successful_customers) > 0,
            "total_customers_processed": len(successful_customers),
            "failed_customers": len(failed_customers),
            "total_rows": total_rows,
            "duration": duration,
            "successful_customers": [c["customer"] for c in successful_customers],
            "failed_customers": [c["customer"] for c in failed_customers] if failed_customers else [],
            "schema_aware": True,
            "ddl_enforced": True,
            "incremental_processing": True
        }
    
    def run(self) -> Dict[str, Any]:
        """Main execution method with schema awareness"""
        self.logger.info("=" * 80)
        self.logger.info("[PROCESS] ORDER_LIST TRANSFORM - PRODUCTION DDL-BASED PIPELINE")
        self.logger.info("=" * 80)
        self.logger.info("Key Innovation:")
        self.logger.info("- Creates swp_ORDER_LIST from DDL schema (not broken production table)")
        self.logger.info("- Enforces proper data types: INT stays INT, DECIMAL stays DECIMAL")
        self.logger.info("- Eliminates NVARCHAR pollution")
        self.logger.info("- Maintains atomic swap capabilities")
        self.logger.info("- ONE-TO-ONE canonical mapping: no duplicate columns possible")
        
        # TRY SERVER-SIDE OPTIMIZED APPROACH FIRST!
        self.logger.info("\n[STRATEGY] Using SERVER-SIDE OPTIMIZED processing")
        self.logger.info("- All data cleaning happens in SQL Server")
        self.logger.info("- No 41M cell Python operations")
        self.logger.info("- Direct INSERT INTO ... SELECT with transforms")
        
        result = self.run_transform_server_side_optimized()
        
        self.logger.info(f"\n{'='*80}")
        self.logger.info("[INFO] FINAL SUMMARY - PRODUCTION RESULTS")
        self.logger.info(f"{'='*80}")
        
        if result["success"]:
            self.logger.info(f"[SUCCESS] Production transform completed successfully!")
            self.logger.info(f"[PROCESS] Server-side optimized: {result.get('server_side_optimized', False)}")
            self.logger.info(f"[INFO] Customers processed: {result['total_customers_processed']}")
            self.logger.info(f"[INFO] Total rows: {result['total_rows']:,}")
            self.logger.info(f"[INFO] Duration: {result['duration']:.2f}s")
            self.logger.info(f"[INFO] Performance: {result['total_rows'] / result['duration']:.0f} rows/sec")
            self.logger.info(f"[INFO] Schema preservation: Proper data types enforced")
            
            if result.get('successful_customers'):
                self.logger.info(f"[SUCCESS] Successful: {', '.join(result['successful_customers'])}")
            
            if result.get('failed_customers'):
                self.logger.info(f"[ERROR] Failed: {', '.join(result['failed_customers'])}")
                
        else:
            self.logger.info(f"[ERROR] Production transform failed: {result.get('error', 'Unknown error')}")
        
        return result

if __name__ == "__main__":
    try:
        transformer = OrderListTransformer()
        result = transformer.run()
        
        if not result["success"]:
            sys.exit(1)
            
    except Exception as e:
        self.logger.info(f"CRITICAL ERROR: {e}")
        sys.exit(1)
