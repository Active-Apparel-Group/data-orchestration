"""
MES (Manufacturing Execution System) Data Processing and Planning Integration Script
This script processes MES operational performance data and integrates it with planning data
to provide comprehensive production status and work-in-progress (WIP) tracking.
Main Functions:
    find_repo_root(): Locates the repository root directory containing utils folder
    get_status(row): Determines production status based on cut, sew, and finish numbers
Processing Steps:
    1. Loads MES operational performance data from the 'orders' database
    2. Calculates production status for each record based on manufacturing stage
    3. Computes WIP quantities for cutting, sewing, and finishing stages
    4. Calculates finished goods quantities
    5. Loads and aggregates planning data by MO (Manufacturing Order) number
    6. Merges MES data with planning data to get total MO quantities
    7. Calculates percentage of MO completion if bulk PO quantity is available
    8. Flags variance between MES order qty and planned MO qty in three tiers
Production Status Categories:
    - NOT STARTED: No items finished (finish_number == 0)
    - CUTTING: Items cut but none sewn (cut_number > 0, sew_number == 0)
    - SEWING: Items sewn but none finished (sew_number > 0, finish_number == 0)
    - FINISHED: Some items finished but not complete (0 < finish_number < order_number)
    - COMPLETE: All items finished (finish_number == order_number)
Calculated Fields:
    - QTY WIP CUT: Work-in-progress in cutting stage
    - QTY WIP SEW: Work-in-progress in sewing stage  
    - QTY WIP FIN: Work-in-progress in finishing stage
    - QTY FG: Finished goods quantity
    - Pct_of_MO: Percentage of manufacturing order completed
    - Qty_Var_Pct: Absolute variance % between MES order_number and MO_Qty
    - Qty_Var_Flag: Tiered flag (0 ≤5%, 1 =5–10%, 2 >10%)
Dependencies:
    - pandas: Data manipulation and analysis
    - numpy: Numerical operations
    - db_helper: Database connection and query utilities
    - logger_helper: Logging functionality
Database Tables:
    - MES_operational_performance: Contains production tracking data
    - MON_COO_Planning: Contains planning and order information
"""
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
from datetime import datetime

def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils" / "db_helper.py").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

import db_helper as db
import logger_helper

logger = logger_helper.get_logger("mes_integration")

# 1) Load MES data
MES_TABLE = "MES_operational_performance"
df = pd.DataFrame(db.run_query(f"SELECT * FROM {MES_TABLE} ORDER BY [MO Number] DESC", db_key="orders"))

# unify MO_Number column
if "MO_Number" not in df.columns:
    if "MO Number" in df.columns:
        df["MO_Number"] = df["MO Number"]
    else:
        raise KeyError("MES DataFrame missing MO_Number")
    
# coalesce nulls to zero for all relevant numeric columns
num_cols = ["cut_number", "sew_number", "finish_number", "PNP_Receive"]
df[num_cols] = df[num_cols].fillna(0)

# 2) Production Status
def get_status(row):
    state = str(row.state).lower()
    if "closed" in state:
        return "COMPLETE"
    if row.cut_number > 0 and row.sew_number == 0:
        return "CUTTING"
    if row.sew_number > 0 and row.finish_number == 0:
        return "SEWING"
    if row.finish_number > 0 and row.PNP_Receive < row.finish_number:
        return "FINISHING"
    if row.PNP_Receive > 0 and row.finish_number > 0 and row.PNP_Receive >= row.finish_number:
        return "PNP RECEIVED"
    return "NOT STARTED"

df["Production Status"] = df.apply(get_status, axis=1)

# 3) WIP quantities
df["QTY WIP CUT"] = (df.cut_number - df.WIP_Cut).clip(lower=0)
df["QTY WIP SEW"] = (df.sew_number - df.WIP_Sew).clip(lower=0)
df["QTY WIP FIN"] = (df.finish_number - df.WIP_Fin).clip(lower=0)

# 4) Finished goods
df["QTY FG"] = df.PNP_Receive

# 5) Load planning lines
planning_sql = """
SELECT [MO NUMBER] AS MO_Number,
       [BULK PO QTY] AS Bulk_PO_Qty
FROM MON_COO_Planning
WHERE [MO NUMBER] IS NOT NULL
  AND [ORDER TYPE] <> 'CANCELLED'
ORDER BY [MO NUMBER] DESC;
"""
planning_lines_df = pd.DataFrame(db.run_query(planning_sql, db_key="orders"))

# 6) Aggregate per MO and compute percent
mo_qty_df = (
    planning_lines_df
    .groupby("MO_Number", as_index=False)["Bulk_PO_Qty"].sum()
    .rename(columns={"Bulk_PO_Qty": "MO_Qty"})
)
planning_lines_df = planning_lines_df.merge(mo_qty_df, on="MO_Number", how="left")
planning_lines_df["Pct_of_MO"] = planning_lines_df["Bulk_PO_Qty"] / planning_lines_df["MO_Qty"]

# 7) Merge into MES data (inner join to only matching MOs)
merged_df = df.merge(
    planning_lines_df[["MO_Number", "Bulk_PO_Qty", "MO_Qty", "Pct_of_MO"]],
    on="MO_Number",
    how="inner"
)
merged_df[["Bulk_PO_Qty","MO_Qty","Pct_of_MO"]] = merged_df[["Bulk_PO_Qty","MO_Qty","Pct_of_MO"]].fillna(0)

# 8) Variance flag: compare MES order_number vs MO_Qty
# compute expected quantity for each line based on MO_Qty and Pct_of_MO
merged_df["Expected_Qty"] = merged_df["MO_Qty"] 

# variance pct = abs(actual MES order_number – expected qty) / expected qty
merged_df["Qty_Var_Pct"] = (
    (merged_df["order_number"] - merged_df["Expected_Qty"]).abs()
    / merged_df["Expected_Qty"].replace(0, np.nan)
)

merged_df.drop(columns="Expected_Qty", inplace=True)


def assign_variance_tier(pct):
    if pd.isna(pct):
        return np.nan
    if pct <= 0.05:
        return 0  # within ±5%
    if pct <= 0.10:
        return 1  # 5–10% variance
    return 2      # >10% variance

merged_df["Qty_Var_Flag"] = merged_df["Qty_Var_Pct"].apply(assign_variance_tier)

# 9) Save to CSV
outputs_dir = repo_root / "outputs"
outputs_dir.mkdir(exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = outputs_dir / f"mes_planning_integrated_{timestamp}.csv"

try:
    merged_df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(merged_df)} records to {output_path}")
    print(f"\n✅ Data saved to: {output_path}")
    print(f"📊 Records exported: {len(merged_df)}")
    print(f"\n📈 Summary:")
    print(f"   Total MOs: {merged_df['MO_Number'].nunique()}")
    for status, cnt in merged_df['Production Status'].value_counts().items():
        print(f"     {status}: {cnt}")
    print(f"\n   Variance Flags: 0=≤5%, 1=5–10%, 2=>10%")
    print(merged_df['Qty_Var_Flag'].value_counts().sort_index().to_string())
except Exception as e:
    logger.error(f"Error saving CSV: {e}")
    print(f"❌ Error saving file: {e}")
