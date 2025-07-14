#!/usr/bin/env python3
"""
Unified Monday.com Board Loader
===============================

Dynamic board extraction system that combines the best of:
- monday_refresh.py: Fast ETL with atomic swaps
- universal_board_extractor.py: Template-based generation

Usage:
    python load_boards.py --board-id 9200517329
    python load_boards.py --board-id 9200517329 --generate-config-only
    python load_boards.py --board-id 9200517329 --update-registry

Features:
- JSON-based configuration (not TOML)
- Auto-generation of missing configs with user guidance
- Helper-based architecture using existing utils/
- Atomic swap operations for zero-downtime
- Registry management for board tracking
- Workflow generation for Kestra
"""

import sys
import os
import json
import argparse
import time
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from tqdm import tqdm as tqdm_orig

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Fallback: manually load .env file
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# ─────────────────── Repository Root & Utils Import ───────────────────
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

# Import helpers
import db_helper as db
import logger_helper
import staging_helper

# Set staging mode for Monday.com boards (dirty data requires robust handling)
staging_helper.set_staging_mode('robust')

# Load configuration from centralized config
config = db.load_config()

logger = logger_helper.get_logger("load_boards")

# ─────────────────── Feature Flags ───────────────────
ENABLE_TQDM = False
ENABLE_REGISTRY_WRITE = False

def tqdm_wrapper(iterable, **kwargs):
    if ENABLE_TQDM:
        return tqdm_orig(iterable, **kwargs)
    else:
        return iterable

# ─────────────────── Data Conversion Functions ───────────────────

def safe_date_convert(val):
    """Robust date conversion handling Monday.com formats and SQL Server constraints"""
    # Handle None, NaN, empty strings, and Monday.com's literal "None" string
    if (pd.isna(val) or val is None or 
        str(val).strip() in ['', 'None', 'nan', 'null', 'NaT']):
        return None
    
    # If already a date object, return as-is
    import datetime
    if isinstance(val, datetime.date):
        return val
    
    try:
        val_str = str(val).strip()
        
        # Skip obviously invalid values
        if val_str in ['', 'None', 'nan', 'null', 'NaT']:
            return None
        
        # Handle Monday.com JSON date format: {"date":"2025-06-13","icon":""}
        if val_str.startswith('{"date":"') and val_str.endswith('"}'):
            try:
                import json
                date_obj = json.loads(val_str)
                if 'date' in date_obj and date_obj['date']:
                    date_str = date_obj['date']
                    # Validate the extracted date
                    parsed = pd.to_datetime(date_str, format='%Y-%m-%d', errors='raise')
                    if pd.notna(parsed) and 1753 <= parsed.year <= 9999:
                        return parsed.date()
                
            except:
                pass
        
        # Handle ISO datetime strings (like UpdateDate)
        if 'T' in val_str and 'Z' in val_str:
            clean_date = val_str.split('T')[0]
            try:
                parsed = pd.to_datetime(clean_date, format='%Y-%m-%d', errors='raise')
                if pd.notna(parsed) and 1753 <= parsed.year <= 9999:
                    return parsed.date()
            except:
                pass
        
        # Handle ISO date strings (YYYY-MM-DD) - most common case
        import re
        if re.match(r'^\d{4}-\d{2}-\d{2}$', val_str):
            try:
                parsed = pd.to_datetime(val_str, format='%Y-%m-%d', errors='raise')
                if pd.notna(parsed) and 1753 <= parsed.year <= 9999:
                    return parsed.date()
            except:
                pass

        # Last resort: try pandas general conversion
        parsed = pd.to_datetime(val, errors="coerce")
        if pd.notna(parsed) and 1753 <= parsed.year <= 9999:
            return parsed.date()
        return None

    except Exception:
        return None

def safe_numeric_convert(val):
    """Robust numeric conversion handling Monday.com formats and edge cases"""
    # Handle NumPy NaN specifically
    if pd.isna(val) or val is None:
        return None
    # Handle numpy nan explicitly
    if hasattr(val, 'dtype') and pd.isna(val):
        return None
    # Handle string representations
    if isinstance(val, str):
        clean_val = val.strip()
        if clean_val == '' or clean_val.lower() in ['none', 'nan', 'null']:
            return None
        try:
            # Try integer first, then float
            if '.' not in clean_val:
                return int(clean_val)
            else:
                return float(clean_val)
        except:
            return None
    # Handle numeric types
    try:
        if hasattr(val, 'dtype'):
            # Handle numpy types with NaN check
            if 'int' in str(val.dtype) and not pd.isna(val):
                return int(val)
            elif 'float' in str(val.dtype) and not pd.isna(val):
                return float(val)
            else:
                return None
        return val
    except:
        return None

