"""
Check table schemas to identify any column mismatch issues
"""
import sys
from pathlib import Path
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from pipelines.utils import db

print('🔍 Comparing table schemas...')

# Check source table schema (swp_ORDER_LIST_V2)
print('📋 Source table (swp_ORDER_LIST_V2) essential columns:')
source_schema_query = '''
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'swp_ORDER_LIST_V2'
AND COLUMN_NAME IN ('record_uuid', 'AAG ORDER NUMBER', 'PO NUMBER', 'CUSTOMER NAME', 'row_hash', 'sync_state', 'created_at', 'updated_at')
ORDER BY ORDINAL_POSITION
'''

source_schema = pd.read_sql_query(source_schema_query, db.get_connection('orders'))
print(source_schema.to_string(index=False))

print()
print('📋 Target table (ORDER_LIST_V2) essential columns:')
target_schema_query = '''
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'ORDER_LIST_V2'
AND COLUMN_NAME IN ('record_uuid', 'AAG ORDER NUMBER', 'PO NUMBER', 'CUSTOMER NAME', 'row_hash', 'action_type', 'sync_state', 'sync_attempted_at', 'created_at', 'updated_at')
ORDER BY ORDINAL_POSITION
'''

target_schema = pd.read_sql_query(target_schema_query, db.get_connection('orders'))
print(target_schema.to_string(index=False))

# Check if sync columns exist in target
print()
print('🔍 Checking sync columns in target table:')
sync_columns_query = '''
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'ORDER_LIST_V2'
AND COLUMN_NAME IN ('action_type', 'sync_state', 'sync_attempted_at')
ORDER BY COLUMN_NAME
'''

sync_columns = pd.read_sql_query(sync_columns_query, db.get_connection('orders'))
if len(sync_columns) > 0:
    print('✅ Sync columns found:')
    print(sync_columns.to_string(index=False))
else:
    print('❌ Sync columns NOT found in target table!')
    print('This could be the issue - the INSERT statement references columns that don\'t exist.')

# Test a simple INSERT to verify table structure
print()
print('🔍 Testing simple INSERT to verify table accepts our column structure...')
test_insert = '''
INSERT INTO ORDER_LIST_V2 (
    record_uuid,
    [AAG ORDER NUMBER],
    [PO NUMBER],
    [CUSTOMER NAME],
    action_type,
    sync_state
) VALUES (
    NEWID(),
    'TEST-12345',
    'TEST-PO',
    'TEST CUSTOMER',
    'INSERT',
    'PENDING'
);

SELECT @@ROWCOUNT as rows_inserted;

-- Clean up the test record
DELETE FROM ORDER_LIST_V2 WHERE [AAG ORDER NUMBER] = 'TEST-12345';
'''

try:
    test_result = pd.read_sql_query(test_insert, db.get_connection('orders'))
    if test_result.iloc[0]['rows_inserted'] == 1:
        print('✅ Simple INSERT works - table structure is correct')
    else:
        print('❌ Simple INSERT failed')
except Exception as e:
    print(f'❌ Simple INSERT error: {e}')
    print('This indicates a column mismatch or constraint issue')
