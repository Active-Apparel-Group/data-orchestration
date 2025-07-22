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
    
    def __init__(self, config_path: str = "configs/pipelines/sync_order_list.toml"):
        """
        Initialize CLI with TOML configuration
        
        Args:
            config_path: Path to sync_order_list.toml configuration
        """
        self.config_path = config_path
        self.logger = logger.get_logger(__name__)
        
        # Initialize sync engine
        self.sync_engine = SyncEngine(config_path)
        
        self.logger.info(f"Ultra-lightweight sync CLI initialized")
    
    def sync_command(self, dry_run: bool = False, limit: Optional[int] = None, 
                     customer: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute sync command
        
        Args:
            dry_run: If True, validate but don't execute
            limit: Optional limit on number of records to process
            customer: Optional customer filter
            
        Returns:
            Sync execution results
        """
        self.logger.info(f"🚀 Starting ORDER_LIST → Monday.com sync")
        self.logger.info(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
        if limit:
            self.logger.info(f"Limit: {limit} records")
        if customer:
            self.logger.info(f"Customer filter: {customer}")
        
        try:
            # Execute sync using sync engine
            result = self.sync_engine.run_sync(dry_run=dry_run, limit=limit)
            
            # Log results
            if result['success']:
                self.logger.info(f"✅ Sync completed: {result['total_synced']} records in {result['execution_time_seconds']:.2f}s")
                self.logger.info(f"   Headers: {result['headers'].get('synced', 0)}, Lines: {result['lines'].get('synced', 0)}")
            else:
                self.logger.error(f"❌ Sync failed: {result.get('error', 'Unknown error')}")
            
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


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Ultra-Lightweight ORDER_LIST Monday.com Sync",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run sync (validate only)
  python -m src.pipelines.sync_order_list.cli sync --dry-run
  
  # Execute sync with limit
  python -m src.pipelines.sync_order_list.cli sync --execute --limit 100
  
  # Execute full sync
  python -m src.pipelines.sync_order_list.cli sync --execute
  
  # Check status
  python -m src.pipelines.sync_order_list.cli status
        """
    )
    
    # Configuration arguments
    parser.add_argument(
        '--config', 
        type=str, 
        default='configs/pipelines/sync_order_list.toml',
        help='Path to TOML configuration file'
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
    sync_parser.add_argument('--customer', type=str, help='Filter by customer name')
    
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
        cli = UltraLightweightSyncCLI(args.config)
        
        # Execute command
        if args.command == 'sync':
            dry_run = args.dry_run
            result = cli.sync_command(
                dry_run=dry_run,
                limit=args.limit,
                customer=args.customer
            )
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
            print("\n" + "="*50)
            print("SYNC OPERATION RESULTS")
            print("="*50)
            print(f"Success: {'✅ Yes' if result['success'] else '❌ No'}")
            print(f"Command: {args.command}")
            
            if 'records_processed' in result:
                print(f"Records processed: {result['records_processed']}")
            
            if 'execution_time_seconds' in result:
                print(f"Execution time: {result['execution_time_seconds']:.2f}s")
            
            if not result['success'] and 'error' in result:
                print(f"Error: {result['error']}")
        
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
        sys.exit(3)


if __name__ == "__main__":
    main()
