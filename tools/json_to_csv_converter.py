"""
Board Metadata JSON to CSV Converter
Purpose: Convert Monday.com board metadata JSON files to CSV format for analysis
Author: Data Engineering Team
Date: July 18, 2025

Usage:
    python json_to_csv_converter.py --file board_8709134353_metadata.json
    python json_to_csv_converter.py --file configs/boards/board_8709134353_metadata.json
    python json_to_csv_converter.py --file board_8709134353_metadata.json --output custom_name.csv
"""

import argparse
import json
import csv
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

def find_repo_root() -> Path:
    """Find repository root by looking for configs folder"""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current / "configs").exists():
            return current
        current = current.parent
    raise RuntimeError("Could not find repository root with configs folder")

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load and parse JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in file {file_path}: {e}")

def extract_board_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract board-level metadata"""
    return {
        'board_id': data.get('board_id'),
        'board_name': data.get('board_name'),
        'table_name': data.get('table_name'),
        'database': data.get('database'),
        'discovered_at': data.get('discovered_at'),
        'item_terminology_name': data.get('item_terminology', {}).get('name'),
        'item_terminology_overwrite': data.get('item_terminology', {}).get('overwrite_name'),
        'total_columns': len(data.get('columns', []))
    }

def convert_columns_to_csv(data: Dict[str, Any], output_path: Path):
    """Convert board metadata to CSV with separate sheets/files"""
    
    # 1. Board metadata summary
    board_info = extract_board_metadata(data)
    
    # 2. Column duplications (if any)
    duplications = data.get('column_duplications', [])
    
    # 3. Columns details
    columns = data.get('columns', [])
    
    # Create main CSV with columns data
    columns_output = output_path
    
    print(f"📊 Converting board metadata to CSV...")
    print(f"   Board: {board_info['board_name']} (ID: {board_info['board_id']})")
    print(f"   Columns: {len(columns)}")
    print(f"   Output: {columns_output}")
    
    # Write columns CSV
    if columns:
        fieldnames = [
            'monday_id', 'monday_title', 'monday_type', 
            'sql_column', 'sql_type', 'extraction_field',
            'nullable', 'is_system_field', 'exclude',
            'conversion_logic', 'custom_sql_type', 'custom_extraction_field'
        ]
        
        with open(columns_output, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for column in columns:
                # Clean up the column data for CSV
                row = {}
                for field in fieldnames:
                    value = column.get(field)
                    # Convert None to empty string for CSV
                    row[field] = value if value is not None else ''
                writer.writerow(row)
    
    # Create additional files for other data
    base_name = output_path.stem
    output_dir = output_path.parent
    
    # Board summary CSV
    summary_file = output_dir / f"{base_name}_summary.csv"
    with open(summary_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=board_info.keys())
        writer.writeheader()
        writer.writerow(board_info)
    
    # Column duplications CSV (if any)
    if duplications:
        duplications_file = output_dir / f"{base_name}_duplications.csv"
        with open(duplications_file, 'w', newline='', encoding='utf-8') as csvfile:
            if duplications:
                fieldnames = duplications[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(duplications)
    
    return {
        'columns_file': columns_output,
        'summary_file': summary_file,
        'duplications_file': duplications_file if duplications else None,
        'total_columns': len(columns),
        'board_info': board_info
    }

def resolve_file_path(file_arg: str) -> Path:
    """Resolve file path with multiple search strategies"""
    repo_root = find_repo_root()
    
    # Strategy 1: Exact path as provided
    if Path(file_arg).exists():
        return Path(file_arg).resolve()
    
    # Strategy 2: Relative to current directory
    current_path = Path.cwd() / file_arg
    if current_path.exists():
        return current_path.resolve()
    
    # Strategy 3: Look in configs/boards/
    boards_path = repo_root / "configs" / "boards" / file_arg
    if boards_path.exists():
        return boards_path.resolve()
    
    # Strategy 4: Look for board ID pattern and construct filename
    if file_arg.isdigit() or file_arg.startswith('board_'):
        if file_arg.isdigit():
            constructed_name = f"board_{file_arg}_metadata.json"
        else:
            constructed_name = file_arg if file_arg.endswith('.json') else f"{file_arg}.json"
        
        constructed_path = repo_root / "configs" / "boards" / constructed_name
        if constructed_path.exists():
            return constructed_path.resolve()
    
    # Strategy 5: Search for files containing the argument
    boards_dir = repo_root / "configs" / "boards"
    if boards_dir.exists():
        for file_path in boards_dir.glob("*.json"):
            if file_arg in file_path.name:
                return file_path.resolve()
    
    raise FileNotFoundError(f"Could not find file: {file_arg}")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Convert Monday.com board metadata JSON files to CSV format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert by exact filename
  python json_to_csv_converter.py --file board_8709134353_metadata.json
  
  # Convert with relative path
  python json_to_csv_converter.py --file configs/boards/board_8709134353_metadata.json
  
  # Convert by board ID
  python json_to_csv_converter.py --file 8709134353
  
  # Specify custom output name
  python json_to_csv_converter.py --file board_8709134353_metadata.json --output planning_board.csv
  
  # Convert partial filename match
  python json_to_csv_converter.py --file 8709134353_metadata
        """
    )
    
    parser.add_argument('--file', '-f', required=True,
                       help='JSON file to convert (supports multiple resolution strategies)')
    parser.add_argument('--output', '-o',
                       help='Output CSV filename (default: auto-generated from input)')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Reduce output verbosity')
    
    args = parser.parse_args()
    
    try:
        # Resolve input file path
        input_path = resolve_file_path(args.file)
        
        if not args.quiet:
            print(f"🔍 Found input file: {input_path}")
        
        # Load JSON data
        data = load_json_file(input_path)
        
        # Determine output path
        if args.output:
            output_path = Path(args.output)
        else:
            # Auto-generate output filename
            base_name = input_path.stem.replace('_metadata', '_columns')
            output_path = input_path.parent / f"{base_name}.csv"
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to CSV
        results = convert_columns_to_csv(data, output_path)
        
        if not args.quiet:
            print(f"\n✅ Conversion completed successfully!")
            print(f"\n📁 Generated files:")
            print(f"   📋 Columns:      {results['columns_file']}")
            print(f"   📊 Summary:      {results['summary_file']}")
            if results['duplications_file']:
                print(f"   🔄 Duplications: {results['duplications_file']}")
            
            print(f"\n📈 Statistics:")
            print(f"   Board: {results['board_info']['board_name']}")
            print(f"   Table: {results['board_info']['table_name']}")
            print(f"   Total Columns: {results['total_columns']}")
            
        return 0
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        print(f"\n💡 Available board files:", file=sys.stderr)
        
        try:
            repo_root = find_repo_root()
            boards_dir = repo_root / "configs" / "boards"
            if boards_dir.exists():
                for json_file in sorted(boards_dir.glob("*.json")):
                    print(f"   - {json_file.name}", file=sys.stderr)
        except:
            pass
        
        return 1
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())