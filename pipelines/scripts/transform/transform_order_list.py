#!/usr/bin/env python3
"""
ORDER_LIST Staging Data Cleaner - Post-ETL Modular SQL Runner
=============================================================

Runs post-staging SQL scripts (delete blanks, fill-down, canonical mapping, etc)
in sequence before atomic swap of ORDER_LIST. Modular SQL lives in:
    db/sql/order_list_transform/*.sql

- Each SQL file is executed in order.
- SELECTs (validation) are logged, errors raised if validation fails.
- Works with your project utilities and DB connection.

Edit CONFIG section as needed.

Author: [Your Team]
Date: [Today]
"""

import sys, os
from pathlib import Path

# ========== CONFIG ==========
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SQL_DIR = REPO_ROOT / "sql" / "operations" / "order_list_transform"
DB_NAME = "orders"

SQL_FILES = [
    "01_delete_null_rows.sql",
    "02_filldown_customer_name.sql",
    "03_check_customer_name_blanks.sql",
    "04_copy_customer_to_source_customer.sql",
    "05_update_canonical_customer_name.sql",
    "06_validate_canonical_mapping.sql",
    "10_group_name_create.sql",
    "11_group_name_match_existing.sql",
]

# ─────────────────── Repository Root & Utils Import ───────────────────
def find_repo_root() -> Path:
    """Find repository root by looking for pipelines/utils folder"""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current.parent.parent / "pipelines" / "utils").exists():
            return current.parent.parent
        current = current.parent
    raise RuntimeError("Could not find repository root with utils/ folder")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db
from pipelines.utils import logger

logger = logger.get_logger("order_list_post_stage_clean")

def run_post_stage_sql():
    for sql_file in SQL_FILES:
        sql_path = SQL_DIR / sql_file
        logger.info(f"Running {sql_file} ...")
        with open(sql_path, "r", encoding="utf-8") as f:
            sql = f.read().strip()

        if sql.upper().startswith("SELECT"):
            df = db.run_query(sql, DB_NAME)
            # Optional: fail if validation/SELECT returns issues
            if "blank_count" in df.columns and df["blank_count"].iloc[0] > 0:
                raise Exception(f"{sql_file}: blank CUSTOMER NAME records remain after fill-down.")
        else:
            db.execute(sql, DB_NAME)
            logger.info(f"Executed {sql_file}.")

    logger.info("All post-staging SQL scripts completed.")

def main():
    logger.info(f"=== POST-STAGING DATA CLEANING: {SQL_DIR} ===")
    run_post_stage_sql()
    logger.info("SUCCESS: ORDER_LIST staging data cleaned and canonicalized.")

if __name__ == "__main__":
    main()
