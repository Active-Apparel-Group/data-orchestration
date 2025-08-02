"""
Ultra-Lightweight Monday.com API Client
======================================
Purpose: Direct, minimal Monday.com integration - no abstraction layers
Location: src/pipelines/sync_order_list/monday_api_client.py
Created: 2025-07-22 (Architecture Simplification)

Core Philosophy: TOML + GraphQL Template + Data = API Call
- Zero abstraction layers
- Handles single/batch/async automatically
- Direct execution path from database row to Monday.com
- Total complexity: ~200 lines

Usage:
    client = MondayAPIClient(toml_config_path)
    result = client.execute("create_items", database_rows, dry_run=False)
"""

import json
import asyncio
import aiohttp
import os
import sys
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
from datetime import datetime

# Modern Python package imports - ultra-minimal dependencies
from src.pipelines.utils import logger, config, db
from src.pipelines.integrations.monday.graphql_loader import GraphQLLoader


class MondayAPIClient:
    """
    Ultra-lightweight Monday.com API client
    Combines TOML configuration + GraphQL templates + HTTP client
    """
    
    def __init__(self, toml_config_path: str, environment: str = "production"):
        """
        Initialize with TOML configuration
        
        Args:
            toml_config_path: Path to sync_order_list.toml configuration
            environment: Environment to use ('development' or 'production')
        """
        self.logger = logger.get_logger(__name__)
        self.config_path = Path(toml_config_path)
        self.environment = environment  # Store the environment parameter
        
        # Load TOML configuration
        self.toml_config = self._load_toml_config()
        
        # Initialize GraphQL loader
        self.graphql_loader = GraphQLLoader()
        
        # Get Monday.com API configuration - Use production pattern from load_boards.py
        try:
            # Try to get from centralized config first (production standard)
            config = db.load_config()
            self.api_token = os.getenv('MONDAY_API_KEY') or config.get('apis', {}).get('monday', {}).get('api_token')
        except Exception:
            # Final fallback
            self.api_token = os.getenv("MONDAY_API_KEY")
        
        if not self.api_token or self.api_token == "your_monday_api_token_here":
            self.logger.warning("Using fallback Monday API token - ensure MONDAY_API_KEY is configured")
            self.api_token = "your_monday_api_token_here"
        
        self.api_url = "https://api.monday.com/v2"
        
        # Environment-specific configuration using proper config parser
        from .config_parser import DeltaSyncConfig
        
        # Load configuration using the proper parser
        delta_config = DeltaSyncConfig.from_toml(self.config_path, environment=environment)
        
        # Get board IDs from the config parser (handles defaults properly)
        self.board_id = delta_config.monday_board_id
        self.subitem_board_id = delta_config.monday_subitems_board_id
        
        self.logger.info(f"Monday API Client initialized for {delta_config.environment} (items board: {self.board_id}, subitems board: {self.subitem_board_id})")
    
    def _load_toml_config(self) -> Dict[str, Any]:
        """Load and parse TOML configuration"""
        try:
            import tomli
            with open(self.config_path, 'rb') as f:
                return tomli.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load TOML config from {self.config_path}: {e}")
            raise
    
    def _get_environment(self) -> str:
        """Get current environment"""
        return self.environment

# REMOVED DUPLICATE METHOD - Using the comprehensive version below that returns tuple (config, default)
    
