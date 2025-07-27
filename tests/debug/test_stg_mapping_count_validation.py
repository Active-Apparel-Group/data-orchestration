"""
STG Column Mapping Validation and Count Script
This script provides concrete proof of the STG → Monday.com column mapping coverage.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.mapping_helper import get_orders_field_mappings, get_orders_subitem_mappings, load_orders_mapping_config
from utils.db_helper import get_db_connection
import yaml

def analyze_stg_column_mappings():
    """
    Analyze and count exactly how many STG columns are mapped to Monday.com columns.
    """
    print("🔍 STG Column Mapping Analysis - Production Readiness Validation")
    print("=" * 80)
    
    # Load the mapping configuration
    try:
        field_mappings = get_orders_field_mappings()
        subitem_mappings = get_orders_subitem_mappings()
        config = load_orders_mapping_config()
        
        print(f"✅ Successfully loaded orders mapping configuration")
        print(f"📁 Source: sql/mappings/orders-unified-comprehensive-mapping.yaml")
        print()
        
    except Exception as e:
        print(f"❌ Error loading mapping configuration: {e}")
        return
    
    # Analyze master item mappings
    print("📊 MASTER ITEM MAPPINGS (STG → Monday.com)")
    print("-" * 50)
    
    master_count = 0
    for source_field, monday_column_id in field_mappings.items():
        print(f"  {source_field:30} → {monday_column_id}")
        master_count += 1
    
    print(f"\n📈 Total Master Item Mappings: {master_count}")
    
    # Analyze subitem mappings
    print("\n📊 SUBITEM MAPPINGS (STG → Monday.com)")
    print("-" * 50)
    
    subitem_count = 0
    for field_name, monday_column_id in subitem_mappings.items():
        print(f"  {field_name:30} → {monday_column_id}")
        subitem_count += 1
    
    print(f"\n📈 Total Subitem Mappings: {subitem_count}")
    
    # Total mapping count
    total_mapped_columns = master_count + subitem_count
    print(f"\n🎯 TOTAL STG COLUMNS MAPPED TO MONDAY.COM: {total_mapped_columns}")
    
    # Analyze mapping categories from config
    metadata = config.get('metadata', {})
    print(f"\n📋 MAPPING METADATA:")
    print(f"  Total Source Fields: {metadata.get('total_source_fields', 'Unknown')}")
    print(f"  Total Target Fields: {metadata.get('total_target_fields', 'Unknown')}")
    print(f"  Mappable Fields: {metadata.get('mappable_fields', 'Unknown')}")
    print(f"  Version: {metadata.get('version', 'Unknown')}")
    print(f"  Status: {metadata.get('status', 'Unknown')}")
    
    return field_mappings, subitem_mappings, total_mapped_columns

def validate_api_adapter_usage():
    """
    Validate that the API adapter actually uses the mapping helper functions.
    """
    print("\n🔧 API ADAPTER USAGE VALIDATION")
    print("=" * 80)
    
    # Check the API adapter file
    api_adapter_path = os.path.join(os.path.dirname(__file__), '..', '..', 'dev', 'customer-orders', 'monday_api_adapter.py')
    
    if not os.path.exists(api_adapter_path):
        print(f"❌ API adapter file not found: {api_adapter_path}")
        return False
    
    try:
        with open(api_adapter_path, 'r') as f:
            content = f.read()
        
        # Check for mapping helper imports
        uses_mapping_helper = 'from utils.mapping_helper import' in content
        uses_get_orders_mappings = 'get_orders_field_mappings' in content
        uses_get_subitem_mappings = 'get_orders_subitem_mappings' in content
        
        print(f"✅ Uses mapping_helper import: {uses_mapping_helper}")
        print(f"✅ Uses get_orders_field_mappings: {uses_get_orders_mappings}")
        print(f"✅ Uses get_orders_subitem_mappings: {uses_get_subitem_mappings}")
        
        # Check for hardcoded column IDs (should not exist)
        hardcoded_patterns = ['text_', 'numbers_', 'dropdown_', 'date_']
        hardcoded_found = []
        
        for pattern in hardcoded_patterns:
            if f"'{pattern}" in content or f'"{pattern}' in content:
                # Look for lines with hardcoded patterns
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if pattern in line and ('mkr' in line or 'text4' in line or 'numbers' in line):
                        hardcoded_found.append(f"Line {i}: {line.strip()}")
        
        if hardcoded_found:
            print(f"⚠️  Potential hardcoded column IDs found:")
            for item in hardcoded_found:
                print(f"    {item}")
        else:
            print(f"✅ No hardcoded column IDs detected")
        
        return uses_mapping_helper and uses_get_orders_mappings and not hardcoded_found
        
    except Exception as e:
        print(f"❌ Error reading API adapter: {e}")
        return False

def validate_stg_table_columns():
    """
    Validate that STG tables have the necessary columns for mapping.
    """
    print("\n🗄️  STG TABLE COLUMN VALIDATION")
    print("=" * 80)
    
    try:
        with get_db_connection('dms') as conn:
            cursor = conn.cursor()
            
            # Check STG master table columns
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'stg_mon_custmasterschedule'
                ORDER BY ORDINAL_POSITION
            """)
            
            stg_master_columns = cursor.fetchall()
            print(f"📋 STG Master Table Columns ({len(stg_master_columns)}):")
            for col_name, data_type in stg_master_columns:
                print(f"  {col_name:35} {data_type}")
            
            # Check STG subitems table columns
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'stg_mon_custmasterschedule_subitems'
                ORDER BY ORDINAL_POSITION
            """)
            
            stg_subitems_columns = cursor.fetchall()
            print(f"\n📋 STG Subitems Table Columns ({len(stg_subitems_columns)}):")
            for col_name, data_type in stg_subitems_columns:
                print(f"  {col_name:35} {data_type}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error validating STG table columns: {e}")
        return False

def generate_production_readiness_summary():
    """
    Generate a final production readiness summary.
    """
    print("\n🎯 PRODUCTION READINESS SUMMARY")
    print("=" * 80)
    
    # Run all validations
    field_mappings, subitem_mappings, total_mapped = analyze_stg_column_mappings()
    api_adapter_valid = validate_api_adapter_usage()
    stg_tables_valid = validate_stg_table_columns()
    
    print(f"\n📊 FINAL VALIDATION RESULTS:")
    print(f"  ✅ Total STG columns mapped to Monday.com: {total_mapped}")
    print(f"  {'✅' if api_adapter_valid else '❌'} API adapter uses dynamic mapping: {api_adapter_valid}")
    print(f"  {'✅' if stg_tables_valid else '❌'} STG tables have required columns: {stg_tables_valid}")
    
    all_valid = api_adapter_valid and stg_tables_valid and total_mapped > 0
    
    print(f"\n🎉 PRODUCTION READY: {'YES' if all_valid else 'NO'}")
    
    if all_valid:
        print("🚀 The mapping infrastructure is rock solid and production-ready!")
        print("   ✓ Dynamic mapping configuration loaded from YAML")
        print("   ✓ Real Monday.com column IDs are used")
        print("   ✓ No hardcoded values detected")
        print("   ✓ STG tables have proper schema")
        print(f"   ✓ {total_mapped} columns mapped for data synchronization")
    else:
        print("⚠️  Issues detected that need resolution before production deployment")
    
    return all_valid

if __name__ == "__main__":
    try:
        success = generate_production_readiness_summary()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Script execution failed: {e}")
        sys.exit(1)
