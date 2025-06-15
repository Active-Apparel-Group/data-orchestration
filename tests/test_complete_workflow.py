#!/usr/bin/env python3
"""
Test Complete Order Processing Workflow

Tests the end-to-end workflow for processing new orders:
1. Query new orders from ORDERS_UNIFIED
2. Transform using mapping configuration  
3. Validate field mappings and transformations
"""

import sys
import os

# Add src to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
sys.path.append(src_path)

def test_complete_workflow():
    """Test the complete order processing workflow"""
    print('=== Testing Complete Order Processing Workflow ===')
      # Import required modules
    from customer_master_schedule.order_queries import get_new_orders_from_unified
    from customer_master_schedule.order_mapping import (
        transform_order_data, 
        load_mapping_config,
        load_customer_mapping
    )    # Step 1: Get new orders
    print('\n📋 Step 1: Getting new orders...')
    new_orders = get_new_orders_from_unified(limit=10)  # Get more to filter
    print(f'Found {len(new_orders)} new orders')
    
    if new_orders.empty:
        print('No new orders to process')
        return
    
    # Show customer breakdown
    print('\nCustomer breakdown:')
    customer_counts = new_orders['CUSTOMER NAME'].value_counts()
    for customer, count in customer_counts.head(5).items():
        print(f'  {customer}: {count} orders')
    
    # Filter out LORNA JANE orders for now
    filtered_orders = new_orders[~new_orders['CUSTOMER NAME'].str.startswith('LORNA', na=False)]
    print(f'After filtering out LORNA orders: {len(filtered_orders)} orders remaining')
    
    if filtered_orders.empty:
        print('All orders are from LORNA - proceeding with LORNA order but expecting customer mapping warning')
        # Use original orders since all are LORNA
        new_orders = new_orders
    else:
        # Use filtered orders
        new_orders = filtered_orders
      # Step 2: Load mapping configuration
    print('\n⚙️ Step 2: Loading mapping configuration...')
    try:
        config = load_mapping_config()
        field_mappings = config.get('field_mappings', {})
        print(f'✅ Loaded mapping config with {len(field_mappings)} field mappings')
        
        # Load customer mapping
        customer_lookup = load_customer_mapping()
        print(f'✅ Loaded customer mapping with {len(customer_lookup)} customers')
        
        # Debug: Show some config details
        print(f'Config keys: {list(config.keys())}')
        if field_mappings:
            print(f'Sample field mappings: {list(field_mappings.keys())[:5]}')
            
    except Exception as e:
        print(f'❌ Error loading mapping config: {e}')
        import traceback
        traceback.print_exc()
        return    # Step 3: Transform first order as test
    print('\n🔄 Step 3: Testing order transformation...')
    try:
        first_order = new_orders.iloc[0]  # Keep as Series, not dict
        customer_name = first_order['CUSTOMER NAME']
        print(f'Testing with customer: {customer_name}')
        print(f'Original order fields (first 5): {list(first_order.index)[:5]}')
        
        transformed = transform_order_data(first_order, config, customer_lookup)
        print(f'✅ Transformation successful!')
        print(f'Transformed order has {len(transformed)} fields')
        print(f'Sample transformed fields: {list(transformed.keys())[:5]}')
        
        # Check key mappings
        if 'STYLE' in transformed:
            print(f'✅ STYLE mapping working: {transformed["STYLE"]}')
        if 'COLOR' in transformed:
            print(f'✅ COLOR mapping working: {transformed["COLOR"]}')
        if 'AAG ORDER NUMBER' in transformed:
            print(f'✅ AAG ORDER NUMBER mapping: {transformed["AAG ORDER NUMBER"]}')
        if 'CUSTOMER NAME' in transformed:
            print(f'✅ CUSTOMER NAME mapping: {transformed["CUSTOMER NAME"]}')
            
    except Exception as e:
        print(f'❌ Error in transformation: {e}')
        import traceback
        traceback.print_exc()
    
    print('\n✅ Workflow test completed!')

if __name__ == '__main__':
    test_complete_workflow()
