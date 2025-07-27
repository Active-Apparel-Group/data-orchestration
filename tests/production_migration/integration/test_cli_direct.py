#!/usr/bin/env python3
"""
CLI Direct Test - Quick CLI Validation
=====================================
Purpose: Test CLI directly with correct path resolution
Location: tests/production_migration/integration/test_cli_direct.py
Created: 2025-07-29

Bypass path resolution issues by testing CLI components directly.
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

def test_sync_engine_direct():
    """Test SyncEngine directly with absolute path"""
    print("🧪 Testing SyncEngine Direct Initialization")
    print("=" * 50)
    
    try:
        # Use absolute path to config
        config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
        print(f"Config path: {config_path}")
        
        # Test SyncEngine initialization
        engine = SyncEngine(config_path)
        print("✅ SyncEngine initialized successfully!")
        
        # Test sync status check
        print("\n🔍 Testing sync status...")
        
        # Check for pending records
        pending_headers = engine._get_pending_headers(limit=5, action_types=['INSERT'])
        print(f"📊 Found {len(pending_headers)} pending headers for sync")
        
        if pending_headers:
            print("📋 Sample pending header:")
            header = pending_headers[0]
            print(f"   AAG ORDER NUMBER: {header.get('AAG ORDER NUMBER', 'N/A')}")
            print(f"   CUSTOMER NAME: {header.get('CUSTOMER NAME', 'N/A')}")
            print(f"   PO NUMBER: {header.get('PO NUMBER', 'N/A')}")
            print(f"   sync_state: {header.get('sync_state', 'N/A')}")
            print(f"   record_uuid: {header.get('record_uuid', 'N/A')}")
        
        return True, len(pending_headers)
        
    except Exception as e:
        logger.exception(f"SyncEngine direct test failed: {e}")
        return False, str(e)

def test_dry_run_direct():
    """Test dry run execution directly"""
    print("\n🧪 Testing Dry Run Direct Execution")
    print("=" * 50)
    
    try:
        # Use absolute path to config
        config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
        
        # Initialize engine
        engine = SyncEngine(config_path)
        
        # Execute dry run
        result = engine.run_sync(dry_run=True, limit=3, action_types=['INSERT'])
        
        print("📋 Dry Run Results:")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Total synced: {result.get('total_synced', 0)}")
        print(f"   Execution time: {result.get('execution_time_seconds', 0):.2f}s")
        print(f"   Action types: {result.get('action_types', [])}")
        print(f"   Dry run: {result.get('dry_run', False)}")
        
        if 'error' in result:
            print(f"   Error: {result['error']}")
        
        return result.get('success', False), result
        
    except Exception as e:
        logger.exception(f"Dry run direct test failed: {e}")
        return False, str(e)

def main():
    print("🚀 CLI Direct Test - Bypass Path Issues")
    print("=" * 60)
    
    # Test 1: SyncEngine initialization
    engine_success, engine_result = test_sync_engine_direct()
    
    if not engine_success:
        print(f"❌ SyncEngine test failed: {engine_result}")
        return {'success': False, 'phase': 'engine_init', 'error': engine_result}
    
    print(f"✅ SyncEngine test successful - {engine_result} pending records found")
    
    # Test 2: Dry run execution
    dry_run_success, dry_run_result = test_dry_run_direct()
    
    if dry_run_success:
        print("\n🎉 CLI Direct Test Complete!")
        print("✅ SyncEngine initialization successful")
        print("✅ Dry run execution successful")
        return {
            'success': True,
            'engine_ready': True,
            'dry_run_success': True,
            'pending_records': engine_result,
            'dry_run_result': dry_run_result
        }
    else:
        print(f"\n⚠️ Dry run failed: {dry_run_result}")
        return {
            'success': False,
            'phase': 'dry_run',
            'engine_ready': True,
            'error': dry_run_result
        }

if __name__ == "__main__":
    result = main()
    if result['success']:
        print("\n🎯 Ready for live execution!")
    else:
        print(f"\n🔧 CLI direct test phase {result.get('phase', 'unknown')} needs attention")
