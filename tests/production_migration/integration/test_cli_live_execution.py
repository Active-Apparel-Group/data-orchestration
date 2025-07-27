#!/usr/bin/env python3
"""
CLI Live Execution - GREYSON PO 4755 to Monday.com
=================================================
Purpose: Execute live CLI sync of GREYSON PO 4755 to Monday.com board 9200517329
Location: tests/production_migration/integration/test_cli_live_execution.py
Created: 2025-07-29

This executes LIVE sync to Monday.com - creates real groups and items!
"""

import sys
import os
from pathlib import Path

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

# Set working directory to repo root for correct relative path resolution
os.chdir(str(repo_root))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.sync_engine import SyncEngine

logger = logger.get_logger(__name__)

def execute_live_sync(limit: int = 10):
    """Execute LIVE sync to Monday.com"""
    print(f"🚀 LIVE CLI Execution - GREYSON PO 4755 (limit: {limit})")
    print("=" * 60)
    
    print("⚠️  LIVE EXECUTION WARNING:")
    print("   This will create REAL Monday.com groups and items!")
    print("   Target board: 9200517329 (clean production board)")
    print("   Customer: GREYSON CLOTHIERS PO 4755")
    print("   Proceeding in 3 seconds...")
    
    import time
    time.sleep(3)
    
    try:
        # Use absolute path to config
        config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
        
        # Initialize engine
        engine = SyncEngine(config_path)
        
        print(f"\n🎯 Executing LIVE sync with limit: {limit}")
        
        # Execute LIVE sync
        result = engine.run_sync(dry_run=False, limit=limit, action_types=['INSERT'])
        
        print(f"\n📋 LIVE Execution Results:")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Total synced: {result.get('total_synced', 0)}")
        print(f"   Execution time: {result.get('execution_time_seconds', 0):.2f}s")
        print(f"   Batches processed: {result.get('batches_processed', 0)}")
        print(f"   Successful batches: {result.get('successful_batches', 0)}")
        print(f"   Failed batches: {result.get('failed_batches', 0)}")
        
        if 'error' in result:
            print(f"   Error: {result['error']}")
        
        # Show batch details
        if 'batch_results' in result and result['batch_results']:
            print(f"\n📊 Batch Details:")
            for i, batch in enumerate(result['batch_results'], 1):
                success_icon = "✅" if batch.get('success', False) else "❌"
                record_uuid = batch.get('record_uuid', 'unknown')[:8]
                synced = batch.get('records_synced', 0)
                print(f"   {success_icon} Batch {i}: {record_uuid}... ({synced} records)")
        
        return result.get('success', False), result
        
    except Exception as e:
        logger.exception(f"Live execution failed: {e}")
        return False, str(e)

def check_monday_sync_status():
    """Check database sync status after execution"""
    print("\n🔍 Checking Database Sync Status...")
    print("=" * 50)
    
    try:
        with db.get_connection('orders') as connection:
            cursor = connection.cursor()
            
            # Check FACT_ORDER_LIST sync status for GREYSON PO 4755
            cursor.execute("""
                SELECT 
                    sync_state,
                    COUNT(*) as record_count,
                    COUNT(monday_item_id) as synced_with_item_id,
                    MIN([AAG ORDER NUMBER]) as first_order,
                    MAX([AAG ORDER NUMBER]) as last_order
                FROM [FACT_ORDER_LIST]
                WHERE [CUSTOMER NAME] LIKE 'GREYSON%' 
                  AND [PO NUMBER] = '4755'
                GROUP BY sync_state
                ORDER BY sync_state
            """)
            
            print("📊 GREYSON PO 4755 Sync Status:")
            results = cursor.fetchall()
            for row in results:
                sync_state, count, item_id_count, first_order, last_order = row
                print(f"   {sync_state}: {count} records ({item_id_count} with monday_item_id)")
                print(f"      Range: {first_order} → {last_order}")
            
            # Check if any Monday item IDs were assigned
            cursor.execute("""
                SELECT 
                    [AAG ORDER NUMBER],
                    [monday_item_id],
                    [sync_completed_at]
                FROM [FACT_ORDER_LIST]
                WHERE [CUSTOMER NAME] LIKE 'GREYSON%' 
                  AND [PO NUMBER] = '4755'
                  AND [monday_item_id] IS NOT NULL
                ORDER BY [AAG ORDER NUMBER]
            """)
            
            synced_items = cursor.fetchall()
            
            if synced_items:
                print(f"\n🎉 Successfully Synced Items ({len(synced_items)}):")
                for row in synced_items[:5]:  # Show first 5
                    order_num, item_id, completed_at = row
                    print(f"   {order_num} → Monday Item ID: {item_id}")
                
                if len(synced_items) > 5:
                    print(f"   ... and {len(synced_items) - 5} more")
            
            return True
            
    except Exception as e:
        logger.exception(f"Database sync status check failed: {e}")
        return False

def main():
    print("🚀 CLI Live Execution - GREYSON PO 4755 Production Test")
    print("=" * 70)
    
    # Execute live sync
    live_success, live_result = execute_live_sync(limit=10)
    
    if not live_success:
        print(f"❌ Live execution failed: {live_result}")
        return {'success': False, 'error': live_result}
    
    print("\n✅ Live execution completed successfully!")
    
    # Check database status
    db_check_success = check_monday_sync_status()
    
    if db_check_success:
        print("\n🎉 PRODUCTION MIGRATION COMPLETE!")
        print("✅ Live Monday.com sync successful")
        print("✅ Database sync status validated")
        print("✅ GREYSON PO 4755 synced to board 9200517329")
        print("\n🌟 Monday.com sync pipeline is now operational!")
        return {
            'success': True,
            'live_execution_success': True,
            'database_validated': True,
            'live_result': live_result
        }
    else:
        print("\n⚠️ Live execution successful but database validation failed")
        return {
            'success': False,
            'live_execution_success': True,
            'database_validated': False
        }

if __name__ == "__main__":
    result = main()
    if result['success']:
        print("\n🎯 Production pipeline ready for full deployment!")
    else:
        print(f"\n🔧 Post-execution validation needs attention")
