#!/usr/bin/env python3
"""
Validate mapping for critical fields needed for GREYSON PO 4755 pipeline.
Focus only on essential columns that must work for production.
"""

import pandas as pd
from pathlib import Path
import sys
import yaml

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

def validate_critical_mappings():
    """Validate only the critical fields needed for GREYSON PO 4755 production pipeline"""
    
    print("🎯 CRITICAL FIELDS VALIDATION FOR GREYSON PO 4755")
    print("=" * 60)
    
    # Define the critical fields we absolutely need
    critical_fields = {
        'CUSTOMER': {
            'source_column': 'CUSTOMER NAME',
            'target_column': 'CUSTOMER',
            'table': 'master',
            'required_for': 'Customer identification and filtering'
        },
        'STYLE': {
            'source_column': 'CUSTOMER STYLE', 
            'target_column': 'STYLE',
            'table': 'master',
            'required_for': 'Product identification'
        },
        'COLOR': {
            'source_column': 'CUSTOMER COLOUR DESCRIPTION',
            'target_column': 'COLOR', 
            'table': 'master',
            'required_for': 'Product variant identification'
        },
        'PO_NUMBER': {
            'source_column': 'PO NUMBER',
            'target_column': 'PO_NUMBER',
            'table': 'master', 
            'required_for': 'Order identification and filtering'
        },
        'DUE_DATE': {
            'source_column': 'EX FACTORY DATE',
            'target_column': 'CUSTOMER EX FACTORY DATE',
            'table': 'master',
            'required_for': 'Production planning and scheduling'
        }
    }
    
    # Get actual ORDERS_UNIFIED schema
    print("🔍 Checking ORDERS_UNIFIED schema...")
    with db.get_connection('orders') as conn:
        query = """
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'ORDERS_UNIFIED'
        """
        df = pd.read_sql(query, conn)
    
    orders_unified_columns = set(df['COLUMN_NAME'].tolist())
    print(f"✅ ORDERS_UNIFIED has {len(orders_unified_columns)} columns")
    
    # Get staging table schemas
    print("\n🔍 Checking staging table schemas...")
    
    def get_staging_columns(table_name):
        ddl_path = repo_root / "sql" / "ddl" / "tables" / "orders" / "staging" / f"{table_name}.sql"
        if not ddl_path.exists():
            return []
        
        with open(ddl_path, 'r') as f:
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
    
    master_columns = set(get_staging_columns('stg_mon_custmasterschedule'))
    subitem_columns = set(get_staging_columns('stg_mon_custmasterschedule_subitems'))
    
    print(f"✅ Master staging table has {len(master_columns)} columns")
    print(f"✅ Subitem staging table has {len(subitem_columns)} columns")
    
    # Validate each critical field
    print(f"\n🎯 VALIDATING {len(critical_fields)} CRITICAL FIELDS:")
    print("=" * 60)
    
    validation_results = []
    all_valid = True
    
    for field_name, field_info in critical_fields.items():
        source_col = field_info['source_column']
        target_col = field_info['target_column']
        table_type = field_info['table']
        purpose = field_info['required_for']
        
        # Check source exists in ORDERS_UNIFIED
        source_exists = source_col in orders_unified_columns
        
        # Check target exists in appropriate staging table
        if table_type == 'master':
            target_exists = target_col in master_columns
        elif table_type == 'subitem':
            target_exists = target_col in subitem_columns
        else:
            target_exists = False
        
        # Overall validation
        is_valid = source_exists and target_exists
        
        validation_results.append({
            'field': field_name,
            'source_column': source_col,
            'target_column': target_col,
            'table': table_type,
            'source_exists': source_exists,
            'target_exists': target_exists,
            'is_valid': is_valid,
            'purpose': purpose
        })
        
        # Print result
        status = "✅" if is_valid else "❌"
        print(f"\n{status} {field_name}:")
        print(f"   Source: {source_col} {'✅' if source_exists else '❌'}")
        print(f"   Target: {target_col} ({'master' if table_type == 'master' else 'subitem'}) {'✅' if target_exists else '❌'}")
        print(f"   Purpose: {purpose}")
        
        if not is_valid:
            all_valid = False
            if not source_exists:
                print(f"   🚨 ERROR: Source column '{source_col}' not found in ORDERS_UNIFIED")
            if not target_exists:
                print(f"   🚨 ERROR: Target column '{target_col}' not found in {table_type} staging table")
    
    # Summary
    valid_count = sum(1 for r in validation_results if r['is_valid'])
    print(f"\n📊 VALIDATION SUMMARY:")
    print(f"   Total critical fields: {len(critical_fields)}")
    print(f"   Valid mappings: {valid_count}")
    print(f"   Invalid mappings: {len(critical_fields) - valid_count}")
    print(f"   Success rate: {valid_count/len(critical_fields)*100:.1f}%")
    
    if all_valid:
        print(f"\n🎉 SUCCESS! All critical fields are properly mapped.")
        print(f"   ✅ GREYSON PO 4755 pipeline is ready for production!")
    else:
        print(f"\n❌ ISSUES FOUND! Fix the errors above before proceeding.")
        print(f"   🚨 GREYSON PO 4755 pipeline is NOT ready for production.")
    
    # Save detailed report
    df_results = pd.DataFrame(validation_results)
    report_path = repo_root / "critical_fields_validation_report.csv"
    df_results.to_csv(report_path, index=False)
    print(f"\n📄 Detailed report saved to: {report_path}")
    
    return all_valid, validation_results

if __name__ == "__main__":
    validate_critical_mappings()
