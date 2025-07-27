"""
Test Canonical Customer Integration with ORDER_LIST Pipeline
Purpose: Comprehensive test framework for canonical customer functionality
Location: tests/debug/test_canonical_customer_integration.py

Tests all aspects of canonical customer integration including:
- YAML configuration loading
- Customer mapping functionality
- ORDER_LIST pipeline integration
- Data validation and quality checks
"""
import sys
from pathlib import Path
from typing import Dict, Any
import pandas as pd

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
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

import db_helper as db
import logger_helper
from canonical_customer_manager import get_canonical_customer_manager
from canonical_order_list_transformer import create_canonical_order_list_transformer

class CanonicalCustomerIntegrationTest:
    """Test framework for canonical customer integration"""
    
    def __init__(self):
        self.logger = logger_helper.get_logger(__name__)
        self.canonical_manager = get_canonical_customer_manager()
        self.transformer = create_canonical_order_list_transformer()
        self.test_results = {}
    
    def test_canonical_configuration_loading(self) -> Dict[str, Any]:
        """Test Phase 1: Validate canonical customer configuration loading"""
        print("\n1️⃣ CANONICAL CONFIGURATION LOADING TEST")
        print("-" * 50)
        
        try:
            stats = self.canonical_manager.generate_mapping_stats()
            
            print(f"   📊 Configuration File: {stats['config_file']}")
            print(f"   📊 Total Canonical Customers: {stats['total_canonical_customers']}")
            print(f"   ✅ Approved Customers: {stats['approved_customers']}")
            print(f"   🔍 Review Customers: {stats['review_customers']}")
            print(f"   🔗 Total Aliases: {stats['total_aliases']}")
            
            # Test source system mappings
            print(f"   📋 Source System Mappings:")
            for source, count in stats['source_mapping_counts'].items():
                print(f"      {source}: {count} mappings")
            
            result = {
                'success': stats['total_canonical_customers'] > 0,
                'stats': stats,
                'validation_checks': {
                    'has_customers': stats['total_canonical_customers'] > 0,
                    'has_approved': stats['approved_customers'] > 0,
                    'has_aliases': stats['total_aliases'] > 0,
                    'all_source_systems': len(stats['source_mapping_counts']) == 4
                }
            }
            
            all_checks_pass = all(result['validation_checks'].values())
            print(f"   📋 Configuration Loading: {'✅ PASSED' if all_checks_pass else '❌ FAILED'}")
            result['success'] = all_checks_pass
            
            return result
            
        except Exception as e:
            self.logger.exception(f"Configuration loading test failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_canonical_mappings(self) -> Dict[str, Any]:
        """Test Phase 2: Validate specific canonical customer mappings"""
        print("\n2️⃣ CANONICAL CUSTOMER MAPPINGS TEST")
        print("-" * 50)
        
        try:
            # Test known mappings from the YAML
            test_cases = [
                # (input_name, source_system, expected_canonical)
                ('GREYSON', 'master_order_list', 'GREYSON'),
                ('GREYSON CLOTHIERS', 'master_order_list', 'GREYSON'),
                ('JOHNNIE O', 'master_order_list', 'JOHNNIE O'),
                ('RHONE', 'master_order_list', 'RHONE'),
                ('TRACK SMITH', 'master_order_list', 'TRACK SMITH'),
                ('TRACKSMITH', 'master_order_list', 'TRACK SMITH'),
                ('TITLE 9', 'master_order_list', 'TITLE NINE'),
                ('CAMILLA (AU)', 'master_order_list', 'CAMILLA'),
                ('WHITE FOX (AU)', 'master_order_list', 'WHITE FOX')
            ]
            
            mapping_results = []
            for input_name, source, expected in test_cases:
                canonical = self.canonical_manager.get_canonical_customer(input_name, source)
                success = canonical == expected
                mapping_results.append({
                    'input': input_name,
                    'source_system': source,
                    'expected': expected,
                    'actual': canonical,
                    'success': success
                })
                
                status = "✅" if success else "❌"
                print(f"   {status} '{input_name}' → '{canonical}' (expected: '{expected}')")
            
            # Test status validation
            approved_customers = self.canonical_manager.get_approved_customers()
            print(f"   📋 Approved Customers Count: {len(approved_customers)}")
            
            result = {
                'success': all(r['success'] for r in mapping_results),
                'mapping_tests': mapping_results,
                'total_tests': len(mapping_results),
                'passed_tests': sum(1 for r in mapping_results if r['success']),
                'approved_customers_count': len(approved_customers)
            }
            
            print(f"   📊 Mapping Success Rate: {result['passed_tests']}/{result['total_tests']} ({result['passed_tests']/result['total_tests']*100:.1f}%)")
            print(f"   📋 Mapping Test Result: {'✅ PASSED' if result['success'] else '❌ FAILED'}")
            
            return result
            
        except Exception as e:
            self.logger.exception(f"Canonical mappings test failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_order_list_customer_validation(self) -> Dict[str, Any]:
        """Test Phase 3: Validate ORDER_LIST customers against canonical mappings"""
        print("\n3️⃣ ORDER_LIST CUSTOMER VALIDATION")
        print("-" * 50)
        
        try:
            # Query raw ORDER_LIST tables
            with db.get_connection('orders') as conn:
                tables_query = """
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME LIKE '%_ORDER_LIST_RAW'
                ORDER BY TABLE_NAME
                """
                tables_df = pd.read_sql(tables_query, conn)
            
            raw_tables = tables_df['TABLE_NAME'].tolist()
            print(f"   📊 Found {len(raw_tables)} raw ORDER_LIST tables")
            
            # Use transformer validation
            validation_results = self.transformer.validate_canonical_customers(raw_tables)
            
            print(f"   ✅ Valid Customers: {validation_results['valid_count']}")
            print(f"   ❌ Invalid Customers: {validation_results['invalid_count']}")
            print(f"   📊 Success Rate: {validation_results['success_rate']:.1f}%")
            
            # Show detailed mappings
            for customer, canonical in validation_results['canonical_mappings'].items():
                status = validation_results['approval_status'].get(canonical, 'unknown')
                print(f"   ✅ '{customer}' → '{canonical}' (status: {status})")
            
            # Show unmapped customers
            for unmapped in validation_results['unmapped_details']:
                print(f"   ❌ '{unmapped['customer_from_table']}' → NO MAPPING")
            
            result = {
                'success': validation_results['all_valid'],
                'validation_details': validation_results,
                'success_rate': validation_results['success_rate']
            }
            
            print(f"   📋 Customer Validation: {'✅ PASSED' if result['success'] else '❌ FAILED'}")
            
            return result
            
        except Exception as e:
            self.logger.exception(f"Customer validation test failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_data_quality_validation(self) -> Dict[str, Any]:
        """Test Phase 4: Validate data quality for canonical customer tables"""
        print("\n4️⃣ DATA QUALITY VALIDATION")
        print("-" * 50)
        
        try:
            # Get sample of raw tables for validation
            with db.get_connection('orders') as conn:
                tables_query = """
                SELECT TOP 5 TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME LIKE '%_ORDER_LIST_RAW'
                ORDER BY TABLE_NAME
                """
                tables_df = pd.read_sql(tables_query, conn)
            
            raw_tables = tables_df['TABLE_NAME'].tolist()
            
            quality_results = []
            for table_name in raw_tables:
                quality_metrics = self.transformer.validate_customer_data_quality(table_name)
                quality_results.append(quality_metrics)
                
                if 'error' not in quality_metrics:
                    customer_name = table_name.replace('_ORDER_LIST_RAW', '').replace('x', '')
                    total = quality_metrics['total_records']
                    customer_completeness = quality_metrics['customer_completeness_pct']
                    
                    print(f"   📊 {customer_name}: {total} records, {customer_completeness:.1f}% customer completeness")
                else:
                    print(f"   ❌ {table_name}: Error - {quality_metrics['error']}")
            
            # Calculate overall quality metrics
            valid_results = [r for r in quality_results if 'error' not in r]
            if valid_results:
                avg_customer_completeness = sum(r['customer_completeness_pct'] for r in valid_results) / len(valid_results)
                total_records = sum(r['total_records'] for r in valid_results)
                
                print(f"   📊 Overall Average Customer Completeness: {avg_customer_completeness:.1f}%")
                print(f"   📊 Total Records Validated: {total_records}")
                
                result = {
                    'success': avg_customer_completeness >= 95.0,  # 95% threshold
                    'quality_results': quality_results,
                    'avg_customer_completeness': avg_customer_completeness,
                    'total_records': total_records,
                    'tables_validated': len(valid_results)
                }
            else:
                result = {
                    'success': False,
                    'error': 'No valid quality results obtained',
                    'quality_results': quality_results
                }
            
            print(f"   📋 Data Quality Validation: {'✅ PASSED' if result['success'] else '❌ FAILED'}")
            
            return result
            
        except Exception as e:
            self.logger.exception(f"Data quality validation test failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_customer_mapping_summary(self) -> Dict[str, Any]:
        """Test Phase 5: Generate comprehensive customer mapping summary"""
        print("\n5️⃣ CUSTOMER MAPPING SUMMARY")
        print("-" * 50)
        
        try:
            # Get all raw tables
            with db.get_connection('orders') as conn:
                tables_query = """
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME LIKE '%_ORDER_LIST_RAW'
                ORDER BY TABLE_NAME
                """
                tables_df = pd.read_sql(tables_query, conn)
            
            raw_tables = tables_df['TABLE_NAME'].tolist()
            
            # Generate mapping summary
            mapping_summary = self.transformer.get_customer_mapping_summary(raw_tables)
            
            print(f"   📊 Total Tables: {mapping_summary['total_tables']}")
            print(f"   📊 Unique Canonical Customers: {mapping_summary['unique_canonical_count']}")
            print(f"   📊 Approval Status Distribution:")
            for status, count in mapping_summary['approval_status_counts'].items():
                print(f"      {status}: {count}")
            
            # Show canonical customers
            print(f"   📋 Canonical Customers in Pipeline:")
            for canonical in sorted(mapping_summary['canonical_customers']):
                status = self.canonical_manager.get_customer_status(canonical)
                status_icon = "✅" if status == 'approved' else "🔍" if status == 'review' else "❓"
                print(f"      {status_icon} {canonical} ({status})")
            
            result = {
                'success': mapping_summary['total_tables'] > 0 and mapping_summary['unique_canonical_count'] > 0,
                'mapping_summary': mapping_summary
            }
            
            print(f"   📋 Mapping Summary: {'✅ PASSED' if result['success'] else '❌ FAILED'}")
            
            return result
            
        except Exception as e:
            self.logger.exception(f"Customer mapping summary test failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run complete canonical customer integration test suite"""
        print("🧪 CANONICAL CUSTOMER INTEGRATION TEST SUITE")
        print("=" * 60)
        
        # Run test phases
        self.test_results['configuration_loading'] = self.test_canonical_configuration_loading()
        self.test_results['canonical_mappings'] = self.test_canonical_mappings()
        self.test_results['customer_validation'] = self.test_order_list_customer_validation()
        self.test_results['data_quality'] = self.test_data_quality_validation()
        self.test_results['mapping_summary'] = self.test_customer_mapping_summary()
        
        # Generate final report
        all_passed = all(result.get('success', False) for result in self.test_results.values())
        
        print("\n📊 FINAL TEST REPORT")
        print("=" * 30)
        
        phase_names = {
            'configuration_loading': 'Configuration Loading',
            'canonical_mappings': 'Canonical Mappings',
            'customer_validation': 'Customer Validation',
            'data_quality': 'Data Quality',
            'mapping_summary': 'Mapping Summary'
        }
        
        for phase, result in self.test_results.items():
            phase_name = phase_names.get(phase, phase)
            status = "✅ PASSED" if result.get('success') else "❌ FAILED"
            print(f"{phase_name}: {status}")
            
            if 'error' in result:
                print(f"   Error: {result['error']}")
            
            # Show key metrics
            if phase == 'canonical_mappings' and 'mapping_tests' in result:
                success_rate = result['passed_tests'] / result['total_tests'] * 100
                print(f"   Success Rate: {success_rate:.1f}%")
            
            if phase == 'customer_validation' and 'success_rate' in result:
                print(f"   Success Rate: {result['success_rate']:.1f}%")
        
        overall_status = "✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED"
        print(f"\nOverall Result: {overall_status}")
        
        # Summary statistics
        if all_passed:
            print("\n🎉 CANONICAL CUSTOMER INTEGRATION READY FOR PRODUCTION!")
            print("✅ All validation checks passed")
            print("✅ Customer mappings verified")
            print("✅ Data quality validated")
            print("✅ ORDER_LIST pipeline integration tested")
        else:
            print("\n⚠️  ISSUES FOUND - REVIEW REQUIRED")
            failed_tests = [phase for phase, result in self.test_results.items() if not result.get('success')]
            print(f"❌ Failed phases: {', '.join(failed_tests)}")
        
        return {
            'overall_success': all_passed,
            'test_results': self.test_results,
            'failed_phases': [phase for phase, result in self.test_results.items() if not result.get('success')]
        }


if __name__ == "__main__":
    print("🚀 Starting Canonical Customer Integration Test Suite...")
    test_framework = CanonicalCustomerIntegrationTest()
    results = test_framework.run_all_tests()
    
    print(f"\n🏁 Test Suite Complete - Overall Success: {results['overall_success']}")
    if not results['overall_success']:
        print(f"❌ Failed Phases: {results['failed_phases']}")
        exit(1)
    else:
        print("✅ All tests passed successfully!")
        exit(0)
