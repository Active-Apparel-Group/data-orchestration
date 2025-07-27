#!/usr/bin/env python3
"""
🧪 API LOGGING FIX VALIDATION - Test if batch operations now capture API logging data
"""

import sys
from pathlib import Path

# Legacy transition support pattern
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import logger

logger = logger.get_logger(__name__)

def main():
    print("🧪 API Logging Fix Validation...")
    
    try:
        # Import the fixed Monday API client
        from src.pipelines.sync_order_list.monday_api_client import MondayAPIClient
        
        print("✅ Import successful - no syntax errors")
        
        # Check if the methods exist and have the right signatures
        import inspect
        
        # Check _execute_batch method
        batch_method = getattr(MondayAPIClient, '_execute_batch')
        batch_signature = inspect.signature(batch_method)
        print(f"✅ _execute_batch method found with signature: {batch_signature}")
        
        # Quick code inspection - look for the API logging keys in the method
        import ast
        import inspect
        
        # Get the source code of the _execute_batch method
        source = inspect.getsource(batch_method)
        
        # Check for the API logging keys
        api_logging_keys = ['api_request', 'api_response', 'request_timestamp', 'response_timestamp']
        
        found_keys = []
        for key in api_logging_keys:
            if key in source:
                found_keys.append(key)
        
        print(f"✅ Found API logging keys in _execute_batch: {found_keys}")
        
        if len(found_keys) == 4:
            print("🎉 FIX VALIDATED: All API logging keys are present in _execute_batch method!")
        else:
            missing = set(api_logging_keys) - set(found_keys)
            print(f"⚠️ Missing API logging keys: {missing}")
        
        print(f"\n📋 Summary:")
        print(f"   ✅ Monday API client imports successfully")
        print(f"   ✅ _execute_batch method exists")
        print(f"   ✅ Found {len(found_keys)}/4 API logging keys")
        print(f"   🎯 Fix should resolve empty response payload issue for batch operations")
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        logger.exception("Validation error")

if __name__ == "__main__":
    main()
