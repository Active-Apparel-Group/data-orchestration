"""
Ultra-Lightweight ORDER_LIST Monday.com Sync CLI
===============================================
Purpose: Command-line interface for ORDER_LIST → Monday.com synchronization
Location: src/pipelines/sync_order_list/cli.py
Created: 2025-07-22 (Architecture Simplification)

Ultra-Minimal Architecture:
- 2 files total: monday_api_client.py + sync_engine.py
- Direct TOML + GraphQL template execution
- Zero abstraction layers

Usage:
    python -m src.pipelines.sync_order_list.cli sync --dry-run
    python -m src.pipelines.sync_order_list.cli sync --execute --limit 100
"""

import argparse
import sys
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Modern Python package imports - ultra-minimal dependencies
from src.pipelines.utils import logger

# Import ultra-lightweight components
from .sync_engine import SyncEngine


class UltraLightweightSyncCLI:
    """
    Ultra-lightweight CLI for ORDER_LIST → Monday.com sync
    Direct execution with minimal complexity
    """
    
    def __init__(self, config_path: Optional[str] = None, environment: str = "production"):
        """
        Initialize CLI with TOML configuration
        
        Args:
            config_path: Optional path to sync_order_list.toml configuration (defaults to standard location)
            environment: Environment to use ('development' or 'production')
        """
        # Use default config path if none provided
        if config_path is None:
            # Get absolute path to config file from repository root
            repo_root = Path(__file__).parent.parent.parent.parent
            config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
        self.config_path = config_path
        self.environment = environment
        self.logger = logger.get_logger(__name__)
        
        # Initialize sync engine with environment
        self.sync_engine = SyncEngine(config_path, environment=environment)
        
        self.logger.info(f"Ultra-lightweight sync CLI initialized (environment: {environment})")
    
    def sync_command(self, dry_run: bool = False, limit: Optional[int] = None, 
                     customer: Optional[str] = None, createitem_mode: str = 'batch',
                     skip_subitems: bool = False, retry_errors: bool = False,
                     generate_report: bool = False, sequential: bool = False) -> Dict[str, Any]:
        """
        Enhanced sync command with customer processing and retry functionality.
        
        Args:
            dry_run: If True, validate but don't execute
            limit: Optional limit on number of records to process
            customer: Optional customer filter (e.g., "GREYSON")
            createitem_mode: Item creation strategy ('single', 'batch', 'asyncBatch')
            skip_subitems: If True, skip subitem creation for faster sync (groups/items only)
            retry_errors: If True, retry failed records before processing new ones
            generate_report: If True, generate customer summary report after processing
            sequential: If True, process customers one at a time with isolated group creation
            
        Returns:
            Enhanced sync execution results including retry statistics and customer reports
        """
        self.logger.info(f"🚀 Starting Enhanced ORDER_LIST → Monday.com sync")
        self.logger.info(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
        self.logger.info(f"Item creation mode: {createitem_mode}")
        if skip_subitems:
            self.logger.info(f"⏭️ Subitem processing: SKIPPED (--skip-subitems flag)")
        if limit:
            self.logger.info(f"Limit: {limit} records")
        if customer:
            self.logger.info(f"Customer filter: {customer}")
        if retry_errors:
            self.logger.info(f"🔁 Retry errors: ENABLED")
        if generate_report:
            self.logger.info(f"📊 Generate report: ENABLED")
        
        try:
            # STEP 1: Run Enhanced Merge Orchestrator (data preparation + transformations)
            self.logger.info("🔧 STEP 1: Running Enhanced Merge Orchestrator...")
            from .merge_orchestrator import EnhancedMergeOrchestrator
            orchestrator = EnhancedMergeOrchestrator(self.sync_engine.config)
            
            # Execute complete enhanced merge sequence with transformations
            orchestrator_result = orchestrator.execute_enhanced_merge_sequence(dry_run=dry_run)
            
            if not orchestrator_result.get('success', False):
                return {
                    'success': False,
                    'error': f"Enhanced Merge Orchestrator failed: {orchestrator_result.get('error', 'Unknown error')}",
                    'orchestrator_result': orchestrator_result
                }
            
            self.logger.info(f"✅ Enhanced Merge Orchestrator completed successfully")
            
            # STEP 2: Execute enhanced sync using sync engine
            if sequential:
                self.logger.info("🚀 STEP 2: Running Enhanced Monday.com Sync (Sequential Mode - Per Customer)...")
                result = self.sync_engine.run_sync_per_customer_sequential(
                    dry_run=dry_run, 
                    limit=limit, 
                    createitem_mode=createitem_mode, 
                    skip_subitems=skip_subitems,
                    customer_name=customer,
                    retry_errors=retry_errors,
                    generate_report=generate_report
                )
            else:
                self.logger.info("🚀 STEP 2: Running Enhanced Monday.com Sync (Default Mode - Cross Customer)...")
                result = self.sync_engine.run_sync(
                    dry_run=dry_run, 
                    limit=limit, 
                    createitem_mode=createitem_mode, 
                    skip_subitems=skip_subitems,
                    customer_name=customer,
                    retry_errors=retry_errors,
                    generate_report=generate_report
                )
            
            # Enhanced results logging
            if result['success']:
                synced_count = result.get('total_synced', result.get('synced', 0))
                exec_time = result.get('execution_time_seconds', 0)
                self.logger.info(f"✅ Enhanced sync completed: {synced_count} records in {exec_time:.2f}s")
                
                # Log retry statistics if available
                if result.get('retry_results'):
                    retry_info = result['retry_results']
                    self.logger.info(f"🔁 Retry results: {retry_info.get('records_reset', 0)} records reset for retry")
                
                # Log customer report if generated
                if result.get('customer_report') and customer:
                    self.logger.info(f"📊 Customer report generated for {customer}")
                    # Save report to sync-specific folder (TASK027 Phase 1.3)
                    sync_folder = result.get('sync_folder')
                    self._save_customer_report(customer, result['customer_report'], sync_folder)
                
                # Log multiple customer reports if generated
                if result.get('customer_reports') and not customer:
                    customer_reports = result['customer_reports']
                    if customer_reports and 'error' not in customer_reports:
                        self.logger.info(f"📊 Customer reports generated for {len(customer_reports)} customers")
                        # Save each customer report to sync-specific folder (TASK027 Phase 1.3)
                        sync_folder = result.get('sync_folder')
                        for customer_name, report_content in customer_reports.items():
                            self._save_customer_report(customer_name, report_content, sync_folder)
                    else:
                        self.logger.warning(f"⚠️ Customer reports generation failed")
                
                # Get headers/lines synced from batch results if available
                total_headers = sum(batch.get('headers_synced', 0) for batch in result.get('batch_results', []))
                total_lines = sum(batch.get('lines_synced', 0) for batch in result.get('batch_results', []))
                self.logger.info(f"   Headers: {total_headers}, Lines: {total_lines}")
            else:
                self.logger.error(f"❌ Enhanced sync failed: {result.get('error', 'Unknown error')}")
            
            # Add orchestrator result to final result
            result['orchestrator_result'] = orchestrator_result
            
            return result
            
        except Exception as e:
            self.logger.exception(f"Sync command failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'records_processed': 0
            }
    
    def status_command(self) -> Dict[str, Any]:
        """
        Get sync status
        
        Returns:
            Current sync status
        """
        try:
            # For now, return basic status - could be enhanced with database queries
            return {
                'success': True,
                'status': 'ready',
                'config_path': self.config_path,
                'engine': 'ultra-lightweight'
            }
            
        except Exception as e:
            self.logger.exception(f"Status command failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _save_customer_report(self, customer_name: str, report_content: str, sync_folder: Optional[str] = None) -> None:
        """
        Save customer processing report to sync-specific folder (TASK027 Phase 1.3).
        
        Args:
            customer_name: Name of customer for report
            report_content: Markdown content of report  
            sync_folder: Optional sync session folder path for organized output
        """
        try:
            # TASK027 Phase 1.3: Use sync-based folder structure if available
            if sync_folder:
                reports_dir = Path(sync_folder) / "customer_reports"
                self.logger.info(f"📁 Using sync-based folder structure: {reports_dir}")
            else:
                # Fallback to legacy folder structure
                reports_dir = Path("reports/customer_processing")
                self.logger.info(f"📁 Using legacy folder structure: {reports_dir}")
            
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate timestamped filename
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{customer_name.replace(' ', '_').lower()}_{timestamp}.md"
            file_path = reports_dir / filename
            
            # Write report content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            self.logger.info(f"📄 Customer report saved: {file_path}")
            
        except Exception as e:
            self.logger.warning(f"Failed to save customer report: {e}")
    
    def retry_command(self, customer: Optional[str] = None, dry_run: bool = False, 
                     max_retries: int = 3, generate_report: bool = False) -> Dict[str, Any]:
        """
        Retry failed records command (Fix #3: Retry Functionality).
        
        Args:
            customer: Optional customer filter for retry
            dry_run: If True, show what would be retried without executing
            max_retries: Maximum retry attempts per record
            generate_report: If True, generate customer processing report after retry
            
        Returns:
            Retry processing results
        """
        self.logger.info(f"🔁 Starting retry processing for failed records")
        if customer:
            self.logger.info(f"Customer filter: {customer}")
        self.logger.info(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
        
        try:
            retry_results = self.sync_engine.retry_failed_records(
                customer_name=customer,
                max_retries=max_retries,
                dry_run=dry_run
            )
            
            if retry_results['success']:
                self.logger.info(f"✅ Retry processing completed")
                self.logger.info(f"   Records identified: {retry_results['records_identified']}")
                self.logger.info(f"   Records reset: {retry_results['records_reset']}")
                
                # Generate customer report if requested
                if generate_report and customer and not dry_run:
                    self.logger.info(f"📊 Generating customer processing report for {customer}...")
                    try:
                        report_content = self.sync_engine.generate_customer_processing_report(customer)
                        # TASK027 Phase 1: Use sync folder from retry results for organized output
                        sync_folder = retry_results.get('sync_folder')
                        self._save_customer_report(customer, report_content, sync_folder)
                        retry_results['customer_report'] = report_content
                        retry_results['report_generated'] = True
                        
                        if sync_folder:
                            self.logger.info(f"✅ Customer report generated and saved to sync folder: {sync_folder}")
                        else:
                            self.logger.info(f"✅ Customer report generated and saved for {customer}")
                    except Exception as e:
                        self.logger.warning(f"⚠️ Failed to generate customer report: {e}")
                        retry_results['report_generated'] = False
                        retry_results['report_error'] = str(e)
                elif generate_report and not customer:
                    self.logger.warning(f"⚠️ --generate-report requires --customer to be specified")
                    retry_results['report_generated'] = False
                    retry_results['report_error'] = "Customer name required for report generation"
                elif generate_report and dry_run:
                    self.logger.info(f"📊 Report generation skipped (dry run mode)")
                    retry_results['report_generated'] = False
                    retry_results['report_error'] = "Report generation skipped in dry run mode"
            else:
                self.logger.error(f"❌ Retry processing failed: {retry_results.get('error', 'Unknown error')}")
            
            return retry_results
            
        except Exception as e:
            self.logger.exception(f"Retry command failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'records_identified': 0,
                'records_reset': 0
            }
    
    def report_command(self, customer: str) -> Dict[str, Any]:
        """
        Generate customer processing report command (Fix #4: Customer Processing).
        
        Args:
            customer: Customer name to generate report for
            
        Returns:
            Report generation results
        """
        self.logger.info(f"📊 Generating customer processing report for {customer}")
        
        try:
            report_content = self.sync_engine.generate_customer_processing_report(customer)
            
            # Save report to file
            self._save_customer_report(customer, report_content)
            
            # Print report summary to console
            lines = report_content.split('\n')
            summary_lines = [line for line in lines[:20] if line.strip()]  # First 20 non-empty lines
            
            self.logger.info(f"📄 Report summary:")
            for line in summary_lines:
                if line.startswith('#'):
                    self.logger.info(f"   {line}")
                elif '|' in line and '-' not in line:  # Table rows, not separators
                    self.logger.info(f"   {line}")
            
            return {
                'success': True,
                'customer': customer,
                'report_generated': True,
                'report_content': report_content
            }
            
        except Exception as e:
            self.logger.exception(f"Report command failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'customer': customer,
                'report_generated': False
            }


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Ultra-Lightweight ORDER_LIST Monday.com Sync",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run sync (validate only) - development environment
  python -m src.pipelines.sync_order_list.cli sync --dry-run
  
  # Execute sync with limit in production environment
  python -m src.pipelines.sync_order_list.cli sync --execute --limit 100 --environment production
  
  # Execute full sync in production
  python -m src.pipelines.sync_order_list.cli sync --execute --environment production
  
  # Check status
  python -m src.pipelines.sync_order_list.cli status
        """
    )
    
    # Configuration arguments
    parser.add_argument(
        '--config', 
        type=str, 
        default=None,
        help='Path to TOML configuration file (defaults to configs/pipelines/sync_order_list.toml)'
    )
    
    parser.add_argument(
        '--environment', 
        type=str, 
        choices=['development', 'production'],
        default='production',
        help='Environment to use (development or production)'
    )
    
    # Output arguments
    parser.add_argument(
        '--output-json', 
        type=str,
        help='Save results to JSON file'
    )
    
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--quiet', 
        action='store_true',
        help='Suppress most output'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Execute sync operation')
    sync_group = sync_parser.add_mutually_exclusive_group(required=True)
    sync_group.add_argument('--dry-run', action='store_true', help='Validate but do not execute')
    sync_group.add_argument('--execute', action='store_true', help='Execute sync operations')
    
    sync_parser.add_argument('--limit', type=int, help='Limit number of records to process')
    sync_parser.add_argument('--customer', type=str, help='Filter by customer name (e.g., "GREYSON")')
    sync_parser.add_argument('--createitem', choices=['single', 'batch', 'asyncBatch'], 
                           default='batch', help='Item creation mode: single (one-by-one), batch (GraphQL batch), asyncBatch (high-performance async)')
    sync_parser.add_argument('--skip-subitems', action='store_true', 
                           help='Skip subitem creation for faster sync (groups/items only) - 3-5x performance improvement')
    sync_parser.add_argument('--retry-errors', action='store_true',
                           help='Retry failed records before processing new ones (Fix #3: Retry Functionality)')
    sync_parser.add_argument('--generate-report', action='store_true',
                           help='Generate customer summary report after processing (requires --customer)')
    sync_parser.add_argument('--sequential', action='store_true',
                           help='Process customers one at a time with isolated group creation (vs cross-customer batch mode)')
    
    # Retry command
    retry_parser = subparsers.add_parser('retry', help='Retry failed records')
    retry_group = retry_parser.add_mutually_exclusive_group(required=True)
    retry_group.add_argument('--dry-run', action='store_true', help='Show what would be retried')
    retry_group.add_argument('--execute', action='store_true', help='Execute retry operations')
    
    retry_parser.add_argument('--customer', type=str, help='Filter retry by customer name')
    retry_parser.add_argument('--max-retries', type=int, default=3, 
                            help='Maximum retry attempts per record (default: 3)')
    retry_parser.add_argument('--generate-report', action='store_true',
                            help='Generate customer processing report after retry operation')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate customer processing report')
    report_parser.add_argument('customer', type=str, help='Customer name to generate report for')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Get sync status')
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = 'DEBUG' if args.verbose else ('ERROR' if args.quiet else 'INFO')
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Check for command
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        # Initialize CLI
        cli = UltraLightweightSyncCLI(args.config, environment=args.environment)
        
        # Execute command
        if args.command == 'sync':
            dry_run = args.dry_run
            
            result = cli.sync_command(
                dry_run=dry_run,
                limit=args.limit,
                customer=args.customer,
                createitem_mode=args.createitem,
                skip_subitems=args.skip_subitems,
                retry_errors=args.retry_errors,
                generate_report=args.generate_report,
                sequential=args.sequential
            )
        elif args.command == 'retry':
            dry_run = args.dry_run
            result = cli.retry_command(
                customer=args.customer,
                dry_run=dry_run,
                max_retries=args.max_retries,
                generate_report=args.generate_report
            )
        elif args.command == 'report':
            result = cli.report_command(args.customer)
        elif args.command == 'status':
            result = cli.status_command()
        else:
            print(f"Unknown command: {args.command}")
            sys.exit(1)
        
        # Output results
        if args.output_json:
            with open(args.output_json, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            print(f"Results saved to {args.output_json}")
        
        if not args.quiet:
            _print_enhanced_sync_results(result, args)
            
        # Exit with appropriate code
        sys.exit(0 if result['success'] else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Operation interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _print_enhanced_sync_results(result, args):
    """Print comprehensive sync operation results with executive summary"""
    try:
        print("\n" + "="*60)
        print("🚀 SYNC OPERATION RESULTS - EXECUTIVE SUMMARY")
        print("="*60)
        
        # Overall Status
        success_icon = "✅" if result['success'] else "❌"
        print(f"📊 **Overall Status**: {success_icon} {'SUCCESS' if result['success'] else 'FAILED'}")
        print(f"🔧 **Command**: {args.command}")
        print(f"⚡ **Mode**: {'TRUE BATCH PROCESSING' if hasattr(args, 'createitem_mode') and args.createitem_mode == 'batch' else 'STANDARD'}")
        
        # Performance Metrics
        if 'execution_time_seconds' in result:
            exec_time = result['execution_time_seconds']
            print(f"⏱️  **Execution Time**: {exec_time:.2f}s")
            
        # TASK027 Phase 1: Display Sync ID and output organization
        if result.get('sync_id'):
            print(f"🆔 **Sync ID**: {result['sync_id']}")
            if result.get('sync_folder'):
                print(f"📁 **Output Folder**: {result['sync_folder']}")
                print(f"   📄 Reports: {result['sync_folder']}/customer_reports/")
                print(f"   📊 Summary: {result['sync_folder']}/_SYNC_SUMMARY.md")
        else:
            # Legacy fallback for compatibility
            import uuid
            sync_id = str(uuid.uuid4())[:8].upper()
            timestamp = result.get('sync_timestamp', 'UNKNOWN')
            print(f"🆔 **Sync ID**: SYNC-{sync_id}-{timestamp}")
        
        # Records Summary
        total_synced = result.get('total_synced', 0)
        if total_synced > 0:
            print(f"📈 **Records Processed**: {total_synced:,}")
            
            if 'execution_time_seconds' in result and result['execution_time_seconds'] > 0:
                throughput = total_synced / result['execution_time_seconds']
                print(f"🚄 **Throughput**: {throughput:.1f} records/second")
        
        # Batch Processing Summary
        if 'successful_batches' in result and 'batches_processed' in result:
            success_rate = (result['successful_batches'] / result['batches_processed']) * 100 if result['batches_processed'] > 0 else 0
            print(f"📦 **Batch Processing**: {result['successful_batches']}/{result['batches_processed']} batches ({success_rate:.1f}% success)")
        
        # Customer Summary - Enhanced with detailed breakdown
        if 'customer_summary' in result and result['customer_summary']:
            customer_summary = result['customer_summary']
            print(f"\n📋 **CUSTOMER BREAKDOWN**:")
            print(f"   👥 **Total Customers**: {customer_summary.get('total_customers', 0)}")
            print(f"   📊 **Total Records**: {customer_summary.get('total_records', 0):,}")
            print(f"   📁 **Groups Processed**: {customer_summary.get('total_groups', 0)}")
            print(f"   ✅ **Success Rate**: {customer_summary.get('success_rate', 0):.1f}%")
            
            # Individual customer details
            customers = customer_summary.get('customers', {})
            if customers:
                print(f"\n   � **Individual Customer Details**:")
                for customer_name, customer_data in customers.items():
                    records = customer_data.get('records_processed', 0)
                    groups = customer_data.get('groups', [])
                    print(f"      🏢 **{customer_name}**: {records:,} records")
                    if groups:
                        group_list = ', '.join(groups)
                        print(f"         📂 Groups: {group_list}")
            
            # Group summary
            group_summary = customer_summary.get('group_summary', [])
            if group_summary:
                print(f"\n   �️  **Group Summary**: {', '.join(group_summary)}")
        
        # Error Summary
        if not result['success'] and 'error' in result:
            print(f"\n❌ **ERROR DETAILS**:")
            print(f"   🚨 {result['error']}")
            
        # Report Generation Status
        if result.get('customer_report') or result.get('customer_reports'):
            print(f"\n📊 **REPORTS GENERATED**:")
            if result.get('customer_report'):
                print(f"   📄 Customer Report: Available")
            if result.get('customer_reports'):
                report_count = len(result['customer_reports'])
                print(f"   📄 All Customer Reports: {report_count} reports generated")
        
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error displaying results: {e}")
        print(f"Raw result data: {result}")


if __name__ == "__main__":
    main()
