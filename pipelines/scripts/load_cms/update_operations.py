# New file: update_operations.py
"""
Monday.com Update Operations
Handles update workflows using existing staging infrastructure
"""

from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import json
import uuid
from datetime import datetime
from .staging_operations import StagingOperations
from .monday_api_client import MondayApiClient
from .metadata_processor import process_metadata_columns
from .conversion_functions import safe_numeric_convert, safe_date_convert, safe_string_convert

class UpdateOperations:
    """Handle update workflows using staging infrastructure"""
    
    def __init__(self, config: StagingConfig):
        self.config = config
        self.staging_ops = StagingOperations(config)
        self.monday_client = MondayApiClient(config.monday_api_key)
        self.logger = get_logger(__name__)
        
    def stage_updates_from_query(self, 
                                board_id: str,
                                source_query: str,
                                column_mappings: Dict[str, str],
                                update_type: str = 'update_items',
                                batch_id: Optional[str] = None) -> str:
        """
        Stage updates from SQL query results
        
        Args:
            board_id: Monday.com board ID
            source_query: SQL query to get update data (must include key columns)
            column_mappings: {sql_column: monday_column_id}
            update_type: 'update_items', 'update_subitems', 'update_groups'
            batch_id: Optional batch ID for tracking (auto-generated if None)
        
        Returns:
            batch_id for tracking and processing
        """
        if not batch_id:
            batch_id = f"upd_{update_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        self.logger.info(f"Staging updates: batch_id={batch_id}, board_id={board_id}, type={update_type}")
        
        # Load metadata for board
        metadata = self._load_board_metadata(board_id)
        
        # Validate update configuration
        validation_result = self._validate_update_operation(metadata, column_mappings, update_type)
        if not validation_result['valid']:
            raise ValueError(f"Update validation failed: {validation_result['errors']}")
        
        # Execute source query
        df = pd.read_sql(source_query, self.staging_ops.get_connection())
        self.logger.info(f"Source query returned {len(df)} rows")
        
        # Validate required columns exist
        required_columns = self._get_required_columns(update_type)
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Transform data using metadata mappings
        transformed_updates = self._transform_for_updates(df, column_mappings, metadata, update_type)
        
        # Stage the updates with validation
        staged_count = self._insert_updates_to_staging(
            transformed_updates, 
            update_type,
            batch_id,
            source_query,
            metadata
        )
        
        self.logger.info(f"Staged {staged_count} updates for batch {batch_id}")
        return batch_id
    
    def validate_staged_updates(self, batch_id: str) -> Dict[str, Any]:
        """
        Validate staged updates before execution
        
        Args:
            batch_id: Batch ID to validate
            
        Returns:
            Validation result with detailed report
        """
        self.logger.info(f"Validating staged updates for batch {batch_id}")
        
        # Get staged updates
        staged_updates = self._get_staged_updates(batch_id)
        
        validation_results = {
            'batch_id': batch_id,
            'total_updates': len(staged_updates),
            'valid_updates': 0,
            'invalid_updates': 0,
            'validation_errors': [],
            'warnings': []
        }
        
        for update in staged_updates:
            update_validation = self._validate_single_update(update)
            
            if update_validation['valid']:
                validation_results['valid_updates'] += 1
                self._mark_update_valid(update['id'])
            else:
                validation_results['invalid_updates'] += 1
                validation_results['validation_errors'].extend(update_validation['errors'])
                self._mark_update_invalid(update['id'], update_validation['errors'])
        
        validation_results['success_rate'] = (
            validation_results['valid_updates'] / validation_results['total_updates'] * 100
            if validation_results['total_updates'] > 0 else 0
        )
        
        self.logger.info(f"Validation complete: {validation_results['valid_updates']}/{validation_results['total_updates']} valid")
        return validation_results
    
    def process_staged_updates(self, batch_id: str, dry_run: bool = True) -> Dict[str, Any]:
        """
        Process updates from staging tables
        
        Args:
            batch_id: Batch ID to process
            dry_run: If True, simulate updates without executing
            
        Returns:
            Processing results with detailed metrics
        """
        self.logger.info(f"Processing staged updates: batch_id={batch_id}, dry_run={dry_run}")
        
        # Get validated updates only
        updates = self._get_validated_updates(batch_id)
        
        if not updates:
            return {
                'batch_id': batch_id,
                'status': 'NO_VALID_UPDATES',
                'message': 'No valid updates found for processing'
            }
        
        if dry_run:
            return self._generate_dry_run_report(updates, batch_id)
        
        # Execute updates with comprehensive error handling
        processing_results = {
            'batch_id': batch_id,
            'total_updates': len(updates),
            'successful_updates': 0,
            'failed_updates': 0,
            'results': [],
            'errors': [],
            'processing_time': 0
        }
        
        start_time = datetime.now()
        
        try:
            # Group updates by operation type for efficient processing
            grouped_updates = self._group_updates_by_type(updates)
            
            for update_type, type_updates in grouped_updates.items():
                self.logger.info(f"Processing {len(type_updates)} {update_type} updates")
                
                type_results = self._process_updates_by_type(update_type, type_updates)
                processing_results['results'].extend(type_results)
                
                # Update metrics
                successful = sum(1 for r in type_results if r['success'])
                failed = len(type_results) - successful
                
                processing_results['successful_updates'] += successful
                processing_results['failed_updates'] += failed
        
        except Exception as e:
            self.logger.error(f"Batch processing failed: {e}")
            processing_results['errors'].append(f"Batch processing error: {str(e)}")
        
        finally:
            processing_results['processing_time'] = (datetime.now() - start_time).total_seconds()
        
        # Update batch status
        self._update_batch_status(batch_id, processing_results)
        
        self.logger.info(
            f"Batch {batch_id} complete: {processing_results['successful_updates']} success, "
            f"{processing_results['failed_updates']} failed"
        )
        
        return processing_results
    
    def rollback_batch(self, batch_id: str, reason: str) -> Dict[str, Any]:
        """
        Rollback updates from a batch using audit trail
        
        Args:
            batch_id: Batch ID to rollback
            reason: Reason for rollback
            
        Returns:
            Rollback result summary
        """
        self.logger.info(f"Rolling back batch {batch_id}: {reason}")
        
        # Get audit records for the batch
        audit_records = self._get_batch_audit_records(batch_id)
        
        if not audit_records:
            return {
                'batch_id': batch_id,
                'status': 'NO_ROLLBACK_DATA',
                'message': 'No audit records found for rollback'
            }
        
        rollback_results = {
            'batch_id': batch_id,
            'reason': reason,
            'total_rollbacks': len(audit_records),
            'successful_rollbacks': 0,
            'failed_rollbacks': 0,
            'rollback_errors': []
        }
        
        # Execute rollbacks
        for audit_record in audit_records:
            try:
                rollback_result = self._execute_rollback(audit_record)
                if rollback_result['success']:
                    rollback_results['successful_rollbacks'] += 1
                    self._mark_audit_rolled_back(audit_record['audit_id'], reason)
                else:
                    rollback_results['failed_rollbacks'] += 1
                    rollback_results['rollback_errors'].append(rollback_result['error'])
            
            except Exception as e:
                rollback_results['failed_rollbacks'] += 1
                rollback_results['rollback_errors'].append(str(e))
        
        self.logger.info(
            f"Rollback complete: {rollback_results['successful_rollbacks']} success, "
            f"{rollback_results['failed_rollbacks']} failed"
        )
        
        return rollback_results
    
    # Private helper methods
    def _load_board_metadata(self, board_id: str) -> Dict[str, Any]:
        """Load board metadata from configuration"""
        metadata_path = self.config.metadata_dir / f"board_{board_id}_metadata.json"
        
        if not metadata_path.exists():
            raise FileNotFoundError(f"Board metadata not found: {metadata_path}")
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _validate_update_operation(self, metadata: Dict, mappings: Dict, update_type: str) -> Dict[str, Any]:
        """Validate update operation against metadata and Monday.com schema"""
        validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Validate update type is supported
        supported_types = ['update_items', 'update_subitems', 'update_groups', 'update_boards']
        if update_type not in supported_types:
            validation['valid'] = False
            validation['errors'].append(f"Unsupported update type: {update_type}")
        
        # Validate column mappings against metadata
        metadata_columns = {col['monday_id']: col for col in metadata.get('columns', [])}
        
        for sql_col, monday_col_id in mappings.items():
            if monday_col_id not in metadata_columns:
                validation['valid'] = False
                validation['errors'].append(f"Monday column '{monday_col_id}' not found in metadata")
            else:
                col_meta = metadata_columns[monday_col_id]
                if col_meta.get('exclude', False):
                    validation['warnings'].append(f"Column '{monday_col_id}' is marked as excluded")
        
        return validation
    
    def _get_required_columns(self, update_type: str) -> List[str]:
        """Get required columns for each update type"""
        requirements = {
            'update_items': ['monday_item_id'],
            'update_subitems': ['monday_item_id', 'monday_subitem_id'],
            'update_groups': ['monday_group_id'],
            'update_boards': ['monday_board_id']
        }
        return requirements.get(update_type, [])
    
    def _transform_for_updates(self, df: pd.DataFrame, mappings: Dict, metadata: Dict, update_type: str) -> List[Dict]:
        """Transform DataFrame to update operations using metadata"""
        updates = []
        
        # Get conversion functions from metadata
        columns_meta, _ = process_metadata_columns(metadata)
        
        for _, row in df.iterrows():
            update = {
                'update_operation': update_type,
                'board_id': metadata['board_id'],
                'column_values': {}
            }
            
            # Set key fields based on update type
            if update_type == 'update_items':
                update['monday_item_id'] = row['monday_item_id']
            elif update_type == 'update_subitems':
                update['monday_item_id'] = row['monday_item_id'] 
                update['monday_subitem_id'] = row['monday_subitem_id']
            elif update_type == 'update_groups':
                update['monday_group_id'] = row['monday_group_id']
            
            # Transform column values using metadata conversion
            for sql_col, monday_col_id in mappings.items():
                if sql_col in df.columns and monday_col_id in columns_meta:
                    raw_value = row[sql_col]
                    col_meta = columns_meta[monday_col_id]
                    
                    # Apply conversion based on metadata
                    converted_value = self._apply_conversion(raw_value, col_meta)
                    
                    if converted_value is not None:
                        update['column_values'][monday_col_id] = converted_value
            
            updates.append(update)
        
        return updates
    
    def _apply_conversion(self, value: Any, col_meta: Dict) -> Any:
        """Apply conversion logic based on column metadata"""
        if pd.isna(value) or value is None:
            return None
        
        monday_type = col_meta.get('type', '')
        conversion_logic = col_meta.get('conversion_logic')
        
        # Use conversion logic if specified
        if conversion_logic:
            if 'safe_date_convert' in conversion_logic:
                return safe_date_convert(value)
            elif 'safe_numeric_convert' in conversion_logic:
                return safe_numeric_convert(value)
            else:
                return safe_string_convert(value)
        
        # Default conversions based on Monday.com type
        if monday_type == 'date':
            return safe_date_convert(value)
        elif monday_type in ('numbers', 'numeric'):
            return safe_numeric_convert(value)
        else:
            return safe_string_convert(value)
    
    def _insert_updates_to_staging(self, updates: List[Dict], update_type: str, batch_id: str, source_query: str, metadata: Dict) -> int:
        """Insert updates to appropriate staging table"""
        if update_type in ['update_items', 'update_groups', 'update_boards']:
            table_name = 'STG_MON_CustMasterSchedule'
        else:  # update_subitems
            table_name = 'STG_MON_CustMasterSchedule_Subitems'
        
        # Transform updates to staging table format
        staging_records = []
        for update in updates:
            record = {
                'update_operation': update['update_operation'],
                'update_fields': json.dumps(update['column_values']),
                'source_query': source_query,
                'update_batch_id': batch_id,
                'validation_status': 'PENDING',
                'board_id': metadata['board_id'],
                'monday_item_id': update.get('monday_item_id'),
                'created_at': datetime.now()
            }
            
            if 'monday_subitem_id' in update:
                record['monday_subitem_id'] = update['monday_subitem_id']
            if 'monday_group_id' in update:
                record['monday_group_id'] = update['monday_group_id']
            
            staging_records.append(record)
        
        # Bulk insert to staging table
        df_staging = pd.DataFrame(staging_records)
        self.staging_ops.bulk_insert(df_staging, table_name)
        
        return len(staging_records)