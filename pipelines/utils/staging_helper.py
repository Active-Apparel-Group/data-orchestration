# utils/staging_helper.py - Performance optimized version with mode-based execution

import logging
import pandas as pd
import time
from typing import Generator
import db_helper as db

logger = logging.getLogger("staging_helper")

# Global variable to track the current mode (set by calling scripts)
_STAGING_MODE = 'robust'  # Default to robust (safest)

def set_staging_mode(mode: str):
    """Set the staging helper mode from calling script"""
    global _STAGING_MODE
    if mode.lower() in ['fast', 'robust']:
        _STAGING_MODE = mode.lower()
        logger.info(f"Staging helper mode set to: {_STAGING_MODE.upper()}")
    else:
        logger.warning(f"Invalid staging mode '{mode}', using default 'robust'")
        _STAGING_MODE = 'robust'

def get_staging_mode() -> str:
    """Get current staging mode"""
    return _STAGING_MODE

def prepare_staging_table(
    df: pd.DataFrame,
    staging_table: str,
    production_table: str,  # This is the target, not what we need
    db_name: str,
    column_type_map: dict = None,  # Optional: {col: sql_type}
    options: dict = None  # Optional: job options from TOML config
) -> None:
    """
    Create staging table with proper SQL types based on DataFrame dtypes.
    The DataFrame comes from the SOURCE query, so use its schema.
    """
    start_time = time.time()
    
    # Drop existing staging table if it exists
    exists = db.run_query(
        f"SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{staging_table}'",
        db_name
    ).shape[0] > 0

    if exists:
        db.execute(f"DROP TABLE dbo.{staging_table}", db_name)
        logger.info("Dropped existing staging %s", staging_table)

    # Use options from config if provided
    if options is None:
        options = {}

    # Create staging table based on DataFrame schema (from source query)
    def pandas_to_sql_type(col_name, dtype, series, options):
        dtype_str = str(dtype).lower()
        # Handle dates/timestamps
        if 'datetime' in dtype_str or 'timestamp' in dtype_str:
            return "DATETIME2"
        # Handle integers (use BIGINT to avoid range issues)
        if 'int' in dtype_str:
            return "BIGINT"
        # Handle floats/decimals - NOW CONFIGURABLE
        if 'float' in dtype_str:
            return get_sql_type(col_name, dtype, options)
        # Handle booleans
        if 'bool' in dtype_str:
            return "BIT"
        # Handle text/objects
        if 'object' in dtype_str or 'string' in dtype_str:
            if series.dtype == 'object' and len(series) > 0:
                max_len = series.astype(str).str.len().max()
                if pd.isna(max_len) or max_len <= 255:
                    return "NVARCHAR(255)"
                elif max_len <= 4000:
                    return f"NVARCHAR({min(4000, int(max_len * 1.2))})"
                else:
                    return "NVARCHAR(MAX)"
            return "NVARCHAR(255)"
        # Default fallback
        return "NVARCHAR(255)"

    # Build CREATE TABLE statement from DataFrame, using column_type_map if provided
    cols_sql = []
    for col in df.columns:
        if column_type_map and col in column_type_map and column_type_map[col]:
            sql_type = column_type_map[col]
        else:
            sql_type = pandas_to_sql_type(col, df[col].dtype, df[col], options)
        col_sql = f"[{col}] {sql_type}"
        cols_sql.append(col_sql)

    cols_sql_str = ", ".join(cols_sql)
    db.execute(f"CREATE TABLE dbo.{staging_table} ({cols_sql_str})", db_name)

    elapsed = time.time() - start_time
    logger.info("Created staging %s with proper SQL types from DataFrame (%.2fs, %d columns)", 
                staging_table, elapsed, len(cols_sql))


