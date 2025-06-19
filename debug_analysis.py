#!/usr/bin/env python3
"""
Debug script to analyze specific file
"""

import os
import sys
from pathlib import Path
import re

def find_repo_root():
    """Find the repository root by looking for utils folder"""
    current_path = Path(__file__).resolve()
    while current_path.parent != current_path:
        utils_path = current_path / "utils"
        if utils_path.exists() and (utils_path / "db_helper.py").exists():
            return current_path
        current_path = current_path.parent
    raise RuntimeError("Could not find repository root with utils folder")

def analyze_script_imports(script_path):
    """Analyze a script's import patterns to determine if refactoring is needed"""
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        analysis = {
            'path': script_path,
            'needs_refactor': False,
            'has_old_imports': False,
            'has_new_pattern': False,
            'import_issues': [],
            'uses_db_helper': False,
            'uses_logger': False
        }
          # Check for old import patterns (hardcoded paths, not our new standardized ones)
        old_patterns = [
            r'sys\.path\.append\(',  # Old append style
            r'sys\.path\.insert\(0,\s*r[\'"].*utils',  # Hardcoded raw string paths
            r'sys\.path\.insert\(0,\s*[\'"].*utils',   # Hardcoded regular string paths  
            r'from.*utils.*import',  # Direct utils imports
        ]
        
        for pattern in old_patterns:
            if re.search(pattern, content):
                analysis['has_old_imports'] = True
                analysis['import_issues'].append(f"Found old pattern: {pattern}")
        
        # Check for new standardized pattern
        if 'def find_repo_root():' in content:
            analysis['has_new_pattern'] = True
        
        # Check for specific module usage
        if 'db_helper' in content or 'db.' in content:
            analysis['uses_db_helper'] = True
        
        if 'logger' in content and ('logging' in content or 'logger_helper' in content):
            analysis['uses_logger'] = True
        
        # Determine if refactoring is needed
        if analysis['uses_db_helper'] or analysis['uses_logger']:
            if not analysis['has_new_pattern']:
                analysis['needs_refactor'] = True
        
        return analysis
        
    except Exception as e:
        print(f"Error analyzing {script_path}: {e}")
        return None

# Debug specific files
files_to_debug = [
    r"dev\audit-pipeline\validation\validate_env.py",
    r"dev\monday-boards-dynamic\core\monday_board_cli.py", 
    r"dev\monday-boards-dynamic\debugging\verify_db_types.py"
]

repo_root = find_repo_root()

for file_path in files_to_debug:
    full_path = repo_root / file_path
    print(f"\n=== ANALYZING: {file_path} ===")
    analysis = analyze_script_imports(full_path)
    if analysis:
        for key, value in analysis.items():
            print(f"{key:15}: {value}")
    else:
        print("ANALYSIS FAILED")
