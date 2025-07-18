"""Database utilities - migrated from pipelines/utils/db_helper.py"""
import sys
from pathlib import Path

# Source from pipelines/utils (NOT root utils - that's outdated)
pipelines_utils_path = Path(__file__).parent.parent.parent.parent / "pipelines" / "utils"
if pipelines_utils_path.exists():
    sys.path.insert(0, str(pipelines_utils_path))
    
    try:
        from db_helper import *
        # Re-export for new package structure
        get_connection = get_connection
        load_config = load_config
    except ImportError as e:
        print(f"Warning: Could not import from pipelines/utils/db_helper: {e}")

# TODO: Replace with native implementation
