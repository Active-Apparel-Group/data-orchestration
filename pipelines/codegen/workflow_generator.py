#!/usr/bin/env python3
"""
Kestra Workflow Generator for Board Extraction
==============================================

Generates Kestra workflow YAML files for board extraction jobs.
"""

import json
import yaml
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

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

def generate_workflow_yaml(board_id: int, config: Dict[str, Any]) -> str:
    """Generate Kestra workflow YAML for a board"""
    
    board_name = config["meta"]["board_name"]
    table_name = config["meta"]["table_name"]
    db_name = config["meta"]["db_name"]
    
    # Clean workflow ID (lowercase, no spaces)
    workflow_id = f"extract_board_{board_id}"
    
    workflow = {
        "id": workflow_id,
        "namespace": "data.monday.boards",
        "description": f"Extract {board_name} (ID: {board_id}) to {db_name}.{table_name}",
        "labels": {
            "board_id": str(board_id),
            "board_name": board_name,
            "target_table": table_name,
            "target_database": db_name
        },
        "inputs": [
            {
                "id": "board_id",
                "type": "INT",
                "defaults": board_id,
                "description": "Monday.com board ID to extract"
            }
        ],
        "triggers": [
            {
                "id": "schedule",
                "type": "io.kestra.core.models.triggers.types.Schedule",
                "cron": "0 */6 * * *",  # Every 6 hours
                "timezone": "America/New_York"
            }
        ],
        "tasks": [
            {
                "id": "extract_board",
                "type": "io.kestra.plugin.scripts.python.Script",
                "description": f"Extract Monday.com board {board_id} to SQL Server",
                "script": f"""
import subprocess
import sys
from pathlib import Path

# Standard import pattern for logger helper in Kestra
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "pipelines" / "utils").exists():
            return current
        current = current.parent
    return Path("/app")  # Fallback for Kestra

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

import logger_helper
logger = logger_helper.get_logger(__name__)

# Run the unified board loader
result = subprocess.run([
    sys.executable, 
    "pipelines/scripts/load_boards.py",
    "--board-id", "{board_id}"
], capture_output=True, text=True, cwd="/app")

logger.info(f"Exit code: {{result.returncode}}")
logger.info(f"STDOUT: {{result.stdout}}")
if result.stderr:
    logger.info(f"STDERR: {{result.stderr}}")

if result.returncode != 0:
    raise Exception(f"Board extraction failed with exit code {{result.returncode}}")

logger.info("✅ Board extraction completed successfully")
                """.strip(),
                "env": {
                    "MONDAY_API_KEY": "{{ secret('MONDAY_API_KEY') }}",
                    "MONDAY_API_VERSION": "2025-04"
                }
            }
        ]
    }
    
    return yaml.dump(workflow, default_flow_style=False, sort_keys=False)

def save_workflow(board_id: int, config: Dict[str, Any], workflows_dir: Path):
    """Save workflow YAML file"""
    workflow_yaml = generate_workflow_yaml(board_id, config)
    workflow_path = workflows_dir / f"extract_board_{board_id}.yaml"
    
    with open(workflow_path, 'w', encoding='utf-8') as f:
        f.write(workflow_yaml)
    
    return workflow_path

if __name__ == "__main__":
    # Example usage
    repo_root = Path(__file__).parent.parent.parent
    config_path = repo_root / "configs" / "boards" / "board_9200517329.json"
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        workflows_dir = repo_root / "workflows"
        workflows_dir.mkdir(exist_ok=True)
        
        workflow_path = save_workflow(9200517329, config, workflows_dir)
        logger.info(f"✅ Generated workflow: {workflow_path}")
    else:
        logger.info("❌ Config file not found")
