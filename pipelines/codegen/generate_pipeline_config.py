#!/usr/bin/env python3
"""
Pipeline Configuration Generator for Monday.com Boards
======================================================

Generates board registry entries for configs/pipelines/monday_boards.toml
from board metadata JSON files.

Creates entries like:
[boards.registry."9200517329"]
name = "Planning - Production"
database_table = "MON_Planning"
complexity_category = "medium"
optimal_batch_size = 25
optimal_concurrency = 8
notes = "Production planning board with moderate complexity"
number_of_cols = 87
number_of_formula_cols = 12
number_of_lookup_cols = 15
number_of_items = 4327

Usage:
    python generate_pipeline_config.py board_9200517329_metadata.json
    python generate_pipeline_config.py board_8709134353_metadata.json -o custom_output.toml
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Standard import pattern for logger helper
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current.parent.parent / "pipelines" / "utils").exists():
            return current.parent.parent
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

# Import logger helper using project standards
import logger_helper

# Initialize logger for Kestra/VS Code compatibility
logger = logger_helper.get_logger(__name__)

def analyze_board_complexity(columns: list, items_count: int) -> dict:
    """
    Analyze board complexity and determine optimal settings.
    
    Args:
        columns: List of column dictionaries from board metadata
        items_count: Number of items in the board
        
    Returns:
        dict: Analysis results with complexity category and optimal settings
    """
    # Count different column types
    total_cols = len([c for c in columns if c.get("monday_id")])
    formula_cols = len([c for c in columns if c.get("monday_type") == "formula"])
    lookup_cols = len([c for c in columns if c.get("monday_type") in ["mirror", "lookup"]])
    
    # Determine complexity category based on items count and column complexity
    if items_count >= 3000 or formula_cols >= 10 or lookup_cols >= 10:
        complexity_category = "large"
        optimal_batch_size = 20
        optimal_concurrency = 6
    elif items_count >= 500 or formula_cols >= 5 or lookup_cols >= 5:
        complexity_category = "medium"
        optimal_batch_size = 25
        optimal_concurrency = 8
    else:
        complexity_category = "small"
        optimal_batch_size = 25
        optimal_concurrency = 12
    
    return {
        "complexity_category": complexity_category,
        "optimal_batch_size": optimal_batch_size,
        "optimal_concurrency": optimal_concurrency,
        "total_cols": total_cols,
        "formula_cols": formula_cols,
        "lookup_cols": lookup_cols,
        "items_count": items_count
    }

def generate_complexity_notes(analysis: dict) -> str:
    """Generate descriptive notes based on board analysis."""
    notes_parts = []
    
    if analysis["complexity_category"] == "large":
        notes_parts.append("High complexity board")
    elif analysis["complexity_category"] == "medium":
        notes_parts.append("Medium complexity board")
    else:
        notes_parts.append("Simple board")
    
    if analysis["formula_cols"] > 5:
        notes_parts.append(f"{analysis['formula_cols']} formula columns")
    
    if analysis["lookup_cols"] > 5:
        notes_parts.append(f"{analysis['lookup_cols']} lookup/mirror columns")
    
    if analysis["items_count"] > 2000:
        notes_parts.append(f"large dataset ({analysis['items_count']:,} items)")
    
    return " - ".join(notes_parts) if notes_parts else "Standard board configuration"

def generate_pipeline_config_toml(input_file: Path, output_file: Path):
    """
    Generate pipeline configuration TOML from board metadata JSON.
    
    Args:
        input_file: Path to the board metadata JSON file
        output_file: Path where pipeline config TOML will be written
    """
    # Load the board metadata
    data = json.loads(input_file.read_text(encoding="utf-8"))
    
    # Extract basic metadata
    board_id = str(data.get("board_id", ""))
    board_name = data.get("board_name", "Unknown Board")
    table_name = data.get("table_name", "")
    database = data.get("database", "orders")
    items_count = data.get("metadata", {}).get("items_count", 0)
    
    # Analyze board complexity
    columns = data.get("columns", [])
    analysis = analyze_board_complexity(columns, items_count)
    
    # Generate notes
    notes = generate_complexity_notes(analysis)
    
    # Build TOML content
    toml_content = []
    
    # Header comment
    toml_content.append("# Monday.com Board Registry Entry")
    toml_content.append(f"# Generated from: {input_file.name}")
    toml_content.append(f"# Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    toml_content.append(f"# Board: {board_name} ({board_id})")
    toml_content.append("")
    toml_content.append("# Add this section to configs/pipelines/monday_boards.toml")
    toml_content.append("# under the [boards.registry] section")
    toml_content.append("")
    
    # Board registry entry
    toml_content.append(f'[boards.registry."{board_id}"]')
    toml_content.append(f'name = "{board_name}"')
    toml_content.append(f'database_table = "{table_name}"')
    toml_content.append(f'complexity_category = "{analysis["complexity_category"]}"')
    toml_content.append(f'optimal_batch_size = {analysis["optimal_batch_size"]}')
    toml_content.append(f'optimal_concurrency = {analysis["optimal_concurrency"]}')
    toml_content.append(f'notes = "{notes}"')
    toml_content.append("")
    
    # Detailed statistics
    toml_content.append("# Board Analysis Statistics")
    toml_content.append(f'number_of_cols = {analysis["total_cols"]}')
    toml_content.append(f'number_of_formula_cols = {analysis["formula_cols"]}')
    toml_content.append(f'number_of_lookup_cols = {analysis["lookup_cols"]}')
    toml_content.append(f'number_of_items = {analysis["items_count"]}')
    
    if database != "orders":
        toml_content.append(f'database = "{database}"')
    
    # Write the file
    final_content = "\n".join(toml_content)
    output_file.write_text(final_content, encoding="utf-8")
    
    logger.info(f"✅ Pipeline config written to {output_file}")
    logger.info(f"📊 Board Analysis:")
    logger.info(f"   - Complexity: {analysis['complexity_category']}")
    logger.info(f"   - Total columns: {analysis['total_cols']}")
    logger.info(f"   - Formula columns: {analysis['formula_cols']}")
    logger.info(f"   - Lookup columns: {analysis['lookup_cols']}")
    logger.info(f"   - Items: {analysis['items_count']:,}")
    logger.info(f"   - Recommended batch size: {analysis['optimal_batch_size']}")
    logger.info(f"   - Recommended concurrency: {analysis['optimal_concurrency']}")

def main():
    parser = argparse.ArgumentParser(
        description="Generate pipeline configuration for Monday.com boards"
    )
    parser.add_argument(
        "input", type=Path,
        help="Path to the board_{id}_metadata.json file"
    )
    parser.add_argument(
        "-o", "--output", type=Path,
        help="Output file path (default: configs/pipelines/pipeline_config_{board_id}.toml)"
    )
    args = parser.parse_args()
    
    # Determine output file
    if args.output:
        output_file = args.output
    else:
        # Extract board ID from filename for default output
        try:
            data = json.loads(args.input.read_text(encoding="utf-8"))
            board_id = data.get("board_id", "unknown")
            
            # Create pipelines directory in configs/extracts
            pipelines_dir = Path("configs/extracts/pipelines")
            pipelines_dir.mkdir(parents=True, exist_ok=True)
            
            output_file = pipelines_dir / f"pipeline_config_{board_id}.toml"
        except Exception as e:
            logger.error(f"Failed to determine output file: {e}")
            sys.exit(1)
    
    # Generate the pipeline configuration
    generate_pipeline_config_toml(args.input, output_file)

if __name__ == "__main__":
    main()
