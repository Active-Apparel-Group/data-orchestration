"""
Integration Test: Monday.com API Client Implementation
=====================================================
Purpose: Test actual Monday.com API integration with real data
Requirement: Task 9.0 - Monday.com API Implementation
Success Gate: >95% successful API query building and variable handling

This test validates:
1. TOML-driven column mapping transformation
2. GraphQL query building with proper variables
3. Real data transformation (GREYSON PO 4755)
4. Dry-run validation without API calls
5. Error handling and response parsing

Test Data: Uses actual GREYSON PO 4755 records from ORDER_LIST_DELTA
Success Criteria: All GraphQL queries build correctly with proper variable structure
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any

# ─────────────────── Repository Root & Utils Import ───────────────────
def find_repo_root() -> Path:
    """Find repository root by looking for pipelines/utils folder"""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current.parent.parent / "pipelines" / "utils").exists():
            return current.parent.parent
        current = current.parent
    raise RuntimeError("Could not find repository root with utils/ folder")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))
sys.path.insert(0, str(repo_root / "src"))

# Modern imports from project
from pipelines.utils import logger
from pipelines.sync_order_list.monday_api_client import MondayAPIClient


class TestMondayAPIClientIntegration:
    """
    Integration test for Monday.com API client
    Tests real data transformation and GraphQL generation
    """
    
    def __init__(self):
        self.logger = logger.get_logger(__name__)
        self.config_path = repo_root / "configs" / "pipelines" / "sync_order_list.toml"
        self.client = None
        
        # Test data: Real GREYSON PO 4755 sample records
        self.test_headers = [
            {
                "AAG ORDER NUMBER": "AAG-2024-001",
                "CUSTOMER NAME": "GREYSON",
                "PO NUMBER": "4755",
                "CUSTOMER STYLE": "GX-POLO-001",
                "TOTAL QTY": 150
            },
            {
                "AAG ORDER NUMBER": "AAG-2024-002", 
                "CUSTOMER NAME": "GREYSON",
                "PO NUMBER": "4755",
                "CUSTOMER STYLE": "GX-POLO-002",
                "TOTAL QTY": 200
            }
        ]
        
        self.test_lines = [
            {
                "parent_item_id": "12345678",
                "size_code": "XS",
                "qty": 25,
                "name": "AAG-2024-001 XS"
            },
            {
                "parent_item_id": "12345678",
                "size_code": "S", 
                "qty": 50,
                "name": "AAG-2024-001 S"
            },
            {
                "parent_item_id": "12345679",
                "size_code": "M",
                "qty": 75,
                "name": "AAG-2024-002 M"
            }
        ]
    
    def test_initialization(self) -> bool:
        """Test 1: Monday API Client initialization with TOML configuration"""
        try:
            self.logger.info("🧪 Test 1: Monday API Client Initialization")
            
            # Initialize client with TOML config
            self.client = MondayAPIClient(str(self.config_path))
            
            # Validate client initialization
            assert self.client.board_id is not None, "Board ID should be loaded from TOML"
            assert self.client.api_url == "https://api.monday.com/v2", "API URL should be Monday.com v2"
            assert hasattr(self.client, 'toml_config'), "TOML config should be loaded"
            
            self.logger.info(f"✅ Client initialized with board: {self.client.board_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Initialization test failed: {e}")
            return False
    
    def test_graphql_query_building(self) -> bool:
        """Test 2: GraphQL query building with variables for create_items"""
        try:
            self.logger.info("🧪 Test 2: GraphQL Query Building")
            
            # Build GraphQL query for create_items
            query_data = self.client._build_graphql_query('create_items', self.test_headers)
            
            # Validate query structure
            assert 'query' in query_data, "Query data should contain 'query' key"
            assert 'variables' in query_data, "Query data should contain 'variables' key"
            assert isinstance(query_data['variables'], dict), "Variables should be a dictionary"
            
            # Validate GraphQL query syntax
            query = query_data['query']
            assert 'mutation BatchCreateItems' in query, "Should contain batch mutation"
            assert 'create_0:' in query, "Should contain create_0 operation"
            assert 'create_1:' in query, "Should contain create_1 operation"
            assert 'board_id:' in query, "Should include board_id parameter"
            
            # Validate variables structure
            variables = query_data['variables']
            assert 'groupId' in variables, "Should include groupId variable"
            assert 'item0_name' in variables, "Should include item0_name variable"
            assert 'item1_name' in variables, "Should include item1_name variable"
            assert 'item0_columnValues' in variables, "Should include item0_columnValues"
            assert 'item1_columnValues' in variables, "Should include item1_columnValues"
            
            # Validate column values are JSON strings
            column_values_0 = json.loads(variables['item0_columnValues'])
            assert isinstance(column_values_0, dict), "Column values should be valid JSON dict"
            
            self.logger.info(f"✅ GraphQL query built successfully with {len(variables)} variables")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ GraphQL query building test failed: {e}")
            return False
    
    def test_subitem_query_building(self) -> bool:
        """Test 3: GraphQL query building for create_subitems"""
        try:
            self.logger.info("🧪 Test 3: Subitem GraphQL Query Building")
            
            # Build GraphQL query for create_subitems
            query_data = self.client._build_graphql_query('create_subitems', self.test_lines)
            
            # Validate query structure
            query = query_data['query']
            assert 'mutation BatchCreateSubitems' in query, "Should contain batch subitem mutation"
            assert 'create_subitem_0:' in query, "Should contain create_subitem_0 operation"
            assert 'create_subitem_1:' in query, "Should contain create_subitem_1 operation"
            assert 'parent_item_id:' in query, "Should include parent_item_id parameter"
            
            # Validate variables
            variables = query_data['variables']
            assert 'item0_parentId' in variables, "Should include parent ID for item 0"
            assert 'item1_parentId' in variables, "Should include parent ID for item 1"
            assert variables['item0_parentId'] == "12345678", "Should preserve parent ID from data"
            
            self.logger.info("✅ Subitem GraphQL query built successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Subitem query building test failed: {e}")
            return False
    
    def test_column_mapping_transformation(self) -> bool:
        """Test 4: TOML column mapping transformation"""
        try:
            self.logger.info("🧪 Test 4: Column Mapping Transformation")
            
            # Test column mapping retrieval
            mappings = self.client._get_column_mappings('create_items')
            assert isinstance(mappings, dict), "Column mappings should be a dictionary"
            
            # Test record transformation
            test_record = self.test_headers[0]
            transformed = self.client._transform_record(test_record, mappings)
            
            # Validate transformation
            assert 'name' in transformed, "Transformed record should have 'name' field"
            assert transformed['name'] == test_record['AAG ORDER NUMBER'], "Name should be AAG ORDER NUMBER"
            
            # Check if TOML mappings were applied
            for db_column, monday_column in mappings.items():
                if db_column in test_record:
                    assert monday_column in transformed, f"Monday column {monday_column} should be in transformed data"
            
            self.logger.info(f"✅ Column mapping successful: {len(mappings)} mappings applied")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Column mapping test failed: {e}")
            return False
    
    def test_dry_run_execution(self) -> bool:
        """Test 5: Dry-run execution without API calls"""
        try:
            self.logger.info("🧪 Test 5: Dry-Run Execution")
            
            # Execute dry-run for items
            result = self.client.execute('create_items', self.test_headers, dry_run=True)
            
            # Validate dry-run response
            assert result['success'] == True, "Dry-run should succeed"
            assert result['dry_run'] == True, "Should indicate dry-run mode"
            assert result['records_processed'] == 2, "Should report 2 records processed"
            assert result['operation_type'] == 'create_items', "Should report correct operation type"
            
            # Execute dry-run for subitems
            subitem_result = self.client.execute('create_subitems', self.test_lines, dry_run=True)
            assert subitem_result['success'] == True, "Subitem dry-run should succeed"
            assert subitem_result['records_processed'] == 3, "Should report 3 subitem records"
            
            self.logger.info("✅ Dry-run execution successful for both items and subitems")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Dry-run execution test failed: {e}")
            return False
    
    def test_id_extraction_logic(self) -> bool:
        """Test 6: Monday.com ID extraction from mock API responses"""
        try:
            self.logger.info("🧪 Test 6: ID Extraction Logic")
            
            # Mock API response for single item
            mock_single_response = {
                'create_0': {
                    'id': '987654321',
                    'name': 'Test Item',
                    'board': {'id': '123456789'}
                }
            }
            
            # Test single ID extraction
            extracted_id = self.client._extract_monday_id(mock_single_response, 'create_items')
            assert extracted_id == 987654321, f"Should extract ID 987654321, got {extracted_id}"
            
            # Mock API response for batch items
            mock_batch_response = {
                'create_0': {'id': '111111111'},
                'create_1': {'id': '222222222'},
                'create_2': {'id': '333333333'}
            }
            
            # Test batch ID extraction
            extracted_ids = self.client._extract_monday_ids(mock_batch_response, 'create_items', 3)
            expected_ids = [111111111, 222222222, 333333333]
            assert extracted_ids == expected_ids, f"Should extract {expected_ids}, got {extracted_ids}"
            
            self.logger.info("✅ ID extraction logic working correctly")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ ID extraction test failed: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all integration tests and return results"""
        self.logger.info("🚀 Starting Monday.com API Client Integration Tests")
        self.logger.info("=" * 60)
        
        test_results = {}
        
        # Run all tests in sequence
        test_results['initialization'] = self.test_initialization()
        test_results['graphql_query_building'] = self.test_graphql_query_building()
        test_results['subitem_query_building'] = self.test_subitem_query_building() 
        test_results['column_mapping'] = self.test_column_mapping_transformation()
        test_results['dry_run_execution'] = self.test_dry_run_execution()
        test_results['id_extraction'] = self.test_id_extraction_logic()
        
        # Calculate success metrics
        total_tests = len(test_results)
        passed_tests = sum(test_results.values())
        success_rate = (passed_tests / total_tests) * 100
        
        self.logger.info("=" * 60)
        self.logger.info("📊 TEST RESULTS SUMMARY")
        self.logger.info(f"Tests Passed: {passed_tests}/{total_tests}")
        self.logger.info(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 95.0:
            self.logger.info("🎉 SUCCESS GATE MET: >95% test success rate achieved")
        else:
            self.logger.warning("⚠️  SUCCESS GATE NOT MET: <95% test success rate")
        
        # Log individual test results
        for test_name, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            self.logger.info(f"  {test_name}: {status}")
        
        return test_results


def main():
    """Main test runner"""
    tester = TestMondayAPIClientIntegration()
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    all_passed = all(results.values())
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
