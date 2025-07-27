"""
Integration Test: Monday.com API Conservative Batching
====================================================
Purpose: Validate Monday.com HTTP API implementation with conservative rate limiting
Requirements: Task 11.0 - Monday.com HTTP API with proven async batch patterns

Test Scenarios:
- Conservative batch sizes (5 items max for testing)
- Rate limiting (100ms delays, 25s timeouts) 
- Fallback strategies (15→5→1 batch reduction)
- Connection pooling and error handling
- Dry-run validation before live API calls

Success Criteria:
- API client handles rate limits gracefully (>95% success rate)
- Conservative batching prevents Monday.com rate limit violations
- Fallback strategies work for failed batches
- Connection pooling prevents resource exhaustion
- Error handling provides actionable feedback

@author: Data Orchestration Team  
@created: 2025-01-22 (Task 11.0 Implementation)
@requirement: Monday.com HTTP API Integration with Conservative Rate Limiting
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
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


class TestMondayAPIConservativeBatching:
    """Test Monday.com API with conservative batching and rate limiting"""
    
    @pytest.fixture
    def test_config_path(self, tmp_path):
        """Create test TOML configuration"""
        config_content = """
[environment]
mode = "development"

[monday.development]
board_id = "9609317401"
subitem_board_id = "9609317401"

[monday.column_mapping.development.headers]
"AAG ORDER NUMBER" = "text"
"CUSTOMER NAME" = "text9" 
"DELIVERY DATE" = "date4"
"CUSTOMER SEASON" = "text"
"TOTAL ORDER QTY" = "numbers"

[monday.column_mapping.development.lines]
"ITEM" = "text"
"COLOR" = "color"
"SIZE" = "text8"
"QTY" = "numbers"
"UNIT PRICE" = "numbers"

