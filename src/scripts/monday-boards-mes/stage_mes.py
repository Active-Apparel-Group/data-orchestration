import os, sys, logging, warnings, urllib3
from datetime import datetime
from pathlib import Path
import pandas as pd

# ─── repo-root / utils path ────────────────────────────────────────────────────
def find_repo_root():
    p = Path(__file__).resolve()
    while p.parent != p:
        if (p / "utils" / "db_helper.py").exists():
            return p
        p = p.parent
    raise RuntimeError("Repo root with utils not found")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

import db_helper as db                   # central helper
import logger_helper                     # <- your wrapper

logger = logger_helper.get_logger("mes_zero_downtime_loader")

# --- UTF-8 console‐safety on Windows ----------------------------
base_logger = getattr(logger, "_logger", logger)
for h in getattr(base_logger, "handlers", []):
    if isinstance(h, logging.StreamHandler):
        try:
            h.stream.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass

urllib3.disable_warnings()
warnings.filterwarnings("ignore", category=UserWarning, module="pandas")

# ─── SQL templates ─────────────────────────────────────────────────────────────
SELECT_SRC = """
SELECT  order_no      AS [MO Number],
        style_no,
        closed_time_t,
        state,
        order_number,
        prep_number,
        cut_number,
        sew_number,
        finish_number,
        sample_number,
        defect_number,
        remain_number,
        cut_fdate,
        sew_fdate,
        finish_fdate,
        customer_name,
        customer_no,
        [Package scan] AS Package_scan,
        [Bucket Scan]  AS Bucket_Scan,
        [PNP Receive]  AS PNP_Receive,
        [big_ironing],
        -- new WIP and FG columns
        (cut_number - sew_number)       AS WIP_Cut,
        (sew_number - finish_number)   AS WIP_Sew,
        (finish_number - [PNP Receive]) AS WIP_Fin,
        [PNP Receive]                  AS FG_Qty
FROM    QuickData.dbo.rpt_operational_performance;
"""

CREATE_STAGE = """
IF OBJECT_ID('dbo.stg_MES_operational_performance') IS NULL
BEGIN
    CREATE TABLE dbo.stg_MES_operational_performance (
        MO_Number        NVARCHAR(50),
        style_no         NVARCHAR(50),
        closed_time_t    VARCHAR(10),
        state            VARCHAR(20),
        order_number     BIGINT NOT NULL DEFAULT 0,
        prep_number      BIGINT NOT NULL DEFAULT 0,
        cut_number       BIGINT NOT NULL DEFAULT 0,
        sew_number       BIGINT NOT NULL DEFAULT 0,
        finish_number    BIGINT NOT NULL DEFAULT 0,
        sample_number    BIGINT NOT NULL DEFAULT 0,
        defect_number    BIGINT NOT NULL DEFAULT 0,
        remain_number    BIGINT NOT NULL DEFAULT 0,
        cut_fdate        VARCHAR(20),
        sew_fdate        VARCHAR(20),
        finish_fdate     VARCHAR(20),
        customer_name    VARCHAR(50),
        customer_no      VARCHAR(50),
        Package_scan     BIGINT NOT NULL DEFAULT 0,
        Bucket_Scan      BIGINT NOT NULL DEFAULT 0,
        PNP_Receive      BIGINT NOT NULL DEFAULT 0,
        big_ironing      BIGINT NOT NULL DEFAULT 0,
        WIP_Cut          BIGINT NOT NULL DEFAULT 0,
        WIP_Sew          BIGINT NOT NULL DEFAULT 0,
        WIP_Fin          BIGINT NOT NULL DEFAULT 0,
        FG_Qty           BIGINT NOT NULL DEFAULT 0
    );
END
"""

INSERT_STAGE = """
INSERT INTO dbo.stg_MES_operational_performance
VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
"""

SWITCH_TABLES = """
BEGIN TRAN;

IF OBJECT_ID('dbo.MES_operational_performance_old') IS NOT NULL
    DROP TABLE dbo.MES_operational_performance_old;

IF OBJECT_ID('dbo.MES_operational_performance') IS NOT NULL
    EXEC sp_rename 'dbo.MES_operational_performance',
                   'MES_operational_performance_old';

EXEC sp_rename 'dbo.stg_MES_operational_performance',
               'MES_operational_performance';

DROP TABLE dbo.MES_operational_performance_old;

COMMIT;
"""

# ─── helpers ───────────────────────────────────────────────────────────────────
def extract_source() -> pd.DataFrame:
    return db.run_query(SELECT_SRC, "quickdata")

def load_stage(df: pd.DataFrame):
    df = df.where(pd.notnull(df), None)
    with db.get_connection("orders") as conn, conn.cursor() as cur:
        cur.execute(CREATE_STAGE)
        cur.execute("TRUNCATE TABLE dbo.stg_MES_operational_performance;")
        cur.fast_executemany = True
        cur.executemany(INSERT_STAGE, df.values.tolist())
        conn.commit()

def swap_tables():
    with db.get_connection("orders") as conn, conn.cursor() as cur:
        cur.execute(SWITCH_TABLES)
        conn.commit()

# ─── main ──────────────────────────────────────────────────────────────────────
def main():
    logger.info("Workflow started — %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    try:
        logger.info("Extracting from quickdata…")
        df = extract_source()
        logger.info("Rows pulled: %s", f"{len(df):,}")

        logger.info("Loading stage in ORDERS…")
        load_stage(df)

        logger.info("Swapping tables atomically…")
        swap_tables()

        logger.info("✅ Completed in %s", datetime.now().strftime("%H:%M:%S"))
    except Exception:
        logger.exception("❌ Workflow failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
