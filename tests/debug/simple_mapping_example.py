"""
Example: Using the Simple Mapping Approach
Shows how to replace complex mapping logic with the new simple approach
"""

import sys
import json
from pathlib import Path

# Add the project root to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.simple_mapper import SimpleOrdersMapper
from utils.db_helper import get_connection

def example_simple_mapping():
    """Example of using the simple mapping approach"""
    
    print("🚀 Simple Mapping Example - GREYSON PO 4755")
    print("=" * 50)
    
    # Initialize the simple mapper
    mapper = SimpleOrdersMapper()
    
    # Sample data from your ORDERS_UNIFIED table
    sample_order = {
        "AAG ORDER NUMBER": "JOO-00505",
        "CUSTOMER": "greyson",  # Will be standardized
        "AAG SEASON": "2026 SPRING", 
        "DUE DATE": "2025-07-01",
        "ORDER QTY": 720,
        "STATUS": "NEW"
    }
    
    print("📋 Source Data:")
    print(json.dumps(sample_order, indent=2))
    
    # Validate the data
    validation = mapper.validate_data(sample_order)
    print(f"\n✅ Validation: {'PASSED' if validation['valid'] else 'FAILED'}")
    if validation['issues']:
        for issue in validation['issues']:
            print(f"   ⚠️  {issue}")
    
    # Transform to Monday.com format
    monday_payload = mapper.transform_master_item(sample_order)
    print(f"\n🎯 Monday.com Payload:")
    print(json.dumps(monday_payload, indent=2))
    
    # Show what this replaces
    print(f"\n💡 This replaces:")
    print(f"   ❌ 798-line orders_unified_monday_mapping.yaml")
    print(f"   ❌ 305-line master_field_mapping.json") 
    print(f"   ❌ 379-line subitems_mapping_schema.json")
    print(f"   ✅ 1 simple 67-line simple-orders-mapping.yaml")
    print(f"   ✅ 1 clean 150-line simple_mapper.py")
    
    return monday_payload

def example_database_integration():
    """Example of using simple mapping with database"""
    
    print("\n🔄 Database Integration Example")
    print("=" * 50)
    
    try:
        # Get database connection (your existing pattern)
        with get_connection('dms') as conn:
            
            # Your existing query pattern
            query = """
            SELECT TOP 1
                [AAG ORDER NUMBER],
                [CUSTOMER], 
                [AAG SEASON],
                [DUE DATE],
                [ORDER QTY],
                [STATUS]
            FROM ORDERS_UNIFIED 
            WHERE [CUSTOMER] LIKE '%GREYSON%'
            """
            
            cursor = conn.cursor()
            cursor.execute(query)
            
            # Get the data
            row = cursor.fetchone()
            if row:
                # Convert to dictionary
                columns = [desc[0] for desc in cursor.description]
                source_data = dict(zip(columns, row))
                
                print("📊 Database Record:")
                print(json.dumps(source_data, indent=2, default=str))
                
                # Use simple mapping
                mapper = SimpleOrdersMapper()
                monday_payload = mapper.transform_master_item(source_data)
                
                print(f"\n🎯 Ready for Monday.com API:")
                print(json.dumps(monday_payload, indent=2))
                
                return monday_payload
            else:
                print("⚠️  No GREYSON records found")
                
    except Exception as e:
        print(f"❌ Database error: {e}")
        print(f"💡 Make sure your database connection is configured correctly")

def compare_old_vs_new():
    """Show the complexity reduction"""
    
    print(f"\n📊 Complexity Comparison")
    print("=" * 50)
    
    old_approach = {
        "Files": 4,
        "Total Lines": 1482,  # 798 + 305 + 379 = 1482 lines
        "Complexity": "HIGH",
        "Maintainability": "DIFFICULT",
        "Testing": "COMPLEX"
    }
    
    new_approach = {
        "Files": 2, 
        "Total Lines": 217,   # 67 + 150 = 217 lines
        "Complexity": "LOW",
        "Maintainability": "EASY", 
        "Testing": "SIMPLE"
    }
    
    print("📉 OLD Approach:")
    for key, value in old_approach.items():
        print(f"   {key}: {value}")
    
    print(f"\n📈 NEW Approach:")
    for key, value in new_approach.items():
        print(f"   {key}: {value}")
    
    reduction = ((old_approach["Total Lines"] - new_approach["Total Lines"]) / old_approach["Total Lines"]) * 100
    print(f"\n🎉 Code Reduction: {reduction:.1f}%")

if __name__ == "__main__":
    example_simple_mapping()
    example_database_integration()
    compare_old_vs_new()
    
    print(f"\n🚀 Next Steps:")
    print(f"   1. Test this example: python tests/debug/simple_mapping_example.py")
    print(f"   2. Replace complex mapping logic in your orders sync script")
    print(f"   3. Update GraphQL operations to use simple payloads")
    print(f"   4. Test with real GREYSON PO 4755 data")
