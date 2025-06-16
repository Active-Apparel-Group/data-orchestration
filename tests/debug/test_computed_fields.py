#!/usr/bin/env python3
"""
Test computed fields logic after restoration
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import pandas as pd
from customer_master_schedule.order_mapping import (
    load_mapping_config,
    load_customer_mapping,
    transform_order_data
)

def test_computed_fields():
    """Test that computed fields logic is working"""
    
    print("🧪 TESTING COMPUTED FIELDS RESTORATION")
    print("=" * 60)
    
    # Load configurations
    print("📋 Loading configurations...")
    mapping_config = load_mapping_config()
    customer_lookup = load_customer_mapping()
    
    if not mapping_config:
        print("❌ Failed to load mapping config")
        return False
        
    # Check for computed_fields in config
    computed_fields = mapping_config.get('computed_fields', [])
    print(f"📊 Found {len(computed_fields)} computed fields in config:")
    for field in computed_fields:
        print(f"   - {field.get('target_field', 'Unknown')}: {field.get('transformation', 'Unknown')}")
      # Create sample order data
    sample_order = pd.Series({
        'CUSTOMER STYLE': 'M01Y09',
        "CUSTOMER'S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS": 'DEAN BLUE/WHITE',
        'AAG ORDER NUMBER': 'MWE-00024',
        'CUSTOMER NAME': 'MACK WELDON',
        'TOTAL QTY': 500,
        'ORDER DATE PO RECEIVED': '2025-06-09'
    })
    
    print(f"\n🔄 Testing transformation with sample order:")
    print(f"   Style: {sample_order['CUSTOMER STYLE']}")
    color_field = "CUSTOMER'S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS"
    print(f"   Color: {sample_order[color_field]}")
    print(f"   Order: {sample_order['AAG ORDER NUMBER']}")
    print(f"   Total QTY: {sample_order['TOTAL QTY']}")
    
    # Transform the order
    try:
        transformed_data = transform_order_data(sample_order, mapping_config, customer_lookup)
        
        print(f"\n📊 Transformation completed!")
        print(f"   Total fields transformed: {len([k for k in transformed_data.keys() if not k.startswith('_')])}")
        
        # Check for computed fields in results
        computed_results = {}
        for field_name, field_data in transformed_data.items():
            if not field_name.startswith('_') and 'computed:' in str(field_data.get('source_field', '')):
                computed_results[field_name] = field_data.get('value', 'N/A')
        
        print(f"\n✅ COMPUTED FIELDS RESULTS:")
        if computed_results:
            for field_name, value in computed_results.items():
                print(f"   {field_name}: '{value}'")
                
                # Special check for Title field
                if field_name in ['Name', 'Title']:
                    expected = "M01Y09 DEAN BLUE/WHITE MWE-00024"
                    if value == expected:
                        print(f"      ✅ Title format CORRECT!")
                    else:
                        print(f"      ⚠️ Title format mismatch. Expected: '{expected}'")
        else:
            print("   ❌ No computed fields found in results")
            
        # Check for Title/Name field specifically
        title_found = False
        for field_name in ['Name', 'Title']:
            if field_name in transformed_data:
                title_value = transformed_data[field_name].get('value', '')
                print(f"\n🎯 {field_name} field: '{title_value}'")
                title_found = True
                
        if not title_found:
            print(f"\n❌ No Title/Name field found in transformation results")
            
        return len(computed_results) > 0
        
    except Exception as e:
        print(f"❌ Transformation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_computed_fields()
    if success:
        print(f"\n🎉 STEP 1 VALIDATION: ✅ PASSED")
        print(f"📋 Computed fields logic restored successfully!")
    else:
        print(f"\n❌ STEP 1 VALIDATION: FAILED")
        print(f"📋 Computed fields logic needs more work")
