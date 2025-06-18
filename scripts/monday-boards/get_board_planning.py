#!/usr/bin/env python3
"""
HYBRID ETL Script: Monday.com to SQL Server with Zero-Downtime Staging
Combines production-proven API/data processing with zero-downtime staging approach
DEVELOPMENT VERSION - Testing hybrid approach
"""

import os, requests, pandas as pd, pyodbc, asyncio, concurrent.futures, logging, yaml
from datetime import datetime
import time
import sys
from pathlib import Path

# NEW STANDARD: Find repository root, then find utils (Option 2)
def find_repo_root():
    """Find the repository root by looking for utils folder"""
    current_path = Path(__file__).resolve()
    while current_path.parent != current_path:  # Not at filesystem root
        utils_path = current_path / "utils"
        if utils_path.exists() and (utils_path / "db_helper.py").exists():
            return current_path
        current_path = current_path.parent
    raise RuntimeError("Could not find repository root with utils folder")

# Add utils to path using repository root method
repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))
import db_helper as db

# Import centralized logger helper for Kestra/VS Code compatibility
import logger_helper
logger = logger_helper.get_logger("monday_planning_etl")

# Load configuration from centralized config
config = db.load_config()

# Import centralized mapping system
import mapping_helper as mapping

# Configuration - Monday.com API settings
# Use centralized mapping system for board configuration
board_config = mapping.get_board_config('coo_planning')
BOARD_ID = int(board_config['board_id'])
TABLE_NAME = board_config['table_name']  # MON_COO_Planning
DATABASE_NAME = board_config['database']  # orders
MONDAY_TOKEN = os.getenv('MONDAY_API_KEY') or config.get('apis', {}).get('monday', {}).get('api_token')
API_VER = "2025-04"
API_URL = config.get('apis', {}).get('monday', {}).get('api_url', "https://api.monday.com/v2")

# Production configuration - runs on full dataset
# Set TEST_MODE=true environment variable for limited testing
TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'
TEST_LIMIT = 100  # Number of records to fetch in test mode (when enabled)

# HITL Configuration - Schema approval settings
AUTO_REJECT_BOARD_RELATIONS = True  # Automatically reject board_relation columns without prompting

if not MONDAY_TOKEN or MONDAY_TOKEN == "YOUR_MONDAY_API_TOKEN_HERE":
    raise ValueError("Monday.com API token not configured. Please set MONDAY_API_KEY environment variable or update utils/config.yaml")

HEADERS = {
    "Authorization": f"Bearer {MONDAY_TOKEN}",
    "API-Version": API_VER,
    "Content-Type": "application/json"
}

# Logger configured via logger_helper (Kestra-compatible)

