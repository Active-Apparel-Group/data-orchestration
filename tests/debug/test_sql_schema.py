#!/usr/bin/env python3
"""
Test to determine the actual SQL table schema for MON_CustMasterSchedule
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from customer_master_schedule.order_queries import get_db_connection

def check_table_schema():
    """Check the actual table schema"""
    try:
        conn = get_db_connection('ORDERS')
        if not conn:
            print("❌ Failed to connect to database")
            return
        
        cursor = conn.cursor()
        
        # Get table schema using INFORMATION_SCHEMA
        schema_query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE,
            COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'MON_CustMasterSchedule' 
        AND TABLE_SCHEMA = 'dbo'
        ORDER BY ORDINAL_POSITION
        """
        
        cursor.execute(schema_query)
        columns = cursor.fetchall()
        
        print(f"✅ Found {len(columns)} columns in MON_CustMasterSchedule table:")
        print("=" * 80)
        
        for col in columns:
            col_name, data_type, max_len, nullable, default = col
            len_str = f"({max_len})" if max_len else ""
            null_str = "NULL" if nullable == "YES" else "NOT NULL"
            default_str = f" DEFAULT {default}" if default else ""
            
            print(f"{col_name:<30} {data_type}{len_str:<15} {null_str}{default_str}")
        
        conn.close()
        print("\n✅ Schema check completed")
        
    except Exception as e:
        print(f"❌ Error checking schema: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_table_schema()
