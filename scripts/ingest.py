#!/usr/bin/env python3
"""
ORDER_LIST Data Ingest Pipeline
===============================

Migrates data from 45 customer ORDER_LIST tables into the unified ORDER_LIST table.
Handles column mapping, deduplication, type conversions, and data validation.

Usage:
    python scripts/ingest.py --customer GREYSON --dry-run
    python scripts/ingest.py --all-customers --execute
"""
import sys
from pathlib import Path
import pandas as pd
import argparse
from datetime import datetime
import yaml

# Standard import pattern - use this in ALL scripts
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

# Import from utils/
import db_helper as db
import logger_helper

def convert_na_values(values):
    """
    Enhanced version with better DECIMAL/NULL handling (matches proven test logic)
    """
    from decimal import Decimal
    import numpy as np
    converted = []
    for val in values:
        # Handle all pandas null types
        if pd.isna(val):
            converted.append(None)
        # Handle numpy numeric types
        elif hasattr(val, 'item'):
            try:
                if isinstance(val, (float, np.floating)):
                    if abs(val) > 1e15:
                        converted.append(None)
                    else:
                        converted.append(float(val))
                else:
                    converted.append(val.item())
            except:
                converted.append(None)
        # Handle Decimal compatibility
        elif isinstance(val, (float, int)):
            if val in (float('inf'), float('-inf')):
                converted.append(None)
            else:
                try:
                    dec_val = Decimal(str(val))
                    converted.append(float(dec_val))
                except:
                    converted.append(None)
        # Handle string nulls
        elif isinstance(val, str) and val.strip().lower() in ['nan', 'null', 'none', '']:
            converted.append(None)
        else:
            converted.append(val)
    return converted

