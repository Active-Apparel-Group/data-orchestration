#!/usr/bin/env python3
"""
Run comprehensive mapping validation using the corrected comprehensive mapping YAML
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

def run_comprehensive_validation():
    """Run validation using our corrected comprehensive mapping"""
    
    print("🚀 COMPREHENSIVE MAPPING VALIDATION (CORRECTED)")
    print("=" * 60)
    
    # Get actual database schema
    with db.get_connection('orders') as conn:
        query = """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'ORDERS_UNIFIED'
        ORDER BY COLUMN_NAME
        """
        df = pd.read_sql(query, conn)
        
    orders_unified_columns = set(df['COLUMN_NAME'].tolist())
    print(f"📊 ORDERS_UNIFIED has {len(orders_unified_columns)} columns")
    
    # Get staging DDL columns
    def extract_columns_from_ddl(file_path):
        if not file_path.exists():
            return []
        
        with open(file_path, 'r') as f:
            content = f.read()
        
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
                parts = line.split()
                if parts and not parts[0].upper() in ['PRIMARY', 'FOREIGN', 'CONSTRAINT', 'INDEX']:
                    col_name = parts[0].replace('[', '').replace(']', '').replace(',', '')
                    if col_name:
                        columns.append(col_name)
        
        return columns
    
    master_ddl_path = repo_root / "sql" / "ddl" / "tables" / "orders" / "staging" / "stg_mon_custmasterschedule.sql"
    subitem_ddl_path = repo_root / "sql" / "ddl" / "tables" / "orders" / "staging" / "stg_mon_custmasterschedule_subitems.sql"
    
    master_columns = set(extract_columns_from_ddl(master_ddl_path))
    subitem_columns = set(extract_columns_from_ddl(subitem_ddl_path))
    
    print(f"📋 Master DDL columns: {len(master_columns)}")
    print(f"📋 Subitem DDL columns: {len(subitem_columns)}")
    
    # Load comprehensive mapping
    comprehensive_mapping_path = repo_root / "sql" / "mappings" / "orders-unified-comprehensive-mapping.yaml"
    
    if not comprehensive_mapping_path.exists():
        print(f"❌ Comprehensive mapping not found at: {comprehensive_mapping_path}")
        return
        
    print(f"📖 Loading comprehensive mapping from: {comprehensive_mapping_path}")
    with open(comprehensive_mapping_path, 'r') as f:
        comprehensive_mapping = yaml.safe_load(f)
    
    # Extract mappings from comprehensive format
    mappings = {}
    
    if 'exact_matches' in comprehensive_mapping:
        for mapping in comprehensive_mapping['exact_matches']:
            source_field = mapping.get('source_field')
            target_field = mapping.get('target_field')
            if source_field and target_field:
                mappings[target_field] = source_field
    
    print(f"🗺️ Found {len(mappings)} mappings from comprehensive mapping")
    
    # Create validation DataFrame
    validation_data = []
    
    for target_col, source_col in mappings.items():
        # Determine table target
        if target_col in master_columns:
            table_target = 'master'
        elif target_col in subitem_columns:
            table_target = 'subitem'
        else:
            table_target = 'missing'
        
        # Check if source exists in ORDERS_UNIFIED
        source_exists = source_col in orders_unified_columns
        
        # Check if target exists in staging DDL
        target_in_master = target_col in master_columns
        target_in_subitem = target_col in subitem_columns
        
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
    df_validation = pd.DataFrame(validation_data)
    
    # Save detailed report
    report_path = repo_root / "mapping_validation_comprehensive_report.csv"
    df_validation.to_csv(report_path, index=False)
    
    # Analysis
    total_mappings = len(df_validation)
    valid_mappings = len(df_validation[df_validation['mapping_valid'] == True])
    invalid_mappings = total_mappings - valid_mappings
    
    print(f"\n📈 COMPREHENSIVE MAPPING VALIDATION RESULTS:")
    print(f"   Total mappings: {total_mappings}")
    print(f"   Valid mappings: {valid_mappings} ({valid_mappings/total_mappings*100:.1f}%)")
    print(f"   Invalid mappings: {invalid_mappings} ({invalid_mappings/total_mappings*100:.1f}%)")
    
    # Show breakdown by table target
    master_count = len(df_validation[df_validation['table_target'] == 'master'])
    subitem_count = len(df_validation[df_validation['table_target'] == 'subitem'])  
    missing_count = len(df_validation[df_validation['table_target'] == 'missing'])
    
    print(f"\n🎯 TABLE TARGET BREAKDOWN:")
    print(f"   Master table mappings: {master_count}")
    print(f"   Subitem table mappings: {subitem_count}")
    print(f"   Missing/unmapped: {missing_count}")
    
    # Show valid mappings
    valid_df = df_validation[df_validation['mapping_valid'] == True]
    print(f"\n✅ VALID MAPPINGS ({len(valid_df)} found):")
    for _, row in valid_df.head(20).iterrows():
        print(f"   {row['source_column']} -> {row['target_column']} ({row['table_target']})")
    
    if len(valid_df) > 20:
        print(f"   ... and {len(valid_df) - 20} more valid mappings")
    
    # Show critical field analysis
    critical_fields = ['CUSTOMER', 'STYLE', 'COLOR', 'PO NUMBER', 'EX FACTORY DATE']
    print(f"\n🚨 CRITICAL FIELD ANALYSIS:")
    
    for field in critical_fields:
        field_rows = df_validation[df_validation['target_column'].str.contains(field, case=False, na=False)]
        if len(field_rows) > 0:
            row = field_rows.iloc[0]
            print(f"   {field}:")
            print(f"      Source: {row['source_column']}")
            print(f"      Target: {row['target_column']}")
            print(f"      Valid: {row['mapping_valid']}")
            if row['issues'] != 'none':
                print(f"      Issues: {row['issues']}")
        else:
            print(f"   {field}: NOT FOUND in mapping")
    
    # Show invalid mappings (top issues)
    invalid_df = df_validation[df_validation['mapping_valid'] == False]
    if len(invalid_df) > 0:
        print(f"\n❌ TOP INVALID MAPPINGS ({len(invalid_df)} found, showing first 10):")
        for _, row in invalid_df.head(10).iterrows():
            print(f"   {row['source_column']} -> {row['target_column']} ({row['issues']})")
        
        if len(invalid_df) > 10:
            print(f"   ... and {len(invalid_df) - 10} more invalid mappings")
    
    print(f"\n📄 Detailed report saved to: {report_path}")
    
    if valid_mappings >= 60:
        print(f"\n🎉 SUCCESS! We have {valid_mappings} valid mappings (target: 80+)")
        print("🎯 NEXT STEPS:")
        print("   1. Test the pipeline with GREYSON PO 4755")
        print("   2. Verify data flows correctly to Monday.com")
        print("   3. Add any remaining missing mappings")
    else:
        print(f"\n⚠️  Still need more valid mappings (current: {valid_mappings}, target: 80+)")
        print("🎯 IMMEDIATE ACTIONS:")
        print("   1. Fix remaining source column name mismatches")
        print("   2. Add missing staging table columns")
        print("   3. Complete the comprehensive mapping")

if __name__ == "__main__":
    run_comprehensive_validation()
