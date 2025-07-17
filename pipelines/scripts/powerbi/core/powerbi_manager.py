"""
Universal Power BI Manager Script
Purpose: Unified Power BI operations for dataflows, datasets, reports, and datamarts
Location: pipelines/scripts/powerbi/powerbi_manager.py

Usage:
    # Load tokens
    python pipelines/scripts/powerbi/powerbi_manager.py load-tokens
    
    # Refresh dataflow (replace order_list_dataflow_refresh.py)
    python pipelines/scripts/powerbi/powerbi_manager.py refresh-dataflow --dataflow order_list_dataflow
    python pipelines/scripts/powerbi/powerbi_manager.py refresh-dataflow --workspace-id XXX --dataflow-id YYY
    
    # Trigger Power Automate workflow
    python pipelines/scripts/powerbi/powerbi_manager.py trigger-workflow --workflow order_list_refresh
    
    # Discover resources
    python pipelines/scripts/powerbi/powerbi_manager.py discover --workspaces
    python pipelines/scripts/powerbi/powerbi_manager.py discover --dataflows --workspace-id XXX
"""
import sys, os
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Fallback: manually load .env file
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# Standard import pattern
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "pipelines" / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

# Import project utilities
import logger_helper
from token_manager import UniversalTokenManager
from powerbi_manager import PowerBIManager

def handle_load_tokens(args):
    """Handle token loading operations"""
    logger = logger_helper.get_logger(__name__)
    logger.info("🔑 Loading Power BI tokens...")
    
    token_manager = UniversalTokenManager(args.config)
    
    if args.profile:
        tokens = {args.profile: token_manager.get_token(args.profile, args.refresh)}
    else:
        tokens = token_manager.get_all_tokens(args.refresh)
    
    # Display results
    for profile_name, token_info in tokens.items():
        if 'error' in token_info:
            logger.error(f"❌ {profile_name}: {token_info['error']}")
        else:
            logger.info(f"✅ {profile_name}: Token loaded successfully")
    
    return 0 if all('error' not in t for t in tokens.values()) else 1

def handle_refresh_dataflow(args):
    """Handle dataflow refresh operations"""
    logger = logger_helper.get_logger(__name__)
    logger.info("🔄 Refreshing Power BI dataflow...")
    
    powerbi_manager = PowerBIManager(args.config)
    
    # Get dataflow info
    if args.dataflow:
        # Use named dataflow from config
        dataflow_config = powerbi_manager.config['priority_resources']['dataflows'].get(args.dataflow)
        if not dataflow_config:
            logger.error(f"Dataflow '{args.dataflow}' not found in configuration")
            return 1
        
        workspace_id = dataflow_config.get('workspace_id')
        dataflow_id = dataflow_config.get('dataflow_id')
        
        if workspace_id == "TBD" or dataflow_id == "TBD":
            logger.error(f"Dataflow '{args.dataflow}' not configured yet. Use --workspace-id and --dataflow-id instead.")
            return 1
            
    elif args.workspace_id and args.dataflow_id:
        # Use explicit IDs
        workspace_id = args.workspace_id
        dataflow_id = args.dataflow_id
    else:
        logger.error("Must specify either --dataflow NAME or --workspace-id + --dataflow-id")
        return 1
    
    # Perform refresh
    result = powerbi_manager.refresh_dataflow(
        workspace_id=workspace_id,
        dataflow_id=dataflow_id,
        profile_name=args.profile,
        wait_for_completion=args.wait
    )
    
    # Display result
    if result['status'] == 'started':
        logger.info(f"✅ Dataflow refresh started successfully")
        if args.wait:
            if result['status'] == 'completed':
                logger.info("✅ Dataflow refresh completed successfully")
            else:
                logger.error(f"❌ Dataflow refresh failed: {result.get('error', 'Unknown error')}")
                return 1
    else:
        logger.error(f"❌ Failed to start dataflow refresh: {result.get('error', 'Unknown error')}")
        return 1
    
    return 0

