#!/usr/bin/env python3
"""
Quick database test script
"""
import sys
sys.path.append('src')

from customer_master_schedule.order_queries import get_database_connection

def test_tables():
    print('📊 Checking table contents...')
    conn = get_database_connection()
    if not conn:
        print('❌ Database connection failed')
        return
    
    cursor = conn.cursor()
    
    try:
        # Check ORDERS_UNIFIED count
        cursor.execute('SELECT COUNT(*) FROM ORDERS_UNIFIED')
        orders_count = cursor.fetchone()[0]
        print(f'📦 ORDERS_UNIFIED total records: {orders_count}')
        
        # Check if MON_CustMasterSchedule table exists
        try:
            cursor.execute('SELECT COUNT(*) FROM MON_CustMasterSchedule')
            staging_count = cursor.fetchone()[0]
            print(f'🏗️ MON_CustMasterSchedule total records: {staging_count}')
        except Exception as e:
            print(f'⚠️ MON_CustMasterSchedule table issue: {e}')
        
        # Check sample of ORDERS_UNIFIED
        cursor.execute("""
        SELECT TOP 3 
            [AAG ORDER NUMBER], 
            [CUSTOMER NAME], 
            [CUSTOMER STYLE],
            [CUSTOMER'S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS]
        FROM ORDERS_UNIFIED 
        WHERE [AAG ORDER NUMBER] IS NOT NULL
        ORDER BY [ORDER DATE PO RECEIVED] DESC
        """)
        sample_orders = cursor.fetchall()
        print(f'📋 Sample ORDERS_UNIFIED records:')
        for order in sample_orders:
            print(f'   AAG: {order[0]} | Customer: {order[1]} | Style: {order[2]} | Color: {order[3]}')
        
    except Exception as e:
        print(f'❌ Error: {e}')
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    test_tables()