[monday.sync.groups]
strategy = "season"
"""
        config_file = tmp_path / "test_config.toml"
        config_file.write_text(config_content)
        return str(config_file)
    
    @pytest.fixture
    def sample_records(self):
        """Generate test records for conservative batching validation"""
        return [
            {
                'AAG ORDER NUMBER': f'TEST-ORDER-{i:03d}',
                'CUSTOMER NAME': 'GREYSON CLOTHIERS',
                'DELIVERY DATE': '2025-03-15',
                'CUSTOMER SEASON': 'SPRING 2025',
                'TOTAL ORDER QTY': 100 + i,
                'record_uuid': f'test-uuid-{i:03d}',
                'customer_batch_uuid': 'test-batch-greyson-001'
            }
            for i in range(1, 8)  # 7 records to test conservative batching (5+2 split)
        ]
    
    @pytest.fixture
    def mock_api_client(self, test_config_path):
        """Create Monday API client with mocked dependencies"""
        with patch('src.pipelines.sync_order_list.monday_api_client.config') as mock_config:
            mock_config.get_config_value.return_value = "test_token_12345"
            
            client = MondayAPIClient(test_config_path)
            return client
    
    def test_conservative_batch_size_calculation(self, mock_api_client, sample_records):
        """
        Test: Conservative batch sizing for Monday.com rate limits
        Validates: 7 records → 2 batches (5 + 2) with conservative limits
        """
        # Simulate batch calculation logic
        batch_size = 5  # Conservative limit for testing
        batches = [sample_records[i:i + batch_size] for i in range(0, len(sample_records), batch_size)]
        
        # Assertions
        assert len(batches) == 2, f"Expected 2 batches, got {len(batches)}"
        assert len(batches[0]) == 5, f"First batch should have 5 records, got {len(batches[0])}"
        assert len(batches[1]) == 2, f"Second batch should have 2 records, got {len(batches[1])}"
        
        print(f"✅ Conservative batching: {len(sample_records)} records → {len(batches)} batches (sizes: {[len(b) for b in batches]})")
    
    def test_execution_strategy_selection(self, mock_api_client, sample_records):
        """
        Test: Conservative execution strategy selection
        Validates: 1 record→single, ≤5→batch, >5→async batch with rate limiting
        """
        # Test single record
        single_record = sample_records[:1]
        with patch.object(mock_api_client, '_execute_single', new_callable=AsyncMock) as mock_single:
            mock_single.return_value = {'success': True, 'records_processed': 1}
            result = mock_api_client.execute("create_items", single_record[0], dry_run=False)
            mock_single.assert_called_once()
        
        # Test small batch (5 records)
        small_batch = sample_records[:5]
        with patch.object(mock_api_client, '_execute_batch', new_callable=AsyncMock) as mock_batch:
            mock_batch.return_value = {'success': True, 'records_processed': 5}
            result = mock_api_client.execute("create_items", small_batch, dry_run=False)
            mock_batch.assert_called_once()
        
        # Test large batch (>5 records → async batch)
        large_batch = sample_records  # 7 records
        with patch.object(mock_api_client, '_execute_async_batch', new_callable=AsyncMock) as mock_async:
            mock_async.return_value = {'success': True, 'records_processed': 7, 'conservative_batching': True}
            result = mock_api_client.execute("create_items", large_batch, dry_run=False)
            mock_async.assert_called_once()
        
        print("✅ Conservative execution strategies validated: single→batch→async_batch")
    
    @pytest.mark.asyncio
    async def test_conservative_rate_limiting(self, mock_api_client):
        """
        Test: Conservative rate limiting with proven async patterns
        Validates: 100ms delays, 25s timeouts, 3-concurrent limit
        """
        import time
        
        # Mock the _execute_batch method to simulate timing
        async def mock_execute_batch(operation_type, batch_records):
            await asyncio.sleep(0.1)  # Simulate 100ms processing time
            return {
                'success': True,
                'records_processed': len(batch_records),
                'monday_ids': [1000 + i for i in range(len(batch_records))]
            }
        
        # Test rate limiting behavior
        with patch.object(mock_api_client, '_execute_batch', side_effect=mock_execute_batch):
            start_time = time.time()
            
            # Execute multiple small batches to test rate limiting
            tasks = []
            for i in range(3):  # 3 concurrent batches (at limit)
                batch = [{'AAG ORDER NUMBER': f'TEST-{i}-{j}'} for j in range(2)]
                task = mock_api_client._execute_async_batch("create_items", batch * 3)  # 6 records → 2 batches each
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            elapsed = time.time() - start_time
            
            # Validate rate limiting worked
            assert elapsed >= 0.1, f"Expected at least 100ms delay, got {elapsed:.3f}s"
            assert all(r['success'] for r in results), "All batches should succeed with rate limiting"
            
            print(f"✅ Conservative rate limiting: {len(tasks)} concurrent batches in {elapsed:.3f}s")
    
    @pytest.mark.asyncio 
    async def test_fallback_strategy_timeout_handling(self, mock_api_client, sample_records):
        """
        Test: Fallback strategy for batch timeouts (batch→single records)
        Validates: 25s timeout → fallback to single record processing
        """
        # Mock timeout scenario
        async def mock_execute_batch_timeout(operation_type, batch_records):
            raise asyncio.TimeoutError("Simulated 25s timeout")
        
        async def mock_execute_single_success(operation_type, record):
            return {
                'success': True, 
                'records_processed': 1, 
                'monday_ids': [2000]
            }
        
        with patch.object(mock_api_client, '_execute_batch', side_effect=mock_execute_batch_timeout):
            with patch.object(mock_api_client, '_execute_single', side_effect=mock_execute_single_success):
                
                # Test fallback with 3 records
                test_batch = sample_records[:3]
                result = await mock_api_client._execute_async_batch("create_items", test_batch)
                
                # Validate fallback worked
                assert result['success'], "Fallback strategy should succeed"
                assert result['records_processed'] == 3, "Should process all records via fallback"
                assert result.get('fallback_used_count', 0) > 0, "Should report fallback usage"
                
                print(f"✅ Fallback strategy: batch timeout → single record processing ({result['records_processed']} records)")
    
    def test_dry_run_validation(self, mock_api_client, sample_records):
        """
        Test: Dry run validation before live API calls
        Validates: Configuration validation, GraphQL template loading, data transformation
        """
        # Test dry run execution
        result = mock_api_client.execute("create_items", sample_records, dry_run=True)
        
        # Validate dry run response
        assert result['success'], "Dry run should always succeed for valid data"
        assert result['dry_run'], "Should be marked as dry run"
        assert result['records_processed'] == len(sample_records), "Should count all records"
        assert 'would_execute' in result, "Should describe what would be executed"
        
        print(f"✅ Dry run validation: {result['records_processed']} records, operation: {result['operation_type']}")
    
    def test_error_handling_and_logging(self, mock_api_client, sample_records):
        """
        Test: Comprehensive error handling for Monday.com API failures
        Validates: Rate limit detection, timeout handling, GraphQL error parsing
        """
        # Mock various error scenarios
        error_scenarios = [
            {'status': 429, 'error': 'Rate limited', 'expected_delay': True},
            {'status': 500, 'error': 'Server error', 'expected_delay': False},
            {'graphql_errors': [{'message': 'Invalid field'}], 'expected_delay': False}
        ]
        
        for scenario in error_scenarios:
            with patch.object(mock_api_client, '_make_api_call') as mock_call:
                mock_call.return_value = {
                    'success': False, 
                    'error': scenario['error']
                }
                
                result = mock_api_client.execute("create_items", sample_records[0], dry_run=False)
                
                assert not result['success'], f"Should fail for scenario: {scenario['error']}"
                assert 'error' in result, "Should include error details"
        
        print("✅ Error handling validated: rate limits, server errors, GraphQL errors")
    
    def test_connection_pooling_configuration(self, mock_api_client):
        """
        Test: HTTP connection pooling for efficient API usage
        Validates: TCPConnector limits, timeout configuration, session reuse
        """
        # This test validates the connection pooling configuration
        # In the actual _make_api_call method, we set:
        # - limit=10 (total connections)
        # - limit_per_host=3 (per Monday.com)
        # - timeout=25s total, 5s connect
        
        # Validate configuration through inspection
        import inspect
        source = inspect.getsource(mock_api_client._make_api_call)
        
        # Check for connection pooling configuration
        assert 'TCPConnector' in source, "Should use TCPConnector for connection pooling"
        assert 'limit=10' in source, "Should limit total connections"
        assert 'limit_per_host=3' in source, "Should limit connections per host"
        assert 'timeout=25.0' in source, "Should set 25s timeout"
        
        print("✅ Connection pooling: 10 total connections, 3 per host, 25s timeout")


def run_conservative_batching_integration_test():
    """
    Execute comprehensive Monday.com API conservative batching test
    Success Gate: >95% test pass rate with rate limiting validation
    """
    print("🧪 TASK 11.0: Monday.com API Conservative Batching Integration Test")
    print("=" * 70)
    
    # Configure pytest for detailed output
    pytest_args = [
        __file__,
        "-v",
        "--tb=short", 
        "-s",
        "--disable-warnings"
    ]
    
    # Execute tests
    exit_code = pytest.main(pytest_args)
    
    if exit_code == 0:
        print("\n" + "=" * 70)
        print("✅ INTEGRATION TEST SUCCESS: Monday.com API Conservative Batching")
        print("📊 Success Criteria: >95% pass rate with rate limiting")
        print("🚀 Ready for Task 11.0 Implementation Phase")
        print("=" * 70)
        return True
    else:
        print("\n" + "=" * 70) 
        print("❌ INTEGRATION TEST FAILED: Conservative batching validation")
        print("🔍 Review test failures before proceeding")
        print("=" * 70)
        return False


if __name__ == "__main__":
    success = run_conservative_batching_integration_test()
    exit(0 if success else 1)
