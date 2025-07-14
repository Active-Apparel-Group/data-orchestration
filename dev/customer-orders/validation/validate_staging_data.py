#!/usr/bin/env python3
"""
Quick validation script to check staging table data
"""

import sys
from pathlib import Path

# Add project paths
current_dir = Path(__file__).parent
repo_root = current_dir.parent.parent
sys.path.insert(0, str(repo_root / "utils"))

import db_helper as db

def validate_staging_data():
    print("=" * 60)
    print("STAGING DATA VALIDATION")
    print("=" * 60)
      # Check orders in staging
    orders_query = """
    SELECT 
        COUNT(*) as total_orders,
        stg_status,
        COUNT(DISTINCT stg_batch_id) as batch_count
    FROM [dbo].[STG_MON_CustMasterSchedule] 
    GROUP BY stg_status
    ORDER BY stg_status
    """
    
    print("\n1. STAGING ORDERS")
    print("-" * 30)
    try:
        orders_result = db.run_query("ORDERS", orders_query)
        if not orders_result.empty:
            for _, row in orders_result.iterrows():
                print(f"   Status: {row['stg_status']}")
                print(f"   Orders: {row['total_orders']}")
                print(f"   Batches: {row['batch_count']}")
                print()
        else:
            print("   No orders found in staging table")
    except Exception as e:
        print(f"   ERROR: {e}")
      # Check subitems in staging
    subitems_query = """
    SELECT 
        COUNT(*) as total_subitems,
        stg_status,
        COUNT(DISTINCT stg_batch_id) as batch_count
    FROM [dbo].[STG_MON_CustMasterSchedule_Subitems] 
    GROUP BY stg_status
    ORDER BY stg_status
    """
    
    print("\n2. STAGING SUBITEMS")
    print("-" * 30)
    try:
        subitems_result = db.run_query("ORDERS", subitems_query)
        if not subitems_result.empty:
            for _, row in subitems_result.iterrows():
                print(f"   Status: {row['stg_status']}")
                print(f"   Subitems: {row['total_subitems']}")
                print(f"   Batches: {row['batch_count']}")
                print()
        else:
            print("   No subitems found in staging table")
    except Exception as e:
        print(f"   ERROR: {e}")
        
    # Sample data from orders
    sample_query = """
    SELECT TOP 3
        [CUSTOMER],        [AAG ORDER NUMBER],
        [STYLE],
        [COLOR],
        stg_batch_id,
        stg_status,
        stg_created_date
    FROM [dbo].[STG_MON_CustMasterSchedule] 
    ORDER BY stg_created_date DESC
    """
    
    print("\n3. SAMPLE STAGING DATA")
    print("-" * 30)
    try:
        sample_result = db.run_query("ORDERS", sample_query)
        if not sample_result.empty:
            for _, row in sample_result.iterrows():
                print(f"   Customer: {row['CUSTOMER']}")
                print(f"   Order: {row['AAG ORDER NUMBER']}")
                print(f"   Style: {row['STYLE']} - {row['COLOR']}")
                print(f"   Batch: {str(row['stg_batch_id'])[:8]}...")
                print(f"   Status: {row['stg_status']}")
                print(f"   Created: {row['stg_created_date']}")
                print()
        else:
            print("   No sample data found")
    except Exception as e:
        print(f"   ERROR: {e}")

if __name__ == "__main__":
    validate_staging_data()
