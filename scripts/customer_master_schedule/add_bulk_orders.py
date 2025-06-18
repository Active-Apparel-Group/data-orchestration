"""
Order Sync - Monday.com Integration
Single file, no nonsense, gets the job done.

Workflow:
1. Get pending orders from MON_CustMasterSchedule (staging IDs 1000+)
2. Create Monday.com items with proper names and column data
3. Update staging records with Monday.com item IDs

That's it.
"""

import os
import sys
import json
import pandas as pd
import pyodbc
import requests
import math
import yaml
from datetime import datetime
import urllib3
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

# Load configuration from centralized config
config = db.load_config()

# Import centralized mapping system
import mapping_helper as mapping

# Import the complete mapping transformation system
from order_mapping import (
    transform_orders_batch,
    create_staging_dataframe,
    get_monday_column_values_dict,
    transform_order_data,
    load_mapping_config,
    load_customer_mapping
)

# Suppress SSL warnings for corporate networks
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ++++  add right here  ++++
def safe_json(column_values: dict) -> str:
    """
    Drop None / '' / NaN / pd.NA and return a JSON string Monday accepts.
    """
    cleaned = {}
    for k, v in column_values.items():
        if v is None:
            continue
        if isinstance(v, float) and math.isnan(v):
            continue
        if pd.isna(v):
            continue
        if isinstance(v, str) and not v.strip():
            continue
        cleaned[k] = v

    return json.dumps(cleaned, ensure_ascii=False, allow_nan=False)
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# Universal Mapping Functions - Reusable across all pipelines
def load_mapping_dataframe():
    """Load YAML mapping configuration into a reusable DataFrame
    
    Returns:
        DataFrame with columns: source_field, target_field, target_column_id, target_type, transformation
    """
    mapping_config = load_mapping_config()
    customer_lookup = load_customer_mapping()
    
    if not mapping_config:
        return pd.DataFrame()
    
    mappings = []
    
    # Process exact matches
    for mapping in mapping_config.get('exact_matches', []):
        mappings.append({
            'source_field': mapping['source_field'],
            'target_field': mapping['target_field'],
            'target_column_id': mapping['target_column_id'],
            'target_type': mapping['target_type'],
            'transformation': mapping.get('transformation', 'direct_mapping'),
            'mapping_rules': mapping.get('mapping_rules', [])
        })
    
    # Process mapped fields
    for mapping in mapping_config.get('mapped_fields', []):
        mappings.append({
            'source_field': mapping['source_field'],
            'target_field': mapping['target_field'],
            'target_column_id': mapping['target_column_id'],
            'target_type': mapping['target_type'],
            'transformation': mapping.get('transformation', 'direct_mapping'),
            'mapping_rules': mapping.get('mapping_rules', [])
        })
    
    # Process computed fields
    for mapping in mapping_config.get('computed_fields', []):
        mappings.append({
            'source_field': '+'.join(mapping['source_fields']),  # Concatenated source fields
            'target_field': mapping['target_field'],
            'target_column_id': mapping.get('target_column_id'),
            'target_type': mapping.get('target_type', 'text'),
            'transformation': mapping['transformation'],
            'source_fields': mapping['source_fields']  # Keep original for computed fields
        })
    
    df = pd.DataFrame(mappings)
    print(f"✅ Loaded mapping dataframe with {len(df)} mappings")
    return df, customer_lookup

