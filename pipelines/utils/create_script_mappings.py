#---
"""
Script for transforming Monday board metadata JSON files into either enhanced JSON 
or TOML configuration files.

This module provides functionality to:
1. Transform Monday board config JSON by adding 'script_mappings' field (original functionality)
2. Generate TOML format with proper [column_mapping] sections for Monday.com updates

Functions:
    transform_config(input_file: Path, output_file: Path): 
        Transforms a Monday board config JSON by adding script mappings.
    transform_to_toml(input_file: Path, output_file: Path): 
        Transforms a Monday board config JSON into TOML format.
    generate_column_mapping_toml(columns: list) -> str:
        Generates TOML [column_mapping] section from columns data.
    main(): 
        Command-line interface for the transformation script.

Usage:
    # Generate enhanced JSON (default):
    python create_script_mappings.py board_metadata.json
    
    # Generate TOML configuration:
    python create_script_mappings.py board_metadata.json --toml
    python create_script_mappings.py board_metadata.json --toml -o planning_update.toml

Examples:
    python create_script_mappings.py board_8709134353_metadata.json
    python create_script_mappings.py board_8709134353_metadata.json --toml -o planning_update.toml
"""
#----


#!/usr/bin/env python3
import json
import argparse
from pathlib import Path
from datetime import datetime

def transform_config(input_file: Path, output_file: Path):
    """
    Transform Monday board metadata JSON by adding script_mappings field.
    This is the original functionality for enhanced JSON output.
    """
    # 1) Load the existing JSON
    data = json.loads(input_file.read_text(encoding="utf-8"))
    
    # 2) Build script_mappings
    cols = data.get("columns", [])
    script_mappings = {c["monday_id"]: c["sql_column"] for c in cols}
    
    # 3) Inject into top-level JSON
    data["script_mappings"] = script_mappings
    
    # 4) Write out
    output_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"✅ Enhanced JSON config written to {output_file}")

def generate_column_mapping_toml(columns: list) -> str:
    """
    Generate TOML [column_mapping] section from columns data.
    
    Args:
        columns: List of column dictionaries from board metadata
        
    Returns:
        str: TOML formatted column mapping section
    """
    toml_lines = ["[column_mapping]"]
    toml_lines.append("# Monday.com column_id -> SQL query column mapping")
    
    for col in columns:
        # Skip excluded columns
        if col.get("exclude", False):
            continue
            
        monday_id = col.get("monday_id", "")
        sql_column = col.get("sql_column", "")
        monday_title = col.get("monday_title", "")
        
        if monday_id and sql_column:
            # Add comment with Monday title for clarity
            if monday_title:
                toml_lines.append(f'# {monday_title}')
            
            # Format as TOML key-value pair with proper quoting
            toml_lines.append(f'"{monday_id}" = "{sql_column}"')
            
    return "\n".join(toml_lines)

def transform_to_toml(input_file: Path, output_file: Path):
    """
    Transform Monday board metadata JSON to TOML configuration format.
    
    Args:
        input_file: Path to the original board metadata JSON
        output_file: Path where TOML configuration will be written
    """
    # 1) Load the existing JSON
    data = json.loads(input_file.read_text(encoding="utf-8"))
    
    # 2) Extract metadata
    board_id = data.get("board_id", "")
    board_name = data.get("board_name", "Unknown")
    table_name = data.get("table_name", "")
    database = data.get("database", "")
    
    # 3) Build TOML content
    toml_content = []
    
    # Header comment
    toml_content.append("# OPUS Universal Monday.com Update Configuration")
    toml_content.append(f"# Generated from: {input_file.name}")
    toml_content.append(f"# Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    toml_content.append(f"# Board: {board_name} ({board_id})")
    toml_content.append("")
    
    # Metadata section
    toml_content.append("[metadata]")
    toml_content.append(f'board_id = {board_id}')
    toml_content.append(f'board_name = "{board_name}"')
    toml_content.append(f'table_name = "{table_name}"')
    toml_content.append(f'database = "{database}"')
    toml_content.append('update_type = "batch_item_updates"')
    toml_content.append(f'description = "Update {board_name} items with latest data"')
    toml_content.append("")
    
    # Query config placeholder
    toml_content.append("[query_config]")
    toml_content.append("# SQL query to get update data")
    toml_content.append('query = """')
    toml_content.append("# TODO: Add your SQL query here")
    toml_content.append("# SELECT")
    toml_content.append("#     [Item ID] as monday_item_id,")
    toml_content.append("#     -- Add your columns here")
    toml_content.append("# FROM your_table")
    toml_content.append("# WHERE your_conditions")
    toml_content.append('"""')
    toml_content.append("")
    toml_content.append("# Column mapping configuration")
    toml_content.append('item_id_column = "monday_item_id"')
    toml_content.append("")
    
    # Generate column mapping section
    columns = data.get("columns", [])
    column_mapping = generate_column_mapping_toml(columns)
    toml_content.append(column_mapping)
    
    # 4) Write TOML file
    final_content = "\n".join(toml_content)
    output_file.write_text(final_content, encoding="utf-8")
    
    print(f"✅ TOML configuration written to {output_file}")
    print(f"📊 Generated mapping for {len([c for c in columns if not c.get('exclude', False)])} columns")

def main():
    parser = argparse.ArgumentParser(
        description="Transform Monday board metadata: enhance JSON or generate TOML config"
    )
    parser.add_argument(
        "input", type=Path,
        help="Path to the original board_{id}_metadata.json"
    )
    parser.add_argument(
        "-o", "--output", type=Path,
        help="Where to write the output file (defaults based on format)"
    )
    parser.add_argument(
        "--toml", action="store_true",
        help="Generate TOML configuration instead of enhanced JSON"
    )
    args = parser.parse_args()
    
    # Determine output file and format
    if args.toml:
        # TOML mode
        if args.output:
            out = args.output
        else:
            # Generate default TOML filename in configs/updates/templates/
            try:
                data = json.loads(args.input.read_text(encoding="utf-8"))
                board_name = data.get("board_name", "board").lower().replace(" ", "_")
                # Create the templates directory if it doesn't exist
                templates_dir = Path("configs/updates/templates")
                templates_dir.mkdir(parents=True, exist_ok=True)
                out = templates_dir / f"{board_name}_update.toml"
            except:
                # Fallback to templates directory with generic name
                templates_dir = Path("configs/updates/templates")
                templates_dir.mkdir(parents=True, exist_ok=True)
                out = templates_dir / args.input.with_suffix(".toml").name
        
        transform_to_toml(args.input, out)
    else:
        # JSON mode (original functionality)
        out = args.output or args.input
        transform_config(args.input, out)

if __name__ == "__main__":
    main()
