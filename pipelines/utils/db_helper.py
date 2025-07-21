"""
Lightweight SQL helper for Kestra/data pipelines.
- Loads DB credentials from config.yaml in the working directory
- Uses ODBC Driver 17 for SQL Server
- Provides canonical customer name transformation
"""

import os
import pyodbc
import pandas as pd
import yaml
from pathlib import Path
from typing import Union, Optional

import warnings
warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy connectable")

# Import logger following Kestra compatibility standards
try:
    from pipelines.utils import logger_helper
except ImportError:
    # Fallback to direct import
    import importlib.util
    
    logger_helper_path = Path(__file__).parent / "logger_helper.py"
    spec = importlib.util.spec_from_file_location("logger_helper", logger_helper_path)
    if spec and spec.loader:
        logger_helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(logger_helper)
    else:
        # Final fallback
        import logging
        class MockLoggerHelper:
            @staticmethod
            def get_logger(name):
                return logging.getLogger(name)
        logger_helper = MockLoggerHelper()

# --------------------------
# CONSTANTS
# --------------------------
DEFAULT_DRIVER = "{ODBC Driver 17 for SQL Server}"
logger = logger_helper.get_logger(__name__)

# --------------------------
# CONFIG LOADING
# --------------------------

# -- Set config path to always resolve relative to this file's location
CONFIG_PATH = os.getenv("DB_CONFIG_PATH", str(Path(__file__).parent / "config.yaml"))

def load_config(path: str = CONFIG_PATH):
    """Load configuration from YAML file"""
    with open(path, "r") as f:
        config = yaml.safe_load(f)
        return config

def get_database_config(path: str = CONFIG_PATH):
    """Get database configuration (for backward compatibility)"""
    config = load_config(path)
    return config.get('databases', {})

def get_api_config(api_name: str, path: str = CONFIG_PATH):
    """Get API configuration for specified API"""
    config = load_config(path)
    return config.get('apis', {}).get(api_name, {})

# Load database config for backward compatibility
DB_CONFIG = get_database_config()

# --------------------------
# CONNECTION FACTORY
# --------------------------
def get_connection(db_key: str) -> pyodbc.Connection:
    """
    Create a pyodbc connection using config.yaml block for the given db_key.
    Tries ODBC Driver 17 first, falls back to SQL Server if not available.
    """
    cfg = DB_CONFIG[db_key.lower()]
    driver = cfg.get("driver", DEFAULT_DRIVER)
    
    # If using default driver, try ODBC Driver 17 first, then fall back to SQL Server
    if driver == DEFAULT_DRIVER:
        drivers_to_try = ["{ODBC Driver 17 for SQL Server}", "{SQL Server}"]
    else:
        drivers_to_try = [driver]
    
    conn_parts_base = [
        f"SERVER={cfg['host']},{cfg['port']}",
        f"DATABASE={cfg['database']}"
    ]

    if cfg.get('trusted_connection', '').lower() in ('yes', 'true', '1'):
        conn_parts_base.append("Trusted_Connection=yes")
    else:
        conn_parts_base.append(f"UID={cfg['username']}")
        conn_parts_base.append(f"PWD={cfg['password']}")

    encrypt = cfg.get('encrypt', 'yes').lower()
    conn_parts_base.append(f"Encrypt={'yes' if encrypt in ('yes', 'true', '1') else 'no'}")

    trust_cert = cfg.get('trustServerCertificate', 'no').lower()
    conn_parts_base.append(f"TrustServerCertificate={'yes' if trust_cert in ('yes', 'true', '1') else 'no'}")

    conn_parts_base.append("Connection Timeout=30")
    
    # Try each driver in order
    last_error = None
    for driver_attempt in drivers_to_try:
        try:
            conn_parts = [f"DRIVER={driver_attempt}"] + conn_parts_base
            conn_str = ";".join(conn_parts) + ";"
            return pyodbc.connect(conn_str)
        except pyodbc.InterfaceError as e:
            last_error = e
            # If this is a driver not found error, try the next driver
            if "Data source name not found" in str(e) or "IM002" in str(e):
                continue
            else:
                # Different error, re-raise immediately
                raise
        except Exception as e:
            # Non-driver related error, re-raise immediately
            raise
    
    # If we get here, all drivers failed
    raise last_error if last_error else Exception("No suitable ODBC driver found")