def safe_string_convert(val):
    """Robust string conversion handling Monday.com null variations"""
    if pd.isna(val) or val is None:
        return None
    try:
        str_val = str(val).strip()
        if str_val in ['None', 'nan', 'null', '']:
            return None
        return str_val
    except:
        return None

# ─────────────────── Environment & API Setup ───────────────────
# Load centralized configuration (like get_board_planning.py)
config = db.load_config()

MONDAY_TOKEN = os.getenv('MONDAY_API_KEY') or config.get('apis', {}).get('monday', {}).get('api_token')
API_VER = "2025-04"
API_URL = config.get('apis', {}).get('monday', {}).get('api_url', "https://api.monday.com/v2")

if not MONDAY_TOKEN or MONDAY_TOKEN == "YOUR_MONDAY_API_TOKEN_HERE":
    logger.error("MONDAY_API_KEY environment variable not set or config.yaml not configured")
    sys.exit(1)

API_URL = config.get('apis', {}).get('monday', {}).get('api_url', "https://api.monday.com/v2")
HEADERS = {
    "Authorization": f"Bearer {MONDAY_TOKEN}",
    "API-Version": API_VER,
    "Content-Type": "application/json"
}

# ─────────────────── Configuration Management ───────────────────

def get_config_path(board_id: int) -> Path:
    """Get path to board configuration file"""
    return repo_root / "configs" / "boards" / f"board_{board_id}.json"

def get_registry_path() -> Path:
    """Get path to board registry file"""
    return repo_root / "configs" / "registry.json"

def load_board_json_config(board_id: int) -> Dict[str, Any]:
    """Load board configuration from single metadata file (new single-file approach)"""
    metadata_path = repo_root / "configs" / "boards" / f"board_{board_id}_metadata.json"
    
    if not metadata_path.exists():
        logger.info(f"Board metadata not found for {board_id}, running discovery...")
        # Auto-run discovery if metadata doesn't exist
        logger.info("TIP: Run discovery first: python pipelines/codegen/universal_board_extractor.py --board-id {board_id}")
        sys.exit(1)
    
    # Load metadata file
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    logger.info(f"SCHEMA: Loaded metadata for board {board_id}: {metadata_path}")
    return metadata

