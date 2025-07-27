"""
Debug Script: Customer Batch Pipeline Step-by-Step Tester
Purpose: Incrementally test each stage of the customer orders pipeline (batching, mapping, staging, subitem melt, etc.)
Location: tests/debug/debug_customer_batch_pipeline.py
"""

import sys
from pathlib import Path
import pandas as pd

# --- Standard import pattern for this project ---
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

# --- Import helpers ---
import db_helper as db
import logger_helper
import path_helper

# --- Import pipeline modules as needed ---
# from dev.customer-orders.customer_batch_processor import ... (add as needed)
# from dev.customer-orders.staging_processor import StagingProcessor

def main():
    logger = logger_helper.get_logger(__name__)
    logger.info("Starting step-by-step pipeline debug...")

    # --- Step 1: Load ORDERS_UNIFIED for a specific customer ---
    customer = "GREYSON"
    sql = """
    SELECT *
    FROM [dbo].[ORDERS_UNIFIED]
    WHERE [CUSTOMER NAME] = ?
    ORDER BY [AAG ORDER NUMBER]
    """
    with db.get_connection('orders') as conn:
        df = pd.read_sql(sql, conn, params=[customer])
    print(f"Loaded {len(df)} records for customer: {customer}")
    print("Columns:", list(df.columns))
    print("Sample rows:\n", df.head())

    # --- Step 2: (Placeholder) Mapping, staging, subitem melt, etc. ---
    # Add each step here, one at a time, as we debug and validate.
    # For example:
    # - Apply YAML mapping
    # - Canonicalize customer
    # - Compute Title
    # - Detect size columns and melt
    # - Prepare for staging insert

    # Example: Check for size columns with >0 values
    size_cols = [col for col in df.columns if col.upper() in ['XS', 'S', 'M', 'L', 'XL', 'XXL', '2XL', '3XL', '4XL', '5XL']]
    if size_cols:
        print("Detected size columns:", size_cols)
        size_gt0 = df[size_cols].gt(0).any(axis=1)
        print(f"Rows with any size > 0: {size_gt0.sum()} / {len(df)}")
        print(df.loc[size_gt0, ['AAG ORDER NUMBER'] + size_cols].head())
    else:
        print("No standard size columns detected.")

    # --- Add more steps as needed, one at a time ---

if __name__ == "__main__":
    main()