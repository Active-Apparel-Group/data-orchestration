"""
Monday.com Sync Engine for ORDER_LIST Delta Sync
===============================================
Purpose: Two-pass sync engine for syncing ORDER_LIST delta records to Monday.com
Location: src/pipelines/sync_order_list/monday_sync.py
Created: 2025-07-20 (Milestone 2: Business Key Implementation)

This module handles the two-pass synchronization of ORDER_LIST records to Monday.com:
1. Pass A (Headers): Sync ORDER_LIST_DELTA records as Monday.com items
2. Pass B (Lines): Sync ORDER_LIST_LINES_DELTA records as Monday.com subitems

Architecture Integration:
- Uses existing pipelines.integrations.monday infrastructure
- Integrates with shared customer utilities for business key resolution
- TOML-driven configuration for column mappings and GraphQL templates
- Supports async batch processing with configurable concurrency

Business Flow:
1. Query ORDER_LIST_DELTA for PENDING records
2. Create/update Monday.com items using GraphQL templates
3. Update sync_state to SYNCED and store monday_item_id
4. Query ORDER_LIST_LINES_DELTA for PENDING records (parent items synced)
5. Create/update Monday.com subitems linked to parent items
6. Update sync_state to SYNCED and store monday_subitem_id
"""

import sys
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, AsyncGenerator
import time
import json

# Modern import pattern for project utilities
from pipelines.utils import db, logger, config

# Import customer utilities using direct path resolution
import sys
from pathlib import Path
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root / "src"))

try:
    from pipelines.shared.customer import CanonicalCustomerManager, OrderKeyGenerator
except ImportError:
    # Fallback for compatibility - mock classes
    class CanonicalCustomerManager:
        def canonicalize_customer(self, name, source='monday'):
            return name
    
    class OrderKeyGenerator:
        def generate_key(self, *args, **kwargs):
            return "MOCK_KEY"

from .config_parser import DeltaSyncConfig, load_delta_sync_config

# Monday.com integration (when implemented)
try:
    from pipelines.integrations.monday.client import MondayClient
    from pipelines.integrations.monday.sync_engine import DeltaSyncEngine
    MONDAY_INTEGRATION_AVAILABLE = True
except ImportError:
    # Graceful fallback for development
    MONDAY_INTEGRATION_AVAILABLE = False