def auto_generate_config_template(board_id: int) -> Dict[str, Any]:
    """Auto-generate configuration template by inspecting board schema"""
    logger.info(f"SEARCH: Inspecting board {board_id} to generate config template...")
    
    # Fetch board metadata
    board_info = fetch_board_info(board_id)
    board_name = board_info.get('name', f'Board_{board_id}')
    
    # Generate table name (clean board name)
    table_name = f"MON_{board_name.replace(' ', '').replace('-', '_')}"
    
    template_config = {
        "meta": {
            "board_id": board_id,
            "board_name": board_name,
            "table_name": table_name,
            "db_name": "orders",
            "schema_version": "1.0",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        "column_mappings": {
            "default_rule": {
                "sql": "NVARCHAR(255)",
                "include": True
            },
            "type_overrides": {
                "date": {"sql": "DATE"},
                "numbers": {"sql": "DECIMAL(18,2)"},
                "numeric": {"sql": "DECIMAL(18,2)"},
                "status": {"sql": "NVARCHAR(50)", "field": "label"},
                "dropdown": {"sql": "NVARCHAR(100)", "field": "text"},
                "people": {"sql": "NVARCHAR(255)", "field": "text"}
            },
            "column_overrides": {
                # User can add specific column customizations here
            }
        },
        "exclusions": {
            "column_ids": [],
            "column_titles": ["Internal Notes", "Private Comments"]
        }
    }
    
    return template_config

def fetch_board_info(board_id: int) -> Dict[str, Any]:
    """Fetch basic board information (items_count only - terminology comes from metadata)"""
    query = """
    query ($ids: [ID!]!) {
        boards(ids: $ids) {
            name
            description
            items_count
        }
    }
    """
    
    response = gql_request(query, {"ids": [board_id]})
    return response["boards"][0] if response["boards"] else {}

def update_board_registry(board_id: int, metadata: Dict[str, Any], status: str = "active"):
    """Update the board registry with current board info (single metadata file)"""
    if not ENABLE_REGISTRY_WRITE:
        logger.info(f"SKIP: Registry update skipped (ENABLE_REGISTRY_WRITE is False)")
        return
    registry_path = get_registry_path()
    
    # Load existing registry
    if registry_path.exists():
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
    else:
        registry = {
            "boards": {},
            "metadata": {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        }
    
    # Update board entry using new metadata structure
    registry["boards"][str(board_id)] = {
        "board_name": metadata["board_name"],
        "table_name": metadata["table_name"],
        "database": metadata["database"],
        "last_run": datetime.now().isoformat(),
        "status": status,
        "metadata_path": f"configs/boards/board_{board_id}_metadata.json",
        "workflow_path": f"workflows/extract_board_{board_id}.yaml"
    }
    
    registry["metadata"]["updated_at"] = datetime.now().isoformat()
    
    # Save registry
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2)
    
    logger.info(f"SUCCESS: Updated registry for board {board_id}")

# ─────────────────── Monday GraphQL Requests ───────────────────

def process_metadata_columns(metadata: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, str]]:
    """
    Process metadata columns once and return both column rules and type mapping.
    Eliminates duplication between DataFrame building and SQL schema creation.
    
    Returns:
        tuple: (columns_meta for DataFrame, column_type_map for SQL)
    """
    columns_meta = {}
    column_type_map = {}
    
    for col in metadata.get("columns", []):
        # Skip excluded columns entirely
        if col.get("exclude", False):
            continue
            
        # Build column rule for DataFrame construction
        sql_type = col.get("custom_sql_type") or col["sql_type"]
        extraction_field = col.get("custom_extraction_field") or col["extraction_field"]
        
        col_rule = {
            "title": col["monday_title"],
            "type": col["monday_type"],
            "field": extraction_field,
            "sql": sql_type,
            "nullable": col.get("nullable", True),
            "conversion_logic": col.get("conversion_logic")
        }
        
        # Add to both collections
        columns_meta[col["monday_id"]] = col_rule
        
        # CRITICAL FIX: Use monday_title as key (DataFrame column name), not sql_column
        # This ensures column_type_map matches actual DataFrame column names
        if sql_type:
            column_type_map[col["monday_title"]] = sql_type
    
    return columns_meta, column_type_map if column_type_map else None

def gql_request(query: str, variables: Dict = None, max_retries: int = 3, timeout: int = 60) -> Dict[str, Any]:
    """Execute GraphQL request with retries"""
    for attempt in range(max_retries):
        try:
            payload = {"query": query}
            if variables:
                payload["variables"] = variables
            
            response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                raise Exception(f"GraphQL errors: {data['errors']}")
            
            return data["data"]
            
        except requests.RequestException as e:
            logger.warning(f"Request attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff

def fetch_board_schema_from_metadata(board_id: int) -> tuple:
    """Load board schema from single metadata file (new single-file approach)"""
    metadata_path = repo_root / "configs" / "boards" / f"board_{board_id}_metadata.json"
    
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}. Run discovery first.")
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # Get item terminology from metadata with overwrite capability
    item_terminology_config = metadata.get("item_terminology", {"name": "Item", "overwrite_name": ""})
    if item_terminology_config.get("overwrite_name"):
        item_terminology = item_terminology_config["overwrite_name"]
    else:
        item_terminology = item_terminology_config.get("name", "Item")
    
    columns_meta = {}
    
    # Process columns using consolidated function
    columns_meta, _ = process_metadata_columns(metadata)
    
    logger.info(f"DATA: Schema loaded from metadata: {len(columns_meta)} columns mapped")
    logger.info(f"DATA: Item terminology: '{item_terminology}'")
    return item_terminology, columns_meta

