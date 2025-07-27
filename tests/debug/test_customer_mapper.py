"""
Test Customer Mapper - Validate dynamic YAML-based customer mapping
Purpose: Test the new CustomerMapper utility
Location: tests/debug/test_customer_mapper.py
"""
import sys
from pathlib import Path

# Add project root for imports
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / "utils"))

from customer_mapper import CustomerMapper

def test_customer_mapper():
    """Test the CustomerMapper functionality"""
    print("🧪 Testing Customer Mapper...")
    print("=" * 50)
    
    try:
        # Initialize mapper
        mapper = CustomerMapper()
        
        # Test mapping summary
        summary = mapper.get_mapping_summary()
        print("📊 Mapping Summary:")
        print(f"   Total Customers: {summary['total_customers']}")
        print(f"   Approved Customers: {summary['approved_customers']}")
        print(f"   Review Customers: {summary['review_customers']}")
        print(f"   Total Mappings: {summary['total_mappings']}")
        print(f"   Mapping File: {summary['mapping_file']}")
        print()
        
        # Test specific customer mappings
        test_customers = [
            "GREYSON",
            "GREYSON CLOTHIERS", 
            "ACTIVELY BLACK",
            "AIME LEON DORE",
            "UNKNOWN_CUSTOMER",
            "",
            None
        ]
        
        print("🔍 Customer Mapping Tests:")
        for customer in test_customers:
            canonical = mapper.normalize_customer_name(customer)
            priority = mapper.get_customer_priority(customer)
            status = mapper.get_customer_status(customer)
            
            print(f"   {customer or 'None':<20} → {canonical:<20} (Priority: {priority}, Status: {status})")
        
        print()
        
        # Test approved customers
        approved = mapper.get_approved_customers()
        print(f"✅ Approved Customers ({len(approved)}):")
        for customer in approved[:5]:  # Show first 5
            print(f"   - {customer}")
        if len(approved) > 5:
            print(f"   ... and {len(approved) - 5} more")
        
        print()
        print("✅ Customer Mapper test completed successfully!")
        
    except Exception as e:
        print(f"❌ Customer Mapper test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_customer_mapper()
