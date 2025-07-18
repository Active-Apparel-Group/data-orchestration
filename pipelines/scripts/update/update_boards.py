"""
OPUS Universal Monday.com Update Script
Purpose: Standalone script for immediate Monday.com updates
Author: CTO / Head Data Engineer
Date: 2025-06-30

URGENT DEADLINE SOLUTION:
- Direct Monday.com updates without staging dependencies
- TOML-based configuration for rapid deployment
- Supports both items and subitems
- Uses existing infrastructure and metadata
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

class UniversalMondayUpdater:
    """
    Universal Monday.com update handler for urgent deployment
    
    Features:
    - Direct API updates (no staging delay)
    - TOML configuration
    - Metadata-driven mapping
    - GraphQL template system
    - Comprehensive error handling
    - Country column type detection and formatting
    """
    
    def __init__(self, config_file: str = None):
        self.logger = logger_helper.get_logger(__name__)
        self.config = db.load_config()
        
        # Use consistent configuration pattern like other Monday scripts
        self.api_token = os.getenv('MONDAY_API_KEY') or self.config.get('apis', {}).get('monday', {}).get('api_token')
        self.api_version = self.config.get('apis', {}).get('monday', {}).get('api_version', '2025-04')
        self.api_url = self.config.get('apis', {}).get('monday', {}).get('api_url', 'https://api.monday.com/v2')
        
        if not self.api_token:
            raise ValueError("Monday.com API token not configured. Please set MONDAY_API_KEY environment variable or update utils/config.yaml")
        
        # Load TOML config if provided
        if config_file and Path(config_file).exists():
            with open(config_file, 'rb') as f:
                self.update_config = tomli.load(f)
        else:
            self.update_config = {}
            
        self.logger.info("UniversalMondayUpdater initialized")
    
    def format_country_value(self, country_name: str) -> dict:
        """
        Format country value for Monday.com country column type.
        
        Args:
            country_name: Country name (e.g., "Cambodia")
            
        Returns:
            Dict with countryCode and countryName for Monday.com API
        """
        return format_country_for_monday(country_name, self.logger)
    
    def detect_column_type(self, column_id: str, board_metadata: dict) -> str:
        """
        Detect Monday.com column type from board metadata.
        
        Args:
            column_id: Monday.com column ID
            board_metadata: Board metadata dict
            
        Returns:
            Column type string (e.g., 'country', 'text', 'date', etc.)
        """
        columns = board_metadata.get('columns', [])
        for column in columns:
            if column.get('monday_id') == column_id:
                return column.get('monday_type', 'text')
        return 'text'  # Default fallback
    
    def format_column_value(self, column_id: str, value: any, board_metadata: dict) -> any:
        """
        Format column value based on Monday.com column type.
        
        Args:
            column_id: Monday.com column ID
            value: Raw value to format
            board_metadata: Board metadata dict
            
        Returns:
            Properly formatted value for Monday.com API
        """
        if pd.isna(value) or value is None:
            return None
            
        column_type = self.detect_column_type(column_id, board_metadata)
        
        # Handle country columns specifically
        if column_type == 'country':
            return self.format_country_value(value)
        
        # For other types, return as string (existing behavior)
        return str(value)
    
    def load_graphql_template(self, template_name: str) -> str:
        """Load GraphQL template from sql/graphql/mutations/"""
        # Get repo root from current location (must have utils folder)
        current = Path(__file__).parent
        while current != current.parent:
            if (current / "utils").exists():
                repo_root = current
                break
            current = current.parent
        else:
            raise FileNotFoundError("Could not find repository root (needs utils folder)")
            
        template_path = repo_root / "sql" / "graphql" / "mutations" / f"{template_name}.graphql"
        
        if not template_path.exists():
            raise FileNotFoundError(f"GraphQL template not found: {template_path}")
            
        with open(template_path, 'r') as f:
            return f.read()
    
    def load_board_metadata(self, board_id: int) -> dict:
        """Load board metadata from configs/boards/"""
        # Get repo root from current location (must have both utils and integrations)
        current = Path(__file__).parent
        while current != current.parent:
            if (current / "utils").exists() and (current / "integrations").exists():
                repo_root = current
                break
            current = current.parent
        else:
            raise FileNotFoundError("Could not find repository root (needs both utils and integrations folders)")
            
        metadata_path = repo_root / "configs" / "boards" / f"board_{board_id}_metadata.json"
        
        if not metadata_path.exists():
            raise FileNotFoundError(f"Board metadata not found: {metadata_path}")
            
        with open(metadata_path, 'r') as f:
            return json.load(f)
    
    def execute_graphql(self, query: str, variables: dict) -> dict:
        """Execute GraphQL mutation against Monday.com API"""
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "API-Version": self.api_version,
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": query,
            "variables": variables
        }
        
        self.logger.info(f"Executing GraphQL: {query[:100]}...")
        self.logger.debug(f"Variables: {variables}")
        
        response = requests.post(self.api_url, json=payload, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
            
        result = response.json()
        
        if 'errors' in result:
            raise Exception(f"GraphQL errors: {result['errors']}")
            
        return result
    
    def update_item(self, board_id: int, item_id: int, column_updates: dict, dry_run: bool = True) -> dict:
        """
        Update Monday.com item
        
        Args:
            board_id: Monday.com board ID
            item_id: Monday.com item ID  
            column_updates: Dict of column_id -> new_value
            dry_run: If True, only validate without executing
            
        Returns:
            Dict with update results
        """
        try:
            # Load resources
            query = self.load_graphql_template("update_item")
            metadata = self.load_board_metadata(board_id)
            
            # Prepare column values JSON
            column_values = json.dumps(column_updates)
            
            variables = {
                "boardId": str(board_id),
                "itemId": str(item_id),
                "columnValues": column_values
            }
            
            if dry_run:
                self.logger.info("DRY RUN: Update item operation")
                self.logger.info(f"Board: {board_id}, Item: {item_id}")
                self.logger.info(f"Updates: {column_updates}")
                return {
                    'success': True,
                    'dry_run': True,
                    'board_id': board_id,
                    'item_id': item_id,
                    'updates': column_updates,
                    'message': 'Dry run successful - no changes made'
                }
            
            # Execute update
            result = self.execute_graphql(query, variables)
            
            self.logger.info(f"SUCCESS: Updated item {item_id} on board {board_id}")
            return {
                'success': True,
                'dry_run': False,
                'board_id': board_id,
                'item_id': item_id,
                'updates': column_updates,
                'monday_response': result,
                'updated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"ERROR: Failed to update item: {e}")
            return {
                'success': False,
                'error': str(e),
                'board_id': board_id,
                'item_id': item_id,
                'updates': column_updates
            }
    
    def update_subitem(self, board_id: int, item_id: int, subitem_id: int, column_updates: dict, dry_run: bool = True) -> dict:
        """
        Update Monday.com subitem
        
        Args:
            board_id: Monday.com board ID
            item_id: Parent Monday.com item ID
            subitem_id: Monday.com subitem ID
            column_updates: Dict of column_id -> new_value
            dry_run: If True, only validate without executing
            
        Returns:
            Dict with update results
        """
        try:
            # Load resources
            query = self.load_graphql_template("update_subitem")
            metadata = self.load_board_metadata(board_id)
            
            # Prepare column values JSON
            column_values = json.dumps(column_updates)
            
            variables = {
                "itemId": str(item_id),
                "subitemId": str(subitem_id),
                "columnValues": column_values
            }
            
            if dry_run:
                self.logger.info("DRY RUN: Update subitem operation")
                self.logger.info(f"Board: {board_id}, Item: {item_id}, Subitem: {subitem_id}")
                self.logger.info(f"Updates: {column_updates}")
                return {
                    'success': True,
                    'dry_run': True,
                    'board_id': board_id,
                    'item_id': item_id,
                    'subitem_id': subitem_id,
                    'updates': column_updates,
                    'message': 'Dry run successful - no changes made'
                }
            
            # Execute update
            result = self.execute_graphql(query, variables)
            
            self.logger.info(f"SUCCESS: Updated subitem {subitem_id} on item {item_id}, board {board_id}")
            return {
                'success': True,
                'dry_run': False,
                'board_id': board_id,
                'item_id': item_id,
                'subitem_id': subitem_id,
                'updates': column_updates,
                'monday_response': result,
                'updated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"ERROR: Failed to update subitem: {e}")
            return {
                'success': False,
                'error': str(e),
                'board_id': board_id,
                'item_id': item_id,
                'subitem_id': subitem_id,
                'updates': column_updates
            }
    
    def batch_update_from_query(self, query: str, update_config: dict, dry_run: bool = True) -> dict:
        """
        Execute batch updates from SQL query results
        
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
                import pandas as pd
                df = pd.read_sql(query, conn)
            
            if df.empty:
                return {
                    'success': True,
                    'message': 'No data found for updates',
                    'total_records': 0
                }
            
            self.logger.info(f"Processing {len(df)} records for batch update")
            
            # Get batch size from config (default to 10)
            batch_size = update_config.get('validation', {}).get('max_batch_size', 10)
            
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
            
            success_rate = (total_success / len(df) * 100) if len(df) > 0 else 0
            
            return {
                'success': True,
                'total_records': len(df),
                'success_count': total_success,
                'error_count': total_errors,
                'success_rate': success_rate,
                'results': all_results,
                'dry_run': dry_run
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
        Process a batch of records using Monday.com batch mutation
        
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
                    elif 'board_id' in update_config:
                        board_id = int(update_config['board_id'])
                    elif 'board_id_column' in update_config:
                        board_id = int(row[update_config['board_id_column']])
                    else:
                        board_id = int(row['board_id'])  # fallback
                    
                    # Get item_id_column from config
                    item_id_column = update_config.get('item_id_column') or update_config.get('query_config', {}).get('item_id_column', 'monday_item_id')
                    item_id = int(row[item_id_column])
                    
                    # Build column updates from mapping with column type detection
                    column_updates = {}
                    metadata = self.load_board_metadata(board_id)  # Load metadata for column type detection
                    
                    for monday_column_id, source_column in update_config['column_mapping'].items():
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
                return self._execute_batch_mutations(batch_updates)
                
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
    
    def _execute_batch_mutations(self, batch_updates: list) -> dict:
        """Execute actual batch mutations to Monday.com"""
        try:
            # Create batch GraphQL mutation
            batch_query = self._build_batch_mutation_query(batch_updates)
            variables = self._build_batch_variables(batch_updates)
            
            self.logger.info(f"Executing batch mutation for {len(batch_updates)} items")
            
            # Execute the batch mutation
            result = self.execute_graphql(batch_query, variables)
            
            # Process batch results
            return self._process_batch_response(result, batch_updates)
            
        except Exception as e:
            self.logger.error(f"ERROR: Batch mutation execution failed: {e}")
            # Return individual errors for each update
            error_results = []
            for update in batch_updates:
                error_results.append({
                    'success': False,
                    'error': str(e),
                    'board_id': update['board_id'],
                    'item_id': update['item_id'],
                    'updates': update['column_updates']
                })
            
            return {
                'success_count': 0,
                'error_count': len(batch_updates),
                'results': error_results
            }
    
    def _build_batch_mutation_query(self, batch_updates: list) -> str:
        """Build GraphQL mutation for batch updates"""
        mutations = []
        
        for i, update in enumerate(batch_updates):
            mutation_alias = f"update_{i}"
            mutations.append(f"""
            {mutation_alias}: change_multiple_column_values(
                board_id: $boardId_{i},
                item_id: $itemId_{i},
                column_values: $columnValues_{i}
            ) {{
                id
                name
                updated_at
            }}""")
        
        batch_query = f"""
        mutation BatchUpdateItems({self._build_batch_variable_definitions(batch_updates)}) {{
            {chr(10).join(mutations)}
        }}
        """
        
        return batch_query
    
    def _build_batch_variable_definitions(self, batch_updates: list) -> str:
        """Build variable definitions for batch mutation"""
        definitions = []
        
        for i in range(len(batch_updates)):
            definitions.extend([
                f"$boardId_{i}: ID!",
                f"$itemId_{i}: ID!",
                f"$columnValues_{i}: JSON!"
            ])
        
        return ", ".join(definitions)
    
    def _build_batch_variables(self, batch_updates: list) -> dict:
        """Build variables dictionary for batch mutation"""
        variables = {}
        
        for i, update in enumerate(batch_updates):
            variables[f"boardId_{i}"] = str(update['board_id'])
            variables[f"itemId_{i}"] = str(update['item_id'])
            variables[f"columnValues_{i}"] = json.dumps(update['column_updates'])
        
        return variables
    
    def _process_batch_response(self, response: dict, batch_updates: list) -> dict:
        """Process the response from batch mutation"""
        results = []
        success_count = 0
        error_count = 0
        
        if 'data' in response:
            for i, update in enumerate(batch_updates):
                mutation_alias = f"update_{i}"
                
                if mutation_alias in response['data'] and response['data'][mutation_alias]:
                    # Success
                    update_result = response['data'][mutation_alias]
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
                        'error': f"No response data for {mutation_alias}",
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

def main():
    import logger_helper
    logger = logger_helper.get_logger(__name__)
    
    parser = argparse.ArgumentParser(description="Universal Monday.com Update Script")
    parser.add_argument('--board_id', type=int, help='Monday.com board ID (optional if in config)')
    parser.add_argument('--item_id', type=int, help='Monday.com item ID (for single item update)')
    parser.add_argument('--subitem_id', type=int, help='Monday.com subitem ID (for subitem update)')
    parser.add_argument('--column_updates', type=str, help='JSON string of column updates')
    parser.add_argument('--config', type=str, help='TOML config file for batch updates')
    parser.add_argument('--query', type=str, help='SQL query for batch updates')
    parser.add_argument('--dry_run', action='store_true', default=True, help='Dry run mode (default: True)')
    parser.add_argument('--execute', action='store_true', help='Execute updates (overrides dry_run)')
    
    args = parser.parse_args()
    
    # Override dry_run if execute is specified
    dry_run = not args.execute
    
    updater = UniversalMondayUpdater(args.config)
    
    # Get board_id from args or config
    board_id = args.board_id
    if not board_id and 'metadata' in updater.update_config:
        board_id = updater.update_config['metadata'].get('board_id')
    
    if not board_id:
        logger.error("ERROR: board_id required either as argument or in config file")
        parser.print_help()
        return
    
    if args.item_id and args.column_updates:
        # Single item/subitem update
        column_updates = json.loads(args.column_updates)
        
        if args.subitem_id:
            result = updater.update_subitem(board_id, args.item_id, args.subitem_id, column_updates, dry_run)
        else:
            result = updater.update_item(board_id, args.item_id, column_updates, dry_run)
            
        logger.info(json.dumps(result, indent=2))
        
    elif args.config:
        # Batch update from TOML config
        if 'query_config' in updater.update_config and 'query' in updater.update_config['query_config']:
            query = updater.update_config['query_config']['query']
            result = updater.batch_update_from_query(query, updater.update_config, dry_run)
            logger.info(json.dumps(result, indent=2))
        else:
            logger.error("ERROR: No query found in TOML config file")
            
    elif args.query and args.config:
        # Batch update from query parameter
        result = updater.batch_update_from_query(args.query, updater.update_config, dry_run)
        logger.info(json.dumps(result, indent=2))
        
    else:
        parser.print_help()
        logger.info("\nExamples:")
        logger.info("  # Single item update (dry run)")
        logger.info('  python scripts/universal_monday_update.py --board_id 8709134353 --item_id 123456 --column_updates \'{"status": "Done"}\'')
        logger.info('')
        logger.info("  # Execute single item update")
        logger.info('  python scripts/universal_monday_update.py --board_id 8709134353 --item_id 123456 --column_updates \'{"status": "Done"}\' --execute')
        logger.info('')
        logger.info("  # Batch update from config")
        logger.info("  python scripts/universal_monday_update.py --config planning_update_fob.toml --execute")

if __name__ == "__main__":
    main()
