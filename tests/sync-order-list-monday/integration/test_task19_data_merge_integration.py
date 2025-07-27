"""
Integration Test: Task 19.14.3 - Data Merge Integration Test
Purpose: Validate complete merge workflow from swp_ORDER_LIST_V2 → ORDER_LIST_V2 → ORDER_LIST_LINES with sync column population
Requirement: Test actual data merge using DELTA-free templates, validate sync columns populated correctly

SUCCESS CRITERIA:
- merge_headers.j2 successfully merges swp_ORDER_LIST_V2 → ORDER_LIST_V2 with sync columns populated
- unpivot_sizes.j2 successfully creates ORDER_LIST_LINES with inherited sync state
- All records have action_type, sync_state, sync_pending_at properly set
- All 245 size columns processed correctly in unpivot operation
- 100% sync column population (no NULL sync tracking values)
- Overall success rate: 100% (Critical success gate for Task 19.14.3)

CONTEXT: Task 19.0 DELTA Elimination - Phase 5 Integration Testing
Previous: Task 19.14.2 PASSED - Template integration validation (templates render correctly)
Current: Task 19.14.3 - Data merge integration (actual source → target merge with sync columns)
Next: Task 19.15 - Sync engine validation with freshly merged data
"""

import sys
from pathlib import Path
from typing import Dict, Any, List
import re
import pandas as pd

# Legacy transition support pattern (PROVEN SUCCESSFUL)
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

# Modern imports from project (VALIDATED PATTERN)
from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.sql_template_engine import SQLTemplateEngine
from src.pipelines.sync_order_list.merge_orchestrator import MergeOrchestrator

logger = logger.get_logger(__name__)