def handle_trigger_workflow(args):
    """Handle Power Automate workflow triggers"""
    logger = logger_helper.get_logger(__name__)
    logger.info("🚀 Triggering Power Automate workflow...")
    
    powerbi_manager = PowerBIManager(args.config)
    
    # Parse payload if provided
    payload = None
    if args.payload:
        try:
            payload = json.loads(args.payload)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON payload: {e}")
            return 1
    
    # Trigger workflow
    result = powerbi_manager.trigger_power_automate_workflow(
        workflow_name=args.workflow,
        payload=payload
    )
    
    # Display result
    if result['status'] == 'success':
        logger.info(f"✅ Workflow '{args.workflow}' triggered successfully")
    else:
        logger.error(f"❌ Workflow trigger failed: {result.get('error', 'Unknown error')}")
        return 1
    
    return 0

def handle_discover(args):
    """Handle resource discovery operations"""
    logger = logger_helper.get_logger(__name__)
    logger.info("Discovering Power BI resources...")
    
    powerbi_manager = PowerBIManager(args.config)
    
    if args.workspaces:
        # Discover workspaces
        workspaces = powerbi_manager.discover_workspaces(args.profile)
        
        if workspaces:
            logger.info(f"\n📁 Found {len(workspaces)} workspaces:")
            for workspace in workspaces:
                logger.info(f"  • {workspace['name']} (ID: {workspace['id']})")
        else:
            logger.warning("No workspaces found or access denied")
            
    elif args.dataflows:
        # Discover dataflows
        if not args.workspace_id:
            logger.error("--workspace-id required when discovering dataflows")
            return 1
            
        dataflows = powerbi_manager.discover_dataflows(args.workspace_id, args.profile)
        
        if dataflows:
            logger.info(f"\n💧 Found {len(dataflows)} dataflows:")
            for dataflow in dataflows:
                logger.info(f"  • {dataflow['name']} (ID: {dataflow['objectId']})")
        else:
            logger.warning("No dataflows found in workspace")
    
    return 0

def main():
    """Main function with command-line interface"""
    parser = argparse.ArgumentParser(description="Universal Power BI Manager")
    parser.add_argument('--config', default="pipelines/utils/powerbi_config.yaml", help="Configuration file")
    parser.add_argument('--profile', default="powerbi_primary", help="Token profile to use")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Load tokens command
    token_parser = subparsers.add_parser('load-tokens', help='Load authentication tokens')
    token_parser.add_argument('--refresh', action='store_true', help='Force refresh tokens')
    
    # Refresh dataflow command
    refresh_parser = subparsers.add_parser('refresh-dataflow', help='Refresh Power BI dataflow')
    refresh_parser.add_argument('--dataflow', help='Named dataflow from config (e.g., order_list_dataflow)')
    refresh_parser.add_argument('--workspace-id', help='Power BI workspace ID')
    refresh_parser.add_argument('--dataflow-id', help='Power BI dataflow ID')
    refresh_parser.add_argument('--wait', action='store_true', help='Wait for refresh completion')
    
    # Trigger workflow command
    workflow_parser = subparsers.add_parser('trigger-workflow', help='Trigger Power Automate workflow')
    workflow_parser.add_argument('--workflow', default='order_list_refresh', help='Workflow name from config')
    workflow_parser.add_argument('--payload', help='JSON payload for workflow')
    
    # Discover command
    discover_parser = subparsers.add_parser('discover', help='Discover Power BI resources')
    discover_parser.add_argument('--workspaces', action='store_true', help='Discover workspaces')
    discover_parser.add_argument('--dataflows', action='store_true', help='Discover dataflows')
    discover_parser.add_argument('--workspace-id', help='Workspace ID for dataflow discovery')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize logger
    logger = logger_helper.get_logger(__name__)
    logger.info(f"Universal Power BI Manager - {args.command}")
    
    try:
        # Route to appropriate handler
        if args.command == 'load-tokens':
            return handle_load_tokens(args)
        elif args.command == 'refresh-dataflow':
            return handle_refresh_dataflow(args)
        elif args.command == 'trigger-workflow':
            return handle_trigger_workflow(args)
        elif args.command == 'discover':
            return handle_discover(args)
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1
            
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
