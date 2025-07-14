#!/usr/bin/env python3
"""
Universal Monday.com Board Extractor
Dynamic board discovery and metadata generation system

Usage: 
    python universal_board_extractor.py --board-id 8685586257 --board-name "Test Board" --table-name "test_board" --database "orders"

Workflow:
1. Extract board schema from Monday.com
2. Generate metadata.json file  
3. Update board_registry.json
4. Create Kestra workflow YAML
5. Generate extraction script (optional)
"""

import argparse
import os
import sys
import json
import requests
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# Find repository root and add utils to path
def find_repo_root():
    """Find the repository root by looking for pipelines/utils folder"""
    current_path = Path(__file__).resolve()
    while current_path.parent != current_path:
        if (current_path.parent.parent / "pipelines" / "utils").exists():
            return current_path.parent.parent
        current_path = current_path.parent
    raise RuntimeError("Could not find repository root with pipelines/utils folder")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

# Import helpers
import logger_helper

logger = logger_helper.get_logger("universal_board_extractor")

# Monday.com API setup
MONDAY_TOKEN = os.getenv("MONDAY_API_KEY")
if not MONDAY_TOKEN:
    logger.error("MONDAY_API_KEY environment variable not set")
    sys.exit(1)

API_URL = "https://api.monday.com/v2"
HEADERS = {
    "Authorization": MONDAY_TOKEN,
    "API-Version": "2025-04",
    "Content-Type": "application/json"
}

def gql_request(query: str, variables: Dict = None) -> Dict[str, Any]:
    """Execute GraphQL request"""
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    if "errors" in data:
        raise Exception(f"GraphQL errors: {data['errors']}")
    
    return data["data"]

def discover_board_schema(board_id: int) -> Dict[str, Any]:
    """Discover complete board schema including columns and sample data"""
    logger.info(f"Discovering schema for board {board_id}...")
    
    # Get board info and columns
    query = """
    query ($ids: [ID!]!) {
        boards(ids: $ids) {
            name
            description
            item_terminology
            items_count
            columns {
                id
                title
                type
                settings_str
            }
        }
    }
    """
    
    data = gql_request(query, {"ids": [board_id]})
    board = data["boards"][0]
    
    # Get sample items for data type analysis
    sample_query = f"""
    query {{
        boards(ids: {board_id}) {{
            items_page(limit: 5) {{
                items {{
                    id
                    name
                    column_values {{
                        id
                        text
                        value
                        type
                        ... on StatusValue {{ label }}
                        ... on DropdownValue {{ text }}
                        ... on NumbersValue {{ number }}
                        ... on DateValue {{ date }}
                        ... on MirrorValue {{ display_value }}
                        ... on FormulaValue {{ display_value }}
                    }}
                }}
            }}
        }}
    }}
    """
    
    sample_data = gql_request(sample_query)
    sample_items = sample_data["boards"][0]["items_page"]["items"]
    
    # Build metadata with item_terminology as an object at the top level
    metadata = {
        "board_id": board_id,
        "board_name": board["name"],
        "table_name": f"MON_{board['name'].replace(' ', '').replace('-', '_')}",
        "database": "orders",
        "discovered_at": datetime.now().isoformat(),
        "item_terminology": {
            "name": board.get("item_terminology", "Item"),
            "overwrite_name": ""
        },
        "columns": [],
        "global_defaults": {
            "default_sql_type": "NVARCHAR(255)",
            "date_sql_type": "DATE",
            "numbers_sql_type": "DECIMAL(18,2)",
            "status_sql_type": "NVARCHAR(50)",
            "dropdown_sql_type": "NVARCHAR(100)",
            "people_sql_type": "NVARCHAR(255)"
        },
        "metadata": {
            "description": board.get("description"),
            "items_count": board.get("items_count", 0),
            "discovery_version": "2.0"
        }
    }
    
    # Process columns with enhanced control fields
    for col in board["columns"]:
        col_info = {
            "monday_id": col["id"],
            "monday_title": col["title"],
            "monday_type": col["type"],
            "sql_column": col["title"],
            "sql_type": map_monday_type_to_sql(col["type"]),
            "extraction_field": get_extraction_field(col["type"]),
            "nullable": True,
            "is_system_field": col["id"] in ["name", "person", "status", "date"],
            "conversion_logic": get_conversion_logic(col["type"]),
            "exclude": False,                    # Default to include
            "custom_sql_type": None,             # User can override
            "custom_extraction_field": None     # User can override
        }
        
        metadata["columns"].append(col_info)
    
    logger.info(f"Schema discovered: {len(metadata['columns'])} columns")
    return metadata

def map_monday_type_to_sql(monday_type: str) -> str:
    """Map Monday.com column types to SQL types"""
    type_mapping = {
        'text': 'NVARCHAR(MAX)',
        'long_text': 'NVARCHAR(MAX)', 
        'numbers': 'DECIMAL(18,2)',
        'date': 'DATE',
        'status': 'NVARCHAR(100)',
        'dropdown': 'NVARCHAR(100)',
        'people': 'NVARCHAR(255)',
        'item_id': 'BIGINT NOT NULL',
        'mirror': 'NVARCHAR(MAX)',
        'formula': 'NVARCHAR(MAX)',
        'board_relation': 'NVARCHAR(MAX)',
        'subtasks': 'NVARCHAR(MAX)',
        'dependency': 'NVARCHAR(MAX)'
    }
    return type_mapping.get(monday_type, 'NVARCHAR(255)')