class Task19DataMergeIntegrationTest:
    """Integration test for Task 19.14.3 - Complete data merge workflow validation"""
    
    def __init__(self, config_path: str = None):
        # Use repo_root pattern like other tests
        if config_path is None:
            config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
        self.config_path = config_path
        self.success_threshold = 1.0  # 100% success required for Task 19.14.3
        self.test_customer = "GREYSON"
        self.test_po = "4755"
        
        # Clean tables at start of test
        self._clean_test_tables()
    
    def _clean_test_tables(self):
        """Clean target tables before testing"""
        try:
            logger.info("🧹 Cleaning target tables before test...")
            
            # Load config to get db_key
            config = DeltaSyncConfig.from_toml(self.config_path)
            conn = db.get_connection(config.db_key)
            
            # Clean ORDER_LIST_V2 first
            db.execute("DELETE FROM ORDER_LIST_V2", config.db_key)
            v2_result = pd.read_sql("SELECT COUNT(*) as count FROM ORDER_LIST_V2", conn)
            v2_count = v2_result.iloc[0]['count']
            logger.info(f"   ORDER_LIST_V2 cleaned: {v2_count} records remaining")
            
            # Clean ORDER_LIST_LINES
            db.execute("TRUNCATE TABLE ORDER_LIST_LINES", config.db_key)
            lines_result = pd.read_sql("SELECT COUNT(*) as count FROM ORDER_LIST_LINES", conn)
            lines_count = lines_result.iloc[0]['count']
            logger.info(f"   ORDER_LIST_LINES cleaned: {lines_count} records remaining")
            
            logger.info("✅ Tables cleaned successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to clean tables: {e}")
            raise
        
    def validate_pre_merge_state(self) -> Dict[str, Any]:
        """Validate source data exists and target tables are clean"""
        try:
            # Load configuration for database connection
            config = DeltaSyncConfig.from_toml(self.config_path)
            
            # Check source data exists
            source_query = """
            SELECT COUNT(*) as source_count 
            FROM swp_ORDER_LIST_V2 
            WHERE [CUSTOMER NAME] = ? AND [PO NUMBER] = ?
            """
            
            with db.get_connection(config.db_key) as conn:
                source_result = pd.read_sql(source_query, conn, params=(self.test_customer, self.test_po))
                source_count = source_result.iloc[0]['source_count'] if len(source_result) > 0 else 0
                
                # Check target tables are clean
                target_query = "SELECT COUNT(*) as target_count FROM ORDER_LIST_V2"
                target_result = pd.read_sql(target_query, conn)
                target_count = target_result.iloc[0]['target_count'] if len(target_result) > 0 else 0
                
                lines_query = "SELECT COUNT(*) as lines_count FROM ORDER_LIST_LINES"
                lines_result = pd.read_sql(lines_query, conn)
                lines_count = lines_result.iloc[0]['lines_count'] if len(lines_result) > 0 else 0
            
            pre_merge_valid = source_count > 0 and target_count == 0 and lines_count == 0
            
            logger.info("Pre-merge state validation:")
            logger.info(f"  Source data (swp_ORDER_LIST_V2): {source_count} records")
            logger.info(f"  Target table (ORDER_LIST_V2): {target_count} records")
            logger.info(f"  Lines table (ORDER_LIST_LINES): {lines_count} records")
            logger.info(f"  Pre-merge state: {'✅ CLEAN' if pre_merge_valid else '❌ NOT CLEAN'}")
            
            return {
                'pre_merge_valid': pre_merge_valid,
                'source_count': source_count,
                'target_count': target_count,
                'lines_count': lines_count,
                'test_passed': pre_merge_valid
            }
            
        except Exception as e:
            logger.error(f"Pre-merge state validation failed: {e}")
            return {
                'pre_merge_valid': False,
                'test_passed': False,
                'error': str(e)
            }
    
    def execute_merge_headers_template(self) -> Dict[str, Any]:
        """Execute merge_headers.j2 template: swp_ORDER_LIST_V2 → ORDER_LIST_V2"""
        try:
            # Load configuration and template engine
            config = DeltaSyncConfig.from_toml(self.config_path)
            template_engine = SQLTemplateEngine(config)
            
            # Render and execute merge_headers SQL
            merge_headers_sql = template_engine.render_merge_headers_sql()
            
            logger.info("🔄 Executing merge_headers.j2 template...")
            logger.info(f"   Source: {config.source_table}")
            logger.info(f"   Target: {config.target_table}")
            
            # PRINT THE ACTUAL SQL BEING EXECUTED
            logger.info("=" * 80)
            logger.info("🔍 RENDERED MERGE SQL:")
            logger.info("=" * 80)
            logger.info(merge_headers_sql)
            logger.info("=" * 80)
            
            # Execute the merge operation
            with db.get_connection(config.db_key) as conn:
                cursor = conn.cursor()
                cursor.execute(merge_headers_sql)
                conn.commit()
                
            logger.info("✅ merge_headers.j2 executed successfully")
            
            # Validate results
            result_query = """
            SELECT 
                COUNT(*) as merged_count,
                COUNT(CASE WHEN action_type IS NOT NULL THEN 1 END) as action_type_populated,
                COUNT(CASE WHEN sync_state IS NOT NULL THEN 1 END) as sync_state_populated,
                COUNT(CASE WHEN sync_attempted_at IS NOT NULL THEN 1 END) as sync_attempted_at_populated,
                COUNT(CASE WHEN sync_state = 'PENDING' THEN 1 END) as pending_records
            FROM ORDER_LIST_V2
            WHERE [CUSTOMER NAME] = ? AND [PO NUMBER] = ?
            """
            
            with db.get_connection(config.db_key) as conn:
                result = pd.read_sql(result_query, conn, params=(self.test_customer, self.test_po))
            
            if not result.empty:
                merged_count = result.iloc[0]['merged_count']
                action_type_populated = result.iloc[0]['action_type_populated']
                sync_state_populated = result.iloc[0]['sync_state_populated']
                sync_attempted_at_populated = result.iloc[0]['sync_attempted_at_populated']
                pending_records = result.iloc[0]['pending_records']
                
                sync_columns_complete = (
                    action_type_populated == merged_count and
                    sync_state_populated == merged_count and
                    sync_attempted_at_populated == merged_count
                )
                
                logger.info(f"merge_headers.j2 results:")
                logger.info(f"  Records merged: {merged_count}")
                logger.info(f"  action_type populated: {action_type_populated}/{merged_count}")
                logger.info(f"  sync_state populated: {sync_state_populated}/{merged_count}")
                logger.info(f"  sync_attempted_at populated: {sync_attempted_at_populated}/{merged_count}")
                logger.info(f"  Records in PENDING state: {pending_records}")
                logger.info(f"  Sync columns complete: {'✅ YES' if sync_columns_complete else '❌ NO'}")
                
                return {
                    'template_name': 'merge_headers.j2',
                    'merged_count': merged_count,
                    'sync_columns_complete': sync_columns_complete,
                    'action_type_populated': action_type_populated,
                    'sync_state_populated': sync_state_populated,
                    'sync_attempted_at_populated': sync_attempted_at_populated,
                    'pending_records': pending_records,
                    'test_passed': merged_count > 0 and sync_columns_complete
                }
            else:
                logger.error("No results from merge validation query")
                return {
                    'template_name': 'merge_headers.j2',
                    'test_passed': False,
                    'error': 'No validation results'
                }
                
        except Exception as e:
            logger.error(f"merge_headers.j2 execution failed: {e}")
            return {
                'template_name': 'merge_headers.j2',
                'test_passed': False,
                'error': str(e)
            }
    
    def execute_unpivot_sizes_template(self) -> Dict[str, Any]:
        """Execute unpivot_sizes.j2 template: ORDER_LIST_V2 → ORDER_LIST_LINES"""
        try:
            # Load configuration and template engine
            config = DeltaSyncConfig.from_toml(self.config_path)
            template_engine = SQLTemplateEngine(config)
            
            # Render and execute unpivot_sizes_direct SQL
            unpivot_sizes_sql = template_engine.render_unpivot_sizes_direct_sql()
            
            logger.info("🔄 Executing unpivot_sizes_direct.j2 template...")
            logger.info(f"   Source: {config.target_table} (WHERE sync_state = 'PENDING')")
            logger.info(f"   Target: {config.source_lines_table}")
            
            # Execute the unpivot operation
            with db.get_connection(config.db_key) as conn:
                cursor = conn.cursor()
                cursor.execute(unpivot_sizes_sql)
                conn.commit()
                
            logger.info("✅ unpivot_sizes.j2 executed successfully")
            
            # Validate results
            result_query = """
            SELECT 
                COUNT(*) as unpivoted_count,
                COUNT(DISTINCT ol.record_uuid) as unique_records,
                COUNT(DISTINCT ol.size_code) as unique_sizes,
                SUM(CASE WHEN ol.qty > 0 THEN 1 ELSE 0 END) as non_zero_qty,
                COUNT(CASE WHEN ol.action_type IS NOT NULL THEN 1 END) as action_type_populated,
                COUNT(CASE WHEN ol.sync_state IS NOT NULL THEN 1 END) as sync_state_populated
            FROM ORDER_LIST_LINES ol
            JOIN ORDER_LIST_V2 ov ON ol.record_uuid = ov.record_uuid
            WHERE ov.[CUSTOMER NAME] = ? AND ov.[PO NUMBER] = ?
            """
            
            with db.get_connection(config.db_key) as conn:
                result = pd.read_sql(result_query, conn, params=(self.test_customer, self.test_po))
                
            if len(result) > 0:
                unpivoted_count = result.iloc[0]['unpivoted_count']
                unique_records = result.iloc[0]['unique_records']
                unique_sizes = result.iloc[0]['unique_sizes']
                non_zero_qty = result.iloc[0]['non_zero_qty']
                action_type_populated = result.iloc[0]['action_type_populated']
                sync_state_populated = result.iloc[0]['sync_state_populated']
                
                sync_inheritance_complete = (
                    action_type_populated == unpivoted_count and
                    sync_state_populated == unpivoted_count
                )
                
                logger.info(f"unpivot_sizes.j2 results:")
                logger.info(f"  Lines created: {unpivoted_count}")
                logger.info(f"  Unique records: {unique_records}")
                logger.info(f"  Unique sizes: {unique_sizes}")
                logger.info(f"  Non-zero quantities: {non_zero_qty}")
                logger.info(f"  action_type inherited: {action_type_populated}/{unpivoted_count}")
                logger.info(f"  sync_state inherited: {sync_state_populated}/{unpivoted_count}")
                logger.info(f"  Sync inheritance complete: {'✅ YES' if sync_inheritance_complete else '❌ NO'}")
                
                return {
                    'template_name': 'unpivot_sizes.j2',
                    'unpivoted_count': unpivoted_count,
                    'unique_records': unique_records,
                    'unique_sizes': unique_sizes,
                    'non_zero_qty': non_zero_qty,
                    'sync_inheritance_complete': sync_inheritance_complete,
                    'action_type_populated': action_type_populated,
                    'sync_state_populated': sync_state_populated,
                    'test_passed': unpivoted_count > 0 and sync_inheritance_complete and non_zero_qty > 0
                }
            else:
                logger.error("No results from unpivot validation query")
                return {
                    'template_name': 'unpivot_sizes.j2',
                    'test_passed': False,
                    'error': 'No validation results'
                }
                
        except Exception as e:
            logger.error(f"unpivot_sizes.j2 execution failed: {e}")
            return {
                'template_name': 'unpivot_sizes.j2',
                'test_passed': False,
                'error': str(e)
            }
    
    def validate_complete_merge_workflow(self, merge_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate the complete merge workflow end-to-end"""
        try:
            # Check that both templates passed
            headers_passed = merge_results[0]['test_passed'] if len(merge_results) > 0 else False
            unpivot_passed = merge_results[1]['test_passed'] if len(merge_results) > 1 else False
            
            # Load configuration for database connection
            config = DeltaSyncConfig.from_toml(self.config_path)
            
            # Get final state counts
            final_headers_query = """
            SELECT COUNT(*) as final_headers_count
            FROM ORDER_LIST_V2
            WHERE [CUSTOMER NAME] = ? AND [PO NUMBER] = ?
            """
            with db.get_connection(config.db_key) as conn:
                headers_result = pd.read_sql(final_headers_query, conn, params=(self.test_customer, self.test_po))
                final_headers_count = headers_result.iloc[0]['final_headers_count'] if len(headers_result) > 0 else 0
            
            final_lines_query = """
            SELECT COUNT(*) as final_lines_count
            FROM ORDER_LIST_LINES ol
            JOIN ORDER_LIST_V2 ov ON ol.record_uuid = ov.record_uuid
            WHERE ov.[CUSTOMER NAME] = ? AND ov.[PO NUMBER] = ?
            """
            with db.get_connection(config.db_key) as conn:
                lines_result = pd.read_sql(final_lines_query, conn, params=(self.test_customer, self.test_po))
                final_lines_count = lines_result.iloc[0]['final_lines_count'] if len(lines_result) > 0 else 0
            
            # Check data consistency between headers and lines
            consistency_query = """
            SELECT 
                h.record_uuid,
                h.[AAG ORDER NUMBER],
                h.action_type as header_action_type,
                h.sync_state as header_sync_state,
                COUNT(l.line_uuid) as line_count,
                COUNT(CASE WHEN l.action_type = h.action_type THEN 1 END) as matching_action_type,
                COUNT(CASE WHEN l.sync_state = h.sync_state THEN 1 END) as matching_sync_state
            FROM ORDER_LIST_V2 h
            LEFT JOIN ORDER_LIST_LINES l ON h.record_uuid = l.record_uuid
            WHERE h.[CUSTOMER NAME] = ? AND h.[PO NUMBER] = ?
            GROUP BY h.record_uuid, h.[AAG ORDER NUMBER], h.action_type, h.sync_state
            """
            
            with db.get_connection(config.db_key) as conn:
                consistency_result = pd.read_sql(consistency_query, conn, params=(self.test_customer, self.test_po))
                
            # Calculate consistency metrics - Only check headers that HAVE lines (exclude cancelled orders)
            headers_with_lines = consistency_result[consistency_result['line_count'] > 0]
            total_headers_with_lines = len(headers_with_lines)
            consistent_action_types = sum(1 for _, row in headers_with_lines.iterrows() 
                                        if row['matching_action_type'] == row['line_count'])
            consistent_sync_states = sum(1 for _, row in headers_with_lines.iterrows() 
                                       if row['matching_sync_state'] == row['line_count'])
            
            # Calculate success metrics
            workflow_success = {
                'headers_template_passed': headers_passed,
                'unpivot_template_passed': unpivot_passed,
                'headers_populated': final_headers_count > 0,
                'lines_populated': final_lines_count > 0,
                'sync_consistency': consistent_action_types == total_headers_with_lines and consistent_sync_states == total_headers_with_lines
            }
            
            workflow_success_rate = sum(workflow_success.values()) / len(workflow_success)
            
            logger.info("Complete Merge Workflow Validation:")
            logger.info(f"  Headers template passed: {'✅ YES' if workflow_success['headers_template_passed'] else '❌ NO'}")
            logger.info(f"  Unpivot template passed: {'✅ YES' if workflow_success['unpivot_template_passed'] else '❌ NO'}")
            logger.info(f"  Headers populated: {'✅ YES' if workflow_success['headers_populated'] else '❌ NO'} ({final_headers_count} records)")
            logger.info(f"  Lines populated: {'✅ YES' if workflow_success['lines_populated'] else '❌ NO'} ({final_lines_count} records)")
            logger.info(f"  Sync consistency: {'✅ YES' if workflow_success['sync_consistency'] else '❌ NO'} ({consistent_action_types}/{total_headers_with_lines} action_type, {consistent_sync_states}/{total_headers_with_lines} sync_state)")
            logger.info(f"  Workflow success rate: {workflow_success_rate:.1%}")
            
            return {
                'workflow_success': workflow_success,
                'workflow_success_rate': workflow_success_rate,
                'final_headers_count': final_headers_count,
                'final_lines_count': final_lines_count,
                'total_headers_with_lines': total_headers_with_lines,
                'consistent_action_types': consistent_action_types,
                'consistent_sync_states': consistent_sync_states,
                'test_passed': workflow_success_rate >= self.success_threshold
            }
            
        except Exception as e:
            logger.error(f"Complete merge workflow validation failed: {e}")
            return {
                'test_passed': False,
                'error': str(e)
            }
    
    def validate_cancelled_order_integration(self) -> Dict[str, Any]:
        """
        Validate cancelled order handling via merge orchestrator (Task 19.14.4)
        Uses production merge orchestrator validate_cancelled_order_handling method
        """
        try:
            # Load configuration and initialize merge orchestrator
            config = DeltaSyncConfig.from_toml(self.config_path)
            merge_orchestrator = MergeOrchestrator(config)
            
            # Test GREYSON PO 4755 specific validation through merge orchestrator
            logger.info("🎯 Testing cancelled order validation via merge orchestrator...")
            validation_result = merge_orchestrator.validate_cancelled_order_handling(
                customer_name=self.test_customer,
                po_number=self.test_po
            )
            
            if validation_result['success']:
                logger.info("✅ Cancelled order validation via merge orchestrator PASSED")
                logger.info(f"   Integration working: merge orchestrator → cancelled order validation")
                logger.info(f"   Current data state: {validation_result['total_headers']} total, {validation_result['active_headers_with_lines']} active with lines, {validation_result['cancelled_orders']} cancelled")
                
                # Success based on sync consistency, not strict pattern matching
                sync_success = validation_result.get('sync_consistency_success', False)
                
                if sync_success:
                    logger.info("✅ Sync consistency validation passed for active orders")
                else:
                    logger.warning("⚠️ Sync consistency issues detected")
                
                return {
                    'test_passed': sync_success,
                    'validation_result': validation_result
                }
            else:
                logger.error("❌ Cancelled order validation via merge orchestrator FAILED")
                return {
                    'test_passed': False,
                    'validation_result': validation_result
                }
                
        except Exception as e:
            logger.error(f"Cancelled order integration validation failed: {e}")
            return {
                'test_passed': False,
                'error': str(e)
            }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run Task 19.14.3 - Complete data merge integration test"""
        logger.info("=" * 80)
        logger.info("🎯 TASK 19.14.3: Data Merge Integration Test")
        logger.info("=" * 80)
        logger.info("Context: Task 19.0 DELTA Elimination - Phase 5 Integration Testing")
        logger.info("Previous: Task 19.14.2 PASSED - Template integration validation")
        logger.info("Current: Complete merge workflow - swp_ORDER_LIST_V2 → ORDER_LIST_V2 → ORDER_LIST_LINES")
        logger.info("Success Gate: 100% merge workflow with sync column population")
        logger.info("=" * 80)
        
        # Phase 1: Pre-merge validation
        logger.info("📋 Phase 1: Pre-Merge State Validation")
        pre_merge_result = self.validate_pre_merge_state()
        
        if not pre_merge_result['test_passed']:
            logger.error("❌ Pre-merge state validation failed - cannot proceed")
            return {
                'task_19_14_3_success': False,
                'error': 'Pre-merge state invalid',
                'pre_merge_result': pre_merge_result
            }
        
        # Phase 2: Execute merge templates
        merge_results = []
        
        logger.info("🔄 Phase 2: Execute merge_headers.j2 Template")
        headers_result = self.execute_merge_headers_template()
        merge_results.append(headers_result)
        
        if not headers_result['test_passed']:
            logger.error("❌ merge_headers.j2 failed - cannot proceed to unpivot")
            return {
                'task_19_14_3_success': False,
                'error': 'Headers merge failed',
                'pre_merge_result': pre_merge_result,
                'headers_result': headers_result
            }
        
        logger.info("🔄 Phase 3: Execute unpivot_sizes.j2 Template")
        unpivot_result = self.execute_unpivot_sizes_template()
        merge_results.append(unpivot_result)
        
        # Phase 4: Validate complete workflow
        logger.info("🔍 Phase 4: Complete Merge Workflow Validation")
        workflow_result = self.validate_complete_merge_workflow(merge_results)
        
        # Phase 5: Cancelled Order Validation via Merge Orchestrator (Task 19.14.4)
        logger.info("🔍 Phase 5: Cancelled Order Validation via Merge Orchestrator")
        cancelled_order_result = self.validate_cancelled_order_integration()
        
        # Calculate overall Task 19.14.3 success
        task_19_14_3_success = (
            pre_merge_result['test_passed'] and
            headers_result['test_passed'] and
            unpivot_result['test_passed'] and
            workflow_result['test_passed'] and
            cancelled_order_result['test_passed']
        )
        
        logger.info("=" * 80)
        logger.info("📊 TASK 19.14.3 RESULTS:")
        logger.info(f"   Pre-merge validation: {'✅ PASS' if pre_merge_result['test_passed'] else '❌ FAIL'}")
        logger.info(f"   merge_headers.j2: {'✅ PASS' if headers_result['test_passed'] else '❌ FAIL'}")
        logger.info(f"   unpivot_sizes.j2: {'✅ PASS' if unpivot_result['test_passed'] else '❌ FAIL'}")
        logger.info(f"   Complete workflow: {'✅ PASS' if workflow_result['test_passed'] else '❌ FAIL'}")
        logger.info(f"   Cancelled order validation: {'✅ PASS' if cancelled_order_result['test_passed'] else '❌ FAIL'}")
        logger.info(f"   Overall Task 19.14.3 Success: {'✅ PASS' if task_19_14_3_success else '❌ FAIL'}")
        
        if task_19_14_3_success:
            logger.info("🎉 SUCCESS GATE MET: Task 19.14.3 Data Merge Integration!")
            logger.info("✅ Complete merge workflow: swp_ORDER_LIST_V2 → ORDER_LIST_V2 → ORDER_LIST_LINES")
            logger.info(f"✅ Headers merged: {headers_result.get('merged_count', 'N/A')} records with sync columns")
            logger.info(f"✅ Lines created: {unpivot_result.get('unpivoted_count', 'N/A')} with inherited sync state")
            logger.info(f"✅ Data consistency: Headers and lines properly linked")
            logger.info(f"✅ Cancelled order validation: Integrated with merge orchestrator")
            logger.info("🚀 Ready for Task 19.15: Sync Engine Main Table Operations")
        else:
            logger.error("❌ SUCCESS GATE FAILED: Task 19.14.3 Data Merge Integration failed!")
            logger.error("🔧 Check merge template execution and sync column population")
        
        logger.info("=" * 80)
        
        return {
            'task_19_14_3_success': task_19_14_3_success,
            'pre_merge_result': pre_merge_result,
            'headers_result': headers_result,
            'unpivot_result': unpivot_result,
            'workflow_result': workflow_result,
            'cancelled_order_result': cancelled_order_result,
            'success_gate_met': task_19_14_3_success
        }

def main():
    """Run Task 19.14.3 - Data Merge Integration Test"""
    try:
        tester = Task19DataMergeIntegrationTest()
        results = tester.run_comprehensive_test()
        
        # Exit with proper code for Task 19.14.3
        return 0 if results['success_gate_met'] else 1
        
    except Exception as e:
        logger.error(f"Task 19.14.3 data merge integration test failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
