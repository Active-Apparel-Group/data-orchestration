#!/usr/bin/env python3
"""
Set GREYSON PO 4755 to PENDING Status
====================================
Purpose: Update GREYSON PO 4755 records in FACT_ORDER_LIST to sync_state = 'PENDING'
Location: tests/production_migration/integration/test_set_greyson_pending.py
Created: 2025-07-29

This sets the inserted GREYSON PO 4755 records to PENDING status so CLI can sync them.
"""

import sys
from pathlib import Path

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger

logger = logger.get_logger(__name__)

def main():
    print("🔧 Setting GREYSON PO 4755 Records to PENDING Status")
    print("=" * 60)
    
    try:
        with db.get_connection('orders') as connection:
            cursor = connection.cursor()
            
            # First, check current status
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN sync_state = 'PENDING' THEN 1 END) as pending_records,
                    COUNT(CASE WHEN sync_state IS NULL THEN 1 END) as null_sync_state
                FROM [FACT_ORDER_LIST]
                WHERE [CUSTOMER NAME] LIKE 'GREYSON%' 
                  AND [PO NUMBER] = '4755'
            """)
            
            result = cursor.fetchone()
            total, pending, null_state = result
            
            print(f"📊 Current GREYSON PO 4755 Status:")
            print(f"   Total records: {total}")
            print(f"   Already PENDING: {pending}")
            print(f"   NULL sync_state: {null_state}")
            
            if total == 0:
                print("❌ No GREYSON PO 4755 records found!")
                print("   Make sure to run your SQL insert script first.")
                return {'success': False, 'error': 'No records found'}
            
            # Update records to PENDING status
            print(f"\n🔄 Setting {total} records to PENDING status...")
            
            update_query = """
                UPDATE [FACT_ORDER_LIST]
                SET [action_type] = 'INSERT',
                    [sync_state] = 'PENDING',
                    [sync_pending_at] = GETUTCDATE(),
                    [monday_item_id] = NULL,
                    [sync_completed_at] = NULL,
                    [sync_error_message] = NULL,
                    [retry_count] = 0,
                    [updated_at] = GETUTCDATE()
                WHERE [CUSTOMER NAME] LIKE 'GREYSON%' 
                  AND [PO NUMBER] = '4755'
                  AND ([sync_state] IS NULL OR [sync_state] != 'PENDING')
            """
            
            cursor.execute(update_query)
            rows_updated = cursor.rowcount
            connection.commit()
            
            print(f"✅ Updated {rows_updated} records to PENDING status")
            
            # Verify update
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_pending,
                    [CUSTOMER NAME],
                    [PO NUMBER],
                    COUNT([AAG ORDER NUMBER]) as order_count
                FROM [FACT_ORDER_LIST]
                WHERE [CUSTOMER NAME] LIKE 'GREYSON%' 
                  AND [PO NUMBER] = '4755'
                  AND [sync_state] = 'PENDING'
                GROUP BY [CUSTOMER NAME], [PO NUMBER]
            """)
            
            verification = cursor.fetchall()
            
            print(f"\n📋 Verification:")
            for row in verification:
                pending_count, customer, po, order_count = row
                print(f"   {customer} PO {po}: {pending_count} records PENDING")
            
            return {
                'success': True,
                'total_records': total,
                'updated_records': rows_updated,
                'pending_records': pending_count if verification else 0
            }
            
    except Exception as e:
        logger.exception(f"Failed to set GREYSON records to PENDING: {e}")
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    result = main()
    if result['success']:
        print(f"\n🎉 GREYSON PO 4755 Ready for CLI Sync!")
        print(f"   {result['pending_records']} records set to PENDING")
        print(f"\n🚀 Now run: python tests/production_migration/integration/test_cli_direct.py")
    else:
        print(f"\n❌ Failed: {result['error']}")
