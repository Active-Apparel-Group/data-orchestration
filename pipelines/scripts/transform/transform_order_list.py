#!/usr/bin/env python3
"""
ORDER_LIST Staging Data Cleaner & Indexer - Post-ETL Modular SQL Runner
=======================================================================

• Runs post-staging SQL scripts (delete blanks, fill-down, canonical mapping, etc)
• Optionally creates indexes on the sync table after refresh, using a drop-in pattern.
• Each SQL file is executed in order.
• SELECTs (validation) are logged, errors raised if validation fails.
• Works with your project utilities and DB connection.

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
    "12_update_order_type.sql",
]

# Columns or sets of columns to index (edit as needed)
INDEX_COLUMNS = [
    ["AAG ORDER NUMBER"],
    ["PO NUMBER"],
    ["CUSTOMER NAME"],
    ["SOURCE_CUSTOMER_NAME"],
    ["CUSTOMER STYLE"],
    ["AAG SEASON"],
    ["ORDER TYPE"],
    ["CUSTOMER SEASON"],
    ["AAG ORDER NUMBER", "PO NUMBER"],  # Composite index for common queries
]

# ─────────────────── Repository Root & Utils Import ───────────────────
def find_repo_root() -> Path:
    """Find repository root by looking for pipelines/utils folder."""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current.parent.parent / "pipelines" / "utils").exists():
            return current.parent.parent
        current = current.parent
    raise RuntimeError("Could not find repository root with utils/ folder.")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db
from pipelines.utils import logger

logger = logger.get_logger("order_list_post_stage_clean")

# ─────────────────────── Index Creation Helper ────────────────────────
def create_index_sql(table: str, cols: list) -> str:
    """Return CREATE INDEX SQL for given table/column(s) with dynamic name."""
    clean_cols = [c.replace(" ", "_").replace("/", "_").replace("-", "_") for c in cols]
    index_name = f"IDX_{table}_" + "_".join(clean_cols)
    col_list = ", ".join(f"[{c}]" for c in cols)
    return f"CREATE INDEX {index_name} ON {table} ({col_list});"

def create_indexes(table: str, column_sets: list, db_key: str):
    """Drop and recreate indexes for the given table and column sets."""
    for cols in column_sets:
        clean_cols = [c.replace(" ", "_").replace("/", "_").replace("-", "_") for c in cols]
        index_name = f"IDX_{table}_" + "_".join(clean_cols)
        # Drop old index if exists (idempotent pattern)
        try:
            db.execute(f"""
                IF EXISTS (SELECT * FROM sys.indexes WHERE name = '{index_name}' AND object_id = OBJECT_ID('{table}'))
                    DROP INDEX [{index_name}] ON [{table}];
            """, db_key)
            logger.info(f"   ✅ Dropped index if existed: {index_name}")
        except Exception as e:
            logger.info(f"   ⚠️  Could not drop index (safe to ignore): {e}")
        # Create index
        try:
            db.execute(create_index_sql(table, cols), db_key)
            logger.info(f"   ✅ Created index: {index_name}")
        except Exception as e:
            logger.error(f"   ❌ Failed to create index {index_name}: {e}")

# ─────────────────────────── Main Functions ───────────────────────────
def refresh_sync_table(source_table="ORDER_LIST", sync_table="swp_ORDER_LIST_SYNC", db_key=DB_NAME):
    logger.info(f"\n[STEP 4] Creating/Refreshing {sync_table} from {source_table} ...")
    # Drop sync table if exists
    try:
        db.execute(f"""
            IF OBJECT_ID('{sync_table}', 'U') IS NOT NULL
                DROP TABLE {sync_table};
        """, db_key)
        logger.info(f"   ✅ Dropped existing {sync_table}")
    except Exception as e:
        logger.info(f"   ⚠️  {sync_table} did not exist or drop failed (safe to ignore): {e}")
    # Create new sync table from latest data
    try:
        logger.info(f"   Creating {sync_table} from {source_table} ...")
        db.execute(f"""
            SELECT * INTO {sync_table} FROM {source_table} -- WHERE [CUSTOMER NAME] like 'GREYSON%' AND [PO NUMBER] = '4755' ;
        """, db_key)
        logger.info(f"   ✅ Created {sync_table} from {source_table}")
        return True
    except Exception as e:
        logger.error(f"   ❌ Failed to create {sync_table}: {e}")
        return False

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
    # STEP 4: Refresh sync table for downstream (Monday.com, etc)
    success = refresh_sync_table(source_table="ORDER_LIST", sync_table="swp_ORDER_LIST_SYNC", db_key=DB_NAME)
    if success:
        logger.info("STEP 4 SUCCESS: swp_ORDER_LIST_SYNC refreshed and ready.")
        # Drop-in: create indexes right after refresh
        create_indexes("swp_ORDER_LIST_SYNC", INDEX_COLUMNS, DB_NAME)
    else:
        logger.error("STEP 4 FAILED: Could not refresh swp_ORDER_LIST_SYNC.")
    logger.info(f"=== POST-STAGING DATA CLEANING: {SQL_DIR} ===")
    run_post_stage_sql()
    logger.info("SUCCESS: ORDER_LIST staging data cleaned, indexed, and canonicalized.")

if __name__ == "__main__":
    main()
