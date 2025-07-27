#!/usr/bin/env python3
"""
Debug CLI Execution - Check table states and sync pipeline status
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def main():
    print("🔧 Debug CLI Execution - Table Analysis")
    print("=" * 45)
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        try:
            print("\n📋 1. Basic Table Existence Check...")
            
            tables_to_check = ['FACT_ORDER_LIST', 'ORDER_LIST', 'ORDER_LIST_LINES']
            
            for table in tables_to_check:
                cursor.execute(f"""
                    SELECT COUNT(*) as total_records,
                           COUNT(CASE WHEN sync_state IS NOT NULL THEN 1 END) as records_with_sync_state
                    FROM {table}
                """)
                result = cursor.fetchone()
                total = result[0]
                with_sync_state = result[1]
                
                print(f"   📊 {table}:")
                print(f"      Total records: {total}")
                print(f"      Records with sync_state: {with_sync_state}")
                
                if total > 0:
                    # Check sync states
                    cursor.execute(f"""
                        SELECT sync_state, COUNT(*) as count
                        FROM {table}
                        WHERE sync_state IS NOT NULL
                        GROUP BY sync_state
                        ORDER BY count DESC
                    """)
                    sync_states = cursor.fetchall()
                    
                    if sync_states:
                        print(f"      Sync states breakdown:")
                        for state, count in sync_states:
                            print(f"        {state}: {count}")
                else:
                    print(f"      ⚠️  No records found in {table}")
            
            print("\n📋 2. API Logging Columns Check...")
            
            # Check if API columns exist and have data
            cursor.execute("""
                SELECT COUNT(*) as total,
                       COUNT(api_request_payload) as with_req_payload,
                       COUNT(api_response_payload) as with_resp_payload,
                       COUNT(api_request_timestamp) as with_req_ts,
                       COUNT(api_response_timestamp) as with_resp_ts,
                       COUNT(api_operation_type) as with_operation,
                       COUNT(api_status) as with_status
                FROM FACT_ORDER_LIST
            """)
            
            api_result = cursor.fetchone()
            total_records = api_result[0]
            
            if total_records > 0:
                print(f"   📊 FACT_ORDER_LIST API Columns Status:")
                print(f"      Total records: {total_records}")
                print(f"      With api_request_payload: {api_result[1]}")
                print(f"      With api_response_payload: {api_result[2]}")
                print(f"      With api_request_timestamp: {api_result[3]}")
                print(f"      With api_response_timestamp: {api_result[4]}")
                print(f"      With api_operation_type: {api_result[5]}")
                print(f"      With api_status: {api_result[6]}")
            else:
                print("   ⚠️  No records in FACT_ORDER_LIST to check API columns")
            
            print("\n📋 3. Recent Activity Check...")
            
            # Check for recent activity (last 24 hours)
            cursor.execute("""
                SELECT COUNT(*) as recent_records
                FROM FACT_ORDER_LIST
                WHERE created_at >= DATEADD(hour, -24, GETDATE())
            """)
            
            recent_result = cursor.fetchone()
            recent_count = recent_result[0]
            
            print(f"   📊 Recent Activity (Last 24 Hours):")
            print(f"      New records created: {recent_count}")
            
            if recent_count > 0:
                cursor.execute("""
                    SELECT TOP 5 
                        record_uuid,
                        sync_state,
                        created_at,
                        monday_item_id
                    FROM FACT_ORDER_LIST
                    WHERE created_at >= DATEADD(hour, -24, GETDATE())
                    ORDER BY created_at DESC
                """)
                
                recent_records = cursor.fetchall()
                print(f"   📋 Recent Records Sample:")
                for record in recent_records:
                    uuid_short = str(record[0])[:8] + "..."
                    sync_state = record[1] or "None"
                    created_at = record[2]
                    monday_id = record[3] or "None"
                    print(f"      {uuid_short} | {sync_state} | {created_at} | Monday ID: {monday_id}")
            
            print("\n📋 4. Configuration Analysis...")
            
            print(f"   📊 CLI Configuration Used:")
            print(f"      Environment: {config.environment}")
            print(f"      Database Key: {config.db_key}")
            print(f"      Monday Board ID: {config.monday_board_id}")
            print(f"      Sync Table: {config.sync_table}")
            print(f"      Lines Table: {config.lines_table}")
            
            print("\n📋 5. Troubleshooting Suggestions...")
            
            if total_records == 0:
                print("   🔧 No records found - possible causes:")
                print("      1. CLI might have run against different database")
                print("      2. CLI execution might have failed silently")
                print("      3. Tables might have been cleared/reset")
                print("      4. Configuration mismatch between CLI and validation")
            elif recent_count == 0:
                print("   🔧 No recent activity - possible causes:")
                print("      1. CLI execution didn't create new records")
                print("      2. CLI might have updated existing records without changing timestamps")
                print("      3. CLI might have run in dry-run mode")
            else:
                print("   🔧 Records exist but no sync data - possible causes:")
                print("      1. API logging not triggered (sync might not have reached Monday.com)")
                print("      2. Sync process failed before API calls")
                print("      3. API logging code path not executed")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Debug analysis failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            cursor.close()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
