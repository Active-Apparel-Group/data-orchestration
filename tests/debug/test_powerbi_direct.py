"""
Quick Test: Direct Power BI Dataflow Refresh
Purpose: Test the direct Power BI API approach with your actual IDs
"""
import sys
from pathlib import Path

# Standard import pattern
sys.path.insert(0, str(Path.cwd() / "pipelines" / "utils"))

import logger_helper
from token_manager import UniversalTokenManager
import requests

def test_powerbi_token():
    """Test that we can get a valid Power BI token"""
    logger = logger_helper.get_logger(__name__)
    
    logger.info("🔍 Testing Power BI Token Access")
    logger.info("=" * 40)
    
    try:
        token_manager = UniversalTokenManager()
        token_data = token_manager.get_token('powerbi_primary')
        
        if 'error' in token_data:
            logger.error(f"❌ Token error: {token_data['error']}")
            return False
        
        logger.info(f"✅ Token obtained: {token_data['source']}")
        logger.info(f"   Expires: {token_data['expires_at']}")
        
        # Test a simple API call (this should work regardless of workspace permissions)
        headers = {
            'Authorization': f"Bearer {token_data['access_token']}",
            'Content-Type': 'application/json'
        }
        
        # Try to get user info (should always work)
        test_url = "https://api.powerbi.com/v1.0/myorg"
        logger.info(f"🧪 Testing API access: {test_url}")
        
        response = requests.get(test_url, headers=headers, timeout=30)
        logger.info(f"📡 Response: HTTP {response.status_code}")
        
        if response.status_code == 200:
            logger.info("✅ Power BI API access confirmed!")
            return True
        else:
            logger.warning(f"⚠️ API response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_powerbi_token()
    print("\\n" + "="*50)
    if success:
        print("✅ READY: Power BI token working!")
        print("🎯 Next: Provide your workspace_id and dataflow_id")
        print("📝 Usage: python pipelines/scripts/powerbi/refresh_dataflow_direct.py --workspace-id YOUR_ID --dataflow-id YOUR_ID")
    else:
        print("❌ ISSUE: Power BI token not working")
        print("🔧 Check: Azure app registration permissions")
    print("="*50)