def get_column_rule_from_metadata(column: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get mapping rule for a column from enhanced metadata (single-file approach)"""
    # Check if excluded
    if column.get("exclude", False):
        return None
    
    # Use custom overrides or defaults
    sql_type = column.get("custom_sql_type") or column["sql_type"]
    extraction_field = column.get("custom_extraction_field") or column["extraction_field"]
    
    return {
        "title": column["monday_title"],
        "type": column["monday_type"],
        "field": extraction_field,
        "sql": sql_type,
        "nullable": column.get("nullable", True),
        "conversion_logic": column.get("conversion_logic")
    }

def fetch_all_items(board_id: int, limit: int = 400) -> List[Dict[str, Any]]:
    """Fetch all board items with pagination"""
    items = []
    cursor = None
    
    while True:
        cursor_arg = f', cursor: "{cursor}"' if cursor else ''
        query = f'''
        query {{
            boards(ids: {board_id}) {{
                items_page(limit: {limit}{cursor_arg}) {{
                    cursor
                    items {{
                        id
                        name
                        updated_at
                        group {{ title }}
                        column_values {{
                            id
                            text
                            value
                            ... on MirrorValue {{ display_value }}
                            ... on BoardRelationValue {{ display_value }}
                            ... on FormulaValue {{ display_value }}
                            ... on DateValue {{ text }}
                            ... on DependencyValue {{ display_value }}
                            ... on StatusValue {{ label }}
                            ... on DropdownValue {{ text }}
                            ... on PeopleValue {{ text }}
                            ... on ItemIdValue {{ item_id }}
                        }}
                    }}
                }}
            }}
        }}
        '''
        
        data = gql_request(query)
        page = data["boards"][0]["items_page"]
        batch = page["items"]
        
        items.extend(batch)
        cursor = page.get("cursor")
        
        logger.info(f"FETCH: Fetched {len(batch)} items (total: {len(items)})")
        
        if not cursor or not batch:
            break
            
        time.sleep(0.1)  # Rate limiting
    
    return items

# ─────────────────── Data Processing & ETL ───────────────────

def extract_column_value(column_value: Dict[str, Any], column_meta: Dict[str, Any]) -> Any:
    """Extract value from column_value based on column metadata"""
    field = column_meta["field"]
    col_type = column_meta.get("type", "")
    
    # Handle date columns
    if col_type == "date":
        if column_value.get("text"):
            return column_value["text"]
        if column_value.get("value"):
            try:
                # Parse date from value if needed
                return column_value["value"]
            except:
                pass
    
    # Handle numeric columns
    if col_type in ("numbers", "numeric"):
        try:
            value = column_value.get("text", "").replace(",", "")
            return float(value) if value else None
        except:
            return None
    
    # Default field extraction
    return (column_value.get(field) or 
            column_value.get("text") or 
            column_value.get("label") or 
            column_value.get("display_value"))

def build_dataframe(items: List[Dict[str, Any]], columns_meta: Dict[str, Any], item_terminology: str) -> pd.DataFrame:
    """Build DataFrame from Monday items"""
    records = []
    
    for item in tqdm_wrapper(items, desc="PROCESS: Building DataFrame", unit="item"):
        record = {
            item_terminology: item["name"],
            "UpdateDate": item["updated_at"],
            "Group": item["group"]["title"],
            "Item ID": int(item["id"])
        }
        
        # Extract column values
        for column_value in item["column_values"]:
            col_id = column_value["id"]
            if col_id in columns_meta:
                col_meta = columns_meta[col_id]
                record[col_meta["title"]] = extract_column_value(column_value, col_meta)
        
        records.append(record)
    
    df = pd.DataFrame(records)
    logger.info(f"SUCCESS: DataFrame built: {len(df)} rows x {len(df.columns)} columns")
    return df

def clean_dataframe(df: pd.DataFrame, metadata: Dict[str, Any] = None) -> pd.DataFrame:
    """Clean and optimize DataFrame for SQL insertion with robust Monday.com handling"""
    
    logger.info("PROCESS: Applying data conversions...")
    
    # Apply metadata-driven conversions if available
    if metadata and "columns" in metadata:
        # Process conversions using successful pattern from get_board_planning.py
        for col_info in metadata["columns"]:
            if col_info.get("exclude", False):
                continue
                
            # CRITICAL FIX: Use monday_title (DataFrame column name), not sql_column
            monday_title = col_info.get("monday_title", "")
            sql_type = col_info.get("custom_sql_type") or col_info.get("sql_type", "")
            monday_type = col_info.get("monday_type", "")
            
            if monday_title not in df.columns:
                continue
            
            # Apply conversions based on type - following successful get_board_planning.py pattern
            if "DATE" in sql_type.upper() or monday_type == "date":
                logger.info(f"CONVERT: Converting date column '{monday_title}' from strings to datetime.date objects")
                original_count = df[monday_title].notna().sum()
                df[monday_title] = df[monday_title].apply(safe_date_convert)
                converted_count = df[monday_title].notna().sum()
                null_count = df[monday_title].isna().sum()
                logger.info(f"    {monday_title}: {original_count} -> {converted_count} valid dates, {null_count} nulls")
                
            elif ("DECIMAL" in sql_type.upper() or "NUMERIC" in sql_type.upper() or 
                  "INT" in sql_type.upper() or monday_type == "numbers"):
                logger.info(f"CONVERT: Converting numeric column '{monday_title}' (type: {sql_type}, monday_type: {monday_type})")
                
                # Use proven approach from get_board_planning.py - define function in scope
                def safe_numeric_convert_scoped(val):
                    # Handle NumPy NaN specifically
                    if pd.isna(val) or val is None:
                        return None
                    # Handle numpy nan explicitly  
                    if hasattr(val, 'dtype') and pd.isna(val):
                        return None
                    # Handle string representations
                    if isinstance(val, str):
                        clean_val = val.strip()
                        if clean_val == '' or clean_val.lower() in ['none', 'nan', 'null']:
                            return None
                        try:
                            # Try integer first, then float
                            if '.' not in clean_val:
                                return int(clean_val)
                            else:
                                return float(clean_val)
                        except:
                            return None
                    # Handle numeric types
                    try:
                        if hasattr(val, 'dtype'):
                            # Handle numpy types with NaN check
                            if 'int' in str(val.dtype) and not pd.isna(val):
                                return int(val)
                            elif 'float' in str(val.dtype) and not pd.isna(val):
                                return float(val)
                            else:
                                return None
                        return val
                    except:
                        return None
                
                original_count = df[monday_title].notna().sum()
                sample_values_before = [str(x) for x in df[monday_title].head(3).tolist()]
                logger.info(f"    BEFORE: {monday_title} sample values: {sample_values_before}")
                
                # Apply conversion using proven pattern
                df[monday_title] = df[monday_title].apply(safe_numeric_convert_scoped)
                
                converted_count = df[monday_title].notna().sum()
                sample_values_after = [str(x) for x in df[monday_title].head(3).tolist()]
                logger.info(f"    AFTER: {monday_title}: {original_count} -> {converted_count} valid numbers")
                logger.info(f"    AFTER: {monday_title} sample values: {sample_values_after}")
                logger.info(f"    AFTER: {monday_title} dtype: {df[monday_title].dtype}")
                
            else:
                df[monday_title] = df[monday_title].apply(safe_string_convert)
    
    else:
        # Fallback: Apply basic conversions
        logger.info("PROCESS: Applying basic conversions (no metadata)...")
        
        # Convert common date columns
        date_cols = [c for c in df.columns if "DATE" in c.upper() or c in ["UpdateDate"]]
        for col in date_cols:
            if col in df.columns:
                df[col] = df[col].apply(safe_date_convert)
        
        # Try numeric conversion for object columns (excluding known text columns)
        text_cols = ["Group", "Name", "Item"]
        for col in df.columns:
            if col in text_cols or col == "Item ID":
                continue
            if df[col].dtype == object:
                # Test if column is numeric
                numeric_test = pd.to_numeric(df[col], errors='coerce')
                if not numeric_test.isna().all():
                    df[col] = df[col].apply(safe_numeric_convert)
                else:
                    df[col] = df[col].apply(safe_string_convert)
    
    # Final cleanup: Convert NaN to None for SQL Server
    df = df.where(pd.notna(df), None)
    
    logger.info(f"PROCESS: Cleaned {len(df.columns)} columns")
    return df

def make_sql_safe(df: pd.DataFrame) -> pd.DataFrame:
    """Make DataFrame safe for SQL insertion"""
    for col in df.columns:
        if df[col].dtype == "O":  # object dtype
            df[col] = df[col].astype(str).replace('nan', None)
    
    return df

# ─────────────────── Database Operations ───────────────────

def prepare_staging_table(df: pd.DataFrame, metadata: dict):
    """Prepare staging table using metadata configuration"""
    # Use consolidated metadata processing to get column type map
    _, column_type_map = process_metadata_columns(metadata)
    
    # DEBUG: Log the column type map to verify date columns
    logger.info(f"SCHEMA: Processing {len(column_type_map)} column type mappings")
    date_columns = {k: v for k, v in column_type_map.items() if v == "DATE"}
    logger.info(f"SCHEMA: Found {len(date_columns)} DATE columns: {list(date_columns.keys())}")
    
    # DEBUG: Validate DataFrame dtypes for date columns
    for col_name in date_columns.keys():
        if col_name in df.columns:
            dtype = df[col_name].dtype
            sample_values = df[col_name].dropna().head(3).tolist()
            logger.info(f"SCHEMA:   {col_name}: dtype={dtype}, sample={sample_values}")
    
    staging_helper.prepare_staging_table(
        df,
        f"swp_{metadata['table_name']}",
        metadata['table_name'],
        metadata['database'],
        column_type_map=column_type_map
    )

def load_to_staging_table(df: pd.DataFrame, metadata: dict):
    """Load data to staging table with optimal batch size"""
    optimal_batch_size = min(1000, max(100, len(df) // 10))
    logger.info(f"Using batch size: {optimal_batch_size} for {len(df)} rows")
    staging_helper.load_to_staging_table(df, f"swp_{metadata['table_name']}", 
                                        metadata['database'], batch_size=optimal_batch_size)

def atomic_swap_tables(metadata: dict):
    """Perform atomic table swap"""
    staging_helper.atomic_swap_tables(f"swp_{metadata['table_name']}", 
                                     metadata['table_name'], metadata['database'])

def execute_etl_pipeline(board_id: int, metadata: Dict[str, Any]):
    """Execute the complete ETL pipeline using single metadata file"""
    logger.info(f"START: Starting ETL pipeline for board {board_id}")
    
    # Get configuration from metadata structure
    table_name = metadata["table_name"]
    db_name = metadata["database"]
    stage_table = f"swp_{table_name}"
    
    start_time = time.time()
    
    # 1. Load schema from metadata file
    logger.info("SCHEMA: 1/5 Loading board schema from metadata...")
    item_terminology, columns_meta = fetch_board_schema_from_metadata(board_id)
    
    # 2. Fetch all items
    logger.info("FETCH 2/5 Fetching board items...")
    items = fetch_all_items(board_id)
    
    # 3. Build and clean DataFrame
    logger.info("PROCESS 3/5 Processing data...")
    df = build_dataframe(items, columns_meta, item_terminology)
    
    # Apply column duplications from metadata (if any)
    df = staging_helper.apply_column_duplications(df, metadata)
    
    df = clean_dataframe(df, metadata)
    df = make_sql_safe(df)
    
    # 4. Prepare staging table
    logger.info("STAGING 4/5 Preparing staging table...")
    prepare_staging_table(df, metadata)
    
    # 5. Load to staging and atomic swap
    logger.info("SAVE 5/5 Loading data and swapping tables...")
    load_to_staging_table(df, metadata)
    atomic_swap_tables(metadata)
    
    # Performance metrics
    elapsed_time = time.time() - start_time
    rows_per_sec = len(df) / elapsed_time if elapsed_time > 0 else 0
    
    logger.info(f"SUCCESS ETL Complete: {len(df)} rows loaded to {db_name}.{table_name}")
    logger.info(f"TIME Total time: {elapsed_time:.2f}s ({rows_per_sec:.0f} rows/sec)")
    
    # Update registry
    update_board_registry(board_id, metadata, "active")

# ─────────────────── Main CLI Interface ───────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Unified Monday.com Board Loader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python load_boards.py --board-id 9200517329
  python load_boards.py --board-id 9200517329 --generate-config-only
  python load_boards.py --board-id 9200517329 --update-registry
        """
    )
    
    parser.add_argument('--board-id', required=True, type=int, help='Monday.com board ID')
    parser.add_argument('--generate-config-only', action='store_true', 
                       help='Only generate config template, do not run ETL')
    parser.add_argument('--update-registry', action='store_true',
                       help='Update registry after manual config changes')
    
    args = parser.parse_args()
    
    logger.info(f"START: Unified Monday.com Board Loader")
    logger.info(f"SCHEMA: Board ID: {args.board_id}")
    
    try:
        # Load board configuration (JSON pattern like get_board_planning.py)
        board_config = load_board_json_config(args.board_id)
        
        if args.generate_config_only:
            logger.info("SUCCESS: Config generation complete")
            return
        
        if args.update_registry:
            update_board_registry(args.board_id, board_config)
            logger.info("SUCCESS: Registry updated")
            return
        
        # Execute ETL pipeline
        execute_etl_pipeline(args.board_id, board_config)
        
        logger.info("COMPLETE: Board loading complete!")
        
    except Exception as e:
        logger.error(f"ERROR: {e}")
        raise

if __name__ == "__main__":
    main()