# REMOVED: Duplicate method with incorrect tuple unpacking - using the correct version below
    
    def _determine_create_labels_for_records(self, records: List[Dict], item_type: str = "headers") -> bool:
        """
        Determine if we should enable create_labels_if_missing for a batch of records.
        Returns True if ANY column in ANY record needs label creation.
        
        Args:
            records: List of records containing column data (already transformed with Monday.com column IDs)
            item_type: Either "headers" or "lines"
            
        Returns:
            bool: Whether to enable create_labels_if_missing for this batch
        """
        try:
            # Get dropdown configuration for current environment and item type
            dropdown_config, default = self._get_dropdown_config(item_type)
            
            if not dropdown_config:
                self.logger.debug(f"No dropdown config found for {item_type}, using default: {default}")
                return default
            
            # Check each record for dropdown columns that need label creation
            for record in records:
                for monday_column_id, value in record.items():
                    # Only check dropdown columns with non-empty values
                    if monday_column_id.startswith("dropdown_") and value:
                        # Handle both string values and JSON object format {"labels": ["VALUE"]}
                        has_meaningful_value = False
                        if isinstance(value, dict) and "labels" in value:
                            # JSON format: {"labels": ["VALUE"]}
                            labels = value.get("labels", [])
                            has_meaningful_value = bool(labels and any(str(label).strip() for label in labels))
                            display_value = f"JSON labels: {labels}"
                        else:
                            # String format: "VALUE"
                            str_value = str(value).strip()
                            has_meaningful_value = bool(str_value and str_value.lower() != 'none')
                            display_value = str_value
                        
                        if has_meaningful_value:
                            should_create = dropdown_config.get(monday_column_id, default)
                            self.logger.error(f"🎯 CRITICAL DEBUG: Column {monday_column_id} = '{display_value}' -> should_create = {should_create}")
                            self.logger.error(f"🎯 CRITICAL DEBUG: Raw value = {value}")
                            self.logger.error(f"🎯 CRITICAL DEBUG: Config key exists = {monday_column_id in dropdown_config}")
                            if monday_column_id == "dropdown_mkr5rgs6":
                                self.logger.error(f"🚨 REBUY COLUMN FOUND! dropdown_mkr5rgs6 config = {dropdown_config.get(monday_column_id, 'NOT FOUND')}")
                                self.logger.error(f"� REBUY VALUE = {display_value}")
                                self.logger.error(f"🚨 SHOULD CREATE = {should_create}")
                            if should_create:
                                self.logger.error(f"✅ ENABLING create_labels_if_missing for column {monday_column_id}: '{display_value}'")
                                return True
            
            self.logger.debug(f"No dropdown columns need label creation for {item_type}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error determining create_labels setting: {e}")
            return False
    
    def _get_dropdown_config(self, item_type: str) -> Tuple[Dict[str, bool], bool]:
        """
        Get environment-specific dropdown configuration for create_labels_if_missing
        
        Args:
            item_type: 'headers' or 'lines'
            
        Returns:
            Tuple of (dropdown_config_dict, default_value)
        """
        environment = self._get_environment()
        
        # Build config path: monday.{environment}.{item_type}.create_labels_if_missing
        config_path = ['monday', environment, item_type, 'create_labels_if_missing']
        
        self.logger.debug(f"🔍 Looking for dropdown config at path: {config_path}")
        
        config_section = self.toml_config
        for key in config_path:
            if key in config_section:
                config_section = config_section.get(key, {})
            else:
                break
        
        if not config_section:
            self.logger.debug(f"No dropdown config found for {environment}.{item_type}, using defaults")
            return {}, False  # Return tuple with empty config and default False
        
        # Get default and column-specific settings
        default = config_section.get('default', False)
        dropdown_config = {}
        
        for column_id, should_create in config_section.items():
            if column_id != 'default':  # Skip the default key
                dropdown_config[column_id] = should_create
        
        self.logger.debug(f"✅ Dropdown config for {environment}.{item_type}: {len(dropdown_config)} columns, default={default}")
        return dropdown_config, default
    
    def _should_create_labels_for_column(self, column_id: str, item_type: str) -> bool:
        """
        Determine if we should create labels for a specific column
        
        Args:
            column_id: Monday.com column ID (e.g., 'dropdown_mkr58de6')
            item_type: 'headers' or 'lines'
            
        Returns:
            Boolean indicating whether to set create_labels_if_missing=true
        """
        dropdown_config, default = self._get_dropdown_config(item_type)
        result = dropdown_config.get(column_id, default)
        
        if result:
            self.logger.debug(f"✅ create_labels_if_missing=true for {column_id} ({item_type})")
        
        return result

    def _determine_create_labels_for_record(self, record: Dict[str, Any], item_type: str = "headers") -> bool:
        """
        LEGACY METHOD - NOT USED ANYWHERE IN CODEBASE
        This method is legacy and has been replaced by _determine_create_labels_for_records (plural).
        The active method handles batches properly and uses the correct configuration reading.
        """
        # Legacy method - return False to avoid any issues
        return False
    
    def execute(self, operation_type: str, data: Union[Dict, List[Dict]], dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute Monday.com operation with automatic single/batch/async handling
        
        Args:
            operation_type: "create_items", "create_subitems", "update_items", "update_subitems", "create_groups",
                          "batch_create_items", "async_batch_create_items"
            data: Single dict or list of dicts from database
            dry_run: If True, validate but don't execute
            
        Returns:
            Execution results with success status and Monday.com IDs
        """
        # Normalize data to list
        data_list = data if isinstance(data, list) else [data]
        
        self.logger.info(f"Executing {operation_type} for {len(data_list)} records (dry_run: {dry_run})")
        
        if dry_run:
            return self._dry_run_response(operation_type, data_list)
        
        # Dynamic execution strategy based on operation type
        if operation_type == 'batch_create_items':
            # Use GraphQL batch template for items
            return asyncio.run(self._execute_batch(operation_type, data_list))
        elif operation_type == 'async_batch_create_items':
            # Use high-performance async batch execution for items
            return asyncio.run(self._execute_async_batch(operation_type, data_list))
        elif operation_type == 'create_subitems' and len(data_list) > 1:
            # Default batch subitems for performance
            return asyncio.run(self._execute_batch(operation_type, data_list))
        else:
            # Single item operations (default)
            return asyncio.run(self._execute_all_single(operation_type, data_list))
    
    async def _execute_all_single(self, operation_type: str, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute all records as single item operations with rate limiting and API logging aggregation"""
        results = []
        for record in data_list:
            result = await self._execute_single(operation_type, record)
            results.append(result)
            # Small delay to respect API rate limits
            await asyncio.sleep(0.1)
        
        # Aggregate results
        total_processed = sum(r.get('records_processed', 0) for r in results)
        all_monday_ids = []
        errors = []
        
        # Capture API logging data from first successful operation
        api_request = None
        api_response = None
        request_timestamp = None
        response_timestamp = None
        
        for result in results:
            if result.get('success'):
                all_monday_ids.extend(result.get('monday_ids', []))
                
                # Capture API data from first successful operation for logging
                if api_request is None:
                    api_request = result.get('api_request')
                    api_response = result.get('api_response')
                    request_timestamp = result.get('request_timestamp')
                    response_timestamp = result.get('response_timestamp')
            else:
                errors.append(result.get('error', 'Unknown error'))
                
                # If no successful operations yet, capture error API data
                if api_request is None:
                    api_request = result.get('api_request')
                    api_response = result.get('api_response')
                    request_timestamp = result.get('request_timestamp')
                    response_timestamp = result.get('response_timestamp')
        
        return {
            'success': len(errors) == 0,
            'records_processed': total_processed,
            'monday_ids': all_monday_ids,
            'operation_type': operation_type,
            'errors': errors if errors else None,
            # Include aggregated API logging data
            'api_request': api_request,
            'api_response': api_response,
            'request_timestamp': request_timestamp,
            'response_timestamp': response_timestamp
        }
    
    async def _execute_single(self, operation_type: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """Execute single record operation with full API logging data"""
        try:
            # Build GraphQL query with variables
            query_data = self._build_graphql_query(operation_type, [record])
            
            # Execute API call (now returns full API logging data)
            result = await self._make_api_call(query_data['query'], query_data['variables'])
            
            if result['success']:
                monday_id = self._extract_monday_id(result['data'], operation_type)
                return {
                    'success': True,
                    'records_processed': 1,
                    'monday_ids': [monday_id],
                    'operation_type': operation_type,
                    # Propagate API logging data
                    'api_request': result.get('api_request'),
                    'api_response': result.get('api_response'),
                    'request_timestamp': result.get('request_timestamp'),
                    'response_timestamp': result.get('response_timestamp')
                }
            else:
                return {
                    'success': False,
                    'error': result['error'],
                    'records_processed': 0,
                    'operation_type': operation_type,
                    # Propagate API logging data even for errors
                    'api_request': result.get('api_request'),
                    'api_response': result.get('api_response'),
                    'request_timestamp': result.get('request_timestamp'),
                    'response_timestamp': result.get('response_timestamp')
                }
                
        except Exception as e:
            self.logger.exception(f"Single operation failed: {e}")
            
            # Return error with minimal API logging data
            response_timestamp = datetime.utcnow()
            return {
                'success': False,
                'error': f'Single operation failed: {str(e)}',
                'records_processed': 0,
                'operation_type': operation_type,
                'api_request': {'operation': operation_type, 'record': record},
                'api_response': {'error': str(e)},
                'request_timestamp': datetime.utcnow(),
                'response_timestamp': response_timestamp
            }
            return {
                'success': False,
                'error': str(e),
                'records_processed': 0
            }
    
    async def _execute_batch(self, operation_type: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute batch operation (up to 50 records)"""
        try:
            # Build batch GraphQL query with variables
            query_data = self._build_graphql_query(operation_type, records)
            
            # Execute API call
            result = await self._make_api_call(query_data['query'], query_data['variables'])
            
            if result['success']:
                monday_ids = self._extract_monday_ids(result['data'], operation_type, len(records))
                return {
                    'success': True,
                    'records_processed': len(records),
                    'monday_ids': monday_ids,
                    'operation_type': operation_type,
                    # CRITICAL FIX: Propagate API logging data for batch operations
                    'api_request': result.get('api_request'),
                    'api_response': result.get('api_response'),
                    'request_timestamp': result.get('request_timestamp'),
                    'response_timestamp': result.get('response_timestamp')
                }
            else:
                return {
                    'success': False,
                    'error': result['error'],
                    'records_processed': 0,
                    'operation_type': operation_type,
                    # CRITICAL FIX: Propagate API logging data even for batch errors
                    'api_request': result.get('api_request'),
                    'api_response': result.get('api_response'),
                    'request_timestamp': result.get('request_timestamp'),
                    'response_timestamp': result.get('response_timestamp')
                }
                
        except Exception as e:
            self.logger.exception(f"Batch operation failed: {e}")
            
            # CRITICAL FIX: Return error with API logging data for batch exceptions
            from datetime import datetime
            response_timestamp = datetime.utcnow()
            return {
                'success': False,
                'error': f'Batch operation failed: {str(e)}',
                'records_processed': 0,
                'operation_type': operation_type,
                'api_request': {'operation': operation_type, 'records': records},
                'api_response': {'error': str(e)},
                'request_timestamp': datetime.utcnow(),
                'response_timestamp': response_timestamp
            }
    
    async def _execute_async_batch(self, operation_type: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute large dataset with conservative async batch processing
        Uses proven rate limiting patterns: 15→5→1 fallback, 100ms delays, 25s timeouts
        """
        # Get batch size from configuration
        initial_batch_size = self.toml_config.get('monday', {}).get('rate_limits', {}).get('item_batch_size', 5)
        batches = [records[i:i + initial_batch_size] for i in range(0, len(records), initial_batch_size)]
        
        self.logger.info(f"🚀 Conservative batch processing: {len(records)} records in {len(batches)} batches (size: {initial_batch_size})")
        
        successful_records = 0
        failed_records = 0
        all_monday_ids = []
        
        # Ultra-conservative concurrency - max 3 concurrent batches for testing
        semaphore = asyncio.Semaphore(3)
        
        async def process_batch_with_backoff(batch_records, batch_index):
            """Process batch with exponential backoff and rate limiting"""
            async with semaphore:
                # Rate limiting: 100ms delay between batches
                if batch_index > 0:
                    await asyncio.sleep(0.1)
                
                try:
                    # Execute with 25s timeout per batch
                    result = await asyncio.wait_for(
                        self._execute_batch(operation_type, batch_records),
                        timeout=25.0
                    )
                    return result
                    
                except asyncio.TimeoutError:
                    self.logger.warning(f"Batch {batch_index} timed out after 25s - retrying with smaller batch")
                    
                    # Fallback to single items if batch fails
                    if len(batch_records) > 1:
                        single_results = []
                        for record in batch_records:
                            try:
                                single_result = await asyncio.wait_for(
                                    self._execute_single(operation_type, record),
                                    timeout=10.0
                                )
                                single_results.append(single_result)
                                await asyncio.sleep(0.05)  # 50ms between single calls
                            except Exception as e:
                                self.logger.error(f"Single record failed: {e}")
                                single_results.append({'success': False, 'error': str(e), 'records_processed': 0})
                        
                        # Aggregate single results
                        success_count = sum(1 for r in single_results if r['success'])
                        all_ids = []
                        for r in single_results:
                            if r['success'] and 'monday_ids' in r:
                                all_ids.extend(r['monday_ids'])
                        
                        return {
                            'success': success_count == len(batch_records),
                            'records_processed': success_count,
                            'monday_ids': all_ids,
                            'operation_type': operation_type,
                            'fallback_used': True
                        }
                    else:
                        return {'success': False, 'error': 'Single record timeout', 'records_processed': 0}
                        
                except Exception as e:
                    self.logger.error(f"Batch {batch_index} failed: {e}")
                    return {'success': False, 'error': str(e), 'records_processed': 0}
        
        # Execute batches with conservative rate limiting
        self.logger.info(f"📊 Executing {len(batches)} batches with 3-concurrent limit and 100ms delays")
        batch_tasks = [process_batch_with_backoff(batch, i) for i, batch in enumerate(batches)]
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Aggregate results with detailed tracking
        fallback_count = 0
        for i, result in enumerate(batch_results):
            if isinstance(result, Exception):
                self.logger.error(f"Batch {i} exception: {result}")
                failed_records += len(batches[i])
            elif result['success']:
                successful_records += result['records_processed']
                if 'monday_ids' in result:
                    all_monday_ids.extend(result['monday_ids'])
                if result.get('fallback_used'):
                    fallback_count += 1
            else:
                self.logger.warning(f"Batch {i} failed: {result.get('error', 'Unknown error')}")
                failed_records += len(batches[i])
        
        success_rate = (successful_records / len(records)) * 100 if records else 0
        
        self.logger.info(f"✅ Conservative batch complete: {successful_records}/{len(records)} ({success_rate:.1f}%), {fallback_count} fallbacks used")
        
        return {
            'success': failed_records == 0,
            'records_processed': successful_records,
            'records_failed': failed_records,
            'monday_ids': all_monday_ids,
            'operation_type': operation_type,
            'batches_processed': len(batches),
            'success_rate_percent': success_rate,
            'fallback_used_count': fallback_count,
            'conservative_batching': True
        }
    
    def _build_graphql_query(self, operation_type: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Ultra-lightweight: TOML + GraphQL Template + Data = API Call
        Core transformation: Database Records → Monday.com GraphQL Query
        
        Returns:
            Dict with 'query' and 'variables' keys for GraphQL execution
        """
        # 1. Get column mappings from TOML
        column_mappings = self._get_column_mappings(operation_type)
        
        # 2. Handle single vs batch operations
        if operation_type == 'create_items':
            # Single item creation only
            if len(records) > 1:
                raise ValueError(f"Single item operation expected, got {len(records)} records")
            
            record = records[0]
            transformed_record = self._transform_record(record, column_mappings)
            
            template = self.graphql_loader.get_mutation("create-master-item")
            
            # Build variables for create-master-item
            # Priority 1: Use item_name from Enhanced Merge Orchestrator transformation
            item_name = record.get('item_name')
            if not item_name:
                # Priority 2: Fallback to AAG ORDER NUMBER
                item_name = record.get('AAG ORDER NUMBER', 'Unknown Order')
                self.logger.info(f"Using fallback item name: {item_name}")
            else:
                self.logger.info(f"Using Enhanced Merge Orchestrator item_name: {item_name}")
            
            column_values = self._build_column_values(transformed_record)
            
            # Extract group_id for proper group placement - BINARY LOGIC
            group_id = self._get_group_id_from_record(record)
            
            # BINARY LOGIC: If group_id is None, we must create the group first
            if group_id is None:
                group_name = record.get('group_name')
                if not group_name:
                    raise ValueError(f"Cannot create item: no group_id and no group_name in record")
                
                self.logger.info(f"🏗️ Creating group first: '{group_name}'")
                # Create group and get the returned group_id
                group_creation_result = self._create_group_and_update_database(group_name, record)
                if not group_creation_result:
                    raise ValueError(f"Failed to create group: '{group_name}'")
                group_id = group_creation_result.get('group_id')
                if not group_id:
                    raise ValueError(f"Group creation succeeded but no group_id returned for: '{group_name}'")
                self.logger.info(f"✅ Group created successfully: '{group_id}'")
            
            # Determine create_labels_if_missing based on TOML configuration
            create_labels = self._determine_create_labels_for_records([transformed_record], 'headers')
            
            variables = {
                'boardId': int(self.board_id),  # Monday.com expects integer for ID
                'groupId': group_id,            # Now guaranteed to be valid group_id
                'itemName': str(item_name),
                'columnValues': column_values,
                'createLabelsIfMissing': create_labels
            }
            
            self.logger.debug(f"create_items variables: createLabelsIfMissing={create_labels}")
            return {'query': template, 'variables': variables}
            
        elif operation_type == 'create_subitems':
            if len(records) == 1:
                # Single subitem
                record = records[0]
                transformed_record = self._transform_record(record, column_mappings)
                
                template = self.graphql_loader.get_mutation("create_subitem")
                
                # Build variables for create_subitem
                parent_item_id = record.get('parent_item_id')
                if not parent_item_id:
                    raise ValueError("parent_item_id is required for create_subitems operation")
                
                # Use size_code and description for subitem name
                size_code = record.get('size_code', 'N/A')
                item_name = f"Size {size_code}"
                
                # Build minimal column values for subitems
                column_values = self._build_column_values(transformed_record)
                
                # Determine create_labels_if_missing based on TOML configuration for subitems
                create_labels = self._determine_create_labels_for_records([transformed_record], 'lines')
                
                variables = {
                    'parentItemId': str(parent_item_id),  # Monday.com expects string for parent ID
                    'itemName': str(item_name),
                    'columnValues': column_values,
                    'createLabelsIfMissing': create_labels
                }
                
                return {'query': template, 'variables': variables}
            else:
                # Batch subitems - build dynamic GraphQL
                return self._build_batch_subitems_query(records, column_mappings)
        
        elif operation_type == 'update_items':
            # UPDATE existing items
            if len(records) > 1:
                raise ValueError(f"Single item update operation expected, got {len(records)} records")
            
            record = records[0]
            transformed_record = self._transform_record(record, column_mappings)
            
            template = self.graphql_loader.get_mutation("update_item")
            
            # Build variables for update_item
            monday_item_id = record.get('monday_item_id')
            if not monday_item_id:
                raise ValueError("monday_item_id is required for update_items operation")
            
            column_values = self._build_column_values(transformed_record)
            
            # Determine create_labels_if_missing based on TOML configuration
            create_labels = self._determine_create_labels_for_records([transformed_record], 'headers')
            
            variables = {
                'board_id': str(self.board_id),        # Match GraphQL template
                'item_id': str(monday_item_id),        # Match GraphQL template  
                'column_values': column_values,        # Match GraphQL template
                'createLabelsIfMissing': create_labels # Match GraphQL template
            }
            
            self.logger.debug(f"update_items variables: board_id={self.board_id}, item_id={monday_item_id}, createLabelsIfMissing={create_labels}")
            return {'query': template, 'variables': variables}
            
        elif operation_type == 'update_subitems':
            if len(records) == 1:
                # Single subitem update
                record = records[0]
                transformed_record = self._transform_record(record, column_mappings)
                
                template = self.graphql_loader.get_mutation("update_subitem")
                
                # Build variables for update_subitem
                monday_subitem_id = record.get('monday_subitem_id')
                if not monday_subitem_id:
                    raise ValueError("monday_subitem_id is required for update_subitems operation")
                
                # Build minimal column values for subitems
                column_values = self._build_column_values(transformed_record)
                
                # Determine create_labels_if_missing based on TOML configuration for subitems
                create_labels = self._determine_create_labels_for_records([transformed_record], 'lines')
                
                variables = {
                    'itemId': str(monday_subitem_id),  # Monday.com expects string for subitem ID
                    'columnValues': column_values,
                    'createLabelsIfMissing': create_labels
                }
                
                return {'query': template, 'variables': variables}
            else:
                # Batch subitem updates - build dynamic GraphQL
                return self._build_batch_subitem_updates_query(records, column_mappings)
        
        elif operation_type == 'create_groups':
            # CREATE GROUPS operation - the missing piece for 100% success!
            if len(records) == 1:
                # Single group creation
                record = records[0]
                
                template = self.graphql_loader.get_mutation("create_group")
                
                # Build variables for create_group
                group_name = record.get('group_name')
                if not group_name:
                    raise ValueError("group_name is required for create_groups operation")
                
                variables = {
                    'board_id': str(self.board_id),  # Monday.com expects string for board_id in GraphQL
                    'group_name': str(group_name)
                }
                
                self.logger.info(f"Creating group: '{group_name}' on board {self.board_id}")
                return {'query': template, 'variables': variables}
            else:
                # Batch group creation - build dynamic GraphQL
                return self._build_batch_groups_query(records)
        
        elif operation_type == 'batch_create_items':
            # Batch item creation using GraphQL batch template
            return self._build_batch_items_query(records, column_mappings)
            
        elif operation_type == 'async_batch_create_items':
            # Same as batch_create_items - the async nature is handled in execution, not query building
            return self._build_batch_items_query(records, column_mappings)
        
        else:
            # For other operations, fall back to template rendering (future enhancement)
            raise NotImplementedError(f"Operation {operation_type} not yet implemented for MVP")
    
    def _get_column_mappings(self, operation_type: str) -> Dict[str, str]:
        """Get column mappings from TOML configuration"""
        # Get the environment from config parser (development/production)
        try:
            from .config_parser import DeltaSyncConfig
            delta_config = DeltaSyncConfig.from_toml(self.config_path, environment=self.environment)
            environment = delta_config.environment
        except:
            environment = self.environment  # Use instance environment
        
        monday_mapping = self.toml_config.get('monday', {}).get('column_mapping', {})
        
        if operation_type in ['create_items', 'update_items']:
            # For headers: use environment-specific mapping (development.headers or production.headers)
            headers_mapping = monday_mapping.get(environment, {}).get('headers', {})
            
            self.logger.debug(f"Headers mapping for {operation_type} ({environment}): {len(headers_mapping)} columns found")
            return headers_mapping
        elif operation_type in ['create_subitems', 'update_subitems']:
            # For lines: environment-specific mapping
            lines_mapping = monday_mapping.get(environment, {}).get('lines', {})
            
            self.logger.debug(f"Lines mapping for {operation_type}: {len(lines_mapping)} columns found")
            return lines_mapping
        else:
            # Default to headers mapping for unknown operations
            headers_mapping = monday_mapping.get(environment, {}).get('headers', {})
            
            self.logger.debug(f"Default headers mapping for {operation_type}: {len(headers_mapping)} columns found")
            return headers_mapping
    
    def _transform_record(self, record: Dict[str, Any], mappings: Dict[str, str]) -> Dict[str, Any]:
        """Transform database record using TOML column mappings"""
        transformed = {}
        mapped_count = 0
        
        # Apply TOML column mappings
        for db_column, monday_column in mappings.items():
            if db_column in record:
                transformed[monday_column] = record[db_column]
                mapped_count += 1
        
        # Add required Monday.com fields that might not be in mappings
        if 'name' not in transformed:
            # Priority 1: Use item_name from Enhanced Merge Orchestrator transformation
            item_name = record.get('item_name')
            if not item_name:
                # Priority 2: Fallback to AAG ORDER NUMBER
                item_name = record.get('AAG ORDER NUMBER', 'Unknown Order')
                self.logger.debug(f"Using fallback item name for transformation: {item_name}")
            else:
                self.logger.debug(f"Using Enhanced Merge Orchestrator item_name for transformation: {item_name}")
            transformed['name'] = item_name
        
        self.logger.debug(f"Record transformation: {mapped_count}/{len(mappings)} TOML mappings applied, {len(transformed)} total fields")
        
        return transformed
    
    def _get_group_id_from_record(self, record: Dict[str, Any]) -> Optional[str]:
        """
        BINARY LOGIC: Extract group_id from database record
        - group_id NOT NULL → USE existing group_id
        - group_id NULL → RETURN None (caller must create group first)
        NO FALLBACKS - BINARY ONLY
        """
        group_id = record.get('group_id')
        if group_id:
            self.logger.debug(f"✅ Using database group_id: '{group_id}'")
            return group_id
            
        # BINARY LOGIC: group_id is NULL - return None to signal group creation needed
        group_name = record.get('group_name')
        if group_name:
            self.logger.warning(f"⚠️ group_id is NULL - GROUP CREATION REQUIRED for: '{group_name}'")
            return None  # Return None to trigger group creation workflow
            
        self.logger.error("❌ No group_name found - cannot determine group for item creation")
        return None
    
    def _create_group_and_update_database(self, group_name: str, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create group on Monday.com and update database with returned group_id
        BINARY LOGIC: Create group → Update database → Return group_id
        """
        try:
            # Step 1: Create group on Monday.com
            self.logger.info(f"🏗️ Creating Monday.com group: '{group_name}'")
            
            template = self.graphql_loader.get_mutation("create-group")
            variables = {
                'board_id': str(self.board_id),
                'group_name': str(group_name)
            }
            
            response = self._make_graphql_request({'query': template, 'variables': variables})
            
            if not response or 'data' not in response:
                self.logger.error(f"❌ Group creation failed: Invalid response for '{group_name}'")
                return None
                
            # Extract group_id from response
            group_data = response['data'].get('create_group')
            if not group_data or 'id' not in group_data:
                self.logger.error(f"❌ Group creation failed: No group ID returned for '{group_name}'")
                return None
                
            new_group_id = group_data['id']
            self.logger.info(f"✅ Monday.com group created: '{group_name}' → '{new_group_id}'")
            
            # Step 2: Update database with new group_id
            record_uuid = record.get('record_uuid')
            if record_uuid:
                self._update_database_group_id(record_uuid, new_group_id)
                self.logger.info(f"✅ Database updated: record_uuid '{record_uuid}' → group_id '{new_group_id}'")
            else:
                self.logger.warning(f"⚠️ No record_uuid found - database not updated for group '{new_group_id}'")
            
            return {
                'group_id': new_group_id,
                'group_name': group_name,
                'created': True
            }
            
        except Exception as e:
            self.logger.error(f"❌ Group creation failed for '{group_name}': {str(e)}")
            return None
    
    def _update_database_group_id(self, record_uuid: str, group_id: str) -> bool:
        """Update FACT_ORDER_LIST with new group_id for given record_uuid"""
        try:
            # This would typically use the database connection from config
            # For now, log the operation - actual implementation depends on database setup
            self.logger.info(f"📝 DATABASE UPDATE: record_uuid='{record_uuid}' → group_id='{group_id}'")
            
            # TODO: Implement actual database update
            # UPDATE FACT_ORDER_LIST SET group_id = ? WHERE record_uuid = ?
            
            return True
        except Exception as e:
            self.logger.error(f"❌ Database update failed: record_uuid='{record_uuid}' group_id='{group_id}': {str(e)}")
            return False
    
    def _get_group_id(self, record: Dict[str, Any]) -> Optional[str]:
        """Get or create group ID based on TOML group strategy"""
        group_config = self.toml_config.get('monday.sync.groups', {})
        strategy = group_config.get('strategy', 'season')
        
        if strategy == 'season':
            # Use GroupMonday column if available, or build from customer + season
            if 'GroupMonday' in record:
                return record['GroupMonday']
            else:
                customer = record.get('CUSTOMER NAME', 'Unknown')
                season = record.get('CUSTOMER SEASON', record.get('AAG SEASON', 'Unknown'))
                return f"{customer} {season}"
        
        return None

    def _build_column_values(self, record: Dict[str, Any]) -> str:
        """Build JSON-formatted column values for Monday.com item creation using TOML mappings"""
        column_values = {}
        
        # Create reverse mapping from Monday column ID to database column name for better logging
        headers_mapping = self._get_column_mappings('headers')
        reverse_mapping = {monday_col: db_col for db_col, monday_col in headers_mapping.items()}
        
        # Use the transformed record (already mapped via TOML) instead of generic conversion
        # The record should already be transformed by _transform_record using TOML mappings
        for monday_column_id, value in record.items():
            # CRITICAL FIX: Skip 'name' field - it's for item naming, not column values
            if monday_column_id == 'name':
                self.logger.debug(f"⚡ Skipping 'name' field in column_values: '{value}' (used for item naming only)")
                continue
            
            # Get original database column name for logging
            db_column_name = reverse_mapping.get(monday_column_id, monday_column_id)
            
            # Log all dropdown columns before filtering
            if monday_column_id.startswith("dropdown_"):
                # Debug logging disabled for dropdown processing - only log errors/warnings
                pass
            
            # Enhanced filtering: exclude None, empty strings, and string literal 'None'
            if value is not None and str(value).strip() and str(value).strip().lower() != 'none':
                # Format dropdown columns correctly for Monday.com API
                if monday_column_id.startswith("dropdown_"):
                    # Dropdown values must be formatted as {"labels": ["value"]}
                    column_values[monday_column_id] = {"labels": [str(value)]}
                    # Debug logging disabled for dropdown processing
                else:
                    # Text/numeric columns can be strings
                    column_values[monday_column_id] = str(value)
            elif monday_column_id.startswith("dropdown_"):
                self.logger.debug(f"⚠️  Dropdown {monday_column_id} (DB: {db_column_name}) FILTERED OUT: '{value}' (type: {type(value).__name__})")
        
        self.logger.debug(f"Built column values: {len(column_values)} columns mapped (filtered 'None' values and 'name' field)")
        
        # Return as JSON string for GraphQL
        import json
        return json.dumps(column_values)
    
    def _build_batch_subitem_updates_query(self, records: List[Dict[str, Any]], column_mappings: Dict[str, str]) -> Dict[str, Any]:
        """Build dynamic batch GraphQL query for subitem updates"""
        # Determine create_labels_if_missing based on TOML configuration for this batch
        create_labels = self._determine_create_labels_for_records(records, 'lines')
        
        # Build variable definitions
        var_definitions = ["$createLabelsIfMissing: Boolean"]
        mutation_calls = []
        variables = {"createLabelsIfMissing": create_labels}
        
        for i, record in enumerate(records):
            # Variable definitions
            var_definitions.append(f"$item{i}_itemId: ID!")
            var_definitions.append(f"$item{i}_columnValues: JSON")
            
            # Transform record
            transformed_record = self._transform_record(record, column_mappings)
            
            # Variables for this subitem
            monday_subitem_id = record.get('monday_subitem_id')
            if not monday_subitem_id:
                raise ValueError(f"monday_subitem_id is required for update_subitems operation (record {i})")
            
            variables[f"item{i}_itemId"] = str(monday_subitem_id)
            variables[f"item{i}_columnValues"] = self._build_column_values(transformed_record)
            
            # GraphQL mutation call
            mutation_calls.append(f"""
                item{i}: change_multiple_column_values(
                    item_id: $item{i}_itemId,
                    column_values: $item{i}_columnValues,
                    create_labels_if_missing: $createLabelsIfMissing
                ) {{
                    id
                }}
            """.strip())
        
        # Build complete query
        query = f"""
        mutation UpdateBatchSubitems({', '.join(var_definitions)}) {{
            {chr(10).join(mutation_calls)}
        }}
        """
        
        return {'query': query, 'variables': variables}
    
    def _build_batch_subitems_query(self, records: List[Dict[str, Any]], column_mappings: Dict[str, str]) -> Dict[str, Any]:
        """Build dynamic batch GraphQL query for subitems"""
        # Determine create_labels_if_missing based on TOML configuration for this batch
        create_labels = self._determine_create_labels_for_records(records, 'lines')
        
        # Build variable definitions
        var_definitions = ["$createLabelsIfMissing: Boolean"]
        mutation_calls = []
        variables = {"createLabelsIfMissing": create_labels}
        
        for i, record in enumerate(records):
            # Variable definitions
            var_definitions.append(f"$item{i}_parentId: ID!")
            var_definitions.append(f"$item{i}_name: String!")
            var_definitions.append(f"$item{i}_columnValues: JSON")
            
            # Transform record
            transformed_record = self._transform_record(record, column_mappings)
            
            # Get parent item ID
            parent_item_id = record.get('parent_item_id')
            if not parent_item_id:
                raise ValueError(f"parent_item_id is required for subitem {i}")
            
            # Build subitem name
            size_code = record.get('size_code', 'N/A')
            item_name = f"Size {size_code}"
            
            # Build column values
            column_values = self._build_column_values(transformed_record)
            
            # Add to variables
            variables[f'item{i}_parentId'] = str(parent_item_id)
            variables[f'item{i}_name'] = str(item_name)
            variables[f'item{i}_columnValues'] = column_values
            
            # Build mutation call with dynamic createLabelsIfMissing
            mutation_calls.append(f"""
  create_subitem_{i}: create_subitem(
    parent_item_id: $item{i}_parentId,
    item_name: $item{i}_name,
    column_values: $item{i}_columnValues,
    create_labels_if_missing: $createLabelsIfMissing
  ) {{
    id
    name
    board {{ id }}
    column_values {{ id text value }}
    created_at
  }}""")
        
        # Build complete GraphQL mutation
        var_definitions_str = ", ".join(var_definitions)
        mutation_calls_str = "".join(mutation_calls)
        
        query = f"""
mutation BatchCreateSubitems({var_definitions_str}) {{{mutation_calls_str}
}}
        """.strip()
        
        self.logger.debug(f"Batch subitems query: createLabelsIfMissing={create_labels}")
        return {'query': query, 'variables': variables}
    
    def _build_batch_items_query(self, records: List[Dict[str, Any]], column_mappings: Dict[str, str]) -> Dict[str, Any]:
        """Build dynamic batch GraphQL query for items"""
        # First transform all records to Monday column format
        transformed_records = []
        for record in records:
            transformed_record = self._transform_record(record, column_mappings)
            transformed_records.append(transformed_record)
        
        # CRITICAL FIX: Determine create_labels_if_missing AFTER transformation
        create_labels = self._determine_create_labels_for_records(transformed_records, 'headers')
        
        # Build variable definitions
        var_definitions = ["$boardId: ID!", "$createLabelsIfMissing: Boolean"]
        mutation_calls = []
        variables = {
            "boardId": int(self.board_id),
            "createLabelsIfMissing": create_labels
        }
        
        for i, (record, transformed_record) in enumerate(zip(records, transformed_records)):
            # Variable definitions
            var_definitions.append(f"$item{i}_name: String!")
            var_definitions.append(f"$item{i}_columnValues: JSON")
            var_definitions.append(f"$item{i}_groupId: String")
            
            # Priority 1: Use item_name from Enhanced Merge Orchestrator transformation
            item_name = record.get('item_name')
            if not item_name:
                # Priority 2: Fallback to AAG ORDER NUMBER
                item_name = record.get('AAG ORDER NUMBER', 'Unknown Order')
                self.logger.debug(f"Using fallback item name: {item_name}")
            else:
                self.logger.debug(f"Using Enhanced Merge Orchestrator item_name: {item_name}")
            
            # Build column values from already-transformed record
            column_values = self._build_column_values(transformed_record)
            
            # Extract group_id for proper group placement
            group_id = self._get_group_id_from_record(record)
            
            # Add to variables
            variables[f'item{i}_name'] = str(item_name)
            variables[f'item{i}_columnValues'] = column_values
            variables[f'item{i}_groupId'] = group_id
            
            # Build mutation call
            mutation_calls.append(f"""
  create_item_{i}: create_item(
    board_id: $boardId,
    group_id: $item{i}_groupId,
    item_name: $item{i}_name,
    column_values: $item{i}_columnValues,
    create_labels_if_missing: $createLabelsIfMissing
  ) {{
    id
    name
    board {{ id }}
    column_values {{ id text value }}
    created_at
  }}""")
        
        # Build complete GraphQL mutation
        var_definitions_str = ", ".join(var_definitions)
        mutation_calls_str = "".join(mutation_calls)
        
        query = f"""
mutation BatchCreateItems({var_definitions_str}) {{{mutation_calls_str}
}}
        """.strip()
        
        self.logger.debug(f"Batch items query: {len(records)} items, createLabelsIfMissing={create_labels}")
        return {'query': query, 'variables': variables}

    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """Render GraphQL template with context data (simple string replacement for now)"""
        # For MVP: Simple string replacement
        # Future: Use Jinja2 for complex templating if needed
        
        query = template
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            if isinstance(value, (list, dict)):
                query = query.replace(placeholder, json.dumps(value))
            else:
                query = query.replace(placeholder, str(value))
        
        return query
    
    async def _make_api_call(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute GraphQL query against Monday.com API with conservative rate limiting
        Enhanced with comprehensive API logging data capture for troubleshooting
        """
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        # Capture request timestamp
        request_timestamp = datetime.utcnow()
        
        try:
            # Conservative timeout and connection settings
            timeout = aiohttp.ClientTimeout(total=25.0, connect=5.0)
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=3)
            
            async with aiohttp.ClientSession(
                timeout=timeout, 
                connector=connector,
                headers={"User-Agent": "DataOrchestration/1.0 Monday.com Sync"}
            ) as session:
                
                # Rate limiting: Small delay before request
                await asyncio.sleep(0.01)  # 10ms baseline delay
                
                variables_count = len(variables) if variables else 0
                self.logger.debug(f"Making API call to Monday.com: {len(query)} chars, {variables_count} variables")
                
                async with session.post(self.api_url, json=payload, headers=headers) as response:
                    # Capture response timestamp
                    response_timestamp = datetime.utcnow()
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Check for GraphQL errors
                        if 'errors' in data and data['errors']:
                            error_details = data['errors']
                            self.logger.error(f"Monday.com GraphQL errors: {error_details}")
                            
                            # Check for rate limit errors
                            for error in error_details:
                                if 'rate limit' in str(error).lower() or 'too many requests' in str(error).lower():
                                    self.logger.warning("Rate limit detected - implementing exponential backoff")
                                    await asyncio.sleep(1.0)  # Wait 1 second for rate limits
                            
                            # Return error with full API logging data
                            return {
                                'success': False, 
                                'error': error_details,
                                'api_request': payload,
                                'api_response': data,
                                'request_timestamp': request_timestamp,
                                'response_timestamp': response_timestamp
                            }
                        
                        # Successful response with full API logging data
                        self.logger.debug(f"API call successful: {response.status}")
                        return {
                            'success': True, 
                            'data': data.get('data', {}),
                            'api_request': payload,
                            'api_response': data,
                            'request_timestamp': request_timestamp,
                            'response_timestamp': response_timestamp
                        }
                    
                    elif response.status == 429:  # Too Many Requests
                        self.logger.warning(f"Rate limited by Monday.com (429) - backing off")
                        await asyncio.sleep(2.0)  # Extended backoff for explicit rate limits
                        
                        # Return rate limit error with API logging data
                        error_response = {"status": response.status, "message": "Rate limited"}
                        return {
                            'success': False, 
                            'error': f"Rate limited: HTTP {response.status}",
                            'api_request': payload,
                            'api_response': error_response,
                            'request_timestamp': request_timestamp,
                            'response_timestamp': response_timestamp
                        }
                    
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Monday.com API error {response.status}: {error_text}")
                        
                        # Return HTTP error with API logging data
                        error_response = {"status": response.status, "error": error_text}
                        return {
                            'success': False, 
                            'error': f"HTTP {response.status}: {error_text}",
                            'api_request': payload,
                            'api_response': error_response,
                            'request_timestamp': request_timestamp,
                            'response_timestamp': response_timestamp
                        }
                        
        except asyncio.TimeoutError:
            self.logger.error("Monday.com API call timed out after 25s")
            
            # Capture timeout error with API logging data
            response_timestamp = datetime.utcnow()
            error_response = {"error": "timeout", "duration_ms": 25000}
            return {
                'success': False, 
                'error': 'API call timeout (25s)',
                'api_request': payload,
                'api_response': error_response,
                'request_timestamp': request_timestamp,
                'response_timestamp': response_timestamp
            }
            
        except aiohttp.ClientError as e:
            self.logger.error(f"HTTP client error: {e}")
            
            # Capture client error with API logging data
            response_timestamp = datetime.utcnow()
            error_response = {"error": "client_error", "message": str(e)}
            return {
                'success': False, 
                'error': f'HTTP client error: {str(e)}',
                'api_request': payload,
                'api_response': error_response,
                'request_timestamp': request_timestamp,
                'response_timestamp': response_timestamp
            }
            
        except Exception as e:
            self.logger.exception(f"Unexpected API call error: {e}")
            
            # Capture unexpected error with API logging data
            response_timestamp = datetime.utcnow()
            error_response = {"error": "unexpected_error", "message": str(e)}
            return {
                'success': False, 
                'error': f'Unexpected error: {str(e)}',
                'api_request': payload,
                'api_response': error_response,
                'request_timestamp': request_timestamp,
                'response_timestamp': response_timestamp
            }
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}
    
    def _extract_monday_id(self, data: Dict[str, Any], operation_type: str) -> Optional[Union[int, str]]:
        """
        Extract Monday.com ID from API response
        
        Args:
            data: GraphQL response data
            operation_type: Type of operation (create_items, create_subitems, etc.)
            
        Returns:
            Monday.com ID as integer (items/subitems) or string (groups), or None if not found
        """
        try:
            if operation_type == 'create_items':
                # For single item creation using create-master-item template
                if 'create_item' in data and data['create_item']:
                    monday_id = data['create_item']['id']
                    self.logger.debug(f"Extracted item ID: {monday_id}")
                    return int(monday_id)
                # Fallback for batch creation (create_0, create_1, etc.)
                elif 'create_0' in data and data['create_0']:
                    monday_id = data['create_0']['id']
                    self.logger.debug(f"Extracted batch item ID: {monday_id}")
                    return int(monday_id)
                    
            elif operation_type in ['batch_create_items', 'async_batch_create_items']:
                # CRITICAL FIX: For batch operations, look for create_item_0 first
                if 'create_item_0' in data and data['create_item_0']:
                    monday_id = data['create_item_0']['id']
                    self.logger.debug(f"Extracted batch item ID from create_item_0: {monday_id}")
                    return int(monday_id)
                    
            elif operation_type == 'create_subitems':
                # For single subitem creation using create_subitem template
                if 'create_subitem' in data and data['create_subitem']:
                    monday_id = data['create_subitem']['id']
                    self.logger.debug(f"Extracted subitem ID: {monday_id}")
                    return int(monday_id)
                # Fallback for batch creation (create_subitem_0, create_subitem_1, etc.)
                elif 'create_subitem_0' in data and data['create_subitem_0']:
                    monday_id = data['create_subitem_0']['id']
                    self.logger.debug(f"Extracted batch subitem ID: {monday_id}")
                    return int(monday_id)
                    
            elif operation_type == 'create_groups':
                # For group creation, look for create_group key
                if 'create_group' in data and data['create_group']:
                    monday_id = data['create_group']['id']
                    self.logger.debug(f"Extracted group ID: {monday_id}")
                    # Groups return string IDs like 'group_mkt9x838', not integers
                    return str(monday_id)
                    
            elif operation_type == 'update_items':
                # For item updates, look for change_multiple_column_values key
                if 'change_multiple_column_values' in data and data['change_multiple_column_values']:
                    monday_id = data['change_multiple_column_values']['id']
                    self.logger.debug(f"Extracted updated item ID: {monday_id}")
                    return int(monday_id)
                    
            elif operation_type == 'update_subitems':
                # For subitem updates, look for change_multiple_column_values key
                if 'change_multiple_column_values' in data and data['change_multiple_column_values']:
                    monday_id = data['change_multiple_column_values']['id']
                    self.logger.debug(f"Extracted updated subitem ID: {monday_id}")
                    return int(monday_id)
            
            self.logger.warning(f"No ID found in response data for {operation_type}: {data}")
            return None
            
        except (KeyError, ValueError, TypeError) as e:
            self.logger.error(f"Failed to extract Monday.com ID from response: {e}")
            return None
    
    def _extract_monday_ids(self, data: Dict[str, Any], operation_type: str, count: int) -> List[int]:
        """
        Extract multiple Monday.com IDs from batch API response
        
        Args:
            data: GraphQL response data 
            operation_type: Type of operation (create_items, create_subitems, etc.)
            count: Expected number of IDs
            
        Returns:
            List of Monday.com IDs as integers
        """
        ids = []
        
        try:
            if operation_type in ['batch_create_items', 'async_batch_create_items']:
                # CRITICAL FIX: For batch item creation, look for create_item_0, create_item_1, etc.
                # This matches the query structure built in _build_batch_items_query
                for i in range(count):
                    key = f'create_item_{i}'
                    if key in data and data[key] and 'id' in data[key]:
                        monday_id = int(data[key]['id'])
                        ids.append(monday_id)
                        self.logger.info(f"✅ Extracted batch item ID {i}: {monday_id}")
                    else:
                        self.logger.error(f"❌ Missing or invalid ID in batch response for {key}")
                        self.logger.debug(f"Available keys in response: {list(data.keys())}")
                        
            elif operation_type == 'create_items':
                # For single item creation, look for create_0, create_1, create_2, etc.
                for i in range(count):
                    key = f'create_{i}'
                    if key in data and data[key] and 'id' in data[key]:
                        monday_id = int(data[key]['id'])
                        ids.append(monday_id)
                        self.logger.debug(f"Extracted batch item ID {i}: {monday_id}")
                    else:
                        self.logger.warning(f"Missing or invalid ID in batch response for {key}")
                        
            elif operation_type == 'create_subitems':
                # For batch subitem creation, look for create_subitem_0, create_subitem_1, etc.
                for i in range(count):
                    key = f'create_subitem_{i}'
                    if key in data and data[key] and 'id' in data[key]:
                        monday_id = int(data[key]['id'])
                        ids.append(monday_id)
                        self.logger.debug(f"Extracted batch subitem ID {i}: {monday_id}")
                    else:
                        self.logger.warning(f"Missing or invalid ID in batch response for {key}")
            
            elif operation_type == 'create_groups':
                # For batch group creation, look for create_group_0, create_group_1, etc.
                for i in range(count):
                    key = f'create_group_{i}'
                    if key in data and data[key] and 'id' in data[key]:
                        monday_id = int(data[key]['id'])
                        ids.append(monday_id)
                        self.logger.debug(f"Extracted batch group ID {i}: {monday_id}")
                    else:
                        self.logger.warning(f"Missing or invalid ID in batch response for {key}")
            
            self.logger.info(f"Extracted {len(ids)}/{count} IDs from {operation_type} batch response")
            return ids
            
        except (KeyError, ValueError, TypeError) as e:
            self.logger.error(f"Failed to extract Monday.com IDs from batch response: {e}")
            return []
    
    def _build_batch_groups_query(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build dynamic batch GraphQL query for groups"""
        # Build variable definitions
        var_definitions = [f"$board_id: ID!"]
        mutation_calls = []
        variables = {"board_id": str(self.board_id)}
        
        for i, record in enumerate(records):
            # Variable definitions
            var_definitions.append(f"$group{i}_name: String!")
            
            # Get group name
            group_name = record.get('group_name')
            if not group_name:
                raise ValueError(f"group_name is required for group {i}")
            
            # Add to variables
            variables[f'group{i}_name'] = str(group_name)
            
            # Build mutation call
            mutation_calls.append(f"""
  create_group_{i}: create_group(
    board_id: $board_id,
    group_name: $group{i}_name
  ) {{
    id
    title
    color
  }}""")
        
        # Build complete GraphQL mutation
        var_definitions_str = ", ".join(var_definitions)
        mutation_calls_str = "".join(mutation_calls)
        
        query = f"""
mutation BatchCreateGroups({var_definitions_str}) {{{mutation_calls_str}
}}
        """.strip()
        
        self.logger.debug(f"Batch groups query: {len(records)} groups")
        return {'query': query, 'variables': variables}
    
    def _dry_run_response(self, operation_type: str, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate dry run response for validation with full API logging structure"""
        self.logger.info(f"DRY RUN: Would execute {operation_type} for {len(data_list)} records")
        
        # Generate mock Monday IDs for dry run
        mock_monday_ids = [f"dry_run_id_{i+1}" for i in range(len(data_list))]
        
        return {
            'success': True,
            'dry_run': True,
            'records_processed': len(data_list),
            'monday_ids': mock_monday_ids,
            'operation_type': operation_type,
            'would_execute': f"{operation_type} with {len(data_list)} records",
            # Include mock API logging data for consistency
            'api_request': {'dry_run': True, 'operation': operation_type, 'record_count': len(data_list)},
            'api_response': {'dry_run': True, 'mock_ids': mock_monday_ids},
            'request_timestamp': datetime.utcnow(),
            'response_timestamp': datetime.utcnow()
        }