def _row_generator_fast(df_chunk: pd.DataFrame) -> Generator[tuple, None, None]:
    """
    FAST: Vectorized approach for clean data (ORDER_LIST style)
    Pre-processes DataFrame to replace problematic strings, then simple row iteration
    """
    # Pre-convert problematic string values at DataFrame level (MUCH faster)
    problematic_strings = {'nan', 'none', 'null', ''}
    
    # Apply vectorized replacements only where needed (avoid row-by-row processing)
    df_clean = df_chunk.copy()
    for col in df_clean.select_dtypes(include=['object']).columns:
        df_clean[col] = df_clean[col].replace(problematic_strings, None)
    
    # Simple, fast row generation without per-cell type checking
    for row in df_clean.itertuples(index=False, name=None):
        converted_row = []
        for v in row:
            if pd.isna(v) or v is None:
                converted_row.append(None)
            elif hasattr(v, "date"):  # Handle datetime objects
                converted_row.append(v.date())
            else:
                converted_row.append(v)
        
        yield tuple(converted_row)


def _row_generator_robust(df_chunk: pd.DataFrame) -> Generator[tuple, None, None]:
    """
    ROBUST: Per-cell checking for dirty data (Kestra/Monday.com style)
    Handles mixed types and problematic string values at the cell level
    """
    for row_idx, row in enumerate(df_chunk.itertuples(index=False, name=None)):
        converted_row = []
        for col_idx, v in enumerate(row):
            if pd.isna(v) or v is None:
                converted_row.append(None)
            elif hasattr(v, "date"):
                converted_row.append(v.date())
            else:
                # Check for problematic string values that should be None
                if isinstance(v, str) and v.lower() in ['nan', 'none', 'null', '']:
                    converted_row.append(None)
                else:
                    converted_row.append(v)
        
        # Debug: Log first few problematic rows for numeric columns
        if row_idx < 3:
            numeric_issues = []
            for col_idx, v in enumerate(converted_row):
                if isinstance(v, str) and v.lower() in ['nan', 'none']:
                    col_name = df_chunk.columns[col_idx] if col_idx < len(df_chunk.columns) else f"col_{col_idx}"
                    numeric_issues.append(f"{col_name}={v}")
            if numeric_issues:
                logger.warning(f"Row {row_idx} has string values that should be numeric: {numeric_issues}")
        
        yield tuple(converted_row)


def _row_generator(df_chunk: pd.DataFrame) -> Generator[tuple, None, None]:
    """
    Mode-aware row generation based on script configuration
    Routes to appropriate generator based on _STAGING_MODE
    """
    if _STAGING_MODE == 'fast':
        return _row_generator_fast(df_chunk)
    else:
        return _row_generator_robust(df_chunk)


def load_to_staging_table(
    df: pd.DataFrame,
    staging_table: str,
    db_name: str,
    batch_size: int = 5000  # ⚡ INCREASED from 1000 to 5000 for better performance
) -> None:
    """
    MODE-BASED: Direct execution based on staging mode - no try-catch overhead.
    - Uses appropriate row generator based on _STAGING_MODE
    - Larger batch sizes (5000 vs 1000)
    - Better connection management
    """
    if df.empty:
        logger.warning("No data to load into %s", staging_table)
        return

    start_time = time.time()
    total = len(df)
    
    logger.info("MODE-BASED BULK INSERT: %d rows in batches of %d (mode: %s)", 
                total, batch_size, _STAGING_MODE.upper())
    
    # Pre-build SQL statement
    cols = list(df.columns)
    collist = ", ".join(f"[{c}]" for c in cols)
    placeholders = ", ".join("?" for _ in cols)
    insert_sql = f"INSERT INTO dbo.{staging_table} ({collist}) VALUES ({placeholders})"

    # Single connection for entire operation (more efficient)
    conn = db.get_connection(db_name)
    cursor = conn.cursor()
    cursor.fast_executemany = True

    batches_processed = 0
    
    try:
        for start in range(0, total, batch_size):
            batch_start = time.time()
            chunk = df.iloc[start : start + batch_size]
            rows_in_batch = len(chunk)

            logger.info("Processing batch %d: rows %d-%d (%d rows)", 
                       batches_processed + 1, start + 1, start + rows_in_batch, rows_in_batch)
            
            # DIRECT MODE EXECUTION - no try-catch overhead
            cursor.executemany(insert_sql, _row_generator(chunk))
            
            batch_elapsed = time.time() - batch_start
            batches_processed += 1
            
            logger.info("✅ Batch %d complete: %d rows in %.2fs (%.0f rows/sec)",
                       batches_processed, rows_in_batch, batch_elapsed,
                       rows_in_batch / batch_elapsed if batch_elapsed > 0 else 0)

        # Commit all batches at once (faster than per-batch commits)
        conn.commit()
        
    except Exception as e:
        logger.error("Bulk insert failed at batch %d: %s", batches_processed + 1, e)
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

    total_elapsed = time.time() - start_time
    rows_per_sec = total / total_elapsed if total_elapsed > 0 else 0
    logger.info("🚀 BULK INSERT COMPLETE: %d rows in %.2fs (%.0f rows/sec, %d batches)",
                total, total_elapsed, rows_per_sec, batches_processed)


