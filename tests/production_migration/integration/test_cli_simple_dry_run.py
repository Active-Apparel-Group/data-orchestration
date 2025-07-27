#!/usr/bin/env python3
"""
Simple CLI Dry Run Test
======================
Purpose: Run CLI dry run to check group_name transformation
Location: tests/production_migration/integration/test_cli_simple_dry_run.py
Created: 2025-07-29

This will use the CLI directly to run a dry run and see group names.
"""

import sys
from pathlib import Path
import subprocess

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger

logger = logger.get_logger(__name__)

def check_pending_data():
    """Check what PENDING data we have"""
    print("📋 Checking PENDING GREYSON Data")
    print("=" * 40)
    
    try:
        with db.get_connection('orders') as connection:
            cursor = connection.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_pending,
                    [CUSTOMER NAME],
                    [PO NUMBER]
                FROM [FACT_ORDER_LIST]
                WHERE [CUSTOMER NAME] LIKE 'GREYSON%' 
                  AND [PO NUMBER] = '4755'
                  AND [sync_state] = 'PENDING'
                GROUP BY [CUSTOMER NAME], [PO NUMBER]
            """)
            
            results = cursor.fetchall()
            
            for count, customer, po in results:
                print(f"✅ {count} PENDING records: {customer} PO {po}")
                
            if not results:
                print("❌ No PENDING records found!")
                return False
                
            return True
            
    except Exception as e:
        logger.exception(f"Failed to check pending data: {e}")
        return False

def run_cli_dry_run():
    """Run CLI dry run using subprocess"""
    print("\n🧪 Running CLI Dry Run via Subprocess")
    print("=" * 45)
    
    try:
        # Use python -m to run the CLI module
        cmd = [
            sys.executable, '-m', 'src.pipelines.sync_order_list.cli', 
            'sync', '--dry-run', '--limit', '3'
        ]
        
        print(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print(f"Return code: {result.returncode}")
        
        if result.stdout:
            print("📤 STDOUT:")
            print(result.stdout)
            
        if result.stderr:
            print("📥 STDERR:")
            print(result.stderr)
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ CLI command timed out")
        return False
    except Exception as e:
        logger.exception(f"CLI execution failed: {e}")
        return False

def main():
    print("🚀 Simple CLI Dry Run Test")
    print("=" * 35)
    
    # Check we have pending data
    has_data = check_pending_data()
    if not has_data:
        print("❌ No PENDING data found - run test_set_greyson_pending.py first")
        return {'success': False, 'error': 'No pending data'}
    
    # Run the CLI dry run
    cli_success = run_cli_dry_run()
    
    print("\n📋 Summary:")
    if cli_success:
        print("✅ CLI dry run completed successfully")
        print("🔍 Check the output above for group_name issues")
    else:
        print("❌ CLI dry run failed")
    
    return {'success': cli_success}

if __name__ == "__main__":
    result = main()
    if result['success']:
        print("\n🎯 Dry run complete - review group names in output")
    else:
        print("\n🔧 CLI dry run failed")
