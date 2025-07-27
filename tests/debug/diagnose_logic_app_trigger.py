"""
Enhanced Power Automate Logic App Diagnostics
Purpose: Debug Logic App trigger issues with detailed response analysis
Date: 2025-07-15
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

logger = logger_helper.get_logger("logic_app_diagnostics")

def diagnose_logic_app_trigger():
    """Enhanced Logic App trigger with detailed diagnostics"""
    
    # Your current Logic App URL
    logic_app_url = (
        "https://prod-27.australiasoutheast.logic.azure.com:443/"
        "workflows/f6b302ba68c040619502cbf79e89d853/triggers/"
        "manual/paths/invoke?api-version=2016-06-01"
        "&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0"
        "&sig=HIXJekmqnQhsarXH5w8lbDDtzLt1qR7qOWy0HudZ4IM"
    )
    
    # Enhanced headers for better diagnostics
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "DataOrchestration-Diagnostics/1.0",
        "Accept": "application/json",
        "x-ms-client-request-id": f"diag-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    }
    
    # Simple test payload
    payload = {
        "trigger_source": "diagnostics_test",
        "timestamp": datetime.now().isoformat(),
        "test_message": "Logic App trigger diagnostics",
        "debug_mode": True
    }
    
    logger.info("🔍 LOGIC APP DIAGNOSTICS")
    logger.info("=" * 50)
    logger.info(f"Target URL: {logic_app_url}")
    logger.info(f"Headers: {json.dumps(headers, indent=2)}")
    logger.info(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        logger.info("\n📡 Sending request...")
        
        # Make request with verbose logging
        response = requests.post(
            logic_app_url,
            headers=headers,
            json=payload,
            timeout=60  # Longer timeout for diagnostics
        )
        
        # Detailed response analysis
        logger.info(f"\n📊 RESPONSE ANALYSIS")
        logger.info("=" * 30)
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Status Text: {response.reason}")
        logger.info(f"Response Time: {response.elapsed.total_seconds():.3f} seconds")
        logger.info(f"Response Size: {len(response.content)} bytes")
        
        # Headers analysis
        logger.info(f"\n📋 RESPONSE HEADERS:")
        for header, value in response.headers.items():
            logger.info(f"  {header}: {value}")
        
        # Content analysis
        logger.info(f"\n📄 RESPONSE CONTENT:")
        if response.text:
            logger.info(f"Raw text: {response.text}")
            try:
                json_response = response.json()
                logger.info(f"JSON parsed: {json.dumps(json_response, indent=2)}")
            except:
                logger.info("Response is not valid JSON")
        else:
            logger.info("⚠️  EMPTY RESPONSE BODY")
        
        # Status code interpretation
        logger.info(f"\n🔍 STATUS CODE ANALYSIS:")
        if response.status_code == 200:
            logger.info("✅ 200 OK - Request successful and completed")
        elif response.status_code == 202:
            logger.info("⏳ 202 Accepted - Request accepted, processing asynchronously")
            logger.info("   This usually means the Logic App received the trigger")
            logger.info("   but the workflow may still be running or queued")
        elif response.status_code == 400:
            logger.info("❌ 400 Bad Request - Invalid request format")
        elif response.status_code == 401:
            logger.info("❌ 401 Unauthorized - Authentication failed")
        elif response.status_code == 403:
            logger.info("❌ 403 Forbidden - Access denied")
        elif response.status_code == 404:
            logger.info("❌ 404 Not Found - Logic App or trigger not found")
        else:
            logger.info(f"❓ {response.status_code} - Unexpected status code")
        
        # Logic App specific diagnostics
        logger.info(f"\n🧩 LOGIC APP DIAGNOSTICS:")
        
        # Check for Logic App specific headers
        if 'x-ms-workflow-run-id' in response.headers:
            run_id = response.headers['x-ms-workflow-run-id']
            logger.info(f"✅ Workflow Run ID: {run_id}")
            logger.info(f"   This indicates the Logic App was triggered successfully")
        else:
            logger.info("⚠️  No x-ms-workflow-run-id header found")
            logger.info("   This might indicate the trigger didn't start a run")
        
        if 'x-ms-request-id' in response.headers:
            request_id = response.headers['x-ms-request-id']
            logger.info(f"📋 Request ID: {request_id}")
        
        # Check for error indicators
        if response.status_code == 202 and not response.text:
            logger.info("\n⚠️  POTENTIAL ISSUE DETECTED:")
            logger.info("   Status 202 with empty response might indicate:")
            logger.info("   1. Logic App is disabled")
            logger.info("   2. Trigger conditions not met")
            logger.info("   3. Logic App has no actions configured")
            logger.info("   4. Access key permissions insufficient")
        
        return response
        
    except requests.exceptions.Timeout:
        logger.error("⏰ Request timed out after 60 seconds")
    except requests.exceptions.ConnectionError:
        logger.error("🌐 Connection error - check network connectivity")
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
    
    return None

def check_alternative_trigger_methods():
    """Test alternative trigger approaches"""
    
    logger.info("\n🔄 TESTING ALTERNATIVE METHODS")
    logger.info("=" * 40)
    
    # Method 1: Minimal payload
    logger.info("1. Testing with minimal payload...")
    minimal_url = (
        "https://prod-27.australiasoutheast.logic.azure.com:443/"
        "workflows/f6b302ba68c040619502cbf79e89d853/triggers/"
        "manual/paths/invoke?api-version=2016-06-01"
        "&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0"
        "&sig=HIXJekmqnQhsarXH5w8lbDDtzLt1qR7qOWy0HudZ4IM"
    )
    
    try:
        minimal_response = requests.post(
            minimal_url,
            headers={"Content-Type": "application/json"},
            json={},  # Empty JSON object
            timeout=30
        )
        logger.info(f"   Minimal payload result: {minimal_response.status_code}")
        if minimal_response.text:
            logger.info(f"   Response: {minimal_response.text}")
    except Exception as e:
        logger.info(f"   Minimal payload failed: {e}")
    
    # Method 2: GET request to check if endpoint exists
    logger.info("\n2. Testing endpoint accessibility with GET...")
    try:
        get_response = requests.get(minimal_url, timeout=10)
        logger.info(f"   GET request result: {get_response.status_code}")
        logger.info(f"   This should return 405 Method Not Allowed if endpoint exists")
    except Exception as e:
        logger.info(f"   GET request failed: {e}")

def main():
    """Main diagnostic execution"""
    logger.info("🚀 POWER AUTOMATE LOGIC APP DIAGNOSTICS")
    logger.info("=" * 60)
    
    # Run primary diagnostics
    response = diagnose_logic_app_trigger()
    
    # Run alternative tests
    check_alternative_trigger_methods()
    
    # Final recommendations
    logger.info("\n💡 TROUBLESHOOTING RECOMMENDATIONS:")
    logger.info("=" * 40)
    logger.info("1. Check Azure Logic App portal for recent runs")
    logger.info("2. Verify Logic App is enabled and not suspended")
    logger.info("3. Check if trigger has conditions that might prevent execution")
    logger.info("4. Verify the SAS token hasn't expired")
    logger.info("5. Check Logic App consumption limits")
    logger.info("6. Review Logic App definition for required parameters")
    
    if response and response.status_code == 202:
        logger.info("\n✅ Logic App appears to be receiving requests successfully")
        logger.info("   The issue might be in the Logic App configuration or conditions")

if __name__ == "__main__":
    main()
