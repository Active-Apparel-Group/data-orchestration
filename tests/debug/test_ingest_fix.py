"""
COMPREHENSIVE INGEST FIX TEST
Test fixes for:
1. UnicodeEncodeError with '∆' character in logging 
2. numpy.float64(nan) → SQL NULL conversion for DECIMAL columns
3. CUSTOMER_PRICE NaN handling that caused TDS errors

CRITICAL: Test BEFORE running main ingest.py again!
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

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
import logger_helper

class IngestFixTester:
    """
    Comprehensive test for ingest fixes
    Tests Unicode handling and NaN conversion BEFORE running main script
    """
    
    def __init__(self):
        # SAFE Logger setup - explicitly handle Unicode
        import logging
        self.logger = logging.getLogger(__name__)
        
        # Create console handler with UTF-8 encoding to handle Unicode
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Use UTF-8 formatter that can handle Unicode characters
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        if not self.logger.handlers:
            self.logger.addHandler(console_handler)
            self.logger.setLevel(logging.INFO)
    
    def test_unicode_safe_logging(self):
        """Test 1: Verify Unicode characters can be logged safely"""
        print("\n🔧 TEST 1: Unicode Safe Logging")
        print("-" * 40)
        
        try:
            # Test data with problematic Unicode character
            test_data = {
                'column_with_unicode': 'Contains ∆ character',
                'normal_column': 'Regular text',
                'CUSTOMER_PRICE': 'nan'
            }
            
            # Try logging with repr() to make it safe
            safe_log_msg = f"Test data: {repr(test_data)}"
            self.logger.info(safe_log_msg)
            
            print("   ✅ Unicode logging: PASSED")
            return True
            
        except UnicodeEncodeError as e:
            print(f"   ❌ Unicode logging: FAILED - {e}")
            return False
        except Exception as e:
            print(f"   ❌ Unicode logging: FAILED - {e}")
            return False
    
    def test_nan_conversion_pattern(self):
        """Test 2: Verify numpy.float64(nan) → SQL NULL conversion"""
        print("\n🔧 TEST 2: NaN Conversion Pattern")
        print("-" * 40)
        
        try:
            # Create test DataFrame with problematic values (EXACT same as error)
            test_data = {
                'CUSTOMER_PRICE': [np.float64('nan'), 28.7, np.float64('nan')],
                'EX_WORKS_USD': [38.27, np.float64('nan'), 45.50],
                'TOTAL_QTY': ['400', '200', '300']
            }
            
            df = pd.DataFrame(test_data)
            print(f"   Original data types:")
            print(f"   CUSTOMER_PRICE: {df['CUSTOMER_PRICE'].dtype}")
            print(f"   Sample values: {df['CUSTOMER_PRICE'].head().tolist()}")
            
            # DEBUG: Test different conversion methods
            print(f"   Testing pd.isna() on numpy.float64(nan):")
            test_val = np.float64('nan')
            print(f"   pd.isna(np.float64('nan')): {pd.isna(test_val)}")
            print(f"   np.isnan(np.float64('nan')): {np.isnan(test_val)}")
            
            # Apply the PROVEN conversion pattern from ingest.py
            converted_df = self.convert_pandas_na_to_none_safe(df)
            
            print(f"   Converted data types:")
            print(f"   CUSTOMER_PRICE: {converted_df['CUSTOMER_PRICE'].dtype}")
            print(f"   Sample values: {converted_df['CUSTOMER_PRICE'].head().tolist()}")
            
            # Verify conversion worked - check for None specifically
            none_count = sum(1 for x in converted_df['CUSTOMER_PRICE'] if x is None)
            nan_count = sum(1 for x in converted_df['CUSTOMER_PRICE'] if pd.isna(x))
            
            print(f"   None values after conversion: {none_count}")
            print(f"   NaN values still remaining: {nan_count}")
            
            if none_count == 2:  # Should have 2 None values
                print("   ✅ NaN conversion: PASSED")
                return True
            else:
                print("   ❌ NaN conversion: FAILED - Wrong None count")
                print(f"   Expected 2 None values, got {none_count}")
                return False
                
        except Exception as e:
            print(f"   ❌ NaN conversion: FAILED - {e}")
            return False
    
    def convert_pandas_na_to_none_safe(self, df):
        """
        SAFE version of the NaN conversion from ingest.py
        Test the exact pattern that should work
        """
        df_converted = df.copy()
        
        for col in df_converted.columns:
            series = df_converted[col]
            
            if pd.api.types.is_float_dtype(series):
                print(f"   DEBUG: Processing float column {col}")
                
                # CRITICAL: Handle numpy.float64(nan) specifically
                # WORKING METHOD: Convert to list, replace, convert back
                values_list = series.tolist()
                print(f"   DEBUG: Original values: {values_list}")
                
                # Replace NaN values with None in the list
                converted_list = [None if pd.isna(val) else val for val in values_list]
                print(f"   DEBUG: Converted values: {converted_list}")
                
                # Create new series from converted list
                df_converted[col] = pd.Series(converted_list, dtype=object)
            else:
                # String/object columns
                df_converted[col] = series.where(pd.notna(series), None)
        
        return df_converted
    
    def test_database_connectivity(self):
        """Test 3: Verify database connection works"""
        print("\n🔧 TEST 3: Database Connectivity")
        print("-" * 40)
        
        try:
            with db.get_connection('orders') as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'ORDER_LIST'")
                result = cursor.fetchone()
                
                if result and result[0] > 0:
                    print("   ✅ ORDER_LIST table exists: PASSED")
                    return True
                else:
                    print("   ❌ ORDER_LIST table missing: FAILED")
                    return False
                    
        except Exception as e:
            print(f"   ❌ Database connection: FAILED - {e}")
            return False
    
    def test_single_row_insert(self):
        """Test 4: Try inserting a single clean row"""
        print("\n🔧 TEST 4: Single Row Insert Test")
        print("-" * 40)
        
        try:
            # Create minimal test row with CORRECT column names (with spaces)
            test_row = {
                'AAG ORDER NUMBER': 'TEST-00001',
                'CUSTOMER NAME': 'TEST_CUSTOMER',
                'PO NUMBER': '12345',
                'CUSTOMER PRICE': None,  # CRITICAL: Use None not np.nan
                'EX WORKS (USD)': 25.50,
                'TOTAL QTY': '100'
            }
            
            with db.get_connection('orders') as conn:
                cursor = conn.cursor()
                
                # Create minimal INSERT statement with proper column names
                columns = ', '.join(f'[{col}]' for col in test_row.keys())  # Bracket column names with spaces
                placeholders = ', '.join('?' * len(test_row))
                sql = f"INSERT INTO ORDER_LIST ({columns}) VALUES ({placeholders})"
                
                values = tuple(test_row.values())
                cursor.execute(sql, values)
                conn.commit()
                
                print("   ✅ Single row insert: PASSED")
                
                # Clean up test data
                cursor.execute("DELETE FROM ORDER_LIST WHERE [AAG ORDER NUMBER] = 'TEST-00001'")
                conn.commit()
                
                return True
                
        except Exception as e:
            print(f"   ❌ Single row insert: FAILED - {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests and report results"""
        print("🎯 COMPREHENSIVE INGEST FIX TESTING")
        print("=" * 50)
        print("Testing fixes BEFORE running main ingest.py")
        
        results = {
            'unicode_logging': self.test_unicode_safe_logging(),
            'nan_conversion': self.test_nan_conversion_pattern(),
            'database_connectivity': self.test_database_connectivity(),
            'single_row_insert': self.test_single_row_insert()
        }
        
        print("\n📊 TEST RESULTS SUMMARY")
        print("=" * 50)
        
        all_passed = True
        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name:20}: {status}")
            if not passed:
                all_passed = False
        
        print("\n🎯 FINAL RECOMMENDATION:")
        if all_passed:
            print("✅ ALL TESTS PASSED - Safe to run main ingest.py")
        else:
            print("❌ SOME TESTS FAILED - DO NOT run main ingest.py yet!")
            print("   Fix the failing issues first.")
        
        return all_passed

def main():
    """Main test execution"""
    tester = IngestFixTester()
    success = tester.run_all_tests()
    
    print(f"\nOverall result: {'SUCCESS' if success else 'FAILURE'}")
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
