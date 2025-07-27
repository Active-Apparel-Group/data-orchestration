#!/usr/bin/env python3
"""
Test API Logging Archiver Fix - Verify archival process works correctly

This test validates that the APILoggingArchiver fixes are working properly:
1. Fix #1: Corrected column names in archive queries
2. Verify archival extracts data from FACT_ORDER_LIST to ORDER_LIST_API_LOG  
3. Confirm archiver runs even with partial batch failures
"""

import sys
from pathlib import Path

# Standard import pattern for this project
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.api_logging_archiver import APILoggingArchiver

logger = logger.get_logger(__name__)

def main():
    print("🧪 TESTING API LOGGING ARCHIVER FIX")
    print("=" * 60)
    
    # Configuration
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # 1. Check current state BEFORE archival
        print("\n🔍 BEFORE ARCHIVAL - Current State:")
        
        cursor.execute("SELECT COUNT(*) FROM FACT_ORDER_LIST WHERE api_request_payload IS NOT NULL")
        fact_with_payload = cursor.fetchone()[0]
        print(f"   FACT_ORDER_LIST with payloads: {fact_with_payload:,}")
        
        cursor.execute("SELECT COUNT(*) FROM ORDER_LIST_API_LOG")
        current_api_log = cursor.fetchone()[0]
        print(f"   ORDER_LIST_API_LOG records: {current_api_log:,}")
        
        gap = fact_with_payload - current_api_log
        print(f"   Current gap: {gap:,} records")
        
        # 2. Test archiver in DRY RUN mode first
        print("\n🔍 TESTING ARCHIVER (DRY RUN):")
        archiver = APILoggingArchiver(config)
        
        try:
            dry_run_stats = archiver.archive_api_logging_data(cursor, dry_run=True)
            print(f"   Would archive: {dry_run_stats['total_archived']} records")
            print(f"   Headers: {dry_run_stats['headers_archived']}")
            print(f"   Lines: {dry_run_stats['lines_archived']}")
        except Exception as e:
            print(f"   ❌ Dry run failed: {e}")
        
        # 3. Test actual archival process
        print("\n🔄 TESTING ACTUAL ARCHIVAL:")
        
        try:
            # Run the archiver with the fix
            actual_stats = archiver.archive_api_logging_data(cursor, dry_run=False)
            connection.commit()
            
            print(f"   ✅ Archival completed!")
            print(f"   Headers archived: {actual_stats['headers_archived']}")
            print(f"   Lines archived: {actual_stats['lines_archived']}")
            print(f"   Total archived: {actual_stats['total_archived']}")
            
            # 4. Verify AFTER archival
            print("\n✅ AFTER ARCHIVAL - Verification:")
            
            cursor.execute("SELECT COUNT(*) FROM ORDER_LIST_API_LOG")
            new_api_log_count = cursor.fetchone()[0]
            print(f"   ORDER_LIST_API_LOG records: {new_api_log_count:,}")
            
            records_added = new_api_log_count - current_api_log
            print(f"   Records added: {records_added:,}")
            
            # Check if gap is closed
            new_gap = fact_with_payload - new_api_log_count
            if new_gap <= 0:
                print(f"   🎯 SUCCESS! Gap closed - all API calls now logged")
            else:
                print(f"   ⚠️  Gap reduced but not closed: {new_gap:,} records still missing")
            
            # Sample recent archival records
            print("\n📋 SAMPLE ARCHIVED RECORDS:")
            cursor.execute("""
                SELECT TOP 3
                    source,
                    api_operation_type,
                    api_status,
                    archived_at,
                    pipeline_run_id
                FROM ORDER_LIST_API_LOG
                ORDER BY archived_at DESC
            """)
            
            for row in cursor.fetchall():
                source, op_type, status, archived_at, pipeline_id = row
                print(f"   {source:8} | {op_type or 'NULL':15} | {status or 'NULL':8} | {archived_at} | {pipeline_id}")
                
        except Exception as e:
            print(f"   ❌ Archival failed: {e}")
            connection.rollback()
        
        cursor.close()
    
    print("\n🎯 API LOGGING ARCHIVER TEST COMPLETE")
    
if __name__ == "__main__":
    main()
