#!/usr/bin/env python3
"""
Debug the actual insert statement being generated
"""
import sys
sys.path.append('utils')
sys.path.append('dev/customer-orders')

from staging_processor import StagingProcessor
import pandas as pd

# Create test subitems data similar to what dynamic detection would create
test_subitems = [
    {
        'stg_batch_id': '12345678-1234-1234-1234-123456789012',
        'stg_parent_stg_id': 1,
        'stg_customer_batch': 'GREYSON CLOTHIERS',
        'stg_source_order_number': 'JOO-00505',
        'stg_source_style': 'JWHD100120',
        'stg_source_color': 'WHITE',
        'Size': 'XS',
        'Order Qty': '2',
        'stg_size_label': 'XS',
        'stg_order_qty_numeric': 2,
        'stg_status': 'PENDING',
        'stg_retry_count': 0
    }
]

df = pd.DataFrame(test_subitems)
print("Test subitems DataFrame:")
print(df.info())
print("\nColumns:", list(df.columns))

# Test the insert logic
processor = StagingProcessor()
try:
    result = processor._insert_to_staging_subitems(df, '12345678-1234-1234-1234-123456789012')
    print(f"Successfully inserted {result} subitems")
except Exception as e:
    print(f"Insert failed: {e}")
    print(f"Error type: {type(e)}")
