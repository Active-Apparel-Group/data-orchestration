"""
Compare source and target table schemas to find column mismatches
"""
import sys
from pathlib import Path
import pandas as pd

# Add project root to path  
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from pipelines.utils import db

print('🔍 Comparing source and target table schemas...')

try:
    conn = db.get_connection('orders')
    
    print('📊 Source table (swp_ORDER_LIST_V2) columns:')
    source_query = '''
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'swp_ORDER_LIST_V2' 
    ORDER BY ORDINAL_POSITION
    '''
    source_columns = pd.read_sql_query(source_query, conn)
    print(f"  Total columns: {len(source_columns)}")
    
    print('\n📊 Target table (ORDER_LIST_V2) columns:')
    target_query = '''
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'ORDER_LIST_V2' 
    ORDER BY ORDINAL_POSITION
    '''
    target_columns = pd.read_sql_query(target_query, conn)
    print(f"  Total columns: {len(target_columns)}")
    
    # Find columns that exist in source but not in target
    source_cols = set(source_columns['COLUMN_NAME'].str.upper())
    target_cols = set(target_columns['COLUMN_NAME'].str.upper())
    
    missing_in_target = source_cols - target_cols
    missing_in_source = target_cols - source_cols
    
    print(f'\n❌ Columns in SOURCE but NOT in TARGET ({len(missing_in_target)}):')
    for col in sorted(missing_in_target):
        print(f"  {col}")
    
    print(f'\n❌ Columns in TARGET but NOT in SOURCE ({len(missing_in_source)}):')
    for col in sorted(missing_in_source):
        print(f"  {col}")
    
    # Check specific sync columns
    sync_cols = ['action_type', 'sync_state', 'sync_attempted_at']
    print(f'\n🔍 Sync columns in target table:')
    for col in sync_cols:
        if col.upper() in target_cols:
            print(f"  ✅ {col}")
        else:
            print(f"  ❌ {col} - MISSING!")
    
    # Check business columns from the minimal merge that worked
    working_cols = ['record_uuid', 'AAG ORDER NUMBER', 'PO NUMBER', 'CUSTOMER NAME', 'row_hash', 'created_at', 'updated_at']
    print(f'\n🔍 Working columns from minimal merge:')
    for col in working_cols:
        col_upper = col.upper()
        if col_upper in target_cols and col_upper in source_cols:
            print(f"  ✅ {col}")
        elif col_upper not in target_cols:
            print(f"  ❌ {col} - MISSING in TARGET!")
        elif col_upper not in source_cols:
            print(f"  ❌ {col} - MISSING in SOURCE!")
    
    conn.close()
    
except Exception as e:
    print(f'❌ Error comparing schemas: {e}')
    import traceback
    traceback.print_exc()
