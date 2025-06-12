#!/usr/bin/env python3
"""
Regression Testing for Customer-Specific Matching Logic
Tests that existing customers still work correctly after Phase 2 enhancements.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import pandas as pd
from audit_pipeline.config import get_customer_matching_config
from audit_pipeline.matching import (
    get_style_value_and_source,
    create_matching_key,
    create_alternate_matching_keys,
    add_match_keys,
    weighted_fuzzy_score,
    exact_match,
    fuzzy_match,
    aggregate_quantities
)

def test_standard_customers():
    """Test that standard customers (RHONE, PELOTON, etc.) still work correctly"""
    print("\n=== Testing Standard Customer Behavior ===")
    
    # Test multiple standard customers
    standard_customers = ['RHONE', 'PELOTON', 'GREYSON', 'TRACK_SMITH']
    
    for customer in standard_customers:
        # Test config loading
        config = get_customer_matching_config(customer)
        assert config['style_match_strategy'] == 'standard', f"{customer} should use standard strategy"
        assert config['style_field_name'] == 'Style', f"{customer} should use Style field"
        
        # Test style field logic
        test_row = pd.Series({
            'Canonical_Customer': customer,
            'Style': f'{customer}-STYLE123',
            'Pattern_ID': f'{customer}-PATTERN456',
            'Color': 'BLUE',
            'Size': 'L',
            'Customer_PO': f'PO-{customer}-001',
            'Customer_Alt_PO': f'ALT-{customer}-001'
        })
        
        style_value, style_source = get_style_value_and_source(test_row, customer)
        assert style_value == f'{customer}-STYLE123', f"{customer} should use Style field value"
        assert style_source == 'Style', f"{customer} should report Style as source"
        
        # Test matching key creation
        matching_key = create_matching_key(test_row, canonical_customer=customer)
        expected_key = f'{customer}|PO-{customer}-001|{customer}-STYLE123|BLUE|L'
        assert matching_key == expected_key, f"{customer} matching key mismatch"
        
        print(f"✅ {customer} - Standard behavior verified")
    
    print("✅ All standard customers working correctly!")

def test_pattern_id_fallback():
    """Test that Pattern_ID fallback works for all customer types"""
    print("\n=== Testing Pattern_ID Fallback Logic ===")
    
    customers = ['RHONE', 'RHYTHM', 'PELOTON']
    
    for customer in customers:
        # Test row with no Style but has Pattern_ID
        test_row = pd.Series({
            'Canonical_Customer': customer,
            'Style': None,  # No Style field
            'Pattern_ID': f'{customer}-PATTERN789',
            'Color': 'RED',
            'Size': 'M',
            'Customer_PO': f'PO-{customer}-002'
        })
        
        style_value, style_source = get_style_value_and_source(test_row, customer)
        assert style_value == f'{customer}-PATTERN789', f"{customer} should fallback to Pattern_ID"
        assert style_source == 'Pattern_ID', f"{customer} should report Pattern_ID as source"
        
        print(f"✅ {customer} - Pattern_ID fallback verified")
    
    print("✅ Pattern_ID fallback working correctly for all customers!")

def test_cross_field_po_matching():
    """Test that cross-field PO matching still works correctly"""
    print("\n=== Testing Cross-Field PO Matching ===")
    
    # Create test data for cross-field matching
    packed_data = pd.DataFrame([
        {
            'Canonical_Customer': 'RHONE',
            'Customer': 'RHONE',
            'Customer_PO': 'PO-123',
            'Customer_Alt_PO': None,
            'Style': 'RHONE-STYLE-A',
            'Pattern_ID': None,
            'Color': 'BLACK',
            'Size': 'M',
            'Qty': 10
        }
    ])
    
    shipped_data = pd.DataFrame([
        {
            'Canonical_Customer': 'RHONE',
            'Customer': 'RHONE',
            'Customer_PO': None,
            'Customer_Alt_PO': 'PO-123',  # Same PO in Alt field
            'Style': 'RHONE-STYLE-A',
            'Pattern_ID': None,
            'Color': 'BLACK',
            'Size': 'M',
            'Qty': 5
        }
    ])
    
    orders_data = pd.DataFrame([
        {
            'Canonical_Customer': 'RHONE',
            'Customer': 'RHONE',
            'Customer_PO': 'PO-123',
            'Customer_Alt_PO': None,
            'Style': 'RHONE-STYLE-A',
            'Pattern_ID': None,
            'Color': 'BLACK',
            'Size': 'M',
            'Ordered_Qty': 15
        }
    ])
    
    # Aggregate and match
    combined = aggregate_quantities(packed_data, shipped_data)
    matched_results, unmatched, orders_with_keys = exact_match(combined, orders_data)
    
    # Should find exact matches via cross-field PO matching
    exact_matches = matched_results[matched_results['Match_Type'] == 'EXACT']
    assert len(exact_matches) > 0, "Should find cross-field PO matches"
    
    # Check that Alt_PO field was identified as the matching field
    match_fields = exact_matches['Best_Match_Field'].unique()
    assert 'Alt_PO' in match_fields or 'PO' in match_fields, "Should identify PO match field"
    
    print("✅ Cross-field PO matching verified")

def test_rhythm_alias_field():
    """Test that Rhythm customer uses ALIAS/RELATED ITEM field correctly"""
    print("\n=== Testing Rhythm ALIAS/RELATED ITEM Field ===")
    
    # Test Rhythm with ALIAS/RELATED ITEM field
    rhythm_row = pd.Series({
        'Canonical_Customer': 'RHYTHM',
        'Style': None,  # No Style
        'Pattern_ID': None,  # No Pattern_ID
        'ALIAS/RELATED ITEM': 'RHYTHM-ALIAS-999',
        'Color': 'WHITE',
        'Size': 'S',
        'Customer_PO': 'PO-RHYTHM-999'
    })
    
    style_value, style_source = get_style_value_and_source(rhythm_row, 'RHYTHM')
    assert style_value == 'RHYTHM-ALIAS-999', "Rhythm should use ALIAS/RELATED ITEM field"
    assert style_source == 'ALIAS/RELATED ITEM', "Rhythm should report ALIAS/RELATED ITEM as source"
    
    # Test matching key creation
    matching_key = create_matching_key(rhythm_row, canonical_customer='RHYTHM')
    expected_key = 'RHYTHM|PO-RHYTHM-999|RHYTHM-ALIAS-999|WHITE|S'
    assert matching_key == expected_key, "Rhythm matching key should use ALIAS/RELATED ITEM"
    
    print("✅ Rhythm ALIAS/RELATED ITEM field verified")

def test_mixed_customer_matching():
    """Test matching between different customer types"""
    print("\n=== Testing Mixed Customer Matching ===")
    
    # Create datasets with different customers
    mixed_data = pd.DataFrame([
        {
            'Canonical_Customer': 'RHONE',
            'Customer': 'RHONE',
            'Customer_PO': 'PO-RHONE-001',
            'Customer_Alt_PO': None,
            'Style': 'RHONE-STYLE-001',
            'Pattern_ID': None,
            'Color': 'BLUE',
            'Size': 'L',
            'Packed_Qty': 10,
            'Shipped_Qty': 0,
            'Source_Type': 'PACKED'
        },
        {
            'Canonical_Customer': 'RHYTHM',
            'Customer': 'RHYTHM',
            'Customer_PO': 'PO-RHYTHM-001',
            'Customer_Alt_PO': None,
            'Style': None,
            'Pattern_ID': None,
            'ALIAS/RELATED ITEM': 'RHYTHM-ALIAS-001',
            'Color': 'RED',
            'Size': 'M',
            'Packed_Qty': 5,
            'Shipped_Qty': 3,
            'Source_Type': 'PACKED,SHIPPED'
        }
    ])
    
    # Add match keys
    mixed_with_keys = add_match_keys(mixed_data)
    
    # Verify Style_Source tracking
    rhone_source = mixed_with_keys[mixed_with_keys['Canonical_Customer'] == 'RHONE']['Style_Source'].iloc[0]
    rhythm_source = mixed_with_keys[mixed_with_keys['Canonical_Customer'] == 'RHYTHM']['Style_Source'].iloc[0]
    
    assert rhone_source == 'Style', "RHONE should use Style field"
    assert rhythm_source == 'ALIAS/RELATED ITEM', "RHYTHM should use ALIAS/RELATED ITEM field"
    
    print("✅ Mixed customer matching verified")

def test_weighted_fuzzy_score_regression():
    """Test that weighted fuzzy score works correctly for all customer types"""
    print("\n=== Testing Weighted Fuzzy Score Regression ===")
    
    # Test standard customer fuzzy matching
    rhone_row1 = pd.Series({
        'Canonical_Customer': 'RHONE',
        'Customer_PO': 'PO-RHONE-FUZZY',
        'Customer_Alt_PO': None,
        'Style': 'RHONE-FUZZY-STYLE',
        'Pattern_ID': None,
        'Color': 'NAVY',
        'Size': 'XL'
    })
    
    rhone_row2 = pd.Series({
        'Canonical_Customer': 'RHONE',
        'Customer_PO': 'PO-RHONE-FUZY',  # Slight typo for fuzzy test
        'Customer_Alt_PO': None,
        'Style': 'RHONE-FUZZY-STYL',  # Slight difference
        'Pattern_ID': None,
        'Color': 'NAVY',
        'Size': 'XL'
    })
    
    score, breakdown = weighted_fuzzy_score(rhone_row1, rhone_row2, canonical_customer='RHONE')
    assert score > 80, f"RHONE fuzzy score should be high, got {score}"
    assert 'po' in breakdown and 'style' in breakdown, "Should have PO and style scores"
    
    # Test Rhythm customer fuzzy matching
    rhythm_row1 = pd.Series({
        'Canonical_Customer': 'RHYTHM',
        'Customer_PO': 'PO-RHYTHM-FUZZY',
        'Customer_Alt_PO': None,
        'Style': None,
        'Pattern_ID': None,
        'ALIAS/RELATED ITEM': 'RHYTHM-ALIAS-FUZZY',
        'Color': 'GREEN',
        'Size': 'S'
    })
    
    rhythm_row2 = pd.Series({
        'Canonical_Customer': 'RHYTHM',
        'Customer_PO': 'PO-RHYTHM-FUZY',  # Slight typo
        'Customer_Alt_PO': None,
        'Style': None,
        'Pattern_ID': None,
        'ALIAS/RELATED ITEM': 'RHYTHM-ALIAS-FUZY',  # Slight difference
        'Color': 'GREEN',
        'Size': 'S'
    })
    
    score, breakdown = weighted_fuzzy_score(rhythm_row1, rhythm_row2, canonical_customer='RHYTHM')
    assert score > 80, f"RHYTHM fuzzy score should be high, got {score}"
    
    print("✅ Weighted fuzzy score regression verified")

def main():
    """Run all regression tests"""
    print("🔄 Starting Regression Tests for Customer-Specific Matching Logic...")
    
    try:
        test_standard_customers()
        test_pattern_id_fallback()
        test_cross_field_po_matching()
        test_rhythm_alias_field()
        test_mixed_customer_matching()
        test_weighted_fuzzy_score_regression()
        
        print("\n🎉 All Regression Tests Passed Successfully!")
        print("✅ Existing functionality preserved")
        print("✅ New customer-specific logic working correctly")
        print("✅ Cross-field PO matching still functional")
        print("✅ Pattern_ID fallback logic intact")
        print("✅ Mixed customer scenarios handled properly")
        
    except Exception as e:
        print(f"\n❌ Regression Test Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
