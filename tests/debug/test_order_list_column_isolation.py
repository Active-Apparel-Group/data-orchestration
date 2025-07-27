"""
ORDER_LIST Column Isolation Test - Incremental Diagnostic
========================================================

This script implements the incremental testing approach:
1. Take 100 sample records from processed data
2. Test 1 column, then 2 columns, then 3... until failure
3. Identify exactly which column causes the TDS error
4. Provide detailed data analysis for the problematic column

Usage: python tests/debug/test_order_list_column_isolation.py
"""

import sys
from pathlib import Path
import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Any
import traceback

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

class OrderListColumnIsolationTest:
    """Incremental column testing to isolate TDS data type errors"""
    
    def __init__(self):
        self.logger = logger_helper.get_logger(__name__)
        self.config = db.load_config()
        self.db_key = 'orders'
        self.test_table = 'swp_ORDER_LIST_COLUMN_TEST'
        
        # Get test data from the V2 consolidator output
        self.logger.info("OrderListColumnIsolationTest initialized")
    
    def get_canonical_schema(self) -> Dict[str, str]:
        """Same schema as V2 consolidator"""
        return {
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
            'ETA_CUSTOMER_WAREHOUSE_DATE': 'DATE',
            'EX_FACTORY_DATE': 'DATE',
            'SIZE_XXXS': 'INT', 'SIZE_XXS': 'INT', 'SIZE_XS': 'INT', 'SIZE_S': 'INT',
            'SIZE_M': 'INT', 'SIZE_L': 'INT', 'SIZE_XL': 'INT', 'SIZE_XXL': 'INT',
            'SIZE_XXXL': 'INT', 'SIZE_OS': 'INT',
            'SIZE_0': 'INT', 'SIZE_2': 'INT', 'SIZE_4': 'INT', 'SIZE_6': 'INT',
            'SIZE_8': 'INT', 'SIZE_10': 'INT', 'SIZE_12': 'INT', 'SIZE_14': 'INT',
            'SIZE_16': 'INT', 'SIZE_18': 'INT', 'SIZE_20': 'INT', 'SIZE_22': 'INT',
            'SIZE_24': 'INT', 'SIZE_28': 'INT', 'SIZE_30': 'INT', 'SIZE_32': 'INT',
            'SIZE_34': 'INT', 'SIZE_36': 'INT', 'SIZE_38': 'INT', 'SIZE_40': 'INT',
            'SIZE_42': 'INT', 'SIZE_44': 'INT', 'SIZE_46': 'INT', 'SIZE_48': 'INT',
            'SIZE_50': 'INT',
            'CUSTOMER_PRICE': 'DECIMAL(18,2)',
            'EX_WORKS_USD': 'DECIMAL(18,2)',
            'FINAL_FOB_USD': 'DECIMAL(18,2)',
            'US_DUTY': 'DECIMAL(18,2)',
            'US_TARIFF': 'DECIMAL(18,2)',
            'DDP_US_USD': 'DECIMAL(18,2)',
            'DESTINATION': 'NVARCHAR(255)',
            'DELIVERY_TERMS': 'NVARCHAR(100)',
            'TRACKING_NUMBER': 'NVARCHAR(100)',
            'SHOP_NAME': 'NVARCHAR(255)',
            'SHOP_CODE': 'NVARCHAR(100)',
            'MAKE_OR_BUY': 'NVARCHAR(100)',
            'FACILITY_CODE': 'NVARCHAR(100)',
            'COUNTRY_OF_ORIGIN': 'NVARCHAR(100)',
            'EXTENDED_COLUMNS': 'NVARCHAR(MAX)',
            'SOURCE_TABLE': 'NVARCHAR(255)',
            'LAST_UPDATED': 'DATETIME2 DEFAULT GETDATE()',
            'CREATED_DATE': 'DATETIME2 DEFAULT GETDATE()'
        }
    
    def get_sample_data(self, limit: int = 100) -> pd.DataFrame:
        """Get sample data from one customer table for testing"""
        self.logger.info(f"Getting {limit} sample records for testing...")
        
        # Get a table with decent data
        query = """
        SELECT TOP 1 TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME LIKE 'xGREYSON%ORDER_LIST' 
        AND TABLE_SCHEMA = 'dbo'
        """
        
        with db.get_connection(self.db_key) as conn:
            table_result = pd.read_sql(query, conn)
            
            if table_result.empty:
                # Fallback to any customer table
                query = """
                SELECT TOP 1 TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME LIKE 'x%ORDER_LIST' 
                AND TABLE_NAME NOT LIKE 'swp_%'
                AND TABLE_SCHEMA = 'dbo'
                """
                table_result = pd.read_sql(query, conn)
            
            table_name = table_result['TABLE_NAME'].iloc[0]
            self.logger.info(f"Using sample table: {table_name}")
            
            # Get sample data
            sample_query = f"SELECT TOP {limit} * FROM dbo.[{table_name}]"
            df = pd.read_sql(sample_query, conn)
            
            self.logger.info(f"Retrieved {len(df)} sample records")
            return df
    
    def prepare_test_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply same transformations as V2 consolidator"""
        self.logger.info("Applying V2 consolidator transformations to sample data...")
        
        # Apply column mapping (simplified version)
        column_mapping = {
            'CUSTOMER': 'CUSTOMER_NAME',
            'AAG ORDER NUMBER': 'AAG_ORDER_NUMBER',
            'PO NUMBER': 'PO_NUMBER',
            'CUSTOMER PRICE': 'CUSTOMER_PRICE',
            'TOTAL QTY': 'TOTAL_QTY'
        }
        df = df.rename(columns=column_mapping)
        
        # Ensure required columns
        if 'CUSTOMER_NAME' not in df.columns:
            df['CUSTOMER_NAME'] = 'TEST_CUSTOMER'
        if 'SOURCE_TABLE' not in df.columns:
            df['SOURCE_TABLE'] = 'TEST_SOURCE'
        
        # Date transformations
        date_columns = ['ORDER_DATE_PO_RECEIVED', 'ETA_CUSTOMER_WAREHOUSE_DATE', 'EX_FACTORY_DATE']
        for col in date_columns:
            if col in df.columns:
                df[col] = df[col].replace('', None)
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
        
        # Integer transformations
        size_columns = [col for col in df.columns if col.startswith('SIZE_') or col == 'TOTAL_QTY']
        for col in size_columns:
            if col in df.columns:
                df[col] = df[col].replace('', None)
                series = pd.to_numeric(df[col], errors='coerce').round()
                df[col] = series.where(pd.notna(series), None).astype(object)
        
        # CRITICAL: Price column transformations (this is likely where the issue is)
        price_columns = [col for col in df.columns if 'PRICE' in col or 'USD' in col or 'DUTY' in col or 'TARIFF' in col]
        for col in price_columns:
            if col in df.columns:
                self.logger.info(f"Processing price column: {col}")
                original_values = df[col].copy()
                
                # Show original data types and sample values
                self.logger.info(f"  Original dtype: {original_values.dtype}")
                self.logger.info(f"  Sample values: {original_values.head(10).tolist()}")
                self.logger.info(f"  Unique values count: {original_values.nunique()}")
                
                df[col] = df[col].replace('', None)
                numeric_series = pd.to_numeric(df[col], errors='coerce')
                
                # Check for problematic values BEFORE transformation
                problematic_mask = (
                    numeric_series.isin([float('inf'), float('-inf')]) |
                    (numeric_series.abs() > 9999999999999999.99)
                )
                if problematic_mask.any():
                    self.logger.warning(f"  Found {problematic_mask.sum()} problematic values in {col}")
                    problematic_values = numeric_series[problematic_mask]
                    self.logger.warning(f"  Problematic values: {problematic_values.tolist()}")
                
                # Apply transformations
                numeric_series = numeric_series.replace([float('inf'), float('-inf')], None)
                numeric_series = numeric_series.where(
                    (numeric_series.abs() <= 9999999999999999.99) | pd.isna(numeric_series), 
                    None
                )
                df[col] = numeric_series.round(2)
                
                # Show final data
                self.logger.info(f"  Final dtype: {df[col].dtype}")
                self.logger.info(f"  Final sample: {df[col].head(10).tolist()}")
        
        # String columns
        canonical_schema = self.get_canonical_schema()
        string_columns = [col for col in df.columns 
                         if col not in date_columns + size_columns + price_columns 
                         and col in canonical_schema]
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).replace(['nan', 'None', 'NaN'], None)
        
        # Add metadata
        df['CREATED_DATE'] = datetime.now()
        df['LAST_UPDATED'] = datetime.now()
        
        # Filter to canonical columns only
        canonical_columns = set(canonical_schema.keys())
        available_columns = list(set(df.columns).intersection(canonical_columns))
        df = df[available_columns]
        
        self.logger.info(f"Prepared test data: {len(df)} rows, {len(available_columns)} columns")
        return df
    
    def create_test_table(self, columns: List[str]) -> str:
        """Create test table with specific columns"""
        canonical_schema = self.get_canonical_schema()
        
        # Build CREATE TABLE statement
        column_definitions = []
        for col in columns:
            if col in canonical_schema:
                col_def = canonical_schema[col]
                # Remove DEFAULT constraints for test table
                col_def = col_def.replace(' DEFAULT GETDATE()', '')
                column_definitions.append(f"[{col}] {col_def}")
        
        create_sql = f"""
        IF OBJECT_ID('dbo.{self.test_table}', 'U') IS NOT NULL
            DROP TABLE dbo.{self.test_table}
        
        CREATE TABLE dbo.{self.test_table} (
            {', '.join(column_definitions)}
        )
        """
        
        with db.get_connection(self.db_key) as conn:
            cursor = conn.cursor()
            cursor.execute(create_sql)
            conn.commit()
        
        return create_sql
    
    def test_column_insertion(self, df: pd.DataFrame, columns: List[str]) -> Dict[str, Any]:
        """Test inserting data with specific columns"""
        try:
            # Create test table with these columns
            create_sql = self.create_test_table(columns)
            
            # Prepare data subset
            df_subset = df[columns].copy()
            
            # Convert to SQL-compatible types (same as V2 consolidator)
            df_converted = df_subset.copy()
            canonical_schema = self.get_canonical_schema()
            
            for col in df_converted.columns:
                series = df_converted[col]
                
                # Get SQL data type for this column
                sql_type = canonical_schema.get(col, 'NVARCHAR(255)')
                is_decimal_column = 'DECIMAL' in sql_type
                
                # Handle different pandas dtypes for SQL compatibility (SAME AS V2)
                if pd.api.types.is_integer_dtype(series):
                    df_converted[col] = series.where(pd.notna(series), None).astype(object)
                elif pd.api.types.is_float_dtype(series):
                    # Special handling for DECIMAL columns in SQL Server (SAME AS V2)
                    if is_decimal_column:
                        import numpy as np
                        series_clean = series.copy()
                        
                        # Replace inf and -inf
                        series_clean = series_clean.replace([float('inf'), float('-inf')], None)
                        
                        # CRITICAL: Handle numpy.nan specifically for DECIMAL columns
                        try:
                            # Convert to float array first, then check for NaN
                            float_array = series_clean.astype(float, errors='ignore')
                            nan_mask = np.isnan(float_array)
                            series_clean = series_clean.where(~nan_mask, None)
                        except (TypeError, ValueError):
                            # Fallback to pandas.isna() if numpy conversion fails
                            series_clean = series_clean.where(pd.notna(series_clean), None)
                        
                        # Additional validation for extremely large values
                        try:
                            series_clean = series_clean.where(
                                (series_clean.abs() <= 1.79e308) | pd.isna(series_clean), 
                                None
                            )
                        except (TypeError, AttributeError):
                            # If abs() fails, just ensure None for null values
                            series_clean = series_clean.where(pd.notna(series_clean), None)
                        
                        # FINAL CRITICAL STEP: Convert to Python native types for pyodbc compatibility
                        # This ensures numpy.float64 NaN becomes Python None for SQL Server DECIMAL columns
                        def safe_convert_decimal(val):
                            if pd.isna(val) or val is None:
                                return None
                            if isinstance(val, (np.floating, float)) and np.isnan(val):
                                return None
                            try:
                                return float(val) if val is not None else None
                            except (ValueError, TypeError):
                                return None
                        
                        df_converted[col] = series_clean.apply(safe_convert_decimal)
                        
                    else:
                        # For regular float columns, standard conversion
                        series_clean = series.replace([float('inf'), float('-inf')], None)
                        series_clean = series_clean.where(
                            (series_clean.abs() <= 1.79e308) | pd.isna(series_clean), 
                            None
                        )
                        df_converted[col] = series_clean.where(pd.notna(series_clean), None)
                elif pd.api.types.is_bool_dtype(series):
                    df_converted[col] = series.astype(int).where(pd.notna(series), None)
                elif pd.api.types.is_datetime64_any_dtype(series):
                    df_converted[col] = series.where(pd.notna(series), None)
                else:
                    df_converted[col] = series.where(pd.notna(series) & (series != ''), None)
            
            # Test insertion
            columns_sql = ', '.join([f'[{col}]' for col in columns])
            placeholders = ', '.join(['?' for _ in columns])
            insert_sql = f"INSERT INTO dbo.{self.test_table} ({columns_sql}) VALUES ({placeholders})"
            
            with db.get_connection(self.db_key) as conn:
                cursor = conn.cursor()
                
                # Test with just first row to isolate the issue
                test_row = tuple(df_converted.iloc[0])
                
                self.logger.info(f"Testing columns: {columns}")
                self.logger.info(f"Test row data types: {[type(val) for val in test_row]}")
                self.logger.info(f"Test row values: {test_row}")
                
                cursor.execute(insert_sql, test_row)
                conn.commit()
                
                return {
                    'success': True,
                    'columns': columns,
                    'test_data': test_row,
                    'data_types': [type(val) for val in test_row]
                }
                
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"FAILED with columns {columns}: {error_msg}")
            
            return {
                'success': False,
                'columns': columns,
                'error': error_msg,
                'test_data': tuple(df_converted.iloc[0]) if 'df_converted' in locals() else None,
                'data_types': [type(val) for val in df_converted.iloc[0]] if 'df_converted' in locals() else None
            }
    
    def run_incremental_test(self) -> Dict[str, Any]:
        """Run incremental column testing to find the problematic column"""
        self.logger.info("🧪 Starting incremental column isolation test")
        
        # Get sample data
        sample_df = self.get_sample_data(100)
        prepared_df = self.prepare_test_data(sample_df)
        
        # Get all available columns (sorted for consistent testing)
        all_columns = sorted(prepared_df.columns.tolist())
        self.logger.info(f"Testing {len(all_columns)} columns: {all_columns}")
        
        # Test incrementally: 1 column, then 2, then 3...
        results = []
        last_successful_count = 0
        
        for i in range(1, len(all_columns) + 1):
            columns_to_test = all_columns[:i]
            
            self.logger.info(f"\n🔍 TESTING {i} COLUMNS: {columns_to_test[-1]} (+ {i-1} previous)")
            
            result = self.test_column_insertion(prepared_df, columns_to_test)
            results.append(result)
            
            if result['success']:
                self.logger.info(f"✅ SUCCESS with {i} columns")
                last_successful_count = i
            else:
                self.logger.error(f"❌ FAILED with {i} columns")
                self.logger.error(f"   Problematic column: {columns_to_test[-1]}")
                self.logger.error(f"   Error: {result['error']}")
                
                # Detailed analysis of the failing column
                failing_column = columns_to_test[-1]
                self.analyze_failing_column(prepared_df, failing_column)
                
                break
        
        # Summary
        summary = {
            'total_columns_tested': len(all_columns),
            'last_successful_count': last_successful_count,
            'failing_column': columns_to_test[-1] if not result['success'] else None,
            'all_results': results
        }
        
        self.logger.info(f"\n📊 SUMMARY:")
        self.logger.info(f"   Last successful: {last_successful_count} columns")
        if summary['failing_column']:
            self.logger.info(f"   Failing column: {summary['failing_column']}")
        
        return summary
    
    def analyze_failing_column(self, df: pd.DataFrame, column: str):
        """Detailed analysis of the failing column"""
        self.logger.info(f"\n🔬 DETAILED ANALYSIS OF FAILING COLUMN: {column}")
        
        if column not in df.columns:
            self.logger.error(f"Column {column} not found in DataFrame")
            return
        
        series = df[column]
        
        self.logger.info(f"   Data type: {series.dtype}")
        self.logger.info(f"   Length: {len(series)}")
        self.logger.info(f"   Non-null count: {series.count()}")
        self.logger.info(f"   Null count: {series.isnull().sum()}")
        
        # Show unique values
        unique_values = series.dropna().unique()
        self.logger.info(f"   Unique values count: {len(unique_values)}")
        self.logger.info(f"   Unique values sample: {unique_values[:20].tolist()}")
        
        # For numeric columns, check for problematic values
        if pd.api.types.is_numeric_dtype(series):
            numeric_series = pd.to_numeric(series, errors='coerce')
            
            inf_count = numeric_series.isin([float('inf'), float('-inf')]).sum()
            if inf_count > 0:
                self.logger.warning(f"   ⚠️  Infinite values: {inf_count}")
            
            # Check for extremely large values
            large_values = numeric_series[numeric_series.abs() > 1e15]
            if len(large_values) > 0:
                self.logger.warning(f"   ⚠️  Extremely large values: {len(large_values)}")
                self.logger.warning(f"   Sample large values: {large_values.head(10).tolist()}")
            
            # Check for values that might cause DECIMAL precision issues
            if 'PRICE' in column or 'USD' in column:
                # Check for values that exceed DECIMAL(18,2) precision
                problematic_precision = numeric_series[
                    (numeric_series.abs() >= 10**16) & numeric_series.notna()
                ]
                if len(problematic_precision) > 0:
                    self.logger.warning(f"   ⚠️  Values exceeding DECIMAL(18,2): {len(problematic_precision)}")
                    self.logger.warning(f"   Sample: {problematic_precision.head(10).tolist()}")
        
        # Show problematic values in detail
        problematic_values = []
        for i, val in enumerate(series.head(10)):
            try:
                # Try to convert like SQL would
                if pd.isna(val):
                    converted = None
                elif isinstance(val, (int, float)):
                    if val == float('inf') or val == float('-inf'):
                        problematic_values.append(f"Row {i}: {val} (INFINITE)")
                    elif abs(val) > 9999999999999999.99:
                        problematic_values.append(f"Row {i}: {val} (TOO_LARGE)")
                    else:
                        converted = val
                else:
                    converted = str(val) if val != '' else None
            except Exception as e:
                problematic_values.append(f"Row {i}: {val} (CONVERSION_ERROR: {e})")
        
        if problematic_values:
            self.logger.warning(f"   ⚠️  Problematic values found:")
            for pv in problematic_values:
                self.logger.warning(f"      {pv}")

def main():
    """Run the incremental column isolation test"""
    print("🧪 ORDER_LIST Column Isolation Test")
    print("=" * 50)
    
    tester = OrderListColumnIsolationTest()
    
    try:
        summary = tester.run_incremental_test()
        
        print(f"\n🎯 FINAL RESULT:")
        if summary['failing_column']:
            print(f"   ❌ IDENTIFIED PROBLEMATIC COLUMN: {summary['failing_column']}")
            print(f"   ✅ {summary['last_successful_count']} columns work fine")
        else:
            print(f"   ✅ ALL {summary['total_columns_tested']} columns work!")
        
        return summary['failing_column'] is None
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
