#!/usr/bin/env python3
"""Debug script to test the full pipeline with Rhythm data"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import pandas as pd
from audit_pipeline.config import get_customer_matching_config
from audit_pipeline.matching import (
    match_records,
    add_match_keys,
    exact_match,
    aggregate_quantities
)

def create_rhythm_test_data():
    """Create minimal Rhythm test data"""
    packed_data = pd.DataFrame([{
        'Canonical_Customer': 'RHYTHM',
        'Customer': 'Rhythm',
        'Customer_PO': 'RHYTHM-PO-001',
        'Customer_Alt_PO': '',
        'Style': '',
        'Pattern_ID': '',
        'ALIAS/RELATED ITEM': 'RHY-TEST-ITEM',
        'Color': 'NAVY',
        'Size': 'M',
        'Qty': 25
    }])
    
    shipped_data = packed_data.copy()
    
    orders_data = packed_data.copy()
    orders_data['Ordered_Qty'] = orders_data['Qty']
    
    return packed_data, shipped_data, orders_data

print("=== Debugging Full Pipeline with Rhythm Data ===")

packed_data, shipped_data, orders_data = create_rhythm_test_data()

print(f"Input data: {len(packed_data)} packed, {len(shipped_data)} shipped, {len(orders_data)} orders")

# Step 1: Check add_match_keys individually
print("\n--- Step 1: Testing add_match_keys ---")
packed_with_keys = add_match_keys(packed_data.copy())
print(f"Packed with keys - Style_Source: {packed_with_keys['Style_Source'].iloc[0]}")

shipped_with_keys = add_match_keys(shipped_data.copy())
print(f"Shipped with keys - Style_Source: {shipped_with_keys['Style_Source'].iloc[0]}")

orders_with_keys = add_match_keys(orders_data.copy())
print(f"Orders with keys - Style_Source: {orders_with_keys['Style_Source'].iloc[0]}")

# Step 2: Test aggregate_quantities
print("\n--- Step 2: Testing aggregate_quantities ---")
combined_agg = aggregate_quantities(packed_with_keys.copy(), shipped_with_keys.copy())
print(f"Combined aggregated columns: {list(combined_agg.columns)}")
if 'Style_Source' in combined_agg.columns:
    print(f"Combined aggregated - Style_Source: {combined_agg['Style_Source'].iloc[0]}")
else:
    print("❌ Style_Source column missing after aggregation!")

# Step 3: Test exact_match
print("\n--- Step 3: Testing exact_match ---")
try:
    exact_results, unmatched_results, orders_keys = exact_match(combined_agg.copy(), orders_with_keys.copy())
    print(f"Exact match results columns: {list(exact_results.columns)}")
    if 'Style_Source' in exact_results.columns:
        rhythm_results = exact_results[exact_results['Canonical_Customer'] == 'RHYTHM']
        if len(rhythm_results) > 0:
            print(f"Exact match - Style_Source: {rhythm_results['Style_Source'].iloc[0]}")
        else:
            print("No Rhythm results in exact match")
    else:
        print("❌ Style_Source column missing in exact match results!")
except Exception as e:
    print(f"❌ Exact match failed: {e}")

# Step 4: Test full pipeline
print("\n--- Step 4: Testing full match_records pipeline ---")
try:
    results_df, summary_df = match_records(packed_data.copy(), shipped_data.copy(), orders_data.copy(), threshold=75)
    print(f"Full pipeline results columns: {list(results_df.columns)}")
    
    rhythm_results = results_df[results_df['Canonical_Customer'] == 'RHYTHM']
    if len(rhythm_results) > 0:
        style_source = rhythm_results['Style_Source'].iloc[0] if 'Style_Source' in rhythm_results.columns else 'COLUMN_MISSING'
        print(f"Full pipeline - Style_Source: {style_source}")
        
        if style_source == 'ALIAS/RELATED ITEM':
            print("✅ SUCCESS: Full pipeline preserves Style_Source correctly")
        else:
            print(f"❌ FAILURE: Expected 'ALIAS/RELATED ITEM', got '{style_source}'")
    else:
        print("❌ No Rhythm results in full pipeline")
        
except Exception as e:
    print(f"❌ Full pipeline failed: {e}")
    import traceback
    traceback.print_exc()
