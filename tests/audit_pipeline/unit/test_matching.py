import sys
import os
import pandas as pd

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from audit_pipeline.matching import is_valid_po_value, create_matching_key, create_alternate_matching_keys

def test_dummy():
    assert 1 == 1

def test_is_valid_po_value():
    """Test the is_valid_po_value function with various inputs."""
    # Valid PO values
    assert is_valid_po_value("4053") == True
    assert is_valid_po_value("PO123") == True
    assert is_valid_po_value(12345) == True
    
    # Invalid PO values
    assert is_valid_po_value("NONE") == False
    assert is_valid_po_value("NULL") == False
    assert is_valid_po_value("NAN") == False
    assert is_valid_po_value("") == False
    assert is_valid_po_value("   ") == False
    assert is_valid_po_value(None) == False
    assert is_valid_po_value(pd.NA) == False
    
    # Case insensitive
    assert is_valid_po_value("none") == False
    assert is_valid_po_value("null") == False
    assert is_valid_po_value("N/A") == False

def test_create_matching_key_with_none_values():
    """Test that matching keys exclude NONE values properly."""
    
    # Test row with NONE values
    row_with_none = {
        'Canonical_Customer': 'GREYSON',
        'Customer_PO': 'NONE',
        'Customer_Alt_PO': '4053',
        'Style': 'LSP25A16',
        'Color': '867 - CAMP',
        'Size': 'ONESIZE'
    }
    
    # Should use Alt_PO since PO is NONE
    key = create_matching_key(row_with_none)
    expected = 'GREYSON|4053|LSP25A16|867 - CAMP|ONESIZE'
    assert key == expected, f"Expected {expected}, got {key}"
    
    # Test row where both PO fields are NONE
    row_both_none = {
        'Canonical_Customer': 'GREYSON',
        'Customer_PO': 'NONE',
        'Customer_Alt_PO': 'NONE',
        'Style': 'LSP25A16',
        'Color': '867 - CAMP',
        'Size': 'ONESIZE'
    }
    
    # Should create key without PO
    key = create_matching_key(row_both_none)
    expected = 'GREYSON|LSP25A16|867 - CAMP|ONESIZE'
    assert key == expected, f"Expected {expected}, got {key}"

def test_create_alternate_matching_keys_with_none():
    """Test that alternate matching keys handle NONE values properly."""
    
    row = {
        'Canonical_Customer': 'GREYSON',
        'Customer_PO': 'NONE',
        'Customer_Alt_PO': '4053',
        'Style': 'LSP25A16',
        'Color': '867 - CAMP',
        'Size': 'ONESIZE'
    }
    
    primary_key, alt_key = create_alternate_matching_keys(row)
    
    # Primary key should be None since Customer_PO is NONE
    assert primary_key is None, f"Expected None for primary key, got {primary_key}"
    
    # Alt key should be valid since Customer_Alt_PO is valid
    expected_alt = 'GREYSON|LSP25A16|867 - CAMP|ONESIZE|4053'
    assert alt_key == expected_alt, f"Expected {expected_alt}, got {alt_key}"

if __name__ == "__main__":
    test_is_valid_po_value()
    test_create_matching_key_with_none_values()
    test_create_alternate_matching_keys_with_none()
    print("All tests passed!")
