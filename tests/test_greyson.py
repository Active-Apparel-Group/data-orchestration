#!/usr/bin/env python3
"""
Quick test script for GREYSON CLOTHIERS PO 4755
"""

from dev.milestone_2_customer_analysis import get_customer_detail

if __name__ == "__main__":
    print("Testing GREYSON CLOTHIERS with PO 4755...")
    print()
    
    # Test the enhanced function
    result = get_customer_detail('GREYSON CLOTHIERS', po_number='4755')
    
    print(f"\n✅ Returned {len(result)} records")
    
    if len(result) > 0:
        print("\n📋 Sample record:")
        print(f"Customer: {result.iloc[0]['CUSTOMER']}")
        print(f"AAG Order: {result.iloc[0]['AAG ORDER NUMBER']}")
        print(f"Style: {result.iloc[0]['STYLE']}")
        print(f"Color: {result.iloc[0]['COLOR']}")
        print(f"Qty: {result.iloc[0]['ORDER_QTY']}")
        print(f"PO: {result.iloc[0]['PO NUMBER']}")
    else:
        print("❌ No records found")
