#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import pandas as pd
from audit_pipeline.matching import add_match_keys, aggregate_quantities, exact_match
from audit_pipeline.config import get_customer_matching_config

def debug_step_by_step():
    print("=== Step-by-step Style_Source debugging ===")
    
    # Create Rhythm customer data
    packed_data = pd.DataFrame([{
        'Canonical_Customer': 'RHYTHM',
        'Customer': 'Rhythm',
        'Customer_PO': 'PO123',
        'Customer_Alt_PO': 'ALT123',
        'Style': '',  # Empty style to trigger ALIAS/RELATED ITEM
        'ALIAS/RELATED ITEM': 'Sample Product',
        'Pattern_ID': 'PAT001',
        'Color': 'Blue',
        'Size': 'M',
        'Qty': 10,
        'Status': 'Packed'
    }])
    
    shipped_data = pd.DataFrame([{
        'Canonical_Customer': 'RHYTHM',
        'Customer': 'Rhythm',
        'Customer_PO': 'PO123',
        'Customer_Alt_PO': 'ALT123',
        'Style': '',
        'ALIAS/RELATED ITEM': 'Sample Product',
        'Pattern_ID': 'PAT001',
        'Color': 'Blue',
        'Size': 'M',
        'Qty': 5,
        'Status': 'Shipped'
    }])
    
    orders_data = pd.DataFrame([{
        'Canonical_Customer': 'RHYTHM',
        'Customer': 'Rhythm',
        'Customer_PO': 'PO123',
        'Customer_Alt_PO': 'ALT123',
        'Style': '',
        'ALIAS/RELATED ITEM': 'Sample Product',
        'Pattern_ID': 'PAT001',
        'Color': 'Blue',
        'Size': 'M',
        'Ordered_Qty': 15
    }])
    
    print("Step 1: Add match keys")
    packed_with_keys = add_match_keys(packed_data.copy())
    shipped_with_keys = add_match_keys(shipped_data.copy())
    orders_with_keys = add_match_keys(orders_data.copy())
    
    print(f"Packed Style_Source: {packed_with_keys['Style_Source'].iloc[0]}")
    print(f"Shipped Style_Source: {shipped_with_keys['Style_Source'].iloc[0]}")
    print(f"Orders Style_Source: {orders_with_keys['Style_Source'].iloc[0]}")
    
    print("\nStep 2: Aggregate quantities")
    combined_agg = aggregate_quantities(packed_with_keys.copy(), shipped_with_keys.copy())
    print(f"Combined Style_Source: {combined_agg['Style_Source'].iloc[0]}")
    print(f"Combined Style_Source type: {type(combined_agg['Style_Source'].iloc[0])}")
    
    print("\nStep 3: Before exact_match - check data types")
    print(f"Combined Style_Source dtype: {combined_agg['Style_Source'].dtype}")
    print(f"Orders Style_Source dtype: {orders_with_keys['Style_Source'].dtype}")
    print(f"Combined Style_Source values: {combined_agg['Style_Source'].unique()}")
    print(f"Orders Style_Source values: {orders_with_keys['Style_Source'].unique()}")
    
    print("\nStep 4: Exact match")
    results, unmatched, orders_keys = exact_match(combined_agg.copy(), orders_with_keys.copy())
    print(f"Results Style_Source: {results['Style_Source'].iloc[0]}")
    print(f"Results Style_Source type: {type(results['Style_Source'].iloc[0])}")
    print(f"Results Style_Source dtype: {results['Style_Source'].dtype}")

if __name__ == "__main__":
    debug_step_by_step()
