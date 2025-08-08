#!/usr/bin/env python3
"""
Async Batch Monday.com Board Loader
===================================

High-performance async loader for large Monday.com boards using two-phase extraction:
1. Sequential cursor-based ID harvest (items_page/next_items_page)
2. Fully async batch detail fetch (items(ids: [...]))

Usage:
    python load_boards_async.py --board-id 9200517329
    python load_boards_async.py --board-id 9200517329 --batch-size 150 --concurrency 8
    python load_boards_async.py --board-id 9200517329 --harvest-only

Features:
- Two-phase extraction for optimal performance on large boards
- Configurable batch size and concurrency limits
- Follows project import standards and patterns
- Integration with existing config/registry system
- Comprehensive logging and error handling
"""

import sys
import os
import time
import json
import asyncio
import aiohttp
import argparse
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

logger = logger.get_logger("load_boards_async")

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

# ─────────────────── Configuration Management ───────────────────

def get_metadata_path(board_id: int) -> Path:
    """Get path to board metadata file"""
    return repo_root / "configs" / "boards" / f"board_{board_id}_metadata.json"

def get_registry_path() -> Path:
    """Get path to board registry file"""
    return repo_root / "configs" / "registry.json"

def load_board_metadata(board_id: int) -> Dict[str, Any]:
    """Load board metadata configuration"""
    metadata_path = get_metadata_path(board_id)
    
    if not metadata_path.exists():
        logger.error(f"Board metadata not found for {board_id}")
        logger.info("TIP: Run discovery first: python pipelines/codegen/universal_board_extractor.py --board-id {board_id}")
        sys.exit(1)
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    logger.info(f"SCHEMA: Loaded metadata for board {board_id}: {metadata_path}")
    return metadata

