#!/usr/bin/env python3
"""
Monday → Azure SQL ETL (pandas + db_helper version, FAST REFACTOR)
-------------------------------------------------------------------
* Loads board config from config/boards/board_<BOARD_ID>.toml
* Uses direct requests for Monday GraphQL API
* Fetches all items in batches, builds DataFrame flat
* Uses helper modules for DB, staging, logging, as before
* Fast, vectorized type conversions post-DataFrame
* Zero-downtime: truncate staging, bulk insert, sp_rename swap
"""

import os, sys, re, tomli, pandas as pd
from pathlib import Path
from datetime import datetime
import logging, time, requests, tomli_w
from tqdm import tqdm

# ─────────────────── find utils/ and import helpers ───────────────────
def find_repo_root() -> Path:
    cur = Path(__file__).resolve()
    while cur.parent != cur:
        if (cur / "utils" / "db_helper.py").exists():
            return cur
        cur = cur.parent
    raise RuntimeError("repo root with ./utils/db_helper.py not found")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

import db_helper as db
import logger_helper
import staging_helper

logger = logger_helper.get_logger("monday_refresh")

# ─────────────── runtime env vars ────────────────
API_VERSION   = os.getenv("MONDAY_API_VERSION", "2025-04")
MONDAY_TOKEN  = os.getenv("MONDAY_API_KEY")

API_URL = "https://api.monday.com/v2"
HEADERS = {
    "Authorization": MONDAY_TOKEN,
    "API-Version": API_VERSION,
    "Content-Type": "application/json"
}

# ─────────────── TOML loading function with auto-generation ─────────────────
def load_board_config(board_id: int):
    rules_path = repo_root / f"monday-etl/config/boards/board_{board_id}.toml"
    
    # 🚀 AUTO-TEMPLATE CREATION: If config doesn't exist, create it
    if not rules_path.exists():
        logger.info(f"Board config not found for {board_id}, auto-creating template...")
        
        try:
            # Import template generator (lazy import to avoid circular dependencies)
            sys.path.insert(0, str(repo_root / "monday-etl"))
            from template_generator import create_template_and_guide_user
            
            # Create template and guide user
            created_path = create_template_and_guide_user(board_id)
            
            # Exit gracefully to let user review the template
            logger.info(f"Template created at {created_path}")
            logger.info("ETL exiting to allow template review. Please re-run after customization.")
            sys.exit(0)
            
        except Exception as e:
            logger.error(f"❌ Failed to auto-create template for board {board_id}: {e}")
            raise FileNotFoundError(f"Board config missing and auto-creation failed: {rules_path}")

    # Load existing config
    cfg = tomli.load(open(rules_path, "rb"))
    meta = cfg.get("meta", {})
    config = {
        'cfg': cfg,
        'rules_path': rules_path,
        'meta': meta,
        'RULE_DEFAULT': cfg["default"],
        'COL_OVERRIDES': cfg.get("override", {}),
        'EXCL_IDS': set(cfg.get("exclude", {}).get("ids", [])),
        'EXCL_TITLES': set(cfg.get("exclude", {}).get("titles", [])),
        'OVR_FALLBACK': {"sql": "NVARCHAR(100)", "db_alias": ""},
        'DB_NAME': meta.get("db_name", "orders"),
        'TABLE_NAME': meta.get("table_name", "MON_Table"),
    }
    config['STAGE_TABLE'] = f"swp_{config['TABLE_NAME']}"
    return config

# ─────────────── Monday GraphQL direct requests ───────────────
def gql_request(query, variables=None, max_retries=3, timeout=60):
    for attempt in range(max_retries):
        try:
            payload = {"query": query}
            if variables:
                payload["variables"] = variables
            response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=timeout)
            response.raise_for_status()
            return response.json()["data"]
        except requests.RequestException as e:
            if attempt < max_retries - 1:
                logger.warning(f"API request failed (attempt {attempt+1}): {e}")
                time.sleep(2 ** attempt)
                continue
            raise

def fetch_items_count(board_id: int):
    query = """
    query ($ids: [ID!]!) {
      boards(ids: $ids) { items_count }
    }
    """
    res = gql_request(query, {"ids": [board_id]})
    return res["boards"][0]["items_count"]

