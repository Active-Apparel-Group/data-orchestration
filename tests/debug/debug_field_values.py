"""
Debug Script: Analyze Field Values in Live Data
Purpose: Check why some fields aren't mapping despite being present
Location: tests/debug/debug_field_values.py
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
from monday_api_adapter import MondayApiAdapter

def debug_field_values():
    """Debug why some fields aren't mapping in live data"""
    logger = logger_helper.get_logger(__name__)
    
    print("🔍 DEBUG: Field Values Analysis")
    print("=" * 50)
    
    # Get live data
    batch_processor = CustomerBatchProcessor()
    orders_df = batch_processor.get_customer_changes('GREYSON', limit=1)
    live_order = orders_df.iloc[0]
    
    print(f"Test Order: {live_order['AAG ORDER NUMBER']} - {live_order['CUSTOMER NAME']}")
    
    # Load YAML and check field values
    import yaml
    mapping_file = repo_root / "sql" / "mappings" / "orders-unified-monday-mapping.yaml"
    
    with open(mapping_file, 'r') as f:
        mapping_data = yaml.safe_load(f)
    
    # Test Monday API adapter
    monday_adapter = MondayApiAdapter()
    
    print(f"\n📊 FIELD VALUE ANALYSIS:")
    print("-" * 40)
    
    empty_fields = []
    mapped_fields = []
    
    # Check exact matches
    for field_mapping in mapping_data.get('exact_matches', []):
        source_field = field_mapping.get('source_field')
        target_column_id = field_mapping.get('target_column_id')
        
        if source_field in live_order:
            value = live_order[source_field]
            clean_value = monday_adapter._extract_clean_value(value)
            
            if clean_value and str(clean_value).strip():
                mapped_fields.append({
                    'field': source_field, 
                    'value': clean_value, 
                    'target': target_column_id
                })
            else:
                empty_fields.append({
                    'field': source_field, 
                    'value': value, 
                    'target': target_column_id,
                    'reason': 'empty_or_null'
                })
    
    print(f"✅ Fields with values: {len(mapped_fields)}")
    print(f"❌ Empty/null fields: {len(empty_fields)}")
    
    # Show sample mapped fields
    print(f"\n✅ SAMPLE MAPPED FIELDS:")
    for field in mapped_fields[:10]:
        print(f"   {field['field']}: '{field['value']}'")
    
    # Show empty fields
    if empty_fields:
        print(f"\n❌ EMPTY FIELDS:")
        for field in empty_fields[:10]:
            print(f"   {field['field']}: {field['value']} (reason: {field['reason']})")
    
    # Test actual transformation
    print(f"\n🧪 TRANSFORMATION TEST:")
    print("-" * 30)
    
    column_values = monday_adapter._transform_to_monday_columns(live_order)
    
    print(f"Final mapped fields: {len(column_values)}")
    print(f"Sample mappings:")
    for i, (key, value) in enumerate(column_values.items()):
        if i < 5:
            print(f"   {key}: {value}")
    
    return len(mapped_fields), len(empty_fields), len(column_values)

if __name__ == "__main__":
    debug_field_values()
