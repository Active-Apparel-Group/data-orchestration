#!/usr/bin/env python3
"""
Universal Monday.com Board Extractor
Usage: python universal_board_extractor.py --board-id 9200517329 --board-name "Customer Master Schedule" --table-name "customer_master_schedule" --database "orders"
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

# Find repository root and add utils to path
def find_repo_root():
    """Find the repository root by looking for utils folder"""
    current_path = Path(__file__).resolve()
    while current_path.parent != current_path:  # Not at filesystem root
        utils_path = current_path / "utils"
        if utils_path.exists() and (utils_path / "db_helper.py").exists():
            return current_path
        current_path = current_path.parent
    raise RuntimeError("Could not find repository root with utils folder")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

# Import template generator
sys.path.insert(0, str(Path(__file__).parent / "core"))
from script_template_generator import ScriptTemplateGenerator

def main():
    parser = argparse.ArgumentParser(description='Universal Monday.com Board Extractor')
    parser.add_argument('--board-id', required=True, type=int, help='Monday.com board ID')
    parser.add_argument('--board-name', required=True, help='Human-readable board name')
    parser.add_argument('--table-name', required=True, help='Target SQL table name')
    parser.add_argument('--database', required=True, help='Target database name')
    parser.add_argument('--board-key', help='Board key for mapping (defaults to table_name)')
    parser.add_argument('--generate-only', action='store_true', help='Only generate script, do not execute')
    
    args = parser.parse_args()
    
    # Default board_key to table_name if not provided
    board_key = args.board_key or args.table_name
    
    print(f"🚀 Universal Monday.com Board Extractor")
    print(f"📋 Board: {args.board_name} (ID: {args.board_id})")
    print(f"🗄️  Target: {args.database}.{args.table_name}")
    print(f"🔑 Board Key: {board_key}")
    
    # Template variables
    template_vars = {
        "board_id": args.board_id,
        "board_name": args.board_name,
        "table_name": args.table_name,
        "database": args.database,
        "board_key": board_key,
        "generation_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
      # Generate script using template directly
    print("📄 Generating script from template...")
    from jinja2 import Environment, FileSystemLoader
      # Set up Jinja2 environment
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("board_extractor_production.py.j2")
      # Render template with variables
    script_content = template.render(**template_vars)
    
    if args.generate_only:
        # Save generated script with lowercase, clean board name
        # Convert board name to lowercase and replace spaces/special chars with underscores
        clean_board_name = args.board_name.lower().replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        
        output_file = f"generated/get_board_{clean_board_name}.py"
        output_path = Path(__file__).parent / output_file
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"✅ Generated script saved to: {output_path}")
        return
    
    # Execute script directly
    print("🔄 Executing board extraction...")
    
    # Create a temporary module and execute
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
        temp_file.write(script_content)
        temp_file_path = temp_file.name
    
    try:
        # Execute the generated script
        exec(compile(open(temp_file_path).read(), temp_file_path, 'exec'))
        print("✅ Board extraction completed successfully!")
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        raise
    finally:
        # Clean up temporary file
        os.unlink(temp_file_path)

if __name__ == "__main__":
    main()
