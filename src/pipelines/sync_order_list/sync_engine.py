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
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

# Modern Python package imports - ultra-minimal dependencies
from src.pipelines.utils import logger, db, config
from .monday_api_client import MondayAPIClient
from .api_logging_archiver import APILoggingArchiver


class SyncEngine:
    """
    Ultra-lightweight sync engine for ORDER_LIST → Monday.com pipeline
    Handles complete workflow: DELTA query → API calls → status updates
    """
    
    def __init__(self, toml_config_path: Optional[str] = None, environment: str = "development"):
        """
        Initialize sync engine with TOML configuration
        
        Args:
            toml_config_path: Optional path to sync_order_list.toml configuration (defaults to standard location)
            environment: Environment to use ('development' or 'production')
        """
        # Use default config path if none provided
        if toml_config_path is None:
            # Get absolute path to config file from repository root
            repo_root = Path(__file__).parent.parent.parent.parent
            toml_config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
        
        self.logger = logger.get_logger(__name__)
        self.config_path = Path(toml_config_path)
        
        # Load configuration using proper config parser
        from .config_parser import DeltaSyncConfig
        self.config = DeltaSyncConfig.from_toml(toml_config_path, environment=environment)
        
        # Load TOML configuration for legacy compatibility  
        self.toml_config = self._load_toml_config()
        
        # Initialize Monday.com API client with environment
        self.monday_client = MondayAPIClient(toml_config_path, environment=environment)
        
        # Environment determination (development vs production)
        self.environment = self.config.environment
        
        # Database configuration using proper config parser - DELTA-FREE ARCHITECTURE
        # Phase 3: Direct main table queries (eliminates DELTA dependency)
        self.headers_table = self.config.target_table              # FACT_ORDER_LIST (main)
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
        # Use rate_limits configuration for batch sizes
        self.batch_size = self.toml_config.get('monday', {}).get('rate_limits', {}).get('item_batch_size', 5)
        self.delta_hours = sync_config.get('delta_hours', 24)
        
        self.logger.info(f"Sync engine initialized for {self.headers_table} → Monday.com ({self.environment})")
        self.logger.info(f"DELTA-FREE Architecture: Headers: {self.headers_table}, Lines: {self.lines_table}")
        self.logger.info(f"Batch Processing: {self.batch_size} records per API call (from rate_limits configuration)")
        self.logger.info("Phase 3: Direct main table queries (DELTA tables eliminated)")
        
        # Retry configuration
        self.max_retries = 3
        self.base_retry_delay = 2.0  # seconds
        self.max_retry_delay = 60.0  # seconds
        self.retry_backoff_multiplier = 2.0
    
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
    
    # TASK027 Phase 1: Sync-Based Output Organization
    def _generate_sync_id(self) -> str:
        """
        Generate unique sync identifier for output organization (TASK027 Phase 1.2)
        Enhanced: Better chronological sorting with YYYYMMDDHHMM prefix
        
        Returns:
            Sync ID in format: {YYYYMMDDHHMM}-SYNC-{UUID8}
        """
        import uuid
        sync_uuid = str(uuid.uuid4())[:8].upper()
        sync_timestamp = datetime.now().strftime("%Y%m%d%H%M")
        sync_id = f"{sync_timestamp}-SYNC-{sync_uuid}"
        
        self.logger.info(f"🆔 Generated Sync ID: {sync_id}")
        return sync_id
    
    def _create_sync_folder_structure(self, sync_id: str) -> Path:
        """
        Create sync-based folder structure for organized output (TASK027 Phase 1.1)
        
        Args:
            sync_id: Unique sync identifier
            
        Returns:
            Path to created sync folder
        """
        from pathlib import Path
        
        # Create base sync reports directory
        sync_base_dir = Path("reports/sync")
        sync_session_dir = sync_base_dir / sync_id
        
        # Create directory structure
        sync_session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for organized output
        (sync_session_dir / "customer_reports").mkdir(exist_ok=True)
        (sync_session_dir / "logs").mkdir(exist_ok=True)
        (sync_session_dir / "summaries").mkdir(exist_ok=True)
        
        self.logger.info(f"📁 Created sync folder structure: {sync_session_dir}")
        self.logger.info(f"   Subdirectories: customer_reports/, logs/, summaries/")
        
        return sync_session_dir
    
    def _persist_executive_summary(self, sync_folder: Path, sync_results: Dict[str, Any]) -> None:
        """
        Persist executive summary to _SYNC_SUMMARY.md (TASK027 Phase 1.4)
        
        Args:
            sync_folder: Path to sync session folder
            sync_results: Complete sync operation results
        """
        try:
            summary_file = sync_folder / "_SYNC_SUMMARY.md"
            
            # Generate comprehensive executive summary
            summary_content = self._generate_executive_summary_content(sync_results)
            
            # Write summary to file
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(summary_content)
            
            self.logger.info(f"📄 Executive summary persisted: {summary_file}")
            
        except Exception as e:
            self.logger.warning(f"Failed to persist executive summary: {e}")
    
    def _generate_executive_summary_content(self, sync_results: Dict[str, Any]) -> str:
        """
        Generate comprehensive executive summary content (TASK027 Phase 1.4)
        
        Args:
            sync_results: Complete sync operation results
            
        Returns:
            Formatted markdown executive summary
        """
        sync_id = sync_results.get('sync_id', 'UNKNOWN')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Build comprehensive summary
        summary_lines = [
            f"# SYNC EXECUTIVE SUMMARY",
            f"",
            f"**Sync ID**: {sync_id}",
            f"**Timestamp**: {timestamp}",
            f"**Status**: {'✅ SUCCESS' if sync_results.get('success', False) else '❌ FAILED'}",
            f"",
        ]
        
        # Add customer results table if available
        if sync_results.get('per_customer_results'):
            summary_lines.extend([
                f"## Customer Results",
                f"",
                f"| Customer | Status | Records Processed | Number of Errors | Execution Time |",
                f"|----------|--------|-------------------|------------------|----------------|",
            ])
            
            for customer_name, customer_data in sync_results['per_customer_results'].items():
                status_emoji = "✅ SUCCESS" if customer_data.get('success', False) else "❌ FAILED"
                records_processed = customer_data.get('records_synced', 0)
                errors = len(customer_data.get('batch_results', []))  # Count failed batches as errors
                errors = sum(1 for batch in customer_data.get('batch_results', []) if not batch.get('success', True))
                execution_time = f"{customer_data.get('execution_time', 0):.2f}s"
                
                summary_lines.append(f"| {customer_name} | {status_emoji} | {records_processed} | {errors} | {execution_time} |")
            
            summary_lines.append(f"")
        
        summary_lines.extend([
            f"## Performance Metrics",
            f"- **Records Processed**: {sync_results.get('total_synced', 0):,}",
            f"- **Execution Time**: {sync_results.get('execution_time_seconds', 0):.2f}s",
        ])
        
        # Add throughput if available
        if sync_results.get('total_synced', 0) > 0 and sync_results.get('execution_time_seconds', 0) > 0:
            throughput = sync_results['total_synced'] / sync_results['execution_time_seconds']
            summary_lines.append(f"- **Throughput**: {throughput:.1f} records/second")
        
        # Add customer information
        if sync_results.get('customer'):
            summary_lines.extend([
                f"",
                f"## Customer Processing",
                f"- **Target Customer**: {sync_results['customer']}",
            ])
        
        # Add batch processing results
        if sync_results.get('successful_batches') and sync_results.get('batches_processed'):
            success_rate = (sync_results['successful_batches'] / sync_results['batches_processed']) * 100
            summary_lines.extend([
                f"",
                f"## Batch Processing",
                f"- **Successful Batches**: {sync_results['successful_batches']}/{sync_results['batches_processed']}",
                f"- **Success Rate**: {success_rate:.1f}%",
            ])
        
        # Add error information if any
        if not sync_results.get('success', False) and sync_results.get('error'):
            summary_lines.extend([
                f"",
                f"## Error Details",
                f"```",
                f"{sync_results['error']}",
                f"```",
            ])
        
        summary_lines.extend([
            f"",
            f"## Output Organization",
            f"- **Customer Reports**: Available in `customer_reports/` folder",
            f"- **Detailed Logs**: Available in `logs/` folder", 
            f"- **Summary Files**: Available in `summaries/` folder",
            f"",
            f"---",
            f"*Generated by TASK027 Phase 1 Sync-Based Output Organization*"
        ])
        
        return '\n'.join(summary_lines)
    
    def run_sync(self, dry_run: bool = False, limit: Optional[int] = None, action_types: List[str] = None, 
                 createitem_mode: str = 'batch', skip_subitems: bool = False, customer_name: Optional[str] = None,
                 retry_errors: bool = False, generate_report: bool = False) -> Dict[str, Any]:
        """
        Enhanced Monday.com synchronization with customer processing and retry functionality.
        Supports both INSERT and UPDATE operations with comprehensive error handling.
        
        Args:
            dry_run: If True, validate queries and API calls but don't execute
            limit: Optional limit on number of records to process
            action_types: List of action types to process (e.g., ['INSERT', 'UPDATE'])
            createitem_mode: Item creation strategy ('single', 'batch', 'asyncBatch')
            skip_subitems: If True, skip subitem creation for faster sync (groups/items only)
            customer_name: Process specific customer (e.g., "GREYSON") (Fix #4: Customer Processing)
            retry_errors: If True, retry failed records before processing new ones (Fix #3: Retry)
            generate_report: If True, generate customer summary report after processing (Fix #4: Customer Processing)
            
        Returns:
            Comprehensive sync results including retry statistics and customer reports
        """
        # Default to INSERT operations for backwards compatibility
        if action_types is None:
            action_types = ['INSERT']
            
        self.logger.info(f"🚀 Enhanced sync workflow starting...")
        self.logger.info(f"   Dry run: {dry_run}, Limit: {limit}, Customer: {customer_name or 'ALL'}")
        self.logger.info(f"   Action types: {action_types}, Mode: {createitem_mode}, Skip subitems: {skip_subitems}")
        self.logger.info(f"   Retry errors: {retry_errors}, Generate report: {generate_report}")
        
        if skip_subitems:
            self.logger.info("⏭️ Subitem processing will be SKIPPED for faster sync (groups/items only)")
        
        sync_start_time = datetime.now()
        performance_start_time = time.time()
        performance_log = {}
        
        def log_performance_milestone(milestone_name: str, start_time: float) -> float:
            """Log performance milestone and return current time for next milestone"""
            current_time = time.time()
            elapsed = current_time - start_time
            performance_log[milestone_name] = elapsed
            self.logger.info(f"⏱️ {milestone_name}: {elapsed:.2f}s")
            return current_time
        
        # Enhanced result structure
        enhanced_results = {
            'status': 'STARTED',
            'customer': customer_name or 'ALL',
            'retry_results': None,
            'customer_report': None,
            'success': False,
            'total_synced': 0,
            'execution_time_seconds': 0
        }
        
        # TASK027 Phase 1: Initialize sync-based output organization
        sync_id = self._generate_sync_id()
        sync_folder = self._create_sync_folder_structure(sync_id)
        enhanced_results['sync_id'] = sync_id
        enhanced_results['sync_folder'] = str(sync_folder)
        enhanced_results['sync_timestamp'] = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Step 1: Handle retry processing if requested (Fix #3: Retry Functionality)
            milestone_time = performance_start_time
            if retry_errors:
                self.logger.info("🔁 Processing retry requests first...")
                retry_results = self.retry_failed_records(
                    customer_name=customer_name, 
                    dry_run=dry_run
                )
                enhanced_results['retry_results'] = retry_results
                milestone_time = log_performance_milestone("Retry Processing", milestone_time)
                
                if not retry_results['success']:
                    self.logger.warning("⚠️  Retry processing had issues, continuing with main sync")
            
            # Step 2: ✅ CUSTOMER-NATIVE ARCHITECTURE: Process one customer at a time
            if customer_name:
                # Single customer mode: Process specified customer only
                customers_to_process = [customer_name]
                self.logger.info(f"🎯 Single customer mode: Processing {customer_name}")
            else:
                # All customers mode: Get list of customers with PENDING records, process each completely
                customers_to_process = self._get_customers_with_pending_records(action_types)
                self.logger.info(f"🔄 Multi-customer mode: Processing {len(customers_to_process)} customers sequentially")
                self.logger.info(f"   Customers: {', '.join(customers_to_process[:5])}{'...' if len(customers_to_process) > 5 else ''}")
            
            milestone_time = log_performance_milestone("Customer Discovery", milestone_time)
            
            if not customers_to_process:
                self.logger.info(f"No customers found with pending records (action_types: {action_types})")
                enhanced_results.update({
                    'success': True, 
                    'total_synced': 0, 
                    'message': f'No customers with pending records - {action_types}',
                    'status': 'NO_CUSTOMERS'
                })
                return enhanced_results
            
            # Step 3: Process each customer completely before moving to next
            all_customer_results = []
            customer_batches = {}  # For compatibility with existing code
            all_pending_headers = []  # Collect headers for group creation
            
            for current_customer in customers_to_process:
                self.logger.info(f"🔄 Processing customer: {current_customer}")
                
                # Get this customer's pending headers (limit applied per customer)
                customer_headers = self._get_pending_headers(limit, action_types, current_customer)
                
                if not customer_headers:
                    continue
                
                all_pending_headers.extend(customer_headers)
                
                # Group this customer's headers by record_uuid
                customer_uuid_batches = self._group_by_customer_and_uuid(customer_headers)
                customer_batches.update(customer_uuid_batches)
            
            if not all_pending_headers:
                self.logger.info(f"No pending headers found across all customers")
                enhanced_results.update({
                    'success': True, 
                    'total_synced': 0, 
                    'message': 'No pending headers found across all customers',
                    'status': 'NO_RECORDS'
                })
                return enhanced_results
            
            self.logger.info(f"✅ Total headers collected: {len(all_pending_headers)} across {len(customers_to_process)} customers")
            
            # Step 4: Create ALL needed groups ONCE before processing any records
            self.logger.info("🏗️ Pre-creating all necessary groups for batch...")
            groups_result = self._create_groups_for_headers(all_pending_headers, dry_run)
            if not groups_result.get('success', False):
                enhanced_results.update({
                    'success': False,
                    'error': 'Batch group creation failed',
                    'groups_result': groups_result,
                    'status': 'GROUP_CREATION_FAILED'
                })
                return enhanced_results

            groups_created = groups_result.get('groups_created', 0)
            self.logger.info(f"✅ Pre-created {groups_created} groups for entire batch")
            
            milestone_time = log_performance_milestone("Group Creation", milestone_time)
            
            total_synced = 0
            all_results = []
            
            # TRUE BATCH PROCESSING: Process multiple record_uuids in single API calls
            self.logger.info(f"🚀 Starting TRUE BATCH PROCESSING with batch_size={self.batch_size}")
            
            # Create true batches across multiple record_uuids  
            true_batches = self._create_true_batch_groups(all_pending_headers, self.batch_size)
            
            total_synced = 0
            all_results = []
            
            # Process each true batch (multiple record_uuids per API call)
            for batch_index, batch_records in enumerate(true_batches, 1):
                try:
                    # Process this true batch atomically (groups already pre-created)
                    batch_result = self._process_true_batch(batch_records, batch_index, dry_run, 
                                                          createitem_mode=createitem_mode, skip_subitems=skip_subitems)
                    all_results.append(batch_result)
                    
                    if batch_result.get('success', False):
                        total_synced += batch_result.get('records_processed', 0)
                        
                except Exception as e:
                    self.logger.error(f"Failed to process batch {batch_index}: {e}")
                    all_results.append({
                        'success': False,
                        'batch_number': batch_index,
                        'error': str(e),
                        'records_processed': 0
                    })
            
            milestone_time = log_performance_milestone("Monday.com Sync Operations", milestone_time)
            
            # Calculate results
            sync_duration = (datetime.now() - sync_start_time).total_seconds()
            successful_batches = len([r for r in all_results if r.get('success', False)])
            
            # Update enhanced results with sync details
            enhanced_results.update({
                'success': successful_batches > 0,
                'total_synced': total_synced,
                'batches_processed': len(all_results),
                'successful_batches': successful_batches,
                'failed_batches': len(all_results) - successful_batches,
                'execution_time_seconds': sync_duration,
                'sync_timestamp': sync_start_time,
                'action_types': action_types,
                'dry_run': dry_run,
                'batch_results': all_results,
                'status': 'COMPLETED' if successful_batches > 0 else 'FAILED'
            })
            
            # Generate enhanced customer summary data for reporting
            enhanced_results['customer_summary'] = self._generate_customer_summary_data(
                all_pending_headers, all_results, customer_name
            )
            
            # 🗄️ PERFORMANCE FIX: API archival disabled during sync operations
            # API archival moved to separate background process for performance
            # This was causing 30+ second delays processing 1717+ historical records
            if successful_batches > 0 and not dry_run:
                self.logger.info("🗄️ API archival SKIPPED for performance - run separately via api_logging_archiver.py")
                enhanced_results['api_archival'] = {'status': 'skipped_for_performance', 'message': 'Run api_logging_archiver.py separately'}
            
            # Step 4: Generate customer report if requested (Fix #4: Customer Processing)
            # TASK027 Phase 2.0: CRITICAL - Always generate customer reports, even on errors
            if generate_report:
                try:
                    if customer_name:
                        # Generate report for specific customer
                        self.logger.info(f"📊 Generating customer report for {customer_name}")
                        enhanced_results['customer_report'] = self.generate_customer_processing_report(customer_name, enhanced_results)
                    else:
                        # Generate reports for all customers processed in this sync
                        self.logger.info(f"📊 Generating customer reports for all processed customers")
                        enhanced_results['customer_reports'] = self.generate_all_customer_reports(enhanced_results)
                except Exception as report_error:
                    self.logger.error(f"❌ Customer report generation failed: {report_error}")
                    # Ensure we still have a report entry even if generation fails
                    if customer_name:
                        enhanced_results['customer_report'] = f"# {customer_name}\n\n❌ Report generation failed: {report_error}"
                    else:
                        enhanced_results['customer_reports'] = {'error': f"Report generation failed: {report_error}"}
            
            self.logger.info(f"✅ Enhanced sync completed! Total synced: {total_synced}, "
                           f"Successful batches: {successful_batches}/{len(all_results)}")
            
            # Task 3: Performance Summary Report
            log_performance_milestone("Report Generation", milestone_time)
            total_performance_time = time.time() - performance_start_time
            records_per_second = total_synced / total_performance_time if total_performance_time > 0 else 0
            
            self.logger.info("📊 PERFORMANCE SUMMARY:")
            self.logger.info(f"   Total Time: {total_performance_time:.2f}s")
            self.logger.info(f"   Records Processed: {total_synced}")
            self.logger.info(f"   Throughput: {records_per_second:.1f} records/second")
            for milestone, duration in performance_log.items():
                percentage = (duration / total_performance_time) * 100 if total_performance_time > 0 else 0
                self.logger.info(f"   {milestone}: {duration:.2f}s ({percentage:.1f}%)")
            
            # Add performance data to results
            enhanced_results['performance'] = {
                'total_time_seconds': total_performance_time,
                'records_per_second': records_per_second,
                'milestones': performance_log
            }
            enhanced_results['processing_time'] = total_performance_time  # TASK027: Group summary compatibility
            enhanced_results['successful_batches'] = successful_batches
            enhanced_results['total_batches'] = len(all_results) if 'all_results' in locals() else 1
            enhanced_results['success'] = successful_batches > 0  # TASK027 Phase 2: Fix sync status reporting
            enhanced_results['total_synced'] = total_synced
            
            # TASK027 Phase 1.4: Persist executive summary to sync folder
            self._persist_executive_summary(sync_folder, enhanced_results)
            
            return enhanced_results
            
        except Exception as e:
            sync_duration = (datetime.now() - sync_start_time).total_seconds()
            self.logger.error(f"Enhanced sync workflow failed: {e}")
            enhanced_results.update({
                'success': False,
                'error': str(e),
                'execution_time_seconds': sync_duration,
                'status': 'FAILED'
            })
            
            # TASK027 Phase 2.0: CRITICAL - Generate customer reports even when sync fails
            if generate_report:
                try:
                    self.logger.info(f"📊 Generating customer report despite sync failure")
                    if customer_name:
                        enhanced_results['customer_report'] = self.generate_customer_processing_report(customer_name, enhanced_results)
                    else:
                        enhanced_results['customer_reports'] = self.generate_all_customer_reports(enhanced_results)
                except Exception as report_error:
                    self.logger.error(f"❌ Customer report generation failed during exception handling: {report_error}")
                    # Ensure we still have a report entry
                    if customer_name:
                        enhanced_results['customer_report'] = f"# {customer_name}\n\n❌ Report generation failed: {report_error}"
                    else:
                        enhanced_results['customer_reports'] = {'error': f"Report generation failed: {report_error}"}
            
            # TASK027 Phase 1.4: Persist executive summary even on failure
            if hasattr(self, 'sync_session_dir') and self.sync_session_dir:
                self._persist_executive_summary(self.sync_session_dir, enhanced_results)
            
            return enhanced_results
    
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
                continue
                
            if customer_name not in customer_batches:
                customer_batches[customer_name] = {}
                
            if record_uuid not in customer_batches[customer_name]:
                customer_batches[customer_name][record_uuid] = []
                
            customer_batches[customer_name][record_uuid].append(header)
        
        return customer_batches
    
    def _create_true_batch_groups(self, headers: List[Dict], batch_size: int = None) -> List[List[Dict]]:
        """
        Create batches of headers across multiple record_uuids (TRUE BATCHING)
        
        This method creates batches of records regardless of record_uuid,
        allowing multiple record_uuids in a single Monday.com API call.
        
        Args:
            headers: List of header records to batch
            batch_size: Number of records per batch (defaults to config item_batch_size)
            
        Returns:
            List of batches, where each batch is a list of header records
        """
        if batch_size is None:
            batch_size = self.batch_size
            
        # Group headers by customer first for consistency
        customer_groups = {}
        for header in headers:
            customer_name = header.get('CUSTOMER NAME', 'UNKNOWN')
            if customer_name not in customer_groups:
                customer_groups[customer_name] = []
            customer_groups[customer_name].append(header)
        
        # Create batches within each customer (ensuring proper ordering)
        all_batches = []
        for customer_name, customer_headers in customer_groups.items():
            # Create batches of specified size
            for i in range(0, len(customer_headers), batch_size):
                batch = customer_headers[i:i + batch_size]
                all_batches.append(batch)
                
        self.logger.info(f"🚀 TRUE BATCH PROCESSING: {len(headers)} records in {len(all_batches)} batches (size: {batch_size})")
        return all_batches
    
    def run_sync_per_customer_sequential(self, dry_run: bool = False, limit: Optional[int] = None, action_types: List[str] = None, 
                                       createitem_mode: str = 'batch', skip_subitems: bool = False, customer_name: Optional[str] = None,
                                       retry_errors: bool = False, generate_report: bool = False) -> Dict[str, Any]:
        """
        EXPERIMENTAL: Per-Customer Sequential Sync Processing
        
        This method processes customers one at a time with isolated group creation:
        1. Loop through each customer individually
        2. Create groups for THIS customer only  
        3. Process THIS customer's batches
        4. Generate THIS customer's report immediately
        5. Move to next customer
        
        Benefits:
        - Customer isolation (failures don't affect other customers)
        - Immediate per-customer reporting  
        - Better debugging and error tracking
        - Can skip problematic customers
        
        Args:
            Same as run_sync() but with per-customer isolation
            
        Returns:
            Enhanced results with per-customer breakdown
        """
        # Default to INSERT operations for backwards compatibility
        if action_types is None:
            action_types = ['INSERT']
            
        self.logger.info(f"🚀 EXPERIMENTAL: Per-Customer Sequential Sync Processing")
        self.logger.info(f"   Dry run: {dry_run}, Limit: {limit}, Customer: {customer_name or 'ALL'}")
        self.logger.info(f"   Action types: {action_types}, Mode: {createitem_mode}, Skip subitems: {skip_subitems}")
        
        sync_start_time = datetime.now()
        
        # TASK027 Phase 1: Initialize sync-based output organization
        sync_id = self._generate_sync_id()
        sync_folder = self._create_sync_folder_structure(sync_id)
        
        # Store sync session attributes for report generation
        self.sync_id = sync_id
        self.sync_session_dir = sync_folder
        
        # Enhanced result structure with per-customer tracking
        enhanced_results = {
            'status': 'STARTED',
            'customer': customer_name or 'ALL',
            'sync_id': sync_id,
            'sync_folder': str(sync_folder),
            'sync_timestamp': datetime.now().strftime("%Y%m%d_%H%M%S"),
            'success': False,
            'total_synced': 0,
            'execution_time_seconds': 0,
            'per_customer_results': {},  # NEW: Track each customer individually
            'processing_mode': 'PER_CUSTOMER_SEQUENTIAL'
        }
        
        try:
            # Step 1: Determine customers to process
            if customer_name:
                customers_to_process = [customer_name]
                self.logger.info(f"🎯 Single customer mode: {customer_name}")
            else:
                customers_to_process = self._get_customers_with_pending_records(action_types)
                self.logger.info(f"🔄 Multi-customer sequential mode: {len(customers_to_process)} customers")
                self.logger.info(f"   Customers: {', '.join(customers_to_process[:5])}{'...' if len(customers_to_process) > 5 else ''}")
            
            if not customers_to_process:
                enhanced_results.update({
                    'success': True,
                    'total_synced': 0,
                    'message': 'No customers with pending records found',
                    'status': 'NO_CUSTOMERS'
                })
                return enhanced_results
            
            # Step 2: Process each customer sequentially with isolation
            total_synced_all_customers = 0
            successful_customers = 0
            failed_customers = 0
            
            for current_customer in customers_to_process:
                customer_start_time = datetime.now()
                self.logger.info(f"🔄 [{current_customer}] Starting isolated customer processing...")
                
                try:
                    # Phase 1: Get this customer's headers
                    customer_headers = self._get_pending_headers(limit, action_types, current_customer)
                    
                    if not customer_headers:
                        self.logger.info(f"📝 [{current_customer}] No pending headers found, skipping")
                        enhanced_results['per_customer_results'][current_customer] = {
                            'success': True,
                            'status': 'NO_RECORDS',
                            'records_synced': 0,
                            'execution_time': 0,
                            'message': 'No pending headers'
                        }
                        continue
                    
                    self.logger.info(f"📊 [{current_customer}] Found {len(customer_headers)} pending headers")
                    
                    # Phase 2: Create groups for THIS customer only (ISOLATION)
                    self.logger.info(f"🏗️ [{current_customer}] Creating groups (isolated from other customers)")
                    customer_groups_result = self._create_customer_groups(customer_headers, current_customer, dry_run)
                    
                    if not customer_groups_result.get('success', False):
                        self.logger.error(f"❌ [{current_customer}] Group creation failed: {customer_groups_result.get('error')}")
                        enhanced_results['per_customer_results'][current_customer] = {
                            'success': False,
                            'status': 'GROUP_CREATION_FAILED',
                            'error': customer_groups_result.get('error'),
                            'records_synced': 0,
                            'execution_time': (datetime.now() - customer_start_time).total_seconds()
                        }
                        failed_customers += 1
                        continue  # Skip to next customer (ISOLATION)
                    
                    groups_created = customer_groups_result.get('groups_created', 0)
                    created_group_ids = customer_groups_result.get('created_group_ids', [])
                    self.logger.info(f"✅ [{current_customer}] Created {groups_created} groups successfully: {created_group_ids}")
                    
                    # Phase 3: Process THIS customer's batches
                    customer_batches = self._create_true_batch_groups(customer_headers, self.batch_size)
                    self.logger.info(f"🚀 [{current_customer}] Processing {len(customer_batches)} batches")
                    
                    customer_results = []
                    customer_synced = 0
                    
                    for batch_index, batch_records in enumerate(customer_batches, 1):
                        try:
                            # Groups already created, so skip group creation in batch processing
                            batch_result = self._process_true_batch(batch_records, batch_index, dry_run,
                                                                  createitem_mode=createitem_mode, skip_subitems=skip_subitems)
                            customer_results.append(batch_result)
                            
                            if batch_result.get('success', False):
                                customer_synced += batch_result.get('records_processed', 0)
                                
                        except Exception as batch_error:
                            self.logger.error(f"❌ [{current_customer}] Batch {batch_index} failed: {batch_error}")
                            customer_results.append({
                                'success': False,
                                'batch_number': batch_index,
                                'error': str(batch_error),
                                'records_processed': 0
                            })
                    
                    # Phase 4: Calculate customer results
                    customer_execution_time = (datetime.now() - customer_start_time).total_seconds()
                    customer_successful_batches = len([r for r in customer_results if r.get('success', False)])
                    customer_success = customer_successful_batches > 0
                    
                    # Store per-customer results
                    enhanced_results['per_customer_results'][current_customer] = {
                        'success': customer_success,
                        'status': 'COMPLETED' if customer_success else 'FAILED',
                        'records_synced': customer_synced,
                        'execution_time': customer_execution_time,
                        'batches_processed': len(customer_results),
                        'successful_batches': customer_successful_batches,
                        'groups_created': groups_created,
                        'created_group_ids': created_group_ids,
                        'group_creation_result': customer_groups_result,
                        'batch_results': customer_results
                    }
                    
                    # Phase 5: Generate report for THIS customer immediately
                    if generate_report:
                        try:
                            customer_report = self.generate_customer_processing_report(current_customer, {
                                'customer_summary': self._generate_customer_summary_data(customer_headers, customer_results, current_customer),
                                'sync_id': sync_id,
                                'sync_folder': sync_folder,
                                'success': customer_success,  # Fix sync status reporting bug
                                'successful_batches': customer_successful_batches,
                                'total_batches': len(customer_results),
                                'execution_time_seconds': customer_execution_time
                            })
                            enhanced_results['per_customer_results'][current_customer]['report_generated'] = True
                            enhanced_results['per_customer_results'][current_customer]['report_path'] = customer_report
                            self.logger.info(f"📊 [{current_customer}] Report generated: {customer_report}")
                        except Exception as report_error:
                            self.logger.error(f"❌ [{current_customer}] Report generation failed: {report_error}")
                            enhanced_results['per_customer_results'][current_customer]['report_error'] = str(report_error)
                    
                    # Update totals
                    total_synced_all_customers += customer_synced
                    if customer_success:
                        successful_customers += 1
                        self.logger.info(f"✅ [{current_customer}] Completed successfully: {customer_synced} records in {customer_execution_time:.2f}s")
                    else:
                        failed_customers += 1
                        self.logger.error(f"❌ [{current_customer}] Failed processing")
                    
                except Exception as customer_error:
                    customer_execution_time = (datetime.now() - customer_start_time).total_seconds()
                    self.logger.exception(f"❌ [{current_customer}] Unexpected error: {customer_error}")
                    enhanced_results['per_customer_results'][current_customer] = {
                        'success': False,
                        'status': 'EXCEPTION',
                        'error': str(customer_error),
                        'records_synced': 0,
                        'execution_time': customer_execution_time
                    }
                    failed_customers += 1
            
            # Step 3: Calculate final results
            sync_duration = (datetime.now() - sync_start_time).total_seconds()
            overall_success = successful_customers > 0
            
            enhanced_results.update({
                'success': overall_success,
                'total_synced': total_synced_all_customers,
                'execution_time_seconds': sync_duration,
                'customers_processed': len(customers_to_process),
                'successful_customers': successful_customers,
                'failed_customers': failed_customers,
                'status': 'COMPLETED' if overall_success else 'FAILED'
            })
            
            # Step 4: Persist executive summary
            self._persist_executive_summary(sync_folder, enhanced_results)
            
            self.logger.info(f"✅ PER-CUSTOMER SEQUENTIAL SYNC COMPLETED:")
            self.logger.info(f"   Total Records: {total_synced_all_customers}")
            self.logger.info(f"   Customers: {successful_customers}/{len(customers_to_process)} successful") 
            self.logger.info(f"   Duration: {sync_duration:.2f}s")
            
            return enhanced_results
            
        except Exception as e:
            sync_duration = (datetime.now() - sync_start_time).total_seconds()
            self.logger.exception(f"❌ Per-customer sequential sync failed: {e}")
            
            enhanced_results.update({
                'success': False,
                'error': str(e),
                'execution_time_seconds': sync_duration,
                'status': 'EXCEPTION'
            })
            
            return enhanced_results
    
    def _process_true_batch(self, batch_records: List[Dict], batch_number: int, dry_run: bool, 
                           createitem_mode: str = 'batch', skip_subitems: bool = False) -> Dict[str, Any]:
        """
        Process a true batch of records (multiple record_uuids in single API call)
        
        This method processes multiple record_uuids together:
        1. Extract all record_uuids from batch
        2. Send single Monday.com batch API call (up to 5 records)
        3. Map response back to individual record_uuids
        4. Update database with proper monday_item_id mapping
        
        Args:
            batch_records: List of records (potentially different record_uuids)
            batch_number: Batch number for logging
            dry_run: Whether this is a dry run execution
            createitem_mode: API mode ('batch' for true batching)
            skip_subitems: Whether to skip subitem processing
            
        Returns:
            Dictionary with batch processing results
        """
        try:
            batch_start_time = datetime.now()
            
            # Extract record_uuids from batch
            record_uuids = []
            uuid_to_records = {}
            
            for record in batch_records:
                record_uuid = record.get('record_uuid')
                if record_uuid and record_uuid not in uuid_to_records:
                    record_uuids.append(record_uuid)
                    uuid_to_records[record_uuid] = []
                if record_uuid:
                    uuid_to_records[record_uuid].append(record)
                    
            self.logger.info(f"🚀 BATCH #{batch_number}: Processing {len(batch_records)} records across {len(record_uuids)} record_uuids")
            
            if dry_run:
                # Dry run simulation
                batch_duration = (datetime.now() - batch_start_time).total_seconds()
                self.logger.info(f"✅ BATCH #{batch_number} DRY RUN COMPLETE: {len(batch_records)} records in {batch_duration:.2f}s")
                return {
                    'success': True,
                    'batch_number': batch_number,
                    'records_processed': len(batch_records),
                    'record_uuids': record_uuids,
                    'dry_run': True,
                    'batch_duration': batch_duration
                }
            
            # Get database connection for batch
            with db.get_connection(self.config.db_key) as connection:
                try:
                    # Step 1: Send batch API call to Monday.com
                    api_start_time = datetime.now()
                    self.logger.info(f"📤 API REQUEST - Batch #{batch_number}: Sending {len(batch_records)} records to Monday.com")
                    
                    # Map createitem_mode to correct API operation
                    api_operation = {
                        'batch': 'batch_create_items',
                        'asyncBatch': 'async_batch_create_items',
                        'single': 'create_items'
                    }.get(createitem_mode, 'batch_create_items')
                    
                    api_result = self.monday_client.execute(api_operation, batch_records, dry_run=False)
                    
                    api_duration = (datetime.now() - api_start_time).total_seconds()
                    self.logger.info(f"📥 API RESPONSE - Batch #{batch_number}: Received in {api_duration:.3f}s")
                    
                    if not api_result.get('success', False):
                        raise Exception(f"Monday.com API call failed: {api_result}")
                    
                    # Step 2: Extract monday_item_ids from response
                    monday_item_ids = api_result.get('monday_ids', [])
                    
                    if len(monday_item_ids) != len(record_uuids):
                        raise Exception(f"Monday.com response mismatch: {len(record_uuids)} record_uuids but {len(monday_item_ids)} item_ids")
                    
                    # Step 3: Map record_uuids to monday_item_ids and update database
                    update_start_time = datetime.now()
                    updated_records = 0
                    
                    for i, record_uuid in enumerate(record_uuids):
                        monday_item_id = monday_item_ids[i]
                        
                        # Capture API logging data for this record
                        api_logging_data = self._capture_api_logging_data(
                            createitem_mode, 
                            uuid_to_records[record_uuid], 
                            api_result.get('api_response', {})
                        )
                        
                        # Update database with monday_item_id
                        self._update_headers_delta_with_item_ids_conn(record_uuid, [str(monday_item_id)], connection, api_logging_data)
                        updated_records += 1
                        
                        # Log the mapping
                        self.logger.info(f"🔗 MAPPING - Batch #{batch_number}: {record_uuid} → monday_item_id: {monday_item_id}")
                    
                    # Commit all database updates for this batch
                    connection.commit()
                    
                    update_duration = (datetime.now() - update_start_time).total_seconds()
                    batch_duration = (datetime.now() - batch_start_time).total_seconds()
                    
                    self.logger.info(f"💾 DATABASE UPDATES - Batch #{batch_number}: {updated_records} records updated in {update_duration:.3f}s")
                    self.logger.info(f"✅ BATCH #{batch_number} COMPLETE: {len(batch_records)} records in {batch_duration:.3f}s")
                    
                    # Connection cleanup handled by 'with' statement automatically
                    
                    return {
                        'success': True,
                        'batch_number': batch_number,
                        'records_processed': len(batch_records),
                        'record_uuids': record_uuids,
                        'monday_item_ids': monday_item_ids,
                        'api_duration': api_duration,
                        'update_duration': update_duration,
                        'batch_duration': batch_duration,
                        'dry_run': False
                    }
                    
                except Exception as e:
                    connection.rollback()
                    # Connection cleanup handled by 'with' statement automatically
                    raise
                    
        except Exception as e:
            batch_duration = (datetime.now() - batch_start_time).total_seconds()
            self.logger.error(f"❌ BATCH #{batch_number} FAILED: {e} (duration: {batch_duration:.3f}s)")
            return {
                'success': False,
                'batch_number': batch_number,
                'records_processed': 0,
                'error': str(e),
                'batch_duration': batch_duration,
                'dry_run': dry_run
            }

    def _process_record_uuid_batch(self, record_uuid: str, headers: List[Dict[str, Any]], dry_run: bool, 
                                   skip_group_creation: bool = False, createitem_mode: str = 'single', skip_subitems: bool = False) -> Dict[str, Any]:
        """
        Process a single record_uuid batch atomically with SINGLE DATABASE CONNECTION:
        Supports both INSERT and UPDATE operations based on action_type
        1. Create groups (if needed)
        2. For INSERT: Create Monday.com items → get item_ids
        3. For UPDATE: Update Monday.com items using existing monday_item_id
        4. Update FACT_ORDER_LIST with monday_item_id (DELTA-FREE)
        5. Get related lines fromORDER_LIST_LINES (DELTA-FREE)
        6. Inject parent_item_id into lines
        7. For INSERT: Create Monday.com subitems → get subitem_ids
        8. For UPDATE: Update Monday.com subitems using existing monday_subitem_id
        9. Update ORDER_LIST_LINES with monday_subitem_id (DELTA-FREE)
        10. Sync status already written directly to main tables (no propagation needed)
        """
        try:
            
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
            
            # Step 1: Create groups if needed (for both INSERT and UPDATE) - SKIP if already done
            if skip_group_creation:
                self.logger.debug(f"⏭️ Skipping group creation for record_uuid {record_uuid} (already created in batch)")
                groups_result = {'success': True, 'groups_created': 0, 'message': 'Groups pre-created in batch'}
            else:
                groups_result = self._create_groups_for_headers(headers, dry_run)
                
            if not groups_result.get('success', False):
                return {
                    'success': False,
                    'record_uuid': record_uuid,
                    'error': 'Group creation failed',
                    'operation_type': operation_type,
                    'records_synced': 0
                }
            
            # Step 2: Handle items based on operation type with retry logic
            if operation_type == 'UPDATE':
                # For UPDATE: Update existing Monday.com items
                items_result = self._execute_with_retry('update_items', headers, dry_run)
                operation_name = 'Item update'
            else:
                # For INSERT: Create new Monday.com items using specified mode
                if createitem_mode == 'batch':
                    items_result = self._execute_with_retry('batch_create_items', headers, dry_run)
                    operation_name = 'Batch item creation'
                elif createitem_mode == 'asyncBatch':
                    items_result = self._execute_with_retry('async_batch_create_items', headers, dry_run)
                    operation_name = 'Async batch item creation'
                else:  # single mode (default)
                    items_result = self._execute_with_retry('create_items', headers, dry_run)
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
                # Step 3: Update FACT_ORDER_LIST with monday_item_id
                if operation_type == 'UPDATE':
                    # For UPDATE: Don't update monday_item_id (it should stay the same)
                    # Just update sync status to SYNCED
                    self._update_sync_status_only_conn(record_uuid, connection)
                else:
                    # For INSERT: Update with new monday_item_id from API response
                    # 🎯 NEW: Pass API logging data from items_result
                    api_logging_data = items_result.get('api_logging_data')
                    self._update_headers_delta_with_item_ids_conn(record_uuid, monday_item_ids, connection, api_logging_data)
                
                # Step 4: Get related lines for this record_uuid
                related_lines = self._get_lines_by_record_uuid_conn(record_uuid, connection)
                
                if related_lines:
                    # Determine line operation type
                    line_action_types = set(line.get('action_type', 'INSERT') for line in related_lines)
                    line_operation_type = list(line_action_types)[0] if len(line_action_types) == 1 else 'MIXED'
                    
                    # Step 5: Inject parent_item_id into lines
                    lines_with_parent = self._inject_parent_item_ids(related_lines, record_uuid, monday_item_ids)
                    
                    # Step 6: Handle subitems based on operation type with retry logic (CONDITIONAL)
                    if not skip_subitems:
                        if line_operation_type == 'UPDATE':
                            # For UPDATE: Update existing Monday.com subitems
                            subitems_result = self._execute_with_retry('update_subitems', lines_with_parent, dry_run)
                            subitem_operation_name = 'Subitem update'
                        else:
                            # For INSERT: Create new Monday.com subitems
                            subitems_result = self._execute_with_retry('create_subitems', lines_with_parent, dry_run)
                            subitem_operation_name = 'Subitem creation'
                        
                        if subitems_result.get('success', False):
                            monday_subitem_ids = subitems_result.get('monday_ids', [])
                            
                            # Capture API logging data for lines operation (extract from subitems_result)
                            operation_type = subitem_operation_name.lower().replace(' ', '_')
                            request_data = subitems_result.get('api_request', lines_with_parent)
                            response_data = subitems_result.get('api_response', {})
                            
                            api_logging_data = self._capture_api_logging_data(operation_type, request_data, response_data)
                            
                            # Step 7: Update ORDER_LIST_LINES with monday_subitem_id (DIRECT CONNECTION)
                            self._update_lines_delta_with_subitem_ids(record_uuid, monday_subitem_ids, connection, api_logging_data)
                        else:
                            self.logger.warning(f"{subitem_operation_name} failed for record_uuid {record_uuid}")
                    else:
                        self.logger.info(f"⏭️ Skipping subitem processing for record_uuid {record_uuid} ({len(related_lines)} lines) - --skip-subitems flag enabled")
                
                # Manual commit (NO AUTO-COMMIT TRANSACTION NESTING)
                connection.commit()
                connection.close()
                
            except Exception as e:
                connection.rollback()
                connection.close()
                raise
            
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
            
            # 🎯 NEW: Store API logging data even for failed syncs
            if 'api_logging_data' in locals() and api_logging_data:
                try:
                    # Update record with API logging data but keep sync_state as PENDING
                    connection = db.get_connection(self.db_key)
                    update_query = f"""
                    UPDATE [{self.headers_table}]
                    SET [api_request_payload] = ?,
                        [api_response_payload] = ?,
                        [api_request_timestamp] = ?,
                        [api_response_timestamp] = ?,
                        [api_operation_type] = ?,
                        [api_status] = ?
                    WHERE [record_uuid] = '{record_uuid}'
                    """
                    
                    cursor = connection.cursor()
                    cursor.execute(update_query, 
                        api_logging_data.get('api_request_payload'),
                        api_logging_data.get('api_response_payload'),
                        api_logging_data.get('api_request_timestamp'),
                        api_logging_data.get('api_response_timestamp'),
                        api_logging_data.get('api_operation_type'),
                        api_logging_data.get('api_status')
                    )
                    connection.commit()
                    connection.close()
                    
                    self.logger.info(f"Stored API logging data for failed sync: {record_uuid}")
                except Exception as log_e:
                    self.logger.warning(f"Failed to store API logging data for failed sync: {log_e}")
            
            return {
                'success': False,
                'record_uuid': record_uuid,
                'error': str(e),
                'operation_type': operation_type if 'operation_type' in locals() else 'UNKNOWN',
                'records_synced': 0
            }
    
    def _create_groups_for_headers(self, headers: List[Dict[str, Any]], dry_run: bool) -> Dict[str, Any]:
        """
        BINARY LOGIC: Handle group creation workflow for headers
        - group_id NOT NULL → VALIDATE (already exists)
        - group_id NULL → CREATE group → UPDATE database with returned group_id
        
        NOTE: This is the legacy cross-customer method. For per-customer isolation,
        use _create_customer_groups() instead.
        """
        try:
            # Separate headers by group_id status
            headers_with_group_id = []
            headers_need_group_creation = []
            existing_group_ids = set()
            groups_to_create = {}  # {group_name: [headers]}
            
            for header in headers:
                group_id = header.get('group_id')
                group_name = header.get('group_name')
                
                if group_id:
                    # BINARY: group_id exists → validate and use
                    headers_with_group_id.append(header)
                    existing_group_ids.add(group_id)
                elif group_name:
                    # BINARY: group_id NULL → needs creation
                    headers_need_group_creation.append(header)
                    if group_name not in groups_to_create:
                        groups_to_create[group_name] = []
                    groups_to_create[group_name].append(header)
                else:
                    # ERROR: No group_name to create group from
                    aag_order = header.get('AAG ORDER NUMBER', 'unknown')
                    self.logger.error(f"❌ Header missing both group_id AND group_name: {aag_order}")
                    return {
                        'success': False, 
                        'error': f'Header missing both group_id AND group_name: {aag_order}'
                    }
            
            self.logger.info(f"📊 Group Status: {len(headers_with_group_id)} have group_id, {len(headers_need_group_creation)} need creation")
            
            # Handle group creation for headers missing group_id
            groups_created_count = 0
            if groups_to_create and not dry_run:
                self.logger.info(f"🏗️ Creating {len(groups_to_create)} groups: {list(groups_to_create.keys())}")
                
                # Create records for Monday.com API call
                group_records = [{'group_name': group_name} for group_name in groups_to_create.keys()]
                
                # Call Monday.com API to create groups
                create_result = self.monday_client.execute('create_groups', group_records, dry_run=False)
                
                if not create_result.get('success', False):
                    self.logger.error(f"❌ Group creation failed: {create_result.get('error', 'Unknown error')}")
                    return {
                        'success': False,
                        'error': f"Group creation failed: {create_result.get('error', 'Unknown error')}"
                    }
                
                # Extract created group IDs and update database
                created_group_ids = create_result.get('monday_ids', [])
                if len(created_group_ids) != len(groups_to_create):
                    self.logger.error(f"❌ Group ID mismatch: expected {len(groups_to_create)}, got {len(created_group_ids)}")
                    return {
                        'success': False,
                        'error': f"Group ID count mismatch: expected {len(groups_to_create)}, got {len(created_group_ids)}"
                    }
                
                # Update database with new group_ids
                for i, (group_name, headers_for_group) in enumerate(groups_to_create.items()):
                    new_group_id = created_group_ids[i]
                    self.logger.info(f"🆔 Updating database: '{group_name}' → {new_group_id}")
                    
                    # Update all headers for this group
                    for header in headers_for_group:
                        record_uuid = header.get('record_uuid')
                        if record_uuid:
                            self._update_database_group_id(record_uuid, new_group_id)
                            # Update in-memory header for immediate use
                            header['group_id'] = new_group_id
                
                groups_created_count = len(created_group_ids)
                existing_group_ids.update(created_group_ids)
            
            elif groups_to_create and dry_run:
                self.logger.info(f"📝 DRY RUN: Would create {len(groups_to_create)} groups: {list(groups_to_create.keys())}")
                groups_created_count = len(groups_to_create)
            
            total_groups = len(existing_group_ids) + groups_created_count
            self.logger.info(f"✅ All {len(headers)} headers have group_ids: {total_groups} unique groups")
            
            return {
                'success': True, 
                'groups_created': groups_created_count,
                'existing_groups': len(headers_with_group_id),
                'total_groups': total_groups,
                'message': f'Binary logic: {groups_created_count} created, {len(headers_with_group_id)} existing'
            }
            
        except Exception as e:
            self.logger.exception(f"Failed to validate group_ids: {e}")
            return {'success': False, 'error': str(e)}
    
    def _create_customer_groups(self, customer_headers: List[Dict[str, Any]], customer_name: str, dry_run: bool) -> Dict[str, Any]:
        """
        Per-Customer Group Creation: Isolated group creation for a specific customer
        
        This method creates groups only for the specified customer, providing:
        1. Customer isolation - failures don't affect other customers
        2. Immediate per-customer reporting
        3. Better debugging and error tracking
        4. Sequential customer processing capability
        
        Args:
            customer_headers: Headers for this specific customer only
            customer_name: Name of the customer for logging and reporting
            dry_run: Whether this is a dry run execution
            
        Returns:
            Dictionary with customer-specific group creation results
        """
        try:
            if not customer_headers:
                return {
                    'success': True,
                    'customer': customer_name,
                    'groups_created': 0,
                    'existing_groups': 0,
                    'total_groups': 0,
                    'message': f'No headers for customer {customer_name}'
                }
            
            self.logger.info(f"🏗️ [{customer_name}] Creating groups for {len(customer_headers)} headers")
            
            # Use existing binary logic but with customer context
            headers_with_group_id = []
            headers_need_group_creation = []
            existing_group_ids = set()
            groups_to_create = {}  # {group_name: [headers]}
            
            for header in customer_headers:
                group_id = header.get('group_id')
                group_name = header.get('group_name')
                
                if group_id:
                    # BINARY: group_id exists → validate and use
                    headers_with_group_id.append(header)
                    existing_group_ids.add(group_id)
                elif group_name:
                    # BINARY: group_id NULL → needs creation
                    headers_need_group_creation.append(header)
                    if group_name not in groups_to_create:
                        groups_to_create[group_name] = []
                    groups_to_create[group_name].append(header)
                else:
                    # ERROR: No group_name to create group from
                    aag_order = header.get('AAG ORDER NUMBER', 'unknown')
                    self.logger.error(f"❌ [{customer_name}] Header missing both group_id AND group_name: {aag_order}")
                    return {
                        'success': False,
                        'customer': customer_name,
                        'error': f'Header missing both group_id AND group_name: {aag_order}'
                    }
            
            self.logger.info(f"📊 [{customer_name}] Group Status: {len(headers_with_group_id)} existing, {len(headers_need_group_creation)} need creation")
            
            # Handle group creation for headers missing group_id
            groups_created_count = 0
            created_group_ids = []
            
            if groups_to_create and not dry_run:
                self.logger.info(f"🏗️ [{customer_name}] Creating {len(groups_to_create)} groups: {list(groups_to_create.keys())}")
                
                # Create records for Monday.com API call
                group_records = [{'group_name': group_name} for group_name in groups_to_create.keys()]
                
                # Call Monday.com API to create groups
                create_result = self.monday_client.execute('create_groups', group_records, dry_run=False)
                
                if not create_result.get('success', False):
                    self.logger.error(f"❌ [{customer_name}] Group creation failed: {create_result.get('error', 'Unknown error')}")
                    return {
                        'success': False,
                        'customer': customer_name,
                        'error': f"Group creation failed: {create_result.get('error', 'Unknown error')}"
                    }
                
                # Extract created group IDs and update database
                created_group_ids = create_result.get('monday_ids', [])
                if len(created_group_ids) != len(groups_to_create):
                    self.logger.error(f"❌ [{customer_name}] Group ID mismatch: expected {len(groups_to_create)}, got {len(created_group_ids)}")
                    return {
                        'success': False,
                        'customer': customer_name,
                        'error': f"Group ID count mismatch: expected {len(groups_to_create)}, got {len(created_group_ids)}"
                    }
                
                # Update database with new group_ids
                total_records_updated = 0
                for i, (group_name, headers_for_group) in enumerate(groups_to_create.items()):
                    new_group_id = created_group_ids[i]
                    self.logger.info(f"🆔 [{customer_name}] Updating database: '{group_name}' → {new_group_id}")
                    
                    # 🎯 CRITICAL FIX: Update ALL pending records with this group_name for this customer
                    records_updated = self._update_all_pending_records_with_group_name(customer_name, group_name, new_group_id)
                    total_records_updated += records_updated
                    
                    # Also update in-memory headers for immediate use in current batch
                    for header in headers_for_group:
                        header['group_id'] = new_group_id
                
                self.logger.info(f"🎯 [{customer_name}] Database update complete: {total_records_updated} total records updated across {len(created_group_ids)} groups")
                groups_created_count = len(created_group_ids)
                existing_group_ids.update(created_group_ids)
            
            elif groups_to_create and dry_run:
                self.logger.info(f"📝 [{customer_name}] DRY RUN: Would create {len(groups_to_create)} groups: {list(groups_to_create.keys())}")
                groups_created_count = len(groups_to_create)
            
            total_groups = len(existing_group_ids) + groups_created_count
            self.logger.info(f"✅ [{customer_name}] All headers have group_ids: {total_groups} unique groups")
            
            return {
                'success': True,
                'customer': customer_name,
                'groups_created': groups_created_count,
                'existing_groups': len(headers_with_group_id),
                'total_groups': total_groups,
                'created_group_ids': created_group_ids,
                'group_names_created': list(groups_to_create.keys()) if groups_to_create else [],
                'message': f'[{customer_name}] Binary logic: {groups_created_count} created, {len(headers_with_group_id)} existing'
            }
            
        except Exception as e:
            self.logger.exception(f"❌ [{customer_name}] Failed to create customer groups: {e}")
            return {
                'success': False,
                'customer': customer_name,
                'error': str(e)
            }
    
    def _update_database_group_id(self, record_uuid: str, group_id: str) -> bool:
        """Update FACT_ORDER_LIST with new group_id for given record_uuid"""
        try:
            with db.get_connection(self.db_key) as connection:
                cursor = connection.cursor()
                
                update_sql = """
                UPDATE [FACT_ORDER_LIST]
                SET [group_id] = ?
                WHERE [record_uuid] = ?
                """
                
                cursor.execute(update_sql, (group_id, record_uuid))
                rows_updated = cursor.rowcount
                
                if rows_updated == 0:
                    self.logger.warning(f"❌ No rows updated for record_uuid: {record_uuid}")
                    return False
                
                self.logger.info(f"✅ Updated group_id for record_uuid {record_uuid}: {group_id}")
                cursor.close()
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Failed to update group_id for {record_uuid}: {e}")
            return False

    def _update_all_pending_records_with_group_name(self, customer_name: str, group_name: str, group_id: str) -> int:
        """
        🎯 CRITICAL FIX: Update ALL pending records with matching customer + group_name
        
        This addresses the duplicate group creation issue where only the current batch records
        get updated with group_id, leaving other pending records with NULL group_id.
        
        Args:
            customer_name: Customer name to filter records
            group_name: Group name to match for update
            group_id: Monday.com group ID to set
            
        Returns:
            int: Number of records updated
        """
        try:
            with db.get_connection(self.db_key) as connection:
                cursor = connection.cursor()
                
                update_sql = """
                UPDATE [FACT_ORDER_LIST]
                SET [group_id] = ?,
                    [updated_at] = GETUTCDATE()
                WHERE [CUSTOMER NAME] = ? 
                  AND [group_name] = ?
                  AND ([group_id] IS NULL OR [group_id] = '')
                  AND [sync_state] IN ('NEW', 'PENDING')
                """
                
                cursor.execute(update_sql, (group_id, customer_name, group_name))
                rows_updated = cursor.rowcount
                
                self.logger.info(f"🎯 Updated group_id for {rows_updated} pending records: {customer_name} → {group_name} → {group_id}")
                cursor.close()
                return rows_updated
                
        except Exception as e:
            self.logger.error(f"❌ Failed to update pending records for {customer_name}/{group_name}: {e}")
            return 0
    
    def _store_group_ids_to_database(self, group_names: set, group_ids: List[str], group_data: Dict[str, Any]) -> None:
        """Store Monday.com group IDs back to database after group creation"""
        try:
            if not group_names:
                return
                
            self.logger.info(f"🏗️ Storing group IDs back to database for {len(group_names)} groups...")
            
            # Create mapping from group_name to group_id
            group_name_to_id = {}
            
            # Method 1: Use group_data if available (preferred)
            if group_data:
                for group_name, group_info in group_data.items():
                    if isinstance(group_info, dict) and 'id' in group_info:
                        group_name_to_id[group_name] = group_info['id']
                    elif isinstance(group_info, str):
                        group_name_to_id[group_name] = group_info
            
            # Method 2: Fallback to positional mapping with group_ids list
            elif group_ids and len(group_ids) == len(group_names):
                for i, group_name in enumerate(sorted(group_names)):
                    group_name_to_id[group_name] = group_ids[i]
            
            if not group_name_to_id:
                self.logger.warning("No group ID mappings found to store in database")
                return
            
            # Update database with group_ids
            with db.get_connection(self.db_key) as connection:
                cursor = connection.cursor()
                
                for group_name, group_id in group_name_to_id.items():
                    update_query = f"""
                    UPDATE [{self.headers_table}]
                    SET [group_id] = '{group_id}',
                        [updated_at] = GETUTCDATE()
                    WHERE [group_name] = '{group_name}' 
                      AND ([group_id] IS NULL OR [group_id] = '')
                    """
                    
                    cursor.execute(update_query)
                    rows_updated = cursor.rowcount
                    
                    self.logger.info(f"✅ Updated {rows_updated} records with group_id '{group_id}' for group '{group_name}'")
                
                connection.commit()
                
            self.logger.info(f"✅ Successfully stored {len(group_name_to_id)} group IDs to database")
            
        except Exception as e:
            self.logger.exception(f"Failed to store group IDs to database: {e}")
            raise
    
    def _execute_with_retry(self, operation_type: str, data: List[Dict[str, Any]], dry_run: bool) -> Dict[str, Any]:
        """Execute Monday.com API call with retry logic for 500 errors and timeouts"""
        
        # Capture request timestamp for API logging
        request_timestamp = datetime.utcnow()
        api_logging_data = None
        
        for attempt in range(self.max_retries + 1):  # 0, 1, 2, 3 (4 total attempts)
            try:
                self.logger.info(f"🔄 Executing {operation_type} (attempt {attempt + 1}/{self.max_retries + 1})")
                
                # Execute the API call
                result = self.monday_client.execute(operation_type, data, dry_run)
                
                # 🎯 NEW: Capture API logging data for this attempt
                api_logging_data = self._capture_api_logging_data(operation_type, data, result, request_timestamp)
                
                # If successful, attach API logging data and return immediately
                if result.get('success', False):
                    if attempt > 0:
                        self.logger.info(f"✅ {operation_type} succeeded on retry attempt {attempt + 1}")
                    
                    # 🎯 NEW: Attach API logging data to successful result
                    result['api_logging_data'] = api_logging_data
                    return result
                
                # If failed but not a retryable error, don't retry
                error_msg = result.get('error', '')
                if not self._is_retryable_error(error_msg):
                    self.logger.warning(f"Non-retryable error for {operation_type}: {error_msg}")
                    # 🎯 NEW: Attach API logging data to failed result
                    result['api_logging_data'] = api_logging_data
                    return result
                
                # If this was the last attempt, return the failed result
                if attempt == self.max_retries:
                    self.logger.error(f"❌ {operation_type} failed after {self.max_retries + 1} attempts")
                    # 🎯 NEW: Attach API logging data to final failed result
                    result['api_logging_data'] = api_logging_data
                    return result
                
                # Calculate delay for next retry (exponential backoff)
                delay = min(
                    self.base_retry_delay * (self.retry_backoff_multiplier ** attempt),
                    self.max_retry_delay
                )
                
                self.logger.warning(f"⚠️ {operation_type} failed (attempt {attempt + 1}), retrying in {delay:.1f}s: {error_msg}")
                time.sleep(delay)
                
            except Exception as e:
                error_msg = str(e)
                
                # 🎯 NEW: Capture API logging data for exception case
                if api_logging_data is None:
                    api_logging_data = self._capture_api_logging_data(
                        operation_type, 
                        data, 
                        {'success': False, 'error': error_msg, 'exception': True}, 
                        request_timestamp
                    )
                
                # If this was the last attempt, raise the exception
                if attempt == self.max_retries:
                    self.logger.exception(f"❌ {operation_type} failed after {self.max_retries + 1} attempts with exception")
                    raise
                
                # Check if it's a retryable error
                if not self._is_retryable_error(error_msg):
                    self.logger.exception(f"Non-retryable exception for {operation_type}")
                    raise
                
                # Calculate delay for next retry
                delay = min(
                    self.base_retry_delay * (self.retry_backoff_multiplier ** attempt),
                    self.max_retry_delay
                )
                
                self.logger.warning(f"⚠️ {operation_type} exception (attempt {attempt + 1}), retrying in {delay:.1f}s: {error_msg}")
                time.sleep(delay)
        
        # This should never be reached, but just in case
        final_result = {'success': False, 'error': f'{operation_type} exhausted all retry attempts'}
        
        # 🎯 NEW: Attach final API logging data
        if api_logging_data:
            final_result['api_logging_data'] = api_logging_data
        
        return final_result
    
    def _capture_api_logging_data(self, operation_type: str, request_data: List[Dict[str, Any]], response_data: Dict[str, Any], request_timestamp: datetime = None) -> Dict[str, Any]:
        """
        Capture API request/response data for comprehensive logging
        
        Args:
            operation_type: Type of Monday.com operation ('create_items', 'create_subitems', etc.)
            request_data: The data sent to Monday.com API
            response_data: The response received from Monday.com API
            request_timestamp: When the request was initiated (optional)
            
        Returns:
            Dictionary with all API logging fields ready for database storage
        """
        try:
            current_time = datetime.utcnow()
            
            # Determine API status based on response
            api_status = 'SUCCESS'
            
            # Check for explicit success field (single operations)
            if 'success' in response_data and response_data.get('success') is False:
                api_status = 'ERROR'
            # Check for errors field (GraphQL responses) - only if errors actually exist
            elif 'errors' in response_data and response_data.get('errors'):
                api_status = 'ERROR'
            # Check for explicit error field (custom error responses)
            elif 'error' in response_data:
                api_status = 'ERROR'
            # Check for successful GraphQL data responses (batch operations)
            elif 'data' in response_data:
                # For GraphQL responses with data, consider successful unless data is empty/null
                if response_data['data'] is None or not response_data['data']:
                    api_status = 'ERROR'
                # else: api_status remains 'SUCCESS'
            else:
                print(f"   Status remains SUCCESS (no error conditions met)")
                
            print(f"   Final API status: {api_status}")
            
            # Prepare logging data
            logging_data = {
                'api_operation_type': operation_type,
                'api_request_payload': json.dumps(request_data, default=str, ensure_ascii=False),
                'api_response_payload': json.dumps(response_data, default=str, ensure_ascii=False),
                'api_request_timestamp': request_timestamp or current_time,
                'api_response_timestamp': current_time,
                'api_status': api_status
            }
            
            self.logger.debug(f"📝 Captured API logging data for {operation_type}: status={api_status}")
            return logging_data
            
        except Exception as e:
            self.logger.warning(f"Failed to capture API logging data for {operation_type}: {e}")
            # Return minimal logging data even if JSON serialization fails
            return {
                'api_operation_type': operation_type,
                'api_request_payload': f"JSON_ERROR: {str(e)}",
                'api_response_payload': f"JSON_ERROR: {str(e)}",
                'api_request_timestamp': datetime.utcnow(),
                'api_response_timestamp': datetime.utcnow(),
                'api_status': 'JSON_ERROR'
            }
    
    def _is_retryable_error(self, error_msg) -> bool:
        """Determine if an error is worth retrying"""
        if not error_msg:
            return False
        
        # Handle both string errors and list of error dictionaries
        if isinstance(error_msg, list):
            # Monday.com GraphQL errors - check for retryable conditions
            for error in error_msg:
                if isinstance(error, dict):
                    message = error.get('message', '')
                    extensions = error.get('extensions', {})
                    status_code = extensions.get('status_code', 0)
                    
                    # Retryable status codes
                    if status_code in [500, 502, 503, 504, 429]:
                        return True
                    
                    # Check message for retryable patterns
                    if isinstance(message, str):
                        message_lower = message.lower()
                        retryable_patterns = [
                            'timeout', 'connection', 'network', 'rate limit',
                            'server error', 'service unavailable', 'gateway timeout'
                        ]
                        if any(pattern in message_lower for pattern in retryable_patterns):
                            return True
            
            # Non-retryable GraphQL errors (like column value exceptions)
            return False
        
        # Handle string error messages
        retryable_indicators = [
            '500',  # Internal server error
            'timeout',  # Timeout errors
            'connection',  # Connection errors
            'rate limit',  # Rate limiting (should retry with backoff)
            'temporarily unavailable',  # Temporary service issues
            'service unavailable',  # 503 errors
            'bad gateway',  # 502 errors
            'gateway timeout'  # 504 errors
        ]
        
        error_lower = error_msg.lower()
        return any(indicator in error_lower for indicator in retryable_indicators)
    
    def _get_group_id_from_header(self, header: Dict[str, Any]) -> Optional[str]:
        """
        BINARY LOGIC: Extract group_id from header record
        - group_id NOT NULL → USE existing group_id
        - group_id NULL → CREATE group (handled by caller) → UPDATE database
        NO FALLBACKS - BINARY ONLY
        """
        group_id = header.get('group_id')
        if group_id:
            self.logger.info(f"✅ Using existing database group_id: '{group_id}'")
            return group_id
            
        # BINARY LOGIC: group_id is NULL - caller must create group first
        group_name = header.get('group_name')
        if group_name:
            self.logger.warning(f"⚠️ group_id is NULL - GROUP CREATION REQUIRED for: '{group_name}'")
            return None  # Return None to trigger group creation
            
        self.logger.error("❌ No group_name found - cannot create group or use existing group_id")
        return None
    
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
        """Update FACT_ORDER_LIST (main table - DELTA-FREE) with Monday.com item IDs"""
        with db.get_connection('orders') as connection:
            self._update_headers_delta_with_item_ids_conn(record_uuid, item_ids, connection)
            connection.commit()

    def _update_headers_delta_with_item_ids_conn(self, record_uuid: str, item_ids: List[str], connection, api_logging_data: Dict[str, Any] = None) -> None:
        """Update FACT_ORDER_LIST (main table - DELTA-FREE) with Monday.com item IDs and API logging - CONNECTION PASSING"""
        if not item_ids:
            return
            
        try:
            # Use first item_id (assuming 1 header per record_uuid)
            monday_item_id = item_ids[0]
            
            # Convert string ID to integer for BIGINT column
            monday_item_id_int = int(monday_item_id)
            
            # 🎯 NEW: Build UPDATE query with API logging columns
            if api_logging_data:
                update_query = f"""
                UPDATE [{self.headers_table}]
                SET [monday_item_id] = {monday_item_id_int},
                    [sync_state] = 'SYNCED',
                    [sync_completed_at] = GETUTCDATE(),
                    [api_request_payload] = ?,
                    [api_response_payload] = ?,
                    [api_request_timestamp] = ?,
                    [api_response_timestamp] = ?,
                    [api_operation_type] = ?,
                    [api_status] = ?
                WHERE [record_uuid] = '{record_uuid}'
                """
                
                cursor = connection.cursor()
                cursor.execute(update_query, 
                    api_logging_data.get('api_request_payload'),
                    api_logging_data.get('api_response_payload'),
                    api_logging_data.get('api_request_timestamp'),
                    api_logging_data.get('api_response_timestamp'),
                    api_logging_data.get('api_operation_type'),
                    api_logging_data.get('api_status')
                )
                
                self.logger.info(f"Updated headers with Monday ID {monday_item_id} and API logging data (operation: {api_logging_data.get('api_operation_type')})")
            else:
                # Fallback: Original query without API logging
                update_query = f"""
                UPDATE [{self.headers_table}]
                SET [monday_item_id] = {monday_item_id_int},
                    [sync_state] = 'SYNCED',
                    [sync_completed_at] = GETUTCDATE()
                WHERE [record_uuid] = '{record_uuid}'
                """
                
                cursor = connection.cursor()
                cursor.execute(update_query)
                
                self.logger.info(f"Updated headers with Monday ID {monday_item_id} (no API logging data)")
            
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
    
    def _update_lines_delta_with_subitem_ids(self, record_uuid: str, subitem_ids: List[str], connection=None, api_logging_data=None) -> None:
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
            api_columns = ""
            api_values = ""
            
            # Handle API logging data if provided
            if api_logging_data:
                api_columns = """,
                [api_operation_type] = ?,
                [api_request_payload] = ?,
                [api_response_payload] = ?,
                [api_request_timestamp] = ?,
                [api_response_timestamp] = ?,
                [api_status] = ?"""
            
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
                [sync_completed_at] = GETUTCDATE(){api_columns}
            WHERE [line_uuid] IN ({', '.join(where_conditions)})
            """
            
            # Use provided connection or create new one (CONNECTION PASSING PATTERN)
            if connection:
                cursor = connection.cursor()
                
                # Execute with API logging parameters if provided
                if api_logging_data:
                    cursor.execute(batch_update_query, 
                        api_logging_data.get('api_operation_type'),
                        api_logging_data.get('api_request_payload'),
                        api_logging_data.get('api_response_payload'),
                        api_logging_data.get('api_request_timestamp'),
                        api_logging_data.get('api_response_timestamp'),
                        api_logging_data.get('api_status')
                    )
                else:
                    cursor.execute(batch_update_query)
                    
                # Don't commit here - let caller handle transaction
                rows_updated = cursor.rowcount
                self.logger.info(f"Batch updated {rows_updated} lines with Monday.com subitem IDs for record_uuid: {record_uuid}")
            else:
                # Fallback to single connection (for standalone calls)
                with db.get_connection('orders') as standalone_connection:
                    cursor = standalone_connection.cursor()
                    
                    # Execute with API logging parameters if provided
                    if api_logging_data:
                        cursor.execute(batch_update_query, 
                            api_logging_data.get('api_operation_type'),
                            api_logging_data.get('api_request_payload'),
                            api_logging_data.get('api_response_payload'),
                            api_logging_data.get('api_request_timestamp'),
                            api_logging_data.get('api_response_timestamp'),
                            api_logging_data.get('api_status')
                        )
                    else:
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
    
    def _get_pending_headers(self, limit: Optional[int] = None, action_types: List[str] = None, customer_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get headers records pending Monday.com sync from FACT_ORDER_LIST (main table - DELTA-FREE)
        
        Args:
            limit: Optional limit on number of records
            action_types: List of action types to filter by (e.g., ['INSERT', 'UPDATE'])
            customer_name: Optional customer filter (applied in SQL WHERE clause)
        """
        # Build headers query for FACT_ORDER_LIST (main table) - includes customer filter in SQL
        headers_query = self._build_headers_query(limit, action_types, customer_name)
        
        # DEBUG: Print the generated SQL query
        # (Removed excessive debug logging)
        
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
        # (Removed excessive debug logging)
        
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
    
    def _build_headers_query(self, limit: Optional[int] = None, action_types: List[str] = None, customer_name: Optional[str] = None) -> str:
        """Build query for pending headers from FACT_ORDER_LIST (main table - DELTA-FREE)"""
        
        # Get headers columns from TOML mapping
        headers_columns = self._get_headers_columns()
        columns_clause = ", ".join(headers_columns)
        
        # Default to INSERT operations if no action types specified
        if action_types is None:
            action_types = ['INSERT']
        
        # Build WHERE clause for main table logic (sync_state = 'PENDING' AND action_type IN (...))
        action_type_clause = "', '".join(action_types)
        main_table_clause = f"([sync_state] = 'PENDING' AND [action_type] IN ('{action_type_clause}'))"
        
        # ✅ FIX: Add customer filter to SQL WHERE clause (not Python post-processing)
        if customer_name:
            customer_clause = f" AND [CUSTOMER NAME] = '{customer_name}'"
            main_table_clause += customer_clause
        
        # Build ORDER BY clause - FIXED: Distribute across different groups and customers
        # Original: ORDER BY [AAG ORDER NUMBER] caused all same-customer records to batch together
        # New: ORDER BY group_name, CUSTOMER NAME ensures mixed customer/group processing
        order_clause = "ORDER BY [group_name], [CUSTOMER NAME], [AAG ORDER NUMBER]"
        
        # Build LIMIT clause
        limit_clause = f"TOP ({limit})" if limit else ""
        
        query = f"""
        SELECT {limit_clause} {columns_clause}
        FROM [{self.headers_table}]
        WHERE {main_table_clause}
        {order_clause}
        """
        
        return query.strip()
    
    def _get_customers_with_pending_records(self, action_types: List[str] = None) -> List[str]:
        """
        Get list of customers that have PENDING records for processing
        
        Args:
            action_types: List of action types to filter by (e.g., ['INSERT', 'UPDATE'])
            
        Returns:
            List of customer names with PENDING records, ordered by customer name
        """
        # Default to INSERT operations if no action types specified
        if action_types is None:
            action_types = ['INSERT']
        
        # Build WHERE clause for action types
        action_type_clause = "', '".join(action_types)
        
        query = f"""
        SELECT DISTINCT [CUSTOMER NAME]
        FROM [{self.headers_table}]
        WHERE [sync_state] = 'PENDING' AND [action_type] IN ('{action_type_clause}')
        ORDER BY [CUSTOMER NAME]
        """
        
        try:
            with db.get_connection(self.db_key) as connection:
                cursor = connection.cursor()
                cursor.execute(query)
                customers = [row[0] for row in cursor.fetchall()]
                cursor.close()
                
                self.logger.info(f"Found {len(customers)} customers with PENDING records")
                return customers
                
        except Exception as e:
            self.logger.error(f"Failed to get customers with pending records: {e}")
            raise
    
    def _build_lines_query(self, limit: Optional[int] = None) -> str:
        """Build query for pending lines from ORDER_LIST_LINES (main table - DELTA-FREE)"""
        
        # Get lines columns from TOML mapping
        lines_columns = self._get_lines_columns()
        columns_clause = ", ".join(lines_columns)
        
        # Build WHERE clause for main table logic (sync_state = 'PENDING')
        main_table_clause = "([sync_state] = 'PENDING')"
        
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
        
        # Add CRITICAL sync tracking columns from main table FACT_ORDER_LIST
        # These are REQUIRED for DELTA-FREE sync logic!
        critical_columns = [
            'record_uuid', 'action_type', 'sync_state', 'sync_pending_at',
            'monday_item_id', 'sync_completed_at', 'created_at'
        ]
        headers_columns.update(critical_columns)
        
        # Add CRITICAL transformation columns from Enhanced Merge Orchestrator
        # These are REQUIRED for Monday.com group and item creation!
        transformation_columns = ['group_name', 'group_id', 'item_name']
        headers_columns.update(transformation_columns)
        
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
    
    def retry_failed_records(self, customer_name: Optional[str] = None, max_retries: int = 3, 
                           dry_run: bool = False) -> Dict[str, Any]:
        """
        Retry ERROR records with exponential backoff (Fix #3: Retry Functionality).
        
        Implements intelligent retry for Monday.com sync failures:
        - Exponential backoff for rate limits
        - Error categorization for targeted retry strategies
        - Customer-specific retry processing
        
        Args:
            customer_name: Process specific customer, or None for all
            max_retries: Maximum retry attempts per record
            dry_run: If True, show what would be retried without executing
            
        Returns:
            Dict: Retry processing results and statistics
        """
        import time
        from datetime import datetime
        
        self.logger.info(f"🔁 Starting retry processing (customer: {customer_name or 'ALL'})")
        
        start_time = datetime.now()
        retry_stats = {
            'customer': customer_name or 'ALL',
            'records_identified': 0,
            'records_reset': 0,
            'errors': 0,
            'success': False
        }
        
        try:
            with db.get_connection(self.db_key) as connection:
                cursor = connection.cursor()
                
                # Query for retry candidates
                base_query = """
                SELECT 
                    record_uuid,
                    [CUSTOMER NAME] as customer_name,
                    [AAG ORDER NUMBER] as aag_order_number,
                    api_status,
                    COALESCE(retry_count, 0) as retry_count,
                    sync_error_message
                FROM FACT_ORDER_LIST
                WHERE api_status = 'ERROR' 
                AND COALESCE(retry_count, 0) < ?
                """
                
                params = [max_retries]
                
                if customer_name:
                    base_query += " AND [CUSTOMER NAME] = ?"
                    params.append(customer_name)
                
                base_query += " ORDER BY [CUSTOMER NAME], [AAG ORDER NUMBER]"
                
                cursor.execute(base_query, params)
                retry_candidates = cursor.fetchall()
                
                retry_stats['records_identified'] = len(retry_candidates)
                self.logger.info(f"📋 Found {len(retry_candidates)} records for retry")
                
                if dry_run:
                    self.logger.info("🔍 DRY RUN - Would reset the following records:")
                    for record in retry_candidates[:5]:  # Show first 5
                        uuid, customer, order, status, retry_count, error = record
                        self.logger.info(f"   {customer} | {order} | Retry #{retry_count + 1}")
                    
                    retry_stats['success'] = True
                    return retry_stats
                
                # Reset records for retry
                for record in retry_candidates:
                    record_uuid, customer, order, status, retry_count, error_msg = record
                    
                    # Calculate exponential backoff delay
                    delay = min(2.0 * (2 ** retry_count), 60.0)
                    time.sleep(delay)
                    
                    # Reset record for retry
                    update_query = """
                    UPDATE FACT_ORDER_LIST
                    SET sync_state = 'PENDING',
                        api_status = NULL,
                        retry_count = COALESCE(retry_count, 0) + 1,
                        sync_error_message = NULL,
                        updated_at = GETUTCDATE()
                    WHERE record_uuid = ?
                    """
                    
                    cursor.execute(update_query, (record_uuid,))
                    retry_stats['records_reset'] += 1
                    
                    self.logger.info(f"🔄 Reset for retry: {customer} | {order} | Attempt #{retry_count + 1}")
                
                connection.commit()
                retry_stats['success'] = True
                
                execution_time = (datetime.now() - start_time).total_seconds()
                self.logger.info(f"✅ Retry processing completed in {execution_time:.2f}s")
                
                cursor.close()
                
        except Exception as e:
            self.logger.error(f"❌ Retry processing failed: {e}")
            retry_stats['error'] = str(e)
            retry_stats['errors'] = 1
        
        return retry_stats
    
    def reset_pending_records(self, customer_name: Optional[str] = None, dry_run: bool = False) -> Dict[str, Any]:
        """
        Reset PENDING records for retry (Fix #3: Retry Functionality).
        
        Useful for records stuck in PENDING state that never attempted sync.
        
        Args:
            customer_name: Process specific customer, or None for all
            dry_run: If True, show what would be reset without executing
            
        Returns:
            Dict: Reset processing results and statistics
        """
        self.logger.info(f"🔄 Resetting PENDING records (customer: {customer_name or 'ALL'})")
        
        reset_stats = {
            'customer': customer_name or 'ALL',
            'records_identified': 0,
            'records_reset': 0,
            'success': False
        }
        
        try:
            with db.get_connection(self.db_key) as connection:
                cursor = connection.cursor()
                
                # Query for PENDING records
                base_query = """
                SELECT 
                    record_uuid,
                    [CUSTOMER NAME] as customer_name,
                    [AAG ORDER NUMBER] as aag_order_number
                FROM FACT_ORDER_LIST
                WHERE sync_state = 'PENDING' 
                AND api_status IS NULL
                """
                
                params = []
                
                if customer_name:
                    base_query += " AND [CUSTOMER NAME] = ?"
                    params.append(customer_name)
                
                cursor.execute(base_query, params)
                pending_records = cursor.fetchall()
                
                reset_stats['records_identified'] = len(pending_records)
                self.logger.info(f"📋 Found {len(pending_records)} PENDING records")
                
                if dry_run:
                    self.logger.info("🔍 DRY RUN - Would reset PENDING records")
                    reset_stats['success'] = True
                    return reset_stats
                
                # Update sync_pending_at timestamp to refresh records
                if pending_records:
                    update_query = """
                    UPDATE FACT_ORDER_LIST
                    SET sync_pending_at = GETUTCDATE(),
                        updated_at = GETUTCDATE()
                    WHERE sync_state = 'PENDING' 
                    AND api_status IS NULL
                    """
                    
                    if customer_name:
                        update_query += " AND [CUSTOMER NAME] = ?"
                        cursor.execute(update_query, [customer_name])
                    else:
                        cursor.execute(update_query)
                    
                    reset_stats['records_reset'] = len(pending_records)
                    connection.commit()
                
                reset_stats['success'] = True
                cursor.close()
                
        except Exception as e:
            self.logger.error(f"❌ PENDING reset failed: {e}")
            reset_stats['error'] = str(e)
        
        return reset_stats
    
    def generate_customer_processing_report(self, customer_name: str, sync_session_data: Dict[str, Any] = None) -> str:
        """
        Generate markdown summary report for customer processing results (Fix #4: Customer Processing).
        TASK027 Phase 2: Enhanced with sync session context and metrics.
        
        Creates comprehensive customer-focused report with:
        - TASK027 Phase 2.4: Sync session context (Sync ID, timestamp, processing metrics)
        - TASK027 Phase 2.2: Sync session statistics (API operations, timing, batch success rates)
        - Processing success/failure metrics
        - Error breakdown by category
        - Group distribution analysis
        - Actionable recommendations
        
        Args:
            customer_name: Customer to generate report for
            sync_session_data: Current sync session data including performance metrics and batch results
            
        Returns:
            str: Markdown formatted customer processing report with sync context
        """
        try:
            with db.get_connection(self.db_key) as connection:
                # Use API logging archiver for report generation
                from .api_logging_archiver import APILoggingArchiver
                archiver = APILoggingArchiver(self.config)
                
                cursor = connection.cursor()
                
                # TASK027 Phase 2: Enhanced report with sync session context
                report = archiver.generate_enhanced_customer_summary_report(
                    cursor, 
                    customer_name, 
                    sync_session_data,
                    self.sync_id if hasattr(self, 'sync_id') else None,
                    self.sync_session_dir if hasattr(self, 'sync_session_dir') else None
                )
                cursor.close()
                
                # TASK027 Phase 2.0: Save report to sync-specific customer_reports folder
                if hasattr(self, 'sync_session_dir') and self.sync_session_dir:
                    report_path = self.sync_session_dir / "customer_reports" / f"{customer_name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                    report_path.write_text(report, encoding='utf-8')
                    self.logger.info(f"📄 Customer report saved: {report_path}")
                
                return report
                
        except Exception as e:
            self.logger.error(f"❌ Report generation failed: {e}")
            error_report = f"# {customer_name} - Sync Report\n\n❌ Report generation failed: {e}"
            
            # TASK027 Phase 2.0: Still save error report to sync folder
            if hasattr(self, 'sync_session_dir') and self.sync_session_dir:
                try:
                    report_path = self.sync_session_dir / "customer_reports" / f"{customer_name.lower().replace(' ', '_')}_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                    report_path.write_text(error_report, encoding='utf-8')
                    self.logger.info(f"📄 Error report saved: {report_path}")
                except Exception as save_error:
                    self.logger.error(f"❌ Failed to save error report: {save_error}")
            
            return error_report
    
    def generate_all_customer_reports(self, sync_session_data: Dict[str, Any] = None) -> dict:
        """
        Generate markdown summary reports for all customers processed in current sync.
        TASK027 Phase 2: Enhanced with sync session context.
        
        Args:
            sync_session_data: Current sync session data including performance metrics and batch results
        
        Returns:
            dict: Dictionary with customer names as keys and report content as values
        """
        try:
            with db.get_connection(self.db_key) as connection:
                cursor = connection.cursor()
                
                # Get all customers from recent sync operations
                cursor.execute("""
                    SELECT DISTINCT [CUSTOMER NAME] 
                    FROM FACT_ORDER_LIST 
                    WHERE sync_state IN ('PENDING', 'PROCESSING') 
                    AND [CUSTOMER NAME] IS NOT NULL
                    ORDER BY [CUSTOMER NAME]
                """)
                
                customers = [row[0] for row in cursor.fetchall()]
                customer_reports = {}
                
                if not customers:
                    self.logger.info("📋 No customers found for report generation")
                    return {}
                
                self.logger.info(f"📊 Generating reports for {len(customers)} customers: {', '.join(customers)}")
                
                # Generate report for each customer
                for customer_name in customers:
                    try:
                        report = self.generate_customer_processing_report(customer_name, sync_session_data)
                        customer_reports[customer_name] = report
                        self.logger.info(f"✅ Report generated for {customer_name}")
                    except Exception as e:
                        self.logger.warning(f"⚠️ Failed to generate report for {customer_name}: {e}")
                        customer_reports[customer_name] = f"# {customer_name}\n\n❌ Report generation failed: {e}"
                
                cursor.close()
                return customer_reports
                
        except Exception as e:
            self.logger.error(f"All customer reports generation failed: {e}")
            return {'error': f"All customer reports generation failed: {e}"}

    def _generate_customer_summary_data(self, headers: List[Dict[str, Any]], batch_results: List[Dict[str, Any]], customer_filter: str = None) -> Dict[str, Any]:
        """
        Generate enhanced customer summary data for reporting from headers and batch results
        
        Args:
            headers: List of header records that were processed
            batch_results: List of batch processing results
            customer_filter: Optional customer name filter
            
        Returns:
            Dictionary with customer breakdowns, group summaries, and detailed analytics
        """
        try:
            summary_data = {
                'customers': {},
                'total_customers': 0,
                'total_records': 0,
                'total_groups': 0,
                'success_rate': 0.0
            }
            
            successful_batches = len([r for r in batch_results if r.get('success', False)])
            total_batches = len(batch_results)
            total_records_processed = sum(r.get('records_processed', 0) for r in batch_results if r.get('success', False))
            
            group_names = set()
            customer_records = {}
            
            # Extract customer and group information from headers
            for header in headers:
                customer_name = header.get('CUSTOMER NAME', 'UNKNOWN')
                group_name = header.get('group_name', 'DEFAULT GROUP')
                
                group_names.add(group_name)
                
                if customer_name not in customer_records:
                    customer_records[customer_name] = {
                        'name': customer_name,
                        'records': 0,
                        'groups': set(),
                        'status': 'PROCESSED'
                    }
                
                customer_records[customer_name]['records'] += 1
                customer_records[customer_name]['groups'].add(group_name)
            
            # Convert customer data for summary
            for customer_name, customer_data in customer_records.items():
                summary_data['customers'][customer_name] = {
                    'name': customer_name,
                    'records_processed': customer_data['records'],
                    'groups': list(customer_data['groups']),
                    'status': 'SUCCESS' if successful_batches > 0 else 'FAILED'
                }
            
            # Calculate summary statistics
            summary_data['total_customers'] = len(summary_data['customers'])
            summary_data['total_records'] = len(headers)
            summary_data['total_groups'] = len(group_names)
            summary_data['success_rate'] = (successful_batches / total_batches * 100.0) if total_batches > 0 else 0.0
            summary_data['group_summary'] = list(group_names) if group_names else ['DEFAULT GROUP']
            summary_data['records_synced'] = total_records_processed
            summary_data['batches_successful'] = successful_batches
            summary_data['batches_total'] = total_batches
            
            return summary_data
            
        except Exception as e:
            self.logger.warning(f"Failed to generate customer summary data: {e}")
            return {
                'customers': {},
                'total_customers': 0,
                'total_records': 0,
                'total_groups': 0,
                'success_rate': 0.0,
                'error': str(e)
            }