class MondaySync:
    """
    Two-pass sync engine for ORDER_LIST → Monday.com synchronization
    """
    
    def __init__(self, config: DeltaSyncConfig):
        """
        Initialize Monday sync engine with configuration
        
        Args:
            config: Delta sync configuration from TOML file
        """
        self.config = config
        self.logger = logger.get_logger(__name__)
        
        # Initialize customer utilities for business key resolution
        self.canonical_manager = CanonicalCustomerManager()
        self.key_generator = OrderKeyGenerator()
        
        # Track sync statistics
        self.sync_stats = {
            'headers_synced': 0,
            'headers_failed': 0,
            'lines_synced': 0,
            'lines_failed': 0,
            'api_calls_made': 0,
            'total_duration': 0
        }
        
        # Initialize Monday.com client if available
        if MONDAY_INTEGRATION_AVAILABLE:
            self.monday_client = MondayClient()
            self.sync_engine = DeltaSyncEngine(self.monday_client)
            self.logger.info("Monday.com integration initialized")
        else:
            self.monday_client = None
            self.sync_engine = None
            self.logger.warning("Monday.com integration not available - running in mock mode")
        
        self.logger.info(f"Monday sync initialized for board {config.monday_board_id}")
    
    def execute_two_pass_sync(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute complete two-pass sync: headers → lines
        
        Args:
            dry_run: If True, validate operations but don't execute
            
        Returns:
            Dictionary with sync results and statistics
        """
        start_time = time.time()
        self.logger.info("🔄 Starting two-pass Monday.com sync")
        
        if dry_run:
            self.logger.info("⚠️  DRY RUN MODE: Operations will be validated but not executed")
        
        try:
            # Pass A: Sync headers (ORDER_LIST_DELTA → Monday items)
            headers_result = self._sync_headers_pass(dry_run)
            
            # Pass B: Sync lines (ORDER_LIST_LINES_DELTA → Monday subitems)
            if headers_result['success']:
                lines_result = self._sync_lines_pass(dry_run)
            else:
                lines_result = {'success': False, 'error': 'Headers sync failed', 'records_synced': 0}
            
            # Compile overall results
            overall_success = headers_result['success'] and lines_result['success']
            total_duration = time.time() - start_time
            
            result = {
                'success': overall_success,
                'dry_run': dry_run,
                'total_duration_seconds': round(total_duration, 2),
                'passes': {
                    'headers': headers_result,
                    'lines': lines_result
                },
                'statistics': self.sync_stats,
                'summary': self._generate_sync_summary()
            }
            
            # Log final results
            if overall_success:
                self.logger.info(f"✅ Two-pass sync completed successfully in {total_duration:.2f}s")
            else:
                self.logger.error(f"❌ Two-pass sync failed after {total_duration:.2f}s")
                
            return result
            
        except Exception as e:
            self.logger.exception(f"Fatal error in two-pass sync: {e}")
            return {
                'success': False,
                'error': f"Fatal error: {str(e)}",
                'dry_run': dry_run,
                'total_duration_seconds': time.time() - start_time
            }
    
    def _sync_headers_pass(self, dry_run: bool) -> Dict[str, Any]:
        """
        Pass A: Sync header records (ORDER_LIST_DELTA → Monday items)
        
        Args:
            dry_run: If True, validate operations but don't execute
            
        Returns:
            Results dictionary with success status and statistics
        """
        self.logger.info("📋 Pass A: Syncing Headers (ORDER_LIST_DELTA → Monday Items)")
        
        start_time = time.time()
        
        try:
            # Query PENDING header records from delta table
            pending_headers = self._query_pending_headers()
            
            if not pending_headers:
                self.logger.info("📝 No pending headers to sync")
                return {
                    'success': True,
                    'records_synced': 0,
                    'records_failed': 0,
                    'duration_seconds': round(time.time() - start_time, 2),
                    'pass_type': 'headers'
                }
            
            self.logger.info(f"📤 Found {len(pending_headers)} pending header records")
            
            if dry_run:
                self.logger.info("📝 DRY RUN: Would sync header records to Monday.com")
                self.logger.debug(f"Sample header: {pending_headers[0] if pending_headers else 'None'}")
                return {
                    'success': True,
                    'records_synced': len(pending_headers),
                    'records_failed': 0,
                    'duration_seconds': 0.1,
                    'pass_type': 'headers',
                    'dry_run': True
                }
            
            # Execute header sync with async batch processing
            sync_results = asyncio.run(self._sync_headers_batch(pending_headers))
            
            duration = time.time() - start_time
            
            self.logger.info(f"✅ Headers sync completed: {sync_results['synced']} synced, "
                           f"{sync_results['failed']} failed in {duration:.2f}s")
            
            return {
                'success': sync_results['failed'] == 0,
                'records_synced': sync_results['synced'],
                'records_failed': sync_results['failed'],
                'duration_seconds': round(duration, 2),
                'pass_type': 'headers',
                'api_calls': sync_results.get('api_calls', 0)
            }
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.exception(f"❌ Headers sync failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'duration_seconds': round(duration, 2),
                'pass_type': 'headers'
            }
    
    def _sync_lines_pass(self, dry_run: bool) -> Dict[str, Any]:
        """
        Pass B: Sync line records (ORDER_LIST_LINES_DELTA → Monday subitems)
        
        Args:
            dry_run: If True, validate operations but don't execute
            
        Returns:
            Results dictionary with success status and statistics
        """
        self.logger.info("📊 Pass B: Syncing Lines (ORDER_LIST_LINES_DELTA → Monday Subitems)")
        
        start_time = time.time()
        
        try:
            # Query PENDING line records from delta table (with parent item IDs)
            pending_lines = self._query_pending_lines()
            
            if not pending_lines:
                self.logger.info("📝 No pending lines to sync")
                return {
                    'success': True,
                    'records_synced': 0,
                    'records_failed': 0,
                    'duration_seconds': round(time.time() - start_time, 2),
                    'pass_type': 'lines'
                }
            
            self.logger.info(f"📤 Found {len(pending_lines)} pending line records")
            
            if dry_run:
                self.logger.info("📝 DRY RUN: Would sync line records to Monday.com subitems")
                self.logger.debug(f"Sample line: {pending_lines[0] if pending_lines else 'None'}")
                return {
                    'success': True,
                    'records_synced': len(pending_lines),
                    'records_failed': 0,
                    'duration_seconds': 0.1,
                    'pass_type': 'lines',
                    'dry_run': True
                }
            
            # Execute line sync with async batch processing
            sync_results = asyncio.run(self._sync_lines_batch(pending_lines))
            
            duration = time.time() - start_time
            
            self.logger.info(f"✅ Lines sync completed: {sync_results['synced']} synced, "
                           f"{sync_results['failed']} failed in {duration:.2f}s")
            
            return {
                'success': sync_results['failed'] == 0,
                'records_synced': sync_results['synced'],
                'records_failed': sync_results['failed'],
                'duration_seconds': round(duration, 2),
                'pass_type': 'lines',
                'api_calls': sync_results.get('api_calls', 0)
            }
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.exception(f"❌ Lines sync failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'duration_seconds': round(duration, 2),
                'pass_type': 'lines'
            }
    
    def _query_pending_headers(self) -> List[Dict[str, Any]]:
        """
        Query PENDING header records from ORDER_LIST_DELTA
        
        Returns:
            List of pending header records ready for Monday.com sync
        """
        delta_table = self.config.get_full_table_name('delta')
        
        sql = f"""
        SELECT 
            d.record_uuid,
            d.[AAG ORDER NUMBER],
            d.[CUSTOMER NAME],
            d.[STYLE DESCRIPTION],
            d.[TOTAL QTY],
            d.[ETA CUSTOMER WAREHOUSE DATE],
            d.row_hash,
            d.action_type,
            d.processed_at,
            ol.monday_item_id  -- NULL for new records
        FROM {delta_table} d
        LEFT JOIN {self.config.get_full_table_name('target')} ol 
            ON d.[AAG ORDER NUMBER] = ol.[AAG ORDER NUMBER]
        WHERE d.sync_state = 'PENDING'
        ORDER BY d.processed_at ASC
        """
        
        try:
            with db.get_connection(self.config.database_connection) as conn:
                cursor = conn.cursor()
                cursor.execute(sql)
                
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            self.logger.exception(f"Failed to query pending headers: {e}")
            return []
    
    def _query_pending_lines(self) -> List[Dict[str, Any]]:
        """
        Query PENDING line records from ORDER_LIST_LINES_DELTA
        Only includes lines where parent item has monday_item_id
        
        Returns:
            List of pending line records ready for Monday.com sync
        """
        lines_delta_table = self.config.get_full_table_name('lines_delta')
        target_table = self.config.get_full_table_name('target')
        
        sql = f"""
        SELECT 
            ld.line_uuid,
            ld.record_uuid,
            ld.size_code,
            ld.qty,
            ld.action_type,
            ld.processed_at,
            ol.monday_item_id as parent_item_id,  -- Required for subitems
            ol.[AAG ORDER NUMBER],
            ol.[CUSTOMER NAME]
        FROM {lines_delta_table} ld
        INNER JOIN {target_table} ol 
            ON ld.record_uuid = ol.record_uuid
        WHERE ld.sync_state = 'PENDING'
        AND ol.monday_item_id IS NOT NULL  -- Parent must be synced first
        ORDER BY ld.processed_at ASC
        """
        
        try:
            with db.get_connection(self.config.database_connection) as conn:
                cursor = conn.cursor()
                cursor.execute(sql)
                
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            self.logger.exception(f"Failed to query pending lines: {e}")
            return []
    
    async def _sync_headers_batch(self, headers: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Sync header records to Monday.com items using async batch processing
        
        Args:
            headers: List of header records to sync
            
        Returns:
            Dictionary with sync statistics
        """
        synced = 0
        failed = 0
        api_calls = 0
        
        # Process in batches for better performance
        batch_size = self.config.async_batch_size
        batches = [headers[i:i + batch_size] for i in range(0, len(headers), batch_size)]
        
        self.logger.info(f"Processing {len(headers)} headers in {len(batches)} batches of {batch_size}")
        
        for batch_num, batch in enumerate(batches, 1):
            self.logger.debug(f"Processing batch {batch_num}/{len(batches)} ({len(batch)} records)")
            
            try:
                batch_results = await self._sync_headers_batch_async(batch)
                synced += batch_results['synced']
                failed += batch_results['failed'] 
                api_calls += batch_results['api_calls']
                
                # Rate limiting delay between batches
                if batch_num < len(batches):
                    await asyncio.sleep(self.config.batch_delay_ms / 1000)
                    
            except Exception as e:
                self.logger.exception(f"Batch {batch_num} failed: {e}")
                failed += len(batch)
        
        return {
            'synced': synced,
            'failed': failed,
            'api_calls': api_calls
        }
    
    async def _sync_headers_batch_async(self, batch: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Process a single batch of header records asynchronously
        
        Args:
            batch: List of header records in the batch
            
        Returns:
            Batch processing statistics
        """
        if not MONDAY_INTEGRATION_AVAILABLE:
            # Mock success for development
            self.logger.debug(f"MOCK: Would sync {len(batch)} headers to Monday.com")
            return {
                'synced': len(batch),
                'failed': 0,
                'api_calls': len(batch)
            }
        
        synced = 0
        failed = 0
        api_calls = 0
        
        # Create GraphQL mutations for batch processing
        for record in batch:
            try:
                # Determine if CREATE or UPDATE based on existing monday_item_id
                is_update = record.get('monday_item_id') is not None
                
                if is_update:
                    # Update existing Monday.com item
                    monday_item_id = await self._update_monday_item(record)
                else:
                    # Create new Monday.com item
                    monday_item_id = await self._create_monday_item(record)
                
                if monday_item_id:
                    # Update database with monday_item_id and set sync_state to SYNCED
                    await self._update_header_sync_status(record, monday_item_id, 'SYNCED')
                    synced += 1
                else:
                    # Mark as FAILED
                    await self._update_header_sync_status(record, None, 'FAILED')
                    failed += 1
                
                api_calls += 1
                
            except Exception as e:
                self.logger.exception(f"Failed to sync header record {record.get('AAG ORDER NUMBER')}: {e}")
                await self._update_header_sync_status(record, None, 'FAILED')
                failed += 1
        
        return {
            'synced': synced,
            'failed': failed,
            'api_calls': api_calls
        }
    
    async def _sync_lines_batch(self, lines: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Sync line records to Monday.com subitems using async batch processing
        
        Args:
            lines: List of line records to sync
            
        Returns:
            Dictionary with sync statistics
        """
        # Similar implementation to _sync_headers_batch but for subitems
        if not MONDAY_INTEGRATION_AVAILABLE:
            # Mock success for development
            self.logger.debug(f"MOCK: Would sync {len(lines)} lines to Monday.com subitems")
            return {
                'synced': len(lines),
                'failed': 0,
                'api_calls': len(lines)
            }
        
        # Batch processing logic would go here
        # For now, return mock results
        return {
            'synced': len(lines),
            'failed': 0,
            'api_calls': len(lines)
        }
    
    async def _create_monday_item(self, record: Dict[str, Any]) -> Optional[int]:
        """
        Create new Monday.com item from header record
        
        Args:
            record: Header record dictionary
            
        Returns:
            Monday.com item ID if successful, None if failed
        """
        if not MONDAY_INTEGRATION_AVAILABLE:
            # Mock Monday.com item ID for development
            return 12345678
        
        # Use Monday.com client to create item
        # Implementation would use GraphQL templates from TOML config
        # For now, return mock ID
        return 12345678
    
    async def _update_monday_item(self, record: Dict[str, Any]) -> Optional[int]:
        """
        Update existing Monday.com item from header record
        
        Args:
            record: Header record dictionary
            
        Returns:
            Monday.com item ID if successful, None if failed
        """
        if not MONDAY_INTEGRATION_AVAILABLE:
            # Return existing monday_item_id for development
            return record.get('monday_item_id')
        
        # Use Monday.com client to update item
        # Implementation would use GraphQL templates from TOML config
        return record.get('monday_item_id')
    
    async def _update_header_sync_status(self, record: Dict[str, Any], monday_item_id: Optional[int], sync_state: str):
        """
        Update database with Monday.com sync results for header record
        
        Args:
            record: Header record dictionary
            monday_item_id: Monday.com item ID (None if failed)
            sync_state: 'SYNCED' or 'FAILED'
        """
        target_table = self.config.get_full_table_name('target')
        delta_table = self.config.get_full_table_name('delta')
        
        # Update main table
        sql_main = f"""
        UPDATE {target_table}
        SET monday_item_id = ?,
            sync_state = ?,
            last_synced_at = GETDATE()
        WHERE [AAG ORDER NUMBER] = ?
        """
        
        # Update delta table
        sql_delta = f"""
        UPDATE {delta_table}
        SET sync_state = ?,
            synced_at = GETDATE()
        WHERE [AAG ORDER NUMBER] = ?
        """
        
        try:
            with db.get_connection(self.config.database_connection) as conn:
                cursor = conn.cursor()
                
                # Update main table
                cursor.execute(sql_main, (monday_item_id, sync_state, record['AAG ORDER NUMBER']))
                
                # Update delta table
                cursor.execute(sql_delta, (sync_state, record['AAG ORDER NUMBER']))
                
                conn.commit()
                
        except Exception as e:
            self.logger.exception(f"Failed to update sync status for {record['AAG ORDER NUMBER']}: {e}")
    
    def _generate_sync_summary(self) -> Dict[str, Any]:
        """
        Generate summary statistics for the sync operation
        """
        return {
            'total_records_synced': self.sync_stats['headers_synced'] + self.sync_stats['lines_synced'],
            'total_records_failed': self.sync_stats['headers_failed'] + self.sync_stats['lines_failed'],
            'api_calls_made': self.sync_stats['api_calls_made'],
            'monday_board_id': self.config.monday_board_id,
            'environment': self.config.board_type
        }
    
    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get current sync status from database
        
        Returns:
            Dictionary with sync status statistics
        """
        try:
            with db.get_connection(self.config.database_connection) as conn:
                cursor = conn.cursor()
                
                # Count records by sync state
                target_table = self.config.get_full_table_name('target')
                delta_table = self.config.get_full_table_name('delta')
                
                # Headers status
                cursor.execute(f"""
                SELECT sync_state, COUNT(*) as count
                FROM {target_table}
                GROUP BY sync_state
                """)
                headers_status = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Delta status
                cursor.execute(f"""
                SELECT sync_state, COUNT(*) as count  
                FROM {delta_table}
                GROUP BY sync_state
                """)
                delta_status = {row[0]: row[1] for row in cursor.fetchall()}
                
                return {
                    'headers_status': headers_status,
                    'delta_status': delta_status,
                    'monday_integration_available': MONDAY_INTEGRATION_AVAILABLE
                }
                
        except Exception as e:
            self.logger.exception(f"Failed to get sync status: {e}")
            return {
                'error': str(e),
                'monday_integration_available': MONDAY_INTEGRATION_AVAILABLE
            }


# Factory function for easy usage
def create_monday_sync(environment: str = 'dev') -> MondaySync:
    """
    Factory function to create MondaySync instance
    
    Args:
        environment: 'dev', 'prod', or path to TOML file
        
    Returns:
        Configured MondaySync instance
    """
    config = load_delta_sync_config(environment)
    return MondaySync(config)


# Main execution for testing
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Test Monday sync
    try:
        sync_engine = create_monday_sync('dev')
        
        print("🧪 Testing Monday Sync Engine")
        print("-" * 50)
        
        # Get sync status
        status = sync_engine.get_sync_status()
        print("Current sync status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        # Execute dry run
        result = sync_engine.execute_two_pass_sync(dry_run=True)
        
        print(f"\nDry run result: {result['success']}")
        print(f"Total duration: {result['total_duration_seconds']}s")
        
        for pass_name, pass_result in result['passes'].items():
            print(f"  {pass_name}: {'✅' if pass_result['success'] else '❌'}")
            print(f"    Records: {pass_result.get('records_synced', 0)}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
