#!/usr/bin/env python3
"""
Phase 3 - Integration Testing for Customer-Specific Matching Logic (FIXED)
Tests the complete end-to-end pipeline with realistic data scenarios
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import pandas as pd
import numpy as np
from audit_pipeline.config import get_customer_matching_config
from audit_pipeline.matching import (
    match_records,
    aggregate_quantities,
    exact_match,
    fuzzy_match,
    add_match_keys,
    get_style_value_and_source
)

def create_realistic_rhythm_data():
    """Create realistic test data that mimics actual Rhythm customer data structure"""
    
    # Rhythm Packed Data - uses ALIAS/RELATED ITEM field
    packed_data = pd.DataFrame([
        {
            'Canonical_Customer': 'RHYTHM',
            'Customer': 'Rhythm',
            'Customer_PO': 'RHYTHM-PO-2024-001',
            'Customer_Alt_PO': '',
            'Style': '',  # Rhythm doesn't use Style field
            'Pattern_ID': '',  # Rhythm doesn't use Pattern_ID
            'ALIAS/RELATED ITEM': 'RHY-BOARD-SHORT-001',
            'Color': 'NAVY',
            'Size': 'M',
            'Qty': 25
        },
        {
            'Canonical_Customer': 'RHYTHM',
            'Customer': 'Rhythm',
            'Customer_PO': 'RHYTHM-PO-2024-001',
            'Customer_Alt_PO': '',
            'Style': '',
            'Pattern_ID': '',
            'ALIAS/RELATED ITEM': 'RHY-BOARD-SHORT-001',
            'Color': 'NAVY',
            'Size': 'L',
            'Qty': 30
        },
        {
            'Canonical_Customer': 'RHYTHM',
            'Customer': 'Rhythm',
            'Customer_PO': '',
            'Customer_Alt_PO': 'RHYTHM-ALT-2024-002',
            'Style': '',
            'Pattern_ID': '',
            'ALIAS/RELATED ITEM': 'RHY-TANK-TOP-002',
            'Color': 'WHITE',
            'Size': 'S',
            'Qty': 15
        },
        {
            'Canonical_Customer': 'RHYTHM',
            'Customer': 'Rhythm',
            'Customer_PO': 'RHYTHM-PO-2024-003',
            'Customer_Alt_PO': '',
            'Style': '',
            'Pattern_ID': '',
            'ALIAS/RELATED ITEM': 'RHY-SWIM-BRA-003',
            'Color': 'BLACK',
            'Size': 'M',
            'Qty': 20
        }
    ])
    
    # Rhythm Shipped Data - similar structure
    shipped_data = pd.DataFrame([
        {
            'Canonical_Customer': 'RHYTHM',
            'Customer': 'Rhythm',
            'Customer_PO': 'RHYTHM-PO-2024-001',
            'Customer_Alt_PO': '',
            'Style': '',
            'Pattern_ID': '',
            'ALIAS/RELATED ITEM': 'RHY-BOARD-SHORT-001',
            'Color': 'NAVY',
            'Size': 'M',
            'Qty': 20  # Partial shipment
        },
        {
            'Canonical_Customer': 'RHYTHM',
            'Customer': 'Rhythm',
            'Customer_PO': 'RHYTHM-PO-2024-001',
            'Customer_Alt_PO': '',
            'Style': '',
            'Pattern_ID': '',
            'ALIAS/RELATED ITEM': 'RHY-BOARD-SHORT-001',
            'Color': 'NAVY',
            'Size': 'L',
            'Qty': 30  # Full shipment
        },
        {
            'Canonical_Customer': 'RHYTHM',
            'Customer': 'Rhythm',
            'Customer_PO': 'RHYTHM-PO-2024-004',  # Different PO in shipped
            'Customer_Alt_PO': '',
            'Style': '',
            'Pattern_ID': '',
            'ALIAS/RELATED ITEM': 'RHYTHM-SLIGHTLY-DIFFERENT-NAME',  # Slight variation for fuzzy matching
            'Color': 'WHITE',
            'Size': 'S',
            'Qty': 15
        }
    ])
    
    # Rhythm Orders Data - what was actually ordered
    orders_data = pd.DataFrame([
        {
            'Canonical_Customer': 'RHYTHM',
            'Customer': 'Rhythm',
            'Customer_PO': 'RHYTHM-PO-2024-001',
            'Customer_Alt_PO': '',
            'Style': '',
            'Pattern_ID': '',
            'ALIAS/RELATED ITEM': 'RHY-BOARD-SHORT-001',
            'Color': 'NAVY',
            'Size': 'M',
            'Ordered_Qty': 25
        },
        {
            'Canonical_Customer': 'RHYTHM',
            'Customer': 'Rhythm',
            'Customer_PO': 'RHYTHM-PO-2024-001',
            'Customer_Alt_PO': '',
            'Style': '',
            'Pattern_ID': '',
            'ALIAS/RELATED ITEM': 'RHY-BOARD-SHORT-001',
            'Color': 'NAVY',
            'Size': 'L',
            'Ordered_Qty': 30
        },
        {
            'Canonical_Customer': 'RHYTHM',
            'Customer': 'Rhythm',
            'Customer_PO': '',
            'Customer_Alt_PO': 'RHYTHM-ALT-2024-002',  # Matches Alt_PO from packed data
            'Style': '',
            'Pattern_ID': '',
            'ALIAS/RELATED ITEM': 'RHY-TANK-TOP-002',
            'Color': 'WHITE',
            'Size': 'S',
            'Ordered_Qty': 15
        },
        {
            'Canonical_Customer': 'RHYTHM',
            'Customer': 'Rhythm',
            'Customer_PO': 'RHYTHM-PO-2024-003',
            'Customer_Alt_PO': '',
            'Style': '',
            'Pattern_ID': '',
            'ALIAS/RELATED ITEM': 'RHY-SWIM-BRA-003',
            'Color': 'BLACK',
            'Size': 'M',
            'Ordered_Qty': 20
        },
        {
            'Canonical_Customer': 'RHYTHM',
            'Customer': 'Rhythm',
            'Customer_PO': '',
            'Customer_Alt_PO': 'RHYTHM-ALT-2024-002',
            'Style': '',
            'Pattern_ID': '',
            'ALIAS/RELATED ITEM': 'RHYTHM-SLIGHTLY-DIFFERENT-NAME',  # For fuzzy matching test
            'Color': 'WHITE',
            'Size': 'S',
            'Ordered_Qty': 15
        }
    ])
    
    return packed_data, shipped_data, orders_data

def create_mixed_customer_data():
    """Create test data mixing Rhythm and standard customers"""
    
    # Mixed Packed Data
    packed_data = pd.DataFrame([
        # Rhythm data
        {
            'Canonical_Customer': 'RHYTHM',
            'Customer': 'Rhythm',
            'Customer_PO': 'RHYTHM-MIX-001',
            'Customer_Alt_PO': '',
            'Style': '',
            'Pattern_ID': '',
            'ALIAS/RELATED ITEM': 'RHY-MIXED-PRODUCT-A',
            'Color': 'BLUE',
            'Size': 'M',
            'Qty': 50
        },
        # RHONE data (standard customer)
        {
            'Canonical_Customer': 'RHONE',
            'Customer': 'Rhone',
            'Customer_PO': 'RHONE-MIX-001',
            'Customer_Alt_PO': '',
            'Style': 'RHONE-STYLE-MIXED-001',
            'Pattern_ID': 'RHONE-PATTERN-001',
            'ALIAS/RELATED ITEM': '',
            'Color': 'GREEN',
            'Size': 'L',
            'Qty': 30
        }
    ])
    
    # Mixed Shipped Data  
    shipped_data = pd.DataFrame([
        # Rhythm data
        {
            'Canonical_Customer': 'RHYTHM',
            'Customer': 'Rhythm',
            'Customer_PO': 'RHYTHM-MIX-001',
            'Customer_Alt_PO': '',
            'Style': '',
            'Pattern_ID': '',
            'ALIAS/RELATED ITEM': 'RHY-MIXED-PRODUCT-A',
            'Color': 'BLUE',
            'Size': 'M',
            'Qty': 50
        },
        # RHONE data
        {
            'Canonical_Customer': 'RHONE',
            'Customer': 'Rhone',
            'Customer_PO': 'RHONE-MIX-001',
            'Customer_Alt_PO': '',
            'Style': 'RHONE-STYLE-MIXED-001',
            'Pattern_ID': 'RHONE-PATTERN-001',
            'ALIAS/RELATED ITEM': '',
            'Color': 'GREEN',
            'Size': 'L',
            'Qty': 25  # Partial shipment
        }
    ])
    
    # Mixed Orders Data
    orders_data = pd.DataFrame([
        # Rhythm data
        {
            'Canonical_Customer': 'RHYTHM',
            'Customer': 'Rhythm',
            'Customer_PO': 'RHYTHM-MIX-001',
            'Customer_Alt_PO': '',
            'Style': '',
            'Pattern_ID': '',
            'ALIAS/RELATED ITEM': 'RHY-MIXED-PRODUCT-A',
            'Color': 'BLUE',
            'Size': 'M',
            'Ordered_Qty': 50
        },
        # RHONE data
        {
            'Canonical_Customer': 'RHONE',
            'Customer': 'Rhone',
            'Customer_PO': 'RHONE-MIX-001',
            'Customer_Alt_PO': '',
            'Style': 'RHONE-STYLE-MIXED-001',
            'Pattern_ID': 'RHONE-PATTERN-001',
            'ALIAS/RELATED ITEM': '',
            'Color': 'GREEN',
            'Size': 'L',
            'Ordered_Qty': 30
        }
    ])
    
    return packed_data, shipped_data, orders_data

def create_large_dataset():
    """Create a larger dataset for performance testing"""
    
    rhythm_records = []
    rhone_records = []
    
    # Create 100 Rhythm records
    for i in range(100):
        rhythm_records.append({
            'Canonical_Customer': 'RHYTHM',
            'Customer': 'Rhythm',
            'Customer_PO': f'RHYTHM-PERF-{i:03d}',
            'Customer_Alt_PO': '',
            'Style': '',
            'Pattern_ID': '',
            'ALIAS/RELATED ITEM': f'RHY-PERF-ITEM-{i:03d}',
            'Color': ['BLACK', 'WHITE', 'NAVY', 'GREY'][i % 4],
            'Size': ['XS', 'S', 'M', 'L', 'XL'][i % 5],
            'Qty': (i % 50) + 10
        })
    
    # Create 100 RHONE records  
    for i in range(100):
        rhone_records.append({
            'Canonical_Customer': 'RHONE',
            'Customer': 'Rhone',
            'Customer_PO': f'RHONE-PERF-{i:03d}',
            'Customer_Alt_PO': '',
            'Style': f'RHONE-PERF-STYLE-{i:03d}',
            'Pattern_ID': f'RHONE-PERF-PATTERN-{i:03d}',
            'ALIAS/RELATED ITEM': '',
            'Color': ['RED', 'BLUE', 'GREEN', 'YELLOW'][i % 4],
            'Size': ['XS', 'S', 'M', 'L', 'XL'][i % 5],
            'Qty': (i % 30) + 5
        })
    
    # Combine and create DataFrames
    all_records = rhythm_records + rhone_records
    
    packed_data = pd.DataFrame(all_records)
    shipped_data = pd.DataFrame(all_records)  # Same data for simplicity
    orders_data = pd.DataFrame([{**record, 'Ordered_Qty': record['Qty']} for record in all_records])
    
    return packed_data, shipped_data, orders_data

def test_rhythm_end_to_end():
    """Test complete end-to-end pipeline with realistic Rhythm data"""
    print("=== Testing Rhythm End-to-End Pipeline ===")
    
    packed_data, shipped_data, orders_data = create_realistic_rhythm_data()
    
    print(f"Test data: {len(packed_data)} packed, {len(shipped_data)} shipped, {len(orders_data)} orders")
    
    # Run the complete matching pipeline
    results_df, summary_df = match_records(packed_data, shipped_data, orders_data, threshold=75)
    
    print(f"Results: {len(results_df)} matched records")
    
    # Check that Rhythm data uses ALIAS/RELATED ITEM field
    rhythm_results = results_df[results_df['Canonical_Customer'] == 'RHYTHM']
    
    if len(rhythm_results) > 0:
        style_source = rhythm_results['Style_Source'].iloc[0]
        print(f"Rhythm customer uses style field: {style_source}")
        
        assert style_source == 'ALIAS/RELATED ITEM', f"Expected 'ALIAS/RELATED ITEM', got '{style_source}'"
        
        # Check specific matches
        po_matches = rhythm_results[rhythm_results['Customer_PO'] == 'RHYTHM-PO-2024-001']
        alt_po_matches = rhythm_results[rhythm_results['Customer_Alt_PO'] == 'RHYTHM-ALT-2024-002']
        
        print(f"PO matches: {len(po_matches)}, Alt PO matches: {len(alt_po_matches)}")
        
        assert len(po_matches) > 0, "Should have PO-based matches"
        assert len(alt_po_matches) > 0, "Should have Alt_PO-based matches"
        
        print("✅ Rhythm end-to-end test passed!")
    else:
        print("❌ No Rhythm results found")
        assert False, "No Rhythm results found in pipeline output"

def test_mixed_customer_integration():
    """Test integration with mixed customer types in same dataset"""
    print("\n=== Testing Mixed Customer Integration ===")
    
    packed_data, shipped_data, orders_data = create_mixed_customer_data()
    
    # Run matching pipeline
    results_df, summary_df = match_records(packed_data, shipped_data, orders_data, threshold=75)
    
    # Check that different customers use different style fields
    rhythm_results = results_df[results_df['Canonical_Customer'] == 'RHYTHM']
    rhone_results = results_df[results_df['Canonical_Customer'] == 'RHONE']
    
    rhythm_style_source = rhythm_results['Style_Source'].iloc[0] if len(rhythm_results) > 0 else None
    rhone_style_source = rhone_results['Style_Source'].iloc[0] if len(rhone_results) > 0 else None
    
    print(f"Mixed dataset - Rhythm uses: {rhythm_style_source}, RHONE uses: {rhone_style_source}")
    
    assert rhythm_style_source == 'ALIAS/RELATED ITEM', "Rhythm should use ALIAS/RELATED ITEM in mixed dataset"
    assert rhone_style_source == 'Style', "RHONE should use Style field in mixed dataset"
    
    print("✅ Mixed customer integration test passed!")

def test_performance_with_larger_dataset():
    """Test performance with larger dataset"""
    print("\n=== Testing Performance with Larger Dataset ===")
    
    import time
    
    packed_data, shipped_data, orders_data = create_large_dataset()
    
    print(f"Large dataset: {len(packed_data)} packed, {len(shipped_data)} shipped, {len(orders_data)} orders")
    
    start_time = time.time()
    results_df, summary_df = match_records(packed_data, shipped_data, orders_data, threshold=75)
    end_time = time.time()
    
    processing_time = end_time - start_time
    print(f"Processing time: {processing_time:.2f} seconds")
    print(f"Records processed per second: {len(packed_data) / processing_time:.2f}")
    
    # Check that both customer types are processed correctly
    rhythm_count = len(results_df[results_df['Canonical_Customer'] == 'RHYTHM'])
    rhone_count = len(results_df[results_df['Canonical_Customer'] == 'RHONE'])
    
    print(f"Results: {rhythm_count} Rhythm records, {rhone_count} RHONE records")
    
    assert rhythm_count > 0, "Should have Rhythm results in large dataset"
    assert rhone_count > 0, "Should have RHONE results in large dataset"
    assert processing_time < 30, f"Processing should complete in under 30 seconds, took {processing_time:.2f}s"
    
    print("✅ Performance test passed!")

def test_edge_cases():
    """Test various edge cases"""
    print("\n=== Testing Edge Cases ===")
    
    # Test with minimal data
    minimal_packed = pd.DataFrame([{
        'Canonical_Customer': 'RHYTHM',
        'Customer': 'Rhythm',
        'Customer_PO': 'RHYTHM-MINIMAL-001',
        'Customer_Alt_PO': '',
        'Style': '',
        'Pattern_ID': '',
        'ALIAS/RELATED ITEM': 'MINIMAL-ITEM',
        'Color': 'BLACK',
        'Size': 'M',
        'Qty': 1
    }])
    
    minimal_shipped = minimal_packed.copy()
    minimal_orders = minimal_packed.copy()
    minimal_orders['Ordered_Qty'] = minimal_orders['Qty']
    
    results_df, summary_df = match_records(minimal_packed, minimal_shipped, minimal_orders, threshold=75)
    
    assert len(results_df) > 0, "Should handle minimal dataset"
    assert results_df['Style_Source'].iloc[0] == 'ALIAS/RELATED ITEM', "Should use correct style field for minimal data"
    
    print("✅ Edge cases test passed!")

if __name__ == "__main__":
    # Run all tests
    try:
        test_rhythm_end_to_end()
        test_mixed_customer_integration()
        test_performance_with_larger_dataset()
        test_edge_cases()
        print("\n🎉 All Phase 3 integration tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
