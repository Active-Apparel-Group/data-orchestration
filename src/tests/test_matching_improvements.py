#!/usr/bin/env python3
"""
Quick test script to verify our matching.py improvements work correctly.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import pandas as pd
import numpy as np
from audit_pipeline.matching import (
    is_valid_po_value, 
    is_valid_po_series,
    field_exact_match,
    vectorized_field_exact_match,
    INVALID_PO_TOKENS,
    DEFAULT_FUZZY_WEIGHTS
)

def test_constants():
    """Test that our constants are properly defined."""
    print("Testing constants...")
    assert 'NULL' in INVALID_PO_TOKENS
    assert 'NONE' in INVALID_PO_TOKENS
    assert '' in INVALID_PO_TOKENS
    assert 'po' in DEFAULT_FUZZY_WEIGHTS
    print("✅ Constants test passed")

def test_po_validation():
    """Test PO validation functions."""
    print("Testing PO validation...")
    
    # Test scalar function
    assert is_valid_po_value("PO123") == True
    assert is_valid_po_value("NULL") == False
    assert is_valid_po_value("") == False
    assert is_valid_po_value(None) == False
    assert is_valid_po_value(np.nan) == False
    
    # Test vectorized function
    test_series = pd.Series(["PO123", "NULL", "", None, np.nan, "VALID_PO"])
    results = is_valid_po_series(test_series)
    expected = [True, False, False, False, False, True]
    assert results.tolist() == expected
    print("✅ PO validation test passed")

def test_field_matching():
    """Test field matching helper functions."""
    print("Testing field matching...")
    
    # Test scalar function
    assert field_exact_match("ABC", "abc") == True  # Case insensitive
    assert field_exact_match(" ABC ", "ABC") == True  # Whitespace trimming
    assert field_exact_match("ABC", "DEF") == False
    assert field_exact_match("", "ABC") == False  # Empty not matched
    assert field_exact_match(None, "ABC") == False
    
    # Test vectorized function
    series1 = pd.Series(["ABC", " DEF ", "", None, "GHI"])
    series2 = pd.Series(["abc", "def", "XYZ", "JKL", "ghi"])
    results = vectorized_field_exact_match(series1, series2)
    expected = [True, True, False, False, True]
    assert results.tolist() == expected
    print("✅ Field matching test passed")

def test_mock_matching_data():
    """Test with mock data to ensure our changes work with real DataFrames."""
    print("Testing with mock data...")
    
    # Create mock data
    data = {
        'Canonical_Customer': ['CUSTOMER_A', 'CUSTOMER_B', 'CUSTOMER_C'],
        'Customer_PO': ['PO123', 'NULL', 'PO789'],
        'Customer_Alt_PO': ['ALT456', 'ALT_VALID', ''],
        'Style': ['STYLE1', '', 'STYLE3'],
        'Color': ['RED', 'BLUE', 'GREEN'],
        'Size': ['M', 'L', 'S']
    }
    df = pd.DataFrame(data)
    
    # Test vectorized PO validation
    valid_po = is_valid_po_series(df['Customer_PO'])
    valid_alt_po = is_valid_po_series(df['Customer_Alt_PO'])
    
    assert valid_po.tolist() == [True, False, True]
    assert valid_alt_po.tolist() == [True, True, False]
    
    print("✅ Mock data test passed")

if __name__ == "__main__":
    print("Running matching.py improvement tests...\n")
    
    try:
        test_constants()
        test_po_validation()
        test_field_matching()
        test_mock_matching_data()
        
        print("\n🎉 All tests passed! The matching.py improvements are working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
