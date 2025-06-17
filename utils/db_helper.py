"""
Lightweight SQL helper for Kestra/data pipelines.
- Loads DB credentials from config.yaml in the working directory
- Uses ODBC Driver 17 for SQL Server
"""

import os
import pyodbc
import pandas as pd
import yaml
from pathlib import Path
from typing import Union, Optional

import warnings
warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy connectable")


# --------------------------
# CONSTANTS
# --------------------------
DEFAULT_DRIVER = "{ODBC Driver 17 for SQL Server}"

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
