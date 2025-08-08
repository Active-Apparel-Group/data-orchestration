#!/usr/bin/env python3
"""
Monday.com Dropdown Values Extraction System
===========================================

High-performance async extractor for Monday.com dropdown values:
1. Board-specific dropdown extraction (get-board-dropdowns.graphql)
2. Global managed columns extraction (get-managed-dropdowns.graphql)

Usage:
    python load_dropdown_values.py --board-id 9200517329
    python load_dropdown_values.py --board-id 9200517329 --include-managed
    python load_dropdown_values.py --all-boards

Features:
- Async processing with MondayConfig rate limiting
- JSON parsing of settings_str dropdown labels
- Normalized database storage (board/column/value)
- Batch processing for multiple boards
- Comprehensive error handling and logging
"""

import sys
import os
import json
import asyncio
import aiohttp
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd

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
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
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

# Import helpers following project standards
import db_helper as db
import logger_helper as logger
import staging_helper

# Import Monday.com configuration system
sys.path.insert(0, str(repo_root / "src"))
from pipelines.utils.monday_config import MondayConfig

# Set staging mode for Monday.com boards (dirty data requires robust handling)
staging_helper.set_staging_mode('robust')

# Load configuration from centralized config
config = db.load_config()
monday_config = MondayConfig()

logger = logger.get_logger("load_dropdown_values")

# ─────────────────── Environment & API Setup ───────────────────
MONDAY_TOKEN = os.getenv('MONDAY_API_KEY') or config.get('apis', {}).get('monday', {}).get('api_token')
API_VER = monday_config.get_api_version()
API_URL = monday_config.get_api_url()

if not MONDAY_TOKEN or MONDAY_TOKEN == "YOUR_MONDAY_API_TOKEN_HERE":
    logger.error("MONDAY_API_KEY environment variable not set or config.yaml not configured")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {MONDAY_TOKEN}",
    "API-Version": API_VER,
    "Content-Type": "application/json"
}

# ─────────────────── Database Schema Validation ───────────────────

