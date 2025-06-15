#!/usr/bin/env python3
"""
Test Phase 2 - Customer-specific matching logic implementation
Tests enhanced matching functions with customer-specific style field configurations
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import pandas as pd
from audit_pipeline.config import get_customer_matching_config
from audit_pipeline.matching import (
    get_style_value_and_source, 
    create_matching_key, 
    create_alternate_matching_keys,
    add_match_keys,
    weighted_fuzzy_score
)

def test_enhanced_style_logic():
    """Test customer-specific style field selection logic"""
    print("=== Testing Enhanced Style Field Logic ===")
    
    # Test data for Rhythm customer (should use ALIAS/RELATED ITEM)
    rhythm_row = pd.Series({
        'Canonical_Customer': 'RHYTHM',
        'Style': None,  # No Style value
        'Pattern_ID': None,  # No Pattern_ID
        'ALIAS/RELATED ITEM': 'RHYTHM-ABC123',  # Has ALIAS/RELATED ITEM
        'Color': 'BLACK',
        'Size': 'M'
    })
    
    # Test data for standard customer (should use Style)
    rhone_row = pd.Series({
        'Canonical_Customer': 'RHONE',
        'Style': 'RHONE-XYZ456',  # Has Style value
        'Pattern_ID': 'PAT-789',  # Also has Pattern_ID
        'ALIAS/RELATED ITEM': 'ALT-ITEM',  # Also has ALIAS/RELATED ITEM
        'Color': 'BLUE',
        'Size': 'L'
    })
    
    # Test Rhythm customer style selection
    style_value, style_source = get_style_value_and_source(rhythm_row, 'RHYTHM')
    print(f"Rhythm - Style value: '{style_value}', Source: '{style_source}'")
    assert style_value == 'RHYTHM-ABC123', f"Expected 'RHYTHM-ABC123', got '{style_value}'"
    assert style_source == 'ALIAS/RELATED ITEM', f"Expected 'ALIAS/RELATED ITEM', got '{style_source}'"
    
    # Test standard customer style selection  
    style_value, style_source = get_style_value_and_source(rhone_row, 'RHONE')
    print(f"RHONE - Style value: '{style_value}', Source: '{style_source}'")
    assert style_value == 'RHONE-XYZ456', f"Expected 'RHONE-XYZ456', got '{style_value}'"
    assert style_source == 'Style', f"Expected 'Style', got '{style_source}'"
    
    print("✅ Enhanced style field logic tests passed!")
    

def test_enhanced_matching_keys():
    """Test customer-specific matching key creation"""
    print("\n=== Testing Enhanced Matching Key Creation ===")
    
    # Test data for Rhythm customer
    rhythm_row = pd.Series({
        'Canonical_Customer': 'RHYTHM',
        'Customer_PO': 'PO-RHYTHM-001',
        'Style': None,
        'Pattern_ID': None,
        'ALIAS/RELATED ITEM': 'RHYTHM-ABC123',
        'Color': 'BLACK',
        'Size': 'M'
    })
    
    # Test matching key creation for Rhythm
    key = create_matching_key(rhythm_row, include_size=True, canonical_customer='RHYTHM')
    print(f"Rhythm matching key: '{key}'")
    expected_parts = ['RHYTHM', 'PO-RHYTHM-001', 'RHYTHM-ABC123', 'BLACK', 'M']
    expected_key = '|'.join(expected_parts).upper()
    assert key == expected_key, f"Expected '{expected_key}', got '{key}'"
    
    # Test alternate keys for Rhythm
    primary_key, alt_key = create_alternate_matching_keys(rhythm_row, include_size=True, canonical_customer='RHYTHM')
    print(f"Rhythm primary key: '{primary_key}', alt key: '{alt_key}'")
    
    print("✅ Enhanced matching key creation tests passed!")


def test_enhanced_add_match_keys():
    """Test enhanced add_match_keys function with Style_Source tracking"""
    print("\n=== Testing Enhanced add_match_keys Function ===")
    
    # Create test dataframe with mixed customers
    test_df = pd.DataFrame([
        {
            'Canonical_Customer': 'RHYTHM',
            'Customer_PO': 'PO-RHYTHM-001',
            'Style': None,
            'Pattern_ID': None,
            'ALIAS/RELATED ITEM': 'RHYTHM-ABC123',
            'Color': 'BLACK',
            'Size': 'M',
            'Qty': 10
        },
        {
            'Canonical_Customer': 'RHONE',
            'Customer_PO': 'PO-RHONE-001',
            'Style': 'RHONE-XYZ456',
            'Pattern_ID': 'PAT-789',
            'ALIAS/RELATED ITEM': 'ALT-ITEM',
            'Color': 'BLUE',
            'Size': 'L',
            'Qty': 20
        }
    ])
    
    # Add match keys
    result_df = add_match_keys(test_df)
    
    # Check that Style_Source column was added and populated correctly
    assert 'Style_Source' in result_df.columns, "Style_Source column not found"
    
    rhythm_style_source = result_df[result_df['Canonical_Customer'] == 'RHYTHM']['Style_Source'].iloc[0]
    rhone_style_source = result_df[result_df['Canonical_Customer'] == 'RHONE']['Style_Source'].iloc[0]
    
    print(f"Rhythm Style_Source: '{rhythm_style_source}'")
    print(f"RHONE Style_Source: '{rhone_style_source}'")
    
    assert rhythm_style_source == 'ALIAS/RELATED ITEM', f"Expected 'ALIAS/RELATED ITEM', got '{rhythm_style_source}'"
    assert rhone_style_source == 'Style', f"Expected 'Style', got '{rhone_style_source}'"
    
    print("✅ Enhanced add_match_keys function tests passed!")


def test_enhanced_weighted_fuzzy_score():
    """Test enhanced weighted fuzzy score with customer-specific style logic"""
    print("\n=== Testing Enhanced Weighted Fuzzy Score ===")
    
    # Test data - similar products from different customers using different style fields
    row1 = pd.Series({
        'Canonical_Customer': 'RHYTHM',
        'Customer_PO': 'PO-RHYTHM-001',
        'Style': None,
        'Pattern_ID': None,
        'ALIAS/RELATED ITEM': 'SHARED-PRODUCT-123',
        'Color': 'BLACK',
        'Size': 'M'
    })
    
    row2 = pd.Series({
        'Canonical_Customer': 'RHYTHM',
        'Customer_PO': 'PO-RHYTHM-002',
        'Style': 'SHARED-PRODUCT-123',  # Same product, different field
        'Pattern_ID': None,
        'ALIAS/RELATED ITEM': None,
        'Color': 'BLACK',
        'Size': 'M'
    })
    
    # Test fuzzy score calculation
    score, score_breakdown = weighted_fuzzy_score(row1, row2, canonical_customer='RHYTHM')
    print(f"Fuzzy score: {score}")
    print(f"Score breakdown: {score_breakdown}")
    
    # Should have high style score since they match the same product
    assert score_breakdown['style'] > 90, f"Expected high style score, got {score_breakdown['style']}"
    
    print("✅ Enhanced weighted fuzzy score tests passed!")


def main():
    """Run all Phase 2 tests"""
    print("Starting Phase 2 Enhanced Matching Logic Tests...\n")
    
    try:
        test_enhanced_style_logic()
        test_enhanced_matching_keys()
        test_enhanced_add_match_keys()
        test_enhanced_weighted_fuzzy_score()
        
        print("\n🎉 All Phase 2 tests passed successfully!")
        print("✅ Customer-specific style field logic is working correctly")
        print("✅ Enhanced matching key creation supports customer configurations")  
        print("✅ Style_Source tracking is functioning properly")
        print("✅ Weighted fuzzy score handles customer-specific style fields")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
