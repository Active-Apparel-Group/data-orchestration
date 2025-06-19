#!/usr/bin/env python3
"""
VS Code Tasks Generator
Automatically generates VS Code tasks.json entries from YAML task files and tool scripts
"""

import sys
from pathlib import Path
import json
import yaml
import re
from typing import Dict, List, Any

def find_repo_root() -> Path:
    """Find repository root by looking for marker files"""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if any((parent / marker).exists() for marker in ['.git', 'pyproject.toml', 'requirements.txt']):
            return parent
    raise FileNotFoundError("Repository root not found")

def load_yaml_tasks(task_dir: Path) -> List[Dict[str, Any]]:
    """Load all YAML task files from a directory"""
    tasks = []
    for yaml_file in task_dir.glob("*.yml"):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                task_data = yaml.safe_load(f)
                if task_data:
                    task_data['_file'] = yaml_file.name
                    tasks.append(task_data)
        except Exception as e:
            print(f"Warning: Could not load {yaml_file}: {e}")
    return tasks

def yaml_task_to_vscode_task(yaml_task: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a YAML task to VS Code task format"""
    task_type = yaml_task.get('type', 'unknown')
    title = yaml_task.get('title', yaml_task.get('id', 'Unknown Task'))
    
    # Create a clean label
    label = f"{task_type.title()}: {title}"
    if len(label) > 60:
        # Truncate long titles
        label = f"{task_type.title()}: {title[:50]}..."
    
    # Determine command based on task content
    command = "echo"
    args = [f"Task '{title}' - See {yaml_task.get('_file', 'task file')} for details"]
    
    # Try to extract executable commands from jobs
    if 'jobs' in yaml_task and yaml_task['jobs']:
        first_job = yaml_task['jobs'][0]
        if 'command' in first_job:
            cmd_parts = first_job['command'].split()
            if cmd_parts:
                command = cmd_parts[0]
                args = cmd_parts[1:] if len(cmd_parts) > 1 else []
    
    # Set group based on task type
    group = "build"
    if task_type == "ops":
        group = "build"
    elif "test" in title.lower() or "validate" in title.lower():
        group = "test"
    
    vscode_task = {
        "label": label,
        "type": "shell",
        "command": command,
        "group": group,
        "presentation": {
            "echo": True,
            "reveal": "always",
            "focus": False,
            "panel": "new"
        },
        "options": {
            "cwd": "${workspaceFolder}"
        },
        "problemMatcher": [],
        "detail": yaml_task.get('description', f"Execute {task_type} task: {title}")
    }
    
    if args:
        vscode_task["args"] = args
    
    return vscode_task

def scan_tool_scripts(tools_dir: Path) -> List[Dict[str, Any]]:
    """Scan tools directory for executable scripts"""
    tasks = []
    
    # PowerShell scripts
    for ps_file in tools_dir.glob("*.ps1"):
        if ps_file.name.startswith('.'):
            continue
            
        label = f"Tools: {ps_file.stem.replace('-', ' ').title()}"
        tasks.append({
            "label": label,
            "type": "shell",
            "command": "powershell",
            "args": ["-File", f"tools/{ps_file.name}"],
            "group": "build",
            "presentation": {
                "echo": True,
                "reveal": "always",
                "focus": False,
                "panel": "new"
            },
            "options": {
                "cwd": "${workspaceFolder}"
            },
            "problemMatcher": [],
            "detail": f"Execute PowerShell tool: {ps_file.name}"
        })
    
    # Python scripts
    for py_file in tools_dir.glob("*.py"):
        if py_file.name.startswith('.') or py_file.name.startswith('__'):
            continue
            
        label = f"Tools: {py_file.stem.replace('_', ' ').title()}"
        tasks.append({
            "label": label,
            "type": "shell",
            "command": "python",
            "args": [f"tools/{py_file.name}"],
            "group": "build",
            "presentation": {
                "echo": True,
                "reveal": "always",
                "focus": True if 'scaffold' in py_file.name or 'generator' in py_file.name else False,
                "panel": "new"
            },
            "options": {
                "cwd": "${workspaceFolder}"
            },
            "problemMatcher": [],
            "detail": f"Execute Python tool: {py_file.name}"
        })
    
    return tasks

def generate_vscode_tasks() -> Dict[str, Any]:
    """Generate complete VS Code tasks configuration"""
    repo_root = find_repo_root()
    
    tasks = []
    
    # Load dev tasks
    dev_tasks_dir = repo_root / "tasks" / "dev"
    if dev_tasks_dir.exists():
        dev_yaml_tasks = load_yaml_tasks(dev_tasks_dir)
        for yaml_task in dev_yaml_tasks:
            tasks.append(yaml_task_to_vscode_task(yaml_task))
    
    # Load ops tasks
    ops_tasks_dir = repo_root / "tasks" / "ops"
    if ops_tasks_dir.exists():
        ops_yaml_tasks = load_yaml_tasks(ops_tasks_dir)
        for yaml_task in ops_yaml_tasks:
            tasks.append(yaml_task_to_vscode_task(yaml_task))
    
    # Load tool scripts
    tools_dir = repo_root / "tools"
    if tools_dir.exists():
        tool_tasks = scan_tool_scripts(tools_dir)
        tasks.extend(tool_tasks)
    
    # Add some standard validation tasks
    standard_tasks = [
        {
            "label": "Validate: Import Patterns",
            "type": "shell", 
            "command": "python",
            "args": ["dev/db-helper-refactor/validation/test_import_patterns.py"],
            "group": "test",
            "presentation": {
                "echo": True,
                "reveal": "always",
                "focus": False,
                "panel": "new"
            },
            "options": {
                "cwd": "${workspaceFolder}"
            },
            "problemMatcher": [],
            "detail": "Validate all scripts use correct import patterns"
        },
        {
            "label": "Validate: Environment",
            "type": "shell",
            "command": "python", 
            "args": ["dev/audit-pipeline/validation/validate_env.py"],
            "group": "test",
            "presentation": {
                "echo": True,
                "reveal": "always",
                "focus": False,
                "panel": "new"
            },
            "options": {
                "cwd": "${workspaceFolder}"
            },
            "problemMatcher": [],
            "detail": "Validate Azure SQL connections and environment"
        }
    ]
    
    tasks.extend(standard_tasks)
    
    return {
        "version": "2.0.0",
        "tasks": tasks
    }

def main():
    """Main function"""
    try:
        print("🔧 Generating VS Code tasks from YAML task files and tools...")
        
        # Generate tasks configuration
        tasks_config = generate_vscode_tasks()
        
        print(f"📋 Generated {len(tasks_config['tasks'])} tasks")
        
        # Output as JSON
        print("\n" + "="*60)
        print("VS Code tasks.json content:")
        print("="*60)
        print(json.dumps(tasks_config, indent=4))
        
        # Optionally write to file
        repo_root = find_repo_root()
        output_file = repo_root / ".vscode" / "tasks-generated.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tasks_config, f, indent=4)
        
        print(f"\n✅ Tasks configuration written to: {output_file}")
        print("\n💡 To use this configuration:")
        print("   1. Review the generated tasks-generated.json")
        print("   2. Merge with your existing .vscode/tasks.json")
        print("   3. Access tasks via Ctrl+Shift+P > 'Tasks: Run Task'")
        
    except Exception as e:
        print(f"❌ Error generating tasks: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
