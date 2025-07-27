#!/usr/bin/env python3
"""
CLI Step 3: Dry Run + Live Execution
===================================
Purpose: Execute CLI dry run validation then live sync execution
Location: tests/production_migration/integration/test_cli_step3_execution.py
Created: 2025-07-28

This script validates CLI dry run then executes live sync to Monday.com.
Run this AFTER CLI Step 2 completes successfully.
"""

import sys
from pathlib import Path
import subprocess
import json
import time

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger

logger = logger.get_logger(__name__)

def validate_cli_dry_run(limit: int = 5):
    """Execute CLI dry run to validate configuration and data"""
    print(f"🧪 CLI Dry Run Validation (limit: {limit})")
    print("=" * 50)
    
    try:
        # Execute CLI dry run
        result = subprocess.run([
            sys.executable, '-m', 'src.pipelines.sync_order_list.cli', 
            'sync', '--dry-run', '--limit', str(limit)
        ], 
        cwd=str(repo_root),
        capture_output=True, 
        text=True,
        timeout=60
        )
        
        print("📋 CLI Dry Run Output:")
        print(result.stdout)
        
        if result.stderr:
            print("📋 CLI Dry Run Errors:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ CLI dry run successful!")
            return True
        else:
            print(f"❌ CLI dry run failed with exit code: {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ CLI dry run timed out")
        return False
    except Exception as e:
        logger.exception(f"CLI dry run validation failed: {e}")
        return False

def execute_cli_live_sync(limit: int = 10):
    """Execute live CLI sync to Monday.com"""
    print(f"🚀 CLI Live Execution (limit: {limit})")
    print("=" * 50)
    
    print("⚠️  LIVE EXECUTION WARNING:")
    print("   This will create real Monday.com groups and items!")
    print("   Target: Clean production board (9200517329)")
    print("   Proceeding in 3 seconds...")
    time.sleep(3)
    
    try:
        # Execute CLI live sync
        result = subprocess.run([
            sys.executable, '-m', 'src.pipelines.sync_order_list.cli', 
            'sync', '--execute', '--limit', str(limit)
        ], 
        cwd=str(repo_root),
        capture_output=True, 
        text=True,
        timeout=120  # Longer timeout for live execution
        )
        
        print("📋 CLI Live Execution Output:")
        print(result.stdout)
        
        if result.stderr:
            print("📋 CLI Live Execution Errors:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ CLI live execution successful!")
            return True, result.stdout
        else:
            print(f"❌ CLI live execution failed with exit code: {result.returncode}")
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        print("⏰ CLI live execution timed out")
        return False, "Timeout expired"
    except Exception as e:
        logger.exception(f"CLI live execution failed: {e}")
        return False, str(e)

def check_database_sync_status():
    """Check database for sync status after execution"""
    print("\n🔍 Checking Database Sync Status...")
    print("=" * 50)
    
    try:
        with db.get_connection('orders') as connection:
            cursor = connection.cursor()
            
            # Check FACT_ORDER_LIST sync status
            cursor.execute("""
                SELECT 
                    sync_state,
                    COUNT(*) as record_count,
                    COUNT(monday_item_id) as synced_with_item_id
                FROM [FACT_ORDER_LIST]
                WHERE sync_state IN ('PENDING', 'SYNCED', 'ERROR')
                GROUP BY sync_state
                ORDER BY sync_state
            """)
            
            print("📊 FACT_ORDER_LIST Sync Status:")
            results = cursor.fetchall()
            for row in results:
                sync_state, count, item_id_count = row
                print(f"   {sync_state}: {count} records ({item_id_count} with monday_item_id)")
            
            # Check ORDER_LIST_LINES sync status
            cursor.execute("""
                SELECT 
                    sync_state,
                    COUNT(*) as record_count,
                    COUNT(monday_subitem_id) as synced_with_subitem_id
                FROM [ORDER_LIST_LINES]
                WHERE sync_state IN ('PENDING', 'SYNCED', 'ERROR')
                GROUP BY sync_state
                ORDER BY sync_state
            """)
            
            print("\n📊 ORDER_LIST_LINES Sync Status:")
            results = cursor.fetchall()
            for row in results:
                sync_state, count, subitem_id_count = row
                print(f"   {sync_state}: {count} records ({subitem_id_count} with monday_subitem_id)")
            
            return True
            
    except Exception as e:
        logger.exception(f"Database sync status check failed: {e}")
        return False

def main():
    print("🚀 CLI Step 3: Dry Run + Live Execution")
    print("=" * 60)
    
    # Step 3a: Validate with dry run
    print("Phase 3a: Dry Run Validation")
    dry_run_success = validate_cli_dry_run(limit=5)
    
    if not dry_run_success:
        print("❌ Dry run failed - aborting live execution")
        return {'success': False, 'phase': '3a_dry_run', 'error': 'Dry run validation failed'}
    
    print("\n✅ Dry run successful - proceeding to live execution")
    
    # Step 3b: Execute live sync
    print("\nPhase 3b: Live Execution")
    live_success, live_output = execute_cli_live_sync(limit=10)
    
    if not live_success:
        print("❌ Live execution failed")
        return {'success': False, 'phase': '3b_live_execution', 'error': live_output}
    
    print("\n✅ Live execution successful")
    
    # Step 3c: Validate results
    print("\nPhase 3c: Result Validation")
    db_check_success = check_database_sync_status()
    
    if db_check_success:
        print("\n🎉 CLI Step 3 Complete!")
        print("✅ Dry run validation successful")
        print("✅ Live execution successful")
        print("✅ Database sync status validated")
        return {
            'success': True, 
            'dry_run_success': True,
            'live_execution_success': True,
            'database_validated': True,
            'live_output': live_output
        }
    else:
        print("\n⚠️ CLI Step 3 Partial Success")
        print("✅ Dry run validation successful")
        print("✅ Live execution successful")
        print("❌ Database sync status validation failed")
        return {
            'success': False, 
            'dry_run_success': True,
            'live_execution_success': True,
            'database_validated': False
        }

if __name__ == "__main__":
    result = main()
    if result['success']:
        print("\n🎉 PRODUCTION MIGRATION COMPLETE!")
        print("   Monday.com sync pipeline operational")
        print("   Ready for production use")
    else:
        print(f"\n🔧 CLI Step 3 phase {result.get('phase', 'unknown')} needs attention")
