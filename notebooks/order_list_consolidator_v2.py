# --- ORDER_LIST merge utility for testing ---
try:
    from utils.quick_order_list_merge import merge_customer_tables
    merge_customer_tables()
except Exception as e:
    print(f"ORDER_LIST merge step failed: {e}")
#!/usr/bin/env python3
"""
ORDER_LIST Consolidator V2 - Schema-First Approach
==================================================

Modern, robust replacement for sp_FinalInsert with:
- Predefined canonical schema (no dynamic schema inference)
- Three-phase processing (Extract → Transform → Load)
- Comprehensive error handling and validation
- Performance optimization with parallel processing
"""

import sys
from pathlib import Path
import pandas as pd
import logging
from typing import Dict, List, Any, Optional, Tuple
import concurrent.futures
from dataclasses import dataclass
import json
from datetime import datetime, date
import pyodbc

# Add project root for imports
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

import db_helper as db
import logger_helper

@dataclass
class LoadResult:
    """Results from loading data to ORDER_LIST"""
    total_rows_processed: int
    successful_rows: int
    failed_rows: int
    errors: List[Dict[str, Any]]
    processing_time_seconds: float
    
    @property
    def success_rate(self) -> float:
        if self.total_rows_processed == 0:
            return 0.0
        return (self.successful_rows / self.total_rows_processed) * 100

