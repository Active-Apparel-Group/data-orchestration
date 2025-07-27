#!/usr/bin/env python3
"""
Debug script to test dynamic size detection in isolation
"""
import sys
sys.path.append('utils')
sys.path.append('dev/customer-orders')

from staging_processor import StagingProcessor
import db_helper as db
import pandas as pd

# Create test data that simulates the transformed order data
test_data = {
    'stg_id': [1],
    'CUSTOMER NAME': ['GREYSON CLOTHIERS'],
    'AAG ORDER NUMBER': ['JOO-00505'],
    'STYLE': ['JWHD100120'],
    'COLOR': ['WHITE'],
    'XS': [2],  # Size columns with quantities
    'S': [5],
    'M': [10], 
    'L': [8],
    'XL': [3],
    'CUSTOMER PRICE': [50.00],  # Non-size columns
    'FREIGHT': [10.00],
    'ORDER DATE PO RECEIVED': ['2025-06-25']
}

df = pd.DataFrame(test_data)
print("Test data columns:", list(df.columns))
print("Test data:")
print(df)

# Test dynamic size detection
processor = StagingProcessor()
batch_id = '12345678-1234-1234-1234-123456789012'

print("\n=== Testing Dynamic Size Detection ===")
subitems_df = processor._create_subitems_from_sizes(df, batch_id)

print(f"\nCreated {len(subitems_df)} subitems")
if not subitems_df.empty:
    print("Subitems columns:", list(subitems_df.columns))
    print("\nSubitems data:")
    print(subitems_df[['Size', 'Order Qty']].to_string())
else:
    print("No subitems created!")
