#!/usr/bin/env python3
"""
Test script for Delta Sync V3 - GREYSON Pilot

This script tests the GREYSON PO 4755 pilot case mentioned in the requirements.
Run this to validate the core functionality works before full implementation.

Usage:
    python test_greyson_pilot.py
"""

import sys
from pathlib import Path

# For now, we'll handle import errors gracefully since utils may not be accessible
try:
    # Add utils to path
    def find_repo_root():
        current = Path(__file__).parent
        while current != current.parent:
            if (current / "utils").exists():
                return current
            current = current.parent
        raise FileNotFoundError("Could not find repository root")

    repo_root = find_repo_root()
    sys.path.insert(0, str(repo_root / "utils"))
    
    # Import our modules
    from delta_sync_main import DeltaSyncOrchestrator
    
    def test_greyson_pilot():
        """Test the GREYSON PO 4755 pilot case"""
        
        print("🧪 Testing GREYSON Pilot Case")
        print("=" * 50)
        
        # Create orchestrator in TEST mode
        orchestrator = DeltaSyncOrchestrator(mode="TEST")
        
        # Run with GREYSON filter and small limit
        results = orchestrator.run_delta_sync(
            customer_filter="GREYSON",
            limit=10
        )
        
        print("\n✅ Pilot test results:")
        print(f"   📊 Total processed: {results['total_processed']}")
        print(f"   👥 Customer batches: {results['customer_batches']}")
        print(f"   ⚡ Mode: {results['mode']}")
        
        return results['success']
    
    def test_individual_modules():
        """Test individual modules"""
        
        print("\n🔧 Testing Individual Modules")
        print("=" * 50)
        
        # Test UUID Manager
        try:
            from uuid_manager import UUIDManager
            uuid_mgr = UUIDManager()
            test_uuid = uuid_mgr.generate_test_uuid()
            print(f"✅ UUID Manager: Generated test UUID {test_uuid}")
        except Exception as e:
            print(f"❌ UUID Manager: {str(e)}")
        
        # Test Change Detector
        try:
            from change_detector import ChangeDetector
            detector = ChangeDetector()
            print("✅ Change Detector: Module loaded successfully")
        except Exception as e:
            print(f"❌ Change Detector: {str(e)}")
        
        # Test Customer Batcher
        try:
            from customer_batcher import CustomerBatcher
            batcher = CustomerBatcher()
            print("✅ Customer Batcher: Module loaded successfully")
        except Exception as e:
            print(f"❌ Customer Batcher: {str(e)}")
        
        # Test Staging Processor
        try:
            from staging_processor import StagingProcessor
            processor = StagingProcessor()
            print("✅ Staging Processor: Module loaded successfully")
        except Exception as e:
            print(f"❌ Staging Processor: {str(e)}")
    
    if __name__ == "__main__":
        print("🚀 GREYSON Pilot Test Suite")
        print("=" * 60)
        
        # Test individual modules first
        test_individual_modules()
        
        # Then test full workflow (if modules work)
        try:
            success = test_greyson_pilot()
            
            if success:
                print("\n🎉 GREYSON pilot test PASSED!")
                print("   Ready to proceed with full implementation")
            else:
                print("\n⚠️  GREYSON pilot test had issues")
                print("   Check logs and fix before proceeding")
                
        except Exception as e:
            print(f"\n💥 GREYSON pilot test FAILED: {str(e)}")
            print("   Fix issues before proceeding with implementation")

except ImportError as e:
    print(f"⚠️  Import Error: {str(e)}")
    print("\n🔧 Setup Required:")
    print("   1. Ensure utils/db_helper.py and utils/logger_helper.py exist")
    print("   2. Set up database connections in utils/config.yaml")
    print("   3. Install required packages: pandas, pyodbc, etc.")
    print("\n📋 For now, you can:")
    print("   - Review the module structure created")
    print("   - Set up database connections")
    print("   - Install dependencies")
    print("   - Come back and run this test")
    
except Exception as e:
    print(f"💥 Unexpected error: {str(e)}")
    print("   Check the setup and try again")