def atomic_swap_tables(
    staging_table: str,
    production_table: str,
    db_name: str
) -> None:
    """
    Atomically swap staging → production with performance logging.
    Only drops staging table if swap is successful.
    """
    start_time = time.time()
    
    try:
        sql = f"""
        BEGIN TRAN;
            IF OBJECT_ID('dbo.{production_table}','U') IS NOT NULL
            DROP TABLE dbo.{production_table};
            EXEC sp_rename 'dbo.{staging_table}', '{production_table}';
        COMMIT TRAN;
        """
        
        db.execute(sql, db_name)
        
        # Only drop staging table if swap was successful
        drop_sql = f"DROP TABLE IF EXISTS dbo.{staging_table};"
        db.execute(drop_sql, db_name)
        
        elapsed = time.time() - start_time
        logger.info("Atomic swap complete: %s → %s, staging table dropped (%.2fs)", 
                    staging_table, production_table, elapsed)
        
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error("Atomic swap failed: %s → %s (%.2fs). Staging table preserved for debugging.", 
                     staging_table, production_table, elapsed)
        logger.error("Swap error: %s", str(e))
        raise  # Re-raise the exception to maintain error handling upstream


# Placeholder for future upsert logic
def upsert_into_production(
    staging_table: str,
    production_table: str,
    db_name: str,
    key_columns: list[str]
) -> None:
    """
    Perform a MERGE from staging_table to production_table on key_columns.
    Not implemented yet—reserved for upsert workflows.
    """
    raise NotImplementedError("Upsert logic not yet implemented")


def apply_column_duplications(df, metadata):
    """Apply board-specific column duplications from metadata"""
    duplications = metadata.get('column_duplications', [])

    if not duplications:
        return df
    
    logger.info(f"Processing {len(duplications)} column duplications")
    for dup in duplications:
        source_col = dup['source_column']
        target_col = dup['target_column']
        description = dup.get('description', 'No description')
        null_like = {"None", "null", "nan", "", "{}", "[]"}
        if source_col in df.columns:
            df[target_col] = df[source_col].apply(lambda x: None if pd.isna(x) or str(x).strip() in null_like else x)
            logger.info(f"Duplicated column: '{source_col}' -> '{target_col}' ({description})")
        else:
            # Always set target_col to None if source_col is missing
            df[target_col] = None
            logger.warning(f"Source column '{source_col}' not found for duplication to '{target_col}', setting '{target_col}' to None")
    return df


# Enhanced type mapping function with configurable float handling
def get_sql_type(col, dtype, options):
    """
    Map pandas dtype to SQL Server type with configurable float handling
    
    Args:
        col: Column name
        dtype: Pandas dtype
        options: Job options from TOML config
        
    Returns:
        SQL Server type string
    """
    retain_float = options.get("retain_float", False)
    retain_float_cols = options.get("retain_float_columns", [])
    
    # Convert retain_float_cols to set for faster lookup
    if isinstance(retain_float_cols, list):
        retain_float_cols = set(retain_float_cols)
    else:
        retain_float_cols = set()
    
    dtype_str = str(dtype).lower()
    
    # Handle floats with configurable mapping
    if 'float' in dtype_str:
        if retain_float is True or col in retain_float_cols:
            return "FLOAT"
        else:
            return "DECIMAL(18,4)"  # Default decimal precision
    
    # Handle other types (fallback for non-float types)
    if 'int' in dtype_str:
        return "BIGINT"
    elif 'datetime' in dtype_str or 'timestamp' in dtype_str:
        return "DATETIME2"
    elif 'bool' in dtype_str:
        return "BIT"
    else:
        return "NVARCHAR(255)"  # Default for strings/objects
