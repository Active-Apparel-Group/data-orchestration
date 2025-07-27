#!/usr/bin/env python3
"""
Search for critical field patterns in ORDERS_UNIFIED schema to find correct column names
"""

import sys
from pathlib import Path
import pandas as pd

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

def find_critical_columns():
    """Find actual column names for critical fields in ORDERS_UNIFIED"""
    
    print("🔍 SEARCHING FOR CRITICAL COLUMNS IN ORDERS_UNIFIED")
    print("=" * 60)
    
    with db.get_connection('orders') as conn:
        # Get all column names
        query = """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'ORDERS_UNIFIED'
        ORDER BY COLUMN_NAME
        """
        df = pd.read_sql(query, conn)
        
    all_columns = df['COLUMN_NAME'].tolist()
    print(f"📊 Total columns in ORDERS_UNIFIED: {len(all_columns)}")
    
    # Define search patterns for critical fields
    search_patterns = {
        'CUSTOMER': ['CUSTOMER', 'CLIENT'],
        'STYLE': ['STYLE', 'PRODUCT', 'ITEM'],
        'COLOR': ['COLOR', 'COLOUR'],
        'PO_NUMBER': ['PO', 'ORDER', 'NUMBER'],
        'DUE_DATE': ['DUE', 'DATE', 'DELIVERY'],
        'QUANTITY': ['QTY', 'QUANTITY', 'AMOUNT'],
        'SEASON': ['SEASON'],
        'FACTORY': ['FACTORY', 'VENDOR', 'SUPPLIER']
    }
    
    print("\n🎯 CRITICAL FIELD SEARCH RESULTS:")
    
    for field_type, patterns in search_patterns.items():
        print(f"\n🔸 {field_type} patterns ({patterns}):")
        matches = []
        
        for col in all_columns:
            col_upper = col.upper()
            for pattern in patterns:
                if pattern.upper() in col_upper:
                    matches.append(col)
                    break
        
        if matches:
            print(f"   Found {len(matches)} matches:")
            for match in sorted(matches)[:10]:  # Show first 10
                print(f"     - {match}")
            if len(matches) > 10:
                print(f"     ... and {len(matches) - 10} more")
        else:
            print("   ❌ No matches found")
    
    # Look for size columns (this is the big one - 276+ size columns)
    print(f"\n🎯 SIZE COLUMN ANALYSIS:")
    size_columns = []
    for col in all_columns:
        # Size columns are typically short and numeric/alphanumeric
        if len(col) <= 10 and any(c.isdigit() for c in col):
            size_columns.append(col)
    
    print(f"   Found {len(size_columns)} potential size columns")
    print(f"   Sample size columns: {size_columns[:20]}")
    
    # Show a complete sample of all columns to understand the structure
    print(f"\n📋 COMPLETE COLUMN SAMPLE (first 50 of {len(all_columns)}):")
    for i, col in enumerate(all_columns[:50]):
        print(f"   {i+1:2d}. {col}")
    
    return all_columns

def analyze_orders_unified_data_sample():
    """Get a sample of actual data to understand the structure"""
    
    print(f"\n🔍 ANALYZING ACTUAL DATA SAMPLE")
    print("=" * 40)
    
    with db.get_connection('orders') as conn:
        # Get a sample row to see actual data
        query = "SELECT TOP 1 * FROM ORDERS_UNIFIED"
        df = pd.read_sql(query, conn)
        
    if len(df) > 0:
        print(f"📊 Sample record found with {len(df.columns)} columns")
        
        # Show non-null values from the sample
        sample_row = df.iloc[0]
        non_null_fields = []
        
        for col, value in sample_row.items():
            if pd.notna(value) and str(value).strip():
                non_null_fields.append((col, str(value)[:50]))  # Truncate long values
        
        print(f"\n📈 NON-NULL FIELDS IN SAMPLE ({len(non_null_fields)} found):")
        for col, value in non_null_fields[:30]:  # Show first 30
            print(f"   {col}: {value}")
        
        if len(non_null_fields) > 30:
            print(f"   ... and {len(non_null_fields) - 30} more non-null fields")
    
    else:
        print("❌ No data found in ORDERS_UNIFIED")

if __name__ == "__main__":
    all_columns = find_critical_columns()
    analyze_orders_unified_data_sample()