# ─────────────── rules + column processing ────────
def rule_for_column(col: dict, config: dict) -> dict | None:
    if col["id"] in config['EXCL_IDS'] or col["title"] in config['EXCL_TITLES']:
        return None
    base = config['RULE_DEFAULT'].get(col["type"], {})
    over = config['COL_OVERRIDES'].get(col["id"]) or config['COL_OVERRIDES'].get(col["title"], {})
    if over == {}:
        over = config['OVR_FALLBACK']
    merged = {**base, **over}
    if not merged.get("field") or merged.get("include", True) is False:
        return None
    return merged

def fetch_schema(board_id: int, config: dict):
    query = """
    query ($ids:[ID!]!){
      boards(ids:$ids){
        item_terminology
        columns{
          id
          title
          type
          settings_str
        }
      }
    }"""
    data = gql_request(query, {"ids": [board_id]})
    board = data["boards"][0]
    term = board["item_terminology"] or "Item"
    cols = {}
    for col in board["columns"]:
        rule = rule_for_column(col, config)
        if rule:
            cols[col["id"]] = { **col, **rule }
    return term, cols

# ─────────────── Bulk fetch Monday items ───────────────
def fetch_all_items(board_id, limit=100):
    """Fetch all items with pagination in one batch"""
    items = []
    cursor = None
    while True:
        cursor_arg = f', cursor: "{cursor}"' if cursor else ''
        query = f'''
        query {{
          boards(ids: {board_id}) {{
            items_page(limit: {limit}{cursor_arg}) {{
              cursor
              items {{
                id
                name
                updated_at
                group {{ title }}
                column_values {{
                  id
                  text
                  value
                  ... on MirrorValue         {{ display_value }}
                  ... on BoardRelationValue  {{ display_value }}
                  ... on FormulaValue        {{ display_value }}
                  ... on DependencyValue     {{ display_value }}
                  ... on StatusValue         {{ label }}
                  ... on DropdownValue       {{ text }}
                  ... on PeopleValue         {{ text }}
                  ... on ItemIdValue         {{ item_id }}
                }}
              }}
            }}
          }}
        }}
        '''
        data = gql_request(query)
        page = data["boards"][0]["items_page"]
        batch = page["items"]
        items.extend(batch)
        cursor = page.get("cursor")
        if not cursor or not batch:
            break
        time.sleep(0.1)
    return items

# ─────────────── Fast DataFrame build ───────────────
def extract_value_fast(cv, meta):
    t = meta["type"]
    if t == "date":
        if cv.get("text"): return cv["text"]
        if cv.get("value"):
            try:
                import json
                v = json.loads(cv["value"])
                return v.get("date")
            except Exception: return None
    if t in ("numbers", "numeric"):
        try:
            return float(str(cv.get(meta["field"], "")).replace(",", ""))
        except Exception:
            return None
    return cv.get(meta["field"]) or cv.get("text") or cv.get("label") or None

def build_dataframe_fast(items, cols_meta, term):
    records = []
    for it in tqdm(items, desc="Building DataFrame", unit="item"):
        row = {
            term:        it["name"],
            "UpdateDate": it["updated_at"],
            "Group":      it["group"]["title"],
            "Item ID":    int(it["id"])
        }
        for cv in it["column_values"]:
            meta = cols_meta.get(cv["id"])
            if not meta:
                continue
            db_col = meta.get("db_alias") or meta["title"]
            val = extract_value_fast(cv, meta)
            row[db_col] = val
        records.append(row)
    df = pd.DataFrame(records)
    return df

