"""
ORDER_LIST Incremental Column Diagnosis Test
============================================

This script implements the suggested incremental testing approach:
1. Take 100 records from consolidated data
2. Start with 1 column, then 2, then 3... until it fails
3. Identify the exact problematic column causing TDS errors

Purpose: Find the exact column and data type causing SQL Server insertion failures
"""
import sys
from pathlib import Path
import pandas as pd
import pyodbc
from datetime import datetime
import json
from typing import Dict, List, Any
from decimal import Decimal, InvalidOperation   # ← keep for future use

# Standard import pattern
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

import db_helper as db
import logger_helper

class IncrementalColumnDiagnosticTest:
    def __init__(self):
        self.logger = logger_helper.get_logger(__name__)
        self.db_key = 'dms'
        
    def get_test_data(self) -> pd.DataFrame:
        """Get all xgreyson data using V2 consolidator logic (no row limit)"""
        self.logger.info(f"Getting ALL test records for xgreyson using V2 consolidator logic...")
        sys.path.insert(0, str(repo_root / "notebooks"))
        from order_list_consolidator_v2 import OrderListConsolidatorV2
        consolidator = OrderListConsolidatorV2()
        tables = consolidator.get_customer_tables()
        # Find xgreyson table (case-insensitive match)
        if tables:
            self.logger.info(f"First table keys: {list(tables[0].keys())}")
        else:
            raise Exception("No customer tables found")

        # Try to find the correct key for customer name
        xgreyson_table = None
        for t in tables:
            customer_val = None
            for key in ['customer', 'customer_name', 'name']:
                if key in t:
                    customer_val = t[key]
                    break
            if customer_val and customer_val.lower() == 'xgreyson':
                xgreyson_table = t
                break
            if 'table_name' in t and t['table_name'].lower().startswith('xgreyson'):
                xgreyson_table = t
                break
        if not xgreyson_table:
            raise Exception("xgreyson table not found in customer tables")
        self.logger.info(f"Extracting and standardizing: {xgreyson_table.get('table_name', str(xgreyson_table))} (Customer: xgreyson)")
        df = consolidator.extract_and_standardize_table(xgreyson_table)
        self.logger.info(f"Retrieved {len(df)} rows with {len(df.columns)} columns from xgreyson table")
        return df
    
    def apply_data_transformations(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply the same data transformations as V2 consolidator"""
        self.logger.info("Applying data transformations...")
        
        # Import the V2 consolidator for transformation logic
        sys.path.insert(0, str(repo_root / "notebooks"))
        from order_list_consolidator_v2 import OrderListConsolidatorV2
        
        # Use the V2 consolidator's transformation logic
        consolidator = OrderListConsolidatorV2()
        transformed_df = consolidator.transform_and_validate(df)
        
        return transformed_df
    
    def convert_for_sql(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enhanced SQL conversion with detailed logging and robust Decimal handling"""
        self.logger.info("Converting DataFrame to SQL-compatible types...")
        df_converted = df.copy()
        for col in df_converted.columns:
            series = df_converted[col]
            self.logger.info(f"Processing column '{col}' (dtype: {series.dtype})")
            if pd.api.types.is_integer_dtype(series):
                df_converted[col] = series.where(pd.notna(series), None).astype(object)
                self.logger.info(f"  Converted integer column to object with None for nulls")
            elif pd.api.types.is_float_dtype(series):
                self.logger.info(f"  Processing float column for DECIMAL compatibility...")
                def safe_convert(x):
                    try:
                        if pd.isna(x) or x in (float('inf'), float('-inf')):
                            return None
                        return Decimal(str(x))
                    except (InvalidOperation, ValueError, TypeError):
                        return None
                df_converted[col] = series.apply(safe_convert)
                sample_after = [str(x) if x is not None else 'NULL' for x in df_converted[col].head(5).tolist()][:3]
                null_count = sum(1 for x in df_converted[col] if x is None)
                self.logger.info(f"  Sample after conversion: {sample_after}")
                self.logger.info(f"  NULL values: {null_count}")
                self.logger.info(f"Decimal conversion details for {col}:")
                for val in series.head(5):
                    try:
                        dec_val = Decimal(str(val)) if pd.notna(val) else None
                        self.logger.info(f"  {val} -> {dec_val} (type: {type(dec_val).__name__})")
                    except Exception as e:
                        self.logger.error(f"  Conversion failed for {val}: {str(e)}")
            elif pd.api.types.is_bool_dtype(series):
                df_converted[col] = series.astype(int).where(pd.notna(series), None)
                self.logger.info(f"  Converted boolean to int")
            elif pd.api.types.is_datetime64_any_dtype(series):
                df_converted[col] = series.where(pd.notna(series), None)
                self.logger.info(f"  Processed datetime column")
            else:
                df_converted[col] = series.where(pd.notna(series) & (series != ''), None)
                self.logger.info(f"  Processed string/object column")
        return df_converted
    
    def get_order_list_schema(self) -> Dict[str, str]:
        """Get ORDER_LIST table schema with explicit NULL for DECIMAL columns"""
        return {
            'CUSTOMER_NAME': 'NVARCHAR(255)',
            'AAG_ORDER_NUMBER': 'NVARCHAR(255)',
            'PO_NUMBER': 'NVARCHAR(255)',
            'CUSTOMER_PRICE': 'DECIMAL(18,2) NULL',  # Explicitly allow NULL
            'TOTAL_QTY': 'INT',
            'SOURCE_TABLE': 'NVARCHAR(255)',
            'CREATED_DATE': 'DATETIME2',
            'LAST_UPDATED': 'DATETIME2'
        }
    
    def create_test_table(self, columns: List[str]) -> str:
        """Create test table with specified columns"""
        schema = self.get_order_list_schema()
        table_name = 'ORDER_LIST_TEST'
        
        # Build CREATE TABLE statement
        column_definitions = []
        for col in columns:
            if col in schema:
                column_definitions.append(f"[{col}] {schema[col]}")
        
        create_sql = f"""
        IF OBJECT_ID('dbo.{table_name}', 'U') IS NOT NULL
            DROP TABLE dbo.{table_name}
        
        CREATE TABLE dbo.{table_name} (
            {', '.join(column_definitions)}
        )
        """
        
        with db.get_connection(self.db_key) as conn:
            cursor = conn.cursor()
            cursor.execute(create_sql)
            conn.commit()
        
        self.logger.info(f"Created test table with {len(columns)} columns: {columns}")
        return table_name
    
    def test_insert_columns(self, df: pd.DataFrame, columns: List[str], table_name: str) -> bool:
        """Test inserting ALL data with specified columns, allowing NULLs and logging row-level results. Adds process tracking."""
        try:
            df_subset = df[columns].copy()
            df_subset = self.convert_for_sql(df_subset)
            placeholders = ', '.join(['?' for _ in columns])
            column_list = ', '.join([f'[{col}]' for col in columns])
            insert_sql = f"INSERT INTO dbo.{table_name} ({column_list}) VALUES ({placeholders})"
            self.logger.info(f"Testing INSERT with columns: {columns}")
            success_count = 0
            fail_count = 0
            total_rows = len(df_subset)
            self.logger.info(f"Total rows to insert: {total_rows}")
            with db.get_connection(self.db_key) as conn:
                cursor = conn.cursor()
                for idx, row in df_subset.iterrows():
                    row_data = tuple(row[col] for col in columns)
                    try:
                        cursor.execute(insert_sql, row_data)
                        success_count += 1
                        if idx < 10 or idx == total_rows - 1:
                            self.logger.info(f"  Row {idx}: SUCCESS {row_data}")
                        elif idx % 100 == 0 and idx > 0:
                            self.logger.info(f"  Progress: Inserted {idx} of {total_rows} rows...")
                    except Exception as e:
                        fail_count += 1
                        self.logger.error(f"  Row {idx}: FAILED {row_data} - {str(e)}")
                    if idx % 500 == 0 and idx > 0:
                        self.logger.info(f"  [Process Tracking] {idx} rows processed so far...")
                conn.commit()
            self.logger.info(f"SUCCESS: Inserted {success_count} rows, {fail_count} failed (total: {total_rows})")
            return success_count > 0
        except Exception as e:
            self.logger.error(f"FAILED: {len(columns)} columns - {str(e)}")
            return False
    
    def run_incremental_test(self):
        """Run the enhanced incremental column test with smart skipping and diagnostics (test all columns, no Unicode in logs)"""
        self.logger.info("Starting Enhanced Incremental Column Diagnosis Test")

        # Get test data (xgreyson only, all rows)
        df = self.get_test_data()

        # Apply transformations
        df = self.apply_data_transformations(df)

        # Get all columns present in the DataFrame and schema
        schema = self.get_order_list_schema()
        available_columns = [col for col in df.columns if col in schema]
        # Add any extra columns in df not in schema (for full diagnosis)
        extra_columns = [col for col in df.columns if col not in schema]
        all_columns = available_columns + extra_columns
        self.logger.info(f"Available columns for testing: {all_columns}")

        successful_columns = []
        failed_columns = []
        diagnostics = []  # List of dicts for each failed column
        columns_to_test = all_columns.copy()
        tested_columns = []

        # Smart incremental: always try to add the next column, skip failed ones
        while columns_to_test:
            col = columns_to_test[0]
            test_columns = successful_columns + [col]

            self.logger.info(f"\n{'='*50}")
            self.logger.info(f"TEST {len(test_columns)}: Testing {len(test_columns)} column(s)")
            self.logger.info(f"Columns: {test_columns}")

            # Create test table (only for columns in schema)
            schema_test_columns = [c for c in test_columns if c in schema]
            table_name = self.create_test_table(schema_test_columns)

            # Test insertion (only for columns in schema)
            success = self.test_insert_columns(df, schema_test_columns, table_name)
            tested_columns.append(col)

            if success:
                successful_columns.append(col)
                self.logger.info(f"SUCCESS: {len(test_columns)} columns work fine")
            else:
                self.logger.error(f"FAILURE at column {len(test_columns)}: '{col}'")
                self.logger.error(f"Last working combination: {successful_columns}")
                self.logger.error(f"Problematic column: '{col}'")

                # Analyze the problematic column and collect diagnostics
                diag = self.analyze_problematic_column(df, col, return_dict=True)
                failed_columns.append(col)
                diagnostics.append(diag)

            # Remove this column from columns_to_test (whether pass or fail)
            columns_to_test.pop(0)

        self.logger.info(f"\n{'='*50}")
        self.logger.info("INCREMENTAL TEST COMPLETE")
        self.logger.info(f"Last successful columns: {successful_columns}")
        self.logger.info(f"Failed columns: {failed_columns}")

        # Build diagnostics DataFrame
        if diagnostics:
            diag_df = pd.DataFrame(diagnostics)
            self.logger.info("\nFAILED COLUMN DIAGNOSTICS:")
            self.logger.info(f"\n{diag_df}")
        else:
            self.logger.info("No failed columns!")

        # Print summary
        print("\n===== FINAL SUMMARY =====")
        print(f"Total columns tested: {len(tested_columns)}")
        print(f"Total failed columns: {len(failed_columns)}")
        if diagnostics:
            print("\nFailed column diagnostics:")
            print(diag_df)
        else:
            print("All columns inserted successfully!")
    
    def analyze_problematic_column(self, df: pd.DataFrame, column: str, return_dict=False):
        """Analyze the problematic column in detail. If return_dict, return diagnostics as dict."""
        self.logger.info(f"\nANALYZING PROBLEMATIC COLUMN: '{column}'")

        if column not in df.columns:
            self.logger.error(f"Column '{column}' not found in DataFrame")
            if return_dict:
                return {"column": column, "dtype": None, "non_null": 0, "null": 0, "sample_values": [], "error": "Column not found"}
            return

        series = df[column]
        dtype = str(series.dtype)
        non_null = int(series.count())
        null = int(series.isna().sum())
        sample_values = series.dropna().head(10).tolist()
        inf_count = int(sum(series.isin([float('inf'), float('-inf')]))) if pd.api.types.is_numeric_dtype(series) else 0
        nan_count = int(series.isna().sum()) if pd.api.types.is_numeric_dtype(series) else 0

        self.logger.info(f"Column dtype: {dtype}")
        self.logger.info(f"Column length: {len(series)}")
        self.logger.info(f"Non-null count: {non_null}")
        self.logger.info(f"Null count: {null}")
        self.logger.info(f"Sample non-null values: {sample_values}")
        if pd.api.types.is_numeric_dtype(series):
            self.logger.info(f"Infinite values: {inf_count}")
            self.logger.info(f"NaN count: {nan_count}")
            for i, val in enumerate(series.head(5)):
                self.logger.info(f"  Row {i}: {val} (type: {type(val).__name__})")

        if return_dict:
            return {
                "column": column,
                "dtype": dtype,
                "non_null": non_null,
                "null": null,
                "sample_values": sample_values,
                "inf_count": inf_count,
                "nan_count": nan_count
            }

# Strings that should be treated as null/None in SQL
NULL_LIKE_STRINGS = {"", "none", "null", "nan", "NaN"}

def clean_dataframe_for_sql(df: pd.DataFrame) -> pd.DataFrame:
    """
    Final defensive pass that guarantees every element is either a plain
    Python scalar (int, float, str, datetime) or None.

    This runs AFTER all business-level transformations and just before the
    dataframe is split into tuples for cursor.executemany().
    """
    cleaned_cols = {}
    for col in df.columns:
        s = df[col]

        # Datetimes ─ return native datetime or None
        if pd.api.types.is_datetime64_any_dtype(s):
            cleaned_cols[col] = s.apply(
                lambda v: v.to_pydatetime() if pd.notna(v) else None
            )

        # Integer-like ➜ int / None (avoids Int64(<NA>))
        elif pd.api.types.is_integer_dtype(s):
            cleaned_cols[col] = s.apply(
                lambda v: int(v) if pd.notna(v) else None
            )

        # Float / Decimal ─ strip NaN / ±inf then cast to float
        elif pd.api.types.is_float_dtype(s):
            cleaned_cols[col] = s.apply(
                lambda v: None
                if (pd.isna(v) or v in (float('inf'), float('-inf')))
                else float(v)
            )

        # Everything else treated as string/object
        else:
            cleaned_cols[col] = s.apply(
                lambda v: None
                if (pd.isna(v)
                    or (isinstance(v, str) and v.strip().lower() in NULL_LIKE_STRINGS))
                else str(v)
            )

    # Force object dtype to avoid pandas inserting its own NA scalars later
    return pd.DataFrame(cleaned_cols, dtype=object)

def main():
    """Run the incremental column diagnostic test"""
    test = IncrementalColumnDiagnosticTest()
    test.run_incremental_test()

if __name__ == "__main__":
    main()
