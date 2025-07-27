#!/usr/bin/env python3
"""
Test API Archiver Integration - Verify archiver integration with sync engine
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.sync_engine import SyncEngine

logger = logger.get_logger(__name__)

def main():
    print("🧪 Testing API Archiver Integration...")
    
    # Config
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Check current state BEFORE sync
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Count records before
        cursor.execute("SELECT COUNT(*) FROM FACT_ORDER_LIST")
        headers_before = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ORDER_LIST_LINES") 
        lines_before = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ORDER_LIST_API_LOG")
        api_log_before = cursor.fetchone()[0]
        
        print(f"📊 BEFORE Sync:")
        print(f"  FACT_ORDER_LIST: {headers_before} records")
        print(f"  ORDER_LIST_LINES: {lines_before} records") 
        print(f"  ORDER_LIST_API_LOG: {api_log_before} records")
        
        cursor.close()
    
    # Run small sync with archiver integration
    print("\n🚀 Running sync with API archiver integration...")
    engine = SyncEngine(config_path, environment="development")
    result = engine.run_sync(dry_run=False, limit=3)
    
    print(f"\n📈 Sync Result:")
    print(f"  Success: {result.get('success')}")
    print(f"  Records Synced: {result.get('total_synced')}")
    print(f"  API Archival: {result.get('api_archival', 'Not Available')}")
    
    # Check state AFTER sync
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM FACT_ORDER_LIST")
        headers_after = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ORDER_LIST_LINES")
        lines_after = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ORDER_LIST_API_LOG")
        api_log_after = cursor.fetchone()[0]
        
        print(f"\n📊 AFTER Sync:")
        print(f"  FACT_ORDER_LIST: {headers_after} records (Δ +{headers_after - headers_before})")
        print(f"  ORDER_LIST_LINES: {lines_after} records (Δ +{lines_after - lines_before})")
        print(f"  ORDER_LIST_API_LOG: {api_log_after} records (Δ +{api_log_after - api_log_before})")
        
        # Test PASSED if API_LOG increased
        if api_log_after > api_log_before:
            print("\n✅ API ARCHIVER INTEGRATION SUCCESS!")
            print(f"   🎯 {api_log_after - api_log_before} records archived to ORDER_LIST_API_LOG")
        else:
            print("\n❌ API ARCHIVER INTEGRATION FAILED!")
            print("   📝 No records were archived to ORDER_LIST_API_LOG")
        
        cursor.close()

if __name__ == "__main__":
    main()
