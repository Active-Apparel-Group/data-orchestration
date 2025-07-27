#!/usr/bin/env python3
"""
Test ORDERS_UNIFIED Connection and Column Access
==============================================

This script tests the connection to ORDERS_UNIFIED table and verifies
column access to diagnose any issues with the orchestrator's ORDERS_UNIFIED comparison.
"""

import sys
from pathlib import Path
import re

# Add utils to path for db_helper
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root / "utils"))

import db_helper

def normalize_col(col):
    """Normalize column names (multiple spaces to single space)"""
    return re.sub(r'\s+', ' ', str(col)).strip()

def test_orders_unified_connection():
    """Test connection to ORDERS_UNIFIED and retrieve column information"""
    
    print("🔍 Testing ORDERS_UNIFIED Connection")
    print("=" * 50)
    
    try:
        # Test connection to orders database
        print("📡 Connecting to 'orders' database...")
        with db_helper.get_connection('orders') as conn:
            cursor = conn.cursor()
            
            # Test basic table existence
            print("🔍 Checking if ORDERS_UNIFIED table exists...")
            cursor.execute("""
                SELECT COUNT(*) as table_count
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'ORDERS_UNIFIED' AND TABLE_TYPE = 'BASE TABLE'
            """)
            table_exists = cursor.fetchone()[0]
            
            if table_exists == 0:
                print("❌ ORDERS_UNIFIED table does NOT exist in orders database!")
                return False
            else:
                print(f"✅ ORDERS_UNIFIED table exists in orders database")
            
            # Test column access
            print("🔍 Testing column access with SELECT TOP 1...")
            cursor.execute("SELECT TOP 1 * FROM ORDERS_UNIFIED")
            orders_unified_cols_raw = [desc[0] for desc in cursor.description]
            
            print(f"✅ Successfully accessed ORDERS_UNIFIED columns")
            print(f"📊 Total columns found: {len(orders_unified_cols_raw)}")
            
            # Show first 10 columns
            print("\n📋 First 10 columns (raw):")
            for i, col in enumerate(orders_unified_cols_raw[:10]):
                print(f"  {i+1:2d}. '{col}'")
            
            # Test normalization
            print("\n🔧 Testing column normalization...")
            orders_unified_cols_normalized = [normalize_col(c) for c in orders_unified_cols_raw]
            
            # Show examples of normalization
            print("\n📋 Normalization examples:")
            for i, (raw, norm) in enumerate(zip(orders_unified_cols_raw[:10], orders_unified_cols_normalized[:10])):
                if raw != norm:
                    print(f"  {i+1:2d}. '{raw}' -> '{norm}'")
                else:
                    print(f"  {i+1:2d}. '{raw}' (no change)")
            
            # Test row count
            print("\n🔍 Testing row count...")
            cursor.execute("SELECT COUNT(*) FROM ORDERS_UNIFIED")
            row_count = cursor.fetchone()[0]
            print(f"📊 Total rows in ORDERS_UNIFIED: {row_count:,}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error accessing ORDERS_UNIFIED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sample_column_comparison():
    """Test column comparison with sample data"""
    
    print("\n🧪 Testing Sample Column Comparison")
    print("=" * 50)
    
    # Sample columns from a typical Monday.com export
    sample_df_columns = [
        "AAG ORDER NUMBER",
        "CUSTOMER NAME", 
        "ORDER DATE PO RECEIVED",
        "CUSTOMER ALT PO",
        "AAG SEASON",
        "CUSTOMER SEASON",
        "US Tariff    2 Dec",  # Multiple spaces example
        "S/P, MAKE OR BUY",    # Complex example
        "SOME NEW COLUMN"      # Example of column not in ORDERS_UNIFIED
    ]
    
    try:
        with db_helper.get_connection('orders') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT TOP 1 * FROM ORDERS_UNIFIED")
            orders_unified_cols_raw = [desc[0] for desc in cursor.description]
            
        # Normalize all columns
        orders_unified_cols = [normalize_col(c) for c in orders_unified_cols_raw]
        sample_df_cols_normalized = [normalize_col(c) for c in sample_df_columns]
        
        print(f"📊 Sample DataFrame columns: {len(sample_df_columns)}")
        print(f"📊 ORDERS_UNIFIED columns: {len(orders_unified_cols)}")
        
        # Find matches and misses
        missing_in_orders_unified = [col for col in sample_df_cols_normalized if col not in orders_unified_cols]
        match_count = len(sample_df_cols_normalized) - len(missing_in_orders_unified)
        match_percent = 100 * (match_count / len(sample_df_cols_normalized)) if sample_df_columns else 100
        
        print(f"\n📈 Match Results:")
        print(f"  ✅ Matching columns: {match_count}/{len(sample_df_columns)}")
        print(f"  📊 Match percentage: {match_percent:.1f}%")
        
        if missing_in_orders_unified:
            print(f"\n⚠️  Missing columns in ORDERS_UNIFIED:")
            for col in missing_in_orders_unified:
                print(f"    - '{col}'")
                
                # Show original sample column that maps to this
                original_col = next((c for c in sample_df_columns if normalize_col(c) == col), col)
                if original_col != col:
                    print(f"      (from original: '{original_col}')")
        else:
            print(f"\n✅ All sample columns found in ORDERS_UNIFIED!")
            
        return True
        
    except Exception as e:
        print(f"❌ Error in column comparison test: {e}")
        return False

def main():
    """Run all tests"""
    
    print("🚀 ORDERS_UNIFIED Diagnostic Test")
    print("=" * 60)
    
    # Test 1: Basic connection and column access
    test1_success = test_orders_unified_connection()
    
    if test1_success:
        # Test 2: Sample column comparison
        test2_success = test_sample_column_comparison()
        
        if test1_success and test2_success:
            print(f"\n🎉 All tests passed! ORDERS_UNIFIED connection is working correctly.")
            print(f"💡 If the orchestrator still shows issues, the problem may be:")
            print(f"   - Timing of when the comparison runs")
            print(f"   - Console output formatting")
            print(f"   - Summary aggregation logic")
        else:
            print(f"\n⚠️  Some tests failed. Check the errors above.")
    else:
        print(f"\n❌ Basic connection test failed. Cannot proceed with further tests.")
        print(f"💡 Possible issues:")
        print(f"   - ORDERS_UNIFIED table doesn't exist in 'orders' database")
        print(f"   - Database connection configuration issue")
        print(f"   - Database permission issues")

if __name__ == "__main__":
    main()