# --------------------------
# QUERY HELPERS
# --------------------------
def run_query(
    sql_or_path: Union[str, 'Path'],
    db_key: str,
    params: Optional[tuple] = None,
    index_col: Optional[str] = None
) -> pd.DataFrame:
    """
    Run a SELECT SQL (inline or .sql file) and return DataFrame.
    """
    if isinstance(sql_or_path, str) and sql_or_path.strip().lower().endswith(".sql"):
        with open(sql_or_path, "r") as f:
            query = f.read()
    else:
        query = sql_or_path

    with get_connection(db_key) as conn:
        return pd.read_sql(query, conn, params=params, index_col=index_col)

def run_query_with_display(
    migration_path: 'Path',
    db_key: str,
    max_rows: int = 20,
    verbose: bool = True
) -> bool:
    """
    Run a SQL query and display results as DataFrame with row limits.
    Used by run_migration.py with --show-results flag.
    """
    try:
        # Read SQL file
        with open(migration_path, "r") as f:
            query = f.read()
            
        if verbose:
            print(f"📊 Executing query from: {migration_path.name}")
            
        # Execute query and get results
        df = run_query(query, db_key)
        
        if verbose:
            print(f"✅ Query executed successfully")
            print(f"📈 Total rows: {len(df)}")
            print(f"🔍 Displaying first {min(max_rows, len(df))} rows:")
            print("=" * 60)
            
        # Display results with row limit
        if len(df) > 0:
            display_df = df.head(max_rows)
            print(display_df.to_string(index=False))
            
            if len(df) > max_rows:
                print(f"\n... ({len(df) - max_rows} more rows not shown)")
        else:
            print("No results returned")
            
        return True
        
    except Exception as e:
        if verbose:
            print(f"❌ Query failed: {str(e)}")
        return False

def execute(
    sql_or_path: Union[str, 'Path'],
    db_key: str,
    params: Optional[tuple] = None,
    commit: bool = True
) -> int:
    """
    Execute (INSERT/UPDATE/DELETE). Returns affected row count.
    """
    if isinstance(sql_or_path, str) and sql_or_path.strip().lower().endswith(".sql"):
        with open(sql_or_path, "r") as f:
            query = f.read()
    else:
        query = sql_or_path

    with get_connection(db_key) as conn, conn.cursor() as cur:
        cur.execute(query, params or ())
        rowcount = cur.rowcount
        if commit:
            conn.commit()
        return rowcount

# --------------------------
# MIGRATION HELPERS
# --------------------------
def extract_migration_metadata(script_content: str) -> dict:
    """
    Extract structured metadata from SQL migration files.
    
    Parses Architecture Validation sections, Next Steps, and Success messages
    from SQL comments to provide rich feedback after migration execution.
    
    Args:
        script_content: The SQL script content to parse
        
    Returns:
        dict: Extracted metadata with 'validation', 'next_steps', 'success_info' keys
    """
    import re
    
    metadata = {
        'validation': [],
        'next_steps': [],
        'success_info': []
    }
    
    lines = script_content.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        
        # Remove SQL comment prefixes
        clean_line = line.replace('-- ', '').replace('PRINT ', '').strip()
        clean_line = clean_line.replace("'", "").replace(";", "")
        
        # Skip empty lines and pure comment separators
        if not clean_line or clean_line.startswith('=') or clean_line in ['', "''", '']:
            continue
        
        # Section detection
        if 'ARCHITECTURE VALIDATION' in clean_line.upper():
            current_section = 'validation'
            continue
        elif 'NEXT STEPS' in clean_line.upper():
            current_section = 'next_steps'
            continue
        elif 'SUCCESS MESSAGE' in clean_line.upper() or 'SUCCESS:' in clean_line.upper():
            current_section = 'success_info'
            continue
        
        # Extract content based on current section
        if current_section == 'validation' and ('✅' in clean_line or clean_line.startswith('✅')):
            metadata['validation'].append(clean_line)
        elif current_section == 'next_steps' and (clean_line.startswith(('1.', '2.', '3.', '4.', '5.'))):
            metadata['next_steps'].append(clean_line)
        elif current_section == 'success_info' and ('- ' in clean_line or clean_line.startswith('-')):
            metadata['success_info'].append(clean_line)
    
    return metadata

