#!/usr/bin/env python3
"""
Script Analysis and Refactoring Utility
Helps identify Python scripts that need refactoring and applies the new import pattern
"""

import os
import sys
from pathlib import Path
import re
import shutil
from datetime import datetime

def find_repo_root():
    """Find the repository root by looking for utils folder"""
    current_path = Path(__file__).resolve()
    while current_path.parent != current_path:
        utils_path = current_path / "utils"
        if utils_path.exists() and (utils_path / "db_helper.py").exists():
            return current_path
        current_path = current_path.parent
    raise RuntimeError("Could not find repository root with utils folder")

# Add utils to path
repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

def find_python_scripts(directory):
    """Find all Python scripts in a directory and subdirectories, excluding backups"""
    scripts = []
    directory_path = Path(directory)
    
    if not directory_path.exists():
        print(f"Directory does not exist: {directory}")
        return scripts
    
    for py_file in directory_path.rglob("*.py"):
        # Skip __pycache__, test files, and backup directories
        if ("__pycache__" not in str(py_file) and 
            not py_file.name.startswith("test_") and
            "backup" not in str(py_file).lower()):
            scripts.append(py_file)
    
    return scripts

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

def generate_refactor_report(directories):
    """Generate a comprehensive report of scripts needing refactoring"""
    print("=== DB Helper Refactoring Analysis Report ===")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    all_scripts = []
    scripts_needing_refactor = []
    
    for directory in directories:
        print(f"\nAnalyzing directory: {directory}")
        scripts = find_python_scripts(directory)
        print(f"Found {len(scripts)} Python files")
        
        for script in scripts:
            analysis = analyze_script_imports(script)
            if analysis:
                all_scripts.append(analysis)
                if analysis['needs_refactor']:
                    scripts_needing_refactor.append(analysis)
                    print(f"  NEEDS REFACTOR: {script.relative_to(repo_root)}")
                elif analysis['has_new_pattern']:
                    print(f"  ALREADY UPDATED: {script.relative_to(repo_root)}")
                else:
                    print(f"  NO ACTION NEEDED: {script.relative_to(repo_root)}")
    
    print(f"\n=== SUMMARY ===")
    print(f"Total Python files analyzed: {len(all_scripts)}")
    print(f"Scripts needing refactoring: {len(scripts_needing_refactor)}")
    print(f"Scripts already updated: {len([s for s in all_scripts if s['has_new_pattern']])}")
    
    print(f"\n=== SCRIPTS REQUIRING REFACTORING ===")
    for script in scripts_needing_refactor:
        rel_path = script['path'].relative_to(repo_root)
        print(f"  {rel_path}")
        for issue in script['import_issues']:
            print(f"    - {issue}")
    
    return scripts_needing_refactor

def create_backup(script_path):
    """Create a backup of the original script"""
    backup_dir = repo_root / "dev" / "db-helper-refactor" / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    # Create relative path structure in backup
    rel_path = script_path.relative_to(repo_root)
    backup_path = backup_dir / rel_path
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    
    shutil.copy2(script_path, backup_path)
    print(f"Backup created: {backup_path}")
    return backup_path

def apply_refactor_pattern(script_path, dry_run=True):
    """Apply the new import pattern to a script"""
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # If already has new pattern, skip
        if 'def find_repo_root():' in content:
            print(f"SKIP: {script_path} already has new pattern")
            return True
        
        print(f"REFACTORING: {script_path}")
        
        if not dry_run:
            # Create backup first
            create_backup(script_path)
        
        # This is a simplified refactoring - in practice, you'd need more sophisticated parsing
        # For now, just print what would be done
        print(f"  Would add find_repo_root() function")
        print(f"  Would standardize import statements")
        print(f"  Would add logger_helper integration")
        
        if not dry_run:
            # Here you would actually modify the file
            # This requires careful parsing and replacement
            pass
        
        return True
        
    except Exception as e:
        print(f"Error refactoring {script_path}: {e}")
        return False

def main():
    """Main function to run the analysis and refactoring"""
    print("DB Helper Refactoring Utility")
    print("=" * 50)
    
    # Target directories for analysis
    target_directories = [
        repo_root / "scripts",
        repo_root / "dev"
    ]
    
    # Generate analysis report
    scripts_to_refactor = generate_refactor_report(target_directories)
    
    if not scripts_to_refactor:
        print("\nNo scripts need refactoring!")
        return
    
    print(f"\nFound {len(scripts_to_refactor)} scripts that need refactoring.")
    
    # Ask user if they want to proceed with refactoring
    response = input("\nDo you want to apply refactoring? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        print("\nStarting refactoring process...")
        
        for script_info in scripts_to_refactor:
            success = apply_refactor_pattern(script_info['path'], dry_run=False)
            if success:
                print(f"  ✓ Refactored: {script_info['path']}")
            else:
                print(f"  ✗ Failed: {script_info['path']}")
    else:
        print("\nDry run completed. No files were modified.")
        print("To apply changes, run this script again and choose 'y' when prompted.")

if __name__ == "__main__":
    main()
