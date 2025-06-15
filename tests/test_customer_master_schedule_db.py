#!/usr/bin/env python3
"""
Database connection and query tests for customer_master_schedule
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from customer_master_schedule.order_queries import get_database_connection, get_new_orders_from_unified

def test_database_connection():
    """Test basic database connectivity"""
    print('🔌 Testing database connection...')
    conn = get_database_connection()
    if not conn:
        print('❌ Database connection failed')
        return False
    
    print('✅ Database connection successful')
    conn.close()
    return True

def test_table_contents():
    """Check contents of ORDERS_UNIFIED and MON_CustMasterSchedule tables"""
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

def test_new_orders_query():
    """Test the get_new_orders_from_unified function"""
    print('🔍 Testing new orders query...')
    
    try:
        df = get_new_orders_from_unified(limit=5)
        print(f'✅ Retrieved {len(df)} new orders')
        
        if len(df) > 0:
            print('📋 Sample columns:', list(df.columns)[:10])
            first_order = df.iloc[0]
            print(f'📄 First order:')
            print(f'   AAG ORDER NUMBER: {first_order.get("AAG ORDER NUMBER", "Not found")}')
            print(f'   CUSTOMER NAME: {first_order.get("CUSTOMER NAME", "Not found")}')
            print(f'   CUSTOMER STYLE: {first_order.get("CUSTOMER STYLE", "Not found")}')
        else:
            print('ℹ️ No new orders found (all orders already in MON_CustMasterSchedule)')
            
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

def test_column_names():
    """Check actual column names in ORDERS_UNIFIED table"""
    print('📋 Checking ORDERS_UNIFIED column names...')
    conn = get_database_connection()
    if not conn:
        print('❌ Database connection failed')
        return
    
    cursor = conn.cursor()
    
    try:
        # Get column information
        cursor.execute("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'ORDERS_UNIFIED'
        AND COLUMN_NAME LIKE '%COLOUR%' OR COLUMN_NAME LIKE '%COLOR%'
        ORDER BY ORDINAL_POSITION
        """)
        color_columns = cursor.fetchall()
        print(f'🎨 Color-related columns found:')
        for col in color_columns:
            print(f'   {col[0]}')
        
        # Get sample data from first few columns
        cursor.execute("""
        SELECT TOP 1 [AAG ORDER NUMBER], [CUSTOMER NAME], [CUSTOMER STYLE]
        FROM ORDERS_UNIFIED 
        WHERE [AAG ORDER NUMBER] IS NOT NULL
        """)
        sample = cursor.fetchone()
        if sample:
            print(f'📄 Sample record: {sample[0]} | {sample[1]} | {sample[2]}')
        
    except Exception as e:
        print(f'❌ Error: {e}')
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Customer Master Schedule Database Tests")
    print("=" * 60)
      # Test 1: Database connection
    if test_database_connection():
        # Test 2: Check column names
        test_column_names()
        
        # Test 3: Table contents
        test_table_contents()
        
        # Test 4: New orders query
        test_new_orders_query()
        
        # Test 4: Column names
        test_column_names()
    
    print("=" * 60)
    print("✅ Tests completed")
