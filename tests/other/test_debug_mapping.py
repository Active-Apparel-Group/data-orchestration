"""
Debug if exact_matches section is being processed for value_mapping transformations
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from customer_master_schedule.order_mapping import load_mapping_config

def debug_exact_matches_processing():
    """Debug if ORDER TYPE in exact_matches is being processed correctly"""
    print('=== Debugging exact_matches Processing ===')
    
    config = load_mapping_config()
    
    # Check exact_matches section
    exact_matches = config.get('exact_matches', [])
    print(f'Found {len(exact_matches)} exact_matches')
    
    # Look for ORDER TYPE in exact_matches
    order_type_exact = None
    for field in exact_matches:
        if field.get('source_field') == 'ORDER TYPE':
            order_type_exact = field
            break
    
    if order_type_exact:
        print(f'\n✅ Found ORDER TYPE in exact_matches:')
        print(f'   Source: {order_type_exact.get("source_field")}')
        print(f'   Target: {order_type_exact.get("target_field")}')
        print(f'   Column ID: {order_type_exact.get("target_column_id")}')
        print(f'   Target type: {order_type_exact.get("target_type")}')
        print(f'   Transformation: {order_type_exact.get("transformation")}')
        
        mapping_rules = order_type_exact.get('mapping_rules', [])
        if mapping_rules:
            print(f'   Mapping rules:')
            for rule in mapping_rules:
                source_val = rule.get('source_value')
                target_val = rule.get('target_value')
                print(f'     "{source_val}" → "{target_val}"')
                
                if source_val == "ACTIVE" and target_val == "RECEIVED":
                    print(f'     ✅ Correct ACTIVE → RECEIVED rule found')
        else:
            print(f'   ❌ No mapping rules found!')
    else:
        print(f'\n❌ ORDER TYPE not found in exact_matches!')
    
    # Now check if the order_mapping.py logic processes exact_matches for transformations
    print(f'\n=== Checking order_mapping.py Processing Logic ===')
    print(f'The transform_order_data function needs to:')
    print(f'1. ✅ Process exact_matches section')
    print(f'2. ✅ Check for transformation = "value_mapping"')
    print(f'3. ✅ Apply mapping_rules when transformation is value_mapping')
    print(f'4. ✅ Return transformed value ("RECEIVED") instead of original ("ACTIVE")')
    
    # Let's check if the logic handles exact_matches with transformations
    print(f'\n📝 In order_mapping.py around line 220-240:')
    print(f'   The code should process both exact_matches AND mapped_fields')
    print(f'   And apply transformations to both sections')

if __name__ == "__main__":
    debug_exact_matches_processing()