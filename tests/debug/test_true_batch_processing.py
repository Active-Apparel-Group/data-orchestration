#!/usr/bin/env python3
"""
TRUE BATCH PROCESSING TEST
========================
Test the new true batch processing implementation that processes multiple record_uuids
in a single Monday.com API call instead of 1 record_uuid per API call.

Expected Results:
- 10 records should be processed in 2 batches of 5 records each
- Each batch should have 1 Monday.com API call (instead of 5 separate calls)
- Detailed logging showing record_uuid to monday_item_id mapping
- Complete audit trail from API to database
"""

import sys
from pathlib import Path
from datetime import datetime

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.sync_engine import SyncEngine

logger = logger.get_logger(__name__)

def main():
    print("🧪 TRUE BATCH PROCESSING TEST...")
    
    # Initialize logging to file
    log_filename = f"logs/true_batch_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    print(f"📄 Detailed logging: {log_filename}")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path, environment="production")
    
    # Verify batch configuration
    print(f"🔧 Configuration:")
    print(f"   item_batch_size: {config.item_batch_size}")
    print(f"   group_batch_size: {config.group_batch_size}")
    print(f"   delay_between_batches: {config.delay_between_batches}")
    print(f"   max_concurrent_batches: {config.max_concurrent_batches}")
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Initialize sync engine
        sync_engine = SyncEngine(config_path, environment="production")
        
        print("\n🎯 TESTING TRUE BATCH PROCESSING:")
        print("=" * 60)
        
        # Test with exactly 10 records to create 2 batches of 5
        test_result = sync_engine.run_sync(
            limit=10,                    # Exactly 10 records
            dry_run=False,               # LIVE execution
            createitem_mode='batch',     # Force batch mode
            skip_subitems=True,          # Skip subitems as requested
            customer_name="BORN PRIMITIVE"  # Single customer for consistency
        )
        
        print("\n📊 BATCH PROCESSING RESULTS:")
        print("=" * 60)
        print(f"Success: {test_result.get('success')}")
        print(f"Total Synced: {test_result.get('total_synced')}")
        print(f"Successful Batches: {test_result.get('successful_batches', 0)}/{test_result.get('total_batches', 0)}")
        print(f"Execution Time: {test_result.get('sync_duration', 0):.2f}s")
        
        if 'performance_summary' in test_result:
            perf = test_result['performance_summary']
            print(f"Records/Second: {perf.get('records_per_second', 0):.1f}")
            print(f"Monday.com Operations: {perf.get('monday_operations_time', 0):.3f}s")
        
        print(f"\n📄 Complete log file: {log_filename}")
        
        cursor.close()

if __name__ == "__main__":
    main()
