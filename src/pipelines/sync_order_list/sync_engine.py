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
import tomli
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
        
        # Load configuration using proper config parser
        from .config_parser import DeltaSyncConfig
        self.config = DeltaSyncConfig.from_toml(toml_config_path, environment='development')
        
        # Load TOML configuration for legacy compatibility  
        self.toml_config = self._load_toml_config()
        
        # Initialize Monday.com API client
        self.monday_client = MondayAPIClient(toml_config_path)
        
        # Environment determination (development vs production)
        self.environment = self.config.environment
        
        # Database configuration using proper config parser - DELTA-FREE ARCHITECTURE
        # Phase 3: Direct main table queries (eliminates DELTA dependency)
        self.headers_table = self.config.target_table              # ORDER_LIST_V2 (main)
        self.lines_table = self.config.lines_table                 # ORDER_LIST_LINES (main)
        
        # Legacy DELTA tables - deprecated but kept for rollback capability
        self.headers_delta_table = self.config.target_table        # Points to main table now
        self.lines_delta_table = self.config.lines_table           # Points to main table now
        
        # Main tables for final sync status propagation
        self.main_headers_table = self.config.target_table
        self.main_lines_table = self.config.lines_table
        
        # Database connection key
        self.db_key = self.config.db_key
        
        # Sync configuration
        sync_config = self.toml_config.get('monday', {}).get('sync', {})
        self.sync_config = sync_config  # Store for later use
        self.batch_size = sync_config.get('batch_size', 100)
        self.delta_hours = sync_config.get('delta_hours', 24)
        
        self.logger.info(f"Sync engine initialized for ORDER_LIST_V2 → Monday.com ({self.environment})")
        self.logger.info(f"DELTA-FREE Architecture: Headers: {self.headers_table}, Lines: {self.lines_table}")
        self.logger.info("Phase 3: Direct main table queries (DELTA tables eliminated)")
    
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
    
    def run_sync(self, dry_run: bool = False, limit: Optional[int] = None, action_types: List[str] = None) -> Dict[str, Any]:
        """
        Execute complete sync workflow with record_uuid cascade logic
        Supports both INSERT and UPDATE operations
        
        Args:
            dry_run: If True, validate queries and API calls but don't execute
            limit: Optional limit on number of records to process
            action_types: List of action types to process (e.g., ['INSERT', 'UPDATE'])
            
        Returns:
            Comprehensive sync results
        """
        # Default to INSERT operations for backwards compatibility
        if action_types is None:
            action_types = ['INSERT']
            
        self.logger.info(f"Starting sync workflow (dry_run: {dry_run}, limit: {limit}, action_types: {action_types})")
        
        sync_start_time = datetime.now()
        
        try:
            # Get pending headers from ORDER_LIST_V2 (main table - DELTA-FREE)
            pending_headers = self._get_pending_headers(limit, action_types)
            
            if not pending_headers:
                self.logger.info(f"No pending headers found for sync (action_types: {action_types})")
                return {'success': True, 'synced': 0, 'message': f'No pending headers for {action_types}'}
            
            self.logger.info(f"Found {len(pending_headers)} pending headers for sync (action_types: {action_types})")
            
            # Group headers by customer and record_uuid for atomic processing
            customer_batches = self._group_by_customer_and_uuid(pending_headers)
            
            total_synced = 0
            all_results = []
            
            # Process each customer batch atomically
            for customer_name, record_batches in customer_batches.items():
                self.logger.info(f"Processing {len(record_batches)} record batches for customer: {customer_name}")
                
                for record_uuid, batch_records in record_batches.items():
                    try:
                        # Process this record_uuid batch atomically
                        batch_result = self._process_record_uuid_batch(record_uuid, batch_records, dry_run)
                        all_results.append(batch_result)
                        
                        if batch_result.get('success', False):
                            total_synced += batch_result.get('records_synced', 0)
                            
                    except Exception as e:
                        self.logger.error(f"Failed to process record_uuid {record_uuid}: {e}")
                        all_results.append({
                            'success': False,
                            'record_uuid': record_uuid,
                            'error': str(e),
                            'records_synced': 0
                        })
            
            # Calculate results
            sync_duration = (datetime.now() - sync_start_time).total_seconds()
            successful_batches = len([r for r in all_results if r.get('success', False)])
            
            result = {
                'success': successful_batches > 0,
                'total_synced': total_synced,
                'batches_processed': len(all_results),
                'successful_batches': successful_batches,
                'failed_batches': len(all_results) - successful_batches,
                'execution_time_seconds': sync_duration,
                'sync_timestamp': sync_start_time,
                'action_types': action_types,
                'dry_run': dry_run,
                'batch_results': all_results
            }
            
            self.logger.info(f"✅ Sync completed! Total synced: {total_synced}, Successful batches: {successful_batches}/{len(all_results)}")
            return result
            
        except Exception as e:
            sync_duration = (datetime.now() - sync_start_time).total_seconds()
            self.logger.error(f"Sync workflow failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_synced': 0,
                'action_types': action_types,
                'execution_time_seconds': sync_duration
            }
    
    def _group_by_customer_and_uuid(self, headers: List[Dict[str, Any]]) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """
        Group headers by customer and record_uuid for atomic batch processing
        
        Returns:
            {customer_name: {record_uuid: [header_records]}}
        """
        customer_batches = {}
        
        for header in headers:
            customer_name = header.get('CUSTOMER NAME', 'UNKNOWN')
            record_uuid = header.get('record_uuid')
            
            if not record_uuid:
                self.logger.warning(f"Header missing record_uuid: {header.get('AAG ORDER NUMBER', 'unknown')}")
                continue
                
            if customer_name not in customer_batches:
                customer_batches[customer_name] = {}
                
            if record_uuid not in customer_batches[customer_name]:
                customer_batches[customer_name][record_uuid] = []
                
            customer_batches[customer_name][record_uuid].append(header)
        
        return customer_batches
    
    def _process_record_uuid_batch(self, record_uuid: str, headers: List[Dict[str, Any]], dry_run: bool) -> Dict[str, Any]:
        """
        Process a single record_uuid batch atomically with SINGLE DATABASE CONNECTION:
        Supports both INSERT and UPDATE operations based on action_type
        1. Create groups (if needed)
        2. For INSERT: Create Monday.com items → get item_ids
        3. For UPDATE: Update Monday.com items using existing monday_item_id
        4. Update ORDER_LIST_V2 with monday_item_id (DELTA-FREE)
        5. Get related lines from ORDER_LIST_LINES (DELTA-FREE)
        6. Inject parent_item_id into lines
        7. For INSERT: Create Monday.com subitems → get subitem_ids
        8. For UPDATE: Update Monday.com subitems using existing monday_subitem_id
        9. Update ORDER_LIST_LINES with monday_subitem_id (DELTA-FREE)
        10. Sync status already written directly to main tables (no propagation needed)
        """
        try:
            self.logger.info(f"Processing record_uuid batch: {record_uuid} ({len(headers)} headers)")
            
            # Determine operation type from headers
            action_types = set(header.get('action_type', 'INSERT') for header in headers)
            operation_type = list(action_types)[0] if len(action_types) == 1 else 'MIXED'
            
            self.logger.info(f"Batch operation type: {operation_type} (action_types: {action_types})")
            
            if dry_run:
                return {
                    'success': True,
                    'record_uuid': record_uuid,
                    'records_synced': len(headers),
                    'operation_type': operation_type,
                    'dry_run': True,
                    'message': f'DRY RUN: Would process {len(headers)} headers for {operation_type}'
                }
            
            # Step 1: Create groups if needed (for both INSERT and UPDATE)
            groups_result = self._create_groups_for_headers(headers, dry_run)
            if not groups_result.get('success', False):
                return {
                    'success': False,
                    'record_uuid': record_uuid,
                    'error': 'Group creation failed',
                    'operation_type': operation_type,
                    'records_synced': 0
                }
            
            # Step 2: Handle items based on operation type
            if operation_type == 'UPDATE':
                # For UPDATE: Update existing Monday.com items
                items_result = self.monday_client.execute('update_items', headers, dry_run)
                operation_name = 'Item update'
            else:
                # For INSERT: Create new Monday.com items
                items_result = self.monday_client.execute('create_items', headers, dry_run)
                operation_name = 'Item creation'
            
            if not items_result.get('success', False):
                return {
                    'success': False,
                    'record_uuid': record_uuid,
                    'error': f'{operation_name} failed',
                    'operation_type': operation_type,
                    'records_synced': 0
                }
            
            monday_item_ids = items_result.get('monday_ids', [])
            
            # DIRECT DATABASE CONNECTION (NO TRANSACTION NESTING)
            connection = db.get_connection('orders')
            try:
                # Step 3: Update ORDER_LIST_V2 with monday_item_id
                if operation_type == 'UPDATE':
                    # For UPDATE: Don't update monday_item_id (it should stay the same)
                    # Just update sync status to SYNCED
                    self._update_sync_status_only_conn(record_uuid, connection)
                else:
                    # For INSERT: Update with new monday_item_id from API response
                    self._update_headers_delta_with_item_ids_conn(record_uuid, monday_item_ids, connection)
                
                # Step 4: Get related lines for this record_uuid
                related_lines = self._get_lines_by_record_uuid_conn(record_uuid, connection)
                
                if related_lines:
                    # Determine line operation type
                    line_action_types = set(line.get('action_type', 'INSERT') for line in related_lines)
                    line_operation_type = list(line_action_types)[0] if len(line_action_types) == 1 else 'MIXED'
                    
                    # Step 5: Inject parent_item_id into lines
                    lines_with_parent = self._inject_parent_item_ids(related_lines, record_uuid, monday_item_ids)
                    
                    # Step 6: Handle subitems based on operation type
                    if line_operation_type == 'UPDATE':
                        # For UPDATE: Update existing Monday.com subitems
                        subitems_result = self.monday_client.execute('update_subitems', lines_with_parent, dry_run)
                        subitem_operation_name = 'Subitem update'
                    else:
                        # For INSERT: Create new Monday.com subitems
                        subitems_result = self.monday_client.execute('create_subitems', lines_with_parent, dry_run)
                        subitem_operation_name = 'Subitem creation'
                    
                    if subitems_result.get('success', False):
                        monday_subitem_ids = subitems_result.get('monday_ids', [])
                        
                        # Step 7: Update ORDER_LIST_LINES with monday_subitem_id (DIRECT CONNECTION)
                        self._update_lines_delta_with_subitem_ids(record_uuid, monday_subitem_ids, connection)
                    else:
                        self.logger.warning(f"{subitem_operation_name} failed for record_uuid {record_uuid}")
                
                # Manual commit (NO AUTO-COMMIT TRANSACTION NESTING)
                connection.commit()
                
            except Exception as e:
                connection.rollback()
                raise
            finally:
                connection.close()
            
            total_records = len(headers) + len(related_lines) if related_lines else len(headers)
            
            return {
                'success': True,
                'record_uuid': record_uuid,
                'records_synced': total_records,
                'headers_synced': len(headers),
                'lines_synced': len(related_lines) if related_lines else 0,
                'operation_type': operation_type,
                'monday_item_ids': monday_item_ids
            }
            
        except Exception as e:
            self.logger.exception(f"Failed to process record_uuid {record_uuid}: {e}")
            return {
                'success': False,
                'record_uuid': record_uuid,
                'error': str(e),
                'operation_type': operation_type if 'operation_type' in locals() else 'UNKNOWN',
                'records_synced': 0
            }
    
    def _create_groups_for_headers(self, headers: List[Dict[str, Any]], dry_run: bool) -> Dict[str, Any]:
        """Create Monday.com groups for headers if needed"""
        try:
            # Extract unique group names needed
            unique_groups = set()
            for header in headers:
                group_name = self._get_group_name_from_header(header)
                if group_name:
                    unique_groups.add(group_name)
            
            if not unique_groups:
                return {'success': True, 'groups_created': 0}
            
            # Convert to group records
            group_records = [{'group_name': group_name} for group_name in unique_groups]
            
            # Create groups via Monday.com API
            return self.monday_client.execute('create_groups', group_records, dry_run)
            
        except Exception as e:
            self.logger.exception(f"Failed to create groups: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_group_name_from_header(self, header: Dict[str, Any]) -> Optional[str]:
        """Extract group name from header record using TOML mapping"""
        # Check if group mapping exists in TOML
        group_mapping = (self.toml_config.get('monday', {})
                        .get('sync', {})
                        .get('groups', {}))
        
        if not group_mapping:
            return None
            
        # Get the database field that maps to group
        group_field = group_mapping.get('map_to', 'CUSTOMER NAME')
        return header.get(group_field)
    
    def _get_lines_by_record_uuid(self, record_uuid: str) -> List[Dict[str, Any]]:
        """Get lines from ORDER_LIST_LINES (main table - DELTA-FREE) for specific record_uuid"""
        with db.get_connection(self.db_key) as connection:
            return self._get_lines_by_record_uuid_conn(record_uuid, connection)

    def _get_lines_by_record_uuid_conn(self, record_uuid: str, connection) -> List[Dict[str, Any]]:
        """Get lines from ORDER_LIST_LINES (main table - DELTA-FREE) for specific record_uuid - CONNECTION PASSING"""
        try:
            lines_query = f"""
            SELECT {', '.join(self._get_lines_columns())}
            FROM [{self.lines_table}]
            WHERE [record_uuid] = '{record_uuid}'
            AND [sync_state] = 'PENDING'
            ORDER BY [size_code]
            """
            
            cursor = connection.cursor()
            cursor.execute(lines_query)
            
            columns = [column[0] for column in cursor.description]
            records = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            self.logger.info(f"Retrieved {len(records)} lines for record_uuid: {record_uuid}")
            return records
                
        except Exception as e:
            self.logger.error(f"Failed to get lines for record_uuid {record_uuid}: {e}")
            return []
    
    def _inject_parent_item_ids(self, lines: List[Dict[str, Any]], record_uuid: str, item_ids: List[str]) -> List[Dict[str, Any]]:
        """Inject Monday.com parent item IDs into lines before creating subitems"""
        if not item_ids:
            return lines
            
        # Use first item_id as parent (assuming 1 header per record_uuid)
        parent_item_id = item_ids[0]
        
        # Add parent_item_id to each line record
        for line in lines:
            line['parent_item_id'] = parent_item_id
        
        self.logger.info(f"Injected parent_item_id {parent_item_id} into {len(lines)} lines for record_uuid: {record_uuid}")
        return lines
    
    def _update_headers_delta_with_item_ids(self, record_uuid: str, item_ids: List[str]) -> None:
        """Update ORDER_LIST_V2 (main table - DELTA-FREE) with Monday.com item IDs"""
        with db.get_connection('orders') as connection:
            self._update_headers_delta_with_item_ids_conn(record_uuid, item_ids, connection)
            connection.commit()

    def _update_headers_delta_with_item_ids_conn(self, record_uuid: str, item_ids: List[str], connection) -> None:
        """Update ORDER_LIST_V2 (main table - DELTA-FREE) with Monday.com item IDs - CONNECTION PASSING"""
        if not item_ids:
            return
            
        try:
            # Use first item_id (assuming 1 header per record_uuid)
            monday_item_id = item_ids[0]
            
            # Convert string ID to integer for BIGINT column
            monday_item_id_int = int(monday_item_id)
            
            update_query = f"""
            UPDATE [{self.headers_table}]
            SET [monday_item_id] = {monday_item_id_int},
                [sync_state] = 'SYNCED',
                [sync_completed_at] = GETUTCDATE()
            WHERE [record_uuid] = '{record_uuid}'
            """
            
            cursor = connection.cursor()
            cursor.execute(update_query)
            # Don't commit here - let caller handle transaction
            
            rows_updated = cursor.rowcount
            self.logger.info(f"Updated {rows_updated} headers in main table (DELTA-FREE) with item_id: {monday_item_id}")
                
        except Exception as e:
            self.logger.exception(f"Failed to update headers with item IDs: {e}")
            raise

    def _update_sync_status_only_conn(self, record_uuid: str, connection) -> None:
        """Update sync status only for UPDATE operations (don't change monday_item_id)"""
        try:
            update_query = f"""
            UPDATE [{self.headers_table}]
            SET [sync_state] = 'SYNCED',
                [sync_completed_at] = GETUTCDATE()
            WHERE [record_uuid] = '{record_uuid}'
            """
            
            cursor = connection.cursor()
            cursor.execute(update_query)
            # Don't commit here - let caller handle transaction
            
            rows_updated = cursor.rowcount
            self.logger.info(f"Updated {rows_updated} headers sync status to SYNCED for UPDATE operation")
                
        except Exception as e:
            self.logger.exception(f"Failed to update sync status: {e}")
            raise
    
    def _update_lines_delta_with_subitem_ids(self, record_uuid: str, subitem_ids: List[str], connection=None) -> None:
        """Update ORDER_LIST_LINES (main table - DELTA-FREE) with Monday.com subitem IDs - BATCH UPDATE"""
        if not subitem_ids:
            return
            
        try:
            # Get lines that need updating
            lines = self._get_lines_by_record_uuid(record_uuid)
            
            if len(lines) != len(subitem_ids):
                self.logger.warning(f"Mismatch: {len(lines)} lines vs {len(subitem_ids)} subitem IDs for record_uuid: {record_uuid}")
            
            if not lines:
                self.logger.warning(f"No lines found for record_uuid: {record_uuid}")
                return
            
            # Build batch UPDATE query using CASE statements (ELIMINATES NESTING)
            case_statements = []
            where_conditions = []
            
            for i, line in enumerate(lines):
                if i < len(subitem_ids):
                    lines_uuid = line.get('line_uuid')
                    subitem_id = subitem_ids[i]
                    
                    case_statements.append(f"WHEN '{lines_uuid}' THEN '{subitem_id}'")
                    where_conditions.append(f"'{lines_uuid}'")
            
            if not case_statements:
                self.logger.warning(f"No valid line updates to process for record_uuid: {record_uuid}")
                return
            
            # Single batch UPDATE query (NO NESTED CONNECTIONS)
            batch_update_query = f"""
            UPDATE [{self.lines_table}]
            SET [monday_subitem_id] = CASE [line_uuid]
                    {' '.join(case_statements)}
                    ELSE [monday_subitem_id] 
                END,
                [sync_state] = 'SYNCED',
                [sync_completed_at] = GETUTCDATE()
            WHERE [line_uuid] IN ({', '.join(where_conditions)})
            """
            
            # Use provided connection or create new one (CONNECTION PASSING PATTERN)
            if connection:
                cursor = connection.cursor()
                cursor.execute(batch_update_query)
                # Don't commit here - let caller handle transaction
                
                rows_updated = cursor.rowcount
                self.logger.info(f"Batch updated {rows_updated} lines with Monday.com subitem IDs for record_uuid: {record_uuid}")
            else:
                # Fallback to single connection (for standalone calls)
                with db.get_connection('orders') as standalone_connection:
                    cursor = standalone_connection.cursor()
                    cursor.execute(batch_update_query)
                    standalone_connection.commit()
                    
                    rows_updated = cursor.rowcount
                    self.logger.info(f"Batch updated {rows_updated} lines with Monday.com subitem IDs for record_uuid: {record_uuid}")
                        
        except Exception as e:
            self.logger.error(f"Failed to update lines with subitem IDs: {e}")
            raise
    
    def _propagate_sync_status_to_main_tables(self, record_uuid: str) -> None:
        """DELTA-FREE Architecture: Status already written to main tables - this method is now a no-op"""
        # In DELTA-free architecture, sync status is written directly to main tables
        # This method is kept for backwards compatibility but does nothing
        self.logger.info(f"DELTA-FREE: Sync status already written directly to main tables for record_uuid: {record_uuid}")
        pass
    
    def _get_pending_headers(self, limit: Optional[int] = None, action_types: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get headers records pending Monday.com sync from ORDER_LIST_V2 (main table - DELTA-FREE)
        
        Args:
            limit: Optional limit on number of records
            action_types: List of action types to filter by (e.g., ['INSERT', 'UPDATE'])
        """
        # Build headers query for ORDER_LIST_V2 (main table)
        headers_query = self._build_headers_query(limit, action_types)
        
        # DEBUG: Print the generated SQL query
        print("=" * 80)
        print("DEBUG: HEADERS MAIN TABLE QUERY GENERATED (DELTA-FREE)")
        print("=" * 80)
        print(headers_query)
        print("=" * 80)
        
        try:
            with db.get_connection('orders') as connection:
                cursor = connection.cursor()
                cursor.execute(headers_query)
                
                columns = [column[0] for column in cursor.description]
                records = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                self.logger.info(f"Retrieved {len(records)} headers from {self.headers_table}")
                return records
                
        except Exception as e:
            self.logger.error(f"Failed to get pending headers: {e}")
            raise
    
    def _get_pending_lines(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get lines records pending Monday.com sync from ORDER_LIST_LINES (main table - DELTA-FREE)
        """
        # Build lines query for ORDER_LIST_LINES (main table)
        lines_query = self._build_lines_query(limit)
        
        # DEBUG: Print the generated SQL query
        print("=" * 80)
        print("DEBUG: LINES MAIN TABLE QUERY GENERATED (DELTA-FREE)")
        print("=" * 80)
        print(lines_query)
        print("=" * 80)
        
        try:
            with db.get_connection('orders') as connection:
                cursor = connection.cursor()
                cursor.execute(lines_query)
                
                columns = [column[0] for column in cursor.description]
                records = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                self.logger.info(f"Retrieved {len(records)} lines from {self.lines_table}")
                return records
                
        except Exception as e:
            self.logger.error(f"Failed to get pending lines: {e}")
            raise
    
    def _build_headers_query(self, limit: Optional[int] = None, action_types: List[str] = None) -> str:
        """Build query for pending headers from ORDER_LIST_V2 (main table - DELTA-FREE)"""
        
        # Get headers columns from TOML mapping
        headers_columns = self._get_headers_columns()
        columns_clause = ", ".join(headers_columns)
        
        # Default to INSERT operations if no action types specified
        if action_types is None:
            action_types = ['INSERT']
        
        # DEBUG: Print environment and column mapping info
        print("DEBUG: Headers query configuration (DELTA-FREE):")
        print(f"  Environment: {self.environment}")
        print(f"  Table: {self.headers_table}")
        print(f"  Action types: {action_types}")
        print(f"  Headers columns: {headers_columns}")
        
        # Build WHERE clause for main table logic (sync_state = 'PENDING' AND action_type IN (...))
        action_type_clause = "', '".join(action_types)
        main_table_clause = f"([sync_state] = 'PENDING' AND [action_type] IN ('{action_type_clause}'))"
        
        # DEBUG: Print WHERE clause
        print(f"DEBUG: Headers WHERE clause: {main_table_clause}")
        
        # Build ORDER BY clause
        order_clause = "ORDER BY [AAG ORDER NUMBER]"
        
        # Build LIMIT clause
        limit_clause = f"TOP ({limit})" if limit else ""
        
        query = f"""
        SELECT {limit_clause} {columns_clause}
        FROM [{self.headers_table}]
        WHERE {main_table_clause}
        {order_clause}
        """
        
        return query.strip()
    
    def _build_lines_query(self, limit: Optional[int] = None) -> str:
        """Build query for pending lines from ORDER_LIST_LINES (main table - DELTA-FREE)"""
        
        # Get lines columns from TOML mapping
        lines_columns = self._get_lines_columns()
        columns_clause = ", ".join(lines_columns)
        
        # DEBUG: Print environment and column mapping info
        print("DEBUG: Lines query configuration (DELTA-FREE):")
        print(f"  Environment: {self.environment}")
        print(f"  Table: {self.lines_table}")
        print(f"  Lines columns: {lines_columns}")
        
        # Build WHERE clause for main table logic (sync_state = 'PENDING')
        main_table_clause = "([sync_state] = 'PENDING')"
        
        # DEBUG: Print WHERE clause
        print(f"DEBUG: Lines WHERE clause: {main_table_clause}")
        
        # Build ORDER BY clause
        order_clause = "ORDER BY [record_uuid], [size_code]"
        
        # Build LIMIT clause
        limit_clause = f"TOP ({limit})" if limit else ""
        
        query = f"""
        SELECT {limit_clause} {columns_clause}
        FROM [{self.lines_table}]
        WHERE {main_table_clause}
        {order_clause}
        """
        
        return query.strip()
    
    def _get_headers_columns(self) -> List[str]:
        """Get headers columns from TOML monday.column_mapping.{env}.headers + sync columns (DELTA-FREE)"""
        headers_columns = set()
        
        # Get columns from environment-specific headers mapping
        headers_mapping = (self.toml_config.get('monday', {})
                          .get('column_mapping', {})
                          .get(self.environment, {})
                          .get('headers', {}))
        headers_columns.update(headers_mapping.keys())
        
        # Add CRITICAL sync tracking columns from main table ORDER_LIST_V2
        # These are REQUIRED for DELTA-FREE sync logic!
        critical_columns = [
            'record_uuid', 'action_type', 'sync_state', 'sync_pending_at',
            'monday_item_id', 'sync_completed_at', 'created_at'
        ]
        headers_columns.update(critical_columns)
        
        return [f"[{col}]" for col in sorted(headers_columns)]
    
    def _get_lines_columns(self) -> List[str]:
        """Get lines columns from TOML monday.column_mapping.{env}.lines + sync columns (DELTA-FREE)"""
        lines_columns = set()
        
        # Get columns from environment-specific lines mapping
        lines_mapping = (self.toml_config.get('monday', {})
                        .get('column_mapping', {})
                        .get(self.environment, {})
                        .get('lines', {}))
        lines_columns.update(lines_mapping.keys())
        
        # Add CRITICAL sync tracking columns from main table ORDER_LIST_LINES
        # These are REQUIRED for DELTA-FREE sync logic!
        critical_columns = [
            'line_uuid', 'record_uuid', 'action_type', 'sync_state',
            'sync_pending_at', 'monday_item_id', 'monday_subitem_id',
            'monday_parent_id', 'sync_completed_at', 'created_at'
        ]
        lines_columns.update(critical_columns)
        
        return [f"[{col}]" for col in sorted(lines_columns)]
