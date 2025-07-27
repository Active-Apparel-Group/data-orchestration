"""
Tests Package - Data Orchestration Project
Supports both legacy and modern package structure during transition
"""
import sys
from pathlib import Path

# Add src/ to path for new package structure
repo_root = Path(__file__).parent.parent
src_path = repo_root / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

# Add pipelines/utils for legacy compatibility during transition
pipelines_utils_path = repo_root / "pipelines" / "utils"
if pipelines_utils_path.exists():
    sys.path.insert(0, str(pipelines_utils_path))