def validate_dropdown_values_table():
    """Validate that MON_Dropdown_Values table exists (created via migration)"""
    try:
        with db.get_connection('orders') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM sysobjects 
                WHERE name='MON_Dropdown_Values' AND xtype='U'
            """)
            table_exists = cursor.fetchone()[0] > 0
            
            if not table_exists:
                raise Exception(
                    "MON_Dropdown_Values table not found. "
                    "Please run migration: 025_create_dropdown_values_table.sql"
                )
            
            logger.info("✅ MON_Dropdown_Values table validated")
            return True
            
    except Exception as e:
        logger.error(f"❌ Table validation failed: {e}")
        raise

# ─────────────────── GraphQL Queries ───────────────────

def load_graphql_query(query_name: str) -> str:
    """Load GraphQL query from file"""
    query_path = repo_root / "sql" / "graphql" / "monday" / "queries" / f"{query_name}.graphql"
    
    if not query_path.exists():
        raise FileNotFoundError(f"GraphQL query not found: {query_path}")
    
    with open(query_path, 'r', encoding='utf-8') as f:
        return f.read()

async def gql_request(session: aiohttp.ClientSession, query: str, variables: Dict = None, 
                     max_retries: int = None, timeout: int = None) -> Dict[str, Any]:
    """Execute GraphQL request with intelligent retry and rate limiting"""
    # Use MondayConfig for retry settings
    if max_retries is None:
        max_retries = monday_config.get_retry_settings().max_retries
    if timeout is None:
        timeout = monday_config.get_timeout()
    
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    for attempt in range(max_retries):
        try:
            async with session.post(API_URL, json=payload, headers=HEADERS, 
                                  timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                if response.status == 200:
                    data = await response.json()
                    if "errors" in data:
                        # Check for Monday.com rate limit errors
                        if monday_config.is_rate_limit_error(data):
                            retry_delay = monday_config.get_retry_delay(data)
                            logger.warning(f"MONDAY RATE LIMIT: retry_in_seconds={retry_delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                            await asyncio.sleep(retry_delay)
                            continue
                        else:
                            logger.error(f"GraphQL errors: {data['errors']}")
                            raise Exception(f"GraphQL errors: {data['errors']}")
                    return data["data"]
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
        except asyncio.TimeoutError:
            if attempt == max_retries - 1:
                raise Exception("Request timeout after all retries")
            retry_settings = monday_config.get_retry_settings()
            delay = min(
                retry_settings.base_delay * (retry_settings.exponential_multiplier ** attempt),
                retry_settings.max_delay
            )
            logger.warning(f"Timeout, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
            await asyncio.sleep(delay)
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Request failed after {max_retries} attempts: {e}")
                raise
            retry_settings = monday_config.get_retry_settings()
            delay = min(
                retry_settings.base_delay * (retry_settings.exponential_multiplier ** attempt),
                retry_settings.max_delay
            )
            logger.warning(f"Error, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries}): {e}")
            await asyncio.sleep(delay)

# ─────────────────── Board Dropdown Extraction ───────────────────

async def extract_board_dropdowns(session: aiohttp.ClientSession, board_id: str) -> List[Dict[str, Any]]:
    """Extract dropdown values from a specific board"""
    logger.info(f"🔍 Extracting dropdown values for board {board_id}")
    
    query = load_graphql_query("get-board-dropdowns")
    variables = {"boardId": board_id}
    
    try:
        data = await gql_request(session, query, variables)
        
        if not data.get("boards") or len(data["boards"]) == 0:
            logger.warning(f"⚠️ No board found with ID {board_id}")
            return []
        
        board = data["boards"][0]
        board_name = board["name"]
        
        dropdown_values = []
        
        for column in board.get("columns", []):
            column_id = column["id"]
            column_name = column["title"]
            settings_str = column.get("settings_str", "{}")
            
            try:
                # Parse the settings JSON
                settings = json.loads(settings_str)
                labels = settings.get("labels", [])
                deactivated_labels = settings.get("deactivated_labels", [])
                deactivated_ids = {label.get("id") if isinstance(label, dict) else label for label in deactivated_labels}
                
                logger.info(f"  📊 Column '{column_name}' ({column_id}): {len(labels)} dropdown values")
                
                # Debug: Log first label structure
                if labels and len(labels) > 0:
                    logger.debug(f"    🔍 Sample label structure: {type(labels[0])} - {labels[0]}")
                
                for i, label in enumerate(labels):
                    try:
                        # Handle different label formats
                        if isinstance(label, dict):
                            label_id = label.get("id")
                            label_name = label.get("name", "")
                        elif isinstance(label, (int, str)):
                            # Handle case where label is just an ID
                            label_id = int(label) if str(label).isdigit() else None
                            label_name = f"Label {label_id}" if label_id else str(label)
                        else:
                            logger.warning(f"    ⚠️ Unexpected label format in {column_name}: {type(label)} - {label}")
                            continue
                        
                        # Skip if we couldn't extract a valid label_id
                        if label_id is None:
                            logger.warning(f"    ⚠️ Could not extract label_id from: {label}")
                            continue
                        
                        is_deactivated = label_id in deactivated_ids
                        
                        dropdown_values.append({
                            "board_id": board_id,
                            "board_name": board_name,
                            "column_id": column_id,
                            "column_name": column_name,
                            "label_id": label_id,
                            "label_name": label_name,
                            "is_deactivated": is_deactivated,
                            "source_type": "board"
                        })
                        
                    except Exception as label_error:
                        logger.warning(f"    ⚠️ Error processing label {i} in column {column_name}: {label_error}")
                        continue
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse settings_str for column {column_id}: {e}")
                continue
        
        logger.info(f"✅ Extracted {len(dropdown_values)} dropdown values from board {board_id}")
        return dropdown_values
        
    except Exception as e:
        logger.error(f"❌ Failed to extract dropdown values for board {board_id}: {e}")
        return []

# ─────────────────── Managed Columns Extraction ───────────────────

async def extract_managed_dropdowns(session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
    """Extract global managed dropdown columns"""
    logger.info("🌐 Extracting managed dropdown columns")
    
    query = load_graphql_query("get-managed-dropdowns")
    
    try:
        data = await gql_request(session, query)
        
        managed_values = []
        managed_columns = data.get("managed_column", [])
        
        logger.info(f"🔍 Found {len(managed_columns)} managed columns")
        
        for column in managed_columns:
            column_id = column["id"]
            column_name = column["title"]
            settings = column.get("settings", {})
            
            # Handle DropdownColumnSettings
            labels = settings.get("labels", [])
            
            logger.info(f"  📊 Managed column '{column_name}' ({column_id}): {len(labels)} dropdown values")
            
            for label in labels:
                label_id = label.get("id")
                label_name = label.get("label", "")
                is_deactivated = label.get("is_deactivated", False)
                
                managed_values.append({
                    "board_id": "MANAGED",
                    "board_name": "Managed Columns",
                    "column_id": column_id,
                    "column_name": column_name,
                    "label_id": label_id,
                    "label_name": label_name,
                    "is_deactivated": is_deactivated,
                    "source_type": "managed"
                })
        
        logger.info(f"✅ Extracted {len(managed_values)} managed dropdown values")
        return managed_values
        
    except Exception as e:
        logger.error(f"❌ Failed to extract managed dropdown values: {e}")
        return []

# ─────────────────── Database Operations ───────────────────

def store_dropdown_values(dropdown_values: List[Dict[str, Any]]) -> int:
    """Store dropdown values using high-performance MERGE/UPSERT operation"""
    if not dropdown_values:
        logger.info("📝 No dropdown values to store")
        return 0
    
    logger.info(f"💾 Storing {len(dropdown_values)} dropdown values using MERGE operation")
    
    # Create DataFrame for bulk operations
    df = pd.DataFrame(dropdown_values)
    
    # Convert boolean to int for SQL Server
    df['is_deactivated'] = df['is_deactivated'].astype(int)
    
    try:
        with db.get_connection('orders') as conn:
            # Create temporary table for bulk insert
            temp_table_sql = """
            CREATE TABLE #TempDropdownValues (
                board_id NVARCHAR(50) NOT NULL,
                board_name NVARCHAR(255) NOT NULL,
                column_id NVARCHAR(100) NOT NULL,
                column_name NVARCHAR(255) NOT NULL,
                label_id INT NOT NULL,
                label_name NVARCHAR(500) NOT NULL,
                is_deactivated BIT NOT NULL,
                source_type NVARCHAR(20) NOT NULL
            )
            """
            
            cursor = conn.cursor()
            cursor.execute(temp_table_sql)
            
            # Bulk insert into temp table (much faster than row-by-row)
            logger.info("📊 Bulk inserting to temporary table...")
            
            insert_sql = """
            INSERT INTO #TempDropdownValues 
            (board_id, board_name, column_id, column_name, label_id, label_name, is_deactivated, source_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            # Prepare data for bulk insert
            data_tuples = [
                (row['board_id'], row['board_name'], row['column_id'], row['column_name'],
                 row['label_id'], row['label_name'], row['is_deactivated'], row['source_type'])
                for _, row in df.iterrows()
            ]
            
            cursor.executemany(insert_sql, data_tuples)
            
            # Execute high-performance MERGE operation
            logger.info("🔄 Executing MERGE operation...")
            
            merge_sql = """
            MERGE MON_Dropdown_Values AS target
            USING #TempDropdownValues AS source
            ON (target.board_id = source.board_id 
                AND target.column_id = source.column_id 
                AND target.label_id = source.label_id)
            
            WHEN MATCHED THEN
                UPDATE SET 
                    board_name = source.board_name,
                    column_name = source.column_name,
                    label_name = source.label_name,
                    is_deactivated = source.is_deactivated,
                    source_type = source.source_type,
                    extracted_at = GETDATE()
            
            WHEN NOT MATCHED THEN
                INSERT (board_id, board_name, column_id, column_name, label_id, label_name, 
                       is_deactivated, source_type, extracted_at)
                VALUES (source.board_id, source.board_name, source.column_id, source.column_name,
                       source.label_id, source.label_name, source.is_deactivated, source.source_type, GETDATE())
            
            OUTPUT $action, inserted.board_id, inserted.column_id, inserted.label_id;
            """
            
            # Execute MERGE and capture results
            results = cursor.execute(merge_sql).fetchall()
            
            # Count operations
            inserted_count = sum(1 for result in results if result[0] == 'INSERT')
            updated_count = sum(1 for result in results if result[0] == 'UPDATE')
            
            # Clean up temp table
            cursor.execute("DROP TABLE #TempDropdownValues")
            
            conn.commit()
            logger.info(f"✅ MERGE operation complete: {inserted_count} inserted, {updated_count} updated")
            
            return inserted_count + updated_count
            
    except Exception as e:
        logger.error(f"❌ Failed to store dropdown values: {e}")
        raise

# ─────────────────── Board Discovery ───────────────────

async def get_all_board_ids(session: aiohttp.ClientSession) -> List[str]:
    """Get all board IDs from workspace"""
    logger.info("🔍 Discovering all boards in workspace")
    
    query = """
    query {
      boards(limit: 100) {
        id
        name
        state
        board_kind
      }
    }
    """
    
    try:
        data = await gql_request(session, query)
        boards = data.get("boards", [])
        
        # Filter active boards
        active_boards = [
            board["id"] for board in boards 
            if board.get("state") == "active" and board.get("board_kind") == "public"
        ]
        
        logger.info(f"✅ Found {len(active_boards)} active boards")
        return active_boards
        
    except Exception as e:
        logger.error(f"❌ Failed to discover boards: {e}")
        return []

# ─────────────────── Main ETL Pipeline ───────────────────

async def execute_dropdown_extraction(board_ids: List[str] = None, include_managed: bool = False, 
                                     batch_size: int = None, max_concurrency: int = None):
    """Execute dropdown values extraction pipeline"""
    start_time = time.time()
    
    # Get optimal settings from MondayConfig
    if batch_size is None:
        batch_size = monday_config.get_optimal_batch_size(operation="ingestion")
    if max_concurrency is None:
        max_concurrency = monday_config.get_optimal_concurrency(operation="ingestion")
    
    logger.info(f"🚀 Starting dropdown extraction pipeline")
    logger.info(f"📊 Settings: batch_size={batch_size}, max_concurrency={max_concurrency}")
    
    # Validate table exists (created via migration)
    validate_dropdown_values_table()
    
    all_dropdown_values = []
    
    # Create aiohttp session
    timeout = aiohttp.ClientTimeout(total=monday_config.get_timeout())
    async with aiohttp.ClientSession(timeout=timeout) as session:
        
        # Extract board-specific dropdowns
        if board_ids:
            logger.info(f"🎯 Processing {len(board_ids)} specific boards")
            
            # Process boards in batches with concurrency control
            semaphore = asyncio.Semaphore(max_concurrency)
            
            async def extract_with_semaphore(board_id):
                async with semaphore:
                    return await extract_board_dropdowns(session, board_id)
            
            # Execute board extractions concurrently
            tasks = [extract_with_semaphore(board_id) for board_id in board_ids]
            board_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(board_results):
                if isinstance(result, Exception):
                    logger.error(f"❌ Board {board_ids[i]} failed: {result}")
                else:
                    all_dropdown_values.extend(result)
        
        # Extract managed columns if requested
        if include_managed:
            logger.info("🌐 Processing managed columns")
            managed_values = await extract_managed_dropdowns(session)
            all_dropdown_values.extend(managed_values)
    
    # Store results in database
    total_stored = store_dropdown_values(all_dropdown_values)
    
    duration = time.time() - start_time
    logger.info(f"🎉 Extraction complete!")
    logger.info(f"📊 Total dropdown values extracted: {len(all_dropdown_values)}")
    logger.info(f"💾 Total values stored/updated: {total_stored}")
    logger.info(f"⏱️ Duration: {duration:.2f} seconds")
    
    return {
        "total_extracted": len(all_dropdown_values),
        "total_stored": total_stored,
        "duration_seconds": duration,
        "boards_processed": len(board_ids) if board_ids else 0,
        "managed_included": include_managed
    }

# ─────────────────── CLI Interface ───────────────────

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Monday.com Dropdown Values Extraction System")
    parser.add_argument('--board-id', type=str, help='Specific board ID to extract')
    parser.add_argument('--board-ids', type=str, nargs='+', help='Multiple board IDs to extract')
    parser.add_argument('--all-boards', action='store_true', help='Extract from all workspace boards')
    parser.add_argument('--include-managed', action='store_true', help='Include managed columns extraction')
    parser.add_argument('--batch-size', type=int, help='Batch size for processing (default: MondayConfig optimal)')
    parser.add_argument('--max-concurrency', type=int, help='Max concurrent operations (default: MondayConfig optimal)')
    
    args = parser.parse_args()
    
    # Determine board IDs to process
    board_ids = []
    
    if args.board_id:
        board_ids = [args.board_id]
    elif args.board_ids:
        board_ids = args.board_ids
    elif args.all_boards:
        # Get all boards asynchronously
        async def get_boards():
            timeout = aiohttp.ClientTimeout(total=monday_config.get_timeout())
            async with aiohttp.ClientSession(timeout=timeout) as session:
                return await get_all_board_ids(session)
        
        board_ids = asyncio.run(get_boards())
        if not board_ids:
            logger.error("❌ No boards found or failed to discover boards")
            sys.exit(1)
    else:
        logger.error("❌ Must specify --board-id, --board-ids, or --all-boards")
        parser.print_help()
        sys.exit(1)
    
    # Execute extraction pipeline
    try:
        result = asyncio.run(execute_dropdown_extraction(
            board_ids=board_ids,
            include_managed=args.include_managed,
            batch_size=args.batch_size,
            max_concurrency=args.max_concurrency
        ))
        
        logger.info("✅ Dropdown extraction completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Dropdown extraction failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
