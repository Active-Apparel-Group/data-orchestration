"""
Integration Test: Sync Engine Customer Batching
==============================================
Purpose: Test complete customer batching workflow with real DELTA table data
Requirement: Test 9.0 Monday.com API Implementation - Customer Batch Processing

Success Criteria:
- Customer batching groups records correctly by CUSTOMER NAME + record_uuid
- UUID cascade logic maintains referential integrity  
- DELTA table queries execute successfully with >95% success rate
- Monday.com API integration ready for real data processing

Test Data: Uses real ORDER_LIST_DELTA table with 69 records (GREYSON PO 4755)
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, List, Any

# Repository root discovery and path setup
def find_repo_root() -> Path:
    """Find repository root by looking for pipelines/utils folder"""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current.parent.parent.parent / "pipelines" / "utils").exists():
            return current.parent.parent.parent
        current = current.parent
    raise RuntimeError("Could not find repository root with utils/ folder")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))
sys.path.insert(0, str(repo_root / "src"))

# Project imports
from pipelines.utils import logger, db
from pipelines.sync_order_list.sync_engine import SyncEngine

class TestSyncCustomerBatching:
    """Test customer batching workflow with real DELTA data"""
    
    @pytest.fixture(scope="class")
    def sync_engine(self):
        """Initialize sync engine with test configuration"""
        config_path = repo_root / "configs" / "pipelines" / "sync_order_list.toml"
        if not config_path.exists():
            pytest.skip(f"Configuration file not found: {config_path}")
        
        return SyncEngine(str(config_path))
    
    def test_delta_table_data_availability(self, sync_engine):
        """
        Validate DELTA tables have data and required columns
        Success Gate: >95% of expected columns present
        """
        logger_test = logger.get_logger("test_delta_availability")
        
        # Test ORDER_LIST_DELTA table
        headers_query = f"""
        SELECT TOP 10 [record_uuid], [AAG ORDER NUMBER], [CUSTOMER NAME], 
               [sync_state], [monday_item_id], [created_at]
        FROM [{sync_engine.headers_delta_table}]
        """
        
        # Test ORDER_LIST_LINES_DELTA table  
        lines_query = f"""
        SELECT TOP 5 [line_uuid], [record_uuid], [size_code], [qty],
               [sync_state], [monday_item_id], [created_at]
        FROM [{sync_engine.lines_delta_table}]
        """
        
        try:
            with db.get_connection('orders') as connection:
                cursor = connection.cursor()
                
                # Test headers DELTA
                cursor.execute(headers_query)
                headers_columns = [col[0] for col in cursor.description]
                headers_data = cursor.fetchall()
                
                # Test lines DELTA
                cursor.execute(lines_query)
                lines_columns = [col[0] for col in cursor.description]
                lines_data = cursor.fetchall()
                
                logger_test.info(f"✅ Headers DELTA: {len(headers_columns)} columns, {len(headers_data)} sample records")
                logger_test.info(f"✅ Lines DELTA: {len(lines_columns)} columns, {len(lines_data)} sample records")
                
                # Validate required columns exist
                required_headers_cols = ['record_uuid', 'AAG ORDER NUMBER', 'CUSTOMER NAME', 'sync_state']
                required_lines_cols = ['line_uuid', 'record_uuid', 'size_code', 'qty', 'sync_state']
                
                headers_coverage = sum(1 for col in required_headers_cols if col in headers_columns) / len(required_headers_cols)
                lines_coverage = sum(1 for col in required_lines_cols if col in lines_columns) / len(required_lines_cols)
                
                logger_test.info(f"📊 Headers column coverage: {headers_coverage:.1%}")
                logger_test.info(f"📊 Lines column coverage: {lines_coverage:.1%}")
                
                # Success gate: >95% column coverage
                assert headers_coverage >= 0.95, f"Headers column coverage {headers_coverage:.1%} below 95% threshold"
                assert lines_coverage >= 0.95, f"Lines column coverage {lines_coverage:.1%} below 95% threshold"
                
                return {
                    'success': True,
                    'headers_columns': headers_columns,
                    'lines_columns': lines_columns,
                    'headers_coverage': headers_coverage,
                    'lines_coverage': lines_coverage
                }
                
        except Exception as e:
            logger_test.error(f"❌ DELTA table validation failed: {e}")
            pytest.fail(f"DELTA table data availability test failed: {e}")
    
    def test_customer_batching_logic(self, sync_engine):
        """
        Test customer batching with record_uuid grouping
        Success Gate: >95% successful grouping of customer records
        """
        logger_test = logger.get_logger("test_customer_batching")
        
        # Get sample headers from DELTA table
        try:
            sample_headers = sync_engine._get_pending_headers(limit=20)
            
            if not sample_headers:
                pytest.skip("No pending headers found in DELTA table for batching test")
            
            logger_test.info(f"Testing customer batching with {len(sample_headers)} sample headers")
            
            # Test customer batching logic
            customer_batches = sync_engine._group_by_customer_and_uuid(sample_headers)
            
            # Validate batching results
            total_customers = len(customer_batches)
            total_record_uuids = sum(len(record_batches) for record_batches in customer_batches.values())
            total_headers = sum(len(headers) for record_batches in customer_batches.values() 
                              for headers in record_batches.values())
            
            logger_test.info(f"📊 Batching Results:")
            logger_test.info(f"  • Customers: {total_customers}")
            logger_test.info(f"  • Unique record_uuids: {total_record_uuids}")
            logger_test.info(f"  • Total headers grouped: {total_headers}")
            
            # Test specific customer data (GREYSON if available)
            greyson_batches = customer_batches.get('GREYSON', {})
            if greyson_batches:
                logger_test.info(f"  • GREYSON record_uuids: {len(greyson_batches)}")
                for record_uuid, headers in greyson_batches.items():
                    logger_test.info(f"    - {record_uuid}: {len(headers)} headers")
            
            # Success gates
            batching_efficiency = total_headers / len(sample_headers) if sample_headers else 0
            logger_test.info(f"📊 Batching efficiency: {batching_efficiency:.1%}")
            
            assert total_customers > 0, "No customers found in batching"
            assert total_record_uuids > 0, "No record_uuids found in batching"
            assert batching_efficiency >= 0.95, f"Batching efficiency {batching_efficiency:.1%} below 95%"
            
            return {
                'success': True,
                'customers_count': total_customers,
                'record_uuids_count': total_record_uuids,
                'headers_count': total_headers,
                'batching_efficiency': batching_efficiency,
                'customer_batches': customer_batches
            }
            
        except Exception as e:
            logger_test.error(f"❌ Customer batching test failed: {e}")
            pytest.fail(f"Customer batching logic test failed: {e}")
    
    def test_uuid_cascade_validation(self, sync_engine):
        """
        Test UUID cascade logic with record_uuid → parent_item_id flow
        Success Gate: >95% successful UUID relationships maintained
        """
        logger_test = logger.get_logger("test_uuid_cascade")
        
        try:
            # Get sample data with both headers and lines
            sample_headers = sync_engine._get_pending_headers(limit=5)
            
            if not sample_headers:
                pytest.skip("No headers available for UUID cascade test")
            
            # Extract record_uuids from headers
            test_record_uuids = [header['record_uuid'] for header in sample_headers if header.get('record_uuid')]
            
            if not test_record_uuids:
                pytest.skip("No record_uuids found in sample headers")
            
            logger_test.info(f"Testing UUID cascade with {len(test_record_uuids)} record_uuids")
            
            # Test lines retrieval by record_uuid
            cascade_results = []
            for record_uuid in test_record_uuids:
                lines = sync_engine._get_lines_by_record_uuid(record_uuid)
                cascade_results.append({
                    'record_uuid': record_uuid,
                    'lines_count': len(lines),
                    'has_valid_uuid': record_uuid is not None and record_uuid != '',
                    'lines_have_record_uuid': all(line.get('record_uuid') == record_uuid for line in lines)
                })
                
                logger_test.info(f"  • {record_uuid}: {len(lines)} lines")
            
            # Calculate success metrics
            valid_uuids = sum(1 for result in cascade_results if result['has_valid_uuid'])
            consistent_relationships = sum(1 for result in cascade_results if result['lines_have_record_uuid'])
            total_lines = sum(result['lines_count'] for result in cascade_results)
            
            uuid_validity = valid_uuids / len(cascade_results) if cascade_results else 0
            relationship_consistency = consistent_relationships / len(cascade_results) if cascade_results else 0
            
            logger_test.info(f"📊 UUID Cascade Results:")
            logger_test.info(f"  • UUID validity: {uuid_validity:.1%}")
            logger_test.info(f"  • Relationship consistency: {relationship_consistency:.1%}")
            logger_test.info(f"  • Total lines found: {total_lines}")
            
            # Success gates: >95% UUID validity and consistency
            assert uuid_validity >= 0.95, f"UUID validity {uuid_validity:.1%} below 95% threshold"
            assert relationship_consistency >= 0.95, f"Relationship consistency {relationship_consistency:.1%} below 95%"
            
            return {
                'success': True,
                'uuid_validity': uuid_validity,
                'relationship_consistency': relationship_consistency,
                'total_lines': total_lines,
                'cascade_results': cascade_results
            }
            
        except Exception as e:
            logger_test.error(f"❌ UUID cascade validation failed: {e}")
            pytest.fail(f"UUID cascade validation test failed: {e}")
    
    def test_dry_run_sync_workflow(self, sync_engine):
        """
        Test complete sync workflow in dry-run mode
        Success Gate: Dry-run completes without errors, >90% processing success
        """
        logger_test = logger.get_logger("test_dry_run_sync")
        
        try:
            logger_test.info("🧪 Starting dry-run sync workflow test")
            
            # Execute dry-run with limited records
            result = sync_engine.run_sync(dry_run=True, limit=10)
            
            logger_test.info(f"📊 Dry-run Results:")
            logger_test.info(f"  • Success: {result.get('success', False)}")
            logger_test.info(f"  • Total synced: {result.get('total_synced', 0)}")
            logger_test.info(f"  • Batches processed: {result.get('batches_processed', 0)}")
            logger_test.info(f"  • Execution time: {result.get('execution_time_seconds', 0):.2f}s")
            
            # Validate dry-run results
            if result.get('batches_processed', 0) > 0:
                success_rate = result.get('successful_batches', 0) / result.get('batches_processed', 1)
                logger_test.info(f"  • Success rate: {success_rate:.1%}")
                
                # Success gate: >90% dry-run success rate
                assert success_rate >= 0.90, f"Dry-run success rate {success_rate:.1%} below 90% threshold"
            else:
                logger_test.info("  • No batches to process (acceptable for dry-run)")
            
            # Validate no actual database changes occurred
            assert result.get('dry_run', False), "Dry-run flag not properly set"
            
            return {
                'success': True,
                'dry_run_result': result,
                'execution_success': result.get('success', False)
            }
            
        except Exception as e:
            logger_test.error(f"❌ Dry-run sync workflow failed: {e}")
            pytest.fail(f"Dry-run sync workflow test failed: {e}")

if __name__ == "__main__":
    # Run tests individually for development/debug
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize test instance
    test_instance = TestSyncCustomerBatching()
    
    # Create sync engine fixture manually
    config_path = find_repo_root() / "configs" / "pipelines" / "sync_order_list.toml"
    sync_engine = SyncEngine(str(config_path))
    
    print("🧪 Running Integration Tests: Sync Engine Customer Batching")
    print("=" * 80)
    
    # Run tests in order
    try:
        print("1️⃣  Testing DELTA table data availability...")
        result1 = test_instance.test_delta_table_data_availability(sync_engine)
        print(f"✅ DELTA tables validated: {result1['headers_coverage']:.1%} headers, {result1['lines_coverage']:.1%} lines")
        
        print("2️⃣  Testing customer batching logic...")
        result2 = test_instance.test_customer_batching_logic(sync_engine)
        print(f"✅ Customer batching: {result2['customers_count']} customers, {result2['record_uuids_count']} record_uuids")
        
        print("3️⃣  Testing UUID cascade validation...")
        result3 = test_instance.test_uuid_cascade_validation(sync_engine)
        print(f"✅ UUID cascade: {result3['uuid_validity']:.1%} validity, {result3['relationship_consistency']:.1%} consistency")
        
        print("4️⃣  Testing dry-run sync workflow...")
        result4 = test_instance.test_dry_run_sync_workflow(sync_engine)
        print(f"✅ Dry-run workflow: {result4['execution_success']}")
        
        print("=" * 80)
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("✅ Customer batching ready for Monday.com API implementation")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        raise
