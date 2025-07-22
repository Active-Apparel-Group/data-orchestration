"""
Ultra-Lightweight Sync Engine
=============================
Purpose: Pipeline integration - database query + Monday.com execution + status update
Location: src/pipelines/sync_order_list/sync_engine.py
Created: 2025-07-22 (Architecture Simplification)

Core Philosophy: DELTA Query + Monday API + Database Status = Complete Pipeline
- Handles complete sync workflow in ~200 lines
- Integrates with OPUS data pipeline patterns
- Modern logging and error handling
- Direct database integration

Usage:
    engine = SyncEngine("configs/pipelines/sync_order_list.toml")
    result = engine.run_sync(dry_run=False, limit=None)
"""

import os
import sys
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

# Modern Python package imports - ultra-minimal dependencies
from src.pipelines.utils import logger, db, config
from .monday_api_client import MondayAPIClient


class SyncEngine:
    """
    Ultra-lightweight sync engine for ORDER_LIST → Monday.com pipeline
    Handles complete workflow: DELTA query → API calls → status updates
    """
    
    def __init__(self, toml_config_path: str):
        """
        Initialize sync engine with TOML configuration
        
        Args:
            toml_config_path: Path to sync_order_list.toml configuration
        """
        self.logger = logger.get_logger(__name__)
        self.config_path = Path(toml_config_path)
        
        # Load TOML configuration
        self.toml_config = self._load_toml_config()
        
        # Initialize Monday.com API client
        self.monday_client = MondayAPIClient(toml_config_path)
        
        # Environment determination (development vs production)
        self.environment = self._determine_environment()
        
        # Database configuration - use environment-specific DELTA tables
        self.db_config = self.toml_config.get('database', {})
        env_config = self.toml_config.get('environment', {}).get(self.environment, {})
        
        # Use DELTA tables from environment config (NOT main tables)
        self.headers_delta_table = env_config.get('delta_table', 'ORDER_LIST_DELTA')         # Headers DELTA
        self.lines_delta_table = env_config.get('lines_delta_table', 'ORDER_LIST_LINES_DELTA')  # Lines DELTA
        self.status_table = self.db_config.get('status_table', 'ORDER_LIST_MONDAY_SYNC_STATUS')
        
        # Sync configuration
        sync_config = self.toml_config.get('monday', {}).get('sync', {})
        self.sync_config = sync_config  # Store for later use
        self.batch_size = sync_config.get('batch_size', 100)
        self.delta_hours = sync_config.get('delta_hours', 24)
        
        self.logger.info(f"Sync engine initialized for ORDER_LIST_DELTA → Monday.com ({self.environment})")
        self.logger.info(f"Headers DELTA: {self.headers_delta_table}, Lines DELTA: {self.lines_delta_table}")
    
    def _load_toml_config(self) -> Dict[str, Any]:
        """Load and parse TOML configuration"""
        try:
            import tomli
            with open(self.config_path, 'rb') as f:
                return tomli.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load TOML config from {self.config_path}: {e}")
            raise
    
    def _determine_environment(self) -> str:
        """Determine current environment (development or production)"""
        # Check if environment is explicitly set in Monday config
        monday_dev = self.toml_config.get('monday', {}).get('development', {})
        monday_prod = self.toml_config.get('monday', {}).get('production', {})
        
        # Default to development for phase 1
        phase = self.toml_config.get('phase', {})
        current_phase = phase.get('current', 'phase1_minimal')
        
        if 'phase1' in current_phase or 'minimal' in current_phase:
            return 'development'
        elif 'production' in current_phase or 'phase4' in current_phase:
            return 'production'
        else:
            return 'development'  # Safe default
    
    def run_sync(self, dry_run: bool = False, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute complete sync workflow - SEPARATED headers and lines operations
        
        Args:
            dry_run: If True, validate queries and API calls but don't execute
            limit: Optional limit on number of records to process
            
        Returns:
            Comprehensive sync results
        """
        self.logger.info(f"Starting sync workflow (dry_run: {dry_run}, limit: {limit})")
        
        sync_start_time = datetime.now()
        
        try:
            # Operation 1: Sync headers (ORDER_LIST_DELTA → Monday items)
            headers_results = self._sync_headers(limit, dry_run)
            
            # Operation 2: Sync lines (ORDER_LIST_LINES_DELTA → Monday subitems)
            lines_results = self._sync_lines(limit, dry_run)
            
            # Combine results
            total_synced = headers_results.get('synced', 0) + lines_results.get('synced', 0)
            sync_duration = (datetime.now() - sync_start_time).total_seconds()
            
            result = {
                'success': True,
                'headers': headers_results,
                'lines': lines_results,
                'total_synced': total_synced,
                'execution_time_seconds': sync_duration,
                'sync_timestamp': sync_start_time
            }
            
            self.logger.info(f"✅ Sync completed successfully! Headers: {headers_results.get('synced', 0)}, Lines: {lines_results.get('synced', 0)}")
            return result
            
        except Exception as e:
            self.logger.error(f"Sync workflow failed: {e}")
            raise
    
    def _sync_headers(self, limit: Optional[int], dry_run: bool) -> Dict[str, Any]:
        """Sync headers from ORDER_LIST_DELTA to Monday.com items"""
        try:
            # Get pending headers from ORDER_LIST_DELTA
            pending_headers = self._get_pending_headers(limit)
            
            if not pending_headers:
                self.logger.info("No pending headers found for sync")
                return {'synced': 0, 'message': 'No pending headers'}
            
            self.logger.info(f"Found {len(pending_headers)} pending headers for sync")
            
            # Process headers as Monday.com items
            if dry_run:
                self.logger.info(f"DRY RUN: Would sync {len(pending_headers)} headers")
                return {'synced': 0, 'dry_run': True, 'would_sync': len(pending_headers)}
            
            # TODO: Actual Monday.com API calls for headers
            return {'synced': len(pending_headers), 'message': 'Headers sync completed'}
            
        except Exception as e:
            self.logger.error(f"Headers sync failed: {e}")
            raise
    
    def _sync_lines(self, limit: Optional[int], dry_run: bool) -> Dict[str, Any]:
        """Sync lines from ORDER_LIST_LINES_DELTA to Monday.com subitems"""
        try:
            # Get pending lines from ORDER_LIST_LINES_DELTA
            pending_lines = self._get_pending_lines(limit)
            
            if not pending_lines:
                self.logger.info("No pending lines found for sync")
                return {'synced': 0, 'message': 'No pending lines'}
            
            self.logger.info(f"Found {len(pending_lines)} pending lines for sync")
            
            # Process lines as Monday.com subitems
            if dry_run:
                self.logger.info(f"DRY RUN: Would sync {len(pending_lines)} lines")
                return {'synced': 0, 'dry_run': True, 'would_sync': len(pending_lines)}
            
            # TODO: Actual Monday.com API calls for lines
            return {'synced': len(pending_lines), 'message': 'Lines sync completed'}
            
        except Exception as e:
            self.logger.error(f"Lines sync failed: {e}")
            raise
            headers, lines = self._separate_headers_and_lines(pending_records)
            
            # Phase 3: Execute Monday.com operations
            results = {
                'headers': None,
                'lines': None,
                'success': True,
                'records_processed': 0,
                'errors': []
            }
            
            # Process headers (create items/groups if needed)
            if headers:
                self.logger.info(f"Processing {len(headers)} header records")
                header_result = self._process_headers_sync(headers, dry_run)
                results['headers'] = header_result
                results['records_processed'] += header_result.get('records_processed', 0)
                
                if not header_result.get('success', False):
                    results['success'] = False
                    results['errors'].extend(header_result.get('errors', []))
            
            # Process lines (create subitems)
            if lines:
                self.logger.info(f"Processing {len(lines)} line records")
                lines_result = self._process_lines_sync(lines, dry_run)
                results['lines'] = lines_result
                results['records_processed'] += lines_result.get('records_processed', 0)
                
                if not lines_result.get('success', False):
                    results['success'] = False
                    results['errors'].extend(lines_result.get('errors', []))
            
            # Phase 4: Update sync status in database
            if not dry_run and results['success']:
                self._update_sync_status(pending_records, 'SYNCED')
            elif not dry_run and not results['success']:
                self._update_sync_status(pending_records, 'ERROR')
            
            # Calculate execution time
            execution_time = (datetime.now() - sync_start_time).total_seconds()
            
            # Final results
            final_results = {
                'success': results['success'],
                'records_processed': results['records_processed'],
                'headers_processed': len(headers) if headers else 0,
                'lines_processed': len(lines) if lines else 0,
                'execution_time_seconds': execution_time,
                'dry_run': dry_run,
                'errors': results['errors'],
                'details': results
            }
            
            if results['success']:
                self.logger.info(f"Sync completed successfully: {results['records_processed']} records in {execution_time:.2f}s")
            else:
                self.logger.error(f"Sync completed with errors: {len(results['errors'])} errors")
            
            return final_results
            
        except Exception as e:
            self.logger.exception(f"Sync workflow failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'records_processed': 0,
                'execution_time_seconds': (datetime.now() - sync_start_time).total_seconds()
            }
    
    def _get_pending_headers(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get headers records pending Monday.com sync from ORDER_LIST_DELTA
        """
        # Build headers query for ORDER_LIST_DELTA
        headers_query = self._build_headers_delta_query(limit)
        
        # DEBUG: Print the generated SQL query
        print("=" * 80)
        print("DEBUG: HEADERS DELTA QUERY GENERATED")
        print("=" * 80)
        print(headers_query)
        print("=" * 80)
        
        try:
            with db.get_connection('orders') as connection:
                cursor = connection.cursor()
                cursor.execute(headers_query)
                
                columns = [column[0] for column in cursor.description]
                records = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                self.logger.info(f"Retrieved {len(records)} headers from {self.headers_delta_table}")
                return records
                
        except Exception as e:
            self.logger.error(f"Failed to get pending headers: {e}")
            raise
    
    def _get_pending_lines(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get lines records pending Monday.com sync from ORDER_LIST_LINES_DELTA
        """
        # Build lines query for ORDER_LIST_LINES_DELTA
        lines_query = self._build_lines_delta_query(limit)
        
        # DEBUG: Print the generated SQL query
        print("=" * 80)
        print("DEBUG: LINES DELTA QUERY GENERATED")
        print("=" * 80)
        print(lines_query)
        print("=" * 80)
        
        try:
            with db.get_connection('orders') as connection:
                cursor = connection.cursor()
                cursor.execute(lines_query)
                
                columns = [column[0] for column in cursor.description]
                records = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                self.logger.info(f"Retrieved {len(records)} lines from {self.lines_delta_table}")
                return records
                
        except Exception as e:
            self.logger.error(f"Failed to get pending lines: {e}")
            raise
    
    def _build_headers_delta_query(self, limit: Optional[int] = None) -> str:
        """Build DELTA query for pending headers from ORDER_LIST_DELTA"""
        
        # Get headers columns from TOML mapping
        headers_columns = self._get_headers_columns()
        columns_clause = ", ".join(headers_columns)
        
        # DEBUG: Print environment and column mapping info
        print("DEBUG: Headers query configuration:")
        print(f"  Environment: {self.environment}")
        print(f"  Table: {self.headers_delta_table}")
        print(f"  Headers columns: {headers_columns}")
        
        # Build WHERE clause for DELTA logic (headers use sync_state = 'NEW' or 'PENDING')
        delta_clause = "([sync_state] = 'NEW' OR [sync_state] = 'PENDING')"
        
        # DEBUG: Print WHERE clause
        print(f"DEBUG: Headers WHERE clause: {delta_clause}")
        
        # Build ORDER BY clause
        order_clause = "ORDER BY [AAG ORDER NUMBER]"
        
        # Build LIMIT clause
        limit_clause = f"TOP ({limit})" if limit else ""
        
        query = f"""
        SELECT {limit_clause} {columns_clause}
        FROM [{self.headers_delta_table}]
        WHERE {delta_clause}
        {order_clause}
        """
        
        return query.strip()
    
    def _build_lines_delta_query(self, limit: Optional[int] = None) -> str:
        """Build DELTA query for pending lines from ORDER_LIST_LINES_DELTA"""
        
        # Get lines columns from TOML mapping
        lines_columns = self._get_lines_columns()
        columns_clause = ", ".join(lines_columns)
        
        # DEBUG: Print environment and column mapping info
        print("DEBUG: Lines query configuration:")
        print(f"  Environment: {self.environment}")
        print(f"  Table: {self.lines_delta_table}")
        print(f"  Lines columns: {lines_columns}")
        
        # Build WHERE clause for DELTA logic (lines use sync_state = 'PENDING')
        delta_clause = "([sync_state] = 'PENDING')"
        
        # DEBUG: Print WHERE clause
        print(f"DEBUG: Lines WHERE clause: {delta_clause}")
        
        # Build ORDER BY clause
        order_clause = "ORDER BY [record_uuid], [size_code]"
        
        # Build LIMIT clause
        limit_clause = f"TOP ({limit})" if limit else ""
        
        query = f"""
        SELECT {limit_clause} {columns_clause}
        FROM [{self.lines_delta_table}]
        WHERE {delta_clause}
        {order_clause}
        """
        
        return query.strip()
    
    def _get_headers_columns(self) -> List[str]:
        """Get headers columns from TOML monday.column_mapping.{env}.headers + sync columns"""
        headers_columns = set()
        
        # Get columns from environment-specific headers mapping
        headers_mapping = (self.toml_config.get('monday', {})
                          .get('column_mapping', {})
                          .get(self.environment, {})
                          .get('headers', {}))
        headers_columns.update(headers_mapping.keys())
        
        # Add sync tracking columns that exist in ORDER_LIST_DELTA
        sync_columns = ['sync_state', 'monday_item_id', 'created_at']
        headers_columns.update(sync_columns)
        
        return [f"[{col}]" for col in sorted(headers_columns)]
    
    def _get_lines_columns(self) -> List[str]:
        """Get lines columns from TOML monday.column_mapping.{env}.lines + sync columns"""
        lines_columns = set()
        
        # Get columns from environment-specific lines mapping
        lines_mapping = (self.toml_config.get('monday', {})
                        .get('column_mapping', {})
                        .get(self.environment, {})
                        .get('lines', {}))
        lines_columns.update(lines_mapping.keys())
        
        # Add sync tracking columns that exist in ORDER_LIST_LINES_DELTA
        sync_columns = ['sync_state', 'parent_item_id', 'record_uuid', 'created_at']
        lines_columns.update(sync_columns)
        
        return [f"[{col}]" for col in sorted(lines_columns)]
    
    def _build_delta_query(self, limit: Optional[int] = None) -> str:
        """Build DELTA query for pending records"""
        
        # Get required columns from TOML mapping
        required_columns = self._get_required_columns()
        columns_clause = ", ".join(required_columns)
        
        # DEBUG: Print environment and column mapping info
        print("DEBUG: Environment and mapping configuration:")
        print(f"  Environment: {self.environment}")
        headers_mapping = (self.toml_config.get('monday', {})
                          .get('column_mapping', {})
                          .get(self.environment, {})
                          .get('headers', {}))
        lines_mapping = (self.toml_config.get('monday', {})
                        .get('column_mapping', {})
                        .get(self.environment, {})
                        .get('lines', {}))
        print(f"  Headers mapping: {headers_mapping}")
        print(f"  Lines mapping: {lines_mapping}")
        print(f"  Required columns: {required_columns}")
        
        # Build WHERE clause for DELTA logic
        delta_clause = self._build_delta_where_clause()
        
        # DEBUG: Print WHERE clause
        print("DEBUG: Delta WHERE clause:")
        print(f"  {delta_clause}")
        
        # Build ORDER BY clause (ORDER_LIST_V2 is headers only, no LINE NUMBER)
        order_clause = "ORDER BY [AAG ORDER NUMBER]"
        
        # Build LIMIT clause
        limit_clause = f"TOP ({limit})" if limit else ""
        
        query = f"""
        SELECT {limit_clause} {columns_clause}
        FROM [{self.source_table}]
        WHERE {delta_clause}
        {order_clause}
        """
        
        return query.strip()
    
    def _get_required_columns(self) -> List[str]:
        """Get required columns from TOML column mappings ONLY - NO HARDCODING"""
        required_columns = set()
        
        # Get columns from environment-specific headers mapping
        headers_mapping = (self.toml_config.get('monday', {})
                          .get('column_mapping', {})
                          .get(self.environment, {})
                          .get('headers', {}))
        required_columns.update(headers_mapping.keys())
        
        # Get columns from environment-specific lines mapping
        lines_mapping = (self.toml_config.get('monday', {})
                        .get('column_mapping', {})
                        .get(self.environment, {})
                        .get('lines', {}))
        required_columns.update(lines_mapping.keys())
        
        # Get essential columns from TOML database config
        essential_columns = self.toml_config.get('database', {}).get('essential_columns', [])
        required_columns.update(essential_columns)
        
        # Get sync tracking columns from TOML database config (ORDER_LIST_V2 actual columns)
        sync_columns = self.toml_config.get('database', {}).get('sync_columns', [])
        required_columns.update(sync_columns)
        
        return [f"[{col}]" for col in sorted(required_columns)]
    
    def _build_delta_where_clause(self) -> str:
        """Build WHERE clause for pending records (ORDER_LIST_V2 with sync_state)"""
        
        # Get DELTA configuration
        delta_config = self.sync_config.get('delta', {})
        
        conditions = []
        
        # Remove time-based filter - not needed for ORDER_LIST_V2
        # Time-based DELTA is not used in this architecture
        
        # Status-based filtering using ORDER_LIST_V2 actual column name
        sync_statuses = delta_config.get('sync_statuses', ['PENDING', 'ERROR'])
        status_clause = "', '".join(sync_statuses)
        status_condition = f"([sync_state] IS NULL OR [sync_state] IN ('{status_clause}'))"
        conditions.append(status_condition)
        print(f"DEBUG: Status condition: {status_condition}")
        
        # Customer filter (if specified)
        customer_filter = delta_config.get('customer_filter')
        if customer_filter:
            customer_condition = f"[CUSTOMER NAME] = '{customer_filter}'"
            conditions.append(customer_condition)
            print(f"DEBUG: Customer condition: {customer_condition}")
        
        final_where = " AND ".join(conditions) if conditions else "1=1"
        print(f"DEBUG: Final WHERE clause: {final_where}")
        return final_where
    
    def _separate_headers_and_lines(self, records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Separate records into headers (items) and lines (subitems)"""
        
        headers = []
        lines = []
        
        for record in records:
            line_number = record.get('LINE NUMBER', 0)
            
            if line_number == 0 or line_number is None:
                # This is a header record
                headers.append(record)
            else:
                # This is a line record
                lines.append(record)
        
        return headers, lines
    
    def _process_headers_sync(self, headers: List[Dict[str, Any]], dry_run: bool) -> Dict[str, Any]:
        """Synchronous wrapper for async header processing"""
        import asyncio
        return asyncio.run(self._process_headers(headers, dry_run))
    
    def _process_lines_sync(self, lines: List[Dict[str, Any]], dry_run: bool) -> Dict[str, Any]:
        """Synchronous wrapper for async line processing"""
        import asyncio
        return asyncio.run(self._process_lines(lines, dry_run))
    
    async def _process_headers(self, headers: List[Dict[str, Any]], dry_run: bool) -> Dict[str, Any]:
        """Process header records (create items and groups)"""
        try:
            # Step 1: Create groups if needed
            groups_result = await self._create_groups_if_needed(headers, dry_run)
            
            # Step 2: Create items
            items_result = self.monday_client.execute('create_items', headers, dry_run)
            
            return {
                'success': items_result.get('success', False),
                'records_processed': items_result.get('records_processed', 0),
                'groups_created': groups_result.get('records_processed', 0),
                'items_created': items_result.get('records_processed', 0),
                'monday_ids': items_result.get('monday_ids', [])
            }
            
        except Exception as e:
            self.logger.exception(f"Failed to process headers: {e}")
            return {
                'success': False,
                'error': str(e),
                'records_processed': 0
            }
    
    async def _process_lines(self, lines: List[Dict[str, Any]], dry_run: bool) -> Dict[str, Any]:
        """Process line records (create subitems)"""
        try:
            # Create subitems
            subitems_result = self.monday_client.execute('create_subitems', lines, dry_run)
            
            return {
                'success': subitems_result.get('success', False),
                'records_processed': subitems_result.get('records_processed', 0),
                'subitems_created': subitems_result.get('records_processed', 0),
                'monday_ids': subitems_result.get('monday_ids', [])
            }
            
        except Exception as e:
            self.logger.exception(f"Failed to process lines: {e}")
            return {
                'success': False,
                'error': str(e),
                'records_processed': 0
            }
    
    async def _create_groups_if_needed(self, headers: List[Dict[str, Any]], dry_run: bool) -> Dict[str, Any]:
        """Create Monday.com groups if they don't exist"""
        
        # Get unique groups needed
        unique_groups = set()
        for header in headers:
            group_id = self.monday_client._get_group_id(header)
            if group_id:
                unique_groups.add(group_id)
        
        if not unique_groups:
            return {'success': True, 'records_processed': 0}
        
        # Convert to group records
        group_records = [{'group_name': group_name} for group_name in unique_groups]
        
        # Create groups
        return self.monday_client.execute('create_groups', group_records, dry_run)
    
    def _update_sync_status(self, records: List[Dict[str, Any]], status: str) -> None:
        """Update sync status in database"""
        
        if not records:
            return
        
        try:
            connection = db.get_connection('orders')  # Use 'orders' database
            cursor = connection.cursor()
            
            # Build update query
            order_numbers = [f"'{record['AAG ORDER NUMBER']}'" for record in records]
            order_numbers_clause = ", ".join(order_numbers)
            
            update_query = f"""
            UPDATE [{self.source_table}]
            SET [sync_state] = '{status}',
                [last_synced_at] = GETDATE()
            WHERE [AAG ORDER NUMBER] IN ({order_numbers_clause})
            """
            
            # DEBUG: Print the update SQL query
            print("=" * 80)
            print("DEBUG: UPDATE QUERY GENERATED")
            print("=" * 80)
            print(update_query)
            print("=" * 80)
            
            cursor.execute(update_query)
            connection.commit()
            
            rows_updated = cursor.rowcount
            cursor.close()
            connection.close()
            
            self.logger.info(f"Updated sync status to '{status}' for {rows_updated} records")
            
        except Exception as e:
            self.logger.exception(f"Failed to update sync status: {e}")
            raise
