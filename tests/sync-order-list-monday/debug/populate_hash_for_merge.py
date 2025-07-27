"""
Populate row_hash column in swp_ORDER_LIST_V2 for merge testing
Purpose: Fix NULL row_hash issue preventing merge template from working
"""
import sys
from pathlib import Path
import pandas as pd
import toml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from pipelines.utils import db

print('🔧 Populating row_hash for swp_ORDER_LIST_V2 records...')

try:
    # Load TOML config directly to get hash columns
    config_data = toml.load('configs/pipelines/sync_order_list.toml')
    hash_columns = config_data.get('hash', {}).get('columns', [])
    
    print(f'📋 Hash columns from TOML: {hash_columns}')
    
    if hash_columns and len(hash_columns) > 0:
        # Build the hash calculation SQL using TOML hash columns
        hash_concat_parts = []
        for col in hash_columns:
            hash_concat_parts.append(f"COALESCE([{col}], '')")
        
        hash_concat = ", ".join(hash_concat_parts)
        
        update_sql = f'''
        UPDATE swp_ORDER_LIST_V2
        SET row_hash = CONVERT(VARCHAR(32), HASHBYTES('MD5', 
            CONCAT({hash_concat})
        ), 2)
        WHERE row_hash IS NULL OR row_hash = ''
        '''
        
        print('🔄 Executing hash update...')
        print(f'Hash formula: MD5(CONCAT({hash_concat}))')
        
        # Execute the update
        conn = db.get_connection('orders')
        cursor = conn.cursor()
        cursor.execute(update_sql)
        rows_affected = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f'✅ Updated {rows_affected} records with hash values')
        
        # Verify the update worked
        print('🔍 Verifying hash population...')
        check_sql = '''
        SELECT
            COUNT(*) as total_records,
            COUNT(CASE WHEN row_hash IS NOT NULL AND row_hash != '' THEN 1 END) as records_with_hash
        FROM swp_ORDER_LIST_V2
        '''
        check_result = pd.read_sql_query(check_sql, db.get_connection('orders'))
        total = check_result.iloc[0]['total_records']
        with_hash = check_result.iloc[0]['records_with_hash']
        
        print(f'📊 Verification: {with_hash} of {total} records have hash')
        
        if with_hash == total:
            print('✅ SUCCESS: All records now have hash values!')
        else:
            print(f'⚠️  WARNING: {total - with_hash} records still missing hash')
            
    else:
        print('❌ No hash columns found in TOML configuration')
        
except Exception as e:
    print(f'❌ Error updating hash: {e}')
    import traceback
    traceback.print_exc()
