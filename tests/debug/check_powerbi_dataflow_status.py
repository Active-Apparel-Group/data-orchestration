"""
Check Power BI Dataflow Status - Manual Verification Steps
Purpose: Guide for checking Power BI dataflow status directly in portal
"""

import sys
from pathlib import Path

# Add project root for imports
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

import logger_helper

def main():
    """Generate manual verification steps for Power BI dataflow"""
    logger = logger_helper.get_logger(__name__)
    
    logger.info("POWER BI DATAFLOW STATUS CHECK")
    logger.info("=====================================")
    
    # Key identifiers from the error
    workspace_id = "c108ce52-f948-479a-a35f-d39758253bd0"
    dataflow_id = "e39aa979-a96e-404e-b9a5-8f9c8ef361ae"
    request_id = "d2097cb8-487f-4fec-981d-b47a428087bd"
    
    logger.info(f"TARGET DATAFLOW INFO:")
    logger.info(f"   Workspace ID: {workspace_id}")
    logger.info(f"   Dataflow ID: {dataflow_id}")
    logger.info(f"   Failed Request ID: {request_id}")
    
    logger.info(f"\nMANUAL VERIFICATION STEPS:")
    logger.info("=" * 50)
    
    steps = [
        "1. POWER BI PORTAL CHECK:",
        "   - Go to https://app.powerbi.com/",
        "   - Navigate to the workspace containing the dataflow",
        "   - Look for dataflow refresh status and any error messages",
        "",
        "2. DATAFLOW REFRESH HISTORY:",
        "   - Open the specific dataflow",
        "   - Check 'Refresh history' tab",
        "   - Look for recent failed attempts with timestamps",
        "",
        "3. CONCURRENT REFRESH CHECK:",
        "   - Verify no dataflow refresh is currently running",
        "   - Check if any scheduled refreshes are active",
        "   - Look for 'Currently refreshing' status",
        "",
        "4. PERMISSIONS VERIFICATION:",
        "   - Check workspace access for service principal",
        "   - Verify dataflow-level permissions",
        "   - Confirm Power BI Pro/Premium licensing",
        "",
        "5. ADMIN PORTAL CHECK:",
        "   - Go to https://app.powerbi.com/admin",
        "   - Check 'Usage metrics' for any capacity issues",
        "   - Review 'Audit logs' for the failed request ID",
        "",
        "6. LOGIC APP DIAGNOSTICS:",
        "   - Open Azure Logic App in portal",
        "   - Check 'Run history' for detailed error messages",
        "   - Review Power BI connector action results",
        "",
        "7. TROUBLESHOOTING URLs:",
        f"   - Workspace: https://app.powerbi.com/groups/{workspace_id}",
        "   - Admin Portal: https://app.powerbi.com/admin",
        "   - Logic App Portal: Check Azure portal for your Logic App",
    ]
    
    for step in steps:
        logger.info(step)
    
    logger.info(f"\nQUICK RESOLUTION ATTEMPTS:")
    logger.info("=" * 40)
    
    resolutions = [
        "1. WAIT AND RETRY:",
        "   - Wait 5-10 minutes for any running refresh to complete",
        "   - Try manual dataflow refresh from Power BI portal",
        "",
        "2. PERMISSION FIX:",
        "   - Re-add service principal to workspace with 'Contributor' role",
        "   - Ensure proper dataflow refresh permissions",
        "",
        "3. LOGIC APP RECONFIGURATION:",
        "   - Test Power BI connector with different authentication",
        "   - Add error handling and retry logic to Logic App",
        "",
        "4. CAPACITY CHECK:",
        "   - Verify Power BI capacity isn't overloaded",
        "   - Check for any throttling or rate limiting",
    ]
    
    for resolution in resolutions:
        logger.info(resolution)
    
    logger.info(f"\nNEXT IMMEDIATE ACTION:")
    logger.info("=" * 35)
    logger.info("1. Check Power BI portal for dataflow status")
    logger.info("2. Look for any running or failed refreshes")
    logger.info("3. Verify permissions on workspace and dataflow")
    logger.info("4. Try manual refresh to test current state")

if __name__ == "__main__":
    main()
