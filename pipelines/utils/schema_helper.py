"""
schema_helper.py - Centralized DataFrame-to-SQL schema inference and type conversion
Location: utils/schema_helper.py
"""
import pandas as pd
import numpy as np
from decimal import Decimal

# --- SQL Type Inference ---
def infer_column_sql_type(series: pd.Series, options: dict = None) -> dict:
    """
    Infer the best SQL Server type for a pandas Series.
    Returns dict: { 'sql_type': ..., 'max_length': ..., 'is_numeric': ..., 'is_int': ..., 'is_float': ..., 'is_decimal': ... }
    """
    options = options or {}
    s = series.dropna()
    result = {
        'sql_type': 'NVARCHAR(255)',
        'max_length': 0,
        'is_numeric': False,
        'is_int': False,
        'is_float': False,
        'is_decimal': False
    }
    if len(s) == 0:
        return result
    # Numeric detection
    if pd.api.types.is_integer_dtype(s):
        minv, maxv = s.min(), s.max()
        if minv >= -2147483648 and maxv <= 2147483647:
            result['sql_type'] = 'INT'
        elif minv >= -9223372036854775808 and maxv <= 9223372036854775807:
            result['sql_type'] = 'BIGINT'
        else:
            result['sql_type'] = 'DECIMAL(38,0)'
        result['is_numeric'] = True
        result['is_int'] = True
        return result
    if pd.api.types.is_float_dtype(s):
        # Check if all floats are actually ints
        if (s.dropna() % 1 == 0).all():
            minv, maxv = s.min(), s.max()
            if minv >= -2147483648 and maxv <= 2147483647:
                result['sql_type'] = 'INT'
            elif minv >= -9223372036854775808 and maxv <= 9223372036854775807:
                result['sql_type'] = 'BIGINT'
            else:
                result['sql_type'] = 'DECIMAL(38,0)'
            result['is_numeric'] = True
            result['is_int'] = True
        else:
            result['sql_type'] = 'DECIMAL(18,4)'
            result['is_numeric'] = True
            result['is_float'] = True
        return result
    # Decimal (object dtype, but all values are decimal)
    if s.dtype == 'object':
        try:
            as_decimal = s.apply(lambda x: isinstance(x, Decimal))
            if as_decimal.all():
                result['sql_type'] = 'DECIMAL(18,4)'
                result['is_numeric'] = True
                result['is_decimal'] = True
                return result
        except Exception:
            pass
    # Date/time
    if pd.api.types.is_datetime64_any_dtype(s):
        result['sql_type'] = 'DATETIME2'
        return result
    # Boolean
    if pd.api.types.is_bool_dtype(s):
        result['sql_type'] = 'BIT'
        return result
    # Text
    str_s = s.astype(str)
    max_length = str_s.str.len().max()
    result['max_length'] = max_length
    if max_length <= 100:
        result['sql_type'] = 'NVARCHAR(100)'
    elif max_length <= 255:
        result['sql_type'] = 'NVARCHAR(255)'
    elif max_length <= 500:
        result['sql_type'] = 'NVARCHAR(500)'
    elif max_length <= 1000:
        result['sql_type'] = 'NVARCHAR(1000)'
    elif max_length <= 2000:
        result['sql_type'] = 'NVARCHAR(2000)'
    elif max_length <= 4000:
        result['sql_type'] = 'NVARCHAR(4000)'
    else:
        result['sql_type'] = 'NVARCHAR(MAX)'
    return result


def generate_table_schema(df: pd.DataFrame, options: dict = None):
    """
    Generate SQL column definitions and schema info for a DataFrame.
    Returns: (columns_sql: list[str], schema_info: dict)
    """
    columns_sql = []
    schema_info = {}
    for col in df.columns:
        info = infer_column_sql_type(df[col], options)
        schema_info[col] = info
        columns_sql.append(f"[{col}] {info['sql_type']}")
    return columns_sql, schema_info


def convert_df_for_sql(df: pd.DataFrame, schema_info: dict) -> pd.DataFrame:
    """
    Convert DataFrame columns to native Python types for SQL compatibility.
    - INT/BIGINT: int
    - DECIMAL: float or Decimal
    - BIT: bool
    - DATETIME2: datetime
    - NVARCHAR: str
    """
    df2 = df.copy()
    for col, info in schema_info.items():
        if info.get('is_numeric'):
            if info.get('is_int'):
                df2[col] = pd.to_numeric(df2[col], errors='coerce').dropna().astype('Int64')
                df2[col] = df2[col].apply(lambda x: int(x) if pd.notnull(x) else None)
            elif info.get('is_float') or info.get('is_decimal'):
                df2[col] = pd.to_numeric(df2[col], errors='coerce').astype(float)
        elif info['sql_type'] == 'BIT':
            df2[col] = df2[col].astype(bool)
        elif info['sql_type'] == 'DATETIME2':
            df2[col] = pd.to_datetime(df2[col], errors='coerce')
        else:
            df2[col] = df2[col].astype(str)
    return df2