# ─────────────────── Async GraphQL Client ───────────────────

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
                elif response.status == 429:
                    # HTTP 429 Rate limit - use exponential backoff
                    retry_settings = monday_config.get_retry_settings()
                    wait_time = min(
                        retry_settings.base_delay * (retry_settings.exponential_multiplier ** attempt),
                        retry_settings.max_delay
                    )
                    logger.warning(f"HTTP 429: Rate limit hit, waiting {wait_time:.1f}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                elif response.status >= 500:
                    # Server error - shorter retry delay
                    wait_time = 1 + attempt
                    logger.warning(f"RETRY: Server error {response.status}, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                else:
                    response.raise_for_status()
        except asyncio.TimeoutError:
            if attempt == max_retries - 1:
                logger.error(f"RETRY: Request timeout after {max_retries} attempts")
                raise
            wait_time = 2 + attempt
            logger.warning(f"RETRY: Timeout, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
            await asyncio.sleep(wait_time)
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"RETRY: Request failed after {max_retries} attempts: {e}")
                raise
            wait_time = 2 ** attempt
            logger.warning(f"RETRY: Attempt {attempt + 1}/{max_retries} failed: {e}, waiting {wait_time}s")
            await asyncio.sleep(wait_time)

# ─────────────────── Phase 1: Sequential ID Harvest ───────────────────

async def fetch_cursor_page(session: aiohttp.ClientSession, board_id: int, 
                           cursor: Optional[str] = None, limit: int = 200) -> Tuple[Optional[str], List[int]]:
    """Fetch a single page of item IDs using cursor pagination"""
    if cursor is None:
        # First page
        query = f"""
        query {{
          boards(ids: {board_id}) {{
            items_page(limit: {limit}) {{
              cursor
              items {{ id }}
            }}
          }}
        }}
        """
    else:
        # Subsequent pages
        query = f"""
        query {{
          next_items_page(cursor: "{cursor}", limit: {limit}) {{
            cursor
            items {{ id }}
          }}
        }}
        """
    
    data = await gql_request(session, query)
    
    if cursor is None:
        page = data["boards"][0]["items_page"]
    else:
        page = data["next_items_page"]
    
    next_cursor = page["cursor"]
    item_ids = [int(item["id"]) for item in page["items"]]
    
    return next_cursor, item_ids

async def harvest_all_item_ids(session: aiohttp.ClientSession, board_id: int, 
                              page_limit: int = 500) -> List[int]:
    """Phase 1: Sequential harvest of all item IDs using cursor pagination"""
    logger.info(f"HARVEST: Starting sequential ID harvest for board {board_id}")
    
    all_ids = []
    cursor = None
    page_count = 0
    
    while True:
        try:
            cursor, batch_ids = await fetch_cursor_page(session, board_id, cursor, page_limit)
            page_count += 1
            
            if batch_ids:
                all_ids.extend(batch_ids)
                logger.info(f"HARVEST: Page {page_count}: {len(batch_ids)} IDs collected "
                           f"(total: {len(all_ids)})")
            
            # Stop if no more items or no cursor for next page
            if not cursor or not batch_ids:
                break
                
        except Exception as e:
            logger.error(f"Error during ID harvest on page {page_count}: {e}")
            raise
    
    logger.info(f"HARVEST: Complete - {len(all_ids)} total IDs collected in {page_count} pages")
    return all_ids

# ─────────────────── Phase 2: Async Batch Detail Fetch ───────────────────

async def fetch_details_batch(session: aiohttp.ClientSession, item_ids: List[int]) -> List[Dict[str, Any]]:
    """Fetch full details for a batch of item IDs"""
    if not item_ids:
        return []
    
    ids_list = ",".join(f'"{i}"' for i in item_ids)
    query = f"""
    query {{
      items(ids: [{ids_list}]) {{
        id
        name
        updated_at
        group {{ 
          id
          title 
        }}
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
          ... on NumbersValue {{ text }}
          ... on TimelineValue {{ text }}
        }}
      }}
    }}
    """
    
    try:
        data = await gql_request(session, query)
        return data["items"]
    except Exception as e:
        logger.error(f"Error fetching batch of {len(item_ids)} items: {e}")
        raise

async def fetch_all_details_async(session: aiohttp.ClientSession, item_ids: List[int], 
                                 batch_size: int = 150, max_concurrency: int = 5) -> List[Dict[str, Any]]:
    """Phase 2: Async batch fetch of all item details"""
    logger.info(f"FETCH: Starting async detail fetch for {len(item_ids)} items")
    logger.info(f"FETCH: Using batch size {batch_size}, max concurrency {max_concurrency}")
    
    # Split into batches
    batches = [item_ids[i:i + batch_size] for i in range(0, len(item_ids), batch_size)]
    logger.info(f"FETCH: Created {len(batches)} batches")
    
    # Create semaphore to limit concurrency
    semaphore = asyncio.Semaphore(max_concurrency)
    
    async def fetch_with_semaphore(batch_ids, batch_num):
        async with semaphore:
            try:
                result = await fetch_details_batch(session, batch_ids)
                logger.info(f"FETCH: Batch {batch_num}/{len(batches)} complete - {len(result)} items fetched")
                return result
            except Exception as e:
                logger.error(f"FETCH: Batch {batch_num}/{len(batches)} failed - {e}")
                return []
    
    # Execute all batches concurrently
    start_time = time.time()
    tasks = [fetch_with_semaphore(batch, i+1) for i, batch in enumerate(batches)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Check for exceptions and flatten results
    all_items = []
    failed_batches = 0
    failed_items_count = 0
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"FETCH: Batch {i + 1} failed: {result}")
            failed_batches += 1
            failed_items_count += len(batches[i])  # Count items in failed batch
        else:
            all_items.extend(result)
            # If result is smaller than expected batch, some items failed
            if len(result) < len(batches[i]):
                partial_failures = len(batches[i]) - len(result)
                failed_items_count += partial_failures
                logger.warning(f"FETCH: Batch {i + 1} partial success - {len(result)}/{len(batches[i])} items")
    
    fetch_time = time.time() - start_time
    items_per_sec = len(all_items) / fetch_time if fetch_time > 0 else 0
    
    logger.info(f"FETCH: Complete - {len(all_items)} items fetched in {fetch_time:.2f}s "
               f"({items_per_sec:.0f} items/sec)")
    
    if failed_batches > 0:
        logger.warning(f"FETCH: {failed_batches} batches completely failed")
    if failed_items_count > 0:
        logger.warning(f"FETCH: {failed_items_count} total items failed to fetch")
    
    return all_items

# ─────────────────── Data Processing ───────────────────

def process_items_to_dataframe(items: List[Dict[str, Any]], metadata: Dict[str, Any]) -> pd.DataFrame:
    """Convert Monday.com items to DataFrame using metadata configuration"""
    logger.info(f"PROCESS: Converting {len(items)} items to DataFrame")
    
    records = []
    columns_meta = {}
    
    # Build columns metadata from config
    for col in metadata.get("columns", []):
        if not col.get("exclude", False):
            columns_meta[col["monday_id"]] = {
                "title": col["monday_title"],
                "type": col["monday_type"],
                "field": col.get("custom_extraction_field") or col["extraction_field"],
                "sql": col.get("custom_sql_type") or col["sql_type"]
            }
    
    # Process each item
    for item in items:
        record = {
            "item_id": int(item["id"]),
            "item_name": item["name"],
            "updated_at": item["updated_at"],
            "group_id": item["group"]["id"] if item["group"] else None,
            "group_title": item["group"]["title"] if item["group"] else None
        }
        
        # Process column values
        for col_val in item["column_values"]:
            col_id = col_val["id"]
            
            if col_id in columns_meta:
                col_meta = columns_meta[col_id]
                field = col_meta["field"]
                
                # Extract value based on field type
                if field == "text":
                    value = col_val.get("text")
                elif field == "value":
                    value = col_val.get("value")
                else:
                    value = col_val.get(field) or col_val.get("text")
                
                record[col_meta["title"]] = value
        
        records.append(record)
    
    df = pd.DataFrame(records)
    logger.info(f"PROCESS: DataFrame created with {len(df)} rows x {len(df.columns)} columns")
    
    return df

# ─────────────────── Database Validation ───────────────────

def validate_database_records(table_name: str, database: str = None) -> int:
    """Validate the number of records in the target database table"""
    try:
        # Get database connection
        if database:
            connection = db.get_connection(database)
        else:
            connection = db.get_connection()
        
        cursor = connection.cursor()
        
        # Execute count query
        query = f"SELECT COUNT(*) FROM [{table_name}]"
        cursor.execute(query)
        count = cursor.fetchone()[0]
        
        cursor.close()
        connection.close()
        
        return count
        
    except Exception as e:
        logger.error(f"VALIDATION: Error counting records in {table_name}: {e}")
        return -1

# ─────────────────── Registry and Config Integration ───────────────────

def update_registry(board_id: int, metadata: Dict[str, Any], performance_stats: Dict[str, Any], result_status: str):
    """Update board registry with run information"""
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
    
    # Update board entry
    registry["boards"][str(board_id)] = {
        "board_name": metadata["board_name"],
        "table_name": metadata["table_name"],
        "database": metadata["database"],
        "last_run": datetime.now().isoformat(),
        "last_run_type": "async_batch",
        "last_run_status": result_status.lower(),
        "status": "active",
        "performance": performance_stats,
        "metadata_path": f"configs/boards/board_{board_id}_metadata.json"
    }
    
    registry["metadata"]["updated_at"] = datetime.now().isoformat()
    
    # Save registry
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2)
    
    logger.info(f"SUCCESS: Updated registry for board {board_id}")

# ─────────────────── Main ETL Pipeline ───────────────────

async def execute_async_etl_pipeline(board_id: int, batch_size: int = None, 
                                   max_concurrency: int = None, harvest_only: bool = False):
    """Execute the complete async ETL pipeline"""
    logger.info(f"START: Async ETL pipeline for board {board_id}")
    
    # Use MondayConfig for optimal settings if not provided
    if batch_size is None:
        batch_size = monday_config.get_optimal_batch_size(str(board_id), "ingestion")
        logger.info(f"CONFIG: Using optimal batch size from config: {batch_size}")
    
    if max_concurrency is None:
        max_concurrency = monday_config.get_optimal_concurrency(str(board_id), "ingestion")
        logger.info(f"CONFIG: Using optimal concurrency from config: {max_concurrency}")
    
    logger.info(f"CONFIG: Final settings - Batch size {batch_size}, concurrency {max_concurrency}")
    
    # Load metadata
    metadata = load_board_metadata(board_id)
    table_name = metadata.get('table_name', f'MON_{board_id}')
    database = metadata.get('database', 'default')
    
    logger.info(f"DEBUG: Original table_name from metadata: '{table_name}'")
    logger.info(f"TARGET: Database '{database}', Table '{table_name}'")
    
    total_start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        # Phase 1: Sequential ID harvest
        harvest_start = time.time()
        item_ids = await harvest_all_item_ids(session, board_id)
        harvest_time = time.time() - harvest_start
        
        logger.info(f"HARVEST: {len(item_ids)} total IDs collected in {harvest_time:.2f}s")
        
        if harvest_only:
            logger.info(f"HARVEST_ONLY: Complete - {len(item_ids)} IDs collected")
            return
        
        # Phase 2: Async detail fetch
        items = await fetch_all_details_async(session, item_ids, batch_size, max_concurrency)
        
        # Calculate success rate
        items_fetched = len(items)
        total_ids = len(item_ids)
        success_rate = (items_fetched / total_ids * 100) if total_ids > 0 else 0
        failed_items = total_ids - items_fetched
        
        logger.info(f"FETCH_SUMMARY: {items_fetched}/{total_ids} items fetched ({success_rate:.1f}% success)")
        if failed_items > 0:
            logger.warning(f"FETCH_SUMMARY: {failed_items} items failed to fetch")
        
        # Phase 3: Data processing
        df = process_items_to_dataframe(items, metadata)
        
        # Phase 4: Database operations (reuse from load_boards.py patterns)
        logger.info(f"DATABASE: Preparing staging table for '{table_name}'...")
        # TODO: Integrate staging table creation and atomic swap
        # staging_helper.prepare_staging_table(df, f"swp_{table_name}", ...)
        # staging_helper.load_to_staging_table(df, ...)
        # staging_helper.atomic_swap_tables(...)
        
        total_time = time.time() - total_start_time
        
        # Performance stats
        performance_stats = {
            "total_ids_harvested": total_ids,
            "total_items_fetched": items_fetched,
            "success_rate_percent": success_rate,
            "failed_items": failed_items,
            "harvest_time_seconds": harvest_time,
            "total_time_seconds": total_time,
            "items_per_second": items_fetched / total_time if total_time > 0 else 0,
            "batch_size": batch_size,
            "max_concurrency": max_concurrency
        }
        
        # Determine overall result
        if success_rate >= 95:
            result_status = "SUCCESS"
        elif success_rate >= 85:
            result_status = "WARNING"
        else:
            result_status = "FAILURE"
        
        logger.info(f"PERFORMANCE: {performance_stats['items_per_second']:.0f} items/sec")
        logger.info(f"RESULT: {result_status} - {items_fetched}/{total_ids} items processed ({success_rate:.1f}%) in {total_time:.2f}s")
        
        # Database validation (if database operations were completed)
        # For now, just validate if table exists and show count
        try:
            db_count = validate_database_records(table_name, database)
            if db_count >= 0:
                logger.info(f"VALIDATION: Database table '{table_name}' contains {db_count} records")
                if db_count != items_fetched:
                    logger.warning(f"VALIDATION: Database count ({db_count}) != fetched items ({items_fetched})")
            else:
                logger.warning(f"VALIDATION: Could not validate database table '{table_name}'")
        except Exception as e:
            logger.error(f"VALIDATION: Database validation failed: {e}")
        
        # Update registry
        # update_registry(board_id, metadata, performance_stats, result_status)

# ─────────────────── CLI Interface ───────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Async Batch Monday.com Board Loader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python load_boards_async.py --board-id 9200517329
  python load_boards_async.py --board-id 9200517329 --batch-size 25 --concurrency 8
  python load_boards_async.py --board-id 9200517329 --harvest-only
        """
    )
    
    parser.add_argument('--board-id', required=True, type=int, help='Monday.com board ID')
    parser.add_argument('--batch-size', type=int, 
                       help='Batch size for detail fetch (default: from config, MAX: 100 - Monday.com API limit)')
    parser.add_argument('--concurrency', type=int,
                       help='Max concurrent detail fetch requests (default: from config)')
    parser.add_argument('--harvest-only', action='store_true',
                       help='Only harvest item IDs, skip detail fetch and database operations')
    
    args = parser.parse_args()
    
    # Show optimal settings from configuration
    optimal_batch = monday_config.get_optimal_batch_size(str(args.board_id), "ingestion")
    optimal_concurrency = monday_config.get_optimal_concurrency(str(args.board_id), "ingestion")
    board_info = monday_config.get_board_info(str(args.board_id))
    
    logger.info(f"🔧 MONDAY CONFIG: Optimal settings for board {args.board_id}")
    logger.info(f"   • Batch Size: {optimal_batch}")
    logger.info(f"   • Concurrency: {optimal_concurrency}")
    if board_info:
        complexity = board_info.get('complexity_category', 'unknown')
        logger.info(f"   • Board Complexity: {complexity}")
        logger.info(f"   • Board Name: {board_info.get('name', 'Unknown')}")
    
    # Use configuration defaults if not provided
    batch_size = args.batch_size if args.batch_size is not None else None
    concurrency = args.concurrency if args.concurrency is not None else None
    
    # Show final settings
    final_batch = batch_size if batch_size is not None else optimal_batch
    final_concurrency = concurrency if concurrency is not None else optimal_concurrency
    
    # Validate Monday.com API limits
    if final_batch > 100:
        logger.error(f"❌ INVALID BATCH SIZE: {final_batch} exceeds Monday.com API limit of 100 IDs per batch")
        logger.info("💡 TIP: Use --batch-size 100 or lower")
        sys.exit(1)
    
    if final_concurrency > 20:
        logger.warning(f"⚠️ HIGH CONCURRENCY: {final_concurrency} may hit rate limits (recommended: 6-12)")
    
    logger.info(f"START: Async Batch Monday.com Board Loader")
    logger.info(f"BOARD: {args.board_id}, BATCH: {final_batch}, CONCURRENCY: {final_concurrency}")
    
    try:
        asyncio.run(execute_async_etl_pipeline(
            args.board_id, 
            batch_size, 
            concurrency, 
            args.harvest_only
        ))
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
