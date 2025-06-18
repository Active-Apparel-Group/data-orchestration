#!/usr/bin/env python3
"""
Planning Board Extraction Script
Generated on: 2025-06-18 09:39:44
Board ID: 8709134353
Target Table: orders.planning

This script uses simple type-based extraction from centralized mappings.
"""

import os
import sys
import json
import logging
import requests
import pandas as pd
from datetime import datetime, timezone
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
# import mapping_helper as mapping

# Configuration - Monday.com API settings
MONDAY_TOKEN = os.getenv('MONDAY_API_KEY') or config.get('apis', {}).get('monday', {}).get('api_token')
API_VER = "2025-04"
API_URL = config.get('apis', {}).get('monday', {}).get('api_url', "https://api.monday.com/v2")

if not MONDAY_TOKEN or MONDAY_TOKEN == "YOUR_MONDAY_API_TOKEN_HERE":
    raise ValueError("Monday.com API token not configured. Please set MONDAY_API_KEY environment variable or update utils/config.yaml")

HEADERS = {
    "Authorization": f"Bearer {MONDAY_TOKEN}",
    "API-Version": API_VER,
    "Content-Type": "application/json"
}

# Configure logging
log_handlers = [logging.StreamHandler()]
log_file_path = os.getenv('LOG_FILE_PATH', 'monday_integration.log')

# Try to create the log file handler, fallback to console only if it fails
try:
    log_handlers.append(logging.FileHandler(log_file_path))
except (OSError, IOError):
    # If log file can't be created (e.g., directory doesn't exist), just use console
    pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)
logger = logging.getLogger(__name__)

# Board configuration
BOARD_ID = 8709134353
BOARD_NAME = "Planning"
TARGET_DATABASE = "orders"
TARGET_TABLE = "planning"

def extract_column_value(column_data):
    """Extract value from Monday.com column data using simple type-based logic"""
    if not column_data:
        return None
    
    col_type = column_data.get('type', 'text')
    value = column_data.get('value')
    text = column_data.get('text')
    
    if col_type == 'text' or col_type == 'long_text':
        return text or str(value) if value else None
    elif col_type == 'numbers':
        if isinstance(value, (int, float)):
            return int(value)
        elif text and text.strip():
            try:
                return int(float(text.strip()))
            except:
                return None
        return None
    elif col_type == 'date':
        # Handle Monday date format
        if isinstance(value, dict) and value.get('date'):
            try:
                return datetime.strptime(value['date'], '%Y-%m-%d').date()
            except:
                return None
        elif text and text.strip():
            try:
                return datetime.strptime(text.strip(), '%Y-%m-%d').date()
            except:
                return None
        return None
    elif col_type in ['status', 'dropdown']:
        return text or str(value) if value else None
    elif col_type == 'checkbox':
        if isinstance(value, dict):
            return value.get('checked') == 'true'
        return bool(value) if value else False
    elif col_type == 'people':
        return text or json.dumps(value) if value else None
    else:
        # For complex types, store as JSON or text
        if value and isinstance(value, (dict, list)):
            return json.dumps(value)
        return text or str(value) if value else None

def fetch_board_data():
    """Fetch data from Monday.com board"""
    
    query = """
    query {
        boards(ids: [""" + str(BOARD_ID) + """]) {
            items {
                id
                name
                group { title }
                created_at
                updated_at
                column_values {
                    id
                    title
                    text
                    value
                    type
                }
            }
        }
    }    """
    
    try:
        response = requests.post(API_URL, json={"query": query}, headers=HEADERS)
        response.raise_for_status()
        
        data = response.json()
        if 'errors' in data:
            raise Exception("Monday.com API errors: " + str(data['errors']))
        
        items = data['data']['boards'][0]['items']
        logger.info("Fetched " + str(len(items)) + " items from board " + str(BOARD_ID))
        return items
        
    except Exception as e:
        logger.error("Error fetching board data: " + str(e))
        raise

def transform_items(items):
    """Transform Monday.com items to database rows"""
    transformed_rows = []
    
    for item in items:
        try:
            row = {
                'Item_ID': int(item['id']),
                'Name': item.get('name', '').strip() if item.get('name') else None,
                'Group_Title': item['group']['title'] if item.get('group') else None,
                'Created_At': datetime.fromisoformat(item['created_at'].replace('Z', '+00:00')) if item.get('created_at') else None,
                'Updated_At': datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00')) if item.get('updated_at') else None,
                'ProcessedDate': datetime.now(timezone.utc),
                'SourceBoard': BOARD_NAME
            }
              # Process each column using simple type-based extraction
            for col_data in item.get('column_values', []):
                col_name = col_data.get('title', '').strip()
                if col_name:
                    # Use original Monday.com column name exactly (no transformation)
                    converted_value = extract_column_value(col_data)
                    row[col_name] = converted_value
            
            transformed_rows.append(row)
            
        except Exception as e:
            logger.error("Error transforming item " + str(item.get('id', 'unknown')) + ": " + str(e))
            continue
    
    logger.info("Transformed " + str(len(transformed_rows)) + " rows")
    return transformed_rows

