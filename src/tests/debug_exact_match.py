#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import pandas as pd
from audit_pipeline.matching import add_match_keys, exact_match
from audit_pipeline.config import get_customer_matching_config

def debug_exact_match():
    print("=== Debugging exact_match function ===")
    
    # Create sample data with Style_Source already set
    combined_data = pd.DataFrame([{
        'Canonical_Customer': 'RHYTHM',
        'Customer': 'Rhythm',
        'Customer_PO': 'PO123',
        'Customer_Alt_PO': 'ALT123',
        'Style': 'Sample Style Value',
        'Pattern_ID': 'PAT001',
        'Color': 'Blue',
        'Size': 'M',
        'Style_Source': 'ALIAS/RELATED ITEM',  # This should be preserved
        'Packed_Qty': 10,
        'Shipped_Qty': 5,
        'Source_Type': 'PACKED,SHIPPED',
        'exact_key': 'RHYTHM|PO123|ALT123|Sample Style Value|PAT001|Blue|M',
        'fuzzy_key': 'RHYTHM|Sample Style Value|Blue|M'
    }])
    
    orders_data = pd.DataFrame([{
        'Canonical_Customer': 'RHYTHM',
        'Customer': 'Rhythm',
        'Customer_PO': 'PO123',
        'Customer_Alt_PO': 'ALT123',
        'Style': 'Sample Style Value',
        'Pattern_ID': 'PAT001',
        'Color': 'Blue',
        'Size': 'M',
        'Ordered_Qty': 15
    }])
    
    print(f"Input combined_data Style_Source: {combined_data['Style_Source'].iloc[0]}")
    
    # Test exact_match
    try:
        results, unmatched, orders_keys = exact_match(combined_data.copy(), orders_data.copy())
        print(f"Results columns: {list(results.columns)}")
        if 'Style_Source' in results.columns:
            print(f"Output results Style_Source: {results['Style_Source'].iloc[0]}")
        else:
            print("❌ Style_Source column missing from results!")
            
    except Exception as e:
        print(f"❌ exact_match failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_exact_match()
