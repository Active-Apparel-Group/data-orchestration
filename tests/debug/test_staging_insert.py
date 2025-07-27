#!/usr/bin/env python3
"""
Test script to verify staging table insert functionality
"""
import sys
sys.path.append('src')

from customer_master_schedule.order_queries import get_database_connection, insert_orders_to_staging
from customer_master_schedule.add_order import get_new_orders, transform_order_data
from customer_master_schedule.order_mapping import load_customer_mapping
import pandas as pd

def main():
    print("🔍 Testing staging table insert functionality")
    
    # Get database connection
    conn = get_database_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return
    
    cursor = conn.cursor()
    
    # Check current count in staging table
    try:
        cursor.execute("SELECT COUNT(*) FROM MON_CustMasterSchedule")
        initial_count = cursor.fetchone()[0]
        print(f"📊 Initial count in MON_CustMasterSchedule: {initial_count}")
        
        # Get a small sample of new orders
        print("📥 Fetching new orders...")
        new_orders = get_new_orders(limit=3)  # Just 3 orders for testing
        print(f"Found {len(new_orders)} new orders")
        
        if len(new_orders) == 0:
            print("ℹ️ No new orders to process")
            return
            
        # Transform the orders
        print("🔄 Transforming orders...")
        customer_lookup = load_customer_mapping()
        transformed_orders = transform_order_data(new_orders, customer_lookup)
        print(f"Transformed {len(transformed_orders)} orders")
        
        # Convert to DataFrame
        df = pd.DataFrame(transformed_orders)
        print(f"DataFrame shape: {df.shape}")
        print("DataFrame columns:", list(df.columns))
        
        # Try to insert into staging
        print("💾 Inserting to staging table...")
        success = insert_orders_to_staging(df)
        
        if success:
            print("✅ Insert operation reported success")
            
            # Check count again
            cursor.execute("SELECT COUNT(*) FROM MON_CustMasterSchedule")
            final_count = cursor.fetchone()[0]
            print(f"📊 Final count in MON_CustMasterSchedule: {final_count}")
            
            if final_count > initial_count:
                print(f"🎉 Successfully inserted {final_count - initial_count} records!")
                
                # Show the most recent records
                cursor.execute("""
                    SELECT TOP 5 
                        CUSTOMER_CODE, ORDER_NUMBER, ORDER_TYPE, 
                        ORIGIN_DATE, DUE_DATE, CREATED_AT
                    FROM MON_CustMasterSchedule 
                    ORDER BY CREATED_AT DESC
                """)
                
                recent_records = cursor.fetchall()
                print("\n📋 Most recent records:")
                for record in recent_records:
                    print(f"  {record[0]} | {record[1]} | {record[2]} | {record[3]} | {record[4]} | {record[5]}")
                    
            else:
                print("⚠️ No new records were actually inserted")
        else:
            print("❌ Insert operation failed")
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
