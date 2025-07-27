#!/usr/bin/env python3
"""
Debug Data Issues - Quick Check for ORDER_LIST and FACT_ORDER_LIST
"""
import sys
from pathlib import Path

# EXACT WORKING IMPORT PATTERN from imports.guidance.instructions.md
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger

logger = logger.get_logger(__name__)

def main():
    cursor = None
    connection = None
    try:
        connection = db.get_connection('orders')
        cursor = connection.cursor()
        
        print('🔍 DEBUGGING DATA ISSUES...')
        print('=' * 60)
        
        # Check view v_order_list_nulls_to_delete
        print('1. Checking view v_order_list_nulls_to_delete...')
        try:
            cursor.execute('SELECT COUNT(*) FROM v_order_list_nulls_to_delete')
            count = cursor.fetchone()[0]
            print(f'   Records in view: {count}')
            
            if count > 0:
                cursor.execute('SELECT TOP 3 record_uuid FROM v_order_list_nulls_to_delete')
                rows = cursor.fetchall()
                print('   Sample records:')
                for row in rows:
                    print(f'     {row[0]}')
        except Exception as e:
            print(f'   ❌ View error: {e}')
        
        # Check swp_ORDER_LIST_SYNC table
        print('\n2. Checking swp_ORDER_LIST_SYNC table...')
        try:
            cursor.execute('SELECT COUNT(*) FROM swp_ORDER_LIST_SYNC')
            sync_count = cursor.fetchone()[0]
            print(f'   Records in swp_ORDER_LIST_SYNC: {sync_count}')
        except Exception as e:
            print(f'   ❌ Sync table error: {e}')
        
        # Check source ORDER_LIST
        print('\n3. Checking source ORDER_LIST...')
        try:
            cursor.execute("SELECT COUNT(*) FROM ORDER_LIST WHERE [CUSTOMER NAME] like 'GREYSON%' AND [PO NUMBER] = '4755'")
            source_count = cursor.fetchone()[0]
            print(f'   Source GREYSON PO 4755 records: {source_count}')
        except Exception as e:
            print(f'   ❌ Source table error: {e}')
            
        # Check FACT_ORDER_LIST
        print('\n4. Checking FACT_ORDER_LIST...')
        try:
            cursor.execute("SELECT COUNT(*) FROM FACT_ORDER_LIST WHERE [CUSTOMER NAME] like 'GREYSON%' AND [PO NUMBER] = '4755'")
            fact_count = cursor.fetchone()[0]
            print(f'   FACT_ORDER_LIST GREYSON PO 4755 records: {fact_count}')
        except Exception as e:
            print(f'   ❌ FACT table error: {e}')
            
        # Check if tables exist
        print('\n5. Checking table existence...')
        tables_to_check = ['ORDER_LIST', 'swp_ORDER_LIST_SYNC', 'FACT_ORDER_LIST', 'ORDER_LIST_V2']
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f'   ✅ {table}: {count} records')
            except Exception as e:
                print(f'   ❌ {table}: {e}')
        
        print('\n=' * 60)
        print('✅ Debug complete')
        
    except Exception as e:
        print(f'❌ Connection error: {e}')
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

if __name__ == "__main__":
    main()
