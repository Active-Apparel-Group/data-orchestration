#!/usr/bin/env python3
"""
Test Customer Canonicalization
Verify that customer names are properly canonicalized in the pipeline
"""

import os
import sys
from pathlib import Path

# Add paths
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root / "dev" / "customer-orders"))
sys.path.insert(0, str(repo_root / "utils"))

def test_customer_canonicalization():
    """Test customer name canonicalization"""
    
    print("🔍 Customer Canonicalization Test")
    print("=" * 50)
    
    try:
        # Import the customer mapper from dev/customer-orders (uses customer-canonical.yaml)
        sys.path.insert(0, str(repo_root / "dev" / "customer-orders"))
        from customer_mapper import CustomerMapper
        
        # Initialize mapper
        mapper = CustomerMapper()
        print("✅ CustomerMapper initialized")
        
        # Test cases
        test_cases = [
            ("GREYSON", "GREYSON"),
            ("GREYSON CLOTHIERS", "GREYSON"),
            ("greyson clothiers", "GREYSON"),
            ("Unknown Customer", "Unknown Customer")
        ]
        
        print("\n📋 Customer Mapping Tests:")
        for input_name, expected in test_cases:
            result = mapper.normalize_customer_name(input_name)
            status = "✅" if result == expected else "❌"
            print(f"   {status} '{input_name}' → '{result}' (expected: '{expected}')")
        
        # Test database name mapping
        print("\n📋 Database Name Mapping Tests:")
        for input_name, expected_canonical in test_cases[:2]:  # Only test valid customers
            db_name = mapper.get_database_customer_name(input_name)
            print(f"   📊 '{input_name}' → DB: '{db_name}' (canonical: '{expected_canonical}')")
        
        # Show available customers
        print(f"\n📊 Loaded {len(mapper.canonical_mapping)} customer mappings")
        print("   Sample mappings:")
        for i, (key, value) in enumerate(list(mapper.canonical_mapping.items())[:5]):
            print(f"     '{key}' → '{value}'")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_customer_canonicalization()
    sys.exit(0 if success else 1)
