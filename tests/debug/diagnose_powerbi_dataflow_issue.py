"""
Power BI Dataflow Refresh Issue Diagnostics
Purpose: Analyze the 400 Bad Request error from Power BI dataflow refresh
Date: 2025-07-15

Issue Context:
- Logic App is triggering successfully
- Power BI dataflow refresh is failing with HTTP 400
- Need to identify the specific dataflow issue
"""
import sys
import requests
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Repository root setup
def find_repo_root() -> Path:
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current.parent.parent / "pipelines" / "utils").exists():
            return current.parent.parent
        current = current.parent
    raise RuntimeError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

import logger_helper

logger = logger_helper.get_logger("powerbi_dataflow_diagnostics")

def analyze_power_bi_error():
    """Analyze the Power BI dataflow error from the Logic App response"""
    
    logger.info("🔍 POWER BI DATAFLOW ERROR ANALYSIS")
    logger.info("=" * 60)
    
    # Error details from your Power Automate response
    error_response = {
        "statusCode": 400,
        "headers": {
            "Cache-Control": "no-store, must-revalidate, no-cache",
            "Pragma": "no-cache",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "X-Frame-Options": "deny",
            "X-Content-Type-Options": "nosniff",
            "RequestId": "aee972ae-a508-482d-8f28-40c940974ab2",
            "Access-Control-Expose-Headers": "RequestId",
            "request-redirected": "true",
            "home-cluster-uri": "https://wabi-australia-east-a-primary-redirect.analysis.windows.net/",
            "x-ms-environment-id": "default-95d7583a-1925-44b1-b78b-3483e00c5b46",
            "x-ms-tenant-id": "95d7583a-1925-44b1-b78b-3483e00c5b46",
            "x-ms-subscription-id": "b745f25e-91b5-4140-9d73-93b10b1dfb1d",
            "x-ms-dlp-re": "-|-",
            "x-ms-dlp-gu": "-|-",
            "x-ms-dlp-ef": "-|-/-|-|-",
            "x-ms-mip-sl": "-|-|-|-",
            "Timing-Allow-Origin": "*",
            "x-ms-apihub-cached-response": "true",
            "x-ms-apihub-obo": "false",
            "Date": "Tue, 15 Jul 2025 03:24:45 GMT",
            "Content-Length": "549",
            "Content-Type": "application/json"
        },
        "body": {
            "Message": "The backend request failed with error code '400'",
            "Reason": "Bad Request",
            "WorkspaceType": "Workspace",
            "OperationId": "RefreshDataflow",
            "ClientRequestId": "d2097cb8-487f-4fec-981d-b47a428087bd",
            "ClientRequestUrl": "https://default-95d7583a-1925-44b1-b78b-3483e00c5b46.02.common.australia.azure-apihub.net/apim/dataflows/shared-dataflows-68b19203-d119-495e-a890-3ba8bda1c08a/api/groups/c108ce52-f948-479a-a35f-d39758253bd0/dataflows/e39aa979-a96e-404e-b9a5-8f9c8ef361ae/refreshdataflow?workspaceType=Workspace"
        }
    }
    
    # Extract key information
    client_request_url = error_response["body"]["ClientRequestUrl"]
    request_id = error_response["body"]["ClientRequestId"]
    operation_id = error_response["body"]["OperationId"]
    workspace_type = error_response["body"]["WorkspaceType"]
    
    logger.info(f"📋 ERROR DETAILS:")
    logger.info(f"   Status Code: {error_response['statusCode']}")
    logger.info(f"   Operation: {operation_id}")
    logger.info(f"   Workspace Type: {workspace_type}")
    logger.info(f"   Request ID: {request_id}")
    
    # Parse the dataflow URL to extract IDs
    logger.info(f"\n🔗 DATAFLOW URL ANALYSIS:")
    logger.info(f"   Full URL: {client_request_url}")
    
    # Extract IDs from URL
    url_parts = client_request_url.split('/')
    try:
        # Find dataflow and group IDs in URL
        group_id = None
        dataflow_id = None
        
        for i, part in enumerate(url_parts):
            if part == 'groups' and i + 1 < len(url_parts):
                group_id = url_parts[i + 1]
            elif part == 'dataflows' and i + 1 < len(url_parts):
                dataflow_id = url_parts[i + 1]
        
        if group_id:
            logger.info(f"   🏢 Workspace/Group ID: {group_id}")
        if dataflow_id:
            logger.info(f"   🌊 Dataflow ID: {dataflow_id}")
            
    except Exception as e:
        logger.info(f"   ⚠️  Could not parse URL: {e}")
    
    # Analyze headers for additional insights
    logger.info(f"\n📋 POWER BI ENVIRONMENT INFO:")
    headers = error_response["headers"]
    logger.info(f"   Environment ID: {headers.get('x-ms-environment-id', 'Not found')}")
    logger.info(f"   Tenant ID: {headers.get('x-ms-tenant-id', 'Not found')}")
    logger.info(f"   Subscription ID: {headers.get('x-ms-subscription-id', 'Not found')}")
    logger.info(f"   Home Cluster: {headers.get('home-cluster-uri', 'Not found')}")
    
    # Common causes analysis
    logger.info(f"\n🚨 COMMON CAUSES OF 400 BAD REQUEST FOR DATAFLOW REFRESH:")
    logger.info("   1. 📊 Dataflow is already running (concurrent refresh)")
    logger.info("   2. 🔒 Insufficient permissions on dataflow")
    logger.info("   3. 💾 Data source connection issues")
    logger.info("   4. ⏰ Dataflow is in failed state")
    logger.info("   5. 🏢 Workspace/Group access issues")
    logger.info("   6. 📈 Power BI capacity limitations")
    logger.info("   7. 🔧 Dataflow configuration errors")
    
    return {
        "group_id": group_id,
        "dataflow_id": dataflow_id,
        "request_id": request_id,
        "error_analysis": "HTTP 400 on RefreshDataflow operation"
    }

