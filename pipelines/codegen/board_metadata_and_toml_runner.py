#!/usr/bin/env python3
"""
Runner: Extract Monday.com board metadata and generate TOML config in one step.

- Runs universal_board_extractor.py to extract board metadata
- Runs create_script_mappings.py to generate TOML config from the metadata file
- Runs generate_pipeline_config.py to create board registry entries for monday_boards.toml

Usage:
    python board_metadata_and_toml_runner.py --board-id 9200517329 [--board-name "Customer Master Schedule"] [--table-name "MON_CustMasterSchedule"] [--database "orders"] [--overwrite]

Options:
    --overwrite: Force regeneration of metadata file even if it exists

This script is intended to be used as a VS Code task entry point.
"""
import subprocess
import sys
from pathlib import Path
import argparse

# --- repo utils path setup ----------------------------------------------------
def find_repo_root() -> Path:
    """Find repository root by looking for pipelines/utils folder"""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current.parent.parent / "pipelines" / "utils").exists():
            return current.parent.parent
        current = current.parent
    raise RuntimeError("Could not find repository root with utils/ folder")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))  # pipelines/utils ONLY

# Import logger helper using project standards
import logger_helper

CODEGEN_DIR = Path(__file__).parent
BOARDS_DIR = CODEGEN_DIR.parent.parent / "configs" / "extracts" / "boards"

# Initialize logger for Kestra/VS Code compatibility
logger = logger_helper.get_logger(__name__)

# --- Argument parsing ---
parser = argparse.ArgumentParser(description="Extract Monday.com board metadata and generate TOML config")
parser.add_argument("--board-id", type=int, required=True, help="Monday.com board ID")
parser.add_argument("--board-name", type=str, help="Board name (optional, for extractor)")
parser.add_argument("--table-name", type=str, help="Table name (optional, for extractor)")
parser.add_argument("--database", type=str, default="orders", help="Target database (default: orders)")
parser.add_argument("--overwrite", action="store_true", help="Overwrite existing metadata file if it exists")
args = parser.parse_args()

metadata_path = BOARDS_DIR / f"board_{args.board_id}_metadata.json"

# --- Step 1: Extract board metadata ---
should_extract = args.overwrite or not metadata_path.exists()

if not should_extract:
    logger.info(f"✅ Metadata file already exists: {metadata_path}")
    logger.info("   Use --overwrite flag to regenerate. Skipping extraction.")
else:
    if metadata_path.exists():
        logger.info(f"🔄 Overwriting existing metadata file: {metadata_path}")
    else:
        logger.info(f"🔍 Creating new metadata file: {metadata_path}")
    
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
    logger.info(f"🔍 Extracting board metadata: {' '.join(extractor_cmd)}")
    result = subprocess.run(extractor_cmd)
    if result.returncode != 0:
        logger.info("❌ Board extraction failed. Aborting.")
        sys.exit(result.returncode)
    logger.info(f"✅ Metadata file created: {metadata_path}")

# --- Step 2: Generate TOML config ---
toml_cmd = [
    sys.executable,
    str(CODEGEN_DIR / "create_script_mappings.py"),
    str(metadata_path),
    "--toml"
]
logger.info(f"📝 Generating TOML config: {' '.join(toml_cmd)}")
result = subprocess.run(toml_cmd)
if result.returncode != 0:
    logger.info("❌ TOML generation failed.")
    sys.exit(result.returncode)
logger.info("✅ TOML config generated.")

# --- Step 3: Generate pipeline config for monday_boards.toml ---
pipeline_cmd = [
    sys.executable,
    str(CODEGEN_DIR / "generate_pipeline_config.py"),
    str(metadata_path)
]
logger.info(f"🔧 Generating pipeline config: {' '.join(pipeline_cmd)}")
result = subprocess.run(pipeline_cmd)
if result.returncode != 0:
    logger.info("❌ Pipeline config generation failed.")
    sys.exit(result.returncode)
logger.info("✅ Pipeline config generated.")

logger.info(f"\n🎉 Board configuration complete for {args.board_id}!")
logger.info("📋 Generated files:")
logger.info(f"  • Metadata: {metadata_path}")
logger.info(f"  • TOML config: (check configs/extracts/ directory)")
logger.info(f"  • Pipeline config: configs/extracts/pipelines/pipeline_config_{args.board_id}.toml")
logger.info("\n💡 Next steps:")
logger.info("  1. Review the pipeline config file")
logger.info("  2. Add the board registry entry to configs/pipelines/monday_boards.toml")
logger.info("  3. Test with load_boards_async.py for optimal settings")
