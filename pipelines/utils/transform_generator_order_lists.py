#!/usr/bin/env python3
"""
Generate the hybrid transformation stored-procedure SQL from:

* YAML  : pipelines/utils/order_list_schema.yml
* Jinja : pipelines/codegen/templates/sp_transform_hybrid.sql.j2

Outputs:
* sql/generated/sp_Transform_OrderList_Hybrid.sql
"""

import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import Dict, Any, List

import yaml
from jinja2 import Environment, FileSystemLoader

# ---------------------------------------------------------------------------
#  PATHS & CONSTANTS
# ---------------------------------------------------------------------------

ROOT_DIR          = Path(__file__).resolve().parents[2]      # repo root
UTILS_DIR         = ROOT_DIR / "pipelines" / "utils"
TEMPLATES_DIR     = ROOT_DIR / "pipelines" / "codegen" / "templates"
GENERATED_SQL_DIR = ROOT_DIR / "sql" / "generated"

DEFAULT_YAML      = UTILS_DIR / "order_list_schema.yml"
DEFAULT_TEMPLATE  = TEMPLATES_DIR / "sp_transform_hybrid.sql.j2"
DEFAULT_OUT       = GENERATED_SQL_DIR / "sp_Transform_OrderList_Hybrid.sql"

# ---------------------------------------------------------------------------
#  HELPERS
# ---------------------------------------------------------------------------

def load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        sys.exit(f"❌  YAML not found: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8"))

def create_env(template_dir: Path) -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=False,  # No escaping for SQL codegen
        trim_blocks=True,
        lstrip_blocks=True,
    )
    def sql_identifier(identifier: str) -> str:
        return f"[{identifier.replace(']', ']]')}]"
    env.filters["sql_identifier"] = sql_identifier
    return env

def render_template(template_path: Path, context: Dict[str, Any]) -> str:
    env = create_env(template_path.parent)
    tmpl = env.get_template(template_path.name)
    return tmpl.render(**context)

def write_output(sql: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(sql, encoding="utf-8")
    self.logger.info(f"✅  Wrote {out_path.relative_to(ROOT_DIR)} ({len(sql.splitlines())} lines)")

def set_select_names(columns: List[Dict[str, Any]], raw_column_list: List[str]) -> None:
    """
    Assign 'select_name' for each column based on match:
    1. Canonical name first (case-insensitive)
    2. Then aliases, in order (case-insensitive)
    3. Else, None (for NULL) and print warning
    """
    raw_lower = {c.lower(): c for c in raw_column_list}
    self.logger.info(f"\nRAW columns available: {list(raw_lower.values())}\n")

    for col in columns:
        canon = col["name"]
        found = False
        # Try canonical
        if canon.lower() in raw_lower:
            col["select_name"] = raw_lower[canon.lower()]
            found = True
        else:
            # Try aliases, in order
            for alias in col.get("aliases", []):
                if alias.lower() in raw_lower:
                    col["select_name"] = raw_lower[alias.lower()]
                    found = True
                    break
        if not found:
            self.logger.info(f"⚠️  WARNING: No match found for {canon} (aliases: {col.get('aliases', [])}), inserting NULL")
            col["select_name"] = None  # Jinja template should use NULL when select_name is None

# ---------------------------------------------------------------------------
#  MAIN CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate hybrid transform procedure for ORDER_LIST.")
    parser.add_argument("--yaml",  default=DEFAULT_YAML,     help="Path to metadata YAML file")
    parser.add_argument("--tmpl",  default=DEFAULT_TEMPLATE, help="Path to Jinja2 template")
    parser.add_argument("--out",   default=DEFAULT_OUT,      help="Output .sql file")
    args = parser.parse_args()

    meta      = load_yaml(Path(args.yaml))
    template  = Path(args.tmpl)
    out_file  = Path(args.out)

    # -----
    # TODO: Replace with actual RAW table columns at runtime!
    raw_column_list = [
        # Populate with all x*_ORDER_LIST_RAW actual columns as per your source (case matters only for print/debug)
        "AAG ORDER NUMBER", "CUSTOMER NAME", "PROMO GROUP / CAMPAIGN (HOT 30/GLOBAL EDIT",
        # ...all others...
    ]
    # -----

    set_select_names(meta["columns"], raw_column_list)

    # Enrich context with timestamp/version if missing
    meta.setdefault("generated_at", dt.datetime.utcnow().isoformat(timespec="seconds") + "Z")
    meta.setdefault("version",      meta.get("version", 1))

    sql = render_template(template, meta)
    write_output(sql, out_file)

if __name__ == "__main__":
    main()
