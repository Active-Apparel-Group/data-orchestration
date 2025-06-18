#!/usr/bin/env python3
"""
Task Scaffolding CLI for Data Orchestration Platform

This script helps create new development and operations tasks from templates,
following our established patterns and directory structure.

Usage:
    python task-scaffold.py dev --project monday-boards --title "Extract new board data"
    python task-scaffold.py ops --title "Nightly database backup" --schedule "0 2 * * *"
    python task-scaffold.py workflow --workflow_type monday-board --board_id 123456 --board_name "Customer Onboarding" --title "Sync new users to DB"
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
import yaml
from jinja2 import Template

def get_next_task_id(task_type: str, project: str = None) -> str:
    """Generate next available task ID"""
    today = datetime.now().strftime("%Y%m%d")
    
    if task_type == "dev":
        # Format: dev-{project}-YYYYMMDD-{seq}
        base_pattern = f"dev-{project}-{today}-"
        search_dir = Path("tasks/dev")
    else:
        # Format: ops-{title-slug}-YYYYMMDD-{seq}
        base_pattern = f"ops-{today}-"
        search_dir = Path("tasks/ops")
    
    # Find existing files with same date pattern
    existing_files = []
    if search_dir.exists():
        for file in search_dir.glob("*.yml"):
            if file.stem.startswith(base_pattern.rstrip("-")):
                existing_files.append(file.stem)
    
    # Find next sequence number
    seq = 1
    while f"{base_pattern}{seq:03d}" in existing_files:
        seq += 1
    
    return f"{base_pattern}{seq:03d}"

def slugify(text: str) -> str:
    """Convert text to URL-friendly slug"""
    import re
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

def render_template(template_path: Path, context: dict) -> str:
    """Render Jinja2 template with given context"""
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    template = Template(template_content)
    return template.render(**context)

def create_dev_task(args):
    """Create a new development task"""
    # Ensure required directories exist
    Path("tasks/dev").mkdir(parents=True, exist_ok=True)
    
    # Generate task ID
    task_id = get_next_task_id("dev", args.project)    
    # Prepare template context
    context = {
        'task_id': task_id,
        'project_name': args.project,
        'task_title': args.title,
        'creation_date': datetime.now().isoformat(),
        'assignee': args.assignee or 'unassigned',
        'priority': args.priority or 'medium',
        'task_description': args.description or 'TODO: Add detailed description',
        'background_info': args.background or 'TODO: Add background information',
        'acceptance_criteria': args.criteria or 'TODO: Define acceptance criteria',
    }
    
    # Render template
    template_path = Path("templates/dev-task.yml.tpl")
    if not template_path.exists():
        print(f"❌ Template not found: {template_path}")
        sys.exit(1)
    
    try:
        rendered_content = render_template(template_path, context)
        
        # Write task file
        task_file = Path(f"tasks/dev/{task_id}.yml")
        with open(task_file, 'w', encoding='utf-8') as f:
            f.write(rendered_content)
        
        print(f"✅ Created development task: {task_file}")
        print(f"📋 Task ID: {task_id}")
        print(f"🏗️ Project: {args.project}")
        print(f"📝 Title: {args.title}")
        print(f"\\n📂 Next steps:")
        print(f"   1. Edit {task_file} to fill in TODO sections")
        print(f"   2. Create dev folder: dev/{args.project}/")
        print(f"   3. Follow the checklist in the task file")
        
    except Exception as e:
        print(f"❌ Error creating task: {e}")
        print(f"📝 Context being used:")
        for key, value in context.items():
            print(f"   {key}: {value}")
        sys.exit(1)

def create_ops_task(args):
    """Create a new operations task"""
    # Ensure required directories exist
    Path("tasks/ops").mkdir(parents=True, exist_ok=True)    
    # Generate task ID or use title-based name for ops
    if args.recurring:
        # For recurring ops, use descriptive name
        task_id = slugify(args.title)
    else:
        # For one-off ops, use date-based ID
        task_id = get_next_task_id("ops")
    
    # Prepare template context
    context = {
        'task_id': task_id,
        'title': args.title,
        'description': args.description or 'TODO: Add operation description',
        'cron_expression': args.schedule or 'manual',
        'operation_category': args.category or 'maintenance',
        'operation_name': slugify(args.title),
        'log_path': f"logs/{task_id}/",        'pre_check_command': args.precheck or 'echo Pre-checks passed',
        'main_command': args.command or 'echo Operation completed',
        'validation_command': args.validation or 'echo Validation passed',
        'working_dir': args.workdir or '.',
        'timeout_minutes': args.timeout or 30,
        'required_env_var_1': 'EXAMPLE_VAR_1',
        'required_env_var_2': 'EXAMPLE_VAR_2',
        'optional_env_var_1': 'OPTIONAL_VAR_1',
        'required_tool_1': 'python',
        'required_service_1': 'kestra', 
        'required_file_1': 'requirements.txt',
        'error_log_path': f"logs/{task_id}/error.log",
        'success_log_path': f"logs/{task_id}/success.log",
        'alert_channel': '#ops-alerts',
        'archive_logs_to': f"archives/{task_id}/logs/",
        'archive_outputs_to': f"archives/{task_id}/outputs/",
        'temp_files_pattern': f"tmp/{task_id}/*",        'health_check_command': 'echo Health_check_passed',
        'metric_name': 'operation_duration',
        'metric_command': 'echo 0',
        'alert_condition': 'failure_rate > 10%',
        'alert_action': 'send_notification',
        'workflow_name': slugify(args.title),
        'deployment_script': 'deploy-ops.ps1',
        'makefile_target': f"ops-{slugify(args.title)}",
    }
    
    # Render template
    template_path = Path("templates/op-task.yml.tpl")
    if not template_path.exists():
        print(f"❌ Template not found: {template_path}")
        sys.exit(1)
    
    try:
        rendered_content = render_template(template_path, context)
        
        # Write task file
        task_file = Path(f"tasks/ops/{task_id}.yml")
        with open(task_file, 'w', encoding='utf-8') as f:
            f.write(rendered_content)
        
        print(f"✅ Created operations task: {task_file}")
        print(f"📋 Task ID: {task_id}")
        print(f"⚙️ Operation: {args.title}")
        if args.schedule and args.schedule != 'manual':
            print(f"⏰ Schedule: {args.schedule}")
        print(f"\\n📂 Next steps:")
        print(f"   1. Edit {task_file} to fill in command details")
        print(f"   2. Test commands manually first")
        print(f"   3. Set up monitoring and alerting")
        
    except Exception as e:
        print(f"❌ Error creating task: {e}")
        sys.exit(1)

def create_workflow_task(args):
    """Create a new workflow task from a specific workflow template"""
    # Ensure required directories exist
    Path("tasks/workflows").mkdir(parents=True, exist_ok=True)
    
    # Generate task ID based on workflow type and board name
    today = datetime.now().strftime("%Y%m%d")
    board_slug = slugify(args.board_name) if hasattr(args, 'board_name') else 'workflow'
    task_id = f"{args.workflow_type}-{board_slug}-{today}"
    
    # Prepare template context based on workflow type
    if args.workflow_type == 'monday-board':
        context = {
            'board_id': args.board_id,
            'board_name': args.board_name,
            'table_name': args.table_name or slugify(args.board_name).replace('-', '_'),
            'developer_name': args.developer or 'developer',
            'creation_date': datetime.now().isoformat(),
            'update_frequency': args.frequency or 'daily',
        }
        template_path = Path("templates/monday-board-deployment.yml.tpl")
    else:
        print(f"❌ Unknown workflow type: {args.workflow_type}")
        sys.exit(1)
    
    # Check if template exists
    if not template_path.exists():
        print(f"❌ Template not found: {template_path}")
        sys.exit(1)
    
    try:
        rendered_content = render_template(template_path, context)
        
        # Write workflow task file
        task_file = Path(f"tasks/workflows/{task_id}.yml")
        with open(task_file, 'w', encoding='utf-8') as f:
            f.write(rendered_content)
        
        print(f"✅ Created workflow task: {task_file}")
        print(f"📋 Task ID: {task_id}")
        print(f"🔄 Workflow: {args.workflow_type}")
        if hasattr(args, 'board_name'):
            print(f"📊 Board: {args.board_name} (ID: {args.board_id})")
        print(f"\\n📂 Next steps:")
        print(f"   1. Edit {task_file} to review and customize")
        print(f"   2. Follow the checklist in the workflow task")
        print(f"   3. Use the provided commands for each deployment phase")
        
    except Exception as e:
        print(f"❌ Error creating workflow task: {e}")
        sys.exit(1)

def list_tasks():
    """List existing tasks"""
    print("📋 Existing Tasks:\\n")
    
    # List dev tasks
    dev_dir = Path("tasks/dev")
    if dev_dir.exists():
        dev_tasks = list(dev_dir.glob("*.yml"))
        if dev_tasks:
            print("🏗️ Development Tasks:")
            for task_file in sorted(dev_tasks):
                try:
                    with open(task_file, 'r', encoding='utf-8') as f:
                        task_data = yaml.safe_load(f)
                    title = task_data.get('title', 'No title')
                    project = task_data.get('project', 'Unknown')
                    print(f"   {task_file.stem}: {title} ({project})")
                except Exception:
                    print(f"   {task_file.stem}: [Unable to read]")
            print()
    
    # List ops tasks
    ops_dir = Path("tasks/ops")
    if ops_dir.exists():
        ops_tasks = list(ops_dir.glob("*.yml"))
        if ops_tasks:
            print("⚙️ Operations Tasks:")
            for task_file in sorted(ops_tasks):
                try:
                    with open(task_file, 'r', encoding='utf-8') as f:
                        task_data = yaml.safe_load(f)
                    title = task_data.get('title', 'No title')
                    schedule = task_data.get('schedule', 'manual')
                    print(f"   {task_file.stem}: {title} ({schedule})")
                except Exception:
                    print(f"   {task_file.stem}: [Unable to read]")
            print()
    
    # List workflow tasks
    workflow_dir = Path("tasks/workflows")
    if workflow_dir.exists():
        workflow_tasks = list(workflow_dir.glob("*.yml"))
        if workflow_tasks:
            print("🔄 Workflow Tasks:")
            for task_file in sorted(workflow_tasks):
                try:
                    with open(task_file, 'r', encoding='utf-8') as f:
                        task_data = yaml.safe_load(f)
                    workflow_type = task_data.get('workflow_type', 'Unknown')
                    board_name = task_data.get('board_name', 'No name')
                    print(f"   {task_file.stem}: {workflow_type} - {board_name}")
                except Exception:
                    print(f"   {task_file.stem}: [Unable to read]")
            print()
    
    # List completed tasks
    completed_dir = Path("tasks/completed")
    if completed_dir.exists():
        completed_tasks = list(completed_dir.glob("*.yml"))
        if completed_tasks:
            print(f"✅ Completed Tasks: {len(completed_tasks)} tasks archived")

def main():
    parser = argparse.ArgumentParser(
        description="Create and manage development and operations tasks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a development task
  python task-scaffold.py dev --project monday-boards --title "Extract customer master schedule"
  
  # Create a recurring operations task
  python task-scaffold.py ops --title "Nightly backup" --schedule "0 2 * * *" --recurring
  
  # Create a workflow task from a template
  python task-scaffold.py workflow --workflow_type monday-board --board_id 123456 --board_name "Customer Onboarding" --title "Sync new users to DB"
  
  # List all tasks
  python task-scaffold.py list
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Development task subcommand
    dev_parser = subparsers.add_parser('dev', help='Create a development task')
    dev_parser.add_argument('--project', required=True, help='Project name (e.g., monday-boards)')
    dev_parser.add_argument('--title', required=True, help='Task title')
    dev_parser.add_argument('--description', help='Detailed description')
    dev_parser.add_argument('--background', help='Background information')
    dev_parser.add_argument('--criteria', help='Acceptance criteria')
    dev_parser.add_argument('--assignee', help='Assigned developer')
    dev_parser.add_argument('--priority', choices=['low', 'medium', 'high', 'critical'], help='Task priority')
    
    # Operations task subcommand
    ops_parser = subparsers.add_parser('ops', help='Create an operations task')
    ops_parser.add_argument('--title', required=True, help='Operation title')
    ops_parser.add_argument('--description', help='Operation description')
    ops_parser.add_argument('--schedule', help='Cron schedule (e.g., "0 2 * * *") or "manual"')
    ops_parser.add_argument('--category', help='Operation category (deployment, maintenance, monitoring, etc.)')
    ops_parser.add_argument('--command', help='Main command to execute')
    ops_parser.add_argument('--precheck', help='Pre-check command')
    ops_parser.add_argument('--validation', help='Validation command')
    ops_parser.add_argument('--workdir', help='Working directory')
    ops_parser.add_argument('--timeout', type=int, help='Timeout in minutes')
    ops_parser.add_argument('--recurring', action='store_true', help='This is a recurring operation')
    
    # Workflow template subcommand
    workflow_parser = subparsers.add_parser('workflow', help='Create a workflow from a specific template')
    workflow_parser.add_argument('--type', dest='workflow_type', required=True, 
                                choices=['monday-board'], help='Type of workflow template')
    workflow_parser.add_argument('--board-id', help='Monday.com board ID (for monday-board workflows)')
    workflow_parser.add_argument('--board-name', help='Human-readable board name (for monday-board workflows)')
    workflow_parser.add_argument('--table-name', help='Target SQL table name (optional, will be auto-generated)')
    workflow_parser.add_argument('--frequency', choices=['hourly', 'daily', 'weekly'], 
                                help='Update frequency (default: daily)')
    workflow_parser.add_argument('--developer', help='Developer name for tracking')
    
    # List tasks subcommand
    list_parser = subparsers.add_parser('list', help='List existing tasks')
    
    args = parser.parse_args()
      # Fix: Check if subcommand was properly parsed (workaround for argparse issue)
    if hasattr(args, 'title') and not hasattr(args, 'project') and not hasattr(args, 'workflow_type'):
        # This means ops subcommand was used
        args.command = 'ops'
    elif hasattr(args, 'project'):
        # This means dev subcommand was used
        args.command = 'dev'
    elif hasattr(args, 'workflow_type'):
        # This means workflow subcommand was used
        args.command = 'workflow'
    elif len(sys.argv) > 1 and sys.argv[1] == 'list':
        args.command = 'list'
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'dev':
        create_dev_task(args)
    elif args.command == 'ops':
        create_ops_task(args)
    elif args.command == 'workflow':
        create_workflow_task(args)
    elif args.command == 'list':
        list_tasks()

if __name__ == '__main__':
    main()