def get_extraction_field(monday_type: str) -> str:
    """Get the GraphQL field to extract for each column type"""
    field_mapping = {
        'text': 'text',
        'long_text': 'text',
        'numbers': 'number',
        'date': 'text',
        'status': 'label',
        'dropdown': 'text',
        'people': 'text',
        'item_id': 'item_id',
        'mirror': 'display_value',
        'formula': 'display_value',
        'board_relation': 'display_value'
    }
    return field_mapping.get(monday_type, 'text')

def get_conversion_logic(monday_type: str) -> str:
    """Get SQL conversion logic for complex types"""
    if monday_type == 'date':
        return 'safe_date_convert(extract_value(cv))'
    elif monday_type == 'numbers':
        return 'safe_numeric_convert(extract_value(cv))'
    return None

def save_metadata_file(metadata: Dict[str, Any], board_id: int) -> Path:
    """Save metadata to JSON file"""
    metadata_dir = repo_root / "configs" / "boards"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    
    metadata_file = metadata_dir / f"board_{board_id}_metadata.json"
    
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Metadata saved: {metadata_file}")
    return metadata_file

def update_board_registry(board_id: int, metadata: Dict[str, Any]) -> Path:
    """Update the board registry with new board info"""
    registry_path = repo_root / "configs" / "registry.json"
    
    # Load existing registry
    if registry_path.exists():
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
    else:
        registry = {
            "boards": {},
            "metadata": {
                "version": "1.0",
                "created_at": datetime.now().isoformat()
            }
        }
    
    # Update board entry
    registry["boards"][str(board_id)] = {
        "board_name": metadata["board_name"],
        "table_name": metadata["table_name"],
        "database": metadata["database"],
        "discovered_at": metadata["discovered_at"],
        "status": "discovered",
        "metadata_path": f"configs/boards/board_{board_id}_metadata.json",
        "config_path": f"configs/boards/board_{board_id}.json",
        "workflow_path": f"workflows/extract_board_{board_id}.yaml"
    }
    
    registry["metadata"]["updated_at"] = datetime.now().isoformat()
    
    # Save registry
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Registry updated: {registry_path}")
    return registry_path

def generate_kestra_workflow(board_id: int, metadata: Dict[str, Any]) -> Path:
    """Generate Kestra workflow YAML"""
    workflow_dir = repo_root / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    
    workflow_file = workflow_dir / f"extract_board_{board_id}.yaml"
    
    workflow_content = f"""id: extract_board_{board_id}
namespace: monday.boards

description: "Extract data from Monday.com board: {metadata['board_name']}"

tasks:
  - id: extract_board_data
    type: io.kestra.plugin.scripts.python.Script
    description: "Extract board {board_id} using unified loader"
    script: |
      python pipelines/scripts/load_boards.py --board-id {board_id}
    
  - id: validate_data
    type: io.kestra.plugin.scripts.python.Script
    description: "Validate extracted data"
    script: |
      python tests/validation/validate_board_{board_id}.py

triggers:
  - id: daily_refresh
    type: io.kestra.plugin.core.trigger.Schedule
    cron: "0 6 * * *"  # Daily at 6 AM
    
  - id: manual_trigger
    type: io.kestra.plugin.core.trigger.Webhook
"""
    
    with open(workflow_file, 'w', encoding='utf-8') as f:
        f.write(workflow_content)
    
    logger.info(f"Kestra workflow generated: {workflow_file}")
    return workflow_file

def main():
    parser = argparse.ArgumentParser(description='Universal Monday.com Board Extractor')
    parser.add_argument('--board-id', required=True, type=int, help='Monday.com board ID')
    parser.add_argument('--board-name', help='Human-readable board name (auto-discovered if not provided)')
    parser.add_argument('--table-name', help='Target SQL table name (auto-generated if not provided)')
    parser.add_argument('--database', default='orders', help='Target database name')
    parser.add_argument('--discovery-only', action='store_true', help='Only discover schema, do not generate files')
    
    args = parser.parse_args()
    
    logger.info("Universal Monday.com Board Extractor")
    logger.info(f"Board ID: {args.board_id}")
    logger.info(f"Target Database: {args.database}")
    
    try:
        # 1. Discover board schema
        logger.info("STEP 1/4: Discovering board schema...")
        metadata = discover_board_schema(args.board_id)
        
        # Override with user-provided values if specified
        if args.board_name:
            metadata["board_name"] = args.board_name
        if args.table_name:
            metadata["table_name"] = args.table_name
        if args.database:
            metadata["database"] = args.database
        
        logger.info(f"Discovered board: {metadata['board_name']}")
        
        if args.discovery_only:
            logger.info("Discovery complete (discovery-only mode)")
            return
        
        # 2. Save metadata file
        logger.info("STEP 2/4: Saving metadata file...")
        metadata_file = save_metadata_file(metadata, args.board_id)
        
        # 3. Update registry
        logger.info("STEP 3/4: Updating board registry...")
        registry_file = update_board_registry(args.board_id, metadata)
        
        # 4. Generate Kestra workflow
        logger.info("STEP 4/4: Generating Kestra workflow...")
        workflow_file = generate_kestra_workflow(args.board_id, metadata)
        
        # Summary
        logger.info("SUCCESS: Board extraction setup complete!")
        logger.info(f"  Metadata: {metadata_file}")
        logger.info(f"  Registry: {registry_file}")
        logger.info(f"  Workflow: {workflow_file}")
        logger.info("")
        logger.info("Next steps:")
        logger.info(f"  1. Review metadata: {metadata_file}")
        logger.info(f"  2. Run ETL: python pipelines/scripts/load_boards.py --board-id {args.board_id}")
        logger.info(f"  3. Deploy workflow: kubectl apply -f {workflow_file}")
        
    except Exception as e:
        logger.error(f"Error during board extraction: {e}")
        raise

if __name__ == "__main__":
    main()