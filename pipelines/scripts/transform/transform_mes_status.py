import pandas as pd
import numpy as np
import sys
from pathlib import Path

def find_repo_root():
    p = Path(__file__).resolve()
    while p.parent != p:
        if (p / "utils" / "db_helper.py").exists():
            return p
        p = p.parent
    raise RuntimeError("Repo root not found")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

import db_helper as db

# 1) Load MES data
df = pd.DataFrame(db.run_query(
    "SELECT * FROM MES_operational_performance", db_key="orders"
))

# 2) Normalize MO_Number
if "MO_Number" not in df.columns:
    df["MO_Number"] = df.get("MO Number")

# 3) Coalesce numeric nulls
for c in ["cut_number","sew_number","finish_number","PNP_Receive"]:
    df[c] = df[c].fillna(0)

# 4) Compute Production Status
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

# 5) One row per MO
status_order = ["NOT STARTED","CUTTING","SEWING","FINISHING","PNP RECEIVED","COMPLETE"]
df["Production Status"] = pd.Categorical(df["Production Status"],
                                        categories=status_order,
                                        ordered=True)
mo_status = (
    df
    .groupby("MO_Number", as_index=False)
    .agg({
        "state":           "first",
        "closed_time_t":   "first",
        "Production Status": "max",
    })
)

print(mo_status)
