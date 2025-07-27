"""
Debug Precision Issues - ORDER_LIST Transform
Purpose: Schema-aware analysis of decimal/int precision issues only
Author: Data Engineering Team  
Date: July 10, 2025
"""

import sys
import time
import os
import re
from pathlib import Path
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional

def find_repo_root() -> Path:
    """Find repository root by looking for utils folder"""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise RuntimeError("Could not find repository root with utils/ folder")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

import db_helper as db
import logger_helper

class PrecisionDiagnostics:
    """Schema-aware analysis of decimal/int/date precision issues only"""
    
    def __init__(self):
        self.logger = logger_helper.get_logger(__name__)
        self.db_key = "orders"
        self.schema_types = {}
        self.load_schema_types()
        
    def load_schema_types(self):
        """Load ORDER_LIST schema types from DDL file"""
        ddl_path = repo_root / "notebooks" / "db" / "ddl" / "updates" / "create_order_list_complete_fixed.sql"
        
        with open(ddl_path, 'r') as f:
            ddl_content = f.read()
        
        # Parse DDL to extract column types - include DATE columns
        # Pattern to match: [COLUMN_NAME] TYPE NULL,
        pattern = r'\[([^\]]+)\]\s+(INT|SMALLINT|TINYINT|DECIMAL\(\d+,\d+\)|NUMERIC\(\d+,\d+\)|DATE|DATETIME|DATETIME2)\s+NULL'
        matches = re.findall(pattern, ddl_content)
        
        for column_name, data_type in matches:
            self.schema_types[column_name] = data_type
        
        # Apply the ALTER statements provided by the user
        # Convert DECIMAL(17,15) to DECIMAL(17,4) for specific columns
        decimal_columns_to_update = [
            'FINAL FOB (USD)',
            'DDP US (USD)',
            'TARIFF RELIEF DISCOUNT (20%)',
            'FOB TO USE ON PRODUCT INVOICE',
            'ADDITIONAL TARIFF RATE'
        ]
        
        for column_name in decimal_columns_to_update:
            if column_name in self.schema_types and self.schema_types[column_name] == 'DECIMAL(17,15)':
                self.schema_types[column_name] = 'DECIMAL(17,4)'
                
        self.logger.info(f"Loaded {len(self.schema_types)} numeric/date column types from DDL")
        
    def extract_decimal_precision(self, decimal_type):
        """Extract precision and scale from DECIMAL(p,s) type"""
        if not decimal_type.startswith('DECIMAL') and not decimal_type.startswith('NUMERIC'):
            return None, None
        
        # Extract numbers from DECIMAL(18,4) or NUMERIC(18,4)
        match = re.match(r'(DECIMAL|NUMERIC)\((\d+),(\d+)\)', decimal_type)
        if match:
            precision = int(match.group(2))
            scale = int(match.group(3))
            return precision, scale
        return None, None
    
    def analyze_precision_requirements(self, value_str):
        """Analyze precision requirements for a decimal value"""
        if not value_str or pd.isna(value_str) or str(value_str).strip() == '':
            return None, None, None, None
            
        try:
            clean_value = str(value_str).strip()
            if '.' in clean_value:
                whole_part, frac_part = clean_value.split('.')
                whole_digits = len(whole_part) if whole_part != '0' else 0
                frac_digits = len(frac_part.rstrip('0'))
                total_digits = whole_digits + frac_digits
                return float(clean_value), whole_digits, frac_digits, total_digits
            else:
                whole_digits = len(clean_value)
                return float(clean_value), whole_digits, 0, whole_digits
        except:
            return None, None, None, None
    
    def analyze_column_for_overflow(self, table_name: str, col_name: str, schema_type: str) -> Dict[str, Any]:
        """Analyze a specific column for potential overflow issues"""
        result = {
            'column': col_name,
            'schema_type': schema_type,
            'issues_found': False,
            'transformations_required': 0,
            'schema_compliant': True,
            'schema_adjustment_required': False,
            'extreme_values': {'min': None, 'max': None},
            'extreme_precision': {'whole': 0, 'fractional': 0},
            'sample_values': []
        }
        
        # For INT columns, check if any values have decimals
        if schema_type in ('INT', 'SMALLINT', 'TINYINT'):
            query = f"""
                SELECT 
                    COUNT(*) AS total_records,
                    COUNT(CASE WHEN [{col_name}] LIKE '%.%' THEN 1 END) AS decimal_values,
                    MIN(TRY_CAST([{col_name}] AS FLOAT)) AS min_value,
                    MAX(TRY_CAST([{col_name}] AS FLOAT)) AS max_value
                FROM [dbo].[{table_name}]
                WHERE [{col_name}] IS NOT NULL
            """
            
            df = db.run_query(query, self.db_key)
            if not df.empty:
                total = df.iloc[0]['total_records'] or 0
                decimal_count = df.iloc[0]['decimal_values'] or 0
                min_val = df.iloc[0]['min_value']
                max_val = df.iloc[0]['max_value']
                
                result['extreme_values']['min'] = min_val
                result['extreme_values']['max'] = max_val
                result['transformations_required'] = decimal_count
                
                if decimal_count > 0:
                    result['issues_found'] = True
                    result['schema_compliant'] = False
                    
                    # Get sample values
                    sample_query = f"""
                        SELECT TOP 5 [{col_name}]
                        FROM [dbo].[{table_name}]
                        WHERE [{col_name}] LIKE '%.%'
                    """
                    sample_df = db.run_query(sample_query, self.db_key)
                    if not sample_df.empty:
                        result['sample_values'] = sample_df[col_name].tolist()
                        
        # For DECIMAL columns, check if any values exceed precision
        elif schema_type.startswith('DECIMAL') or schema_type.startswith('NUMERIC'):
            precision, scale = self.extract_decimal_precision(schema_type)
            if precision is None:
                return result
                
            # Calculate max allowed whole number digits
            max_whole_digits = precision - scale
            
            # Find extreme values and check for precision issues
            query = f"""
                WITH precision_analysis AS (
                    SELECT 
                        [{col_name}] AS value_str,
                        TRY_CAST([{col_name}] AS FLOAT) AS value_float,
                        LEN(LEFT(CAST(ABS(TRY_CAST([{col_name}] AS FLOAT)) AS VARCHAR(50)), 
                            CHARINDEX('.', CAST(ABS(TRY_CAST([{col_name}] AS FLOAT)) AS VARCHAR(50)) + '.') - 1)) AS whole_digits,
                        LEN(SUBSTRING(CAST(TRY_CAST([{col_name}] AS FLOAT) AS VARCHAR(50)), 
                            CHARINDEX('.', CAST(TRY_CAST([{col_name}] AS FLOAT) AS VARCHAR(50)) + '.') + 1, 50)) AS frac_digits
                    FROM [dbo].[{table_name}]
                    WHERE [{col_name}] IS NOT NULL AND TRY_CAST([{col_name}] AS FLOAT) IS NOT NULL
                )
                SELECT
                    COUNT(*) AS total_records,
                    COUNT(CASE WHEN whole_digits > {max_whole_digits} OR frac_digits > {scale} THEN 1 END) AS precision_issues,
                    MIN(value_float) AS min_value,
                    MAX(value_float) AS max_value,
                    MAX(whole_digits) AS max_whole_digits,
                    MAX(frac_digits) AS max_frac_digits
                FROM precision_analysis
            """
            
            df = db.run_query(query, self.db_key)
            if not df.empty:
                total = df.iloc[0]['total_records'] or 0
                precision_issues = df.iloc[0]['precision_issues'] or 0
                min_val = df.iloc[0]['min_value']
                max_val = df.iloc[0]['max_value']
                max_whole = df.iloc[0]['max_whole_digits'] or 0
                max_frac = df.iloc[0]['max_frac_digits'] or 0
                
                result['extreme_values']['min'] = min_val
                result['extreme_values']['max'] = max_val
                result['extreme_precision']['whole'] = max_whole
                result['extreme_precision']['fractional'] = max_frac
                result['transformations_required'] = precision_issues
                
                # Special case for DECIMAL(17,15) that will be converted to DECIMAL(17,4)
                if schema_type == 'DECIMAL(17,15)':
                    # We only care about whole digit overflow now
                    if max_whole > (17-4):  # New scale is 4
                        result['issues_found'] = True
                        result['schema_compliant'] = False
                        result['schema_adjustment_required'] = True
                    elif precision_issues > 0:
                        result['issues_found'] = True
                        result['schema_compliant'] = False
                else:
                    # Check if schema adjustment is required
                    if max_whole > max_whole_digits:
                        result['issues_found'] = True
                        result['schema_compliant'] = False
                        result['schema_adjustment_required'] = True
                    elif max_frac > scale and precision_issues > 0:
                        result['issues_found'] = True
                        result['schema_compliant'] = False
                
                if precision_issues > 0:
                    # Get sample problematic values
                    sample_query = f"""
                        WITH precision_analysis AS (
                            SELECT 
                                [{col_name}] AS value_str,
                                TRY_CAST([{col_name}] AS FLOAT) AS value_float,
                                LEN(LEFT(CAST(ABS(TRY_CAST([{col_name}] AS FLOAT)) AS VARCHAR(50)), 
                                    CHARINDEX('.', CAST(ABS(TRY_CAST([{col_name}] AS FLOAT)) AS VARCHAR(50)) + '.') - 1)) AS whole_digits,
                                LEN(SUBSTRING(CAST(TRY_CAST([{col_name}] AS FLOAT) AS VARCHAR(50)), 
                                    CHARINDEX('.', CAST(TRY_CAST([{col_name}] AS FLOAT) AS VARCHAR(50)) + '.') + 1, 50)) AS frac_digits
                            FROM [dbo].[{table_name}]
                            WHERE [{col_name}] IS NOT NULL AND TRY_CAST([{col_name}] AS FLOAT) IS NOT NULL
                        )
                        SELECT TOP 5 value_str
                        FROM precision_analysis
                        WHERE whole_digits > {max_whole_digits} OR frac_digits > {scale}
                    """
                    sample_df = db.run_query(sample_query, self.db_key)
                    if not sample_df.empty:
                        result['sample_values'] = sample_df['value_str'].tolist()
        
        # For DATE columns, check for invalid date formats
        elif schema_type in ('DATE', 'DATETIME', 'DATETIME2'):
            query = f"""
                SELECT 
                    COUNT(*) AS total_records,
                    COUNT(CASE WHEN TRY_CONVERT(DATE, [{col_name}], 120) IS NULL AND [{col_name}] IS NOT NULL THEN 1 END) AS invalid_dates
                FROM [dbo].[{table_name}]
                WHERE [{col_name}] IS NOT NULL
            """
            
            df = db.run_query(query, self.db_key)
            if not df.empty:
                total = df.iloc[0]['total_records'] or 0
                invalid_count = df.iloc[0]['invalid_dates'] or 0
                
                result['transformations_required'] = invalid_count
                
                if invalid_count > 0:
                    result['issues_found'] = True
                    result['schema_compliant'] = False
                    # Get sample invalid dates
                    sample_query = f"""
                        SELECT TOP 5 [{col_name}] FROM [dbo].[{table_name}]
                        WHERE [{col_name}] IS NOT NULL 
                        AND TRY_CONVERT(DATE, [{col_name}], 120) IS NULL
                    """
                    sample_df = db.run_query(sample_query, self.db_key)
                    result['sample_values'] = [str(val) for val in sample_df[col_name].tolist()[:5]]
        
        return result
    
    def debug_date_columns(self):
        """Debug function to identify problematic date columns and values"""
        print("\n" + "="*80)
        print("DATE COLUMN ANALYSIS")
        print("="*80)
        
        # Get all date columns from schema
        date_columns = []
        for col_name, schema_type in self.schema_types.items():
            if schema_type in ('DATE', 'DATETIME', 'DATETIME2'):
                date_columns.append(col_name)
        
        print(f"Found {len(date_columns)} date columns in schema: {date_columns[:5]}...")
        
        # Get all customer RAW tables
        raw_tables_df = db.run_query("""
            SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME LIKE 'x%_ORDER_LIST_RAW'
            ORDER BY TABLE_NAME
        """, self.db_key)
        
        all_problem_values = {}
        
        # Find problematic date values across all tables
        for date_col in date_columns:
            problem_values = []
            
            for idx, row in raw_tables_df.iterrows():
                table_name = row['TABLE_NAME']
                
                # Check if column exists in this table
                col_exists_df = db.run_query(f"""
                    SELECT COUNT(*) AS col_exists
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = '{table_name}'
                    AND COLUMN_NAME = '{date_col}'
                """, self.db_key)
                
                if col_exists_df.empty or col_exists_df.iloc[0]['col_exists'] == 0:
                    continue
                    
                # Get problematic values for this column
                query = f"""
                    SELECT TOP 50 [{date_col}] AS problem_value, COUNT(*) AS count
                    FROM [dbo].[{table_name}]
                    WHERE [{date_col}] IS NOT NULL
                    AND TRY_CONVERT(DATE, [{date_col}], 120) IS NULL
                    AND TRY_CONVERT(DATE, [{date_col}], 101) IS NULL
                    AND TRY_CONVERT(DATE, [{date_col}], 103) IS NULL
                    AND TRY_CONVERT(DATE, [{date_col}], 110) IS NULL
                    AND TRY_CONVERT(DATE, [{date_col}], 23) IS NULL
                    GROUP BY [{date_col}]
                    ORDER BY COUNT(*) DESC
                """
                
                try:
                    df = db.run_query(query, self.db_key)
                    if not df.empty:
                        for _, pv_row in df.iterrows():
                            value = pv_row['problem_value']
                            count = pv_row['count']
                            problem_values.append({
                                'value': value,
                                'count': count,
                                'table': table_name
                            })
                except Exception as e:
                    print(f"   ⚠️  Error checking {date_col} in {table_name}: {e}")
            
            if problem_values:
                all_problem_values[date_col] = problem_values
        
        # Display results
        print("\n" + "="*80)
        print("DATE COLUMN ANALYSIS RESULTS")
        print("="*80)
        
        if not all_problem_values:
            print("✅ No problematic date values found using standard SQL Server date formats")
            return {}
        
        print(f"🚨 Found problematic date values in {len(all_problem_values)} columns:")
        
        for col, values in all_problem_values.items():
            print(f"\nColumn: {col}")
            print("-" * 40)
            print(f"Total unique problematic values: {len(values)}")
            
            for i, value_info in enumerate(values[:10]):  # Show top 10
                print(f"  {i+1}. '{value_info['value']}' ({value_info['count']} occurrences in {value_info['table']})")
            
            if len(values) > 10:
                print(f"  ... and {len(values) - 10} more problematic values")
        
        # Try to determine patterns
        patterns = self.analyze_date_patterns(all_problem_values)
        
        print("\n" + "="*80)
        print("RECOMMENDED DATE FORMAT SOLUTIONS")
        print("="*80)
        
        for col, pattern_info in patterns.items():
            print(f"\nColumn: {col}")
            print(f"Likely format: {pattern_info['likely_format']}")
            print(f"Suggested SQL: {pattern_info['suggested_sql']}")
        
        return all_problem_values
    
    def analyze_date_patterns(self, problem_values):
        """Analyze date patterns to suggest appropriate conversions"""
        patterns = {}
        
        for col, values in problem_values.items():
            sample_values = [v['value'] for v in values if v['value']][:5]
            
            # Pattern detection logic
            has_slashes = any('/' in str(v) for v in sample_values)
            has_dashes = any('-' in str(v) for v in sample_values)
            has_dots = any('.' in str(v) for v in sample_values)
            
            # Check for MM/DD/YY format (2 digit year)
            two_digit_year = any(re.match(r'\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2}$', str(v)) for v in sample_values)
            
            # Check for special formats like 'Jul 10 2025'
            text_month = any(re.match(r'[A-Za-z]{3}\s+\d{1,2}\s+\d{4}', str(v)) for v in sample_values)
            
            likely_format = "Unknown"
            suggested_sql = f"-- Standard formats failed, manual conversion needed"
            
            if text_month:
                likely_format = "Mon DD YYYY (text month)"
                suggested_sql = f"TRY_CONVERT(DATE, NULLIF(LTRIM(RTRIM([{{col}}])), ''), 107)"
            elif two_digit_year and has_slashes:
                likely_format = "MM/DD/YY (2-digit year)"
                suggested_sql = f"TRY_CONVERT(DATE, NULLIF(LTRIM(RTRIM([{{col}}])), ''), 1)"
            elif has_slashes:
                likely_format = "MM/DD/YYYY or DD/MM/YYYY"
                suggested_sql = f"""COALESCE(
                    TRY_CONVERT(DATE, NULLIF(LTRIM(RTRIM([{{col}}])), ''), 101),  -- MM/DD/YYYY
                    TRY_CONVERT(DATE, NULLIF(LTRIM(RTRIM([{{col}}])), ''), 103)   -- DD/MM/YYYY
                )"""
            elif has_dashes:
                likely_format = "YYYY-MM-DD or MM-DD-YYYY"
                suggested_sql = f"""COALESCE(
                    TRY_CONVERT(DATE, NULLIF(LTRIM(RTRIM([{{col}}])), ''), 120),  -- YYYY-MM-DD
                    TRY_CONVERT(DATE, NULLIF(LTRIM(RTRIM([{{col}}])), ''), 110)   -- MM-DD-YYYY
                )"""
            
            patterns[col] = {
                'likely_format': likely_format,
                'suggested_sql': suggested_sql,
                'sample_values': sample_values
            }
        
        return patterns
            
        for col_name in numeric_columns:
                if col_name not in existing_columns:
                    continue
                    
                total_columns_assessed += 1
                schema_type = self.schema_types[col_name]
                
                try:
                    if schema_type in ['INT', 'SMALLINT']:
                        # For INT columns, check if source has decimals
                        analysis_sql = f"""
                            SELECT 
                                COUNT(*) as total_rows,
                                COUNT(CASE WHEN [{col_name}] IS NOT NULL AND LTRIM(RTRIM([{col_name}])) != '' THEN 1 END) as non_null_rows,
                                COUNT(CASE WHEN [{col_name}] LIKE '%.%' THEN 1 END) as has_decimals,
                                COUNT(CASE WHEN TRY_CAST([{col_name}] AS INT) IS NULL AND [{col_name}] IS NOT NULL AND LTRIM(RTRIM([{col_name}])) != '' THEN 1 END) as conversion_failures
                            FROM [dbo].[{table_name}]
                        """
                        
                        result = db.run_query(analysis_sql, self.db_key)
                        row_data = result.iloc[0]
                        total_records_assessed += row_data['total_rows']
                        
                        if row_data['has_decimals'] > 0 or row_data['conversion_failures'] > 0:
                            key = f"{customer}.{col_name}"
                            column_issues[key] = {
                                'customer': customer,
                                'column': col_name,
                                'schema_type': schema_type,
                                'total_rows': row_data['total_rows'],
                                'non_null_rows': row_data['non_null_rows'],
                                'transformations_required': row_data['has_decimals'],
                                'conversion_failures': row_data['conversion_failures'],
                                'issue_type': 'INT_WITH_DECIMALS'
                            }
                            
                            print(f"   🚨 INT ISSUE: {col_name}")
                            print(f"      Schema: {schema_type}")
                            print(f"      Decimal values: {row_data['has_decimals']}")
                            print(f"      Conversion failures: {row_data['conversion_failures']}")
                            
                    elif schema_type.startswith('DECIMAL('):
                        # For DECIMAL columns, check precision requirements
                        schema_precision, schema_scale = self.extract_decimal_precision(schema_type)
                        
                        # Get sample values to analyze precision
                        sample_sql = f"""
                            SELECT TOP 1000 [{col_name}]
                            FROM [dbo].[{table_name}]
                            WHERE [{col_name}] IS NOT NULL 
                            AND LTRIM(RTRIM([{col_name}])) != ''
                            AND ISNUMERIC([{col_name}]) = 1
                        """
                        
                        sample_result = db.run_query(sample_sql, self.db_key)
                        
                        max_whole_digits = 0
                        max_frac_digits = 0
                        transformations_needed = 0
                        
                        for sample_row in sample_result.itertuples():
                            whole_digits, frac_digits = self.analyze_precision_requirements(sample_row[1])
                            if whole_digits is not None and frac_digits is not None:
                                max_whole_digits = max(max_whole_digits, whole_digits)
                                max_frac_digits = max(max_frac_digits, frac_digits)
                                
                                # Check if transformation needed
                                total_digits_needed = whole_digits + frac_digits
                                if total_digits_needed > schema_precision or frac_digits > schema_scale:
                                    transformations_needed += 1
                        
                        # Count total rows
                        count_sql = f"""
                            SELECT COUNT(*) as total_rows
                            FROM [dbo].[{table_name}]
                        """
                        count_result = db.run_query(count_sql, self.db_key)
                        total_rows = count_result.iloc[0]['total_rows']
                        total_records_assessed += total_rows
                        
                        # Check if schema compliant
                        schema_compliant = (max_whole_digits + max_frac_digits <= schema_precision) and (max_frac_digits <= schema_scale)
                        
                        if not schema_compliant or transformations_needed > 0:
                            key = f"{customer}.{col_name}"
                            column_issues[key] = {
                                'customer': customer,
                                'column': col_name,
                                'schema_type': schema_type,
                                'schema_precision': schema_precision,
                                'schema_scale': schema_scale,
                                'max_whole_digits': max_whole_digits,
                                'max_frac_digits': max_frac_digits,
                                'schema_compliant': schema_compliant,
                                'transformations_required': transformations_needed,
                                'total_rows': total_rows,
                                'issue_type': 'DECIMAL_PRECISION'
                            }
                            
                            print(f"   🚨 DECIMAL ISSUE: {col_name}")
                            print(f"      Schema: {schema_type} (precision={schema_precision}, scale={schema_scale})")
                            print(f"      Max digits: {max_whole_digits} whole, {max_frac_digits} fractional")
                            print(f"      Schema compliant: {schema_compliant}")
                            print(f"      Transformations needed: {transformations_needed}")
                            
                except Exception as e:
                    print(f"   ⚠️  Error analyzing {col_name}: {e}")
                    continue
        
        return column_issues, total_columns_assessed, total_records_assessed
    
    def analyze_decimal_columns_schema_aware(self):
        """Schema-aware analysis of decimal/int/date columns only"""
        print("=" * 80)
        print("SCHEMA-AWARE PRECISION & DATE DIAGNOSTICS")
        print("=" * 80)
        
        # Get all RAW tables
        raw_tables_df = db.run_query("""
            SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME LIKE 'x%_ORDER_LIST_RAW'
            ORDER BY TABLE_NAME
        """, self.db_key)
        
        column_issues = {}
        total_columns_assessed = 0
        total_records_assessed = 0
        total_records_requiring_transform = 0
        
        for idx, row in raw_tables_df.iterrows():
            table_name = row['TABLE_NAME']
            customer_name = table_name.replace('_ORDER_LIST_RAW', '').replace('x', '')
            
            print(f"\n[ANALYZING] {customer_name} ({table_name})")
            
            # Get column information for this table
            columns_df = db.run_query(f"""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = '{table_name}'
                ORDER BY ORDINAL_POSITION
            """, self.db_key)
            
            # Get total records in this table
            count_df = db.run_query(f"SELECT COUNT(*) AS record_count FROM [dbo].[{table_name}]", self.db_key)
            table_record_count = count_df.iloc[0]['record_count'] if not count_df.empty else 0
            total_records_assessed += table_record_count
            
            # Process each column
            table_issues_found = False
            
            for _, col_row in columns_df.iterrows():
                col_name = col_row['COLUMN_NAME']
                
                # Skip internal metadata columns
                if col_name.startswith('_'):
                    continue
                
                # Check if this column has a numeric type in the schema
                if col_name in self.schema_types:
                    schema_type = self.schema_types[col_name]
                    
                    # Only analyze numeric columns
                    if schema_type in ('INT', 'SMALLINT', 'TINYINT') or schema_type.startswith('DECIMAL') or schema_type.startswith('NUMERIC'):
                        total_columns_assessed += 1
                        
                        # Analyze this column
                        result = self.analyze_column_for_overflow(table_name, col_name, schema_type)
                        
                        # If issues found, add to the collection
                        if result['issues_found']:
                            table_issues_found = True
                            column_key = f"{customer_name}.{col_name}"
                            
                            if column_key not in column_issues:
                                column_issues[column_key] = result
                                column_issues[column_key]['customer'] = customer_name
                            else:
                                # Update existing record with more extreme values
                                existing = column_issues[column_key]
                                
                                # Update extreme values
                                if result['extreme_values']['min'] is not None:
                                    if existing['extreme_values']['min'] is None or result['extreme_values']['min'] < existing['extreme_values']['min']:
                                        existing['extreme_values']['min'] = result['extreme_values']['min']
                                        
                                if result['extreme_values']['max'] is not None:
                                    if existing['extreme_values']['max'] is None or result['extreme_values']['max'] > existing['extreme_values']['max']:
                                        existing['extreme_values']['max'] = result['extreme_values']['max']
                                
                                # Update precision extremes
                                if result['extreme_precision']['whole'] > existing['extreme_precision']['whole']:
                                    existing['extreme_precision']['whole'] = result['extreme_precision']['whole']
                                    
                                if result['extreme_precision']['fractional'] > existing['extreme_precision']['fractional']:
                                    existing['extreme_precision']['fractional'] = result['extreme_precision']['fractional']
                                
                                # Update transformation count
                                existing['transformations_required'] += result['transformations_required']
                                
                                # Update compliance status
                                if not result['schema_compliant']:
                                    existing['schema_compliant'] = False
                                    
                                if result['schema_adjustment_required']:
                                    existing['schema_adjustment_required'] = True
                                    
                                # Add sample values
                                existing['sample_values'].extend(result['sample_values'])
                                existing['sample_values'] = list(set(existing['sample_values']))[:5]  # Keep max 5 unique samples
                            
                            total_records_requiring_transform += result['transformations_required']
                            
                            # Print issue details
                            print(f"   🚨 ISSUE: {col_name}")
                            print(f"      Schema type: {schema_type}")
                            print(f"      Range: {result['extreme_values']['min']} to {result['extreme_values']['max']}")
                            print(f"      Precision: {result['extreme_precision']['whole']} whole digits, {result['extreme_precision']['fractional']} fractional digits")
                            print(f"      Schema compliant: {'YES' if result['schema_compliant'] else 'NO'}")
                            print(f"      Schema adjustment needed: {'YES' if result['schema_adjustment_required'] else 'NO'}")
                            print(f"      Transformations required: {result['transformations_required']} records")
                            if result['sample_values']:
                                print(f"      Sample problematic values: {', '.join(map(str, result['sample_values']))}")
            
            if not table_issues_found:
                print("   ✅ No precision issues found")
        
        return column_issues, total_columns_assessed, total_records_assessed, total_records_requiring_transform
        
    def generate_final_summary(self, column_issues, total_columns_assessed, total_records_assessed, total_records_requiring_transform=0):
        """Generate comprehensive final summary"""
        print(f"\n{'='*80}")
        print("FINAL PRECISION ANALYSIS SUMMARY")
        print(f"{'='*80}")
        
        columns_with_issues = len(column_issues)
        
        print(f"# of columns assessed: {total_columns_assessed}")
        print(f"# of columns with issues: {columns_with_issues}")
        print(f"# of records assessed: {total_records_assessed:,}")
        print(f"# of records requiring transformation: {total_records_requiring_transform:,}")
        
        if columns_with_issues > 0:
            print(f"\n{'='*80}")
            print("SUMMARY OF ISSUE COLUMNS")
            print(f"{'='*80}")
            
            for column_key, issue in column_issues.items():
                print(f"\nColumn: {issue['column']} (Customer: {issue.get('customer', 'ALL')})")
                print(f"Data type: {issue['schema_type']}")
                
                if issue['schema_type'] in ('INT', 'SMALLINT', 'TINYINT'):
                    print(f"Issue: INT column has decimal values")
                    print(f"Range: {issue['extreme_values']['min']} to {issue['extreme_values']['max']}")
                    print(f"Transformations required: {issue['transformations_required']}")
                    print(f"Schema compliant: NO")
                    print(f"Schema adjustment required: NO (truncate decimals)")
                    
                elif issue['schema_type'].startswith('DECIMAL') or issue['schema_type'].startswith('NUMERIC'):
                    precision, scale = self.extract_decimal_precision(issue['schema_type'])
                    print(f"Range: {issue['extreme_values']['min']} to {issue['extreme_values']['max']}")
                    print(f"Current digits: {issue['extreme_precision']['whole']} whole, {issue['extreme_precision']['fractional']} fractional")
                    print(f"Schema allows: {precision-scale} whole, {scale} fractional")
                    print(f"Schema compliant: {'YES' if issue.get('schema_compliant', False) else 'NO'}")
                    print(f"Schema adjustment required: {'YES' if issue.get('schema_adjustment_required', False) else 'NO'}")
                    print(f"# of transformations required: {issue['transformations_required']}")
                
                if issue.get('sample_values'):
                    print(f"Sample values: {', '.join(map(str, issue['sample_values']))}")
                
                print("-" * 40)
        
        # Performance impact assessment
        transformation_percentage = (total_records_requiring_transform / total_records_assessed * 100) if total_records_assessed > 0 else 0
        
        print(f"\n{'='*80}")
        print("PERFORMANCE IMPACT ASSESSMENT")
        print(f"{'='*80}")
        print(f"Transformation overhead: {transformation_percentage:.3f}% of records")
        
        if transformation_percentage < 0.1:
            print("✅ MINIMAL IMPACT: Use simple SQL Server TRY_CAST approach")
            print("   Recommendation: Standard DECIMAL casting in SQL")
        elif transformation_percentage < 1.0:
            print("⚠️  LOW IMPACT: Selective transformation approach")
            print("   Recommendation: Conditional casting only where needed")
        else:
            print("🚨 SIGNIFICANT IMPACT: Data quality issues need addressing")
            print("   Recommendation: Implement data cleansing pipeline")
        
        # Specific column recommendations
        if columns_with_issues > 0:
            print(f"\n{'='*80}")
            print("COLUMN-SPECIFIC RECOMMENDATIONS")
            print(f"{'='*80}")
            
            for column_key, issue in column_issues.items():
                column_name = issue['column']
                schema_type = issue['schema_type']
                
                print(f"{column_name}:")
                
                if schema_type in ('INT', 'SMALLINT', 'TINYINT'):
                    print(f"   Current: {schema_type}")
                    print(f"   Recommendation: Use FLOOR(TRY_CAST([{column_name}] AS FLOAT))")
                
                elif schema_type.startswith('DECIMAL') or schema_type.startswith('NUMERIC'):
                    precision, scale = self.extract_decimal_precision(schema_type)
                    max_whole = issue['extreme_precision']['whole']
                    max_frac = issue['extreme_precision']['fractional']
                    
                    # Handle special case for the 17,15 columns that are now 17,4
                    if schema_type == 'DECIMAL(17,15)':
                        print(f"   Current: {schema_type}")
                        print(f"   Recommendation: DECIMAL(17,4)")
                    elif max_whole > (precision - scale):
                        # Need more whole number precision
                        new_precision = max_whole + scale
                        new_precision = min(38, new_precision)  # SQL Server max is 38
                        print(f"   Current: {schema_type}")
                        print(f"   Recommendation: DECIMAL({new_precision}.0,{scale}.0)")
                    elif max_frac > scale:
                        # Need more fractional precision
                        new_scale = max_frac
                        new_precision = max_whole + new_scale
                        new_precision = min(38, new_precision)  # SQL Server max is 38
                        print(f"   Current: {schema_type}")
                        print(f"   Recommendation: DECIMAL({new_precision}.0,{new_scale}.0)")
                    else:
                        print(f"   Current: {schema_type}")
                        print(f"   Recommendation: TRY_CAST([{column_name}] AS {schema_type})")
        
        return {
            'column_issues': column_issues,
            'total_columns_assessed': total_columns_assessed,
            'total_records_assessed': total_records_assessed,
            'total_records_requiring_transform': total_records_requiring_transform,
            'transformation_percentage': transformation_percentage
        }
    
    def run_full_diagnostics(self):
        """Run complete schema-aware precision diagnostics"""
        start_time = time.time()
        
        print(f"Schema types loaded: {len(self.schema_types)} numeric columns")
        print(f"Sample types: {list(self.schema_types.items())[:5]}")
        
        # Analyze only decimal/int columns  
        column_issues, total_columns_assessed, total_records_assessed, total_records_requiring_transform = self.analyze_decimal_columns_schema_aware()
        
        # Generate final summary
        summary = self.generate_final_summary(column_issues, total_columns_assessed, total_records_assessed, total_records_requiring_transform)
        
        duration = time.time() - start_time
        print(f"\n{'='*80}")
        print(f"DIAGNOSTICS COMPLETE - Duration: {duration:.2f}s")
        print(f"{'='*80}")
        
        return {
            'column_issues': column_issues,
            'total_columns_assessed': total_columns_assessed,
            'total_records_assessed': total_records_assessed,
            'total_records_requiring_transform': total_records_requiring_transform,
            'duration': duration
        }
    
    def run_date_diagnostics(self):
        """Run date-specific diagnostics to identify conversion issues"""
        start_time = time.time()
        
        print("=" * 80)
        print("DATE CONVERSION DIAGNOSTICS")
        print("=" * 80)
        print("Purpose: Find date values causing 'Conversion failed when converting date' errors")
        
        # Run date analysis
        problem_dates = self.debug_date_columns()
        
        duration = time.time() - start_time
        print(f"\n{'='*80}")
        print(f"DATE DIAGNOSTICS COMPLETE - Duration: {duration:.2f}s")
        print(f"{'='*80}")
        
        return {
            'problem_dates': problem_dates,
            'duration': duration
        }
    
    def run_combined_diagnostics(self):
        """Run both precision and date diagnostics"""
        print("=" * 80)
        print("COMBINED PRECISION & DATE DIAGNOSTICS")
        print("=" * 80)
        
        # Run precision diagnostics first
        precision_results = self.run_full_diagnostics()
        
        # Run date diagnostics
        date_results = self.run_date_diagnostics()
        
        return {
            'precision': precision_results,
            'dates': date_results
        }

if __name__ == "__main__":
    import sys
    
    diagnostics = PrecisionDiagnostics()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == "dates":
            results = diagnostics.run_date_diagnostics()
        elif mode == "precision":
            results = diagnostics.run_full_diagnostics()
        elif mode == "combined":
            results = diagnostics.run_combined_diagnostics()
        else:
            print("Usage: python debug_precision_issues.py [dates|precision|combined]")
            print("  dates     - Run date conversion diagnostics only")
            print("  precision - Run precision diagnostics only")
            print("  combined  - Run both diagnostics")
            sys.exit(1)
    else:
        # Default behavior - run combined diagnostics
        results = diagnostics.run_combined_diagnostics()
