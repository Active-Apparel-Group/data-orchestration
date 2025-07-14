#!/usr/bin/env python3
"""
Runner: Extract Monday.com board metadata and generate TOML config in one step.

- Runs universal_board_extractor.py to extract board metadata (does NOT overwrite if file exists)
- Runs create_script_mappings.py to generate TOML config from the metadata file

Usage:
    python board_metadata_and_toml_runner.py --board-id 9200517329 [--board-name "Customer Master Schedule"] [--table-name "MON_CustMasterSchedule"] [--database "orders"]

This script is intended to be used as a VS Code task entry point.
"""
import subprocess
import sys
from pathlib import Path
import argparse

CODEGEN_DIR = Path(__file__).parent
BOARDS_DIR = CODEGEN_DIR.parent.parent / "configs" / "boards"

# --- Argument parsing ---
parser = argparse.ArgumentParser(description="Extract Monday.com board metadata and generate TOML config")
parser.add_argument("--board-id", type=int, required=True, help="Monday.com board ID")
parser.add_argument("--board-name", type=str, help="Board name (optional, for extractor)")
parser.add_argument("--table-name", type=str, help="Table name (optional, for extractor)")
parser.add_argument("--database", type=str, default="orders", help="Target database (default: orders)")
args = parser.parse_args()

metadata_path = BOARDS_DIR / f"board_{args.board_id}_metadata.json"

# --- Step 1: Extract board metadata if not already present ---
if metadata_path.exists():
    self.logger.info(f"✅ Metadata file already exists: {metadata_path}\n  Skipping extraction.")
else:
    extractor_cmd = [
        sys.executable,
        str(CODEGEN_DIR / "universal_board_extractor.py"),
        "--board-id", str(args.board_id)
    ]
    if args.board_name:
        extractor_cmd += ["--board-name", args.board_name]
    if args.table_name:
        extractor_cmd += ["--table-name", args.table_name]
    if args.database:
        extractor_cmd += ["--database", args.database]
    self.logger.info(f"🔍 Extracting board metadata: {' '.join(extractor_cmd)}")
    result = subprocess.run(extractor_cmd)
    if result.returncode != 0:
        self.logger.info("❌ Board extraction failed. Aborting.")
        sys.exit(result.returncode)
    self.logger.info(f"✅ Metadata file created: {metadata_path}")

# --- Step 2: Generate TOML config ---
toml_cmd = [
    sys.executable,
    str(CODEGEN_DIR / "create_script_mappings.py"),
    str(metadata_path),
    "--toml"
]
self.logger.info(f"📝 Generating TOML config: {' '.join(toml_cmd)}")
result = subprocess.run(toml_cmd)
if result.returncode != 0:
    self.logger.info("❌ TOML generation failed.")
    sys.exit(result.returncode)
self.logger.info("✅ TOML config generated.")