def display_migration_summary(migration_name: str, metadata: dict, verbose: bool = True):
    """
    Display formatted migration summary with extracted metadata.
    
    Args:
        migration_name: Name of the migration file
        metadata: Extracted metadata from extract_migration_metadata
        verbose: Whether to show detailed output
    """
    if not verbose:
        return
    
    print()
    print("=" * 70)
    print(f"🎯 MIGRATION SUMMARY: {migration_name}")
    print("=" * 70)
    
    # Architecture Validation
    if metadata['validation']:
        print()
        print("📋 ARCHITECTURE VALIDATION:")
        for item in metadata['validation']:
            print(f"   {item}")
    
    # Next Steps
    if metadata['next_steps']:
        print()
        print("🚀 NEXT STEPS:")
        for step in metadata['next_steps']:
            print(f"   {step}")
    
    # Success Information
    if metadata['success_info']:
        print()
        print("✅ COLUMN STATUS:")
        for info in metadata['success_info']:
            print(f"   {info}")
    
    print()
    print("=" * 70)
    print()

def run_migration(
    migration_path: Union[str, Path],
    db_key: str = 'UNIFIED_ORDERS',
    verbose: bool = True
) -> bool:
    """
    Execute a SQL migration file against the specified database.
    
    Enhanced with metadata extraction to display Architecture Validation,
    Next Steps, and Success information from SQL comments.
    
    Args:
        migration_path: Path to the .sql migration file
        db_key: Database key from config.yaml (default: UNIFIED_ORDERS)
        verbose: Whether to print progress messages
        
    Returns:
        bool: True if migration succeeded, False otherwise
    """
    try:
        migration_path = Path(migration_path)
        
        if not migration_path.exists():
            raise FileNotFoundError(f"Migration file not found: {migration_path}")
        
        if verbose:
            logger.info(f"PROCESS: Running migration: {migration_path.name}")
            logger.info(f"INFO: Database: {db_key}")
        
        # Read the migration script
        with open(migration_path, 'r', encoding='utf-8') as f:
            script = f.read()
        
        if not script.strip():
            raise ValueError(f"Migration file is empty: {migration_path}")
        
        # Extract metadata before execution
        metadata = extract_migration_metadata(script)
        
        # Execute the migration
        with get_connection(db_key) as conn:
            cursor = conn.cursor()
            cursor.execute(script)
            conn.commit()
            cursor.close()
        
        if verbose:
            logger.info(f"SUCCESS: Migration completed successfully: {migration_path.name}")
        
        # Display enhanced summary with extracted metadata
        display_migration_summary(migration_path.name, metadata, verbose)
        
        return True
        
    except Exception as e:
        if verbose:
            logger.error(f"ERROR: Migration failed: {migration_path.name if 'migration_path' in locals() else migration_path}")
            logger.error(f"ERROR: {str(e)}")
        return False

def run_migrations_directory(
    migrations_dir: Union[str, Path],
    db_key: str = 'UNIFIED_ORDERS',
    pattern: str = "*.sql",
    verbose: bool = True
) -> dict:
    """
    Execute all SQL migration files in a directory in alphabetical order.
    
    Args:
        migrations_dir: Path to directory containing migration files
        db_key: Database key from config.yaml (default: UNIFIED_ORDERS)
        pattern: File pattern to match (default: *.sql)
        verbose: Whether to print progress messages
        
    Returns:
        dict: Results summary with 'successful', 'failed', and 'details' keys
    """
    migrations_dir = Path(migrations_dir)
    
    if not migrations_dir.exists():
        raise FileNotFoundError(f"Migrations directory not found: {migrations_dir}")
    
    # Find all migration files and sort them
    migration_files = sorted(migrations_dir.glob(pattern))
    
    if not migration_files:
        if verbose:
            logger.info(f"WARNING: No migration files found in: {migrations_dir}")
        return {'successful': 0, 'failed': 0, 'details': []}
    
    if verbose:
        logger.info(f"PROCESS: Running {len(migration_files)} migrations from: {migrations_dir}")
        logger.info("=" * 60)
    
    results = {'successful': 0, 'failed': 0, 'details': []}
    
    for migration_file in migration_files:
        success = run_migration(migration_file, db_key, verbose)
        
        result_detail = {
            'file': migration_file.name,
            'success': success,
            'path': str(migration_file)
        }
        
        if success:
            results['successful'] += 1
        else:
            results['failed'] += 1
        
        results['details'].append(result_detail)
        
        if verbose:
            logger.info("-" * 60)
    
    if verbose:
        logger.info(f"\nINFO: Migration Summary:")
        logger.info(f"   SUCCESS: {results['successful']}")
        logger.info(f"   FAILED: {results['failed']}")
        logger.info(f"   TOTAL: {len(migration_files)}")
    
    return results