def gql(query_string, max_retries=3, timeout=60):
    """Execute GraphQL query against Monday.com API with retry logic"""
    for attempt in range(max_retries):
        try:
            response = requests.post(
                API_URL,
                headers=HEADERS,
                json={"query": query_string},
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()["data"]
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 500 and attempt < max_retries - 1:
                logger.warning(f"Monday.com API error (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            raise
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                logger.warning(f"Request error (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(2 ** attempt)
                continue
            raise

def fetch_board_data_with_pagination():
    """Fetch ALL items from Monday.com board using cursor-based pagination"""
    mode_text = f" (TEST MODE - limit {TEST_LIMIT})" if TEST_MODE else ""
    logger.info(f"Fetching data from Monday.com board {BOARD_ID} with pagination{mode_text}...")
    
    all_items = []
    cursor = None
    page_num = 1
    board_name = None
    
    while True:        # Build query with pagination cursor
        cursor_arg = f', cursor: "{cursor}"' if cursor else ''
        
        query = f'''
        query GetBoardItems {{
          boards(ids: {BOARD_ID}) {{
            name
            items_page(limit: 250{cursor_arg}) {{
              cursor
              items {{
                id
                name
                updated_at
                group {{
                  id
                  title
                }}
                column_values {{
                  column {{
                    title
                    id
                    type
                  }}
                  value
                  text
                  ... on DependencyValue {{ display_value }}
                  ... on MirrorValue {{ display_value }}
                  ... on BoardRelationValue {{ display_value }}
                  ... on FormulaValue {{ display_value }}
                  ... on TextValue {{ text }}
                  ... on LongTextValue {{ text }}
                  ... on StatusValue {{ label }}
                  ... on PeopleValue {{ text }}
                  ... on DropdownValue {{ text }}
                  ... on ItemIdValue {{ item_id }}
                  ... on NumbersValue {{ number }}
                }}
              }}
            }}
          }}
        }}
        '''
        
        data = gql(query)
        board = data["boards"][0]
        
        # Store board name from first page
        if board_name is None:
            board_name = board["name"]
        
        items_page = board["items_page"]
        items = items_page["items"]
        
        # Add items from this page
        all_items.extend(items)
        
        logger.info(f"   Page {page_num}: Fetched {len(items)} items (Total: {len(all_items)})")
        
        # Test mode: stop early if we hit the limit
        if TEST_MODE and len(all_items) >= TEST_LIMIT:
            all_items = all_items[:TEST_LIMIT]  # Trim to exact limit
            logger.info(f"   TEST MODE: Stopping at {len(all_items)} items")
            break
        
        # Check if there are more pages
        cursor = items_page.get("cursor")
        if not cursor or len(items) == 0:
            break
            
        page_num += 1
        
        # Add a small delay to respect rate limits
        time.sleep(0.1)  # 100ms delay between requests
    
    logger.info(f"Fetched {len(all_items)} total items from board '{board_name}' across {page_num} pages")
    return all_items, board_name

def extract_value(column_value):
    """Extract the correct value from Monday.com column based on type"""
    cv = column_value
    column_type = cv["column"]["type"]
    
    # Handle different column types with proper value extraction
    if column_type == "date":
        # For date columns, prefer the text value which is already formatted
        if cv.get("text") and cv.get("text").strip():
            return cv["text"]
        elif cv.get("value") and cv.get("value") != "None":
            return cv["value"]
        else:
            return None
    elif column_type == "dropdown" and cv.get("text"):
        return cv["text"]
    elif column_type == "status" and cv.get("label"):
        return cv["label"]
    elif column_type == "numbers" and cv.get("number") is not None:
        return cv["number"]
    elif column_type == "item_id" and cv.get("item_id"):
        return cv["item_id"]
    elif cv.get("display_value") and cv.get("display_value") != "":
        return cv["display_value"]
    elif cv.get("text"):
        return cv["text"]
    elif cv.get("value"):
        return cv["value"]
    
    return None

def process_items(items):
    """Convert Monday.com items to DataFrame"""
    logger.info("Processing items for database insert...")
    
    records = []
    for item in items:
        record = {
            "StyleKey": item["name"],
            "UpdateDate": item["updated_at"],
            "Group": item["group"]["title"],
            "Item ID": item["id"]
        }
        
        # Extract column values
        for cv in item["column_values"]:
            column_title = cv["column"]["title"]
            record[column_title] = extract_value(cv)
        
        records.append(record)
    
    df = pd.DataFrame(records)
    logger.info(f"Created DataFrame with {len(df)} rows and {len(df.columns)} columns")
    
    return df

def prepare_for_database(df):
    """Prepare DataFrame for database insert with robust conversions"""
    logger.info("Preparing data for database...")
    
    # Drop problematic columns
    df = df.drop(columns=[c for c in ["AM (linked)", "board_name"] if c in df.columns])
    
    # Handle the JSON metadata columns separately
    json_metadata_columns = ['FABRIC DUE INTO LONGSON', 'TRIMS DUE INTO LONGSON']
    for col in json_metadata_columns:
        if col in df.columns:
            logger.info(f"Processing JSON metadata column: {col}")
            
            def extract_date_from_json_metadata(val):
                """Extract date from Monday.com JSON metadata or return None"""
                if pd.isna(val) or val is None or str(val).strip() in ['', 'None', 'nan', 'null']:
                    return None
                
                try:
                    val_str = str(val).strip()
                    
                    # Handle JSON metadata: {"changed_at":"2025-04-15T23:46:22.133Z"}
                    if val_str.startswith('{"changed_at":"') and val_str.endswith('"}'):
                        import json
                        metadata_obj = json.loads(val_str)
                        if 'changed_at' in metadata_obj:
                            # Extract just the date part (YYYY-MM-DD)
                            timestamp = metadata_obj['changed_at']
                            if timestamp and 'T' in timestamp:
                                date_part = timestamp.split('T')[0]
                                # Validate the date
                                parsed = pd.to_datetime(date_part, format='%Y-%m-%d', errors='raise')
                                if pd.notna(parsed) and 1753 <= parsed.year <= 9999:
                                    return date_part
                    
                    return None  # If not valid JSON metadata, return None
                    
                except Exception:
                    return None  # If any error, return None
            
            # Apply the conversion
            original_count = df[col].notna().sum()
            df[col] = df[col].apply(extract_date_from_json_metadata)
            converted_count = df[col].notna().sum()
            null_count = df[col].isna().sum()
            logger.info(f"    {col}: {original_count} -> {converted_count} valid dates extracted from JSON, {null_count} nulls")
    
    # Process date columns with robust handling for Monday.com date formats
    exclude_from_date_processing = ['FABRIC DUE INTO LONGSON', 'TRIMS DUE INTO LONGSON']
    date_columns = [
        col for col in df.columns 
        if ('DATE' in col.upper() or col in ['UpdateDate']) 
        and col not in exclude_from_date_processing
    ]
    
    for col in date_columns:
        if col in df.columns:
            logger.info(f"Processing date column: {col}")
            
            def safe_date_convert(val):
                # Handle None, NaN, empty strings, and Monday.com's literal "None" string
                if (pd.isna(val) or val is None or 
                    str(val).strip() in ['', 'None', 'nan', 'null', 'NaT']):
                    return None
                
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
                                    return date_str
                        except:
                            pass
                    
                    # Handle ISO datetime strings (like UpdateDate)
                    if 'T' in val_str and 'Z' in val_str:
                        clean_date = val_str.split('T')[0]
                        try:
                            parsed = pd.to_datetime(clean_date, format='%Y-%m-%d', errors='raise')
                            if pd.notna(parsed) and 1753 <= parsed.year <= 9999:
                                return clean_date
                        except:
                            pass
                    
                    # Handle simple date strings (YYYY-MM-DD)
                    if len(val_str) == 10 and val_str.count('-') == 2:
                        try:
                            parsed = pd.to_datetime(val_str, format='%Y-%m-%d', errors='raise')
                            if pd.notna(parsed) and 1753 <= parsed.year <= 9999:
                                return val_str
                        except:
                            pass
                    
                    # Last resort: try pandas general conversion
                    parsed = pd.to_datetime(val, errors='coerce')
                    if pd.notna(parsed) and 1753 <= parsed.year <= 9999:
                        return parsed.strftime('%Y-%m-%d')
                    
                    return None
                    
                except Exception as e:
                    # Only log unexpected errors (not the common "None" strings)
                    if str(val) not in ['None', '', 'nan', 'null']:
                        logger.info(f"    Unexpected date conversion error for '{val}': {e}")
                    return None
            
            # Apply the conversion and show progress
            original_count = df[col].notna().sum()
            df[col] = df[col].apply(safe_date_convert)
            converted_count = df[col].notna().sum()
            null_count = df[col].isna().sum()
            logger.info(f"    {col}: {original_count} -> {converted_count} valid dates, {null_count} nulls")
    
    # Process numeric columns with robust NumPy NaN handling
    numeric_columns = [
        'BULK PO QTY', 'Fabric Lead Time', 'Precut Quantity', 'Item ID',
        'QTY WIP', 'QTY FG', 'QTY INVOICED', 'QTY FCST',
        'QTY WIP CUT', 'QTY WIP SEW', 'QTY WIP FIN', 'QTY SCRAP'
    ]
    
    for col in numeric_columns:
        if col in df.columns:
            def safe_numeric_convert(val):
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
            
            original_count = df[col].notna().sum()
            df[col] = df[col].apply(safe_numeric_convert)
            converted_count = df[col].notna().sum()
            logger.info(f"    {col}: {original_count} -> {converted_count} valid numbers")
    
    # Handle nulls and convert types for remaining columns
    for col in df.columns:
        if col not in date_columns and col not in numeric_columns and col not in json_metadata_columns:
            def safe_string_convert(val):
                if pd.isna(val) or val is None:
                    return None
                try:
                    str_val = str(val).strip()
                    if str_val in ['None', 'nan', 'null', '']:
                        return None
                    return str_val
                except:
                    return None
            
            df[col] = df[col].apply(safe_string_convert)
    
    logger.info(f"Data prepared: {len(df)} rows ready for insert")
    return df

# ========================================================================
# DYNAMIC SCHEMA HANDLING: Auto-adapt to Monday.com board changes
# ========================================================================

def get_monday_column_info(items):
    """Extract column information from Monday.com board items"""
    column_info = {}
    
    if not items:
        return column_info
    
    # Analyze first few items to get column metadata
    sample_size = min(10, len(items))
    for item in items[:sample_size]:
        for cv in item["column_values"]:
            col_title = cv["column"]["title"]
            col_type = cv["column"]["type"]
            col_id = cv["column"]["id"]
            
            if col_title not in column_info:
                column_info[col_title] = {
                    'monday_type': col_type,
                    'monday_id': col_id,
                    'sql_type': map_monday_type_to_sql(col_type),
                    'sample_values': []
                }
            
            # Collect sample values for type inference
            value = extract_value(cv)
            if value is not None and len(column_info[col_title]['sample_values']) < 5:
                column_info[col_title]['sample_values'].append(value)
    
    return column_info

def map_monday_type_to_sql(monday_type):
    """Map Monday.com column types to SQL Server types"""
    type_mapping = {
        'text': 'NVARCHAR(255)',
        'long_text': 'NVARCHAR(MAX)',
        'numbers': 'FLOAT',
        'date': 'NVARCHAR(50)',  # Store as string for consistency
        'status': 'NVARCHAR(100)',
        'dropdown': 'NVARCHAR(100)',
        'people': 'NVARCHAR(255)',
        'item_id': 'BIGINT',
        'dependency': 'NVARCHAR(255)',
        'mirror': 'NVARCHAR(255)',
        'board_relation': 'NVARCHAR(255)',
        'formula': 'NVARCHAR(255)',
        'creation_log': 'NVARCHAR(255)',
        'last_updated': 'NVARCHAR(255)',
        'checkbox': 'BIT'
    }
    return type_mapping.get(monday_type, 'NVARCHAR(255)')

def get_table_schema(table_name, database_name):
    """Get current SQL table schema"""
    schema_query = f"""
    SELECT 
        COLUMN_NAME,
        DATA_TYPE,
        CHARACTER_MAXIMUM_LENGTH,
        IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'dbo' 
    AND TABLE_NAME = '{table_name}'
    ORDER BY ORDINAL_POSITION
    """
    
    try:
        result = db.run_query(schema_query, database_name)
        return {row['COLUMN_NAME']: row for _, row in result.iterrows()}
    except Exception as e:
        logger.warning(f"Could not get table schema for {table_name}: {e}")
        return {}

# ========================================================================
# HUMAN-IN-THE-LOOP SCHEMA APPROVAL PROCESS
# ========================================================================

def get_approved_columns():
    """Load approved/rejected column decisions from data mapping"""
    try:
        mapping_file = os.path.join(os.path.dirname(__file__), '..', '..', 'utils', 'data_mapping.yaml')
        with open(mapping_file, 'r', encoding='utf-8') as f:
            mapping_data = yaml.safe_load(f)
        
        # Get schema decisions for COO Planning board
        schema_decisions = mapping_data.get('monday_boards', {}).get('coo_planning', {}).get('schema_decisions', {})
        return schema_decisions.get('approved_columns', []), schema_decisions.get('rejected_columns', [])
    except Exception as e:
        logger.warning(f"Could not load schema decisions from data mapping: {e}")
        return [], []

def record_schema_decision(column_name, column_type, approved, reason=""):
    """Record schema approval/rejection decision in data mapping"""
    try:
        mapping_file = os.path.join(os.path.dirname(__file__), '..', '..', 'utils', 'data_mapping.yaml')
        
        # Load current mapping
        with open(mapping_file, 'r', encoding='utf-8') as f:
            mapping_data = yaml.safe_load(f)
        
        # Ensure structure exists
        if 'monday_boards' not in mapping_data:
            mapping_data['monday_boards'] = {}
        if 'coo_planning' not in mapping_data['monday_boards']:
            mapping_data['monday_boards']['coo_planning'] = {}
        if 'schema_decisions' not in mapping_data['monday_boards']['coo_planning']:
            mapping_data['monday_boards']['coo_planning']['schema_decisions'] = {
                'approved_columns': [],
                'rejected_columns': []
            }
        
        # Record decision
        decision_entry = {
            'name': column_name,
            'type': column_type,
            'decision_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'reason': reason
        }
        
        if approved:
            mapping_data['monday_boards']['coo_planning']['schema_decisions']['approved_columns'].append(decision_entry)
            logger.info(f"RECORDED APPROVAL: Column '{column_name}' approved for schema")
        else:
            mapping_data['monday_boards']['coo_planning']['schema_decisions']['rejected_columns'].append(decision_entry)
            logger.info(f"RECORDED REJECTION: Column '{column_name}' rejected from schema")
        
        # Update metadata
        mapping_data['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        
        # Save updated mapping
        with open(mapping_file, 'w', encoding='utf-8') as f:
            yaml.dump(mapping_data, f, default_flow_style=False, allow_unicode=True, indent=2)
        
        return True
    except Exception as e:
        logger.error(f"Failed to record schema decision: {e}")
        return False

def prompt_for_column_approval(column_name, column_type, sample_data=None):
    """Human-in-the-loop: Prompt user to approve new/complex columns"""
    
    # Complex types that require approval
    complex_types = ['board_relation', 'link', 'dependency', 'mirror', 'formula']
      # If it's not a complex type, auto-approve simple text/number columns
    if column_type not in complex_types:
        logger.info(f"AUTO-APPROVED: Simple column '{column_name}' (type: {column_type})")
        record_schema_decision(column_name, column_type, approved=True, reason="Auto-approved: simple type")
        return True
    
    # Check for auto-rejection of board_relation columns
    if column_type == 'board_relation' and AUTO_REJECT_BOARD_RELATIONS:
        logger.info(f"AUTO-REJECTED: board_relation column '{column_name}' (auto-rejection enabled)")
        record_schema_decision(column_name, column_type, approved=False, reason="Auto-rejected: board_relation type (configured)")
        return False
    
    # For complex types, require human approval
    logger.info("=" * 60)
    logger.info("HUMAN APPROVAL REQUIRED - NEW COMPLEX COLUMN DETECTED")
    logger.info("=" * 60)
    logger.info(f"Column Name: {column_name}")
    logger.info(f"Column Type: {column_type}")
    if sample_data:
        logger.info(f"Sample Data: {str(sample_data)[:100]}{'...' if len(str(sample_data)) > 100 else ''}")
    logger.info("")
    logger.info("Complex column types like 'board_relation' can contain large amounts of")
    logger.info("nested data and may not be suitable for direct SQL storage.")
    logger.info("")
    
    try:
        response = input(f"Do you want to add column '{column_name}' to the schema? (y/N): ").strip().lower()
        
        if response in ['y', 'yes']:
            reason = input("Reason for approval (optional): ").strip()
            record_schema_decision(column_name, column_type, approved=True, reason=reason)
            logger.info(f"APPROVED: Column '{column_name}' will be added to schema")
            return True
        else:
            reason = input("Reason for rejection (optional): ").strip() or "Complex type not suitable for SQL storage"
            record_schema_decision(column_name, column_type, approved=False, reason=reason)
            logger.info(f"REJECTED: Column '{column_name}' will NOT be added to schema")
            return False
    except KeyboardInterrupt:
        logger.info(f"INTERRUPTED: Auto-rejecting column '{column_name}'")
        record_schema_decision(column_name, column_type, approved=False, reason="Interrupted: defaulting to rejection")
        return False

# ========================================================================
# DYNAMIC SCHEMA MANAGEMENT 
# ========================================================================

def sync_table_schema(table_name, database_name, monday_columns, df_columns):
    """Synchronize SQL table schema with Monday.com board structure"""
    logger.info(f"Synchronizing schema for table {table_name}")
    
    try:
        # Load existing approval decisions
        approved_columns, rejected_columns = get_approved_columns()
        approved_names = [col['name'] for col in approved_columns]
        rejected_names = [col['name'] for col in rejected_columns]
        
        # Get current table schema
        current_schema = get_table_schema(table_name, database_name)
        current_columns = set(current_schema.keys())
        
        # Core columns that should always exist
        core_columns = {'StyleKey', 'UpdateDate', 'Group', 'Item ID'}
        
        # Columns from DataFrame (what we actually have from Monday.com)
        df_column_set = set(df_columns)
        
        # Find columns to add
        columns_to_add = df_column_set - current_columns
        
        # Remove core columns from the "to add" list (they should already exist)
        columns_to_add = columns_to_add - core_columns
        
        # Remove already rejected columns
        columns_to_add = columns_to_add - set(rejected_names)
        
        if columns_to_add:
            logger.info(f"Processing {len(columns_to_add)} potential new columns for {table_name}")
            
            for col_name in columns_to_add:
                # Check if already approved
                if col_name in approved_names:
                    logger.info(f"PREVIOUSLY APPROVED: {col_name}")
                    add_approved = True
                elif col_name in rejected_names:
                    logger.info(f"PREVIOUSLY REJECTED: {col_name} - skipping")
                    continue
                else:
                    # Get column info for approval process
                    col_info = monday_columns.get(col_name, {})
                    col_type = col_info.get('monday_type', 'unknown')
                    
                    # Prompt for approval
                    add_approved = prompt_for_column_approval(col_name, col_type)
                
                if add_approved:
                    # Determine SQL type for the new column
                    if col_name in monday_columns:
                        sql_type = monday_columns[col_name]['sql_type']
                    else:
                        # Default type for unknown columns
                        sql_type = 'NVARCHAR(255)'
                    
                    # Sanitize column name for SQL
                    safe_col_name = col_name.replace("'", "''")
                    
                    alter_sql = f"ALTER TABLE [dbo].[{table_name}] ADD [{safe_col_name}] {sql_type} NULL"
                    
                    try:
                        db.execute(alter_sql, database_name)
                        logger.info(f"   ADDED COLUMN: [{col_name}] {sql_type}")
                    except Exception as e:
                        logger.warning(f"   FAILED to add column [{col_name}]: {e}")
                else:
                    logger.info(f"   SKIPPED: [{col_name}] - not approved for schema")
        
        # Find columns that exist in SQL but not in Monday.com data
        missing_from_monday = current_columns - df_column_set - core_columns
        
        if missing_from_monday:
            logger.info(f"Note: {len(missing_from_monday)} columns exist in SQL but not in Monday.com data")
            logger.info(f"   These will be set to NULL: {list(missing_from_monday)[:5]}{'...' if len(missing_from_monday) > 5 else ''}")
        
        logger.info(f"Schema synchronization completed for {table_name}")
        return True
        
    except Exception as e:
        logger.error(f"Schema synchronization failed for {table_name}: {e}")
        logger.info("Continuing with existing schema...")
        return False

def handle_schema_changes(df, items):
    """Main function to handle schema changes between Monday.com and SQL tables"""
    logger.info("Checking for schema changes...")
    
    try:
        # Get Monday.com column information
        monday_columns = get_monday_column_info(items)
        df_columns = list(df.columns)
        
        logger.info(f"Monday.com board has {len(monday_columns)} columns")
        logger.info(f"DataFrame has {len(df_columns)} columns")
        
        # Sync both production and staging tables
        staging_table = f"stg_{TABLE_NAME}"
        
        # Sync production table first
        sync_table_schema(TABLE_NAME, DATABASE_NAME, monday_columns, df_columns)
        
        # Sync staging table
        sync_table_schema(staging_table, DATABASE_NAME, monday_columns, df_columns)
        
        logger.info("Schema change handling completed")
        return True
        
    except Exception as e:
        logger.error(f"Schema change handling failed: {e}")
        logger.info("Continuing with current schema...")
        return False

def filter_approved_columns(df):
    """Filter DataFrame to only include approved columns"""
    try:
        # Load existing approval decisions
        approved_columns, rejected_columns = get_approved_columns()
        rejected_names = [col['name'] for col in rejected_columns]
        
        if rejected_names:
            # Remove rejected columns from DataFrame
            original_cols = list(df.columns)
            cols_to_drop = [col for col in original_cols if col in rejected_names]
            
            if cols_to_drop:
                logger.info(f"Filtering out {len(cols_to_drop)} rejected columns: {cols_to_drop}")
                df = df.drop(columns=cols_to_drop)
                logger.info(f"DataFrame now has {len(df.columns)} columns (removed {len(cols_to_drop)})")
        
        return df
        
    except Exception as e:
        logger.warning(f"Could not filter rejected columns: {e}")
        return df

# ========================================================================
# ZERO-DOWNTIME STAGING OPERATIONS
# ========================================================================

def prepare_staging_table():
    """ZERO-DOWNTIME: Prepare staging table for atomic swap"""
    logger.info("PREPARING staging table for zero-downtime refresh...")
    
    staging_table = f"stg_{TABLE_NAME}"
    
    try:
        # Check if staging table exists, create if not
        staging_exists_query = f"""
        SELECT COUNT(*) as count 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = 'dbo' 
        AND TABLE_NAME = '{staging_table}'
        """
        result = db.run_query(staging_exists_query, DATABASE_NAME)
        staging_exists = result.iloc[0]['count'] > 0
        
        if not staging_exists:
            logger.info("Creating staging table...")
            create_staging_sql = f"""
            SELECT TOP 0 * 
            INTO [dbo].[{staging_table}] 
            FROM [dbo].[{TABLE_NAME}]
            """
            db.execute(create_staging_sql, DATABASE_NAME)
            logger.info("Staging table created")
        
        # Get current production record count for reference
        prod_count_result = db.run_query(f"SELECT COUNT(*) as count FROM dbo.{TABLE_NAME}", DATABASE_NAME)
        prod_count = prod_count_result.iloc[0]['count']
        logger.info(f"   Current production records: {prod_count}")
        
        # Truncate staging table for fresh load
        logger.info("Truncating staging table for fresh load")
        db.execute(f"TRUNCATE TABLE [dbo].[{staging_table}]", DATABASE_NAME)
        
        # Verify staging table is empty
        staging_count_result = db.run_query(f"SELECT COUNT(*) as count FROM dbo.{staging_table}", DATABASE_NAME)
        staging_count = staging_count_result.iloc[0]['count']
        
        logger.info(f"   Staging table prepared: {staging_count} records (empty and ready)")
        
    except Exception as e:
        logger.error(f"   Staging table preparation failed: {e}")
        raise

def load_to_staging_table(df):
    """Load data to staging table using zero-downtime approach"""
    if df is None or df.empty:
        logger.warning("No data to load")
        return
    
    staging_table = f"stg_{TABLE_NAME}"
    
    try:
        logger.info(f"Loading {len(df)} rows into staging table {DATABASE_NAME}.dbo.{staging_table}")
        
        # Get valid table columns
        columns_query = f"""
        SELECT name FROM sys.columns 
        WHERE object_id = OBJECT_ID('dbo.{staging_table}')
        """
        columns_df = db.run_query(columns_query, DATABASE_NAME)
        valid_cols = set(columns_df['name'].tolist())
          # Filter DataFrame to only include valid columns
        df = df[[c for c in df.columns if c in valid_cols]]
        
        if len(df.columns) == 0:
            raise ValueError("No valid columns found for insert")
        
        logger.info(f"Inserting {len(df.columns)} columns: {', '.join(df.columns[:5])}{'...' if len(df.columns) > 5 else ''}")
        
        # Use production-proven db_helper pattern: raw connection + executemany
        conn = db.get_connection(DATABASE_NAME)
        cursor = conn.cursor()
        
        try:
            # Build insert statement
            columns = list(df.columns)
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join([f'[{col}]' for col in columns])
            insert_sql = f"INSERT INTO dbo.{staging_table} ({column_names}) VALUES ({placeholders})"
            
            # Prepare all rows for bulk insert
            values_list = []
            for _, row in df.iterrows():
                values = []
                for val in row.values:
                    if pd.isna(val) or val is None:
                        values.append(None)
                    elif hasattr(val, 'dtype'):
                        # Handle numpy types with NaN check
                        if pd.isna(val):
                            values.append(None)
                        elif 'int' in str(val.dtype):
                            values.append(int(val))
                        elif 'float' in str(val.dtype):
                            values.append(float(val))
                        else:
                            values.append(val)
                    else:
                        values.append(val)
                values_list.append(values)
            
            # Use executemany for bulk insert (production pattern)
            logger.info(f"Executing bulk insert of {len(values_list)} rows...")
            cursor.executemany(insert_sql, values_list)
            conn.commit()
            
        finally:
            cursor.close()
            conn.close()
        
        # Validate staging data
        staging_count_result = db.run_query(f"SELECT COUNT(*) as count FROM [dbo].[{staging_table}]", DATABASE_NAME)
        staging_count = staging_count_result.iloc[0]['count']
        
        if staging_count != len(df):
            raise Exception(f"Data validation failed: expected {len(df)}, got {staging_count} in staging table")
        
        logger.info(f"Staging data validated: {staging_count} records loaded")
        
    except Exception as e:
        logger.error(f"Error during staging data load: {e}")
        raise

def atomic_swap_tables():
    """ZERO-DOWNTIME: Atomically swap staging table to production with minimal downtime"""
    logger.info("ATOMIC SWAP: Replacing production table with staging data...")
    
    staging_table = f"stg_{TABLE_NAME}"
    
    try:
        # Get record counts for validation
        staging_count_result = db.run_query(f"SELECT COUNT(*) as count FROM dbo.{staging_table}", DATABASE_NAME)
        staging_count = staging_count_result.iloc[0]['count']
        
        prod_count_result = db.run_query(f"SELECT COUNT(*) as count FROM dbo.{TABLE_NAME}", DATABASE_NAME)
        old_prod_count = prod_count_result.iloc[0]['count']
        
        logger.info(f"   Staging table: {staging_count} records")
        logger.info(f"   Production table (current): {old_prod_count} records")
        
        if staging_count == 0:
            raise Exception("Staging table is empty - cannot perform swap")
        
        # Perform atomic swap operation
        logger.info("   Executing atomic table swap...")
        swap_sql = f"""
        BEGIN TRANSACTION
        
        -- Drop production table
        DROP TABLE [dbo].[{TABLE_NAME}]
        
        -- Rename staging to production
        EXEC sp_rename 'dbo.{staging_table}', '{TABLE_NAME}'
        
        -- Create new empty staging table for next run
        SELECT TOP 0 * 
        INTO [dbo].[{staging_table}] 
        FROM [dbo].[{TABLE_NAME}]
        
        COMMIT TRANSACTION
        """
        
        db.execute(swap_sql, DATABASE_NAME)
        
        # Verify the swap
        new_prod_count_result = db.run_query(f"SELECT COUNT(*) as count FROM dbo.{TABLE_NAME}", DATABASE_NAME)
        new_prod_count = new_prod_count_result.iloc[0]['count']
        
        new_staging_count_result = db.run_query(f"SELECT COUNT(*) as count FROM dbo.{staging_table}", DATABASE_NAME)
        new_staging_count = new_staging_count_result.iloc[0]['count']
        
        logger.info(f"   Swap completed!")
        logger.info(f"   Production table (new): {new_prod_count} records")
        logger.info(f"   Staging table (new): {new_staging_count} records (empty)")
        logger.info(f"   Data refreshed: {old_prod_count} -> {new_prod_count} records")
        
        return new_prod_count
        
    except Exception as e:
        logger.error(f"   Atomic swap failed: {e}")
        logger.info("   Production table remains unchanged - no data loss")
        raise

async def main():
    """Main HYBRID ETL function with zero-downtime staging table approach"""
    logger.info("=== HYBRID Monday.com to Database ETL with ZERO-DOWNTIME REFRESH ===")
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Board ID: {BOARD_ID}")
    logger.info(f"Target: {DATABASE_NAME}.dbo.{TABLE_NAME}")
    
    try:
        # Step 1: Prepare staging table for zero-downtime refresh
        prepare_staging_table()
        
        # Step 2: Fetch data from Monday.com with pagination (production approach)
        items, board_name = fetch_board_data_with_pagination()
        
        if not items:
            logger.info("No items found in board")
            return
          # Step 3: Process items (production approach)
        df = process_items(items)
        
        # Step 4: Prepare for database (production approach)
        df = prepare_for_database(df)

        # ─── DUPLICATE AN EXISTING COLUMN ────────────────────────────────────────
        # e.g. clone the 'Longson RM EX-FTY' column to a new column called 'ProductCode'
        if 'Longson RM EX-FTY' in df.columns:
            df['PC RM Ex-Factory Date'] = df['Longson RM EX-FTY']
        # ──────────────────────────────────────────────────────────────────────────
        
        # Step 4.5: Handle schema changes (NEW - Dynamic schema adaptation)
        handle_schema_changes(df, items)
        
        # Step 4.6: Filter out rejected columns based on HITL decisions
        df = filter_approved_columns(df)
        
        # Step 5: Load data into STAGING table (zero-downtime approach)
        logger.info("Loading data into staging table (production remains available)...")
        load_to_staging_table(df)
        
        # Step 6: Atomic swap staging -> production (minimal downtime)
        final_count = atomic_swap_tables()
        
        logger.info(f"\nZERO-DOWNTIME ETL completed for board '{board_name}'")
        logger.info(f"Total processed: {len(df)} items")
        logger.info(f"Production records: {final_count}")
        logger.info(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("HYBRID APPROACH: SUCCESS")
        
    except Exception as e:
        logger.error(f"HYBRID ETL process failed: {e}")
        logger.info("Production data remains unchanged - zero data loss")
        raise

if __name__ == "__main__":
    asyncio.run(main())
