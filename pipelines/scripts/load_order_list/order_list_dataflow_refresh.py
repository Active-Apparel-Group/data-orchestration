"""
Power Automate Dataflow Refresh Trigger with Business Hours Validation
Purpose: Trigger Power Automate dataflow refresh workflow with time restrictions
Location: pipelines/scripts/load_order_list/order_list_dataflow_refresh.py

Enhanced Features:
- Business hours validation (9am-5pm AEDT Brisbane)
- Daily refresh limit checking (8 per 24 hours)
- Comprehensive error handling for daily limit exceeded
"""
import sys
import requests
import os
from pathlib import Path
from datetime import datetime, time, timedelta
from typing import Optional, Dict, Any


# --- repo utils path setup (pipelines/utils pattern) -------------------------
def find_repo_root() -> Path:
    """Find repository root by looking for pipelines/utils folder"""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current.parent.parent / "pipelines" / "utils").exists():
            return current.parent.parent
        current = current.parent
    raise RuntimeError("Could not find repository root with pipelines/utils/ folder")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))  # pipelines/utils ONLY

try:
    from dotenv import load_dotenv
    # Load .env from repo root and .venv/.env if present
    load_dotenv(repo_root / ".env")
    load_dotenv(repo_root / ".venv" / ".env")
except ImportError:
    pass

# Import helpers (from pipelines/utils)
import db_helper as db
import logger_helper

# Create logger instance for Kestra compatibility
logger = logger_helper.get_logger("order_list_dataflow_refresh")

# Load configuration from centralized config
config = db.load_config()

