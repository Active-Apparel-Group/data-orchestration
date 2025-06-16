"""
Minimal test for staging workflow
Tests the complete pipeline with a single customer
"""

import sys
import os
from pathlib import Path

# Add src to path (go up to workspace root, then to src)
workspace_root = Path(__file__).parent.parent
src_path = workspace_root / 'src'
sys.path.insert(0, str(src_path))

def test_single_customer():
    """Test workflow with a single customer"""
    
    print("🧪 Testing Monday.com Staging Workflow")
    print("=" * 50)
    
    try:
        # Import after path setup
        from order_sync_v2 import get_db_connection_string, setup_logging
        from order_staging.batch_processor import BatchProcessor
        
        # Setup logging
        logger = setup_logging()
        
        # Get database connection
        connection_string = get_db_connection_string()
        
        # Initialize batch processor
        processor = BatchProcessor(connection_string)
        
        # Test connections
        print("1. Testing connections...")
        connection_results = processor.test_connections()
        
        for service, success in connection_results.items():
            status = "✅" if success else "❌"
            print(f"   {status} {service}")
        
        if not all(connection_results.values()):
            print("❌ Connection tests failed - cannot proceed")
            return False
        
        # Get customers with new orders
        print("\n2. Finding customers with new orders...")
        customers = processor.get_customers_with_new_orders()
        
        if not customers:
            print("ℹ️  No customers with new orders found")
            return True
        
        print(f"   Found {len(customers)} customers: {customers[:3]}...")  # Show first 3
        
        # Test with first customer only
        test_customer = customers[0]
        print(f"\n3. Testing with customer: {test_customer}")
        
        # Process single customer batch
        result = processor.process_customer_batch(test_customer)
        
        # Print results
        print(f"\n📊 Test Results:")
        print(f"   Customer: {result['customer_name']}")
        print(f"   Status: {result['status']}")
        print(f"   Orders Loaded: {result['orders_loaded']}")
        print(f"   Items Created: {result['items_created']}")
        print(f"   Items Errors: {result.get('items_errors', 0)}")
        print(f"   Subitems Created: {result['subitems_created']}")
        print(f"   Subitems Errors: {result.get('subitems_errors', 0)}")
        
        success = result['status'] not in ['FAILED']
        
        if success:
            print(f"\n✅ Test completed successfully!")
        else:
            print(f"\n❌ Test failed")
        
        return success
        
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_single_customer()
    exit(0 if success else 1)
