#!/usr/bin/env python3
"""
Quick script to check what customers are available in ORDERS_UNIFIED
"""

import sys
from pathlib import Path

# Add project paths
current_dir = Path(__file__).parent
repo_root = current_dir.parent.parent
sys.path.insert(0, str(repo_root / "utils"))

import db_helper as db

def check_customers():
    query = """
    SELECT Customer, COUNT(*) as order_count 
    FROM ORDERS_UNIFIED 
    GROUP BY Customer 
    ORDER BY order_count DESC
    """
    
    print("Available customers in ORDERS_UNIFIED:")
    result = db.run_query("ORDERS", query)
    for _, row in result.head(15).iterrows():
        print(f"  {row['Customer']}: {row['order_count']} orders")

if __name__ == "__main__":
    check_customers()
