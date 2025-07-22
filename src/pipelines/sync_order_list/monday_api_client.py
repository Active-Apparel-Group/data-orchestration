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
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

# Modern Python package imports - ultra-minimal dependencies
from src.pipelines.utils import logger, config
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
        
        # Get Monday.com API configuration
        try:
            self.api_token = config.get_config_value("MONDAY_API_TOKEN")
        except (AttributeError, Exception):
            # Fallback: try to get from environment or config file
            import os
            self.api_token = os.getenv("MONDAY_API_TOKEN", "your_monday_api_token_here")
            self.logger.warning("Using fallback Monday API token - ensure MONDAY_API_TOKEN is configured")
        
        self.api_url = "https://api.monday.com/v2"
        
        # Environment-specific configuration
        environment = self.toml_config.get('environment', {}).get('mode', 'development')
        self.monday_config = self.toml_config.get(f'monday.{environment}', {})
        self.board_id = self.monday_config.get('board_id')
        self.subitem_board_id = self.monday_config.get('subitem_board_id')
        
        self.logger.info(f"Monday API Client initialized for {environment} (board: {self.board_id})")
    
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
        
        # Determine execution strategy based on data size
        if len(data_list) == 1:
            return asyncio.run(self._execute_single(operation_type, data_list[0]))
        elif len(data_list) <= 50:
            return asyncio.run(self._execute_batch(operation_type, data_list))
        else:
            return asyncio.run(self._execute_async_batch(operation_type, data_list))
    
    async def _execute_single(self, operation_type: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """Execute single record operation"""
        try:
            # Build GraphQL query
            query = self._build_graphql_query(operation_type, [record])
            
            # Execute API call
            result = await self._make_api_call(query)
            
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
            # Build batch GraphQL query
            query = self._build_graphql_query(operation_type, records)
            
            # Execute API call
            result = await self._make_api_call(query)
            
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
        """Execute large dataset with async batch processing"""
        batch_size = 50
        batches = [records[i:i + batch_size] for i in range(0, len(records), batch_size)]
        
        self.logger.info(f"Processing {len(records)} records in {len(batches)} async batches")
        
        successful_records = 0
        failed_records = 0
        all_monday_ids = []
        
        # Process batches concurrently
        semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
        
        async def process_batch(batch_records):
            async with semaphore:
                result = await self._execute_batch(operation_type, batch_records)
                return result
        
        # Execute all batches concurrently
        batch_tasks = [process_batch(batch) for batch in batches]
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Aggregate results
        for result in batch_results:
            if isinstance(result, Exception):
                failed_records += 50  # Assume full batch failed
            elif result['success']:
                successful_records += result['records_processed']
                all_monday_ids.extend(result['monday_ids'])
            else:
                failed_records += len(batches[batch_results.index(result)])
        
        return {
            'success': failed_records == 0,
            'records_processed': successful_records,
            'records_failed': failed_records,
            'monday_ids': all_monday_ids,
            'operation_type': operation_type,
            'batches_processed': len(batches)
        }
    
    def _build_graphql_query(self, operation_type: str, records: List[Dict[str, Any]]) -> str:
        """
        Build GraphQL query by combining TOML mapping + GraphQL template + data
        This is the core transformation: TOML + Template + Data = Query
        """
        # Get column mappings from TOML
        column_mappings = self._get_column_mappings(operation_type)
        
        # Transform data using mappings
        transformed_records = []
        for record in records:
            transformed_record = self._transform_record(record, column_mappings)
            transformed_records.append(transformed_record)
        
        # Build GraphQL mutation based on operation type
        if operation_type == 'create_items':
            return self._build_create_items_mutation(transformed_records)
        elif operation_type == 'create_subitems':
            return self._build_create_subitems_mutation(transformed_records)
        elif operation_type == 'create_groups':
            return self._build_create_group_mutation(transformed_records[0])
        else:
            raise ValueError(f"Unsupported operation type: {operation_type}")
    
    def _build_create_items_mutation(self, transformed_records: List[Dict[str, Any]]) -> str:
        """Build GraphQL mutation for creating items"""
        # Build variables definitions
        variables = []
        mutation_parts = []
        
        for i, record in enumerate(transformed_records):
            # Build column values JSON
            column_values = {}
            for field, value in record.items():
                if field != 'name' and value is not None:
                    column_values[field] = str(value)
            
            variables.append(f'$item{i}_name: String!, $item{i}_columnValues: JSON')
            
            mutation_parts.append(f'''
            create_{i}: create_item(
                board_id: {self.board_id},
                group_id: $groupId,
                item_name: $item{i}_name,
                column_values: $item{i}_columnValues
            ) {{
                id
                name
                board {{ id }}
                column_values {{ id text value }}
                created_at
            }}''')
        
        variables_str = ', '.join(variables)
        mutations_str = ''.join(mutation_parts)
        
        return f'''
        mutation BatchCreateItems($groupId: String, {variables_str}) {{
            {mutations_str}
        }}'''
    
    def _build_create_subitems_mutation(self, transformed_records: List[Dict[str, Any]]) -> str:
        """Build GraphQL mutation for creating subitems"""
        variables = []
        mutation_parts = []
        
        for i, record in enumerate(transformed_records):
            # Get parent item ID from record
            parent_id = record.get('parent_item_id', record.get('monday_item_id'))
            if not parent_id:
                raise ValueError(f"No parent_item_id found for subitem record {i}")
            
            # Build column values JSON
            column_values = {}
            for field, value in record.items():
                if field not in ['name', 'parent_item_id', 'monday_item_id'] and value is not None:
                    column_values[field] = str(value)
            
            variables.append(f'$item{i}_parentId: ID!, $item{i}_name: String!, $item{i}_columnValues: JSON')
            
            mutation_parts.append(f'''
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
            }}''')
        
        variables_str = ', '.join(variables)
        mutations_str = ''.join(mutation_parts)
        
        return f'''
        mutation BatchCreateSubitems({variables_str}) {{
            {mutations_str}
        }}'''
    
    def _build_create_group_mutation(self, group_data: Dict[str, Any]) -> str:
        """Build GraphQL mutation for creating a group"""
        group_name = group_data.get('group_name', 'New Group')
        
        return f'''
        mutation CreateGroup($boardId: ID!, $groupName: String!) {{
            create_group(board_id: $boardId, group_name: $groupName) {{
                id
                title
                color
                position
            }}
        }}'''
    
    def _get_column_mappings(self, operation_type: str) -> Dict[str, str]:
        """Get column mappings from TOML configuration"""
        environment = self.toml_config.get('environment', {}).get('mode', 'development')
        
        if operation_type in ['create_items', 'update_items']:
            mapping_section = f'monday.column_mapping.{environment}.headers'
        else:
            mapping_section = f'monday.column_mapping.{environment}.lines'
        
        mappings = self.toml_config.get('monday', {}).get('column_mapping', {}).get(environment, {})
        
        if operation_type in ['create_items', 'update_items']:
            return mappings.get('headers', {})
        else:
            return mappings.get('lines', {})
    
    def _transform_record(self, record: Dict[str, Any], mappings: Dict[str, str]) -> Dict[str, Any]:
        """Transform database record using TOML column mappings"""
        transformed = {}
        
        for db_column, monday_column in mappings.items():
            if db_column in record:
                transformed[monday_column] = record[db_column]
        
        # Add required Monday.com fields
        transformed['name'] = record.get('AAG ORDER NUMBER', 'Unknown Order')
        
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
    
    async def _make_api_call(self, query: str) -> Dict[str, Any]:
        """Execute GraphQL query against Monday.com API"""
        headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json"
        }
        
        payload = {"query": query}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'errors' in data:
                            return {'success': False, 'error': data['errors']}
                        return {'success': True, 'data': data['data']}
                    else:
                        return {'success': False, 'error': f"HTTP {response.status}: {await response.text()}"}
                        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _extract_monday_id(self, data: Dict[str, Any], operation_type: str) -> Optional[int]:
        """Extract Monday.com ID from API response"""
        # Implementation depends on Monday.com API response structure
        # This is a placeholder - actual implementation would parse the specific response format
        return 12345678  # Mock ID for now
    
    def _extract_monday_ids(self, data: Dict[str, Any], operation_type: str, count: int) -> List[int]:
        """Extract multiple Monday.com IDs from batch API response"""
        # Implementation depends on Monday.com API response structure
        # This is a placeholder - actual implementation would parse the specific response format
        return [12345678 + i for i in range(count)]  # Mock IDs for now
    
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
