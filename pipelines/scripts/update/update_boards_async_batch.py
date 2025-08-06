"""
OPUS Async Batch Monday.com Update Script
Purpose: High-performance async batch updates for Monday.com with intelligent fallback
Author: CTO / Head Data Engineer  
Date: 2025-07-15

Features:
- Async HTTP with aiohttp for concurrent processing
- Intelligent batch sizing (start large, fallback to smaller)
- Connection pooling and rate limiting
- TOML-based configuration for rapid deployment
- Supports both items and subitems
- Country column type detection and formatting
- Comprehensive error handling and retry logic
- Progress tracking for large datasets (5000+ records)

Performance:
- Initial batch size: 15 items (balance of speed vs timeout risk)
- Concurrent batches: 3-5 simultaneous
- Rate limiting: 100ms between batches
- Fallback strategy: 15 → 5 → 1 item batches
"""

import sys
import os
import asyncio
import aiohttp
import time
import math
from pathlib import Path
import tomli
import json
import pandas as pd
from datetime import datetime
import argparse
from typing import Dict, List, Any, Optional, Union

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

import db_helper as db
import logger_helper
from country_mapper import format_country_for_monday

class AsyncBatchMondayUpdater:
    def load_query_from_config(self, query_config: dict) -> str:
        """
        Load SQL from file if 'file' is present in query_config, else use inline 'query'.
        """
        if not query_config:
            raise ValueError("No query_config provided.")
        # Try file first
        file_path = query_config.get('file')
        if file_path:
            sql_path = Path(file_path)
            if not sql_path.is_absolute():
                sql_path = (Path(__file__).parent.parent.parent.parent / file_path).resolve()
            if sql_path.exists():
                with open(sql_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                self.logger.warning(f"SQL file specified in config not found: {sql_path}. Falling back to inline query.")
        # Fallback to inline query
        if 'query' in query_config:
            return query_config['query']
        raise ValueError("No SQL file found and no inline query provided in query_config.")
    """
    High-performance async batch Monday.com updater
    
    Features:
    - Async HTTP requests with connection pooling
    - Intelligent batch sizing with fallback
    - Progress tracking for large datasets
    - Rate limiting and timeout handling
    - Country column type detection
    """
    
    def __init__(self, config_file: str = None, max_concurrent_batches: int = 3):
        self.logger = logger_helper.get_logger(__name__)
        self.config = db.load_config()
        self.max_concurrent_batches = max_concurrent_batches
        
        # Monday.com API configuration
        self.api_url = self.config['monday']['api_url']
        self.api_key = self.config['monday']['api_key']
        self.api_version = self.config['monday']['api_version']
        
        # HTTP headers for Monday.com API
        self.headers = {
            'Authorization': self.api_key,
            'API-Version': self.api_version,
            'Content-Type': 'application/json'
        }
        
        # Batch configuration with fallback strategy
        self.initial_batch_size = 15  # Start with moderate size
        self.fallback_batch_sizes = [5, 1]  # Fallback to smaller sizes on timeout
        self.batch_delay = 0.1  # 100ms between batches
        self.request_timeout = 25  # 25 seconds to avoid 30s timeout
        
        # Load update configuration
        if config_file:
            with open(config_file, 'rb') as f:
                self.update_config = tomli.load(f)
        else:
            self.update_config = {}
            
        self.logger.info(f"AsyncBatchMondayUpdater initialized - Max concurrent batches: {max_concurrent_batches}")
    
    def format_country_value(self, country_name: str) -> dict:
        """Format country value for Monday.com country column type"""
        return format_country_for_monday(country_name, self.logger)
    
    def load_board_metadata(self, board_id: int) -> dict:
        """Load board metadata from configs/boards/"""
        metadata_path = repo_root / "configs" / "boards" / f"board_{board_id}_metadata.json"
        
        if not metadata_path.exists():
            self.logger.warning(f"Board metadata not found: {metadata_path}")
            return {}
            
        with open(metadata_path, 'r') as f:
            return json.load(f)
    
    def detect_column_type(self, column_id: str, board_metadata: dict) -> str:
        """Detect Monday.com column type from board metadata"""
        columns = board_metadata.get('columns', [])
        for column in columns:
            if column.get('monday_id') == column_id:
                return column.get('monday_type', 'text')
        return 'text'  # Default fallback
    
    def format_column_value(self, column_id: str, value: any, board_metadata: dict) -> any:
        """Format column value based on Monday.com column type"""
        if pd.isna(value) or value is None:
            return None
            
        column_type = self.detect_column_type(column_id, board_metadata)
        
        # Handle country columns specifically
        if column_type == 'country':
            return self.format_country_value(value)
        
        # For other types, return as string (existing behavior)
        return str(value)
    
    async def execute_graphql_async(self, session: aiohttp.ClientSession, query: str, variables: dict = None) -> dict:
        """Execute GraphQL query against Monday.com API asynchronously"""
        
        payload = {'query': query}
        if variables:
            payload['variables'] = variables
        
        try:
            async with session.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.request_timeout),
                ssl=False
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API request failed: {response.status} - {error_text}")
                
                result = await response.json()
                
                if 'errors' in result and result['errors']:
                    raise Exception(f"GraphQL errors: {result['errors']}")
                
                return result
                
        except asyncio.TimeoutError:
            raise Exception("Request timeout - batch may be too large")
        except Exception as e:
            self.logger.error(f"ERROR: GraphQL execution failed: {e}")
            raise
    
    def build_batch_mutation(self, batch_updates: List[dict]) -> tuple:
        """Build GraphQL batch mutation with variables"""
        mutations = []
        variables = {}
        
        for i, update in enumerate(batch_updates):
            alias = f"update_{i}"
            mutations.append(f"""
        {alias}: change_multiple_column_values(
            board_id: $boardId_{i},
            item_id: $itemId_{i}, 
            column_values: $columnValues_{i}
        ) {{
            id
            name
            updated_at
        }}""")
            
            # Add variables for this update
            variables[f"boardId_{i}"] = str(update['board_id'])
            variables[f"itemId_{i}"] = str(update['item_id'])
            variables[f"columnValues_{i}"] = json.dumps(update['column_updates'])
        
        # Build variable definitions
        var_defs = []
        for i in range(len(batch_updates)):
            var_defs.extend([
                f"$boardId_{i}: ID!",
                f"$itemId_{i}: ID!",
                f"$columnValues_{i}: JSON!"
            ])
        
        # Complete batch query
        batch_query = f"""
        mutation BatchUpdateItems({', '.join(var_defs)}) {{
            {chr(10).join(mutations)}
        }}
        """
        
        return batch_query, variables
    
    async def execute_batch_with_fallback(self, session: aiohttp.ClientSession, batch_updates: List[dict], batch_num: int) -> dict:
        """Execute batch with intelligent fallback on timeout"""
        
        # Try initial batch size
        try:
            if len(batch_updates) <= self.initial_batch_size:
                return await self._execute_single_batch(session, batch_updates, batch_num)
            else:
                # Split into smaller batches if too large
                results = []
                success_count = 0
                error_count = 0
                
                for i in range(0, len(batch_updates), self.initial_batch_size):
                    sub_batch = batch_updates[i:i + self.initial_batch_size]
                    sub_result = await self._execute_single_batch(session, sub_batch, f"{batch_num}.{i//self.initial_batch_size + 1}")
                    
                    results.extend(sub_result['results'])
                    success_count += sub_result['success_count']
                    error_count += sub_result['error_count']
                    
                    # Small delay between sub-batches
                    await asyncio.sleep(self.batch_delay)
                
                return {
                    'success_count': success_count,
                    'error_count': error_count,
                    'results': results
                }
                
        except Exception as e:
            if "timeout" in str(e).lower():
                self.logger.warning(f"Batch {batch_num} timeout - falling back to smaller batches")
                return await self._fallback_to_smaller_batches(session, batch_updates, batch_num)
            else:
                raise
    
    async def _execute_single_batch(self, session: aiohttp.ClientSession, batch_updates: List[dict], batch_identifier: str) -> dict:
        """Execute a single batch mutation"""
        try:
            batch_query, variables = self.build_batch_mutation(batch_updates)
            
            self.logger.info(f"Executing batch {batch_identifier}: {len(batch_updates)} items")
            
            result = await self.execute_graphql_async(session, batch_query, variables)
            
            # Process batch results
            return self._process_batch_response(result, batch_updates)
            
        except Exception as e:
            self.logger.error(f"ERROR: Batch {batch_identifier} failed: {e}")
            # Return all as errors
            return {
                'success_count': 0,
                'error_count': len(batch_updates),
                'results': [{
                    'success': False,
                    'error': str(e),
                    'board_id': update['board_id'],
                    'item_id': update['item_id'],
                    'updates': update['column_updates']
                } for update in batch_updates]
            }
    
    async def _fallback_to_smaller_batches(self, session: aiohttp.ClientSession, batch_updates: List[dict], batch_num: int) -> dict:
        """Fallback to progressively smaller batch sizes"""
        
        for fallback_size in self.fallback_batch_sizes:
            try:
                self.logger.info(f"Trying fallback batch size: {fallback_size}")
                
                results = []
                success_count = 0
                error_count = 0
                
                for i in range(0, len(batch_updates), fallback_size):
                    sub_batch = batch_updates[i:i + fallback_size]
                    
                    try:
                        sub_result = await self._execute_single_batch(session, sub_batch, f"{batch_num}.fb{fallback_size}.{i//fallback_size + 1}")
                        results.extend(sub_result['results'])
                        success_count += sub_result['success_count']
                        error_count += sub_result['error_count']
                        
                        # Delay between fallback batches
                        await asyncio.sleep(self.batch_delay * 2)
                        
                    except Exception as e:
                        # Even fallback failed - mark all as errors
                        self.logger.error(f"Fallback batch failed: {e}")
                        for update in sub_batch:
                            results.append({
                                'success': False,
                                'error': str(e),
                                'board_id': update['board_id'],
                                'item_id': update['item_id'],
                                'updates': update['column_updates']
                            })
                            error_count += 1
                
                return {
                    'success_count': success_count,
                    'error_count': error_count,
                    'results': results
                }
                
            except Exception as e:
                self.logger.warning(f"Fallback size {fallback_size} also failed: {e}")
                continue
        
        # All fallback strategies failed
        self.logger.error(f"All fallback strategies failed for batch {batch_num}")
        return {
            'success_count': 0,
            'error_count': len(batch_updates),
            'results': [{
                'success': False,
                'error': 'All fallback strategies failed',
                'board_id': update['board_id'],
                'item_id': update['item_id'],
                'updates': update['column_updates']
            } for update in batch_updates]
        }
    
    def _process_batch_response(self, response: dict, batch_updates: List[dict]) -> dict:
        """Process response from batch mutation"""
        results = []
        success_count = 0
        error_count = 0
        
        if 'data' in response:
            for i, update in enumerate(batch_updates):
                alias = f"update_{i}"
                
                if alias in response['data'] and response['data'][alias]:
                    # Success
                    update_result = response['data'][alias]
                    results.append({
                        'success': True,
                        'dry_run': False,
                        'board_id': update['board_id'],
                        'item_id': update['item_id'],
                        'updates': update['column_updates'],
                        'monday_response': update_result,
                        'updated_at': datetime.now().isoformat()
                    })
                    success_count += 1
                else:
                    # Error for this specific update
                    results.append({
                        'success': False,
                        'error': f"No response data for {alias}",
                        'board_id': update['board_id'],
                        'item_id': update['item_id'],
                        'updates': update['column_updates']
                    })
                    error_count += 1
        else:
            # Entire batch failed
            error_message = response.get('errors', ['Unknown batch error'])[0]
            for update in batch_updates:
                results.append({
                    'success': False,
                    'error': str(error_message),
                    'board_id': update['board_id'],
                    'item_id': update['item_id'],
                    'updates': update['column_updates']
                })
                error_count += 1
        
        return {
            'success_count': success_count,
            'error_count': error_count,
            'results': results
        }
    
    def prepare_batch_updates(self, df: pd.DataFrame) -> List[dict]:
        """Prepare batch updates from DataFrame"""
        batch_updates = []
        
        # Load board metadata for column type detection
        if 'metadata' in self.update_config and 'board_id' in self.update_config['metadata']:
            board_id = int(self.update_config['metadata']['board_id'])
            metadata = self.load_board_metadata(board_id)
        else:
            metadata = {}
        
        for _, row in df.iterrows():
            try:
                # Extract parameters from row based on config
                if 'metadata' in self.update_config and 'board_id' in self.update_config['metadata']:
                    board_id = int(self.update_config['metadata']['board_id'])
                else:
                    board_id = int(row['board_id'])  # fallback
                
                # Get item_id_column from config
                item_id_column = self.update_config.get('item_id_column', 'monday_item_id')
                item_id = int(row[item_id_column])
                
                # Build column updates from mapping with column type detection
                column_updates = {}
                
                for monday_column_id, source_column in self.update_config['column_mapping'].items():
                    if source_column in row and pd.notna(row[source_column]):
                        # Format value based on column type (handles country columns)
                        formatted_value = self.format_column_value(monday_column_id, row[source_column], metadata)
                        if formatted_value is not None:
                            column_updates[monday_column_id] = formatted_value
                
                if column_updates:  # Only add if there are updates to make
                    batch_updates.append({
                        'board_id': board_id,
                        'item_id': item_id,
                        'column_updates': column_updates,
                        'row_data': row.to_dict()
                    })
                    
            except Exception as e:
                self.logger.error(f"ERROR: Failed to prepare update for row: {e}")
                continue
        
        return batch_updates
    
    async def async_batch_update_from_query(self, query: str, update_config: dict, dry_run: bool = True) -> dict:
        """
        Execute async batch updates from SQL query results
        
        Args:
            query: SQL query to get update data
            update_config: Configuration for mapping query results
            dry_run: If True, only validate without executing
            
        Returns:
            Dict with comprehensive batch update results
        """
        start_time = time.time()
        
        try:
            # Execute query to get update data
            with db.get_connection('orders') as conn:
                df = pd.read_sql(query, conn)
            
            if df.empty:
                return {
                    'success': True,
                    'message': 'No data found for updates',
                    'total_records': 0,
                    'duration_seconds': time.time() - start_time
                }
            
            self.logger.info(f"Processing {len(df)} records for async batch update")
            
            # Prepare all batch updates
            all_batch_updates = self.prepare_batch_updates(df)
            
            if not all_batch_updates:
                return {
                    'success': False,
                    'error': 'No valid updates prepared from data',
                    'total_records': len(df),
                    'duration_seconds': time.time() - start_time
                }
            
            if dry_run:
                return self._simulate_async_dry_run(all_batch_updates, start_time)
            
            # Execute async batch updates
            return await self._execute_async_batches(all_batch_updates, start_time)
            
        except Exception as e:
            self.logger.error(f"ERROR: Async batch update failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_records': 0,
                'duration_seconds': time.time() - start_time
            }
    
    def _simulate_async_dry_run(self, batch_updates: List[dict], start_time: float) -> dict:
        """Simulate async batch updates for dry run"""
        results = []
        for i, update in enumerate(batch_updates):
            self.logger.info(f"DRY RUN: Would update item {update['item_id']} with {len(update['column_updates'])} fields")
            results.append({
                'success': True,
                'dry_run': True,
                'board_id': update['board_id'],
                'item_id': update['item_id'],
                'updates': update['column_updates'],
                'message': 'Dry run successful - no changes made'
            })
        
        return {
            'success': True,
            'total_records': len(batch_updates),
            'success_count': len(results),
            'error_count': 0,
            'success_rate': 100.0,
            'results': results,
            'dry_run': True,
            'duration_seconds': time.time() - start_time,
            'estimated_batches': math.ceil(len(batch_updates) / self.initial_batch_size)
        }
    
    async def _execute_async_batches(self, all_batch_updates: List[dict], start_time: float) -> dict:
        """Execute async batches with connection pooling and concurrency control"""
        
        # Split into concurrent batch groups
        batch_size = self.initial_batch_size
        batch_groups = [all_batch_updates[i:i + batch_size] for i in range(0, len(all_batch_updates), batch_size)]
        
        self.logger.info(f"Executing {len(batch_groups)} batches with max {self.max_concurrent_batches} concurrent")
        
        all_results = []
        total_success = 0
        total_errors = 0
        
        # Create aiohttp session with connection pooling
        timeout = aiohttp.ClientTimeout(total=self.request_timeout)
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)  # Connection pooling
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            
            # Process batches in groups with concurrency control
            for batch_group_start in range(0, len(batch_groups), self.max_concurrent_batches):
                batch_group_end = min(batch_group_start + self.max_concurrent_batches, len(batch_groups))
                current_batch_group = batch_groups[batch_group_start:batch_group_end]
                
                self.logger.info(f"Processing batch group {batch_group_start//self.max_concurrent_batches + 1}: batches {batch_group_start+1}-{batch_group_end}")
                
                # Execute batches concurrently within this group
                tasks = []
                for i, batch_updates in enumerate(current_batch_group):
                    batch_num = batch_group_start + i + 1
                    task = self.execute_batch_with_fallback(session, batch_updates, batch_num)
                    tasks.append(task)
                
                # Wait for all batches in this group to complete
                group_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results from this group
                for i, result in enumerate(group_results):
                    if isinstance(result, Exception):
                        batch_num = batch_group_start + i + 1
                        self.logger.error(f"Batch {batch_num} failed with exception: {result}")
                        # Count as errors
                        batch_size_failed = len(current_batch_group[i])
                        total_errors += batch_size_failed
                        all_results.extend([{
                            'success': False,
                            'error': str(result),
                            'batch_num': batch_num
                        }] * batch_size_failed)
                    else:
                        all_results.extend(result['results'])
                        total_success += result['success_count']
                        total_errors += result['error_count']
                
                # Delay between batch groups to respect rate limiting
                if batch_group_end < len(batch_groups):
                    await asyncio.sleep(self.batch_delay * 2)
                
                # Progress update
                progress = (batch_group_end / len(batch_groups)) * 100
                self.logger.info(f"Progress: {progress:.1f}% ({batch_group_end}/{len(batch_groups)} batches)")
        
        success_rate = (total_success / len(all_batch_updates) * 100) if len(all_batch_updates) > 0 else 0
        duration = time.time() - start_time
        
        return {
            'success': True,
            'total_records': len(all_batch_updates),
            'success_count': total_success,
            'error_count': total_errors,
            'success_rate': success_rate,
            'results': all_results,
            'dry_run': False,
            'batches_processed': len(batch_groups),
            'duration_seconds': duration,
            'items_per_second': len(all_batch_updates) / duration if duration > 0 else 0
        }