def map_to_monday_values(data_row, mapping_df, customer_lookup):
    """Universal function to map any data row to Monday.com column values
    
    Args:
        data_row: pandas Series with source data (from any table)
        mapping_df: DataFrame with mapping configuration
        customer_lookup: Customer mapping dictionary
        
    Returns:
        Dictionary ready for format_monday_column_values()
    """
    transformed_data = {}
    
    for _, mapping in mapping_df.iterrows():
        source_field = mapping['source_field']
        target_field = mapping['target_field']
        target_column_id = mapping['target_column_id']
        target_type = mapping['target_type']
        transformation = mapping['transformation']
        
        # Skip if no column ID
        if pd.isna(target_column_id) or not target_column_id:
            continue
        
        # Handle computed fields
        if transformation == 'concatenation' and 'source_fields' in mapping:
            values = []
            for field in mapping['source_fields']:
                value = data_row.get(field, '')
                if value and str(value).strip():
                    values.append(str(value).strip())
            computed_value = ' '.join(values) if values else ""
            
        elif transformation == 'sum_aggregation' and 'source_fields' in mapping:
            total = 0
            for field in mapping['source_fields']:
                value = data_row.get(field, 0)
                try:
                    total += float(value) if value else 0
                except (ValueError, TypeError):
                    continue
            computed_value = total
            
        else:
            # Regular field mapping
            source_value = data_row.get(source_field)
            
            # Apply transformations
            if transformation == 'customer_mapping_lookup':
                from customer_master_schedule.order_mapping import apply_customer_mapping
                computed_value = apply_customer_mapping(source_value, customer_lookup)
            elif transformation == 'value_mapping':
                computed_value = source_value
                mapping_rules = mapping.get('mapping_rules', [])
                for rule in mapping_rules:
                    if str(source_value).upper() == str(rule['source_value']).upper():
                        computed_value = rule['target_value']
                        break
            else:
                computed_value = source_value
        
        # Store in the format expected by format_monday_column_values
        transformed_data[target_field] = {
            'value': computed_value,
            'column_id': target_column_id,
            'type': target_type,
            'source_field': source_field
        }
    
    return transformed_data

# Configuration
MONDAY_API_URL = "https://api.monday.com/v2"
MONDAY_API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjE5NzM0MzUxMiwiYWFpIjoxMSwidWlkIjozMTk3MDg4OSwiaWFkIjoiMjAyMi0xMS0yMVQwNTo1MTowNi4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MTI3NDEyODgsInJnbiI6InVzZTEifQ.K2zXiugzNiYW5xo0tuXpAuZexBdv5xaAXPxubwxhNAM"
# Use centralized mapping system for board configuration
BOARD_ID = mapping.get_board_config('customer_master_schedule')['board_id']