class OrderListConsolidatorV2:
    """
    Schema-first ORDER_LIST consolidator with robust error handling.
    
    Key Design Principles:
    1. Predefined canonical schema (no dynamic inference)
    2. Clean separation: Extract → Transform → Load
    3. Comprehensive error handling at each phase
    4. Performance optimization with parallel processing
    5. Full auditability and rollback capability
    """
    
    def __init__(self, config_path: str = None):
        """Initialize consolidator with configuration"""
        self.logger = logger_helper.get_logger(__name__)
        self.config = db.load_config()
        
        # Database configuration
        self.db_key = 'orders'
        self.staging_table = 'swp_ORDER_LIST_V2'
        self.production_table = 'ORDER_LIST'
        
        # Processing configuration
        self.max_workers = 8
        self.batch_size = 1000
        
        # Column name standardization mapping
        self.column_mapping = self._get_column_mapping()
        
        self.logger.info("OrderListConsolidatorV2 initialized with schema-first approach")
    
    def get_canonical_schema(self) -> Dict[str, str]:
        """
        Define the canonical ORDER_LIST schema.
        This is the single source of truth for the table structure.
        """
        return {
            # Core business columns (standardized names)
            'CUSTOMER_NAME': 'NVARCHAR(255) NOT NULL',
            'AAG_ORDER_NUMBER': 'NVARCHAR(100)',
            'PO_NUMBER': 'NVARCHAR(100)',
            'ORDER_DATE_PO_RECEIVED': 'DATE',
            'CUSTOMER_SEASON': 'NVARCHAR(100)',
            'AAG_SEASON': 'NVARCHAR(100)',
            'DROP_INFO': 'NVARCHAR(100)',
            'STYLE_DESCRIPTION': 'NVARCHAR(255)',
            'CUSTOMER_COLOUR_DESCRIPTION': 'NVARCHAR(255)',
            'PATTERN_ID': 'NVARCHAR(100)',
            'CATEGORY': 'NVARCHAR(100)',
            'TOTAL_QTY': 'INT',
            
            # Date columns
            'ETA_CUSTOMER_WAREHOUSE_DATE': 'DATE',
            'EX_FACTORY_DATE': 'DATE',
            
            # Standardized size columns
            'SIZE_XXXS': 'INT',
            'SIZE_XXS': 'INT',
            'SIZE_XS': 'INT',
            'SIZE_S': 'INT',
            'SIZE_M': 'INT',
            'SIZE_L': 'INT',
            'SIZE_XL': 'INT',
            'SIZE_XXL': 'INT',
            'SIZE_XXXL': 'INT',
            'SIZE_OS': 'INT',  # One Size
            
            # Numeric sizes (common ones)
            'SIZE_0': 'INT',
            'SIZE_2': 'INT',
            'SIZE_4': 'INT',
            'SIZE_6': 'INT',
            'SIZE_8': 'INT',
            'SIZE_10': 'INT',
            'SIZE_12': 'INT',
            'SIZE_14': 'INT',
            'SIZE_16': 'INT',
            'SIZE_18': 'INT',
            'SIZE_20': 'INT',
            'SIZE_22': 'INT',
            'SIZE_24': 'INT',
            
            # Men's sizes
            'SIZE_28': 'INT',
            'SIZE_30': 'INT',
            'SIZE_32': 'INT',
            'SIZE_34': 'INT',
            'SIZE_36': 'INT',
            'SIZE_38': 'INT',
            'SIZE_40': 'INT',
            'SIZE_42': 'INT',
            'SIZE_44': 'INT',
            'SIZE_46': 'INT',
            'SIZE_48': 'INT',
            'SIZE_50': 'INT',
            
            # Pricing columns
            'CUSTOMER_PRICE': 'FLOAT',
            'EX_WORKS_USD': 'FLOAT',
            'FINAL_FOB_USD': 'FLOAT',
            'US_DUTY': 'FLOAT',
            'US_TARIFF': 'FLOAT',
            'DDP_US_USD': 'FLOAT',
            
            # Logistics
            'DESTINATION': 'NVARCHAR(255)',
            'DELIVERY_TERMS': 'NVARCHAR(100)',
            'TRACKING_NUMBER': 'NVARCHAR(100)',
            'SHOP_NAME': 'NVARCHAR(255)',
            'SHOP_CODE': 'NVARCHAR(100)',
            
            # Manufacturing
            'MAKE_OR_BUY': 'NVARCHAR(100)',
            'FACILITY_CODE': 'NVARCHAR(100)',
            'COUNTRY_OF_ORIGIN': 'NVARCHAR(100)',
            
            # Extended data for customer-specific fields
            'EXTENDED_COLUMNS': 'NVARCHAR(MAX)',  # JSON for unmapped columns
            
            # Metadata
            'SOURCE_TABLE': 'NVARCHAR(255)',
            'LAST_UPDATED': 'DATETIME2 DEFAULT GETDATE()',
            'CREATED_DATE': 'DATETIME2 DEFAULT GETDATE()'
        }
    
    def _get_column_mapping(self) -> Dict[str, str]:
        """
        Define mappings from various customer column names to canonical names.
        This handles the different naming conventions across customer tables.
        """
        return {
            # Customer name variations
            'CUSTOMER': 'CUSTOMER_NAME',
            'CUSTOMER NAME': 'CUSTOMER_NAME',
            'CUST': 'CUSTOMER_NAME',
            
            # Order number variations
            'AAG ORDER NUMBER': 'AAG_ORDER_NUMBER',
            'ORDER NUMBER': 'AAG_ORDER_NUMBER',
            'ORDER#': 'AAG_ORDER_NUMBER',
            
            # PO variations
            'PO NUMBER': 'PO_NUMBER',
            'PO#': 'PO_NUMBER',
            'PURCHASE ORDER': 'PO_NUMBER',
            
            # Date variations
            'ORDER DATE PO RECEIVED': 'ORDER_DATE_PO_RECEIVED',
            'PO RECEIVED DATE': 'ORDER_DATE_PO_RECEIVED',
            'ORDER DATE': 'ORDER_DATE_PO_RECEIVED',
            
            # Season variations
            'CUSTOMER SEASON': 'CUSTOMER_SEASON',
            'SEASON': 'CUSTOMER_SEASON',
            'AAG SEASON': 'AAG_SEASON',
            
            # Style variations
            'STYLE DESCRIPTION': 'STYLE_DESCRIPTION',
            'STYLE': 'STYLE_DESCRIPTION',
            'DESCRIPTION': 'STYLE_DESCRIPTION',
            
            # Color variations
            'CUSTOMER COLOUR DESCRIPTION': 'CUSTOMER_COLOUR_DESCRIPTION',
            'COLOR': 'CUSTOMER_COLOUR_DESCRIPTION',
            'COLOUR': 'CUSTOMER_COLOUR_DESCRIPTION',
            
            # Size variations (map various size column names to standardized ones)
            'XXS': 'SIZE_XXS',
            'XS': 'SIZE_XS',
            'S': 'SIZE_S',
            'M': 'SIZE_M',
            'L': 'SIZE_L',
            'XL': 'SIZE_XL',
            'XXL': 'SIZE_XXL',
            'XXXL': 'SIZE_XXXL',
            'OS': 'SIZE_OS',
            'ONE SIZE': 'SIZE_OS',
            
            # Numeric sizes
            '0': 'SIZE_0',
            '2': 'SIZE_2',
            '4': 'SIZE_4',
            '6': 'SIZE_6',
            '8': 'SIZE_8',
            '10': 'SIZE_10',
            '12': 'SIZE_12',
            '14': 'SIZE_14',
            '16': 'SIZE_16',
            '18': 'SIZE_18',
            '20': 'SIZE_20',
            '22': 'SIZE_22',
            '24': 'SIZE_24',
            '28': 'SIZE_28',
            '30': 'SIZE_30',
            '32': 'SIZE_32',
            '34': 'SIZE_34',
            '36': 'SIZE_36',
            '38': 'SIZE_38',
            '40': 'SIZE_40',
            '42': 'SIZE_42',
            '44': 'SIZE_44',
            '46': 'SIZE_46',
            '48': 'SIZE_48',
            '50': 'SIZE_50',
            
            # Quantity variations
            'TOTAL QTY': 'TOTAL_QTY',
            'QTY': 'TOTAL_QTY',
            'QUANTITY': 'TOTAL_QTY',
            
            # Date variations
            'ETA CUSTOMER WAREHOUSE DATE': 'ETA_CUSTOMER_WAREHOUSE_DATE',
            'ETA': 'ETA_CUSTOMER_WAREHOUSE_DATE',
            'EX FACTORY DATE': 'EX_FACTORY_DATE',
            'ETD': 'EX_FACTORY_DATE',
            
            # Price variations
            'CUSTOMER PRICE': 'CUSTOMER_PRICE',
            'PRICE': 'CUSTOMER_PRICE',
            'EX WORKS (USD)': 'EX_WORKS_USD',
            'FINAL FOB (USD)': 'FINAL_FOB_USD',
            
            # Drop variations
            'DROP': 'DROP_INFO',
            'DROP INFO': 'DROP_INFO',
        }
    
    def get_customer_tables(self) -> List[Dict[str, str]]:
        """Discover customer tables with enhanced filtering"""
        self.logger.info("Discovering customer tables...")
        
        query = """
        SELECT 
            TABLE_NAME,
            CASE
                WHEN TABLE_NAME LIKE 'x%ORDER_LIST%'
                THEN REPLACE(
                    SUBSTRING(TABLE_NAME, 2, CHARINDEX('_ORDER_LIST', TABLE_NAME) - 2),
                    '_', ' ')
                ELSE 'UNKNOWN'
            END as CUSTOMER_NAME,
            (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
             WHERE TABLE_NAME = t.TABLE_NAME) as COLUMN_COUNT
        FROM INFORMATION_SCHEMA.TABLES t
        WHERE TABLE_SCHEMA = 'dbo'
        AND TABLE_NAME LIKE 'x%ORDER_LIST'
        AND TABLE_NAME NOT LIKE 'swp_%'
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
        return tables
    
    def extract_and_standardize_table(self, table_info: Dict[str, str]) -> pd.DataFrame:
        """
        Phase 1: Extract data and map to canonical column names
        """
        table_name = table_info['table_name']
        customer_name = table_info['customer_name']
        
        self.logger.info(f"Extracting and standardizing: {table_name} (Customer: {customer_name})")
        
        # Extract all data
        query = f"SELECT * FROM dbo.[{table_name}]"
        
        try:
            with db.get_connection(self.db_key) as conn:
                df = pd.read_sql(query, conn)
        except Exception as e:
            self.logger.error(f"Failed to extract data from {table_name}: {e}")
            return pd.DataFrame()
        
        if df.empty:
            self.logger.warning(f"Table {table_name} is empty")
            return pd.DataFrame()
        
        # Apply column name mapping
        df = df.rename(columns=self.column_mapping)
        
        # Ensure customer name is set
        df['CUSTOMER_NAME'] = customer_name
        df['SOURCE_TABLE'] = table_name
        
        # Collect unmapped columns as extended data
        canonical_columns = set(self.get_canonical_schema().keys())
        unmapped_columns = set(df.columns) - canonical_columns
        
        if unmapped_columns:
            self.logger.info(f"Found {len(unmapped_columns)} unmapped columns in {table_name}")
            # Store unmapped columns as JSON
            extended_data = {}
            for col in unmapped_columns:
                extended_data[col] = df[col].fillna('').astype(str).tolist()
            df['EXTENDED_COLUMNS'] = json.dumps(extended_data)
            # Drop unmapped columns from main DataFrame
            df = df.drop(columns=list(unmapped_columns))
        
        self.logger.info(f"Standardized {len(df)} rows from {table_name}")
        return df
    
    def transform_and_validate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Phase 2: Apply business rules and validate data quality
        """
        self.logger.info(f"Transforming and validating {len(df)} rows")
        
        # Date transformations
        date_columns = ['ORDER_DATE_PO_RECEIVED', 'ETA_CUSTOMER_WAREHOUSE_DATE', 'EX_FACTORY_DATE']
        for col in date_columns:
            if col in df.columns:
                df[col] = df[col].replace('', None)
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
        
        # Integer transformations for size and quantity columns
        size_columns = [col for col in df.columns if col.startswith('SIZE_') or col == 'TOTAL_QTY']
        for col in size_columns:
            if col in df.columns:
                df[col] = df[col].replace('', None)
                # Convert to nullable integer, then to regular int/None for SQL compatibility
                series = pd.to_numeric(df[col], errors='coerce').round()
                df[col] = series.where(pd.notna(series), None).astype(object)
        
        # Decimal transformations for price columns
        price_columns = [col for col in df.columns if 'PRICE' in col or 'USD' in col or 'DUTY' in col or 'TARIFF' in col]
        for col in price_columns:
            if col in df.columns:
                df[col] = df[col].replace('', None)
                # Convert to numeric, handling invalid values
                numeric_series = pd.to_numeric(df[col], errors='coerce')
                # Replace infinite and extremely large values with None
                numeric_series = numeric_series.replace([float('inf'), float('-inf')], None)
                # Cap values at reasonable limits for SQL Server DECIMAL(18,2)
                numeric_series = numeric_series.where(
                    (numeric_series.abs() <= 9999999999999999.99) | pd.isna(numeric_series), 
                    None
                )
                df[col] = numeric_series.round(2)
        
        # String columns - ensure proper handling of nulls
        string_columns = [col for col in df.columns if col not in date_columns + size_columns + price_columns]
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).replace(['nan', 'None', 'NaN'], None)
        
        # Add metadata
        df['CREATED_DATE'] = datetime.now()
        df['LAST_UPDATED'] = datetime.now()
        
        self.logger.info(f"Transformation complete: {len(df)} rows")
        return df
    
    def _convert_for_sql(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert DataFrame to SQL-compatible types, handling pandas nullable types.
        This ensures pyodbc can properly handle all values without NAType errors.
        """
        df_converted = df.copy()
        
        for col in df_converted.columns:
            series = df_converted[col]
            
            # Handle different pandas dtypes for SQL compatibility
            if pd.api.types.is_integer_dtype(series):
                # Convert Int64 (nullable) to regular int/None
                df_converted[col] = series.where(pd.notna(series), None).astype(object)
            elif pd.api.types.is_float_dtype(series):
                # CRITICAL FIX: Convert numpy.float64 NaN to Python None for SQL Server compatibility
                import numpy as np
                series_clean = series.replace([float('inf'), float('-inf')], None)
                
                # Convert numpy.nan to None explicitly
                def convert_float_to_sql(val):
                    if pd.isna(val) or val is None:
                        return None
                    if isinstance(val, (np.floating, float)) and np.isnan(val):
                        return None
                    return float(val) if val is not None else None
                
                df_converted[col] = series_clean.apply(convert_float_to_sql)
            elif pd.api.types.is_bool_dtype(series):
                # Convert boolean to int (SQL Server BIT)
                df_converted[col] = series.astype(int).where(pd.notna(series), None)
            elif pd.api.types.is_datetime64_any_dtype(series):
                # Handle datetime
                df_converted[col] = series.where(pd.notna(series), None)
            else:
                # String/object columns - ensure None instead of NaN
                df_converted[col] = series.where(pd.notna(series) & (series != ''), None)
                
        return df_converted
    
    def load_to_order_list(self, df: pd.DataFrame) -> LoadResult:
        """
        Phase 3: Load data to ORDER_LIST with comprehensive error handling
        """
        start_time = datetime.now()
        total_rows = len(df)
        successful_rows = 0
        failed_rows = 0
        errors = []
        
        self.logger.info(f"Loading {total_rows} rows to ORDER_LIST")
        
        # Ensure table exists with canonical schema
        self._ensure_order_list_table_exists()
        
        # Get canonical schema columns that exist in the DataFrame
        canonical_schema = self.get_canonical_schema()
        df_columns = set(df.columns)
        schema_columns = set(canonical_schema.keys())
          # Only include columns that exist in both
        columns_to_insert = list(df_columns.intersection(schema_columns))
        df_subset = df[columns_to_insert].copy()
        
        # Convert to SQL-compatible types (handle pandas nullable types)
        self.logger.info("Converting DataFrame to SQL-compatible types...")
        df_subset = self._convert_for_sql(df_subset)
        
        # Debug: Check for problematic values in price columns
        price_columns = [col for col in columns_to_insert if 'PRICE' in col or 'USD' in col]
        for col in price_columns:
            if col in df_subset.columns:
                # Check for infinite or extremely large values
                problematic = df_subset[col].replace([None], pd.NA).dropna()
                if len(problematic) > 0:
                    inf_count = sum(problematic.isin([float('inf'), float('-inf')]))
                    large_count = sum(problematic.abs() > 1e15)
                    if inf_count > 0 or large_count > 0:
                        self.logger.warning(f"Column {col}: {inf_count} infinite values, {large_count} extremely large values")

        self.logger.info(f"Inserting {len(columns_to_insert)} columns: {columns_to_insert}")
        
        # Load data in batches with error handling
        try:
            with db.get_connection(self.db_key) as conn:
                # Create INSERT statement
                columns_sql = ', '.join([f'[{col}]' for col in columns_to_insert])
                placeholders = ', '.join(['?' for _ in columns_to_insert])
                insert_sql = f"INSERT INTO dbo.[{self.production_table}] ({columns_sql}) VALUES ({placeholders})"
                
                cursor = conn.cursor()
                
                # Process in batches
                for i in range(0, total_rows, self.batch_size):
                    batch_df = df_subset.iloc[i:i+self.batch_size]
                    batch_data = [tuple(row) for row in batch_df.values]
                    
                    try:
                        cursor.executemany(insert_sql, batch_data)
                        conn.commit()
                        successful_rows += len(batch_data)
                        self.logger.info(f"Loaded batch {i//self.batch_size + 1}: {len(batch_data)} rows")
                    except Exception as e:
                        self.logger.error(f"Batch {i//self.batch_size + 1} failed: {e}")
                        conn.rollback()
                        
                        # Try row-by-row for failed batch
                        for j, row_data in enumerate(batch_data):
                            try:
                                cursor.execute(insert_sql, row_data)
                                conn.commit()
                                successful_rows += 1
                            except Exception as row_error:
                                failed_rows += 1
                                errors.append({
                                    'row_index': i + j,
                                    'error': str(row_error),
                                    'data': dict(zip(columns_to_insert, row_data))
                                })
                                conn.rollback()
                
        except Exception as e:
            self.logger.error(f"Fatal error during load: {e}")
            failed_rows = total_rows
            errors.append({'error': str(e), 'fatal': True})
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        result = LoadResult(
            total_rows_processed=total_rows,
            successful_rows=successful_rows,
            failed_rows=failed_rows,
            errors=errors,
            processing_time_seconds=processing_time
        )
        
        self.logger.info(f"Load complete: {successful_rows}/{total_rows} rows successful ({result.success_rate:.1f}%)")
        return result
    
    def _ensure_order_list_table_exists(self):
        """Ensure ORDER_LIST table exists with canonical schema"""
        canonical_schema = self.get_canonical_schema()
        
        # Check if table exists
        check_query = """
        SELECT COUNT(*) as table_count
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME = ? AND TABLE_SCHEMA = 'dbo'
        """
        
        with db.get_connection(self.db_key) as conn:
            result = pd.read_sql(check_query, conn, params=[self.production_table])
            
            if result['table_count'].iloc[0] == 0:
                self.logger.info(f"Creating {self.production_table} table with canonical schema")
                
                # Build CREATE TABLE statement
                columns_sql = []
                for col_name, col_type in canonical_schema.items():
                    columns_sql.append(f"[{col_name}] {col_type}")
                
                create_sql = f"""
                CREATE TABLE dbo.[{self.production_table}] (
                    {','.join(columns_sql)}
                )
                """
                
                cursor = conn.cursor()
                cursor.execute(create_sql)
                conn.commit()
                self.logger.info(f"Successfully created {self.production_table} table")
            else:
                self.logger.info(f"{self.production_table} table already exists")
    
    def run_full_consolidation(self) -> LoadResult:
        """
        Execute the complete consolidation process:
        1. Discover customer tables
        2. Extract and standardize data (parallel)
        3. Transform and validate combined data
        4. Load to ORDER_LIST with error handling
        """
        self.logger.info("Starting full ORDER_LIST consolidation (Schema-First Approach)")
        
        # Phase 1: Discovery
        tables = self.get_customer_tables()
        if not tables:
            self.logger.warning("No customer tables found")
            return LoadResult(0, 0, 0, [], 0.0)
        
        # Phase 2: Extract and standardize (parallel processing)
        self.logger.info(f"Extracting and standardizing {len(tables)} tables...")
        all_dataframes = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_table = {
                executor.submit(self.extract_and_standardize_table, table): table
                for table in tables
            }
            
            for future in concurrent.futures.as_completed(future_to_table):
                table = future_to_table[future]
                try:
                    df = future.result()
                    if not df.empty:
                        all_dataframes.append(df)
                except Exception as e:
                    self.logger.error(f"Failed to process {table['table_name']}: {e}")
        
        if not all_dataframes:
            self.logger.warning("No data extracted from customer tables")
            return LoadResult(0, 0, 0, [], 0.0)
        
        # Phase 3: Combine and transform
        self.logger.info(f"Combining {len(all_dataframes)} dataframes...")
        combined_df = pd.concat(all_dataframes, ignore_index=True, sort=False)
        
        transformed_df = self.transform_and_validate(combined_df)
        
        # Phase 4: Load
        result = self.load_to_order_list(transformed_df)
        
        # Summary
        self.logger.info("=" * 80)
        self.logger.info("CONSOLIDATION SUMMARY")
        self.logger.info("=" * 80)
        self.logger.info(f"Tables processed: {len(tables)}")
        self.logger.info(f"Total rows: {result.total_rows_processed}")
        self.logger.info(f"Successful: {result.successful_rows}")
        self.logger.info(f"Failed: {result.failed_rows}")
        self.logger.info(f"Success rate: {result.success_rate:.1f}%")
        self.logger.info(f"Processing time: {result.processing_time_seconds:.2f} seconds")
        self.logger.info("=" * 80)
        
        return result

def main():
    """Run the ORDER_LIST consolidation"""
    print("=" * 80)
    print("ORDER_LIST CONSOLIDATOR V2 - Schema-First Approach")
    print("=" * 80)
    print("Features:")
    print("- Predefined canonical schema (no dynamic inference)")
    print("- Three-phase processing (Extract → Transform → Load)")
    print("- Comprehensive error handling and rollback")
    print("- Parallel processing for performance")
    print("- Full auditability and validation")
    print("=" * 80)
    
    try:
        consolidator = OrderListConsolidatorV2()
        result = consolidator.run_full_consolidation()
        
        if result.success_rate >= 95:
            print("✅ CONSOLIDATION SUCCESSFUL")
        elif result.success_rate >= 80:
            print("⚠️  CONSOLIDATION COMPLETED WITH WARNINGS")
        else:
            print("❌ CONSOLIDATION FAILED")
            
        return result.success_rate >= 80
        
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
