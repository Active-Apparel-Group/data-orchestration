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

# Check what's currently in both tables
print('📊 Target table (ORDER_LIST_V2) analysis:')
target_query = '''
SELECT 
    COUNT(*) as total_records,
    COUNT(CASE WHEN [AAG ORDER NUMBER] IS NOT NULL THEN 1 END) as records_with_aag_order,
    COUNT(DISTINCT [AAG ORDER NUMBER]) as unique_aag_orders
FROM ORDER_LIST_V2
'''
target_result = pd.read_sql_query(target_query, db.get_connection('orders'))
print(f"  Total records: {target_result.iloc[0]['total_records']}")
print(f"  With AAG ORDER: {target_result.iloc[0]['records_with_aag_order']}")
print(f"  Unique AAG ORDERs: {target_result.iloc[0]['unique_aag_orders']}")

print()
print('📊 Source table (swp_ORDER_LIST_V2) analysis:')
source_query = '''
SELECT 
    COUNT(*) as total_records,
    COUNT(CASE WHEN [AAG ORDER NUMBER] IS NOT NULL THEN 1 END) as records_with_aag_order,
    COUNT(DISTINCT [AAG ORDER NUMBER]) as unique_aag_orders
FROM swp_ORDER_LIST_V2 
WHERE sync_state = 'NEW'
'''

source_result = pd.read_sql_query(source_query, db.get_connection('orders'))
print(f"  Total NEW records: {source_result.iloc[0]['total_records']}")
print(f"  With AAG ORDER: {source_result.iloc[0]['records_with_aag_order']}")
print(f"  Unique AAG ORDERs: {source_result.iloc[0]['unique_aag_orders']}")