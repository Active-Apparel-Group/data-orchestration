#!/usr/bin/env python3
"""
Test Direct API Archiver - Test archiver on existing successful sync data
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.api_logging_archiver import APILoggingArchiver

logger = logger.get_logger(__name__)

def main():
    print("🧪 Testing Direct API Archiver on Existing Data...")
    
    # Config
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Check current state 
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Count records with API logging data
        cursor.execute("""
            SELECT COUNT(*) 
            FROM FACT_ORDER_LIST 
            WHERE [sync_state] = 'COMPLETED' 
              AND [monday_item_id] IS NOT NULL
        """)
        completed_headers = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM ORDER_LIST_LINES 
            WHERE [sync_state] = 'COMPLETED' 
              AND [monday_subitem_id] IS NOT NULL
        """)
        completed_lines = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ORDER_LIST_API_LOG")
        api_log_before = cursor.fetchone()[0]
        
        print(f"📊 Current Data State:")
        print(f"  COMPLETED Headers: {completed_headers} records")
        print(f"  COMPLETED Lines: {completed_lines} records") 
        print(f"  ORDER_LIST_API_LOG: {api_log_before} records")
        
        # Test the archiver directly
        print("\n🗄️ Running API archiver on existing data...")
        archiver = APILoggingArchiver(config)
        
        # First dry run
        print("🔍 Dry run test...")
        dry_stats = archiver.archive_api_logging_data(cursor, dry_run=True)
        print(f"  Would archive: {dry_stats['total_archived']} total records")
        print(f"  Headers: {dry_stats['headers_archived']}, Lines: {dry_stats['lines_archived']}")
        
        # Real run if dry run found data
        if dry_stats['total_archived'] > 0:
            print("\n🚀 Executing real archival...")
            real_stats = archiver.archive_api_logging_data(cursor, dry_run=False)
            connection.commit()
            
            print(f"✅ Archival completed:")
            print(f"  Pipeline Run ID: {real_stats['pipeline_run_id']}")
            print(f"  Total archived: {real_stats['total_archived']} records")
            print(f"  Headers: {real_stats['headers_archived']}")
            print(f"  Lines: {real_stats['lines_archived']}")
            
            # Check final state
            cursor.execute("SELECT COUNT(*) FROM ORDER_LIST_API_LOG")
            api_log_after = cursor.fetchone()[0]
            
            print(f"\n📊 AFTER Archival:")
            print(f"  ORDER_LIST_API_LOG: {api_log_after} records (Δ +{api_log_after - api_log_before})")
            
            if api_log_after > api_log_before:
                print("\n🎯 SUCCESS: API archiver is working correctly!")
                print("   📝 The issue was missing integration, not broken archiver")
            else:
                print("\n❌ ISSUE: Archiver ran but no data was archived")
        else:
            print("\n⚠️ No data found to archive - may need successful sync operations first")
            
        cursor.close()

if __name__ == "__main__":
    main()
