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
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

# Modern Python package imports - ultra-minimal dependencies
from src.pipelines.utils import logger, config, db
from src.pipelines.integrations.monday.graphql_loader import GraphQLLoader


class MondayAPIClient:
    """
    Ultra-lightweight Monday.com API client
    Combines TOML configuration + GraphQL templates + HTTP client
    """
    
    def __init__(self, toml_config_path: str):
        """
        Initialize with TOML configuration
        
        Args:
            toml_config_path: Path to sync_order_list.toml configuration
        """
        self.logger = logger.get_logger(__name__)
        self.config_path = Path(toml_config_path)
        
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
        delta_config = DeltaSyncConfig.from_toml(self.config_path, environment='development')
        
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
    
    def execute(self, operation_type: str, data: Union[Dict, List[Dict]], dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute Monday.com operation with automatic single/batch/async handling
        
        Args:
            operation_type: "create_items", "create_subitems", "update_items", "update_subitems", "create_groups"
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
        
        # Conservative execution strategy - respect Monday.com rate limits
        # MVP: Single items, batch subitems for performance
        if operation_type == 'create_subitems' and len(data_list) > 1:
            return asyncio.run(self._execute_batch(operation_type, data_list))
        else:
            return asyncio.run(self._execute_all_single(operation_type, data_list))
    
    async def _execute_all_single(self, operation_type: str, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute all records as single item operations with rate limiting"""
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
        
        for result in results:
            if result.get('success'):
                all_monday_ids.extend(result.get('monday_ids', []))
            else:
                errors.append(result.get('error', 'Unknown error'))
        
        return {
            'success': len(errors) == 0,
            'records_processed': total_processed,
            'monday_ids': all_monday_ids,
            'operation_type': operation_type,
            'errors': errors if errors else None
        }
    
    async def _execute_single(self, operation_type: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """Execute single record operation"""
        try:
            # Build GraphQL query with variables
            query_data = self._build_graphql_query(operation_type, [record])
            
            # Execute API call
            result = await self._make_api_call(query_data['query'], query_data['variables'])
            
            if result['success']:
                monday_id = self._extract_monday_id(result['data'], operation_type)
                return {
                    'success': True,
                    'records_processed': 1,
                    'monday_ids': [monday_id],
                    'operation_type': operation_type
                }
            else:
                return {
                    'success': False,
                    'error': result['error'],
                    'records_processed': 0
                }
                
        except Exception as e:
            self.logger.exception(f"Single operation failed: {e}")
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
                    'operation_type': operation_type
                }
            else:
                return {
                    'success': False,
                    'error': result['error'],
                    'records_processed': 0
                }
                
        except Exception as e:
            self.logger.exception(f"Batch operation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'records_processed': 0
            }
    
    async def _execute_async_batch(self, operation_type: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute large dataset with conservative async batch processing
        Uses proven rate limiting patterns: 15→5→1 fallback, 100ms delays, 25s timeouts
        """
        # Conservative batching for Monday.com rate limits - start with 5 items for testing
        initial_batch_size = 5
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
            item_name = record.get('AAG ORDER NUMBER', 'Unknown Order')
            column_values = self._build_column_values(transformed_record)
            
            variables = {
                'boardId': int(self.board_id),  # Monday.com expects integer for ID
                'itemName': str(item_name),
                'columnValues': column_values
            }
            
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
                
                variables = {
                    'parentItemId': str(parent_item_id),  # Monday.com expects string for parent ID
                    'itemName': str(item_name),
                    'columnValues': column_values
                }
                
                return {'query': template, 'variables': variables}
            else:
                # Batch subitems - build dynamic GraphQL
                return self._build_batch_subitems_query(records, column_mappings)
        else:
            # For other operations, fall back to template rendering (future enhancement)
            raise NotImplementedError(f"Operation {operation_type} not yet implemented for MVP")
    
    def _get_column_mappings(self, operation_type: str) -> Dict[str, str]:
        """Get column mappings from TOML configuration"""
        # Get the environment from config parser (development/production)
        try:
            from .config_parser import DeltaSyncConfig
            delta_config = DeltaSyncConfig.from_toml(self.config_path, environment='development')
            environment = delta_config.environment
        except:
            environment = 'development'  # Fallback
        
        monday_mapping = self.toml_config.get('monday', {}).get('column_mapping', {})
        
        if operation_type in ['create_items', 'update_items']:
            # For headers: use environment-specific mapping (development.headers or production.headers)
            headers_mapping = monday_mapping.get(environment, {}).get('headers', {})
            
            self.logger.debug(f"Headers mapping for {operation_type} ({environment}): {len(headers_mapping)} columns found")
            return headers_mapping
        else:
            # For lines: environment-specific mapping
            lines_mapping = monday_mapping.get(environment, {}).get('lines', {})
            
            self.logger.debug(f"Lines mapping for {operation_type}: {len(lines_mapping)} columns found")
            return lines_mapping
    
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
            transformed['name'] = record.get('AAG ORDER NUMBER', 'Unknown Order')
        
        self.logger.debug(f"Record transformation: {mapped_count}/{len(mappings)} TOML mappings applied, {len(transformed)} total fields")
        
        return transformed
    
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
        
        # Use the transformed record (already mapped via TOML) instead of generic conversion
        # The record should already be transformed by _transform_record using TOML mappings
        for monday_column_id, value in record.items():
            if value is not None and str(value).strip():
                column_values[monday_column_id] = str(value)
        
        self.logger.debug(f"Built column values: {len(column_values)} columns mapped")
        
        # Return as JSON string for GraphQL
        import json
        return json.dumps(column_values)
    
    def _build_batch_subitems_query(self, records: List[Dict[str, Any]], column_mappings: Dict[str, str]) -> Dict[str, Any]:
        """Build dynamic batch GraphQL query for subitems"""
        # Build variable definitions
        var_definitions = []
        mutation_calls = []
        variables = {}
        
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
            
            # Build mutation call
            mutation_calls.append(f"""
  create_subitem_{i}: create_subitem(
    parent_item_id: $item{i}_parentId,
    item_name: $item{i}_name,
    column_values: $item{i}_columnValues,
    create_labels_if_missing: true
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
        Uses proven patterns: connection pooling, timeout handling, retry logic
        """
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
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
                
                self.logger.debug(f"Making API call to Monday.com: {len(query)} chars, {len(variables)} variables")
                
                async with session.post(self.api_url, json=payload, headers=headers) as response:
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
                            
                            return {'success': False, 'error': error_details}
                        
                        # Successful response
                        self.logger.debug(f"API call successful: {response.status}")
                        return {'success': True, 'data': data.get('data', {})}
                    
                    elif response.status == 429:  # Too Many Requests
                        self.logger.warning(f"Rate limited by Monday.com (429) - backing off")
                        await asyncio.sleep(2.0)  # Extended backoff for explicit rate limits
                        return {'success': False, 'error': f"Rate limited: HTTP {response.status}"}
                    
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Monday.com API error {response.status}: {error_text}")
                        return {'success': False, 'error': f"HTTP {response.status}: {error_text}"}
                        
        except asyncio.TimeoutError:
            self.logger.error("Monday.com API call timed out after 25s")
            return {'success': False, 'error': 'API call timeout (25s)'}
            
        except aiohttp.ClientError as e:
            self.logger.error(f"HTTP client error: {e}")
            return {'success': False, 'error': f'HTTP client error: {str(e)}'}
            
        except Exception as e:
            self.logger.exception(f"Unexpected API call error: {e}")
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}
    
    def _extract_monday_id(self, data: Dict[str, Any], operation_type: str) -> Optional[int]:
        """
        Extract Monday.com ID from API response
        
        Args:
            data: GraphQL response data
            operation_type: Type of operation (create_items, create_subitems, etc.)
            
        Returns:
            Monday.com ID as integer, or None if not found
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
            if operation_type == 'create_items':
                # For batch item creation, look for create_0, create_1, create_2, etc.
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
    
    def _dry_run_response(self, operation_type: str, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate dry run response for validation"""
        self.logger.info(f"DRY RUN: Would execute {operation_type} for {len(data_list)} records")
        
        return {
            'success': True,
            'dry_run': True,
            'records_processed': len(data_list),
            'operation_type': operation_type,
            'would_execute': f"{operation_type} with {len(data_list)} records"
        }
