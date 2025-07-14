"""
OPUS Update Boards - UpdateOperations Module
Purpose: Comprehensive update operations handler using existing staging infrastructure
Date: 2025-06-30
Reference: OPUS_dev_update_boards.yaml - Task 0.3.1, IMM.2

This module extends the existing staging framework to support Monday.com update operations
with comprehensive validation, dry-run capabilities, and audit trail integration.
"""

import sys
from pathlib import Path
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd

# Standard import pattern for data orchestration project
def find_repo_root() -> Path:
    """Find repository root by looking for pipelines/utils folder"""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current.parent.parent / "pipelines" / "utils").exists():
            return current.parent.parent
        current = current.parent
    raise RuntimeError("Could not find repository root with pipelines/utils folder")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))  # Only use pipelines/utils for Kestra compatibility

# Import from utils/ - PRODUCTION PATTERN
import db_helper as db
import logger_helper

class UpdateOperations:
    """
    Comprehensive update operations handler for Monday.com boards
    
    Extends existing staging infrastructure to support bidirectional data flow
    with validation, dry-run capabilities, and comprehensive audit trail.
    
    Key Features:
    - Metadata-driven configuration using existing board metadata
    - Integration with proven staging infrastructure
    - Mandatory dry-run mode for safety
    - Comprehensive validation and error handling
    - Complete audit trail for rollback capability
    """
    
    def __init__(self, board_id: int, config_path: Optional[str] = None):
        """
        Initialize UpdateOperations for specific Monday.com board
        
        Args:
            board_id: Monday.com board ID (e.g., 8709134353 for Planning)
            config_path: Optional path to config.yaml file
        """
        self.board_id = board_id
        self.config = db.load_config(config_path) if config_path else db.load_config()
        self.logger = logger_helper.get_logger(__name__)
        
        # Load board metadata for update configuration
        self.board_metadata = self._load_board_metadata()
        self.update_config = self.board_metadata.get('update_config', {})
        
        # Initialize batch tracking
        self.current_batch_id = None
        
        self.logger.info(f"UpdateOperations initialized for board {board_id}")
    
    def _load_board_metadata(self) -> Dict[str, Any]:
        """Load board metadata with update configuration"""
        try:
            metadata_path = repo_root / f"configs/boards/board_{self.board_id}_metadata.json"
            
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                self.logger.info(f"Loaded metadata for board {self.board_id}")
                return metadata
            else:
                self.logger.warning(f"No metadata file found for board {self.board_id}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Failed to load board metadata: {e}")
            return {}
    
    def stage_updates_from_query(self, 
                                source_query: str, 
                                update_type: str = 'update_items',
                                source_table: Optional[str] = None,
                                batch_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Stage updates from SQL query using existing staging infrastructure
        
        Args:
            source_query: SQL query returning update data
            update_type: Type of update operation (update_items, update_subitems, etc.)
            source_table: Optional source table name for audit
            batch_id: Optional batch ID (generated if not provided)
            
        Returns:
            Dict containing staging results and batch information
        """
        try:
            # Generate batch ID if not provided
            if not batch_id:
                batch_id = f"OPUS_{update_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
            
            self.current_batch_id = batch_id
            
            self.logger.info(f"Staging {update_type} updates for batch {batch_id}")
            
            # Execute source query to get update data
            with db.get_connection('dms') as conn:
                update_data = pd.read_sql(source_query, conn)
            
            if update_data.empty:
                return {
                    'success': False,
                    'error': 'Source query returned no data',
                    'batch_id': batch_id,
                    'records_processed': 0
                }
            
            # Validate required columns based on update type
            validation_result = self._validate_update_data(update_data, update_type)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': f"Data validation failed: {validation_result['errors']}",
                    'batch_id': batch_id,
                    'records_processed': 0
                }
            
            # Prepare staging data with update operation metadata
            staging_data = self._prepare_staging_data(
                update_data, update_type, source_query, source_table, batch_id
            )
            
            # Use existing staging infrastructure to insert data
            staging_result = self._insert_to_staging(staging_data, update_type)
            
            # Log to audit trail
            self._log_staging_operation(batch_id, update_type, staging_result)
            
            return {
                'success': staging_result['success'],
                'batch_id': batch_id,
                'records_processed': len(update_data),
                'records_staged': staging_result.get('rows_inserted', 0),
                'validation_summary': validation_result,
                'staging_result': staging_result
            }
            
        except Exception as e:
            self.logger.error(f"Failed to stage updates: {e}")
            return {
                'success': False,
                'error': str(e),
                'batch_id': batch_id,
                'records_processed': 0
            }
    
    def _validate_update_data(self, data: pd.DataFrame, update_type: str) -> Dict[str, Any]:
        """
        Validate update data against Monday.com metadata and business rules
        
        Args:
            data: DataFrame containing update data
            update_type: Type of update operation
            
        Returns:
            Dict containing validation results
        """
        errors = []
        warnings = []
        
        # Get update configuration for this operation type
        operation_config = self.update_config.get(update_type, {})
        
        # Check required fields
        required_fields = operation_config.get('validation_rules', {}).get('required_fields', [])
        for field in required_fields:
            if field not in data.columns:
                errors.append(f"Required field missing: {field}")
            elif data[field].isnull().any():
                errors.append(f"Required field has null values: {field}")
        
        # Validate Monday.com item IDs exist and are valid
        if 'monday_item_id' in data.columns:
            invalid_ids = data[data['monday_item_id'].isnull() | (data['monday_item_id'] <= 0)]
            if not invalid_ids.empty:
                errors.append(f"Invalid Monday.com item IDs found: {len(invalid_ids)} records")
        
        # Check batch size limits
        max_batch_size = operation_config.get('validation_rules', {}).get('max_batch_size', 100)
        if len(data) > max_batch_size:
            errors.append(f"Batch size ({len(data)}) exceeds maximum ({max_batch_size})")
        
        # Validate allowed columns
        allowed_columns = operation_config.get('validation_rules', {}).get('allowed_columns', [])
        if allowed_columns:
            disallowed_columns = [col for col in data.columns if col not in allowed_columns + required_fields]
            if disallowed_columns:
                warnings.append(f"Unexpected columns found: {disallowed_columns}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'records_validated': len(data)
        }
    
    def _prepare_staging_data(self, 
                            data: pd.DataFrame, 
                            update_type: str,
                            source_query: str,
                            source_table: Optional[str],
                            batch_id: str) -> pd.DataFrame:
        """
        Prepare data for staging with update operation metadata
        
        Args:
            data: Source update data
            update_type: Type of update operation
            source_query: Source SQL query
            source_table: Source table name
            batch_id: Batch identifier
            
        Returns:
            DataFrame prepared for staging insertion
        """
        # Add update operation metadata columns
        staging_data = data.copy()
        
        staging_data['update_operation'] = update_type
        staging_data['update_batch_id'] = batch_id
        staging_data['validation_status'] = 'PENDING'
        staging_data['source_query'] = source_query
        staging_data['source_table'] = source_table or 'DIRECT_QUERY'
        
        # Add metadata fields for update tracking
        staging_data['created_date'] = datetime.utcnow()
        staging_data['monday_board_id'] = self.board_id
        
        # Identify fields being updated for audit trail
        update_fields = [col for col in data.columns 
                        if col not in ['monday_item_id', 'monday_board_id']]
        staging_data['update_fields'] = json.dumps(update_fields)
        
        return staging_data
    
    def _insert_to_staging(self, data: pd.DataFrame, update_type: str) -> Dict[str, Any]:
        """
        Insert prepared data to appropriate staging table
        
        Args:
            data: Prepared staging data
            update_type: Type of update operation
            
        Returns:
            Dict containing insertion results
        """
        try:
            # Determine target staging table based on update type
            if update_type in ['update_items', 'update_groups', 'update_boards']:
                staging_table = 'STG_MON_CustMasterSchedule'
            elif update_type == 'update_subitems':
                staging_table = 'STG_MON_CustMasterSchedule_Subitems'
            else:
                raise ValueError(f"Unknown update type: {update_type}")
            
            # Use existing staging operations infrastructure
            with db.get_connection('dms') as conn:
                # Use pandas to_sql for efficient bulk insert
                rows_inserted = data.to_sql(
                    staging_table, 
                    conn, 
                    if_exists='append', 
                    index=False, 
                    method='multi'
                )
                
                self.logger.info(f"Inserted {rows_inserted} rows to {staging_table}")
                
                return {
                    'success': True,
                    'staging_table': staging_table,
                    'rows_inserted': len(data),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Failed to insert to staging: {e}")
            return {
                'success': False,
                'error': str(e),
                'staging_table': staging_table,
                'rows_inserted': 0
            }
    
    def validate_staged_updates(self, batch_id: str) -> Dict[str, Any]:
        """
        Validate staged updates against Monday.com metadata
        
        Args:
            batch_id: Batch identifier to validate
            
        Returns:
            Dict containing validation results
        """
        try:
            self.logger.info(f"Validating staged updates for batch {batch_id}")
            
            # Query staged data for this batch
            with db.get_connection('dms') as conn:
                staged_data = pd.read_sql("""
                    SELECT *
                    FROM STG_MON_CustMasterSchedule
                    WHERE update_batch_id = %s
                    AND validation_status = 'PENDING'
                """, conn, params=[batch_id])
            
            if staged_data.empty:
                return {
                    'success': False,
                    'error': f'No pending validation records found for batch {batch_id}',
                    'batch_id': batch_id,
                    'records_validated': 0
                }
            
            validation_results = []
            valid_count = 0
            error_count = 0
            
            for _, row in staged_data.iterrows():
                try:
                    # Validate individual record
                    record_validation = self._validate_individual_record(row)
                    
                    if record_validation['valid']:
                        valid_count += 1
                        validation_status = 'VALID'
                        validation_errors = None
                    else:
                        error_count += 1
                        validation_status = 'INVALID'
                        validation_errors = json.dumps(record_validation['errors'])
                    
                    # Update validation status in staging table
                    self._update_validation_status(
                        row.get('staging_id'), validation_status, validation_errors
                    )
                    
                    validation_results.append({
                        'staging_id': row.get('staging_id'),
                        'monday_item_id': row.get('monday_item_id'),
                        'validation_status': validation_status,
                        'errors': record_validation.get('errors', [])
                    })
                    
                except Exception as e:
                    self.logger.error(f"Validation error for record {row.get('staging_id')}: {e}")
                    error_count += 1
            
            success_rate = (valid_count / len(staged_data)) * 100 if len(staged_data) > 0 else 0
            
            return {
                'success': True,
                'batch_id': batch_id,
                'records_validated': len(staged_data),
                'valid_records': valid_count,
                'invalid_records': error_count,
                'success_rate': success_rate,
                'validation_results': validation_results
            }
            
        except Exception as e:
            self.logger.error(f"Failed to validate staged updates: {e}")
            return {
                'success': False,
                'error': str(e),
                'batch_id': batch_id,
                'records_validated': 0
            }
    
    def _validate_individual_record(self, record: pd.Series) -> Dict[str, Any]:
        """
        Validate individual staged record
        
        Args:
            record: Staged record to validate
            
        Returns:
            Dict containing record validation results
        """
        errors = []
        
        # Validate Monday.com item ID exists
        monday_item_id = record.get('monday_item_id')
        if not monday_item_id or monday_item_id <= 0:
            errors.append("Invalid or missing Monday.com item ID")
        
        # Validate board ID matches
        if record.get('monday_board_id') != self.board_id:
            errors.append(f"Board ID mismatch: expected {self.board_id}, got {record.get('monday_board_id')}")
        
        # Validate update fields are present
        update_fields_json = record.get('update_fields')
        if update_fields_json:
            try:
                update_fields = json.loads(update_fields_json)
                if not update_fields:
                    errors.append("No update fields specified")
            except (json.JSONDecodeError, TypeError):
                errors.append("Invalid update fields format")
        
        # Additional business rule validation could be added here
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _update_validation_status(self, 
                                staging_id: int, 
                                status: str, 
                                errors: Optional[str]) -> None:
        """
        Update validation status in staging table
        
        Args:
            staging_id: Staging record ID
            status: Validation status (VALID/INVALID)
            errors: JSON string of validation errors
        """
        try:
            with db.get_connection('dms') as conn:
                conn.execute("""
                    UPDATE STG_MON_CustMasterSchedule
                    SET validation_status = %s,
                        validation_errors = %s,
                        validation_timestamp = GETUTCDATE()
                    WHERE staging_id = %s
                """, [status, errors, staging_id])
                
        except Exception as e:
            self.logger.error(f"Failed to update validation status: {e}")
    
    def process_staged_updates(self, 
                             batch_id: str, 
                             dry_run: bool = True) -> Dict[str, Any]:
        """
        Process staged updates with dry-run capability
        
        Args:
            batch_id: Batch identifier to process
            dry_run: If True, only simulate processing (default: True for safety)
            
        Returns:
            Dict containing processing results
        """
        try:
            self.logger.info(f"Processing staged updates for batch {batch_id} (dry_run={dry_run})")
            
            if dry_run:
                self.logger.info("DRY RUN MODE: No actual Monday.com updates will be performed")
            
            # Get valid staged records for processing
            with db.get_connection('dms') as conn:
                valid_updates = pd.read_sql("""
                    SELECT *
                    FROM STG_MON_CustMasterSchedule
                    WHERE update_batch_id = %s
                    AND validation_status = 'VALID'
                """, conn, params=[batch_id])
            
            if valid_updates.empty:
                return {
                    'success': False,
                    'error': f'No valid records found for batch {batch_id}',
                    'batch_id': batch_id,
                    'dry_run': dry_run,
                    'records_processed': 0
                }
            
            processing_results = []
            success_count = 0
            error_count = 0
            
            for _, record in valid_updates.iterrows():
                try:
                    if dry_run:
                        # Simulate processing - generate report only
                        result = self._simulate_update_processing(record)
                    else:
                        # Actual Monday.com API update (to be implemented)
                        result = self._execute_monday_update(record)
                    
                    if result['success']:
                        success_count += 1
                    else:
                        error_count += 1
                    
                    processing_results.append(result)
                    
                except Exception as e:
                    self.logger.error(f"Processing error for record {record.get('staging_id')}: {e}")
                    error_count += 1
                    processing_results.append({
                        'success': False,
                        'staging_id': record.get('staging_id'),
                        'error': str(e)
                    })
            
            success_rate = (success_count / len(valid_updates)) * 100 if len(valid_updates) > 0 else 0
            
            return {
                'success': True,
                'batch_id': batch_id,
                'dry_run': dry_run,
                'records_processed': len(valid_updates),
                'successful_updates': success_count,
                'failed_updates': error_count,
                'success_rate': success_rate,
                'processing_results': processing_results,
                'summary': self._generate_processing_summary(processing_results, dry_run)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process staged updates: {e}")
            return {
                'success': False,
                'error': str(e),
                'batch_id': batch_id,
                'dry_run': dry_run,
                'records_processed': 0
            }
    
    def _simulate_update_processing(self, record: pd.Series) -> Dict[str, Any]:
        """
        Simulate update processing for dry-run mode
        
        Args:
            record: Staged record to simulate
            
        Returns:
            Dict containing simulation results
        """
        # Generate detailed simulation report
        monday_item_id = record.get('monday_item_id')
        update_fields = json.loads(record.get('update_fields', '[]'))
        
        simulation_report = {
            'monday_item_id': monday_item_id,
            'board_id': self.board_id,
            'update_operation': record.get('update_operation'),
            'fields_to_update': update_fields,
            'simulated_changes': []
        }
        
        # Simulate field updates
        for field in update_fields:
            if field in record and pd.notna(record[field]):
                simulation_report['simulated_changes'].append({
                    'field': field,
                    'new_value': record[field],
                    'action': 'UPDATE'
                })
        
        return {
            'success': True,
            'staging_id': record.get('staging_id'),
            'simulation': simulation_report,
            'dry_run': True
        }
    
    def _execute_monday_update(self, record: pd.Series) -> Dict[str, Any]:
        """
        Execute actual Monday.com update (placeholder for Phase 1 implementation)
        
        Args:
            record: Staged record to update
            
        Returns:
            Dict containing update results
        """
        # This will be implemented in Phase 1 with Monday.com API integration
        # For now, return placeholder result
        
        return {
            'success': False,
            'staging_id': record.get('staging_id'),
            'error': 'Monday.com API integration not yet implemented (Phase 1)',
            'dry_run': False
        }
    
    def _generate_processing_summary(self, results: List[Dict], dry_run: bool) -> str:
        """
        Generate human-readable processing summary
        
        Args:
            results: List of processing results
            dry_run: Whether this was a dry run
            
        Returns:
            Formatted summary string
        """
        mode = "DRY RUN" if dry_run else "LIVE UPDATE"
        total = len(results)
        successful = len([r for r in results if r.get('success', False)])
        failed = total - successful
        
        summary = f"""
{mode} PROCESSING SUMMARY
{'=' * 50}
Total Records: {total}
Successful: {successful}
Failed: {failed}
Success Rate: {(successful/total*100):.1f}% if total > 0 else 0%

"""
        
        if dry_run:
            summary += """
DRY RUN NOTES:
- No actual Monday.com updates performed
- All changes were simulated only
- Use --execute flag to perform actual updates
- Review simulation results before executing
"""
        
        return summary
    
    def _log_staging_operation(self, 
                             batch_id: str, 
                             update_type: str, 
                             result: Dict[str, Any]) -> None:
        """
        Log staging operation to audit trail
        
        Args:
            batch_id: Batch identifier
            update_type: Type of update operation
            result: Staging operation result
        """
        try:
            with db.get_connection('dms') as conn:
                conn.execute("""
                    INSERT INTO MON_UpdateAudit (
                        batch_id, update_operation, old_value, new_value,
                        user_id, source_system
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """, [
                    batch_id,
                    f'staging_{update_type}',
                    'empty_staging',
                    f"staged_{result.get('rows_inserted', 0)}_records",
                    'SYSTEM_STAGING',
                    'OPUS_UPDATE_BOARDS'
                ])
                
        except Exception as e:
            self.logger.error(f"Failed to log staging operation: {e}")

# Factory function for easy usage
def create_update_operations(board_id: int) -> UpdateOperations:
    """
    Factory function to create UpdateOperations instance
    
    Args:
        board_id: Monday.com board ID
        
    Returns:
        Configured UpdateOperations instance
    """
    return UpdateOperations(board_id)
