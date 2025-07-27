#!/usr/bin/env python3
"""
Fix the mapping validation by using the correct ORDERS_UNIFIED column names
from the order-staging reference project and create a proper mapping.
"""

import sys
from pathlib import Path
import pandas as pd
import yaml
import re

# Standard import pattern
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

import db_helper as db

def get_actual_orders_unified_schema():
    """Get the actual column names from ORDERS_UNIFIED table"""
    print("🔍 Getting actual ORDERS_UNIFIED schema...")
    
    with db.get_connection('orders') as conn:
        # Get column information
        query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'ORDERS_UNIFIED'
        ORDER BY ORDINAL_POSITION
        """
        df = pd.read_sql(query, conn)
        
    print(f"📊 Found {len(df)} columns in ORDERS_UNIFIED")
    return df

def load_order_staging_mapping():
    """Load the working mapping from order-staging project"""
    mapping_path = repo_root / "dev" / "order-staging" / "handover" / "orders_unified_monday_mapping.yaml"
    
    if not mapping_path.exists():
        print(f"❌ Order-staging mapping not found at: {mapping_path}")
        return None
        
    print(f"📖 Loading order-staging mapping from: {mapping_path}")
    with open(mapping_path, 'r') as f:
        return yaml.safe_load(f)

def load_staging_ddl_columns():
    """Load staging table DDL columns"""
    master_ddl_path = repo_root / "sql" / "ddl" / "tables" / "orders" / "staging" / "stg_mon_custmasterschedule.sql"
    subitem_ddl_path = repo_root / "sql" / "ddl" / "tables" / "orders" / "staging" / "stg_mon_custmasterschedule_subitems.sql"
    
    def extract_columns_from_ddl(file_path):
        if not file_path.exists():
            return []
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Extract column names from DDL
        columns = []
        lines = content.split('\n')
        in_create_table = False
        
        for line in lines:
            line = line.strip()
            if 'CREATE TABLE' in line.upper():
                in_create_table = True
                continue
            if in_create_table and line.startswith(')'):
                break
            if in_create_table and line and not line.startswith('--'):
                # Extract column name (first word before space or comma)
                parts = line.split()
                if parts and not parts[0].upper() in ['PRIMARY', 'FOREIGN', 'CONSTRAINT', 'INDEX']:
                    col_name = parts[0].replace('[', '').replace(']', '').replace(',', '')
                    if col_name:
                        columns.append(col_name)
        
        return columns
    
    master_columns = extract_columns_from_ddl(master_ddl_path)
    subitem_columns = extract_columns_from_ddl(subitem_ddl_path)
    
    print(f"📋 Master DDL columns: {len(master_columns)}")
    print(f"📋 Subitem DDL columns: {len(subitem_columns)}")
    
    return master_columns, subitem_columns

def create_fixed_mapping_validation():
    """Create a comprehensive mapping validation with correct column names"""
    
    print("🚀 CREATING FIXED MAPPING VALIDATION")
    print("=" * 60)
    
    # Get actual database schema
    orders_unified_df = get_actual_orders_unified_schema()
    orders_unified_columns = set(orders_unified_df['COLUMN_NAME'].tolist())
    
    print(f"\n📊 ORDERS_UNIFIED has {len(orders_unified_columns)} columns")
    print("Sample columns:", list(orders_unified_columns)[:10])
    
    # Get staging DDL columns
    master_columns, subitem_columns = load_staging_ddl_columns()
    master_columns_set = set(master_columns)
    subitem_columns_set = set(subitem_columns)
    
    # Load working order-staging mapping
    order_staging_mapping = load_order_staging_mapping()
    
    if not order_staging_mapping:
        print("❌ Could not load order-staging mapping")
        return
    
    # Extract mappings from order-staging format
    working_mappings = {}
    
    # Process exact_matches
    if 'exact_matches' in order_staging_mapping:
        for mapping in order_staging_mapping['exact_matches']:
            source_field = mapping.get('source_field')
            target_field = mapping.get('target_field')
            if source_field and target_field:
                working_mappings[target_field] = source_field
    
    # Process mapped_fields  
    if 'mapped_fields' in order_staging_mapping:
        for mapping in order_staging_mapping['mapped_fields']:
            source_field = mapping.get('source_field')
            target_field = mapping.get('target_field')
            if source_field and target_field:
                working_mappings[target_field] = source_field
    
    print(f"\n🗺️ Found {len(working_mappings)} working mappings from order-staging")
    
    # Create validation DataFrame
    validation_data = []
    
    for target_col, source_col in working_mappings.items():
        # Determine table target
        if target_col in master_columns_set:
            table_target = 'master'
        elif target_col in subitem_columns_set:
            table_target = 'subitem'
        else:
            table_target = 'missing'
        
        # Check if source exists in ORDERS_UNIFIED
        source_exists = source_col in orders_unified_columns
        
        # Check if target exists in staging DDL
        target_in_master = target_col in master_columns_set
        target_in_subitem = target_col in subitem_columns_set
        
        # Mapping is valid if both source and target exist
        mapping_valid = source_exists and (target_in_master or target_in_subitem)
        
        # Determine issues
        issues = []
        if not source_exists:
            issues.append("source column missing")
        if not target_in_master and not target_in_subitem:
            issues.append("staging column missing")
        
        validation_data.append({
            'target_column': target_col,
            'source_column': source_col,
            'table_target': table_target,
            'in_orders_unified': source_exists,
            'in_master_ddl': target_in_master,
            'in_subitem_ddl': target_in_subitem,
            'mapping_valid': mapping_valid,
            'issues': '; '.join(issues) if issues else 'none'
        })
    
    # Convert to DataFrame
    df = pd.DataFrame(validation_data)
    
    # Save detailed report
    report_path = repo_root / "mapping_validation_fixed_report.csv"
    df.to_csv(report_path, index=False)
    
    # Analysis
    total_mappings = len(df)
    valid_mappings = len(df[df['mapping_valid'] == True])
    invalid_mappings = total_mappings - valid_mappings
    
    print(f"\n📈 FIXED MAPPING VALIDATION RESULTS:")
    print(f"   Total mappings: {total_mappings}")
    print(f"   Valid mappings: {valid_mappings} ({valid_mappings/total_mappings*100:.1f}%)")
    print(f"   Invalid mappings: {invalid_mappings} ({invalid_mappings/total_mappings*100:.1f}%)")
    
    # Show valid mappings
    valid_df = df[df['mapping_valid'] == True]
    print(f"\n✅ VALID MAPPINGS ({len(valid_df)} found):")
    for _, row in valid_df.head(10).iterrows():
        print(f"   {row['source_column']} -> {row['target_column']} ({row['table_target']})")
    
    if len(valid_df) > 10:
        print(f"   ... and {len(valid_df) - 10} more valid mappings")
    
    # Show invalid mappings
    invalid_df = df[df['mapping_valid'] == False]
    print(f"\n❌ INVALID MAPPINGS ({len(invalid_df)} found):")
    for _, row in invalid_df.head(10).iterrows():
        print(f"   {row['source_column']} -> {row['target_column']} ({row['issues']})")
    
    if len(invalid_df) > 10:
        print(f"   ... and {len(invalid_df) - 10} more invalid mappings")
    
    # Critical field analysis
    critical_fields = ['CUSTOMER', 'STYLE', 'COLOR', 'PO_NUMBER', 'DUE_DATE']
    print(f"\n🚨 CRITICAL FIELD ANALYSIS:")
    
    for field in critical_fields:
        # Check if field exists in any form
        field_rows = df[df['target_column'].str.contains(field, case=False, na=False)]
        if len(field_rows) > 0:
            row = field_rows.iloc[0]
            print(f"   {field}:")
            print(f"      Source: {row['source_column']}")
            print(f"      Target: {row['target_column']}")
            print(f"      Valid: {row['mapping_valid']}")
            print(f"      Issues: {row['issues']}")
        else:
            print(f"   {field}: NOT FOUND in mapping")
    
    print(f"\n📄 Detailed report saved to: {report_path}")
    print("\n🎯 NEXT STEPS:")
    print("   1. Review the valid mappings - these are working correctly")
    print("   2. Fix the invalid mappings by updating source column names")
    print("   3. Add missing critical fields to the mapping")
    print("   4. Update the comprehensive mapping YAML with correct column names")

if __name__ == "__main__":
    create_fixed_mapping_validation()
