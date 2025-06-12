#!/usr/bin/env python3
"""
Phase 3 - Integration Testing for Customer-Specific Matching Logic
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
            'Customer_Alt_PO': None,            'Style': '',  # Rhythm doesn't use Style field
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
            'Customer_Alt_PO': None,
            'Style': None,
            'Pattern_ID': None,
            'ALIAS/RELATED ITEM': 'RHY-BOARD-SHORT-001',
            'Color': 'NAVY',
            'Size': 'L',
            'Qty': 30
        },
        {
            'Canonical_Customer': 'RHYTHM',
            'Customer': 'Rhythm',
            'Customer_PO': None,
            'Customer_Alt_PO': 'RHYTHM-ALT-2024-002',
            'Style': None,
            'Pattern_ID': None,
            'ALIAS/RELATED ITEM': 'RHY-TANK-TOP-002',
            'Color': 'WHITE',
            'Size': 'S',
            'Qty': 15
        },
        {
            'Canonical_Customer': 'RHYTHM',
            'Customer': 'Rhythm',
            'Customer_PO': 'RHYTHM-PO-2024-003',
            'Customer_Alt_PO': None,
            'Style': None,
            'Pattern_ID': None,
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
            'Customer_Alt_PO': None,
            'Style': None,
            'Pattern_ID': None,
            'ALIAS/RELATED ITEM': 'RHY-BOARD-SHORT-001',
            'Color': 'NAVY',
            'Size': 'M',
            'Qty': 20  # Partial shipment
        },
        {
            'Canonical_Customer': 'RHYTHM',
            'Customer': 'Rhythm',
            'Customer_PO': 'RHYTHM-PO-2024-001',
            'Customer_Alt_PO': None,
            'Style': None,
            'Pattern_ID': None,
            'ALIAS/RELATED ITEM': 'RHY-BOARD-SHORT-001',
            'Color': 'NAVY',
            'Size': 'L',
            'Qty': 30  # Full shipment
        },
        {
            'Canonical_Customer': 'RHYTHM',
            'Customer': 'Rhythm',
            'Customer_PO': 'RHYTHM-PO-2024-004',  # Different PO in shipped
            'Customer_Alt_PO': None,
            'Style': None,
            'Pattern_ID': None,
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
            'Customer_Alt_PO': None,
            'Style': None,
            'Pattern_ID': None,
            'ALIAS/RELATED ITEM': 'RHY-BOARD-SHORT-001',
            'Color': 'NAVY',
            'Size': 'M',
            'Ordered_Qty': 25
        },
        {
            'Canonical_Customer': 'RHYTHM',
            'Customer': 'Rhythm',
            'Customer_PO': 'RHYTHM-PO-2024-001',
            'Customer_Alt_PO': None,
            'Style': None,
            'Pattern_ID': None,
            'ALIAS/RELATED ITEM': 'RHY-BOARD-SHORT-001',
            'Color': 'NAVY',
            'Size': 'L',
            'Ordered_Qty': 30
        },
        {
            'Canonical_Customer': 'RHYTHM',
            'Customer': 'Rhythm',
            'Customer_PO': None,
            'Customer_Alt_PO': 'RHYTHM-ALT-2024-002',  # Matches Alt_PO from packed data
            'Style': None,
            'Pattern_ID': None,
            'ALIAS/RELATED ITEM': 'RHY-TANK-TOP-002',
            'Color': 'WHITE',
            'Size': 'S',
            'Ordered_Qty': 15
        },
        {
            'Canonical_Customer': 'RHYTHM',
            'Customer': 'Rhythm',
            'Customer_PO': 'RHYTHM-PO-2024-003',
            'Customer_Alt_PO': None,
            'Style': None,
            'Pattern_ID': None,
            'ALIAS/RELATED ITEM': 'RHY-SWIM-BRA-003',
            'Color': 'BLACK',
            'Size': 'M',
            'Ordered_Qty': 20
        },
        {
            'Canonical_Customer': 'RHYTHM',
            'Customer': 'Rhythm',
            'Customer_PO': None,
            'Customer_Alt_PO': 'RHYTHM-ALT-2024-002',
            'Style': None,
            'Pattern_ID': None,
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
            'Customer_Alt_PO': None,
            'Style': None,
            'Pattern_ID': None,
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
            'Customer_Alt_PO': None,
            'Style': 'RHONE-STANDARD-PRODUCT-B',
            'Pattern_ID': 'PAT-RHONE-B',
            'ALIAS/RELATED ITEM': 'RHONE-ALT-NAME',  # This shouldn't be used for RHONE
            'Color': 'RED',
            'Size': 'L',
            'Qty': 40
        }
    ])
    
    shipped_data = pd.DataFrame([
        # Rhythm data
        {
            'Canonical_Customer': 'RHYTHM',
            'Customer': 'Rhythm',
            'Customer_PO': 'RHYTHM-MIX-001',
            'Customer_Alt_PO': None,
            'Style': None,
            'Pattern_ID': None,
            'ALIAS/RELATED ITEM': 'RHY-MIXED-PRODUCT-A',
            'Color': 'BLUE',
            'Size': 'M',
            'Qty': 45  # Partial shipment
        },
        # RHONE data
        {
            'Canonical_Customer': 'RHONE',
            'Customer': 'Rhone',
            'Customer_PO': 'RHONE-MIX-001',
            'Customer_Alt_PO': None,
            'Style': 'RHONE-STANDARD-PRODUCT-B',
            'Pattern_ID': 'PAT-RHONE-B',
            'ALIAS/RELATED ITEM': 'RHONE-ALT-NAME',
            'Color': 'RED',
            'Size': 'L',
            'Qty': 40  # Full shipment
        }
    ])
    
    orders_data = pd.DataFrame([
        # Rhythm order
        {
            'Canonical_Customer': 'RHYTHM',
            'Customer': 'Rhythm',
            'Customer_PO': 'RHYTHM-MIX-001',
            'Customer_Alt_PO': None,
            'Style': None,
            'Pattern_ID': None,
            'ALIAS/RELATED ITEM': 'RHY-MIXED-PRODUCT-A',
            'Color': 'BLUE',
            'Size': 'M',
            'Ordered_Qty': 50
        },
        # RHONE order
        {
            'Canonical_Customer': 'RHONE',
            'Customer': 'Rhone',
            'Customer_PO': 'RHONE-MIX-001',
            'Customer_Alt_PO': None,
            'Style': 'RHONE-STANDARD-PRODUCT-B',
            'Pattern_ID': 'PAT-RHONE-B',
            'ALIAS/RELATED ITEM': 'RHONE-ALT-NAME',
            'Color': 'RED',
            'Size': 'L',
            'Ordered_Qty': 40
        }
    ])
    
    return packed_data, shipped_data, orders_data

def test_rhythm_end_to_end():
    """Test complete end-to-end pipeline with realistic Rhythm data"""
    print("=== Testing Rhythm End-to-End Pipeline ===")
    
    packed_data, shipped_data, orders_data = create_realistic_rhythm_data()
    
    print(f"Test data: {len(packed_data)} packed, {len(shipped_data)} shipped, {len(orders_data)} orders")
    
    # Run the complete matching pipeline
    results_df, summary_df = match_records(packed_data, shipped_data, orders_data, threshold=75)
    
    print(f"Results: {len(results_df)} total matches")
    
    # Analyze results
    match_type_counts = results_df['Match_Type'].value_counts()
    print(f"Match types: {match_type_counts.to_dict()}")
    
    # Check that Rhythm records are using ALIAS/RELATED ITEM field
    rhythm_results = results_df[results_df['Canonical_Customer'] == 'RHYTHM']
    rhythm_style_sources = rhythm_results['Style_Source'].value_counts()
    print(f"Rhythm style sources: {rhythm_style_sources.to_dict()}")
    
    # Verify ALIAS/RELATED ITEM is being used
    assert 'ALIAS/RELATED ITEM' in rhythm_style_sources.index, "Rhythm should use ALIAS/RELATED ITEM field"
    
    # Check for exact matches
    exact_matches = rhythm_results[rhythm_results['Match_Type'] == 'EXACT']
    print(f"Rhythm exact matches: {len(exact_matches)}")
    assert len(exact_matches) >= 3, "Should have at least 3 exact matches for Rhythm"
    
    # Check for cross-field PO matching
    alt_po_matches = rhythm_results[rhythm_results['Best_Match_Field'] == 'Alt_PO']
    print(f"Alt_PO matches: {len(alt_po_matches)}")
    assert len(alt_po_matches) >= 1, "Should have Alt_PO cross-field matches"
    
    # Check for fuzzy matches
    fuzzy_matches = rhythm_results[rhythm_results['Match_Type'] == 'FUZZY']
    print(f"Rhythm fuzzy matches: {len(fuzzy_matches)}")
    
    print("✅ Rhythm end-to-end pipeline test passed!")
    return results_df, summary_df

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
    assert rhone_style_source == 'Style', "RHONE should use Style in mixed dataset"
    
    # Verify both customers have exact matches
    assert len(rhythm_results[rhythm_results['Match_Type'] == 'EXACT']) > 0, "Rhythm should have exact matches"
    assert len(rhone_results[rhone_results['Match_Type'] == 'EXACT']) > 0, "RHONE should have exact matches"
    
    print("✅ Mixed customer integration test passed!")

def test_performance_with_larger_dataset():
    """Test performance with larger dataset"""
    print("\n=== Testing Performance with Larger Dataset ===")
    
    # Create larger test dataset
    np.random.seed(42)  # For reproducible results
    
    customers = ['RHYTHM'] * 100 + ['RHONE'] * 100 + ['PELOTON'] * 100
    
    packed_data = []
    shipped_data = []
    orders_data = []
    
    for i, customer in enumerate(customers):
        if customer == 'RHYTHM':
            # Rhythm products
            style_field = 'ALIAS/RELATED ITEM'
            style_value = f'RHY-PRODUCT-{i:03d}'
            style_col = None
            pattern_col = None
            alias_col = style_value
        else:
            # Standard customers
            style_field = 'Style'
            style_value = f'{customer}-PRODUCT-{i:03d}'
            style_col = style_value
            pattern_col = f'PAT-{i:03d}'
            alias_col = f'ALT-{i:03d}'
        
        # Create records for this product
        for size in ['S', 'M', 'L']:
            base_record = {
                'Canonical_Customer': customer,
                'Customer': customer.lower().title(),
                'Customer_PO': f'PO-{customer}-{i:03d}',
                'Customer_Alt_PO': f'ALT-{customer}-{i:03d}' if i % 3 == 0 else None,
                'Style': style_col,
                'Pattern_ID': pattern_col,
                'ALIAS/RELATED ITEM': alias_col,
                'Color': np.random.choice(['BLACK', 'WHITE', 'BLUE', 'RED']),
                'Size': size
            }
            
            # Add to each dataset with slight variations
            packed_record = base_record.copy()
            packed_record['Qty'] = np.random.randint(10, 50)
            packed_data.append(packed_record)
            
            shipped_record = base_record.copy()
            shipped_record['Qty'] = int(packed_record['Qty'] * np.random.uniform(0.8, 1.0))
            shipped_data.append(shipped_record)
            
            order_record = base_record.copy()
            order_record['Ordered_Qty'] = packed_record['Qty']
            orders_data.append(order_record)
    
    packed_df = pd.DataFrame(packed_data)
    shipped_df = pd.DataFrame(shipped_data)
    orders_df = pd.DataFrame(orders_data)
    
    print(f"Large dataset: {len(packed_df)} packed, {len(shipped_df)} shipped, {len(orders_df)} orders")
    
    import time
    start_time = time.time()
    
    # Run matching pipeline
    results_df, summary_df = match_records(packed_df, shipped_df, orders_df, threshold=75)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    print(f"Processing time: {processing_time:.2f} seconds")
    print(f"Records per second: {len(results_df) / processing_time:.1f}")
    
    # Verify results
    match_type_counts = results_df['Match_Type'].value_counts()
    print(f"Match types: {match_type_counts.to_dict()}")
    
    # Check that Rhythm customers are using correct style field
    rhythm_results = results_df[results_df['Canonical_Customer'] == 'RHYTHM']
    rhythm_style_sources = rhythm_results['Style_Source'].value_counts()
    print(f"Rhythm style sources in large dataset: {rhythm_style_sources.to_dict()}")
    
    assert 'ALIAS/RELATED ITEM' in rhythm_style_sources.index, "Rhythm should use ALIAS/RELATED ITEM in large dataset"
    
    # Performance should be reasonable (< 30 seconds for 900 records)
    assert processing_time < 30, f"Processing should be < 30 seconds, got {processing_time:.2f}s"
    
    print("✅ Performance test passed!")

def test_edge_cases():
    """Test edge cases and error conditions"""
    print("\n=== Testing Edge Cases ===")
    
    # Test with missing ALIAS/RELATED ITEM field for Rhythm
    edge_packed = pd.DataFrame([
        {
            'Canonical_Customer': 'RHYTHM',
            'Customer': 'Rhythm',
            'Customer_PO': 'RHYTHM-EDGE-001',
            'Customer_Alt_PO': None,
            'Style': 'FALLBACK-STYLE',  # Should fall back to this
            'Pattern_ID': None,
            'ALIAS/RELATED ITEM': None,  # Missing!
            'Color': 'GRAY',
            'Size': 'M',
            'Qty': 10
        }
    ])
    
    edge_orders = pd.DataFrame([
        {
            'Canonical_Customer': 'RHYTHM',
            'Customer': 'Rhythm',
            'Customer_PO': 'RHYTHM-EDGE-001',
            'Customer_Alt_PO': None,
            'Style': 'FALLBACK-STYLE',
            'Pattern_ID': None,
            'ALIAS/RELATED ITEM': None,
            'Color': 'GRAY',
            'Size': 'M',
            'Ordered_Qty': 10
        }
    ])
    
    # Test style field fallback for Rhythm
    rhythm_row = edge_packed.iloc[0]
    style_value, style_source = get_style_value_and_source(rhythm_row, 'RHYTHM')
    
    print(f"Edge case - Rhythm fallback: style='{style_value}', source='{style_source}'")
    assert style_value == 'FALLBACK-STYLE', "Should fall back to Style field when ALIAS/RELATED ITEM is missing"
    assert style_source == 'Style', "Should report Style as source for fallback"
    
    # Test matching with fallback
    results_df, _ = match_records(edge_packed, pd.DataFrame(), edge_orders, threshold=75)
    
    rhythm_result = results_df[results_df['Canonical_Customer'] == 'RHYTHM'].iloc[0]
    assert rhythm_result['Style_Source'] == 'Style', "Should track Style as source in edge case"
    assert rhythm_result['Match_Type'] == 'EXACT', "Should still match exactly with fallback"
    
    print("✅ Edge cases test passed!")

def main():
    """Run all Phase 3 integration tests"""
    print("🚀 Starting Phase 3 - Integration Testing...\n")
    
    try:
        # Test 1: Complete Rhythm end-to-end pipeline
        test_rhythm_end_to_end()
        
        # Test 2: Mixed customer integration
        test_mixed_customer_integration()
        
        # Test 3: Performance with larger dataset
        test_performance_with_larger_dataset()
        
        # Test 4: Edge cases and error handling
        test_edge_cases()
        
        print("\n🎉 All Phase 3 Integration Tests Passed Successfully!")
        print("✅ Rhythm customer ALIAS/RELATED ITEM field working end-to-end")
        print("✅ Mixed customer scenarios handled correctly")
        print("✅ Performance acceptable with larger datasets")
        print("✅ Edge cases and fallback logic working properly")
        print("✅ Customer-specific matching logic fully integrated!")
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