def load_to_database(rows):
    """Load data to database using zero-downtime staging table approach"""
    if not rows:
        logger.warning("No rows to load")
        return
    
    staging_table = "stg_" + TARGET_TABLE
    
    try:
        # Step 1: Prepare staging table
        logger.info("Preparing staging table for zero-downtime refresh...")
        
        # Check if staging table exists, create if not
        staging_exists_query = f"""
        SELECT COUNT(*) as count 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = 'dbo' 
        AND TABLE_NAME = '{staging_table}'
        """
        result = db.run_query(staging_exists_query, TARGET_DATABASE)
        staging_exists = result.iloc[0]['count'] > 0
        
        if not staging_exists:
            logger.info("Creating staging table...")
            create_staging_sql = f"""
            SELECT TOP 0 * 
            INTO [dbo].[{staging_table}] 
            FROM [dbo].[{TARGET_TABLE}]
            """
            db.execute(create_staging_sql, TARGET_DATABASE)
            logger.info("Staging table created")
        
        # Truncate staging table for fresh load
        logger.info("Truncating staging table for fresh load")
        db.execute(f"TRUNCATE TABLE [dbo].[{staging_table}]", TARGET_DATABASE)
        
        # Step 2: Load data into staging table (production remains available)
        logger.info("Loading " + str(len(rows)) + " rows into staging table " + TARGET_DATABASE + ".dbo." + staging_table)
        
        # Use pandas DataFrame approach for bulk insert (matching production pattern)
        import pandas as pd
        df = pd.DataFrame(rows)
        
        # Get connection and bulk insert
        conn = db.get_connection(TARGET_DATABASE)
        try:
            df.to_sql(
                name=staging_table,
                con=conn,
                schema='dbo',
                if_exists='append',
                index=False,
                method='multi',
                chunksize=1000
            )
        finally:
            conn.close()
        
        # Step 3: Validate staging data
        staging_count_result = db.run_query(f"SELECT COUNT(*) as count FROM [dbo].[{staging_table}]", TARGET_DATABASE)
        staging_count = staging_count_result.iloc[0]['count']
        
        if staging_count != len(rows):
            raise Exception(f"Data validation failed: expected {len(rows)}, got {staging_count} in staging table")
        
        logger.info("Staging data validated: " + str(staging_count) + " records loaded")
        
        # Step 4: Atomic swap (minimal downtime)
        logger.info("Performing atomic table swap...")
        swap_sql = f"""
        BEGIN TRANSACTION
        
        -- Drop production table
        DROP TABLE [dbo].[{TARGET_TABLE}]
        
        -- Rename staging to production
        EXEC sp_rename 'dbo.{staging_table}', '{TARGET_TABLE}'
        
        -- Create new empty staging table for next run
        SELECT TOP 0 * 
        INTO [dbo].[{staging_table}] 
        FROM [dbo].[{TARGET_TABLE}]
        
        COMMIT TRANSACTION
        """
        
        db.execute(swap_sql, TARGET_DATABASE)
        
        # Verify the swap
        final_count_result = db.run_query(f"SELECT COUNT(*) as count FROM [dbo].[{TARGET_TABLE}]", TARGET_DATABASE)
        final_count = final_count_result.iloc[0]['count']
        
        logger.info("Zero-downtime data load completed successfully")
        logger.info("Final production table count: " + str(final_count))
        
    except Exception as e:
        logger.error("Error during zero-downtime data load: " + str(e))
        logger.info("Production table remains unchanged - no data loss")
        raise

def main():
    """Main execution function"""
    try:
        logger.info("Starting " + BOARD_NAME + " board extraction")
        logger.info("Board ID: " + str(BOARD_ID))
        logger.info("Target: " + TARGET_DATABASE + ".dbo." + TARGET_TABLE)
        
        # Extract, transform, load
        items = fetch_board_data()
        rows = transform_items(items)
        load_to_database(rows)
        
        logger.info("Board extraction completed successfully")
        
    except Exception as e:
        logger.error("Board extraction failed: " + str(e))
        raise

if __name__ == "__main__":
    main()