# Database connection
def get_db_connection():
    """Get database connection using environment variables"""
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
        load_dotenv(dotenv_path=env_path)
    except:
        pass
    
    import base64
    password = os.getenv('SECRET_ORDERS_PWD')
    if password:
        try:
            password = base64.b64decode(password).decode()
        except:
            pass
    else:
        password = os.getenv('DB_ORDERS_PASSWORD')
    
    host = os.getenv('DB_ORDERS_HOST')
    port = int(os.getenv('DB_ORDERS_PORT', 1433))
    database = os.getenv('DB_ORDERS_DATABASE')
    username = os.getenv('DB_ORDERS_USERNAME')
    
    # Use working driver detection from order_queries.py
    driver = "{ODBC Driver 17 for SQL Server}"
    try:
        test_conn_str = f"DRIVER={driver};SERVER=test;DATABASE=test;"
        pyodbc.connect(test_conn_str, timeout=1)
    except:
        driver = "{SQL Server}"
    
    conn_str = (
        f"DRIVER={driver};"
        f"SERVER={host},{port};"
        f"DATABASE={database};"
        f"UID={username};PWD={password};"
        "Encrypt=no;TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)

# Database operations
def get_new_orders_from_unified():
    """Get new orders from ORDERS_UNIFIED not yet in MON_CustMasterSchedule"""
    query = """
    SELECT ou.*
    FROM [dbo].[ORDERS_UNIFIED] ou
    LEFT JOIN [dbo].[MON_CustMasterSchedule] cms 
        ON ou.[AAG ORDER NUMBER] = cms.[AAG ORDER NUMBER]
        AND ou.[CUSTOMER STYLE] = cms.[STYLE] 
        AND ou.[CUSTOMER COLOUR DESCRIPTION] = cms.[COLOR]
    WHERE cms.[AAG ORDER NUMBER] IS NULL
        AND LEFT(ou.[CUSTOMER NAME], 3) <> 'LOR'
        AND LEFT(ou.[CUSTOMER NAME], 3) = 'MAC'
        AND ou.[AAG ORDER NUMBER] IS NOT NULL
        AND ou.[CUSTOMER STYLE] IS NOT NULL
        AND ou.[CUSTOMER COLOUR DESCRIPTION] IS NOT NULL
    ORDER BY ou.[ORDER DATE PO RECEIVED] DESC
    """
    
    conn = get_db_connection()
    try:
        df = pd.read_sql(query, conn)
        print(f"Found {len(df)} new orders from ORDERS_UNIFIED")
        return df
    finally:
        conn.close()

def insert_to_staging(orders_df):
    """Insert new orders to MON_CustMasterSchedule using complete YAML mapping"""
    if orders_df.empty:
        return True
    
    # Transform orders using complete YAML mapping (51 fields)
    print("Transforming orders using YAML mapping...")
    transformed_df = transform_orders_batch(orders_df)
    
    if transformed_df.empty:
        print("No orders successfully transformed")
        return False
    
    conn = get_db_connection()
    try:
        # Get next staging ID
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ISNULL(MAX(TRY_CAST([Item ID] AS BIGINT)), 999) 
            FROM [dbo].[MON_CustMasterSchedule] 
            WHERE [Item ID] IS NOT NULL 
            AND ISNUMERIC([Item ID]) = 1 
            AND TRY_CAST([Item ID] AS BIGINT) >= 1000 
            AND TRY_CAST([Item ID] AS BIGINT) < 10000
        """)
        next_id = cursor.fetchone()[0] + 1
        
        # Add staging IDs to transformed data
        staging_ids = list(range(next_id, next_id + len(transformed_df)))
        transformed_df['Item ID'] = staging_ids
        
        print(f"Assigned staging IDs: {min(staging_ids)} to {max(staging_ids)}")
        
        # Use dynamic insert with all transformed columns (like order_queries.py)
        columns = list(transformed_df.columns)
        placeholders = ', '.join(['?' for _ in columns])
        column_names = ', '.join([f'[{col}]' for col in columns])
        
        insert_query = f"""
            INSERT INTO [dbo].[MON_CustMasterSchedule] ({column_names})
            VALUES ({placeholders})
        """
          # Insert each row with all mapped columns - handle NULL values for SQL Server
        rows_inserted = 0
        for _, row in transformed_df.iterrows():
            values = []
            for col in columns:
                value = row[col]
                # Convert empty strings to None for SQL Server compatibility
                if value == "" or (isinstance(value, str) and value.strip() == ""):
                    values.append(None)
                elif pd.isna(value):
                    values.append(None)
                else:
                    values.append(value)
            cursor.execute(insert_query, values)
            rows_inserted += 1
        
        conn.commit()
        print(f"Inserted {rows_inserted} orders with {len(columns)} columns each (IDs {next_id}-{next_id + len(transformed_df) - 1})")
        return True
        
    except Exception as e:
        print(f"Error inserting to staging: {e}")
        return False
    finally:
        conn.close()

def get_pending_orders():
    """Get orders with staging IDs that need Monday.com sync"""
    query = """
    SELECT *
    FROM [dbo].[MON_CustMasterSchedule]
    WHERE [Item ID] IS NOT NULL 
        AND ISNUMERIC([Item ID]) = 1 
        AND TRY_CAST([Item ID] AS BIGINT) >= 1000 
        AND TRY_CAST([Item ID] AS BIGINT) < 10000
    ORDER BY TRY_CAST([Item ID] AS BIGINT) ASC
    """
    
    conn = get_db_connection()
    try:
        df = pd.read_sql(query, conn)
        print(f"Found {len(df)} orders pending sync")
        return df
    finally:
        conn.close()

def update_staging_record(staging_id, monday_item_id):
    """Update staging record with Monday.com item ID"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE [dbo].[MON_CustMasterSchedule] SET [Item ID] = ? WHERE [Item ID] = ?",
            (monday_item_id, staging_id)
        )
        rows_affected = cursor.rowcount
        conn.commit()
        return rows_affected > 0
    finally:
        conn.close()

