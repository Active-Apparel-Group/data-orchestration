#!/usr/bin/env python3
"""
Task FY1: Verify YAML loads correctly
Validation script for customer_orders_execution_checklist.yaml
"""

import sys
from pathlib import Path
import yaml

# Add project root to Python path
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

def main():
    print("🔍 Task FY1: Verify YAML loads correctly")
    print("-" * 50)
    
    # Load the YAML mapping file
    mapping_path = repo_root / "sql" / "mappings" / "orders-unified-monday-mapping.yaml"
    
    if not mapping_path.exists():
        print(f"❌ FAILED: YAML file not found at {mapping_path}")
        return False
    
    try:
        with open(mapping_path, 'r') as f:
            mapping = yaml.safe_load(f)
        
        exact_matches = mapping.get('exact_matches', [])
        mapped_fields = mapping.get('mapped_fields', [])
        computed_fields = mapping.get('computed_fields', [])
        
        print(f"✅ SUCCESS: YAML file loaded successfully")
        print(f"   📊 Exact matches: {len(exact_matches)}")
        print(f"   📊 Mapped fields: {len(mapped_fields)}")
        print(f"   📊 Computed fields: {len(computed_fields)}")
        print(f"   📊 Total field mappings: {len(exact_matches) + len(mapped_fields) + len(computed_fields)}")
        
        # Validate expected structure
        if len(exact_matches) >= 30:
            print(f"✅ Expected output achieved: Loaded {len(exact_matches)} exact matches")
            return True
        else:
            print(f"❌ FAILED: Expected 30+ exact matches, got {len(exact_matches)}")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: Error loading YAML: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
