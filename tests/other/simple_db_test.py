#!/usr/bin/env python3
"""
Simple test to check database connection and staging table
"""
import sys
import os
sys.path.append('src')

try:
    from customer_master_schedule.order_queries import get_database_connection
    
    print("🔍 Testing database connection...")
    conn = get_database_connection()
    
    if conn:
        print("✅ Database connection successful")
        cursor = conn.cursor()
        
        # Check if staging table exists and get count
        try:
            cursor.execute("SELECT COUNT(*) FROM MON_CustMasterSchedule")
            count = cursor.fetchone()[0]
            print(f"📊 Current records in MON_CustMasterSchedule: {count}")
            
            # Check table structure
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'MON_CustMasterSchedule'
                ORDER BY ORDINAL_POSITION
            """)
            columns = cursor.fetchall()
            print(f"📋 Table has {len(columns)} columns:")
            for col_name, data_type in columns:
                print(f"  - {col_name}: {data_type}")
                
        except Exception as e:
            print(f"❌ Error querying staging table: {e}")
            
        conn.close()
    else:
        print("❌ Database connection failed")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