def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(description="Async Batch Monday.com Update Script")
    parser.add_argument('--config', type=str, required=True, help='TOML config file for batch updates')
    parser.add_argument('--dry_run', action='store_true', default=True, help='Dry run mode (default: True)')
    parser.add_argument('--execute', action='store_true', help='Execute updates (overrides dry_run)')
    parser.add_argument('--max_concurrent', type=int, default=3, help='Max concurrent batches (default: 3)')
    
    args = parser.parse_args()
    
    # Override dry_run if execute is specified
    dry_run = not args.execute
    
    logger = logger_helper.get_logger(__name__)
    logger.info(f"Starting async batch update - Config: {args.config}, Dry run: {dry_run}")
    
    try:
        updater = AsyncBatchMondayUpdater(args.config, args.max_concurrent)
        
        # Async batch update from TOML config
        if 'query_config' in updater.update_config:
            query = updater.load_query_from_config(updater.update_config['query_config'])
            
            # Run async update
            result = asyncio.run(
                updater.async_batch_update_from_query(query, updater.update_config, dry_run)
            )
            
            # Print summary results
            logger.info("=" * 60)
            logger.info("ASYNC BATCH UPDATE SUMMARY")
            logger.info("=" * 60)
            logger.info(f"Total Records: {result.get('total_records', 0)}")
            logger.info(f"Success Count: {result.get('success_count', 0)}")
            logger.info(f"Error Count: {result.get('error_count', 0)}")
            logger.info(f"Success Rate: {result.get('success_rate', 0):.1f}%")
            logger.info(f"Duration: {result.get('duration_seconds', 0):.1f} seconds")
            
            if 'items_per_second' in result:
                logger.info(f"Throughput: {result['items_per_second']:.1f} items/second")
            
            logger.info("=" * 60)
            
        else:
            logger.error("ERROR: No query found in TOML config file")
            
    except Exception as e:
        logger.error(f"FATAL ERROR: {e}")

if __name__ == "__main__":
    main()
