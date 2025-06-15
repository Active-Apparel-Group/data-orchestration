"""
Debug why ORDER TYPE value mapping ACTIVE → RECEIVED is not working
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from customer_master_schedule.order_queries import get_new_orders_from_unified
from customer_master_schedule.order_mapping import transform_order_data, load_mapping_config, load_customer_mapping

def debug_why_mapping_fails():
    """Debug why ACTIVE is not being transformed to RECEIVED"""
    print('=== Debugging Why Value Mapping Fails ===')
    
    # Get sample order
    new_orders = get_new_orders_from_unified(limit=1)
    first_order = new_orders.iloc[0].to_dict()
    
    config = load_mapping_config()
    customer_lookup = load_customer_mapping()
    
    print(f'Original ORDER TYPE value: "{first_order.get("ORDER TYPE")}"')
    
    # Check the mapping configuration for ORDER TYPE
    mapped_fields = config.get('mapped_fields', [])
    order_type_config = None
    
    for field in mapped_fields:
        if (field.get('source_field') == 'ORDER TYPE' and 
            field.get('target_field') == 'ORDER TYPE'):
            order_type_config = field
            break
    
    if order_type_config:
        print(f'\n✅ Found ORDER TYPE mapping config:')
        print(f'   Source: {order_type_config.get("source_field")}')
        print(f'   Target: {order_type_config.get("target_field")}')
        print(f'   Column ID: {order_type_config.get("target_column_id")}')
        print(f'   Transformation: {order_type_config.get("transformation")}')
        print(f'   Mapping rules: {order_type_config.get("mapping_rules", [])}')
        
        # Check if transformation is set correctly
        transformation = order_type_config.get("transformation")
        if transformation != "value_mapping":
            print(f'❌ PROBLEM: Transformation is "{transformation}", should be "value_mapping"')
        else:
            print(f'✅ Transformation is correctly set to "value_mapping"')
            
        # Check mapping rules
        mapping_rules = order_type_config.get("mapping_rules", [])
        if not mapping_rules:
            print(f'❌ PROBLEM: No mapping rules defined!')
        else:
            print(f'✅ Mapping rules found:')
            for rule in mapping_rules:
                source_val = rule.get('source_value')
                target_val = rule.get('target_value')
                print(f'     "{source_val}" → "{target_val}"')
                
                if source_val == "ACTIVE" and target_val == "RECEIVED":
                    print(f'     ✅ Correct ACTIVE → RECEIVED rule found')
    else:
        print(f'❌ PROBLEM: ORDER TYPE mapping config not found!')
        
        # Show what mappings do exist
        print(f'\nAvailable mapped_fields:')
        for field in mapped_fields:
            source = field.get('source_field')
            target = field.get('target_field')
            print(f'   {source} → {target}')
    
    # Now test the transformation directly
    print(f'\n=== Testing Transformation ===')
    transformed = transform_order_data(first_order, config, customer_lookup)
    
    order_type_result = transformed.get('ORDER TYPE')
    if order_type_result:
        final_value = order_type_result.get('value')
        print(f'Transformed ORDER TYPE value: "{final_value}"')
        
        if final_value == "":
            print(f'❌ PROBLEM: Value is empty - transformation logic is not working')
        elif final_value == "ACTIVE":
            print(f'❌ PROBLEM: Value unchanged - mapping rules not applied')
        elif final_value == "RECEIVED":
            print(f'✅ SUCCESS: Value correctly transformed')
        else:
            print(f'⚠️  UNEXPECTED: Value is "{final_value}"')
    else:
        print(f'❌ PROBLEM: ORDER TYPE not found in transformed data')

if __name__ == "__main__":
    debug_why_mapping_fails()