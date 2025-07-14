#!/usr/bin/env python3
"""
Batch-update Customer FOB (USD) on the Planning board.

• Extracts Item ID + FINAL FOB from ORDERS_UNIFIED ↔ MON_COO_Planning join.
• Sends **change_multiple_column_values** mutations in packs of 20
  (≈ 520 complexity/req ≅ two full batches per minute – well under the 1 000 limit).
• Keeps repo standards: find_repo_root, db_helper / logger_helper, UTF-8 console fix.
"""

import os, sys, logging, warnings, json, time, urllib3, math
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import pandas as pd
import requests

# ─── repo-root / utils path ────────────────────────────────────────────────────
def find_repo_root() -> Path:
    p = Path(__file__).resolve()
    while p.parent != p:
        if (p / "utils" / "db_helper.py").exists():
            return p
        p = p.parent
    raise RuntimeError("Repo root with utils not found")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

import db_helper as db
import logger_helper

logger = logger_helper.get_logger("update_customer_fob")
config  = db.load_config()

# ─── console UTF-8 fix (Windows) ───────────────────────────────────────────────
for h in getattr(getattr(logger, "_logger", logger), "handlers", []):
    if isinstance(h, logging.StreamHandler):
        try:
            h.stream.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass

urllib3.disable_warnings()
warnings.filterwarnings("ignore", category=UserWarning, module="pandas")

# ─── SQL extract ───────────────────────────────────────────────────────────────
SELECT_FOB = """
SELECT
    mon.[Item ID]            AS item_id,
    CAST(ou.[FINAL FOB (USD)] AS DECIMAL(18,2)) AS final_fob_usd,
    mon.[Customer FOB (USD)] AS customer_fob_usd
FROM ORDERS_UNIFIED ou
JOIN MON_COO_Planning mon
  ON ou.[AAG ORDER NUMBER] = mon.[AAG ORDER NUMBER]
 AND ou.[CUSTOMER STYLE]   = mon.[STYLE CODE]
WHERE
    ISNUMERIC(ou.[FINAL FOB (USD)]) = 1
  AND CAST(ou.[FINAL FOB (USD)] AS DECIMAL(18,2)) > 0
  AND mon.[Customer FOB (USD)] <> CAST(ou.[FINAL FOB (USD)] AS DECIMAL(18,2))
"""

# ─── Monday API setup ──────────────────────────────────────────────────────────
MONDAY_API_URL = "https://api.monday.com/v2"
BOARD_ID       = 8709134353
TOKEN          = (
    os.getenv("MONDAY_API_KEY")
    or config.get("apis", {}).get("monday", {}).get("api_token")
)
if not TOKEN:
    raise EnvironmentError("MONDAY_API_KEY missing (env or config).")

HEADERS = {"Authorization": TOKEN, "Content-Type": "application/json"}

# ─── helpers ───────────────────────────────────────────────────────────────────
def extract_fob() -> pd.DataFrame:
    return db.run_query(SELECT_FOB, "orders")

def build_batch_mutation(rows: List[Tuple[int, str]]) -> str:
    """
    rows → [(item_id, fob_string), …]  (max 50 by Monday’s docs – we use 20)
    Returns a GraphQL mutation with aliases m0…mn.
    """
    ops = []
    for idx, (item_id, fob) in enumerate(rows):
        col_vals = json.dumps({"numeric_mkp4q1rv": fob}).replace('"', '\\"')
        ops.append(
            f"""m{idx}: change_multiple_column_values(
                    item_id: {item_id},
                    board_id: {BOARD_ID},
                    column_values: "{col_vals}"
               ){{ id }}"""
        )
    return f"mutation {{\n  {'  '.join(ops)}\n}}"

def post_mutation(mutation: str):
    r = requests.post(MONDAY_API_URL, headers=HEADERS,
                      json={"query": mutation}, timeout=30)
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])

def push_batches(df: pd.DataFrame, batch_size: int = 20):
    rows   = [(int(r.item_id), str(r.final_fob_usd)) for r in df.itertuples()]
    total  = len(rows)
    chunks = math.ceil(total / batch_size)
    ok, fail = 0, 0

    for n in range(chunks):
        slice_ = rows[n*batch_size : (n+1)*batch_size]
        mutation = build_batch_mutation(slice_)
        try:
            post_mutation(mutation)
            ok += len(slice_)
        except Exception as exc:
            fail += len(slice_)
            logger.warning("Batch %s failed → %s", n+1, exc)

        if (n+1) % 5 == 0 or n == chunks-1:
            pct = ok * 100 / total
            logger.info("Progress: %d / %d (%.1f %%)", ok, total, pct)

        # 520 complexity per 20-item batch → we can safely send ~1.9 batches/min
        # Sleep 1 s to stay ~ < 2 calls/s, tweak if desired
        time.sleep(1)

    logger.info("Updates done – %s succeeded, %s failed", ok, fail)

# ─── main ──────────────────────────────────────────────────────────────────────
def main():
    logger.info("Workflow started — %s",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    try:
        df = extract_fob()
        logger.info("Rows needing update: %s", f"{len(df):,}")

        if df.empty:
            logger.info("Nothing to update – exiting.")
            return

        push_batches(df)

        logger.info("✅ Completed %s", datetime.now().strftime("%H:%M:%S"))
    except Exception:
        logger.exception("❌ Workflow failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
