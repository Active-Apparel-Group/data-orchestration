"""
Examples of using db_helper.py for SQL workflows.
"""

import db_helper as db
from collections import defaultdict

def main():
  # --- 1. Simple SELECT (inline SQL) ---
  orders_sample = db.run_query("SELECT TOP 5 * FROM dbo.ORDERS_UNIFIED", "orders")
  print("Sample from ORDERS:\n", orders_sample)

if __name__ == "__main__":
    main()
