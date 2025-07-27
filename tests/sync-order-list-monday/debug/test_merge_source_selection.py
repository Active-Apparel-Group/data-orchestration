"""
Debug the merge source selection to see what records are actually being selected
"""
import sys
from pathlib import Path
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from pipelines.utils import db

print('🔍 Testing MERGE source selection directly...')

# Test the exact USING clause from the merge
source_query = '''
SELECT
    record_uuid,
    [AAG ORDER NUMBER],
    [PO NUMBER],
    [CUSTOMER NAME],
    row_hash,
    sync_state,
    created_at,
    updated_at
FROM dbo.swp_ORDER_LIST_V2
WHERE sync_state = 'NEW'
AND [AAG ORDER NUMBER] IS NOT NULL
'''

try:
    print('📊 Executing source selection...')
    result = pd.read_sql_query(source_query, db.get_connection('orders'))
    
    print(f'Records in source query: {len(result)}')
    
    if len(result) > 0:
        print(f'✅ Source selection working - {len(result)} records found')
        print('Sample records:')
        print(result[['AAG ORDER NUMBER', 'PO NUMBER', 'CUSTOMER NAME', 'row_hash', 'sync_state']].head(3))
        
        # Now test if there are any matching records in target
        print()
        print('🔍 Checking for existing records in target with same AAG ORDER NUMBER...')
        
        # Get list of AAG ORDER NUMBERs from source
        aag_orders = result['AAG ORDER NUMBER'].tolist()
        aag_orders_str = "', '".join(aag_orders[:10])  # First 10 for testing
        
        target_check_query = f'''
        SELECT 
            [AAG ORDER NUMBER],
            COUNT(*) as count
        FROM ORDER_LIST_V2 
        WHERE [AAG ORDER NUMBER] IN ('{aag_orders_str}')
        GROUP BY [AAG ORDER NUMBER]
        '''
        
        target_result = pd.read_sql_query(target_check_query, db.get_connection('orders'))
        
        if len(target_result) > 0:
            print(f'⚠️ Found {len(target_result)} matching AAG ORDER NUMBERs in target:')
            print(target_result)
            print('This would trigger WHEN MATCHED condition (UPDATE)')
        else:
            print('✅ No matching AAG ORDER NUMBERs in target')
            print('This should trigger WHEN NOT MATCHED condition (INSERT)')
            
    else:
        print('❌ No records returned from source selection!')
        
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
