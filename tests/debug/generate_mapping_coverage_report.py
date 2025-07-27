#!/usr/bin/env python3
"""
Generate a comprehensive mapping coverage report showing STG column mappings to Monday.com
"""
import sys
from pathlib import Path

# Add project root for imports
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

# Import from utils/
import mapping_helper
import yaml

def generate_mapping_coverage_report():
    """Generate comprehensive mapping coverage report"""
    
    print("=" * 80)
    print("PRODUCTION READINESS: STG COLUMN TO MONDAY.COM MAPPING COVERAGE REPORT")
    print("=" * 80)
    print()
    
    # Load the mapping configuration
    orders_config = mapping_helper.load_orders_mapping_config()
    field_mappings = mapping_helper.get_orders_field_mappings()
    subitem_mappings = mapping_helper.get_orders_subitem_mappings()
    
    # MAIN FIELD MAPPINGS
    print("1. MASTER ITEM FIELD MAPPINGS (STG -> Monday.com)")
    print("-" * 60)
    print(f"Total Mappings: {len(field_mappings)}")
    print()
    
    for i, (stg_field, monday_column_id) in enumerate(field_mappings.items(), 1):
        print(f"{i:2d}. STG Column: '{stg_field}'")
        print(f"    -> Monday.com Column ID: '{monday_column_id}'")
        print()
    
    # SUBITEM MAPPINGS
    print("2. SUBITEM FIELD MAPPINGS (STG -> Monday.com)")
    print("-" * 60)
    print(f"Total Subitem Mappings: {len(subitem_mappings)}")
    print()
    
    for i, (stg_field, monday_column_id) in enumerate(subitem_mappings.items(), 1):
        print(f"{i:2d}. STG Column: '{stg_field}'")
        print(f"    -> Monday.com Column ID: '{monday_column_id}'")
        print()
    
    # CRITICAL FIELDS VALIDATION
    print("3. CRITICAL FIELD VALIDATION")
    print("-" * 60)
    
    critical_stg_fields = [
        'AAG ORDER NUMBER',
        '[CUSTOMER STYLE]', 
        '[TOTAL QTY]',
        'AAG SEASON',
        'CUSTOMER SEASON',
        'CUSTOMER ALT PO',
        '[EX FACTORY DATE]'
    ]
    
    print("Critical STG fields that MUST be mapped:")
    print()
    
    all_mapped = True
    for field in critical_stg_fields:
        if field in field_mappings:
            monday_id = field_mappings[field]
            print(f"✓ MAPPED: '{field}' -> '{monday_id}'")
        else:
            print(f"✗ MISSING: '{field}' -> NOT MAPPED")
            all_mapped = False
    
    print()
    
    # FAKE ID DETECTION
    print("4. FAKE COLUMN ID DETECTION")
    print("-" * 60)
    
    fake_ids = ['text', 'text2', 'text3', 'text4', 'text5', 'text6', 'numbers', 'dropdown', 'date']
    fake_ids_found = []
    
    # Check master item mappings
    for stg_field, monday_id in field_mappings.items():
        if monday_id in fake_ids:
            fake_ids_found.append(f"Master: {stg_field} -> {monday_id}")
    
    # Check subitem mappings  
    for stg_field, monday_id in subitem_mappings.items():
        if monday_id in fake_ids:
            fake_ids_found.append(f"Subitem: {stg_field} -> {monday_id}")
    
    if fake_ids_found:
        print("✗ FAKE COLUMN IDs DETECTED:")
        for fake_mapping in fake_ids_found:
            print(f"   {fake_mapping}")
    else:
        print("✓ NO FAKE COLUMN IDs DETECTED - All mappings use real Monday.com column IDs")
    
    print()
    
    # PRODUCTION READINESS SUMMARY
    print("5. PRODUCTION READINESS SUMMARY")
    print("-" * 60)
    
    total_mappings = len(field_mappings) + len(subitem_mappings)
    critical_mapped_count = sum(1 for field in critical_stg_fields if field in field_mappings)
    
    print(f"Total STG columns mapped: {total_mappings}")
    print(f"Master item mappings: {len(field_mappings)}")
    print(f"Subitem mappings: {len(subitem_mappings)}")
    print(f"Critical fields mapped: {critical_mapped_count}/{len(critical_stg_fields)}")
    print(f"Fake column IDs found: {len(fake_ids_found)}")
    print()
    
    # FINAL VERDICT
    production_ready = all_mapped and len(fake_ids_found) == 0
    
    if production_ready:
        print("🎉 PRODUCTION READINESS: ✅ READY")
        print("   - All critical STG columns are mapped to real Monday.com column IDs")
        print("   - No fake column IDs detected")
        print("   - Mapping infrastructure is production-ready")
    else:
        print("🚨 PRODUCTION READINESS: ❌ NOT READY")
        if not all_mapped:
            print("   - Some critical STG columns are not mapped")
        if fake_ids_found:
            print("   - Fake column IDs detected")
        print("   - Mapping infrastructure needs fixes before production")
    
    print()
    print("=" * 80)
    
    return production_ready

if __name__ == "__main__":
    try:
        success = generate_mapping_coverage_report()
        if success:
            print("Report generated successfully - PRODUCTION READY")
        else:
            print("Report generated - ISSUES FOUND")
    except Exception as e:
        print(f"Error generating report: {e}")
        import traceback
        traceback.print_exc()