class OrderListIngest:
    def get_target_schema_details(self):
        """Get detailed schema information for the target ORDER_LIST table"""
        schema = {}
        with db.get_connection('orders') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COLUMN_NAME, 
                    DATA_TYPE,
                    CHARACTER_MAXIMUM_LENGTH,
                    NUMERIC_PRECISION,
                    NUMERIC_SCALE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'ORDER_LIST'
            """)
            for col in cursor.fetchall():
                schema[col[0]] = {
                    'data_type': col[1],
                    'max_length': col[2],
                    'precision': col[3],
                    'scale': col[4]
                }
        return schema

    def validate_numeric_value(self, value, col_name, schema_info):
        """Validate a numeric value against the target column schema"""
        from decimal import Decimal, InvalidOperation
        if pd.isna(value) or value is None:
            return True  # NULLs are handled by DB constraints
        col_schema = schema_info.get(col_name, {})
        if not col_schema:
            return True  # No schema info - skip validation
        try:
            dec_value = Decimal(str(value))
        except (InvalidOperation, ValueError):
            return False
        # Check precision and scale for numeric/decimal columns
        if col_schema['data_type'] in ('decimal', 'numeric'):
            prec = col_schema.get('precision', 18)
            scale = col_schema.get('scale', 2)
            # Check precision (total digits)
            digits = len(str(dec_value).replace('.', '').replace('-', ''))
            if digits > prec:
                return False
            # Check scale (decimal places)
            if dec_value.as_tuple().exponent and abs(dec_value.as_tuple().exponent) > scale:
                return False
        return True

    def coerce_numeric_value(self, value, col_name, schema_info):
        """
        Coerce numeric values to match target column specifications
        with maximum 4 decimal precision enforcement
        """
        from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
        
        if pd.isna(value) or value is None:
            return None
        
        col_schema = schema_info.get(col_name, {})
        if not col_schema:
            return value
        
        try:
            dec_value = Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None
        
        # Handle decimal/numeric columns
        if col_schema['data_type'] in ('decimal', 'numeric'):
            prec = col_schema.get('precision', 18)
            scale = col_schema.get('scale', 2)
            
            # FORCE MAXIMUM 4 DECIMAL PLACES REGARDLESS OF SCHEMA
            max_scale = min(scale, 4)  # Use schema scale or 4, whichever is smaller
            
            try:
                # Round to max 4 decimal places
                coerced = dec_value.quantize(
                    Decimal('1.' + '0' * max_scale), 
                    rounding=ROUND_HALF_UP
                )
                
                # Check if rounded value still fits in precision
                if len(str(coerced).replace('.','').replace('-','')) > prec:
                    return None
                    
                return float(coerced)
            except:
                return None
        
        # Handle integer columns with range check
        elif col_schema['data_type'] in ('int', 'bigint', 'smallint', 'tinyint'):
            try:
                int_value = int(dec_value.quantize(Decimal('1.'), rounding=ROUND_HALF_UP))
                # Range enforcement (existing code)
                dtype = col_schema['data_type']
                if dtype == 'tinyint' and not (0 <= int_value <= 255):
                    return None
                elif dtype == 'smallint' and not (-32768 <= int_value <= 32767):
                    return None
                elif dtype == 'int' and not (-2147483648 <= int_value <= 2147483647):
                    return None
                elif dtype == 'bigint' and not (-9223372036854775808 <= int_value <= 9223372036854775807):
                    return None
                return int_value
            except:
                return None

        return value

    def transform_data_types(self, df, column_mapping, schema_info=None, table_name=None):
        """Transform data types with precision/scale coercion and capture lost/coerced values for exception reporting"""
        target_schema = self.get_target_schema_details()
        if not hasattr(self, 'lost_value_records'):
            self.lost_value_records = []
        for source_col, target_col in column_mapping.items():
            if source_col not in df.columns:
                continue
            col_schema = target_schema.get(target_col, {})
            dtype = col_schema.get('data_type', str(df[source_col].dtype))
            # Save original values for comparison
            original_series = df[source_col].copy()
            # Numeric/decimal/int columns
            if target_col in target_schema and target_schema[target_col]['data_type'] in ('decimal', 'numeric', 'int', 'bigint', 'smallint', 'tinyint'):
                df[source_col] = df[source_col].apply(lambda x: self.coerce_numeric_value(x, target_col, target_schema))
                # After coercion, compare for lost values (now null but was not null before)
                coerced_series = df[source_col]
                lost_mask = original_series.notnull() & coerced_series.isnull()
                for idx in original_series[lost_mask].index:
                    self.lost_value_records.append({
                        'table': table_name if table_name else '',
                        'row_index': idx,
                        'column': target_col,
                        'data_type': dtype,
                        'input_value': original_series.loc[idx]
                    })
                original_non_null = original_series.notna().sum()
                coerced_non_null = coerced_series.notna().sum()
                if coerced_non_null < original_non_null:
                    self.logger.warning(
                        f"Coerced {source_col}->{target_col}: "
                        f"Lost {original_non_null - coerced_non_null} values "
                        f"(now {coerced_non_null}/{original_non_null} valid)"
                    )
            # Convert date columns
            elif 'DATE' in target_col.upper():
                try:
                    df[source_col] = df[source_col].replace([
                        'nan', 'NaN', 'NULL', 'null', 'None', '', '<NA>', 'NaT', 'N/A', 'n/a', 'NA', 'na', ' '
                    ], pd.NaT)
                    df[source_col] = pd.to_datetime(df[source_col], errors='coerce')
                    msg = f"Converted {source_col} -> DATETIME"
                    self.logger.debug(msg.encode('ascii', 'replace').decode('ascii'))
                except Exception as e:
                    msg = f"Failed to convert {source_col} to DATETIME: {e}"
                    self.logger.warning(msg.encode('ascii', 'replace').decode('ascii'))
            else:
                df[source_col] = df[source_col].replace([
                    'nan', 'NaN', 'NULL', 'null', 'None', '', '<NA>', 'NaT', 'N/A', 'n/a', 'NA', 'na', ' '
                ], None)
        # FINAL: Convert all pandas NA/NaN/NaT and string nulls to Python None for all columns (robust for all dtypes)
        for col in df.columns:
            series = df[col]
            values_list = series.tolist()
            converted_list = []
            for idx, val in enumerate(values_list):
                is_null = False
                if pd.isna(val):
                    is_null = True
                elif isinstance(val, float) and str(val).lower() == 'nan':
                    is_null = True
                elif isinstance(val, str) and val.strip().lower() in [
                    'nan', '<na>', 'nat', 'none', 'null', '', 'n/a', 'na', ' ']:
                    is_null = True
                elif val in [float('inf'), float('-inf')]:
                    is_null = True
                if is_null:
                    converted_list.append(None)
                else:
                    converted_list.append(val)
            # Removed noisy nan debug logging
            df[col] = pd.Series(converted_list, dtype=object)
        return df
    
    def generate_data_quality_report(self, df, column_mapping, target_schema):
        """Generate report showing coercion effects"""
        from decimal import Decimal, InvalidOperation
        report = {
            'coerced_columns': [],
            'type_violations': [],
            'null_changes': [],
            'null_rates': {}
        }
        for source_col, target_col in column_mapping.items():
            if source_col not in df.columns:
                continue
            col_schema = target_schema.get(target_col, {})
            if not col_schema:
                continue
            if col_schema['data_type'] in ('decimal', 'numeric', 'int', 'bigint', 'smallint', 'tinyint'):
                original = df[source_col].copy()
                coerced = original.apply(lambda x: self.coerce_numeric_value(x, target_col, target_schema))
                original_non_null = original.notna().sum()
                coerced_non_null = coerced.notna().sum()
                null_diff = original_non_null - coerced_non_null
                if null_diff > 0:
                    report['null_changes'].append({
                        'column': target_col,
                        'source_column': source_col,
                        'lost_values': null_diff,
                        'original_non_null': original_non_null,
                        'coerced_non_null': coerced_non_null
                    })
                # Check for decimal places being removed
                if col_schema['data_type'] in ('decimal', 'numeric'):
                    scale = col_schema.get('scale', 2)
                    decimal_places_changed = 0
                    for orig_val, coerced_val in zip(original, coerced):
                        if pd.isna(orig_val) or pd.isna(coerced_val):
                            continue
                        try:
                            orig_dec = Decimal(str(orig_val))
                            coerced_dec = Decimal(str(coerced_val))
                            if orig_dec.as_tuple().exponent != coerced_dec.as_tuple().exponent:
                                decimal_places_changed += 1
                        except:
                            pass
                    if decimal_places_changed > 0:
                        report['coerced_columns'].append({
                            'column': target_col,
                            'source_column': source_col,
                            'scale': scale,
                            'decimal_places_changed': decimal_places_changed,
                            'sample_original': original.dropna().head(3).tolist(),
                            'sample_coerced': coerced.dropna().head(3).tolist()
                        })
                elif col_schema['data_type'] in ('int', 'bigint', 'smallint', 'tinyint'):
                    decimal_removed = 0
                    for val in original:
                        if pd.isna(val):
                            continue
                        try:
                            if float(val) % 1 != 0:
                                decimal_removed += 1
                        except:
                            pass
                    if decimal_removed > 0:
                        report['coerced_columns'].append({
                            'column': target_col,
                            'source_column': source_col,
                            'decimals_removed': decimal_removed,
                            'sample_original': original.dropna().head(3).tolist(),
                            'sample_coerced': coerced.dropna().head(3).tolist()
                        })
            # Track null rates
            null_rate = df[source_col].isnull().mean()
            report['null_rates'][target_col] = null_rate
        return report
    """
    ORDER_LIST data ingestion pipeline with column mapping and validation
    """
    
    def __init__(self, dry_run=True):
        self.logger = logger_helper.get_logger(__name__)
        self.dry_run = dry_run
        self.config = db.load_config()
        
        # Load column mappings from schema analysis
        self.load_column_mappings()
        
    def load_column_mappings(self):
        """Load column mappings and fixes from schema analysis"""
        self.logger.info("Loading column mappings and fixes...")
        
        # Fixed column name mappings (from your fixes)
        self.column_fixes = {
            'COUNTRY OF ORIGN': 'COUNTRY OF ORIGIN',
            'PROMO GROUP / CAMPAIGN (HOT 30/GLOBAL EDIT': 'PROMO GROUP / CAMPAIGN (HOT 30/GLOBAL EDIT)',
        }
        
        # Duplicate column handling (keep first occurrence, case-insensitive)
        self.duplicate_columns = {
            'column1': 'Column1',  # Keep the first occurrence
            'longson alias': 'LONGSON ALIAS',
            'validation': 'VALIDATION',
        }
        
        # Size columns - all map to INT
        self.size_columns = [
            '0-3M', '10/M', '11-12 years', '12-18M', '12/18 MTHS', '13-14 years',
            '18-24M', '18/24 MTHS', '1Y', '2Y', '3-4 years', '3-6M', '3/6 MTHS',
            '3Y', '4Y', '5-6 years', '6-12M', '6-9M', '6/12 MTHS', '7-8 years',
            '9-10 years', '9-12M', '10-12', '10/11', '11-14', '12-14', '12/13',
            '2/3', '2T', '3-4', '30/30', '30/32', '31/30', '31/32', '32/30',
            '32/32', '32/34', '32/36', '33/30', '33/32', '34/30', '34/32',
            '34/34', '35/30', '35/32', '36/30', '36/32', '36/34', '38/30',
            '38/32', '38/34', '38/36', '3T', '4/5', '40/30', '40/32', '4T',
            '4XT', '5-6', '5T', '6-10', '6/7', '6T', '7-8', '8/9', '9-10',
            'L(10-12)', 'L(14-16)', 'M(10-12)', 'M(8-10)', 'S(6-8)', '04/XXS',
            '06/XS', '08/S', '12/L', '14/XL', '16/XXL', '18/XXXL', '1X', '2X',
            '2XL', '3X', '3XL', '4X', '4XL', 'L', 'M', 'S', 'S+', 'S-PETITE',
            'XL', 'XS', 'XS-PETITE', 'XXL', 'XXS', 'XXXL', 'XXXS', 'L-XL',
            'S-M', 'S/P', 'XL/2XL', 'XXL/3XL', 'XXS/XS', '0', '0w', '1', '10',
            '10w', '12', '12w', '14', '16', '18', '2', '20', '22', '24', '25',
            '26', '27', '28', '29', '2w', '3', '30', '31', '32', '33', '34',
            '35', '36', '38', '4', '40', '42', '43', '44', '45', '46', '48',
            '4w', '5', '50', '52', '54', '56', '58', '6', '60', '6w', '7', '8',
            '8w', '9', '28-30L', '30-30L', '30-31L', '30-32L', '30X30', '30x32',
            '31-30L', '31-31L', '31-32L', '31X30', '32-30L', '32-31L', '32-32L',
            '32X30', '32x32', '32x34', '33-30L', '33-31L', '33-32L', '34-30L',
            '34-31L', '34-32L', '34X30', '34x32', '34x34', '35-30L', '35-31L',
            '35-32L', '36-30L', '36-31L', '36-32L', '36X30', '36x32', '36x34',
            '38-30L', '38-31L', '38-32L', '38X30', '38x32', '38x34', '40-30L',
            '40-31L', '40X30', '40x32', '40x34', 'AB/M', 'AB/S', 'AB/XL',
            'C/L', 'C/M', 'C/S', 'C/XL', 'C/XS', 'CD/L', 'CD/M', 'CD/S',
            'CD/XL', 'CD/XS', 'D/L', 'D/M', 'D/S', 'D/XL', 'D/XS', 'D/XXL',
            'L/XL', 'M/L', 'O/S', 'S/M', 'XL/XXL', 'XS/S', '32C', '32D',
            '32DD', '32DDD', '34C', '34D', '34DD', '34DDD', '36C', '36D',
            '36DD', '36DDD', '38C', '38D', '38DD', '38DDD', 'ONE SIZE', 'OS',
            'One Sz', 'One_Sz'
        ]
        
        self.logger.info(f"Loaded {len(self.column_fixes)} column fixes")
        self.logger.info(f"Loaded {len(self.duplicate_columns)} duplicate mappings")
        self.logger.info(f"Loaded {len(self.size_columns)} size columns")
    
    def get_customer_tables(self):
        """Get list of customer ORDER_LIST tables"""
        self.logger.info("Discovering customer ORDER_LIST tables...")
        
        sql = """
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
        AND (
            TABLE_NAME LIKE 'x%_ORDER_LIST%'
            OR TABLE_NAME LIKE 'x%ORDER_LIST%'
        )
        AND TABLE_NAME != 'ORDER_LIST'
        ORDER BY TABLE_NAME
        """
        
        with db.get_connection('orders') as conn:
            df = pd.read_sql(sql, conn)
            tables = df['TABLE_NAME'].tolist()
        
        self.logger.info(f"Found {len(tables)} customer ORDER_LIST tables")
        for table in tables:
            self.logger.info(f"  - {table}")
        return tables
    
    def analyze_source_columns(self, table_name):
        """Analyze columns in source customer table"""
        self.logger.info(f"Analyzing columns in {table_name}...")
        
        sql = f"""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table_name}'
        ORDER BY ORDINAL_POSITION
        """
        
        with db.get_connection('orders') as conn:
            df = pd.read_sql(sql, conn)
        
        self.logger.info(f"Found {len(df)} columns in {table_name}")
        return df
    
    def map_source_columns(self, source_columns):
        """Map source columns to target ORDER_LIST columns"""
        self.logger.info("Mapping source columns to target schema...")
        
        mapping = {}
        unmapped = []
        duplicates_handled = []
        
        seen_target_columns = set()
        
        for source_col in source_columns:
            # Apply column fixes first
            fixed_col = source_col
            for old_name, new_name in self.column_fixes.items():
                if old_name.lower() in source_col.lower():
                    fixed_col = new_name
                    self.logger.info(f"Applied fix: {source_col} -> {fixed_col}")
                    break
            
            # Handle duplicates (case-insensitive)
            target_col = fixed_col
            lower_target = target_col.lower()
            
            # Check if this is a known duplicate
            for dup_key, canonical_name in self.duplicate_columns.items():
                if dup_key.lower() == lower_target:
                    if canonical_name.lower() in seen_target_columns:
                        duplicates_handled.append(source_col)
                        self.logger.info(f"Skipping duplicate: {source_col} (already mapped to {canonical_name})")
                        continue
                    target_col = canonical_name
                    break
            
            # Check if we've already seen this target column
            if target_col.lower() in seen_target_columns:
                duplicates_handled.append(source_col)
                self.logger.info(f"Skipping duplicate: {source_col} -> {target_col}")
                continue
            
            # Add to mapping
            mapping[source_col] = target_col
            seen_target_columns.add(target_col.lower())
        
        self.logger.info(f"Column mapping results:")
        self.logger.info(f"  Mapped: {len(mapping)}")
        self.logger.info(f"  Duplicates handled: {len(duplicates_handled)}")
        
        return mapping, duplicates_handled
    
    def standardize_nulls(self, df):
        """Consistent NULL handling across all columns"""
        NULL_EQUIVALENTS = [
            'nan', 'NaN', 'NULL', 'null', 'None', '', '<NA>', 'NaT', 
            'N/A', 'n/a', 'NA', 'na', ' ', '\\N', '\\n', 'NaNAN', 'None'
        ]
        for col in df.columns:
            # Convert string NULL equivalents
            if pd.api.types.is_string_dtype(df[col]):
                df[col] = df[col].replace(NULL_EQUIVALENTS, None)
            # Convert pandas NA types
            df[col] = df[col].where(pd.notna(df[col]), None)
        return df

    def convert_pandas_na_to_none(self, df):
        """
        Convert pandas NA/NaN values to Python None for SQL Server compatibility
        Uses the PROVEN pattern from the working test framework (ORDER_LIST column isolation)
        """
        self.logger.info("Converting pandas NA/NaN values to None for SQL Server compatibility...".encode('ascii', 'replace').decode('ascii'))
        
        # CRITICAL: Use the same conversion pattern as the working test framework
        df_converted = df.copy()
        
        for col in df_converted.columns:
            series = df_converted[col]
            
            # Handle different pandas dtypes for SQL compatibility (SAME AS WORKING TEST)
            if pd.api.types.is_integer_dtype(series):
                df_converted[col] = series.where(pd.notna(series), None).astype(object)
            elif pd.api.types.is_float_dtype(series):
                # CRITICAL: Special handling for DECIMAL columns in SQL Server 
                # FIXED: Use proven list conversion method for numpy.float64(nan) -> None
                msg = f"Converting float column {col} with list method"
                self.logger.debug(msg.encode('ascii', 'replace').decode('ascii'))
                
                # WORKING METHOD: Convert to list, replace NaN, convert back
                values_list = series.tolist()
                converted_list = [None if pd.isna(val) else val for val in values_list]
                
                # Replace inf and -inf values too
                converted_list = [None if val in [float('inf'), float('-inf')] else val for val in converted_list]
                
                # Create new series from converted list
                df_converted[col] = pd.Series(converted_list, dtype=object)
            else:
                # String/object columns - convert pandas NA to Python None
                df_converted[col] = series.where(pd.notna(series), None)
        
        self.logger.info("Applied working test framework NA conversion pattern".encode('ascii', 'replace').decode('ascii'))
        return df_converted

    def validate_column_null_rates(self, df, threshold=0.9):
        """Log warning for columns with high NULL rates"""
        null_rates = df.isnull().mean()
        high_null_cols = null_rates[null_rates > threshold].index.tolist()
        if high_null_cols:
            self.logger.warning(f"Columns with >{threshold*100}% NULLs: {high_null_cols}")
            for col in high_null_cols:
                sample = df[col].dropna().head(3).tolist()
                self.logger.info(f"  {col}: Sample values - {sample}")
        return high_null_cols

    def validate_numeric_ranges(self, df, numeric_cols):
        """Check for values that might overflow SQL Server types. Suppress non-numeric warnings for size columns."""
        for col in numeric_cols:
            if col in df.columns:
                non_null = df[col].dropna()
                # Only keep numeric values
                numeric_vals = pd.to_numeric(non_null, errors='coerce')
                numeric_vals = numeric_vals.dropna()
                if len(numeric_vals) > 0:
                    min_val = numeric_vals.min()
                    max_val = numeric_vals.max()
                    if abs(min_val) > 1e38 or abs(max_val) > 1e38:
                        self.logger.warning(
                            f"Potential overflow in {col}: range {min_val} to {max_val}")
                # Suppress non-numeric value warnings for size columns
                # (these are often all 'nan' and not meaningful)
                # If you want to enable for other columns, add logic here

    def validate_decimal_precision(self, df, decimal_cols, target_schema):
        """Validate decimal columns don't exceed SQL Server precision using actual schema data types."""
        for col in decimal_cols:
            if col in df.columns and col in target_schema:
                col_schema = target_schema[col]
                # Only validate if column is actually a decimal/numeric type in the schema
                if col_schema.get('data_type') in ('decimal', 'numeric'):
                    non_null = df[col].dropna()
                    if len(non_null) > 0:
                        max_val = non_null.max()
                        min_val = non_null.min()
                        precision = col_schema.get('precision', 'unknown')
                        scale = col_schema.get('scale', 'unknown')
                        self.logger.info(f"Decimal range for {col} (precision={precision}, scale={scale}): {min_val} to {max_val}")
                # Skip non-decimal columns (they shouldn't be in decimal_cols anyway)
                elif col_schema.get('data_type') in ('nvarchar', 'varchar', 'text', 'ntext'):
                    self.logger.debug(f"Skipping decimal validation for {col} - schema type is {col_schema.get('data_type')}")
                    continue

    def ingest_customer_data(self, customer_filter=None):
        """Ingest data from customer tables with schema-driven validation and reporting"""
        tables = self.get_customer_tables()
        target_schema = self.get_target_schema_details()
        if customer_filter:
            tables = [t for t in tables if customer_filter.upper() in t.upper()]
            self.logger.info(f"Filtered to {len(tables)} tables matching '{customer_filter}'")
        if not tables:
            self.logger.error(f"No tables found for customer filter: {customer_filter}")
            return
        total_rows_processed = 0
        total_rows_inserted = 0
        for table_name in tables:
            try:
                self.logger.info(f"Processing table: {table_name}")
                with db.get_connection('orders') as conn:
                    source_df = pd.read_sql(f"SELECT * FROM [{table_name}]", conn)
                if source_df.empty:
                    self.logger.warning(f"Table {table_name} is empty, skipping")
                    continue
                self.logger.info(f"Loaded {len(source_df)} rows from {table_name}")
                total_rows_processed += len(source_df)
                self.validate_column_null_rates(source_df)
                self.validate_numeric_ranges(source_df, self.size_columns + ['CUSTOMER_PRICE'])
                source_df = self.standardize_nulls(source_df)
                source_columns = source_df.columns.tolist()
                schema_info = self.analyze_source_columns(table_name)
                column_mapping, duplicates = self.map_source_columns(source_columns)
                transformed_df = self.transform_data_types(source_df.copy(), column_mapping, schema_info, table_name=table_name)
                # Data quality report
                dq_report = self.generate_data_quality_report(transformed_df, column_mapping, target_schema)
                # Exception report for lost/coerced values
                if hasattr(self, 'lost_value_records') and self.lost_value_records:
                    import os
                    lost_dir = os.path.join('outputs', 'lost_records')
                    os.makedirs(lost_dir, exist_ok=True)
                    lost_df = pd.DataFrame(self.lost_value_records)
                    lost_csv_path = os.path.join(lost_dir, f"lost_records_{table_name}.csv")
                    lost_df.to_csv(lost_csv_path, index=False)
                    self.logger.warning(f"Exception report: {len(lost_df)} lost/coerced values written to {lost_csv_path}")
                # Markdown-style summary
                self.logger.info("\n### Data Quality Report (Markdown Table)\n| Column | Source | Type | Nulls Lost | Decimals Removed | Decimal Places Changed | Sample Original | Sample Coerced |")
                self.logger.info("|--------|--------|------|------------|------------------|----------------------|----------------|---------------|")
                for col in dq_report['coerced_columns']:
                    if 'decimal_places_changed' in col:
                        self.logger.info(f"| {col['column']} | {col['source_column']} | decimal |  |  | {col['decimal_places_changed']} | {col['sample_original']} | {col['sample_coerced']} |")
                    elif 'decimals_removed' in col:
                        self.logger.info(f"| {col['column']} | {col['source_column']} | int |  | {col['decimals_removed']} |  | {col['sample_original']} | {col['sample_coerced']} |")
                for col in dq_report['null_changes']:
                    self.logger.info(f"| {col['column']} | {col['source_column']} |  | {col['lost_values']} |  |  |  |  |")
                # Top null rate columns
                null_rates = sorted(
                    [(col, rate) for col, rate in dq_report['null_rates'].items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
                if null_rates:
                    self.logger.info("\n#### Highest Null Rate Columns:")
                    for col, rate in null_rates:
                        self.logger.info(f"  - {col}: {rate:.1%}")
                # Optionally: Export error rows to CSV for review
                # (You can uncomment and adjust the following block as needed)
                # import pandas as pd
                # error_rows_df = pd.DataFrame(error_rows)
                # error_rows_df.to_csv(f"error_rows_{table_name}.csv", index=False)
                # Prepare target DataFrame efficiently to avoid fragmentation warnings
                # Build a dict of columns, then create DataFrame in one step
                column_data = {
                    target_col: transformed_df[source_col]
                    for source_col, target_col in column_mapping.items()
                    if source_col in transformed_df.columns
                }
                target_df = pd.DataFrame(column_data)
                # Add extra columns in a single assignment
                customer_name = table_name.replace('_ORDER_LIST', '').replace('ORDER_LIST_', '')
                if customer_name.startswith('x'):
                    customer_name = customer_name[1:]
                extra_cols = {
                    'CUSTOMER NAME': customer_name,
                    '_SOURCE_TABLE': table_name,
                    '_INGESTED_AT': datetime.now()
                }
                for col, val in extra_cols.items():
                    target_df[col] = val
                # Build decimal column list properly using schema information
                decimal_cols = []
                for col in target_df.columns:
                    if col in target_schema:
                        col_schema = target_schema[col]
                        if col_schema.get('data_type') in ('decimal', 'numeric'):
                            decimal_cols.append(col)
                
                # Validate only actual decimal columns
                if decimal_cols:
                    self.validate_decimal_precision(target_df, decimal_cols, target_schema)
                # Only insert rows where [AAG ORDER NUMBER] is not null or 'nan' (string or float)
                if '[AAG ORDER NUMBER]' in target_df.columns:
                    col = target_df['[AAG ORDER NUMBER]']
                    mask = (~col.isnull()) & (~col.astype(str).str.lower().isin(['nan', 'none', 'null', '']))
                    insert_df = target_df[mask].drop(columns=['_SOURCE_TABLE', '_INGESTED_AT'], errors='ignore')
                else:
                    insert_df = target_df.drop(columns=['_SOURCE_TABLE', '_INGESTED_AT'], errors='ignore')
                insert_df = self.convert_pandas_na_to_none(insert_df)
                if self.dry_run:
                    self.logger.info(f"DRY RUN: Would insert {len(insert_df)} rows from {table_name}")
                    self.logger.info(f"Target columns: {len(insert_df.columns)}")
                    self.logger.info(f"Sample data shape: {insert_df.shape}")
                    if len(insert_df) > 0:
                        self.logger.info("Sample mapped columns:")
                        for i, (source, target) in enumerate(list(column_mapping.items())[:5]):
                            sample_val = transformed_df[source].iloc[0] if source in transformed_df.columns else 'N/A'
                            self.logger.info(f"  {source} -> {target}: {sample_val}")
                else:
                    self.logger.info(f"Inserting {len(insert_df)} rows into ORDER_LIST...")
                    try:
                        with db.get_connection('orders') as conn:
                            cursor = conn.cursor()
                            columns = ', '.join([f'[{col}]' for col in insert_df.columns])
                            placeholders = ', '.join(['?' for _ in insert_df.columns])
                            sql = f"INSERT INTO [ORDER_LIST] ({columns}) VALUES ({placeholders})"
                            rows = [tuple(convert_na_values(row)) for row in insert_df.values]
                            cursor.executemany(sql, rows)
                            conn.commit()
                            total_rows_inserted += len(insert_df)
                            self.logger.info(f"Successfully inserted {len(insert_df)} rows from {table_name}")
                    except Exception as insert_error:
                        self.logger.error(f"Failed to insert data from {table_name}: {insert_error}")
                        continue
            except Exception as e:
                self.logger.error(f"Failed to process {table_name}: {e}")
                continue
        self.logger.info(f"Ingestion complete!")
        self.logger.info(f"Tables processed: {len(tables)}")
        self.logger.info(f"Total rows processed: {total_rows_processed:,}")
        if not self.dry_run:
            self.logger.info(f"Total rows inserted: {total_rows_inserted:,}")
        else:
            self.logger.info(f"DRY RUN: Would have inserted {total_rows_processed:,} rows")

def main():
    parser = argparse.ArgumentParser(description='ORDER_LIST Data Ingest Pipeline')
    parser.add_argument('--customer', help='Filter to specific customer (e.g., GREYSON)')
    parser.add_argument('--all-customers', action='store_true', help='Process all customer tables')
    parser.add_argument('--dry-run', action='store_true', default=True, help='Run in dry-run mode (default)')
    parser.add_argument('--execute', action='store_true', help='Execute actual data insert')
    
    args = parser.parse_args()
    
    if not args.customer and not args.all_customers:
        parser.error("Must specify either --customer or --all-customers")
    
    dry_run = not args.execute
    
    if dry_run:
        print("🔍 Running in DRY-RUN mode (no data will be inserted)")
    else:
        print("⚠️  Running in EXECUTE mode (data will be inserted!)")
        confirm = input("Are you sure? Type 'YES' to continue: ")
        if confirm != 'YES':
            print("Cancelled.")
            return
    
    # Initialize ingest pipeline
    ingest = OrderListIngest(dry_run=dry_run)
    
    # Run ingestion
    customer_filter = args.customer if args.customer else None
    ingest.ingest_customer_data(customer_filter)

if __name__ == "__main__":
    main()
