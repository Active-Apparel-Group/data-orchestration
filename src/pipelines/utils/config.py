"""Configuration utilities"""
import sys
from pathlib import Path

# Source from pipelines/utils (NOT root utils - that's outdated)
pipelines_utils_path = Path(__file__).parent.parent.parent.parent / "pipelines" / "utils"
if pipelines_utils_path.exists():
    sys.path.insert(0, str(pipelines_utils_path))
    
    try:
        from db_helper import load_config
    except ImportError as e:
        print(f"Warning: Could not import config from pipelines/utils: {e}")

# TODO: Create dedicated config module