# Monday.com operations
def monday_api_call(query):
    """Make Monday.com API call"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MONDAY_API_KEY}"
    }
    
    response = requests.post(MONDAY_API_URL, headers=headers, json={'query': query}, verify=False)
    
    if response.status_code != 200:
        raise Exception(f"API call failed: {response.status_code} - {response.text}")
    
    result = response.json()
    if 'errors' in result:
        raise Exception(f"API errors: {result['errors']}")
    
    return result

def ensure_group_exists(group_name):
    """Ensure group exists on board, create if needed"""
    # Get board info
    query = f"""
    query {{
        boards(ids: [{BOARD_ID}]) {{
            groups {{
                id
                title
            }}
        }}
    }}
    """
    
    result = monday_api_call(query)
    groups = result['data']['boards'][0]['groups']
    
    # Check if group exists
    for group in groups:
        if group['title'] == group_name:
            return group['id']
    
    # Create new group
    query = f"""
    mutation {{
        create_group(
            board_id: {BOARD_ID},
            group_name: "{group_name}"
        ) {{
            id
        }}
    }}
    """
    
    result = monday_api_call(query)
    return result['data']['create_group']['id']

def create_monday_item(item_name, group_id, column_values_dict=None):
    """Create item on Monday.com board"""
    # Sanitize item name - remove problematic characters
    sanitized_name = item_name.replace('"', '\\"').replace('\n', ' ').replace('\r', ' ').strip()
    
    # Handle column values - convert dict to JSON and escape for GraphQL
    if column_values_dict is None:
        column_values_dict = {}
    
    column_values_json = safe_json(column_values_dict)
    escaped_column_values = column_values_json.replace('\\', '\\\\').replace('"', '\\"')
    
    # Build mutation with properly escaped JSON string
    mutation = f"""
    mutation {{
        create_item(
            board_id: {BOARD_ID},
            group_id: "{group_id}",
            item_name: "{sanitized_name}",
            column_values: "{escaped_column_values}",
            create_labels_if_missing: true
        ) {{
            id
        }}
    }}
    """
    result = monday_api_call(mutation)
    return result['data']['create_item']['id']

# Data transformation
def create_item_name(order_row):
    """Create Monday.com item name: STYLE COLOR ORDER_NUMBER"""
    # Use the Title field from YAML mapping if available, otherwise fallback to manual construction
    title = order_row.get('Title', '')
    if title:
        return str(title).strip()
    
    # Fallback: manual construction
    style = str(order_row.get('Style', order_row.get('CUSTOMER STYLE', ''))).strip()
    color = str(order_row.get('Color', order_row.get('CUSTOMER COLOUR DESCRIPTION', ''))).strip()
    order_number = str(order_row.get('Order_Number', order_row.get('AAG ORDER NUMBER', ''))).strip()
    
    return f"{style} {color} {order_number}".strip()

def create_group_name(order_row):
    """Create group name: CUSTOMER SEASON"""
    customer = str(order_row.get('Customer', order_row.get('CUSTOMER', order_row.get('CUSTOMER NAME', '')))).strip()
    season = str(order_row.get('Season', order_row.get('CUSTOMER SEASON', ''))).strip()
    
    return f"{customer} {season}".strip()

def get_monday_column_values_for_order(order_row):
    """Get properly formatted Monday.com column values for an order using YAML mapping"""
    try:
        # Load configurations
        mapping_config = load_mapping_config()
        customer_lookup = load_customer_mapping()
        
        if not mapping_config:
            print(f"Warning: No mapping config available for order {order_row.get('AAG ORDER NUMBER', 'Unknown')}")
            return {}
        
        # Transform the order data to get proper column mappings
        transformed = transform_order_data(order_row, mapping_config, customer_lookup)
        
        # Get properly formatted Monday.com column values using column IDs
        column_values = get_monday_column_values_dict(transformed)
        
        return column_values
        
    except Exception as e:
        print(f"Error getting Monday.com column values for order {order_row.get('AAG ORDER NUMBER', 'Unknown')}: {e}")
        return {}

def get_monday_column_values_for_staged_order(order_row):
    """Get properly formatted Monday.com column values for staged order data (already transformed)
    
    This function maps already-transformed staging data directly to Monday.com column IDs
    without running the YAML transformation again.
    """
    try:
        # Load mapping configuration to get column IDs
        mapping_config = load_mapping_config()
        
        if not mapping_config:
            print(f"Warning: No mapping config available for staged order {order_row.get('AAG ORDER NUMBER', 'Unknown')}")
            return {}
        
        # Build column values dictionary by mapping staged column names to Monday.com column IDs
        column_values = {}
        
        # Create a lookup of target_field -> column_id from YAML mapping
        field_to_column_id = {}
        
        # Process exact matches
        for mapping in mapping_config.get('exact_matches', []):
            target_field = mapping['target_field']
            target_column_id = mapping['target_column_id']
            target_type = mapping['target_type']
            field_to_column_id[target_field] = {
                'column_id': target_column_id,
                'type': target_type
            }
        
        # Process mapped fields
        for mapping in mapping_config.get('mapped_fields', []):
            target_field = mapping['target_field']
            target_column_id = mapping['target_column_id']
            target_type = mapping['target_type']
            field_to_column_id[target_field] = {
                'column_id': target_column_id,
                'type': target_type
            }
        
        # Map staged data to Monday.com column IDs
        for field_name, mapping_info in field_to_column_id.items():
            column_id = mapping_info['column_id']
            field_type = mapping_info['type']
            
            # Get value from staged data (use the target field name)
            value = order_row.get(field_name)
            
            # Skip if no value or empty
            if value is None or (isinstance(value, str) and not value.strip()):
                continue
            
            # Format based on Monday.com column type requirements
            if field_type == 'text' or field_type == 'long_text':
                column_values[column_id] = str(value).strip()
            
            elif field_type == 'numbers':
                # Ensure numeric values are passed as numbers, not strings
                try:
                    if isinstance(value, str):
                        # Handle empty strings and convert to float
                        numeric_value = float(value) if value.strip() else 0
                    else:
                        numeric_value = float(value) if value is not None else 0
                    column_values[column_id] = numeric_value
                except (ValueError, TypeError):
                    column_values[column_id] = 0
            
            elif field_type == 'date':
                # CRITICAL: Dates must be YYYY-MM-DD format
                if value:
                    # Handle both string and date objects
                    if hasattr(value, 'strftime'):
                        date_str = value.strftime('%Y-%m-%d')
                    else:
                        date_str = str(value)[:10]  # Take first 10 chars (YYYY-MM-DD)
                    column_values[column_id] = {"date": date_str, "icon": ""}
            
            elif field_type == 'dropdown' or field_type == 'status':
                # For dropdowns and status, pass the text value
                # Monday.com API with create_labels_if_missing=true will handle it
                column_values[column_id] = str(value).strip()
            
            else:
                column_values[column_id] = str(value).strip()
        
        return column_values
        
    except Exception as e:
        print(f"Error getting Monday.com column values for staged order {order_row.get('AAG ORDER NUMBER', 'Unknown')}: {e}")
        return {}

# Database setup functions
def create_failed_api_calls_table():
    """Create table to store failed API calls for review"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Failed_API_Calls' AND xtype='U')
            CREATE TABLE Failed_API_Calls (
                id INT IDENTITY(1,1) PRIMARY KEY,
                staging_id NVARCHAR(50),
                order_number NVARCHAR(100),
                item_name NVARCHAR(500),
                group_name NVARCHAR(200),
                api_payload NVARCHAR(MAX),
                error_message NVARCHAR(MAX),
                error_type NVARCHAR(100),
                created_date DATETIME DEFAULT GETDATE()
            )
        """)
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creating failed_api_calls table: {e}")
        return False
    finally:
        conn.close()

def log_failed_api_call(staging_id, order_number, item_name, group_name, api_payload, error_message, error_type):
    """Log failed API call to database for review"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Failed_API_Calls 
            (staging_id, order_number, item_name, group_name, api_payload, error_message, error_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (staging_id, order_number, item_name, group_name, api_payload, error_message, error_type))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error logging failed API call: {e}")
        return False
    finally:
        conn.close()

