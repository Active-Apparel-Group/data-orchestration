import sys
from pathlib import Path
import logging
import json
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from pipelines.utils import db
from src.pipelines.sync_order_list.config_parser import load_delta_sync_config
import pandas as pd

print('🔍 Testing the exact source query from merge template:')

# This is the exact source query from the merge template
source_query = '''
SELECT
    record_uuid,
    [AAG ORDER NUMBER],
    [PO NUMBER],
    [CUSTOMER NAME],
    sync_state,
    created_at,
    updated_at,
    row_hash
FROM dbo.swp_ORDER_LIST_V2
WHERE sync_state = 'NEW'  -- Only NEW orders (Python preprocessing)
AND [AAG ORDER NUMBER] IS NOT NULL  -- Valid business key
'''

try:
    source_result = pd.read_sql_query(source_query, db.get_connection('orders'))
    print(f"📊 Source query results:")
    print(f"  Records returned: {len(source_result)}")
    
    if len(source_result) > 0:
        print(f"  Sample record:")
        print(f"    AAG ORDER NUMBER: {source_result.iloc[0]['AAG ORDER NUMBER']}")
        print(f"    PO NUMBER: {source_result.iloc[0]['PO NUMBER']}")
        print(f"    CUSTOMER NAME: {source_result.iloc[0]['CUSTOMER NAME']}")
        print(f"    sync_state: {source_result.iloc[0]['sync_state']}")
        print(f"    row_hash: {source_result.iloc[0]['row_hash']}")
        
        # Check for null row_hash which might prevent the merge
        null_hash_count = source_result['row_hash'].isnull().sum()
        print(f"  Records with NULL row_hash: {null_hash_count}")
        
        # Check for null AAG ORDER NUMBER
        null_aag_count = source_result['AAG ORDER NUMBER'].isnull().sum()
        print(f"  Records with NULL AAG ORDER NUMBER: {null_aag_count}")
    else:
        print("❌ No records returned from source query!")
        
        # Check what's in the table without filters
        print("\n🔍 Checking swp_ORDER_LIST_V2 without filters:")
        unfiltered_query = '''
        SELECT 
            sync_state,
            COUNT(*) as count,
            COUNT(CASE WHEN [AAG ORDER NUMBER] IS NOT NULL THEN 1 END) as with_aag_order
        FROM dbo.swp_ORDER_LIST_V2 
        GROUP BY sync_state
        '''
        unfiltered_result = pd.read_sql_query(unfiltered_query, db.get_connection('orders'))
        for index, row in unfiltered_result.iterrows():
            print(f"  sync_state: '{row['sync_state']}' | Records: {row['count']} | With AAG ORDER: {row['with_aag_order']}")

except Exception as e:
    print(f"❌ Error executing source query: {e}")
