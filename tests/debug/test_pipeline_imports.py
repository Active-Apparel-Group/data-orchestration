"""
Quick Pipeline Validation Test
Purpose: Basic validation that the pipeline can be imported and initialized
Author: Data Engineering Team
Date: July 10, 2025
"""

import sys
from pathlib import Path

def find_repo_root() -> Path:
    """Find repository root by looking for pipelines/utils folder"""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current.parent.parent / "pipelines" / "utils").exists():
            return current.parent.parent
        current = current.parent
    raise RuntimeError("Could not find repository root with utils/ folder")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))
sys.path.insert(0, str(repo_root / "pipelines" / "scripts" / "load_order_list"))

def test_pipeline_import():
    """Test that pipeline can be imported and basic functionality works"""
    try:
        print("🧪 Testing ORDER_LIST Pipeline Import...")
        
        # Test imports
        import logger_helper
        print("✅ logger_helper imported successfully")
        
        import db_helper as db
        print("✅ db_helper imported successfully")
        
        # Test transform import
        from order_list_transform import OrderListTransformer
        print("✅ OrderListTransformer imported successfully")
        
        # Test pipeline import
        from order_list_pipeline import OrderListPipeline
        print("✅ OrderListPipeline imported successfully")
        
        # Test pipeline initialization
        pipeline = OrderListPipeline()
        print("✅ OrderListPipeline initialized successfully")
        print(f"✅ Pipeline ID: {pipeline.pipeline_id}")
        
        # Test test framework import
        sys.path.insert(0, str(repo_root / "tests" / "end_to_end"))
        from test_order_list_complete_pipeline import OrderListPipelineTestFramework
        print("✅ OrderListPipelineTestFramework imported successfully")
        
        # Test test framework initialization
        test_framework = OrderListPipelineTestFramework()
        print("✅ Test framework initialized successfully")
        print(f"✅ Test ID: {test_framework.test_id}")
        
        print(f"\n🎉 ALL IMPORTS AND INITIALIZATIONS SUCCESSFUL!")
        print(f"📁 Repository Root: {repo_root}")
        print(f"🔧 Pipeline ready for execution")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def main():
    """Main test execution"""
    print("🚀 ORDER_LIST Pipeline Import Validation")
    print("=" * 50)
    
    success = test_pipeline_import()
    
    if success:
        print(f"\n✅ PIPELINE IMPORT VALIDATION: PASSED")
        print(f"🚀 Ready to run:")
        print(f"   python pipelines/scripts/load_order_list/order_list_pipeline.py --help")
        print(f"   python tests/end_to_end/test_order_list_complete_pipeline.py --help")
        return 0
    else:
        print(f"\n❌ PIPELINE IMPORT VALIDATION: FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
