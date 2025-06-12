#!/usr/bin/env python3
"""
Test the corrected RHYTHM style matching logic
"""
import sys
import pandas as pd
from pathlib import Path

# Add the src directory to Python path for module imports
script_dir = Path(__file__).parent
src_dir = script_dir / "src"
sys.path.insert(0, str(src_dir))

from audit_pipeline.matching import get_style_value_and_source, create_matching_key

def test_rhythm_logic():
    print("=== Testing RHYTHM Style Matching Logic ===")
    
    # Test RHYTHM order record (should prioritize ALIAS/RELATED ITEM)
    print("\n1. RHYTHM Order Record (has ALIAS/RELATED ITEM):")
    rhythm_order = pd.Series({
        'Canonical_Customer': 'RHYTHM',
        'Customer': 'RHYTHM',
        'Customer_PO': '19200',
        'Style': None,  # Orders typically don't have Style for RHYTHM
        'ALIAS/RELATED ITEM': 'CLA24SW-BB04-BLK',
        'Color': 'BLACK',
        'Size': '06/XS'
    })
    
    style_value, style_source = get_style_value_and_source(rhythm_order, 'RHYTHM')
    print(f"   Style Value: '{style_value}'")
    print(f"   Style Source: '{style_source}'")
    print(f"   Expected: 'CLA24SW-BB04-BLK' from 'ALIAS/RELATED ITEM'")
    
    if style_value == 'CLA24SW-BB04-BLK' and style_source == 'ALIAS/RELATED ITEM':
        print("   ✅ CORRECT!")
    else:
        print("   ❌ WRONG!")
    
    # Test RHYTHM shipped record (has Style, no ALIAS/RELATED ITEM)
    print("\n2. RHYTHM Shipped Record (has Style, no ALIAS/RELATED ITEM):")
    rhythm_shipped = pd.Series({
        'Canonical_Customer': 'RHYTHM',
        'Customer': 'RHYTHM',
        'Customer_PO': '19200',
        'Style': 'CLA24SW-BB04-BLK',  # Shipped data has Style
        'ALIAS/RELATED ITEM': None,   # Shipped data doesn't have ALIAS/RELATED ITEM
        'Color': 'BLACK',
        'Size': '06/XS'
    })
    
    style_value, style_source = get_style_value_and_source(rhythm_shipped, 'RHYTHM')
    print(f"   Style Value: '{style_value}'")
    print(f"   Style Source: '{style_source}'")
    print(f"   Expected: 'CLA24SW-BB04-BLK' from 'Style' (fallback)")
    
    if style_value == 'CLA24SW-BB04-BLK' and style_source == 'Style':
        print("   ✅ CORRECT!")
    else:
        print("   ❌ WRONG!")
    
    # Test matching keys
    print("\n3. Matching Key Creation:")
    order_key = create_matching_key(rhythm_order, canonical_customer='RHYTHM')
    shipped_key = create_matching_key(rhythm_shipped, canonical_customer='RHYTHM')
    
    print(f"   Order Key:   '{order_key}'")
    print(f"   Shipped Key: '{shipped_key}'")
    print(f"   Keys Match:  {order_key == shipped_key}")
    
    if order_key == shipped_key:
        print("   ✅ KEYS MATCH - This should allow exact matching!")
    else:
        print("   ❌ KEYS DON'T MATCH - This is why RHYTHM isn't matching!")
    
    # Test standard customer (non-RHYTHM)
    print("\n4. Standard Customer (uses Style first):")
    standard_record = pd.Series({
        'Canonical_Customer': 'RHONE',
        'Customer': 'RHONE',
        'Customer_PO': 'TEST-PO',
        'Style': 'STANDARD-STYLE',
        'ALIAS/RELATED ITEM': 'ALIAS-ITEM',  # Should be ignored for standard customers
        'Color': 'BLUE',
        'Size': 'M'
    })
    
    style_value, style_source = get_style_value_and_source(standard_record, 'RHONE')
    print(f"   Style Value: '{style_value}'")
    print(f"   Style Source: '{style_source}'")
    print(f"   Expected: 'STANDARD-STYLE' from 'Style'")
    
    if style_value == 'STANDARD-STYLE' and style_source == 'Style':
        print("   ✅ CORRECT!")
    else:
        print("   ❌ WRONG!")

if __name__ == "__main__":
    test_rhythm_logic()
