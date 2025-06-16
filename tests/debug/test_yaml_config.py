#!/usr/bin/env python3
"""
Test YAML config loading after TOTAL QTY mapping change
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from customer_master_schedule.order_mapping import load_mapping_config

def test_yaml_config():
    """Test that YAML config loads correctly after TOTAL QTY changes"""
    
    print("🧪 TESTING YAML CONFIG AFTER TOTAL QTY CHANGES")
    print("=" * 60)
    
    try:
        mapping_config = load_mapping_config()
        
        if not mapping_config:
            print("❌ Failed to load mapping config")
            return False
            
        print("✅ YAML config loaded successfully")
        
        # Check exact_matches for TOTAL QTY
        exact_matches = mapping_config.get('exact_matches', [])
        total_qty_in_exact = False
        for match in exact_matches:
            if match.get('target_field') == 'TOTAL QTY':
                total_qty_in_exact = True
                print(f"✅ Found TOTAL QTY in exact_matches:")
                print(f"   Source: {match.get('source_field')}")
                print(f"   Type: {match.get('target_type')}")
                print(f"   Column ID: {match.get('target_column_id')}")
                break
        
        # Check computed_fields for TOTAL QTY (should NOT be there)
        computed_fields = mapping_config.get('computed_fields', [])
        total_qty_in_computed = False
        for field in computed_fields:
            if field.get('target_field') == 'TOTAL QTY':
                total_qty_in_computed = True
                print(f"⚠️ WARNING: TOTAL QTY still in computed_fields")
                break
        
        print(f"\n📊 TOTAL QTY Status:")
        print(f"   In exact_matches: {'✅ YES' if total_qty_in_exact else '❌ NO'}")
        print(f"   In computed_fields: {'❌ YES (should be NO)' if total_qty_in_computed else '✅ NO (correct)'}")
        
        # Check computed fields count
        print(f"\n📋 Configuration Summary:")
        print(f"   Exact matches: {len(exact_matches)}")
        print(f"   Mapped fields: {len(mapping_config.get('mapped_fields', []))}")
        print(f"   Computed fields: {len(computed_fields)}")
        
        # List computed fields
        print(f"\n🔧 Computed fields:")
        for field in computed_fields:
            print(f"   - {field.get('target_field', 'Unknown')}: {field.get('transformation', 'Unknown')}")
        
        return total_qty_in_exact and not total_qty_in_computed
        
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_yaml_config()
    if success:
        print(f"\n🎉 STEP 2 VALIDATION: ✅ PASSED")
        print(f"📋 TOTAL QTY successfully moved from computed_fields to exact_matches!")
    else:
        print(f"\n❌ STEP 2 VALIDATION: FAILED")
        print(f"📋 TOTAL QTY mapping change needs to be fixed")
