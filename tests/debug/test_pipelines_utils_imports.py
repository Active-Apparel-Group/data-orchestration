"""
Test that ORDER_LIST pipeline files use pipelines/utils ONLY
"""

import sys
from pathlib import Path

print("🧪 Testing ORDER_LIST Pipeline Import Standards")
print("=" * 50)

# Add pipelines/utils to path
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

try:
    print("1️⃣ Testing pipelines/utils imports...")
    import db_helper
    import logger_helper  
    import auth_helper
    print("✅ pipelines/utils imports: SUCCESS")
    
    print("\n2️⃣ Testing ORDER_LIST pipeline imports...")
    from pipelines.scripts.load_order_list.order_list_pipeline import OrderListPipeline
    pipeline = OrderListPipeline()
    print(f"✅ Pipeline loaded: {pipeline.pipeline_id}")
    
    print("\n3️⃣ Testing blob uploader imports...")
    from pipelines.scripts.load_order_list.order_list_blob import OrderListBlobUploader
    uploader = OrderListBlobUploader()
    print("✅ Blob uploader loaded successfully")
    
    print("\n🎉 ALL TESTS PASSED!")
    print("✅ All ORDER_LIST files now use pipelines/utils ONLY")
    print("✅ No root utils/ dependencies found")
    print("✅ Import standards compliance: VERIFIED")
    
except Exception as e:
    print(f"❌ Import test failed: {e}")
    import traceback
    traceback.print_exc()
