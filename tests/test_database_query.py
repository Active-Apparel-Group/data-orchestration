#!/usr/bin/env python3
"""
Test script to verify database query functionality
"""
import sys
import os
sys.path.append('src')

print('🔍 Testing small dataset query...')

try:
    from customer_master_schedule.order_queries import get_new_orders_from_unified
    print('✅ Function imported successfully')
    
    # Get just 2 orders to test
    df = get_new_orders_from_unified(limit=2)
    print(f'✅ Retrieved {len(df)} orders')
    
    if len(df) > 0:
        print('📋 Sample columns:', list(df.columns)[:10])
        first_order = df.iloc[0]
        aag_order = first_order.get('AAG ORDER NUMBER', 'Not found')
        customer_name = first_order.get('CUSTOMER NAME', 'Not found')
        customer_style = first_order.get('CUSTOMER STYLE', 'Not found')
        color_field = "CUSTOMER'S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS"
        color = first_order.get(color_field, 'Not found')
        
        print(f'📄 First order details:')
        print(f'   AAG ORDER NUMBER: {aag_order}')
        print(f'   CUSTOMER NAME: {customer_name}')
        print(f'   CUSTOMER STYLE: {customer_style}')
        print(f'   COLOR: {color}')
        print('✅ Data query test successful')
    else:
        print('ℹ️ No new orders found (all orders already in MON_CustMasterSchedule)')
        
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()

print('🏁 Test completed')
