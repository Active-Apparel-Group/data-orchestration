#!/usr/bin/env python3
"""
Canonical Customer Alias Loader - YAML to SQL (No-Args Edition)
================================================================

Loads the canonical/alias customer map from a YAML file to a SQL Server table.
- Always loads from a fixed YAML and writes to a fixed database/table.
- Canonical always first (ref_index=0), aliases after (ref_index>0).
- Deduplicates (canonical, alias) combos.
- Atomic swap for zero-downtime production loads.

Edit the CONFIG section below for your repo.

Author: [Your Team]
Date: [Today]
"""

import sys, os, time, yaml, pandas as pd
from pathlib import Path

# ========== CONFIG (Set these paths/table names for your repo) ==========

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # edit if repo layout differs
YAML_PATH = REPO_ROOT / "utils" / "canonical_customers.yaml"
DB_NAME = "orders"
PROD_TABLE = "map_canonical_customer"
STAGING_TABLE = "swp_map_canonical_customer"

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

# Modern imports from project
from pipelines.utils import db
from pipelines.utils import logger
import staging_helper

logger = logger.get_logger("load_customer_alias_map")

# ========== Main Logic ==========

def load_yaml(path: Path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def build_alias_df(yaml_data):
    rows = []
    for customer in yaml_data.get('customers', []):
        canonical = customer['canonical']
        rows.append({
            'canonical': canonical,
            'name': canonical,
            'ref_index': 0,
            'status': customer.get('status', ''),
        })
        seen = {canonical}
        for idx, alias in enumerate(customer.get('aliases', []), 1):
            if alias not in seen:
                rows.append({
                    'canonical': canonical,
                    'name': alias,
                    'ref_index': idx,
                    'status': customer.get('status', ''),
                })
                seen.add(alias)
    df = pd.DataFrame(rows).drop_duplicates(subset=['canonical', 'name']).reset_index(drop=True)
    return df

def prepare_staging_table(df):
    column_type_map = {
        "canonical": "NVARCHAR(100)",
        "name": "NVARCHAR(100)",
        "ref_index": "INT",
        "status": "NVARCHAR(50)"
    }
    staging_helper.prepare_staging_table(df, STAGING_TABLE, PROD_TABLE, DB_NAME, column_type_map=column_type_map)

def load_to_staging(df):
    batch_size = 500
    staging_helper.load_to_staging_table(df, STAGING_TABLE, DB_NAME, batch_size=batch_size)

def atomic_swap():
    staging_helper.atomic_swap_tables(STAGING_TABLE, PROD_TABLE, DB_NAME)

def main():
    logger.info(f"Loading canonical mapping from: {YAML_PATH}")
    yaml_data = load_yaml(YAML_PATH)

    df = build_alias_df(yaml_data)
    logger.info(f"Rows in alias mapping (deduped): {len(df)}")

    prepare_staging_table(df)
    load_to_staging(df)
    atomic_swap()

    logger.info(f"SUCCESS: Canonical alias map loaded and swapped into {PROD_TABLE}.")

if __name__ == "__main__":
    main()
