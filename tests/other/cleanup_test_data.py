#!/usr/bin/env python3
"""
Test Data Cleanup Script

This script safely removes test data from the MON_CustMasterSchedule table.
Test data is identified by:
- Staging IDs in range 1000-10000 (our test/staging IDs, not Monday.com's large IDs like 9200517596)
- Specific patterns in customer names or order numbers that indicate test data

SAFETY: This script will first show what would be deleted, then ask for confirmation.

IMPORTANT: Monday.com item IDs are large numbers (e.g., 9200517596). Our staging IDs are 1000-10000.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pandas as pd
from customer_master_schedule.order_queries import get_database_connection

def identify_test_records():
    """
    Identify test records in the staging table
    
    Returns:
        pandas.DataFrame: Test records to be cleaned up
    """
    conn = get_database_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return pd.DataFrame()
    
    try:        # Query for potential test records
        query = """
        SELECT 
            [Item ID],
            [CUSTOMER],
            [AAG ORDER NUMBER],
            [STYLE],
            [COLOR],
            [Title],
            [Group]
        FROM [dbo].[MON_CustMasterSchedule]
        WHERE 
            ([Item ID] IS NOT NULL 
             AND ISNUMERIC([Item ID]) = 1 
             AND TRY_CAST([Item ID] AS BIGINT) >= 1000 
             AND TRY_CAST([Item ID] AS BIGINT) <= 10000)  -- Staging ID range
            OR [CUSTOMER] LIKE '%TEST%'
            OR [AAG ORDER NUMBER] LIKE '%TEST%'
            OR [AAG ORDER NUMBER] LIKE '%test%'
            OR [Title] LIKE '%Test%'
        ORDER BY TRY_CAST([Item ID] AS BIGINT) ASC
        """
        
        df = pd.read_sql(query, conn)
        return df
        
    except Exception as e:
        print(f"❌ Error querying test records: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def delete_test_records(item_ids):
    """
    Delete test records by Item ID
    
    Args:
        item_ids: List of Item IDs to delete
        
    Returns:
        int: Number of records deleted
    """
    if not item_ids:
        print("No records to delete")
        return 0
    
    conn = get_database_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return 0
    
    try:
        cursor = conn.cursor()
        
        # Use parameterized query for safety
        placeholders = ','.join(['?'] * len(item_ids))
        delete_query = f"""
        DELETE FROM [dbo].[MON_CustMasterSchedule]
        WHERE [Item ID] IN ({placeholders})
        """
        
        cursor.execute(delete_query, item_ids)
        rows_deleted = cursor.rowcount
        conn.commit()
        
        print(f"✅ Successfully deleted {rows_deleted} test records")
        return rows_deleted
        
    except Exception as e:
        print(f"❌ Error deleting test records: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()

def main():
    """Main cleanup process with safety checks"""
    print("🧹 TEST DATA CLEANUP SCRIPT")
    print("=" * 50)
    
    # Step 1: Identify test records
    print("🔍 Step 1: Identifying test records...")
    test_records = identify_test_records()
    
    if test_records.empty:
        print("✅ No test records found - staging table is already clean!")
        return
    
    print(f"📊 Found {len(test_records)} potential test records:")
    print()
    print("Preview of records to be deleted:")
    print("-" * 80)
    
    # Show preview (limit to first 10 for readability)
    preview = test_records.head(10)
    for _, row in preview.iterrows():
        print(f"ID: {row['Item ID']:<6} | Customer: {row['CUSTOMER']:<20} | Order: {row['AAG ORDER NUMBER']:<15}")
    
    if len(test_records) > 10:
        print(f"... and {len(test_records) - 10} more records")
    
    print("-" * 80)
    
    # Step 2: Safety confirmation
    print()
    print("⚠️  SAFETY CHECK:")
    print("   This will PERMANENTLY DELETE the above records from the database.")
    print("   Please review the list carefully.")
    print()
    
    while True:
        response = input("Do you want to proceed with deletion? (yes/no/preview): ").strip().lower()
        
        if response == 'yes':
            break
        elif response == 'no':
            print("❌ Cleanup cancelled by user")
            return
        elif response == 'preview':
            print("\nFull list of records to be deleted:")
            print(test_records[['Item ID', 'CUSTOMER', 'AAG ORDER NUMBER']].to_string())
            print()
        else:
            print("Please enter 'yes', 'no', or 'preview'")
    
    # Step 3: Perform deletion
    print("\n🗑️  Step 2: Deleting test records...")
    item_ids = test_records['Item ID'].tolist()
    deleted_count = delete_test_records(item_ids)
    
    if deleted_count > 0:
        print(f"✅ Cleanup completed successfully!")
        print(f"   Deleted {deleted_count} test records")
        print(f"   Staging table is now clean")
    else:
        print("❌ Cleanup failed - no records were deleted")

if __name__ == "__main__":
    main()
