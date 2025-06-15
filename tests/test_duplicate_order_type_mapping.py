"""
Debug if order_mapping.py processes transformations in exact_matches
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Read the order_mapping.py file to check the logic
def debug_exact_matches_logic():
    """Check if exact_matches transformations are processed"""
    print('=== Checking order_mapping.py Logic ===')
    
    order_mapping_path = os.path.join(
        os.path.dirname(__file__), '..', 
        'src', 'customer_master_schedule', 
        'order_mapping.py'
    )
    
    try:
        with open(order_mapping_path, 'r') as f:
            content = f.read()
        
        # Look for exact_matches processing logic
        lines = content.split('\n')
        
        print('Looking for exact_matches processing...')
        exact_matches_found = False
        transformation_logic_found = False
        
        for i, line in enumerate(lines):
            # Look for exact_matches processing
            if 'exact_matches' in line.lower() and 'for' in line:
                exact_matches_found = True
                print(f'\n✅ Found exact_matches processing at line {i+1}:')
                # Show context
                for j in range(max(0, i-2), min(len(lines), i+10)):
                    marker = '>>>' if j == i else '   '
                    print(f'{marker} {j+1}: {lines[j]}')
                
                # Check if transformation logic is applied to exact_matches
                for k in range(i, min(len(lines), i+20)):
                    if 'transformation' in lines[k] and 'value_mapping' in lines[k+1:k+5]:
                        transformation_logic_found = True
                        print(f'\n✅ Found transformation logic in exact_matches at line {k+1}')
                        break
                break
        
        if not exact_matches_found:
            print('\n❌ exact_matches processing not found!')
        elif not transformation_logic_found:
            print('\n❌ PROBLEM: exact_matches found but NO transformation logic applied!')
            print('This is why ORDER TYPE → ORDER TYPE is not being transformed')
        
        # Look for the transform_order_data function structure
        print(f'\n=== Checking transform_order_data Function Structure ===')
        
        # Find the function and check its sections
        in_function = False
        sections_found = []
        
        for i, line in enumerate(lines):
            if 'def transform_order_data' in line:
                in_function = True
                print(f'Found transform_order_data at line {i+1}')
                continue
                
            if in_function:
                if line.strip().startswith('def ') and 'transform_order_data' not in line:
                    break  # End of function
                    
                if 'exact_matches' in line:
                    sections_found.append(f'exact_matches (line {i+1})')
                elif 'mapped_fields' in line:
                    sections_found.append(f'mapped_fields (line {i+1})')
        
        print(f'Sections processed in transform_order_data:')
        for section in sections_found:
            print(f'  ✅ {section}')
            
        if 'exact_matches' not in str(sections_found):
            print(f'  ❌ exact_matches section missing or not processed!')
            
    except Exception as e:
        print(f'Error reading order_mapping.py: {e}')

if __name__ == "__main__":
    debug_exact_matches_logic()