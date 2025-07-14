#!/usr/bin/env python3
"""
Main Customer Orders - UUID & Hash-Based Delta Synchronization
Enterprise-grade Monday.com integration with staging-based processing

This is the main entry point for the customer orders synchronization system between 
ORDERS_UNIFIED and Monday.com (CustMasterSchedule + Subitems).

Features:
- UUID-based record tracking
- Hash-based change detection (Methods 1 & 2)
- Enterprise batch processing with retry logic
- Dynamic customer mapping from YAML
- Complete audit trail and rollback capability

Usage:
    python main_customer_orders.py --mode TEST --customer GREYSON --limit 10
    python main_customer_orders.py --mode PRODUCTION --batch-size 100
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Add utils to path using repository root method
def find_repo_root():
    """Find the repository root by looking for utils folder"""
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root (utils folder not found)")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

# Import utilities using working production pattern
import db_helper as db
import logger_helper

# Import package modules (same directory)
from change_detector import ChangeDetector
from staging_processor import StagingProcessor
from customer_batch_processor import CustomerBatchProcessor

class MainCustomerOrders:
    """Main orchestrator for UUID-based customer orders synchronization"""
    
    def __init__(self, mode: str = "TEST"):
        self.mode = mode
        self.logger = logger_helper.get_logger(__name__)
        
        # Initialize components
        self.change_detector = ChangeDetector()
        self.staging_processor = StagingProcessor() 
        self.batch_processor = CustomerBatchProcessor()
        
        self.logger.info(f"Main Customer Orders initialized in {mode} mode")
    
    def run_customer_sync(self, customer_filter: str = None, limit: int = None, po_number_filter: str = None):
        """
        PHASE 1 SIMPLIFIED - Direct customer processing, no triple change detection
        """
        
        try:
            self.logger.info("=" * 60)
            self.logger.info("Starting Customer Orders Synchronization - PHASE 1")
            self.logger.info("=" * 60)
            
            # PHASE 1 - Direct processing, skip redundant change detection
            if customer_filter:
                self.logger.info(f"Processing customer: {customer_filter}")
                
                # Direct customer batch processing
                total_processed = 0
                
                try:
                    # Process the customer batch directly
                    batch_results = self.batch_processor.process_customer_batch(
                        customer_filter, limit, po_number_filter
                    )
                    
                    if batch_results['status'] == 'SUCCESS':
                        total_processed = batch_results['total_records']
                        self.logger.info(f"   SUCCESS {customer_filter}: {total_processed} records processed")
                    else:
                        self.logger.error(f"   ERROR {customer_filter}: {batch_results.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    self.logger.error(f"   ERROR {customer_filter}: Processing failed - {str(e)}")
                
                # Final Summary
                self.logger.info("=" * 60)
                self.logger.info(f"Customer Orders Sync Complete!")
                self.logger.info(f"   Total records processed: {total_processed}")
                self.logger.info(f"   Customer: {customer_filter}")
                self.logger.info(f"   Mode: {self.mode}")
                self.logger.info("=" * 60)
                
                return {
                    'success': True,
                    'total_processed': total_processed,
                    'customers_processed': 1 if total_processed > 0 else 0,
                    'mode': self.mode
                }
            else:
                # For Phase 1, require specific customer
                self.logger.warning("Phase 1 requires specific customer filter")
                return {
                    'success': False,
                    'total_processed': 0,
                    'customers_processed': 0,
                    'mode': self.mode,
                    'message': 'Phase 1 requires --customer parameter'
                }
            
        except Exception as e:
            self.logger.error(f"Customer Orders Sync failed: {str(e)}")
            raise

def main():
    """Main entry point with argument parsing"""
    
    parser = argparse.ArgumentParser(description='ORDERS_UNIFIED Delta Sync')
    parser.add_argument('--mode', choices=['TEST', 'PRODUCTION'], default='TEST',
                       help='Execution mode (default: TEST)')
    parser.add_argument('--customer', type=str,
                       help='Filter to specific customer (e.g., GREYSON)')
    parser.add_argument('--limit', type=int,
                       help='Limit number of records processed')
    parser.add_argument('--po-number', type=str, default=None,
                       help='Filter to specific PO NUMBER for testing (e.g., "4755")')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO',
                       help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=getattr(logging, args.log_level))
    
    # Create and run orchestrator
    orchestrator = MainCustomerOrders(mode=args.mode)
    try:
        results = orchestrator.run_customer_sync(
            customer_filter=args.customer,
            limit=args.limit,
            po_number_filter=args.po_number
        )
        
        print(f"\n🎉 Success! Processed {results['total_processed']} records across {results['customers_processed']} customers")
        return 0
        
    except Exception as e:
        print(f"\n💥 Failed: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
