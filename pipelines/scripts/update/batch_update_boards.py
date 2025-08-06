"""
OPUS Universal Monday.com Update Script with Batch Processing
Purpose: Standalone script for immediate Monday.com updates with 10-20 item batches
Author: CTO / Head Data Engineer
Date: 2025-06-30

Features:
- Batch processing (10-20 items per API call)
- TOML-based configuration for rapid deployment
- Supports both items and subitems
- Uses existing infrastructure and metadata
- Monday.com batch mutation for efficiency
"""

import sys
import os
from pathlib import Path
import tomli
import json
import requests
from datetime import datetime
import argparse
import pandas as pd

# Standard import pattern
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists() and (current / "integrations").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root (needs both utils and integrations folders)")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

import db_helper as db
import logger_helper

class BatchMondayUpdater:
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
    Batch Monday.com update handler for efficient bulk operations
    
    Features:
    - Process 10-20 items per API call
    - Rate limiting with delays
    - Comprehensive error handling
    - Batch mutation templates
    """
    
    def __init__(self, config_file: str = None):
        self.logger = logger_helper.get_logger(__name__)
        self.config = db.load_config()
        
        # Monday.com API configuration
        self.api_url = self.config['monday']['api_url']
        self.api_key = self.config['monday']['api_key']
        self.api_version = self.config['monday']['api_version']
        
        # Load update configuration
        if config_file:
            with open(config_file, 'rb') as f:
                self.update_config = tomli.load(f)
        else:
            self.update_config = {}
            
        self.logger.info("BatchMondayUpdater initialized")
    
    def execute_graphql(self, query: str, variables: dict = None) -> dict:
        """Execute GraphQL query against Monday.com API"""
        
        headers = {
            'Authorization': self.api_key,
            'API-Version': self.api_version,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'query': query
        }
        
        if variables:
            payload['variables'] = variables
        
        self.logger.info(f"Executing GraphQL: {query[:100]}...")
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"API request failed: {response.status_code} - {response.text}")
            
            result = response.json()
            
            if 'errors' in result and result['errors']:
                raise Exception(f"GraphQL errors: {result['errors']}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"ERROR: GraphQL execution failed: {e}")
            raise
    
    def batch_update_from_query(self, query: str, update_config: dict, dry_run: bool = True) -> dict:
        """
        Execute batch updates from SQL query results using Monday.com batch mutations
        
        Args:
            query: SQL query to get update data
            update_config: Configuration for mapping query results to Monday.com updates
            dry_run: If True, only validate without executing
            
        Returns:
            Dict with batch update results
        """
        try:
            # Execute query to get update data
            with db.get_connection('orders') as conn:
                df = pd.read_sql(query, conn)
            
            if df.empty:
                return {
                    'success': True,
                    'message': 'No data found for updates',
                    'total_records': 0
                }
            
            self.logger.info(f"Processing {len(df)} records for batch update")
            
            # Get batch size from config (default to 15)
            batch_size = update_config.get('validation', {}).get('max_batch_size', 15)
            
            # Process in batches
            all_results = []
            total_success = 0
            total_errors = 0
            
            for batch_start in range(0, len(df), batch_size):
                batch_end = min(batch_start + batch_size, len(df))
                batch_df = df.iloc[batch_start:batch_end]
                
                self.logger.info(f"Processing batch {batch_start//batch_size + 1}: records {batch_start+1}-{batch_end}")
                
                # Process this batch
                batch_result = self._process_batch(batch_df, update_config, dry_run)
                all_results.extend(batch_result['results'])
                total_success += batch_result['success_count']
                total_errors += batch_result['error_count']
                
                # Rate limiting - small delay between batches
                if not dry_run and batch_end < len(df):
                    import time
                    time.sleep(0.5)  # 500ms delay between batches
            
            success_rate = (total_success / len(df) * 100) if len(df) > 0 else 0
            
            return {
                'success': True,
                'total_records': len(df),
                'success_count': total_success,
                'error_count': total_errors,
                'success_rate': success_rate,
                'results': all_results,
                'dry_run': dry_run,
                'batches_processed': (len(df) + batch_size - 1) // batch_size
            }
            
        except Exception as e:
            self.logger.error(f"ERROR: Batch update failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_records': 0
            }
    
    def _process_batch(self, batch_df: pd.DataFrame, update_config: dict, dry_run: bool = True) -> dict:
        """
        Process a batch of records - either dry run simulation or actual batch update
        
        Args:
            batch_df: DataFrame with batch of records to update
            update_config: Configuration for mapping
            dry_run: If True, only validate without executing
            
        Returns:
            Dict with batch results
        """
        try:
            # Prepare batch updates
            batch_updates = []
            
            for _, row in batch_df.iterrows():
                try:
                    # Extract update parameters from row based on config
                    if 'metadata' in update_config and 'board_id' in update_config['metadata']:
                        board_id = int(update_config['metadata']['board_id'])
                    else:
                        board_id = int(row['board_id'])  # fallback
                    
                    # Get item_id_column from config
                    item_id_column = update_config.get('item_id_column', 'monday_item_id')
                    item_id = int(row[item_id_column])
                    
                    # Build column updates from mapping
                    column_updates = {}
                    for monday_column_id, source_column in update_config['column_mapping'].items():
                        if source_column in row and pd.notna(row[source_column]):
                            column_updates[monday_column_id] = str(row[source_column])
                    
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
            
            if not batch_updates:
                return {
                    'success_count': 0,
                    'error_count': len(batch_df),
                    'results': [{'success': False, 'error': 'No valid updates in batch'}]
                }
            
            # Execute batch update
            if dry_run:
                return self._simulate_batch_dry_run(batch_updates)
            else:
                return self._execute_true_batch_mutation(batch_updates)
                
        except Exception as e:
            self.logger.error(f"ERROR: Batch processing failed: {e}")
            return {
                'success_count': 0,
                'error_count': len(batch_df),
                'results': [{'success': False, 'error': str(e)}]
            }
    
    def _simulate_batch_dry_run(self, batch_updates: list) -> dict:
        """Simulate batch updates for dry run"""
        results = []
        for update in batch_updates:
            self.logger.info(f"DRY RUN: Batch update item {update['item_id']} with {len(update['column_updates'])} fields")
            results.append({
                'success': True,
                'dry_run': True,
                'board_id': update['board_id'],
                'item_id': update['item_id'],
                'updates': update['column_updates'],
                'message': 'Dry run successful - no changes made'
            })
        
        return {
            'success_count': len(results),
            'error_count': 0,
            'results': results
        }
    
    def _execute_true_batch_mutation(self, batch_updates: list) -> dict:
        """Execute true batch mutation - multiple items in ONE API call"""
        try:
            # Build batch GraphQL mutation
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
            
            self.logger.info(f"Executing TRUE BATCH mutation for {len(batch_updates)} items in ONE API call")
            
            # Execute single batch mutation
            result = self.execute_graphql(batch_query, variables)
            
            # Process batch results
            return self._process_batch_response(result, batch_updates)
            
        except Exception as e:
            self.logger.error(f"ERROR: True batch mutation failed: {e}")
            # Fallback to individual updates if batch fails
            self.logger.info("Falling back to individual updates...")
            return self._execute_individual_updates_with_delay(batch_updates)
    
    def _process_batch_response(self, response: dict, batch_updates: list) -> dict:
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
                    self.logger.info(f"SUCCESS: Batch updated item {update['item_id']}")
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
    
    def _execute_individual_updates_with_delay(self, batch_updates: list) -> dict:
        """Execute individual updates with rate limiting (fallback approach)"""
        results = []
        success_count = 0
        error_count = 0
        
        # Load single update template
        template_path = repo_root / "sql" / "graphql" / "mutations" / "update_item.graphql"
        with open(template_path, 'r') as f:
            update_query = f.read()
        
        for update in batch_updates:
            try:
                variables = {
                    'boardId': str(update['board_id']),
                    'itemId': str(update['item_id']),
                    'columnValues': json.dumps(update['column_updates'])
                }
                
                result = self.execute_graphql(update_query, variables)
                
                results.append({
                    'success': True,
                    'dry_run': False,
                    'board_id': update['board_id'],
                    'item_id': update['item_id'],
                    'updates': update['column_updates'],
                    'monday_response': result,
                    'updated_at': datetime.now().isoformat()
                })
                success_count += 1
                self.logger.info(f"SUCCESS: Updated item {update['item_id']}")
                
                # Rate limiting between individual calls
                import time
                time.sleep(0.1)  # 100ms delay between individual updates
                
            except Exception as e:
                self.logger.error(f"ERROR: Failed to update item {update['item_id']}: {e}")
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

def main():
    parser = argparse.ArgumentParser(description="Batch Monday.com Update Script")
    parser.add_argument('--config', type=str, required=True, help='TOML config file for batch updates')
    parser.add_argument('--dry_run', action='store_true', default=True, help='Dry run mode (default: True)')
    parser.add_argument('--execute', action='store_true', help='Execute updates (overrides dry_run)')
    
    args = parser.parse_args()
    
    # Override dry_run if execute is specified
    dry_run = not args.execute
    
    updater = BatchMondayUpdater(args.config)
    
    # Batch update from TOML config
    if 'query_config' in updater.update_config:
        query = updater.load_query_from_config(updater.update_config['query_config'])
        result = updater.batch_update_from_query(query, updater.update_config, dry_run)
        self.logger.info(json.dumps(result, indent=2))
    else:
        self.logger.info("ERROR: No query found in TOML config file")

if __name__ == "__main__":
    main()