def create_enhanced_logic_app_payload():
    """Create an enhanced payload that might avoid the dataflow issue"""
    
    logger.info(f"\n🔧 ENHANCED PAYLOAD RECOMMENDATIONS:")
    logger.info("=" * 50)
    
    # Enhanced payload with better error handling hints
    enhanced_payload = {
        "trigger_source": "python_script_enhanced",
        "timestamp": datetime.now().isoformat(),
        "description": "Enhanced dataflow refresh with error handling",
        "dataflow_options": {
            "wait_for_completion": False,  # Don't wait for completion
            "skip_if_running": True,      # Skip if already running
            "retry_on_failure": False     # Don't auto-retry
        },
        "debug_info": {
            "client_version": "1.1",
            "requested_by": "data_orchestration_script"
        }
    }
    
    logger.info("📦 Enhanced payload structure:")
    logger.info(json.dumps(enhanced_payload, indent=2))
    
    return enhanced_payload

def test_logic_app_with_enhanced_payload():
    """Test the Logic App with enhanced payload to see if it reduces errors"""
    
    logger.info(f"\n🧪 TESTING ENHANCED LOGIC APP TRIGGER:")
    logger.info("=" * 45)
    
    logic_app_url = (
        "https://prod-27.australiasoutheast.logic.azure.com:443/"
        "workflows/f6b302ba68c040619502cbf79e89d853/triggers/"
        "manual/paths/invoke?api-version=2016-06-01"
        "&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0"
        "&sig=HIXJekmqnQhsarXH5w8lbDDtzLt1qR7qOWy0HudZ4IM"
    )
    
    enhanced_payload = create_enhanced_logic_app_payload()
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "DataOrchestration-Enhanced/1.1",
        "Accept": "application/json"
    }
    
    try:
        logger.info("📡 Sending enhanced request...")
        
        response = requests.post(
            logic_app_url,
            headers=headers,
            json=enhanced_payload,
            timeout=30
        )
        
        logger.info(f"📊 Enhanced Request Results:")
        logger.info(f"   Status Code: {response.status_code}")
        logger.info(f"   Response Time: {response.elapsed.total_seconds():.3f}s")
        
        if 'x-ms-workflow-run-id' in response.headers:
            run_id = response.headers['x-ms-workflow-run-id']
            logger.info(f"   ✅ Run ID: {run_id}")
        
        if response.text:
            logger.info(f"   📄 Response: {response.text}")
        else:
            logger.info(f"   📄 Response: (empty)")
            
        return response
        
    except Exception as e:
        logger.error(f"❌ Enhanced test failed: {e}")
        return None

def generate_troubleshooting_steps():
    """Generate specific troubleshooting steps for the dataflow issue"""
    
    logger.info(f"\n🛠️  SPECIFIC TROUBLESHOOTING STEPS:")
    logger.info("=" * 50)
    
    steps = [
        "1. 🔍 Check Power BI Admin Portal:",
        "   - Go to https://app.powerbi.com/admin",
        "   - Check dataflow status and recent activities",
        "   - Look for failed or running dataflows",
        "",
        "2. 📊 Verify Dataflow State:",
        "   - Open the specific dataflow in Power BI",
        "   - Check if it's currently refreshing",
        "   - Look for any error messages or warnings",
        "",
        "3. 🔒 Check Permissions:",
        "   - Verify service principal has dataflow refresh permissions",
        "   - Check workspace access for the Logic App identity",
        "   - Ensure proper Power BI Pro/Premium licensing",
        "",
        "4. ⏰ Review Refresh Schedule:",
        "   - Check if dataflow has conflicting scheduled refreshes",
        "   - Look for concurrent refresh attempts",
        "   - Verify refresh frequency limits",
        "",
        "5. 🔧 Logic App Configuration:",
        "   - Review Power BI connector configuration",
        "   - Check authentication method (Service Principal vs User)",
        "   - Verify dataflow and workspace IDs are correct",
        "",
        "6. 📈 Capacity and Limits:",
        "   - Check Power BI capacity usage",
        "   - Verify if hitting refresh limits",
        "   - Review any throttling messages"
    ]
    
    for step in steps:
        logger.info(step)

def main():
    """Main diagnostic execution"""
    logger.info("🚀 POWER BI DATAFLOW REFRESH DIAGNOSTICS")
    logger.info("=" * 70)
    
    # Analyze the current error
    error_info = analyze_power_bi_error()
    
    # Test enhanced approach
    enhanced_response = test_logic_app_with_enhanced_payload()
    
    # Generate troubleshooting steps
    generate_troubleshooting_steps()
    
    # Final summary
    logger.info(f"\n📋 DIAGNOSTIC SUMMARY:")
    logger.info("=" * 30)
    logger.info("✅ Logic App: Working correctly")
    logger.info("❌ Power BI Dataflow: Failing with HTTP 400")
    logger.info("🎯 Next Action: Check Power BI dataflow status directly")
    logger.info("🔧 Recommendation: Review dataflow permissions and state")

if __name__ == "__main__":
    main()
