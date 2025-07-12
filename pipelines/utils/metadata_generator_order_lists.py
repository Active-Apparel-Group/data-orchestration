"""
metadata_generator_order_lists.py
---------------------------------
Generate (or refresh) **order_list_schema.yml** that captures
canonical ORDER_LIST metadata and observed raw‑feed header aliases.

The YAML is intended as the single source‑of‑truth for downstream SQL
code‑gen (hybrid transform stored proc) and for analysts to review.

✓  One YAML file, human‑readable
✓  Auto‑discovers column aliases across all x*_ORDER_LIST_RAW tables
✓  Adds simple rule tokens (trim / int / decimal / date) per SQL type
✓  Leaves a `pk:` flag stub for human maintenance (default: false)

Usage ::
    python metadata_generator_order_lists.py \
        --database orders \
        --out order_list_schema.yml

Only read‑level permissions are required.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd
import pyodbc  # pyodbc>=4.0.34
import yaml    # pyyaml

# Import db_helper using standard import pattern
import db_helper as db

# ---------------------------------------------------------------------------
#  Defaults & helpers
# ---------------------------------------------------------------------------

# Mapping SQL data‑types → default rule tokens (kept deliberately small)
RULE_MAP: Dict[str, List[str]] = {
    # character types
    "varchar": ["trim"],
    "nvarchar": ["trim"],
    "char": ["trim"],
    # integers
    "int": ["int"],
    "bigint": ["int"],
    "smallint": ["int"],
    # numerics / floats
    "decimal": ["decimal"],
    "numeric": ["decimal"],
    "float": ["decimal"],
    "real": ["decimal"],
    # temporal
    "date": ["date"],
    "datetime": ["date"],
    "datetime2": ["date"],
}

GLOB_RAW_DEFAULT = "x*_ORDER_LIST_RAW"
YAML_OUT_DEFAULT = "order_list_schema.yml"

# ---------------------------------------------------------------------------
#  Introspection helpers
# ---------------------------------------------------------------------------

def fetch_dataframe(sql: str, cnxn: pyodbc.Connection) -> pd.DataFrame:
    """Return the result of *sql* as a DataFrame (empty df on error)."""
    try:
        return pd.read_sql(sql, cnxn)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"! Skipped query because {exc}", file=sys.stderr)
        return pd.DataFrame()


def get_order_list_schema(cnxn: pyodbc.Connection) -> pd.DataFrame:
    """Return INFORMATION_SCHEMA metadata for ORDER_LIST as DataFrame."""
    return fetch_dataframe(
        """
        SELECT COLUMN_NAME,
               DATA_TYPE,
               CHARACTER_MAXIMUM_LENGTH,
               NUMERIC_PRECISION,
               NUMERIC_SCALE,
               ORDINAL_POSITION
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'ORDER_LIST'
        ORDER BY ORDINAL_POSITION;
        """,
        cnxn,
    )


def infer_yaml_type(row: pd.Series) -> str:
    """Convert SQL type metadata to compact YAML type string."""
    sql_type = row.DATA_TYPE
    if sql_type in {"decimal", "numeric"}:
        return f"{sql_type}({int(row.NUMERIC_PRECISION)},{int(row.NUMERIC_SCALE)})"
    if sql_type in {"varchar", "nvarchar", "char"}:
        return "string"
    return sql_type


def canonicalize(name: str) -> str:
    """Cheap header normaliser used to match raw headers to canonical."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def discover_aliases(sample_headers: List[str], canonical: str) -> List[str]:
    """Return raw headers that appear to refer to *canonical* column."""
    can_key = canonicalize(canonical)
    aliases: List[str] = [h for h in sample_headers if canonicalize(h) == can_key and h != canonical]
    return sorted(dict.fromkeys(aliases))  # dedupe while preserving order

# ---------------------------------------------------------------------------
#  YAML Builder
# ---------------------------------------------------------------------------

def build_yaml_dict(
    db_key: str,
    glob_raw: str = GLOB_RAW_DEFAULT,
    include_pk_stub: bool = True,
) -> Dict:
    """Return YAML structure as a Python dict ready to dump."""

    with db.get_connection(db_key) as cnxn:
        # 1️⃣ canonical schema
        cols_df = get_order_list_schema(cnxn)
        if cols_df.empty:
            raise RuntimeError("Could not read ORDER_LIST schema – check connection / permissions.")

        # 2️⃣ collect sample headers from every landing table
        cursor = cnxn.cursor()
        regex = re.compile(glob_raw.replace("*", ".*"), re.IGNORECASE)
        landing_tables = [row.table_name for row in cursor.tables(tableType="TABLE") if regex.fullmatch(row.table_name)]
        header_samples: List[str] = []
        for tbl in landing_tables:
            df = fetch_dataframe(f"SELECT TOP 1 * FROM {tbl};", cnxn)
            header_samples.extend(df.columns.tolist())
        header_samples = list(dict.fromkeys(header_samples))  # dedupe keep order

        # 3️⃣ build YAML dict
        yaml_dict: Dict = {
            "version": 1,
            "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source_table": "ORDER_LIST",
            "raw_tables": [glob_raw],
            "columns": [],
        }

        for _, row in cols_df.iterrows():
            col_entry: Dict = {
                "name": row.COLUMN_NAME,
                "aliases": discover_aliases(header_samples, row.COLUMN_NAME),
                "type": infer_yaml_type(row),
                "rules": RULE_MAP.get(row.DATA_TYPE, []),
            }
            if include_pk_stub:
                col_entry["pk"] = False
            yaml_dict["columns"].append(col_entry)

        return yaml_dict

# ---------------------------------------------------------------------------
#  CLI
# ---------------------------------------------------------------------------

class NoAliasDumper(yaml.SafeDumper):
    """Prevent PyYAML from emitting anchors (&id001 / *id001)."""
    def ignore_aliases(self, data):
        return True

def write_yaml_file(yaml_data: Dict, out_path: Path) -> None:
    with out_path.open("w", encoding="utf-8") as f:
        # use the custom dumper
        yaml.dump(
            yaml_data,
            f,
            Dumper=NoAliasDumper,     # <- key line
            sort_keys=False,
            width=120,
            allow_unicode=True,
        )
    print(f"\n✅  Wrote {out_path} with {len(yaml_data['columns'])} columns.")



def main() -> None:
    parser = argparse.ArgumentParser(description="Generate order_list_schema.yml metadata file.")
    parser.add_argument("--database", default="orders", help="Database key from config.yaml (default: orders)")
    parser.add_argument("--raw_glob", default=GLOB_RAW_DEFAULT, help="Pattern for landing tables (SQL LIKE style with *)")
    parser.add_argument("--out", default=YAML_OUT_DEFAULT, help="Output YAML file path")

    args = parser.parse_args()

    yaml_dict = build_yaml_dict(args.database, glob_raw=args.raw_glob)
    write_yaml_file(yaml_dict, Path(args.out))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted – no file written.", file=sys.stderr)