# Main workflow
def process_new_orders():
    """Step 1: Find new orders and add to staging"""
    print("Step 1: Finding new orders from ORDERS_UNIFIED...")
    new_orders_df = get_new_orders_from_unified()
    
    if new_orders_df.empty:
        print("No new orders found")
        return 0
    
    print("Step 2: Adding to MON_CustMasterSchedule staging...")
    if insert_to_staging(new_orders_df):
        return len(new_orders_df)
    else:
        return 0

def sync_orders():
    """Main sync workflow"""
    # Load universal mapping dataframe once for the entire job
    print("🔄 Loading universal mapping configuration...")
    mapping_df, customer_lookup = load_mapping_dataframe()
    
    if mapping_df.empty:
        print("❌ Failed to load mapping configuration. Exiting.")
        return
    
    # Step 1: Process new orders from ORDERS_UNIFIED
    new_orders_count = process_new_orders()    
    # Step 2: Sync pending orders to Monday.com
    print("Step 3: Syncing pending orders to Monday.com...")
    orders_df = get_pending_orders()
    
    if orders_df.empty:
        print("No orders to sync")
        if new_orders_count > 0:
            print(f"Added {new_orders_count} new orders to staging")
        return
    
    success_count = 0
    error_count = 0
    
    # Ensure failed API calls table exists
    create_failed_api_calls_table()
    
    for _, order_row in orders_df.iterrows():
        staging_id = str(order_row['Item ID'])
        order_number = order_row.get('AAG ORDER NUMBER', order_row.get('Order_Number', 'Unknown'))
        
        try:
            # Create item name and group name
            item_name = create_item_name(order_row)
            group_name = create_group_name(order_row)
              # Universal mapping - works for any source data
            try:
                # transformed_data   = map_to_monday_values(order_row, mapping_df, customer_lookup)
                column_values_dict = get_monday_column_values_for_staged_order(order_row)
            except Exception as json_error:
                print(f"Column values error for order {order_number}: {json_error}")
                # Log this error and continue with empty column values
                log_failed_api_call(
                    staging_id, order_number, item_name, group_name, 
                    str(order_row.to_dict()), str(json_error), "COLUMN_VALUES_ERROR"
                )
                column_values_json = "{}"
            
            # Ensure group exists
            group_id = ensure_group_exists(group_name)
            
            # Prepare API payload for logging (in case of failure)
            api_payload = {
                "item_name": item_name,
                "group_id": group_id,
                "column_values_dict": column_values_dict,
                "board_id": BOARD_ID
            }

            monday_item_id = create_monday_item(item_name, group_id, column_values_dict)
            
            # Update database
            if update_staging_record(staging_id, monday_item_id):
                print(f"Success: {staging_id} -> {monday_item_id} ({item_name})")
                success_count += 1
            else:
                print(f"Failed to update database for staging ID {staging_id}")
                error_count += 1
                
        except Exception as e:
            error_message = str(e)
            print(f"Error syncing order {order_number}: {error_message}")
            
            # Determine error type based on error message
            if "parsing error" in error_message.lower():
                error_type = "GRAPHQL_PARSING_ERROR"
            elif "dropdown label" in error_message.lower():
                error_type = "DROPDOWN_LABEL_ERROR"
            elif "columnvalueexception" in error_message.lower():
                error_type = "COLUMN_VALUE_ERROR"
            else:
                error_type = "GENERAL_API_ERROR"
            
            # Log the failed API call
            try:
                api_payload_str = json.dumps(api_payload, default=str) if 'api_payload' in locals() else "N/A"
            except:
                api_payload_str = str(locals().get('api_payload', 'N/A'))
            
            log_failed_api_call(
                staging_id, order_number, 
                locals().get('item_name', 'N/A'), 
                locals().get('group_name', 'N/A'),
                api_payload_str, error_message, error_type
            )
            
            error_count += 1
    
    print(f"\nSummary: {success_count} success, {error_count} errors")

def test_connection():
    """Test database and API connections"""
    print("Testing database connection...")
    try:
        conn = get_db_connection()
        conn.close()
        print("Database: OK")
    except Exception as e:
        print(f"Database: FAILED - {e}")
        return False
    
    print("Testing Monday.com API...")
    try:
        query = "query { me { name } }"
        result = monday_api_call(query)
        print("Monday.com API: OK")
    except Exception as e:
        print(f"Monday.com API: FAILED - {e}")
        return False
    
    return True

def main():
    """Main entry point"""
    print("=" * 50)
    print("Order Sync - Monday.com Integration")
    print("=" * 50)
    
    # Test connections first
    if not test_connection():
        print("Connection test failed. Exiting.")
        return 1
    
    # Run sync
    try:
        sync_orders()
        print("Sync completed successfully")
        return 0
    except Exception as e:
        print(f"Sync failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
