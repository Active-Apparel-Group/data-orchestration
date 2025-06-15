#!/usr/bin/env python3
"""
Test RHYTHM matching logic specifically
"""
import sys
import pandas as pd
from pathlib import Path

# Add the src directory to Python path for module imports
script_dir = Path(__file__).parent
src_dir = script_dir / "src"
sys.path.insert(0, str(src_dir))

from audit_pipeline.matching import get_style_value_and_source, create_matching_key, get_customer_config_cached

def test_rhythm_logic():
    print("=== Testing RHYTHM Logic ===")
    
    # Check RHYTHM configuration
    config = get_customer_config_cached('RHYTHM')
    print(f"RHYTHM Config:")
    print(f"  - style_match_strategy: {config.get('style_match_strategy', 'None')}")
    print(f"  - style_field_override: {config.get('style_field_override', 'None')}")
    
    print("\n=== Test 1: RHYTHM Order Data (should use ALIAS/RELATED ITEM) ===")
    # Order data from RHYTHM should have ALIAS/RELATED ITEM
    rhythm_order_row = pd.Series({
        'Canonical_Customer': 'RHYTHM',
        'Customer': 'RHYTHM',
        'Customer_PO': '19200',
        'Style': None,  # Order data doesn't use Style field
        'Pattern_ID': None,  # Order data doesn't use Pattern_ID
        'ALIAS/RELATED ITEM': 'CLA24SW-BB04-BLK',  # This is where the style info is
        'Color': 'BLACK',
        'Size': '06/XS'
    })
    
    style_value, style_source = get_style_value_and_source(rhythm_order_row, 'RHYTHM')
    print(f"Order Style Value: '{style_value}'")
    print(f"Order Style Source: '{style_source}'")
    
    matching_key = create_matching_key(rhythm_order_row, canonical_customer='RHYTHM')
    print(f"Order Matching Key: '{matching_key}'")
    
    print("\n=== Test 2: RHYTHM Shipped Data (has Style field populated) ===")
    # Shipped data always has Style field populated
    rhythm_shipped_row = pd.Series({
        'Canonical_Customer': 'RHYTHM',
        'Customer': 'RHYTHM',
        'Customer_PO': '19200',
        'Style': 'CLA24SW-BB04-BLK',  # Shipped data has this in Style field
        'Pattern_ID': None,
        'ALIAS/RELATED ITEM': None,  # Shipped data doesn't have this
        'Color': 'BLACK',
        'Size': '06/XS'
    })
    
    style_value, style_source = get_style_value_and_source(rhythm_shipped_row, 'RHYTHM')
    print(f"Shipped Style Value: '{style_value}'")
    print(f"Shipped Style Source: '{style_source}'")
    
    matching_key = create_matching_key(rhythm_shipped_row, canonical_customer='RHYTHM')
    print(f"Shipped Matching Key: '{matching_key}'")
    
    print("\n=== Analysis ===")
    # Both should produce the same matching key for proper matching
    order_key = create_matching_key(rhythm_order_row, canonical_customer='RHYTHM')
    shipped_key = create_matching_key(rhythm_shipped_row, canonical_customer='RHYTHM')
    
    if order_key == shipped_key:
        print("✅ MATCHING KEYS ARE IDENTICAL - Good!")
    else:
        print(f"❌ MATCHING KEYS DIFFER:")
        print(f"   Order Key:   '{order_key}'")
        print(f"   Shipped Key: '{shipped_key}'")
        print("   This explains why RHYTHM records are not matching!")

if __name__ == "__main__":
    test_rhythm_logic()
