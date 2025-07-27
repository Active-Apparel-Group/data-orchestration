"""
Debug Script: Compare Test Data vs Live Database Data
Purpose: Identify field differences between test data and real GREYSON data
Location: tests/debug/debug_field_availability.py
"""
import sys
from pathlib import Path
import pandas as pd

# Add project root for imports
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))
sys.path.insert(0, str(repo_root / "dev" / "customer-orders"))

import db_helper as db
import logger_helper
from customer_batch_processor import CustomerBatchProcessor

def debug_field_availability():
    """Compare test data vs live database data field availability"""
    logger = logger_helper.get_logger(__name__)
    
    print("🔍 DEBUG: Field Availability Analysis")
    print("=" * 50)
    
    # Get live data from GREYSON
    print("\n1️⃣ LIVE DATABASE DATA:")
    print("-" * 30)
    
    batch_processor = CustomerBatchProcessor()
    orders_df = batch_processor.get_customer_changes('GREYSON', limit=1)
    
    if orders_df.empty:
        print("❌ No orders found for GREYSON")
        return
    
    live_order = orders_df.iloc[0]
    live_fields = set(live_order.index)
    print(f"Live data fields: {len(live_fields)}")
    print("Live fields:", sorted(live_fields))
    
    # Load YAML mapping to see what fields are expected
    print("\n2️⃣ YAML EXPECTED FIELDS:")
    print("-" * 30)
    
    import yaml
    mapping_file = repo_root / "sql" / "mappings" / "orders-unified-monday-mapping.yaml"
    
    with open(mapping_file, 'r') as f:
        mapping_data = yaml.safe_load(f)
    
    yaml_fields = set()
    
    # Collect all source fields from YAML
    for field_mapping in mapping_data.get('exact_matches', []):
        yaml_fields.add(field_mapping.get('source_field'))
    
    for field_mapping in mapping_data.get('mapped_fields', []):
        yaml_fields.add(field_mapping.get('source_field'))
    
    for computed_field in mapping_data.get('computed_fields', []):
        yaml_fields.update(computed_field.get('source_fields', []))
    
    yaml_fields.discard(None)  # Remove None values
    print(f"YAML expected fields: {len(yaml_fields)}")
    print("YAML fields:", sorted(yaml_fields))
    
    # Find differences
    print("\n3️⃣ FIELD ANALYSIS:")
    print("-" * 30)
    
    missing_in_live = yaml_fields - live_fields
    extra_in_live = live_fields - yaml_fields
    common_fields = yaml_fields & live_fields
    
    print(f"✅ Common fields: {len(common_fields)}")
    print(f"❌ Missing in live data: {len(missing_in_live)}")
    print(f"➕ Extra in live data: {len(extra_in_live)}")
    
    if missing_in_live:
        print(f"\n🚨 MISSING FIELDS (in YAML but not in live data):")
        for field in sorted(missing_in_live):
            print(f"   - {field}")
    
    if extra_in_live:
        print(f"\n➕ EXTRA FIELDS (in live data but not in YAML):")
        for field in sorted(extra_in_live)[:10]:  # Show first 10
            print(f"   - {field}")
        if len(extra_in_live) > 10:
            print(f"   ... and {len(extra_in_live) - 10} more")
    
    # Calculate expected mapping coverage
    coverage_ratio = len(common_fields) / len(yaml_fields) * 100
    print(f"\n📊 MAPPING COVERAGE: {coverage_ratio:.1f}%")
    print(f"Expected mappable fields: {len(common_fields)}")
    
    return common_fields, missing_in_live, extra_in_live

if __name__ == "__main__":
    debug_field_availability()