def is_business_hours() -> bool:
    """
    Check if current time is within business hours (9am-5pm AEDT Brisbane)
    
    Returns:
        bool: True if within business hours, False otherwise
    """
    try:
        # Brisbane timezone - use pytz for better compatibility
        import pytz
        brisbane_tz = pytz.timezone('Australia/Brisbane')
        current_time = datetime.now(brisbane_tz)
        
        # Business hours: 9 AM to 5 PM Brisbane time
        business_start = time(9, 0)  # 9:00 AM
        business_end = time(17, 0)   # 5:00 PM
        
        current_time_only = current_time.time()
        
        # Check if current time is within business hours
        is_within_hours = business_start <= current_time_only <= business_end
        
        logger.info(f"[TIME_CHECK] Current Brisbane time: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info(f"[BUSINESS_HOURS] 9:00 AM - 5:00 PM Brisbane time")
        logger.info(f"[STATUS] Within business hours: {is_within_hours}")
        
        if not is_within_hours:
            logger.warning("[OUTSIDE_HOURS] Current time is outside business hours")
            logger.warning("[SCHEDULE] Dataflow refreshes only allowed 9 AM - 5 PM Brisbane time")
            
            # Calculate next business hour
            if current_time_only < business_start:
                next_run = current_time.replace(hour=9, minute=0, second=0, microsecond=0)
                logger.info(f"[NEXT_RUN] Next allowed run: {next_run.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            else:
                next_run = (current_time + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
                logger.info(f"[NEXT_RUN] Next allowed run: Tomorrow at 9:00 AM Brisbane time")
        
        return is_within_hours
        
    except Exception as e:
        logger.error(f"[TIME_CHECK_ERROR] Failed to check business hours: {e}")
        logger.warning("[FALLBACK] Allowing execution due to time check failure")
        return True  # Allow execution if time check fails

def check_daily_refresh_limit() -> Dict[str, Any]:
    """
    Check daily refresh limit status (8 per 24 hours)
    
    Note: Without database logging, this returns a basic status structure.
    Actual refresh count must be monitored through Power BI service directly.
    
    Returns:
        Dict with limit status and recommendations
    """
    # Since we don't have database logging, return a conservative status
    # that allows execution but provides guidance about the 8 refresh limit
    limit_status = {
        'refreshes_today': 0,  # Unknown without database logging
        'daily_limit': 8,
        'remaining_refreshes': 8,  # Assume full capacity
        'at_limit': False,
        'approaching_limit': False,
        'safe_to_refresh': True,
        'note': 'Refresh count tracking disabled - monitor via Power BI service'
    }
    
    logger.info("[LIMIT_CHECK] Daily refresh usage: Unknown (no database logging)")
    logger.info("[LIMIT_INFO] Power BI allows maximum 8 dataflow refreshes per 24 hours")
    logger.info("[MONITORING] Monitor actual usage via Power BI service directly")
    logger.info("[LIMIT_OK] Execution allowed - check Power BI for actual usage")
    
    return limit_status

def trigger_workflow(payload: Optional[Dict[str, Any]] = None) -> requests.Response:
    """
    Trigger Gen1 dataflow refresh via Power Automate SAS URL
    Enhanced with simplified approach from successful test_power_automate_sas.py
    
    Args:
        payload: Optional JSON payload for the workflow
        
    Returns:
        requests.Response: Response from the Logic App
    """
    # Power Automate SAS URL (same as successful test)
    logic_app_url = (
        "https://prod-27.australiasoutheast.logic.azure.com:443/"
        "workflows/f6b302ba68c040619502cbf79e89d853/triggers/"
        "manual/paths/invoke?api-version=2016-06-01"
        "&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0"
        "&sig=HIXJekmqnQhsarXH5w8lbDDtzLt1qR7qOWy0HudZ4IM"
    )
    
    # Simplified headers (based on working test)
    headers = {"Content-Type": "application/json"}
    
    # Enhanced payload based on successful test approach
    if payload is None:
        payload = {
            "trigger_type": "Gen1_Dataflow_Refresh",
            "dataflow_name": "Master Order List",
            "workspace": "Data Admin", 
            "timestamp": datetime.now().isoformat(),
            "source": "ORDER_LIST_pipeline"
        }
    
    logger.info("[TRIGGER] Starting Gen1 dataflow refresh...")
    logger.info(f"[TARGET] Dataflow: Master Order List in Data Admin workspace")
    logger.info(f"[METHOD] Power Automate SAS URL (simplified authentication)")
    
    try:
        # Make the POST request (same as successful test)
        response = requests.post(
            logic_app_url, 
            headers=headers,
            json=payload,
            timeout=30
        )
        
        # Enhanced success detection with specific error handling
        if response.status_code in [200, 202]:
            logger.info("[SUCCESS] Gen1 dataflow refresh triggered successfully")
            logger.info(f"[STATUS] HTTP {response.status_code} - Flow execution started")
            
            # Check for workflow run ID
            if 'x-ms-workflow-run-id' in response.headers:
                run_id = response.headers['x-ms-workflow-run-id']
                logger.info(f"[RUN_ID] Workflow Run ID: {run_id}")
                
        elif response.status_code == 400:
            logger.warning("[WARNING] Power Automate triggered but dataflow refresh may have encountered issues")
            logger.warning("[COMMON_CAUSES] This could indicate:")
            logger.warning("   • Daily refresh limit exceeded (8 refreshes per 24 hours)")
            logger.warning("   • Dataflow configuration or data source issues")
            logger.warning("   • Authentication or permission problems")
            logger.warning("[ACTION] Check Power BI service for specific error details")
            
            # Log response details for troubleshooting
            if response.text:
                logger.warning(f"[RESPONSE_DETAILS] {response.text[:300]}")
                
        else:
            logger.error(f"[FAILED] Failed to trigger dataflow refresh: HTTP {response.status_code}")
            if response.text:
                logger.error(f"[ERROR_DETAILS] {response.text[:200]}")
        
        return response
        
    except requests.exceptions.Timeout:
        logger.error("[TIMEOUT] Request timed out - flow may still be processing")
        raise
        
    except requests.exceptions.RequestException as e:
        logger.error(f"[NETWORK_ERROR] {e}")
        raise
        
    except Exception as e:
        logger.error(f"[UNEXPECTED_ERROR] {e}")
        raise

def main(custom_payload: Optional[Dict[str, Any]] = None, force_execution: bool = False):
    """
    Main execution flow for Power Automate workflow trigger with business hours validation
    
    Args:
        custom_payload: Optional custom payload for the workflow
        force_execution: Force execution outside business hours (for emergency use)
    """
    logger.info("=" * 60)
    logger.info("POWER AUTOMATE WORKFLOW TRIGGER (BUSINESS HOURS)")
    logger.info("=" * 60)
    
    try:
        # Step 1: Business hours validation (unless forced)
        if not force_execution:
            logger.info("\n[TIME] BUSINESS HOURS VALIDATION")
            logger.info("-" * 40)
            
            if not is_business_hours():
                logger.error("[BLOCKED] Execution blocked - outside business hours")
                logger.error("[SCHEDULE] Dataflow refreshes only allowed 9:00 AM - 5:00 PM Brisbane time")
                logger.error("[OVERRIDE] Use force_execution=True for emergency executions")
                logger.error("[RECOMMENDED] Schedule this script to run only during business hours")
                
                # Return early with specific exit code
                logger.info("\n" + "="*60)
                logger.info("EXECUTION BLOCKED - OUTSIDE BUSINESS HOURS")
                logger.info("="*60)
                return None
        else:
            logger.warning("[FORCED] Execution forced outside business hours")
            logger.warning("[EMERGENCY] This should only be used for urgent situations")
        
        # Step 2: Daily refresh limit check
        logger.info("\n[DATA] DAILY REFRESH LIMIT CHECK")
        logger.info("-" * 40)
        
        limit_status = check_daily_refresh_limit()
        
        if limit_status['at_limit'] and not force_execution:
            logger.error("[BLOCKED] Daily refresh limit exceeded (8/8)")
            logger.error("[POWER_BI] Power BI allows maximum 8 dataflow refreshes per 24 hours")
            logger.error("[RESET] Limit resets at midnight UTC")
            logger.error("[OVERRIDE] Use force_execution=True to attempt anyway (may fail)")
            
            # Return early with specific status
            logger.info("\n" + "="*60)
            logger.info("EXECUTION BLOCKED - DAILY LIMIT EXCEEDED")
            logger.info("="*60)
            return None
            
        elif limit_status['approaching_limit']:
            logger.warning(f"[WARNING] Approaching daily limit ({limit_status['refreshes_today']}/8)")
            logger.warning(f"[REMAINING] {limit_status['remaining_refreshes']} refreshes remaining today")
        
        # Step 3: Verify database connection (optional for logging)
        logger.info("\n[CONN] DATABASE CONNECTION VALIDATION")
        logger.info("-" * 40)
        
        db_config = db.get_database_config()
        logger.info("[DATABASES] Available database configurations:")
        for db_key, db_info in db_config.items():
            host = db_info.get("host", "N/A")
            database = db_info.get("database", "N/A")
            logger.info(f"  * {db_key.upper()}: {host} -> {database}")

        # Test database connection (optional)
        if "orders" in db_config:
            test_query = "SELECT 1 AS connection_test"
            test_result = db.run_query(test_query, "orders")
            logger.info("[SUCCESS] Database connection test successful!")
        else:
            logger.warning("[WARNING] 'orders' database not configured - logging may be limited")
        
        # Step 4: Trigger workflow using access key
        logger.info("\n[EXEC] DATAFLOW REFRESH EXECUTION")
        logger.info("-" * 40)
        
        response = trigger_workflow(custom_payload)
        
        # Step 5: Handle response with enhanced error handling
        status_code = response.status_code
        response_text = response.text
        
        logger.info("\n" + "="*60)
        logger.info("GEN1 DATAFLOW REFRESH RESULTS")
        logger.info("="*60)
        
        if status_code in (200, 202):
            logger.info("[SUCCESS] Gen1 dataflow refresh triggered")
            logger.info(f"[STATUS] HTTP {status_code}")
            logger.info("[DATAFLOW] Master Order List refresh initiated")
            
            # Extract workflow run ID for tracking
            workflow_run_id = None
            if hasattr(response, 'headers') and 'x-ms-workflow-run-id' in response.headers:
                workflow_run_id = response.headers['x-ms-workflow-run-id']
                logger.info(f"[RUN_ID] {workflow_run_id}")
            
        else:
            logger.error(f"[FAILED] HTTP {status_code}")
            if response_text:
                logger.error(f"[ERROR] {response_text[:200]}")
        
        logger.info("\n" + "="*60)
        logger.info("ORDER_LIST DATAFLOW REFRESH COMPLETE")
        logger.info("="*60)
        
        return response
        
    except Exception as e:
        logger.error(f"[FAILED] Workflow trigger failed: {e}")
        logger.error("\n[TROUBLESHOOTING] Troubleshooting tips:")
        logger.error("  * Check Logic App access key validity")
        logger.error("  * Verify Logic App URL and permissions")
        logger.error("  * Check network connectivity to Azure")
        logger.error("  * Review Azure Logic App logs for details")
        
        raise

if __name__ == "__main__":
    # Enhanced payload based on successful test approach
    custom_payload = {
        "trigger_type": "Gen1_Dataflow_Refresh",
        "dataflow_name": "Master Order List",
        "workspace": "Data Admin",
        "trigger_source": "direct_script_execution",
        "timestamp": datetime.now().isoformat(),
        "environment": logger_helper.get_environment_info()
    }
    
    main(custom_payload)