def clean_dataframe(df):
    # Vectorized date conversion
    date_cols = [c for c in df.columns if "DATE" in c.upper() or c in ["UpdateDate"]]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.date

    # Detect numeric columns (excluding IDs)
    for col in df.columns:
        if col == "Item ID": continue
        # Only process object dtype columns
        if df[col].dtype == object:
            # Use astype(str) before .str.replace/.isnumeric
            ser = df[col].astype(str)
            # Ignore nulls for numeric detection
            mask = ser.notnull() & (ser != 'None') & (ser != 'nan') & (ser != 'NaT')
            if mask.any() and ser[mask].str.replace('.', '', 1).str.isnumeric().all():
                df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def make_sql_safe(df):
    # Convert all datetime.date and datetime to string
    for col in df.columns:
        # Convert date/datetime to string
        if df[col].dtype == "O":
            sample = df[col].dropna().iloc[0] if df[col].notna().any() else None
            # Check for date/datetime type by sample
            if sample is not None and (
                isinstance(sample, datetime) or
                str(type(sample)).startswith("<class 'datetime.date")
            ):
                df[col] = df[col].apply(lambda x: x.strftime("%Y-%m-%d") if pd.notnull(x) else None)
            # Convert bool to int (SQL Server doesn't like bool type)
            elif sample is not None and isinstance(sample, bool):
                df[col] = df[col].astype(int)
    return df


# ZERO-DOWNTIME: staging helpers unchanged
def prepare_staging_table(df: pd.DataFrame, config: dict):
    exclude_titles = set(config['EXCL_TITLES'])
    filtered_df = df.loc[:, ~df.columns.isin(exclude_titles)]
    logger.info("Column filtering: %d total -> %d included, %d excluded",
                len(df.columns), len(filtered_df.columns), len(df.columns) - len(filtered_df.columns))
    staging_helper.prepare_staging_table(filtered_df, config['STAGE_TABLE'],
                                         config['TABLE_NAME'], config['DB_NAME'])
    return filtered_df

def load_to_staging_table(df: pd.DataFrame, config: dict):
    optimal_batch_size = min(1000, max(100, len(df) // 10))
    logger.info("Using batch size: %d for %d rows", optimal_batch_size, len(df))
    staging_helper.load_to_staging_table(df, config['STAGE_TABLE'],
                                         config['DB_NAME'], batch_size=optimal_batch_size)

def atomic_swap_tables(config: dict):
    staging_helper.atomic_swap_tables(config['STAGE_TABLE'], config['TABLE_NAME'], config['DB_NAME'])

# ─────────────── main orchestration ─────────────
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Refresh a Monday.com board into SQL")
    parser.add_argument("-b", "--board", type=int, help="Override BOARD_ID from CLI")
    args = parser.parse_args()

    if args.board:
        os.environ["BOARD_ID"] = str(args.board)

    BOARD_ID = int(os.getenv("BOARD_ID", 8685586257))
    logger.info("Starting Monday.com ETL for board %d", BOARD_ID)
    config = load_board_config(BOARD_ID)
    logger.info("Board %s -> %s.dbo.%s (API %s)", BOARD_ID, config['DB_NAME'],
                config['TABLE_NAME'], API_VERSION)

    total_start = time.time()
    # 1. Fetch schema (fast)
    term, cols_meta = fetch_schema(BOARD_ID, config)
    # 2. Fetch all items (fast)
    items = fetch_all_items(BOARD_ID)
    logger.info("Fetched %d items", len(items))
    # 3. Build DataFrame (fast)
    df = build_dataframe_fast(items, cols_meta, term)
    logger.info("DataFrame built: %d rows x %d columns", len(df), len(df.columns))
    # 4. Clean DataFrame
    df = clean_dataframe(df)
    df = make_sql_safe(df)
    # 5. Proceed with DB pipeline
    filtered_df = prepare_staging_table(df, config)
    load_to_staging_table(filtered_df, config)
    atomic_swap_tables(config)

    total_elapsed = time.time() - total_start
    rows_per_sec = len(filtered_df) / total_elapsed if total_elapsed > 0 else 0
    logger.info("SUCCESS: %d rows now live in %s.dbo.%s", len(filtered_df), config['DB_NAME'], config['TABLE_NAME'])
    logger.info("Total ETL time: %.2fs (%.0f rows/sec)", total_elapsed, rows_per_sec)
    if total_elapsed > 60:
        logger.warning("WARNING: ETL took longer than 1 minute. Consider further optimization.")
    elif rows_per_sec < 100:
        logger.warning("WARNING: Processing rate below 100 rows/sec. Monitor performance.")
    else:
        logger.info("Performance within acceptable range")


if __name__ == "__main__":
    main()
