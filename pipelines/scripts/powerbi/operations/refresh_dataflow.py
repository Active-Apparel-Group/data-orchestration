"""
Simple Dataflow Refresh Script  
Purpose: Replace order_list_dataflow_refresh.py with new Power BI API method
Location: pipelines/scripts/powerbi/refresh_dataflow.py

Usage:
    python pipelines/scripts/powerbi/refresh_dataflow.py                    # Default ORDER_LIST dataflow
    python pipelines/scripts/powerbi/refresh_dataflow.py --workspace-id XXX --dataflow-id YYY
    python pipelines/scripts/powerbi/refresh_dataflow.py --wait             # Wait for completion
"""
import sys
import argparse
from pathlib import Path

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
from powerbi_manager import PowerBIManager

def main():
    """Main function for dataflow refresh"""
    parser = argparse.ArgumentParser(description="Refresh Power BI dataflow")
    parser.add_argument('--dataflow', default='order_list_dataflow', help='Named dataflow from config')
    parser.add_argument('--workspace-id', help='Power BI workspace ID')
    parser.add_argument('--dataflow-id', help='Power BI dataflow ID')
    parser.add_argument('--wait', action='store_true', help='Wait for refresh completion')
    parser.add_argument('--config', default="pipelines/utils/powerbi_config.yaml", help="Configuration file")
    parser.add_argument('--profile', default="powerbi_primary", help="Token profile to use")
    
    args = parser.parse_args()
    
    # Initialize logger
    logger = logger_helper.get_logger(__name__)
    logger.info("🔄 Power BI Dataflow Refresh Starting")
    
    try:
        # Initialize Power BI manager
        powerbi_manager = PowerBIManager(args.config)
        
        # Get dataflow info
        if args.workspace_id and args.dataflow_id:
            # Use explicit IDs
            workspace_id = args.workspace_id
            dataflow_id = args.dataflow_id
            logger.info(f"Using explicit IDs: Workspace={workspace_id}, Dataflow={dataflow_id}")
        else:
            # Use named dataflow from config
            dataflow_config = powerbi_manager.config['priority_resources']['dataflows'].get(args.dataflow)
            if not dataflow_config:
                logger.error(f"Dataflow '{args.dataflow}' not found in configuration")
                return 1
            
            workspace_id = dataflow_config.get('workspace_id')
            dataflow_id = dataflow_config.get('dataflow_id')
            
            if workspace_id == "TBD" or dataflow_id == "TBD":
                logger.error(f"Dataflow '{args.dataflow}' not configured yet.")
                logger.info("Use --workspace-id and --dataflow-id arguments instead.")
                return 1
            
            logger.info(f"Using config dataflow: {args.dataflow}")
        
        # Perform refresh
        logger.info(f"Starting dataflow refresh...")
        result = powerbi_manager.refresh_dataflow(
            workspace_id=workspace_id,
            dataflow_id=dataflow_id,
            profile_name=args.profile,
            wait_for_completion=args.wait
        )
        
        # Display result
        if result['status'] == 'started':
            logger.info("✅ Dataflow refresh started successfully")
            if args.wait and result['status'] == 'completed':
                logger.info("✅ Dataflow refresh completed successfully")
                return 0
            elif args.wait:
                logger.error(f"❌ Dataflow refresh failed: {result.get('error', 'Unknown error')}")
                return 1
            else:
                logger.info("🔄 Refresh is running in background")
                return 0
        else:
            logger.error(f"❌ Failed to start dataflow refresh: {result.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Dataflow refresh failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
