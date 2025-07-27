"""
Order Key Generator Test
========================
Purpose: Simple validation test for order key generation functionality
Location: tests/debug/test_order_key_generator.py
Created: 2025-07-19

This test validates the core functionality of the OrderKeyGenerator class following
the testing framework standards from test.instructions.md.
"""
import sys
from pathlib import Path
import pandas as pd

# Add src to path for imports
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils.order_key_generator import create_order_key_generator

class OrderKeyGeneratorTestFramework:
    """
    Test framework for order key generator validation
    """
    
    def __init__(self):
        self.test_results = {}
        print("ORDER_LIST Order Key Generator - Validation Test")
        print("=" * 50)
    
    def test_phase_1_initialization(self):
        """Test Phase 1: Generator Initialization"""
        print("\n1. ORDER KEY GENERATOR INITIALIZATION")
        print("-" * 40)
        
        try:
            # Initialize generator
            generator = create_order_key_generator()
            
            # Validate initialization
            validation = {
                'generator_created': generator is not None,
                'config_loaded': hasattr(generator, 'customer_config'),
                'lookup_built': hasattr(generator, 'customer_lookup'),
                'generated_keys_set': hasattr(generator, 'generated_keys')
            }
            
            success_count = sum(validation.values())
            total_count = len(validation)
            success_rate = (success_count / total_count) * 100
            
            print(f"Generator initialization: {'SUCCESS' if success_rate == 100 else 'PARTIAL'}")
            print(f"Success rate: {success_rate:.1f}% ({success_count}/{total_count})")
            
            for check, result in validation.items():
                status = 'PASS' if result else 'FAIL'
                print(f"  {check}: {status}")
            
            return {
                'success': success_rate >= 95,
                'success_rate': success_rate,
                'validation': validation,
                'generator': generator
            }
            
        except Exception as e:
            print(f"Generator initialization FAILED: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_phase_2_key_generation(self, generator):
        """Test Phase 2: Single Key Generation"""
        print("\n2. SINGLE ORDER KEY GENERATION")
        print("-" * 40)
        
        try:
            # Test data for key generation
            test_row = {
                'AAG ORDER NUMBER': 'TEST-001',
                'CUSTOMER': 'GREYSON',
                'CUSTOMER STYLE': 'TEST-STYLE-001',
                'PO NUMBER': '9999',
                'ORDER TYPE': 'DEVELOPMENT',
                'ORDER QTY': 100
            }
            
            # Generate order business key
            customer_name = test_row['CUSTOMER']
            order_business_key = generator.generate_order_key(test_row, customer_name)
            
            # Generate content hash
            hash_columns = ['CUSTOMER STYLE', 'ORDER QTY', 'ORDER TYPE']
            row_hash = generator.generate_row_hash(test_row, hash_columns)
            
            # Test NEW detection
            existing_orders = set()  # Empty set = all orders are new
            is_new = generator.is_new_order(test_row['AAG ORDER NUMBER'], existing_orders)
            
            # Validation
            validation = {
                'key_generated': bool(order_business_key),
                'key_has_customer': 'GREYSON' in order_business_key,
                'key_has_order_number': 'TEST-001' in order_business_key,
                'hash_generated': bool(row_hash),
                'new_detection_works': is_new == True
            }
            
            success_count = sum(validation.values())
            total_count = len(validation)
            success_rate = (success_count / total_count) * 100
            
            print(f"Key generation: {'SUCCESS' if success_rate == 100 else 'PARTIAL'}")
            print(f"Success rate: {success_rate:.1f}% ({success_count}/{total_count})")
            print(f"Generated key: {order_business_key}")
            print(f"Hash (first 16 chars): {row_hash[:16]}...")
            print(f"Is NEW order: {is_new}")
            
            for check, result in validation.items():
                status = 'PASS' if result else 'FAIL'
                print(f"  {check}: {status}")
            
            return {
                'success': success_rate >= 95,
                'success_rate': success_rate,
                'order_business_key': order_business_key,
                'row_hash': row_hash,
                'validation': validation
            }
            
        except Exception as e:
            print(f"Key generation FAILED: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_phase_3_dataframe_processing(self, generator):
        """Test Phase 3: DataFrame Processing"""
        print("\n3. DATAFRAME PROCESSING")
        print("-" * 40)
        
        try:
            # Create test DataFrame
            test_data = [
                {
                    'AAG ORDER NUMBER': 'NEW-001',
                    'CUSTOMER': 'GREYSON',
                    'CUSTOMER STYLE': 'STYLE-001',
                    'ORDER QTY': 500,
                    'ORDER TYPE': 'PRODUCTION'
                },
                {
                    'AAG ORDER NUMBER': 'NEW-002',
                    'CUSTOMER': 'TRACKSMITH',  # This will map to 'TRACK SMITH'
                    'CUSTOMER STYLE': 'STYLE-002',
                    'ORDER QTY': 300,
                    'ORDER TYPE': 'DEVELOPMENT'
                },
                {
                    'AAG ORDER NUMBER': 'EXISTING-001',
                    'CUSTOMER': 'GREYSON',
                    'CUSTOMER STYLE': 'STYLE-003',
                    'ORDER QTY': 200,
                    'ORDER TYPE': 'SAMPLE'
                }
            ]
            
            df = pd.DataFrame(test_data)
            
            # Process DataFrame
            hash_columns = ['CUSTOMER STYLE', 'ORDER QTY', 'ORDER TYPE']
            existing_orders = {'EXISTING-001'}  # Simulate one existing order
            
            # Reset generator keys to avoid false duplicates
            generator.generated_keys = set()
            generator.duplicate_count = 0
            
            result_df = generator.process_dataframe(df, hash_columns, existing_orders)
            
            # Validate results
            required_columns = ['order_business_key', 'row_hash', 'sync_state']
            columns_present = all(col in result_df.columns for col in required_columns)
            
            # Count sync states
            new_count = len(result_df[result_df['sync_state'] == 'NEW'])
            existing_count = len(result_df[result_df['sync_state'] == 'EXISTING'])
            error_count = len(result_df[result_df['sync_state'] == 'ERROR'])
            
            validation = {
                'columns_added': columns_present,
                'correct_new_count': new_count == 2,  # NEW-001, NEW-002
                'correct_existing_count': existing_count == 1,  # EXISTING-001
                'no_errors': error_count == 0,
                'all_keys_generated': result_df['order_business_key'].notna().all()
            }
            
            success_count = sum(validation.values())
            total_count = len(validation)
            success_rate = (success_count / total_count) * 100
            
            print(f"DataFrame processing: {'SUCCESS' if success_rate == 100 else 'PARTIAL'}")
            print(f"Success rate: {success_rate:.1f}% ({success_count}/{total_count})")
            print(f"Records processed: {len(result_df)}")
            print(f"NEW records: {new_count}")
            print(f"EXISTING records: {existing_count}")
            print(f"ERROR records: {error_count}")
            
            for check, result in validation.items():
                status = 'PASS' if result else 'FAIL'
                print(f"  {check}: {status}")
            
            # Show sample results
            print("\nSample Results:")
            sample_cols = ['CUSTOMER', 'AAG ORDER NUMBER', 'order_business_key', 'sync_state']
            print(result_df[sample_cols].to_string(index=False))
            
            return {
                'success': success_rate >= 95,
                'success_rate': success_rate,
                'processed_records': len(result_df),
                'new_records': new_count,
                'existing_records': existing_count,
                'validation': validation
            }
            
        except Exception as e:
            print(f"DataFrame processing FAILED: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_all_tests(self):
        """Run all test phases"""
        # Phase 1: Initialization
        phase1_result = self.test_phase_1_initialization()
        self.test_results['phase1'] = phase1_result
        
        if not phase1_result['success']:
            print(f"\nOVERALL RESULT: FAILED (Phase 1 initialization failed)")
            return
        
        generator = phase1_result['generator']
        
        # Phase 2: Key Generation  
        phase2_result = self.test_phase_2_key_generation(generator)
        self.test_results['phase2'] = phase2_result
        
        # Phase 3: DataFrame Processing
        phase3_result = self.test_phase_3_dataframe_processing(generator)
        self.test_results['phase3'] = phase3_result
        
        # Overall results
        successful_phases = sum(1 for phase in self.test_results.values() if phase['success'])
        total_phases = len(self.test_results)
        overall_success_rate = (successful_phases / total_phases) * 100
        
        print(f"\n" + "=" * 50)
        print(f"OVERALL SUCCESS RATE: {overall_success_rate:.1f}% ({successful_phases}/{total_phases} tests passed)")
        
        if overall_success_rate >= 95:
            print("ORDER KEY GENERATOR: READY FOR INTEGRATION")
        elif overall_success_rate >= 80:
            print("ORDER KEY GENERATOR: MOSTLY FUNCTIONAL - MINOR ISSUES")
        else:
            print("ORDER KEY GENERATOR: NEEDS ATTENTION")
        
        return self.test_results

if __name__ == "__main__":
    # Run the test framework
    test_framework = OrderKeyGeneratorTestFramework()
    results = test_framework.run_all_tests()
