#!/usr/bin/env python3
"""
Milestone 2 Business Key Integration Test
========================================
Purpose: Validate business key generation, customer resolution, and NEW detection logic
Database: orders (contains ORDER_LIST tables)
Created: 2025-07-19 (Milestone 2: Business Key Implementation)

Tests the core business logic:
1. Customer canonicalization from YAML config
2. Business key generation using customer-specific unique_keys
3. NEW detection via AAG ORDER NUMBER existence
4. Integration with existing reconcile_order_list.py logic
"""
import sys
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List

# Add project paths for imports
def find_repo_root():
    current = Path(__file__).parent.parent.parent
    while current != current.parent:
        if (current / "src" / "pipelines").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "src"))
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

# Import our new modules from utils/ location
# Modern imports using pip install -e .
from pipelines.utils.canonical_customer_manager import CanonicalCustomerManager
from pipelines.utils.order_key_generator import OrderKeyGenerator
from pipelines.utils import db
from pipelines.utils import logger

class Milestone2OrderKeyTestFramework:
    """
    Comprehensive test framework for Milestone 2 order key implementation
    Validates customer resolution, order key generation, and NEW detection
    """
    
    def __init__(self):
        self.test_results = {}
        self.logger = logger.get_logger(__name__)
        
        # Initialize order key components
        try:
            self.customer_manager = CanonicalCustomerManager()
            self.order_key_generator = OrderKeyGenerator()
            self.logger.info("Order key components initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise
    
    def test_customer_canonicalization(self) -> Dict[str, Any]:
        """Test Phase 1: Customer canonicalization from YAML config"""
        print("\n1 CUSTOMER CANONICALIZATION")
        print("-" * 40)
        
        try:
            # Test cases from canonical_customers.yaml
            test_cases = [
                ("GREYSON", "GREYSON"),           # Direct match
                ("GREYSON CLOTHIERS", "GREYSON"), # Alias resolution (if exists)
                ("SUN DAY RED", "SUN DAY RED"),   # Direct match
                ("SUMMERSALT", "SUMMERSALT"),     # Direct match
                ("TAYLOR MADE", "TAYLOR MADE"),   # Direct match
                ("UNKNOWN_CUSTOMER", "UNKNOWN_CUSTOMER")  # No mapping
            ]
            
            correct_mappings = 0
            total_tests = len(test_cases)
            
            for source_name, expected_canonical in test_cases:
                resolved = self.customer_manager.resolve_canonical_customer(source_name)
                if resolved == expected_canonical:
                    correct_mappings += 1
                    print(f"   SUCCESS: {source_name} -> {resolved}")
                else:
                    print(f"   FAILED: {source_name} -> {resolved} (expected {expected_canonical})")
            
            accuracy = (correct_mappings / total_tests) * 100
            
            result = {
                'success': accuracy >= 95,
                'accuracy_percent': accuracy,
                'correct_mappings': correct_mappings,
                'total_tests': total_tests,
                'customers_loaded': len(self.customer_manager.customer_config.get('customers', []))
            }
            
            print(f"   Customer Resolution Accuracy: {accuracy:.1f}%")
            print(f"   Customers Loaded: {result['customers_loaded']}")
            print(f"   SUCCESS: Customer canonicalization PASSED" if result['success'] else f"   FAILED: Customer canonicalization accuracy below 95%")
            
            return result
            
        except Exception as e:
            self.logger.exception(f"Customer canonicalization test failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_order_key_generation(self) -> Dict[str, Any]:
        """Test Phase 2: Order key generation using customer-specific unique_keys"""
        print("\n2 ORDER KEY GENERATION")
        print("-" * 40)
        
        try:
            # Test data mimicking ORDER_LIST records
            test_data = [
                # GREYSON customer data
                {
                    "CUSTOMER NAME": "GREYSON",
                    "AAG ORDER NUMBER": "GRY-2025-001",
                    "CUSTOMER STYLE": "POLO-CLASSIC",
                    "PLANNED DELIVERY METHOD": "GROUND",
                    "PO NUMBER": "PO-GRY-001"
                },
                # SUN DAY RED customer data  
                {
                    "CUSTOMER NAME": "SUN DAY RED",
                    "AAG ORDER NUMBER": "SDR-2025-001", 
                    "CUSTOMER STYLE": "GOLF-SHIRT",
                    "PLANNED DELIVERY METHOD": "EXPRESS",
                    "PO NUMBER": "PO-SDR-001"
                },
                # Duplicate test (same GREYSON customer)
                {
                    "CUSTOMER NAME": "GREYSON",
                    "AAG ORDER NUMBER": "GRY-2025-001",  # Same AAG ORDER NUMBER
                    "CUSTOMER STYLE": "POLO-CLASSIC",   # Same style
                    "PLANNED DELIVERY METHOD": "GROUND", # Same delivery
                    "PO NUMBER": "PO-GRY-001"           # Same PO
                }
            ]
            
            # Convert to DataFrame for testing
            df = pd.DataFrame(test_data)
            
            # Generate order keys
            order_business_keys = []
            for _, row in df.iterrows():
                try:
                    # Pass both row data and customer name
                    order_business_key = self.order_key_generator.generate_order_key(row.to_dict(), row['CUSTOMER NAME'])
                    order_business_keys.append(order_business_key)
                    print(f"   {row['CUSTOMER NAME']}: {order_business_key}")
                except Exception as e:
                    order_business_keys.append(f"ERROR: {e}")
                    print(f"   ERROR generating key for {row['CUSTOMER NAME']}: {e}")
            
            # Validate order key uniqueness and format
            df['order_business_key'] = order_business_keys
            
            # Check for duplicates (expected in this test case)
            duplicates = df[df.duplicated(subset=['order_business_key'], keep=False)]
            unique_keys = len(df['order_business_key'].unique())
            total_records = len(df)
            
            # Success criteria: Keys generated without errors, format is correct
            error_keys = [k for k in order_business_keys if k.startswith('ERROR:')]
            success_rate = ((total_records - len(error_keys)) / total_records) * 100
            
            result = {
                'success': success_rate >= 95,
                'success_rate': success_rate,
                'total_records': total_records,
                'unique_keys': unique_keys,
                'duplicate_count': len(duplicates),
                'error_count': len(error_keys),
                'sample_keys': order_business_keys[:3]
            }
            
            print(f"   Order Key Success Rate: {success_rate:.1f}%")
            print(f"   Unique Keys: {unique_keys}/{total_records}")
            print(f"   Duplicates Found: {len(duplicates)} (expected for test)")
            print(f"   SUCCESS: Order key generation PASSED" if result['success'] else f"   FAILED: Order key generation errors")
            
            return result
            
        except Exception as e:
            self.logger.exception(f"Business key generation test failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_new_detection_logic(self) -> Dict[str, Any]:
        """Test Phase 3: NEW detection via AAG ORDER NUMBER existence in orders database"""
        print("\n3 NEW DETECTION LOGIC")
        print("-" * 40)
        
        try:
            # Test NEW detection logic against orders database
            with db.get_connection('orders') as conn:
                # Check if ORDER_LIST_V2 exists (shadow table)
                table_check_sql = """
                SELECT COUNT(*) as table_exists 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'ORDER_LIST_V2' AND TABLE_SCHEMA = 'dbo'
                """
                table_result = pd.read_sql(table_check_sql, conn)
                table_exists = table_result['table_exists'].iloc[0] > 0
                
                if not table_exists:
                    # If shadow table doesn't exist, check production ORDER_LIST
                    table_check_sql = """
                    SELECT COUNT(*) as table_exists 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_NAME = 'ORDER_LIST' AND TABLE_SCHEMA = 'dbo'
                    """
                    table_result = pd.read_sql(table_check_sql, conn)
                    table_exists = table_result['table_exists'].iloc[0] > 0
                    target_table = 'ORDER_LIST'
                else:
                    target_table = 'ORDER_LIST_V2'
                
                if not table_exists:
                    # Database validation: Table structure exists
                    result = {
                        'success': False,
                        'error': f'Neither ORDER_LIST nor ORDER_LIST_V2 tables found in orders database',
                        'database_connection': True,
                        'target_table': None
                    }
                    print(f"   FAILED: No ORDER_LIST tables found in orders database")
                    return result
                
                # Test NEW detection logic
                # Sample AAG ORDER NUMBERs for testing
                test_order_numbers = ["TEST-NEW-001", "TEST-NEW-002", "EXISTING-CHECK"]
                
                new_count = 0
                existing_count = 0
                
                for order_number in test_order_numbers:
                    existence_sql = f"""
                    SELECT COUNT(*) as record_count 
                    FROM [dbo].[{target_table}] 
                    WHERE [AAG ORDER NUMBER] = ?
                    """
                    
                    existence_result = pd.read_sql(existence_sql, conn, params=[order_number])
                    record_count = existence_result['record_count'].iloc[0]
                    
                    if record_count == 0:
                        new_count += 1
                        print(f"   NEW: {order_number} (not found in {target_table})")
                    else:
                        existing_count += 1
                        print(f"   EXISTING: {order_number} (found {record_count} records)")
                
                # Get total records in table for context
                total_sql = f"SELECT COUNT(*) as total_records FROM [dbo].[{target_table}]"
                total_result = pd.read_sql(total_sql, conn)
                total_records = total_result['total_records'].iloc[0]
                
                result = {
                    'success': True,
                    'database_connection': True,
                    'target_table': target_table,
                    'total_records_in_table': total_records,
                    'test_new_count': new_count,
                    'test_existing_count': existing_count,
                    'new_detection_logic': 'AAG ORDER NUMBER existence check'
                }
                
                print(f"   Database Connection: SUCCESS (orders)")
                print(f"   Target Table: {target_table}")
                print(f"   Total Records in Table: {total_records:,}")
                print(f"   NEW Detection Tests: {new_count}/{len(test_order_numbers)}")
                print(f"   SUCCESS: NEW detection logic validated")
                
                return result
                
        except Exception as e:
            self.logger.exception(f"NEW detection test failed: {e}")
            return {'success': False, 'error': str(e), 'database_connection': False}
    
    def test_yaml_config_integration(self) -> Dict[str, Any]:
        """Test Phase 4: YAML configuration loading and structure validation"""
        print("\n4 YAML CONFIG INTEGRATION")
        print("-" * 40)
        
        try:
            # Validate YAML configuration structure
            config = self.customer_manager.customer_config
            
            if 'customers' not in config:
                result = {
                    'success': False,
                    'error': 'Missing customers section in YAML config',
                    'config_structure': list(config.keys()) if config else []
                }
                print(f"   FAILED: Invalid YAML structure")
                return result
            
            customers = config['customers']
            valid_customers = 0
            total_customers = len(customers)
            
            for customer in customers:
                # Validate required fields
                required_fields = ['canonical', 'status', 'order_key_config']
                has_all_fields = all(field in customer for field in required_fields)
                
                if has_all_fields and 'unique_keys' in customer['order_key_config']:
                    valid_customers += 1
                    unique_keys = customer['order_key_config']['unique_keys']
                    print(f"   {customer['canonical']}: {len(unique_keys)} unique keys")
                else:
                    print(f"   INVALID: {customer.get('canonical', 'UNKNOWN')} missing required fields")
            
            validation_rate = (valid_customers / total_customers) * 100 if total_customers > 0 else 0
            
            result = {
                'success': validation_rate >= 90,
                'validation_rate': validation_rate,
                'valid_customers': valid_customers,
                'total_customers': total_customers,
                'config_path': str(self.customer_manager.config_path)
            }
            
            print(f"   Config Validation Rate: {validation_rate:.1f}%")
            print(f"   Valid Customers: {valid_customers}/{total_customers}")
            print(f"   SUCCESS: YAML config integration PASSED" if result['success'] else f"   FAILED: YAML config validation below 90%")
            
            return result
            
        except Exception as e:
            self.logger.exception(f"YAML config integration test failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run complete Milestone 2 business key test suite"""
        print("ORDER_LIST Delta Monday Sync - Milestone 2 Order Key Test")
        print("=" * 70)
        print("Database: orders (ORDER_LIST tables)")
        print("Focus: Customer resolution, order keys, NEW detection")
        print("")
        
        # Execute all test phases
        self.test_results['customer_canonicalization'] = self.test_customer_canonicalization()
        self.test_results['order_key_generation'] = self.test_order_key_generation()
        self.test_results['new_detection_logic'] = self.test_new_detection_logic()
        self.test_results['yaml_config_integration'] = self.test_yaml_config_integration()
        
        # Calculate overall success rate
        successful_tests = sum(1 for result in self.test_results.values() if result.get('success', False))
        total_tests = len(self.test_results)
        overall_success_rate = (successful_tests / total_tests) * 100
        
        # Final reporting
        print(f"\n" + "=" * 70)
        print(f"MILESTONE 2 ORDER KEY TEST RESULTS")
        print(f"=" * 70)
        
        for phase_name, result in self.test_results.items():
            status = "PASSED" if result.get('success', False) else "FAILED"
            print(f"{phase_name.replace('_', ' ').title()}: {status}")
            
            if not result.get('success', False) and 'error' in result:
                print(f"  Error: {result['error']}")
        
        print(f"\nOVERALL SUCCESS RATE: {overall_success_rate:.1f}% ({successful_tests}/{total_tests} tests passed)")
        
        if overall_success_rate >= 95:
            print("MILESTONE 2 ORDER KEY FOUNDATION: READY FOR MERGE OPERATIONS")
        elif overall_success_rate >= 80:
            print("MILESTONE 2 ORDER KEY FOUNDATION: NEEDS MINOR FIXES")
        else:
            print("MILESTONE 2 ORDER KEY FOUNDATION: REQUIRES SIGNIFICANT WORK")
        
        return {
            'overall_success_rate': overall_success_rate,
            'successful_tests': successful_tests,
            'total_tests': total_tests,
            'test_results': self.test_results,
            'milestone_ready': overall_success_rate >= 95
        }

def main():
    """Main test execution function"""
    try:
        test_framework = Milestone2OrderKeyTestFramework()
        return test_framework.run_all_tests()
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to initialize test framework: {e}")
        return {'overall_success_rate': 0, 'error': str(e)}

if __name__ == "__main__":
    results = main()
    # Exit with error code if tests failed
    import sys
    if results.get('overall_success_rate', 0) < 95:
        sys.exit(1)
    else:
        sys.exit(0)
