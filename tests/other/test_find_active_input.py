"""
Find which field is sending ACTIVE to dropdown_mkr518fc
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from customer_master_schedule.order_mapping import load_mapping_config
import yaml

def find_active_field():
    """Find which field maps to dropdown_mkr518fc that contains ACTIVE"""
    print('=== Finding Field That Contains ACTIVE ===')
    
    config = load_mapping_config()
    
    # Search through all mappings for dropdown_mkr518fc
    target_column_id = "dropdown_mkr518fc"
    found_field = None
    
    # Check exact_matches
    for field in config.get('exact_matches', []):
        if field.get('target_column_id') == target_column_id:
            found_field = field
            break
    
    # Check mapped_fields
    if not found_field:
        for field in config.get('mapped_fields', []):
            if field.get('target_column_id') == target_column_id:
                found_field = field
                break
    
    if found_field:
        print(f'Found field mapping for {target_column_id}:')
        print(f'  Source field: {found_field.get("source_field")}')
        print(f'  Target field: {found_field.get("target_field")}')
        print(f'  Target type: {found_field.get("target_type")}')
        print(f'  Transformation: {found_field.get("transformation", "none")}')
        
        # Check if it has value mapping rules
        mapping_rules = found_field.get('mapping_rules', [])
        if mapping_rules:
            print(f'  Mapping rules: {mapping_rules}')
        else:
            print(f'  ❌ No mapping rules - this is the problem!')
    else:
        print(f'❌ Field mapping for {target_column_id} not found!')
        
        # Let's search the raw YAML to see what this column ID refers to
        print('\nSearching raw configuration for dropdown_mkr518fc...')
        yaml_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'mapping', 'orders_unified_monday_mapping.yaml')
        with open(yaml_path, 'r') as f:
            content = f.read()
            if 'dropdown_mkr518fc' in content:
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'dropdown_mkr518fc' in line:
                        print(f'  Line {i+1}: {line.strip()}')
                        # Show context lines
                        for j in range(max(0, i-3), min(len(lines), i+4)):
                            if j != i:
                                print(f'  Line {j+1}: {lines[j].strip()}')
                        break
            else:
                print('  ❌ dropdown_mkr518fc not found in YAML')

if __name__ == "__main__":
    find_active_field()