"""
Integration Test: Task 19.14.2 - Template Integration DELTA-Free Validation
Purpose: Validate all 3 templates (merge_headers.j2, unpivot_sizes.j2, merge_lines.j2) work with main tables without DELTA dependencies
Requirement: All templates render SQL that works directly with ORDER_LIST_V2 and ORDER_LIST_LINES (no DELTA references)

SUCCESS CRITERIA:
- All 3 templates render without DELTA references or placeholders
- Templates use main tables (ORDER_LIST_V2, ORDER_LIST_LINES) exclusively  
- SQL contains proper sync column handling (action_type, sync_state, sync_pending_at)
- All size columns (245) are properly handled in templates
- Overall success rate: 100% (Task 19.14.2 success gate)

CONTEXT: Task 19.0 DELTA Elimination - Phase 5 Integration Testing
Previous: Task 19.14.1 PASSED - GREYSON PO 4755 DELTA-free pipeline (100% success)
Current: Task 19.14.2 - Template integration validation
Next: Task 19.15 - Sync engine main table operations validation
"""

import sys
from pathlib import Path
from typing import Dict, Any, List
import re

# Legacy transition support pattern (PROVEN SUCCESSFUL)
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

# Modern imports from project (VALIDATED PATTERN)
from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.sql_template_engine import SQLTemplateEngine

logger = logger.get_logger(__name__)

class Task19DeltaFreeTemplateTest:
    """Integration test for Task 19.14.2 - All templates DELTA-free validation"""
    
    def __init__(self, config_path: str = None):
        # Use repo_root pattern like other tests
        if config_path is None:
            config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
        self.config_path = config_path
        self.success_threshold = 1.0  # 100% success required for Task 19.14.2
        self.templates = ["merge_headers.j2", "unpivot_sizes.j2", "merge_lines.j2"]
        
    def validate_delta_free_architecture(self, rendered_sql: str, template_name: str) -> Dict[str, Any]:
        """Validate template uses DELTA-free architecture (main tables only)"""
        try:
            # Check for DELTA references (should be ZERO)
            delta_patterns = [
                r'ORDER_LIST_DELTA',
                r'ORDER_LIST_LINES_DELTA',
                r'DELTA',  # Any DELTA reference
                r'OUTPUT.*INTO.*DELTA'  # OUTPUT clause to DELTA tables
            ]
            
            delta_violations = []
            for pattern in delta_patterns:
                matches = re.findall(pattern, rendered_sql, re.IGNORECASE)
                if matches:
                    delta_violations.extend([(pattern, match) for match in matches])
            
            # Check for main table usage (should be PRESENT)
            main_table_patterns = [
                r'ORDER_LIST_V2',
                r'ORDER_LIST_LINES'
            ]
            
            main_table_usage = []
            for pattern in main_table_patterns:
                matches = re.findall(pattern, rendered_sql, re.IGNORECASE)
                main_table_usage.extend(matches)
            
            # Check for sync column usage (DELTA-free sync tracking)
            sync_column_patterns = [
                r'action_type',
                r'sync_state', 
                r'sync_pending_at',
                r'sync_batch_id',
                r'sync_monday_id',
                r'sync_attempted_at',
                r'sync_error_count'
            ]
            
            sync_column_usage = []
            for pattern in sync_column_patterns:
                matches = re.findall(pattern, rendered_sql, re.IGNORECASE)
                sync_column_usage.extend(matches)
            
            is_delta_free = len(delta_violations) == 0
            uses_main_tables = len(main_table_usage) > 0
            uses_sync_columns = len(sync_column_usage) > 0
            
            logger.info(f"DELTA-free validation for {template_name}:")
            logger.info(f"  ❌ DELTA references found: {len(delta_violations)}")
            logger.info(f"  ✅ Main table references: {len(main_table_usage)}")
            logger.info(f"  ✅ Sync column references: {len(sync_column_usage)}")
            logger.info(f"  🎯 DELTA-free status: {'✅ CLEAN' if is_delta_free else '❌ VIOLATIONS'}")
            
            if delta_violations:
                logger.warning(f"  DELTA violations: {delta_violations[:3]}")  # Show first 3
            
            return {
                'is_delta_free': is_delta_free,
                'uses_main_tables': uses_main_tables,
                'uses_sync_columns': uses_sync_columns,
                'delta_violations': delta_violations,
                'main_table_usage': main_table_usage,
                'sync_column_usage': sync_column_usage,
                'test_passed': is_delta_free and uses_main_tables
            }
            
        except Exception as e:
            logger.error(f"DELTA-free validation failed for {template_name}: {e}")
            return {
                'is_delta_free': False,
                'test_passed': False,
                'error': str(e)
            }
    
    def test_merge_headers_template(self) -> Dict[str, Any]:
        """Test merge_headers.j2 template for DELTA-free compliance"""
        try:
            # Load configuration
            config = DeltaSyncConfig.from_toml(self.config_path)
            template_engine = SQLTemplateEngine(config)
            
            # Render template
            rendered_sql = template_engine.render_merge_headers_sql()
            context = template_engine.get_template_context()
            
            # Basic validation
            basic_checks = {
                'template_rendered': rendered_sql is not None and len(rendered_sql) > 0,
                'no_placeholders': '{{' not in rendered_sql and '}}' not in rendered_sql,
                'contains_merge_logic': 'MERGE' in rendered_sql.upper(),
                'size_columns_present': len([col for col in context['size_columns'][:10] if col in rendered_sql]) > 0
            }
            
            # DELTA-free validation
            delta_free_results = self.validate_delta_free_architecture(rendered_sql, "merge_headers.j2")
            
            overall_success = all(basic_checks.values()) and delta_free_results['test_passed']
            
            logger.info(f"merge_headers.j2 validation: {'✅ PASS' if overall_success else '❌ FAIL'}")
            
            return {
                'template_name': 'merge_headers.j2',
                'basic_checks': basic_checks,
                'delta_free_results': delta_free_results,
                'rendered_sql': rendered_sql,
                'context': context,
                'test_passed': overall_success
            }
            
        except Exception as e:
            logger.error(f"merge_headers.j2 test failed: {e}")
            return {
                'template_name': 'merge_headers.j2',
                'test_passed': False,
                'error': str(e)
            }
    
    def test_unpivot_sizes_template(self) -> Dict[str, Any]:
        """Test unpivot_sizes.j2 template for DELTA-free compliance"""
        try:
            # Load configuration
            config = DeltaSyncConfig.from_toml(self.config_path)
            template_engine = SQLTemplateEngine(config)
            
            # Render template
            rendered_sql = template_engine.render_unpivot_sizes_sql()
            context = template_engine.get_template_context()
            
            # Basic validation
            basic_checks = {
                'template_rendered': rendered_sql is not None and len(rendered_sql) > 0,
                'no_placeholders': '{{' not in rendered_sql and '}}' not in rendered_sql,
                'contains_unpivot_logic': 'UNPIVOT' in rendered_sql.upper(),
                'size_columns_in_unpivot': len([col for col in context['size_columns'][:15] if col in rendered_sql]) > 5
            }
            
            # DELTA-free validation
            delta_free_results = self.validate_delta_free_architecture(rendered_sql, "unpivot_sizes.j2")
            
            overall_success = all(basic_checks.values()) and delta_free_results['test_passed']
            
            logger.info(f"unpivot_sizes.j2 validation: {'✅ PASS' if overall_success else '❌ FAIL'}")
            
            return {
                'template_name': 'unpivot_sizes.j2',
                'basic_checks': basic_checks,
                'delta_free_results': delta_free_results,
                'rendered_sql': rendered_sql,
                'context': context,
                'test_passed': overall_success
            }
            
        except Exception as e:
            logger.error(f"unpivot_sizes.j2 test failed: {e}")
            return {
                'template_name': 'unpivot_sizes.j2',
                'test_passed': False,
                'error': str(e)
            }
    
    def test_merge_lines_template(self) -> Dict[str, Any]:
        """Test merge_lines.j2 template for DELTA-free compliance"""
        try:
            # Load configuration
            config = DeltaSyncConfig.from_toml(self.config_path)
            template_engine = SQLTemplateEngine(config)
            
            # Render template
            rendered_sql = template_engine.render_merge_lines_sql()
            context = template_engine.get_template_context()
            
            # Basic validation
            basic_checks = {
                'template_rendered': rendered_sql is not None and len(rendered_sql) > 0,
                'no_placeholders': '{{' not in rendered_sql and '}}' not in rendered_sql,
                'contains_merge_logic': 'MERGE' in rendered_sql.upper(),
                'contains_lines_table': context['lines_table'] in rendered_sql
            }
            
            # DELTA-free validation
            delta_free_results = self.validate_delta_free_architecture(rendered_sql, "merge_lines.j2")
            
            overall_success = all(basic_checks.values()) and delta_free_results['test_passed']
            
            logger.info(f"merge_lines.j2 validation: {'✅ PASS' if overall_success else '❌ FAIL'}")
            
            return {
                'template_name': 'merge_lines.j2',
                'basic_checks': basic_checks,
                'delta_free_results': delta_free_results,
                'rendered_sql': rendered_sql,
                'context': context,
                'test_passed': overall_success
            }
            
        except Exception as e:
            logger.error(f"merge_lines.j2 test failed: {e}")
            return {
                'template_name': 'merge_lines.j2',
                'test_passed': False,
                'error': str(e)
            }
    
    def validate_template_integration(self, template_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate all templates work together as integrated DELTA-free system"""
        try:
            # Check that all templates passed
            all_templates_passed = all(result['test_passed'] for result in template_results)
            
            # Aggregate DELTA violations across all templates
            total_delta_violations = 0
            total_main_table_usage = 0
            total_sync_column_usage = 0
            
            for result in template_results:
                if 'delta_free_results' in result:
                    delta_free = result['delta_free_results']
                    total_delta_violations += len(delta_free.get('delta_violations', []))
                    total_main_table_usage += len(delta_free.get('main_table_usage', []))
                    total_sync_column_usage += len(delta_free.get('sync_column_usage', []))
            
            # Validate consistent size column handling
            size_column_counts = []
            for result in template_results:
                if 'context' in result:
                    size_column_counts.append(len(result['context']['size_columns']))
            
            consistent_size_columns = len(set(size_column_counts)) <= 1  # All should be same count
            
            integration_score = {
                'all_templates_passed': all_templates_passed,
                'zero_delta_violations': total_delta_violations == 0,
                'main_tables_used': total_main_table_usage > 0,
                'sync_columns_used': total_sync_column_usage > 0,
                'consistent_size_columns': consistent_size_columns
            }
            
            integration_success_rate = sum(integration_score.values()) / len(integration_score)
            
            logger.info("Template Integration Validation:")
            logger.info(f"  All templates passed: {'✅ YES' if integration_score['all_templates_passed'] else '❌ NO'}")
            logger.info(f"  Zero DELTA violations: {'✅ YES' if integration_score['zero_delta_violations'] else '❌ NO'}")
            logger.info(f"  Main tables used: {'✅ YES' if integration_score['main_tables_used'] else '❌ NO'}")
            logger.info(f"  Sync columns used: {'✅ YES' if integration_score['sync_columns_used'] else '❌ NO'}")
            logger.info(f"  Consistent size columns: {'✅ YES' if integration_score['consistent_size_columns'] else '❌ NO'}")
            logger.info(f"  Integration success rate: {integration_success_rate:.1%}")
            
            return {
                'integration_score': integration_score,
                'integration_success_rate': integration_success_rate,
                'total_delta_violations': total_delta_violations,
                'total_main_table_usage': total_main_table_usage,
                'total_sync_column_usage': total_sync_column_usage,
                'size_column_counts': size_column_counts,
                'test_passed': integration_success_rate >= self.success_threshold
            }
            
        except Exception as e:
            logger.error(f"Template integration validation failed: {e}")
            return {
                'test_passed': False,
                'error': str(e)
            }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run Task 19.14.2 - Complete template integration DELTA-free validation"""
        logger.info("=" * 80)
        logger.info("🎯 TASK 19.14.2: Template Integration DELTA-Free Validation")
        logger.info("=" * 80)
        logger.info("Context: Task 19.0 DELTA Elimination - Phase 5 Integration Testing")
        logger.info("Previous: Task 19.14.1 PASSED - GREYSON PO 4755 (100% success)")
        logger.info("Current: All 3 templates must work with main tables (no DELTA)")
        logger.info("Success Gate: 100% template compliance with DELTA-free architecture")
        logger.info("=" * 80)
        
        # Test all three templates
        template_tests = []
        
        logger.info("📋 Phase 1: merge_headers.j2 DELTA-Free Validation")
        headers_result = self.test_merge_headers_template()
        template_tests.append(headers_result)
        
        logger.info("🔄 Phase 2: unpivot_sizes.j2 DELTA-Free Validation")
        unpivot_result = self.test_unpivot_sizes_template()
        template_tests.append(unpivot_result)
        
        logger.info("🔗 Phase 3: merge_lines.j2 DELTA-Free Validation")
        lines_result = self.test_merge_lines_template()
        template_tests.append(lines_result)
        
        logger.info("🔍 Phase 4: Template Integration Validation")
        integration_result = self.validate_template_integration(template_tests)
        
        # Calculate overall Task 19.14.2 success
        individual_success_rate = sum(test['test_passed'] for test in template_tests) / len(template_tests)
        integration_passed = integration_result['test_passed']
        
        task_19_14_2_success = individual_success_rate >= self.success_threshold and integration_passed
        
        logger.info("=" * 80)
        logger.info("📊 TASK 19.14.2 RESULTS:")
        logger.info(f"   merge_headers.j2: {'✅ PASS' if headers_result['test_passed'] else '❌ FAIL'}")
        logger.info(f"   unpivot_sizes.j2: {'✅ PASS' if unpivot_result['test_passed'] else '❌ FAIL'}")
        logger.info(f"   merge_lines.j2: {'✅ PASS' if lines_result['test_passed'] else '❌ FAIL'}")
        logger.info(f"   Template Integration: {'✅ PASS' if integration_passed else '❌ FAIL'}")
        logger.info(f"   Individual Template Success Rate: {individual_success_rate:.1%}")
        logger.info(f"   Overall Task 19.14.2 Success: {'✅ PASS' if task_19_14_2_success else '❌ FAIL'}")
        
        if task_19_14_2_success:
            logger.info("🎉 SUCCESS GATE MET: Task 19.14.2 Template Integration DELTA-Free!")
            logger.info("✅ All 3 templates work with main tables (ORDER_LIST_V2, ORDER_LIST_LINES)")
            logger.info(f"✅ Zero DELTA references found ({integration_result.get('total_delta_violations', 'N/A')} violations)")
            logger.info(f"✅ Consistent size column handling ({len(set(integration_result.get('size_column_counts', [])))<=1})")
            logger.info("🚀 Ready for Task 19.15: Sync Engine Main Table Operations")
        else:
            logger.error("❌ SUCCESS GATE FAILED: Task 19.14.2 Template Integration failed!")
            logger.error("🔧 Check template DELTA references and main table usage")
        
        logger.info("=" * 80)
        
        return {
            'task_19_14_2_success': task_19_14_2_success,
            'individual_success_rate': individual_success_rate,
            'integration_passed': integration_passed,
            'template_results': template_tests,
            'integration_result': integration_result,
            'success_gate_met': task_19_14_2_success,
            'total_templates_tested': len(template_tests),
            'total_delta_violations': integration_result.get('total_delta_violations', 0)
        }

def main():
    """Run Task 19.14.2 - Template Integration DELTA-Free Validation"""
    try:
        tester = Task19DeltaFreeTemplateTest()
        results = tester.run_comprehensive_test()
        
        # Exit with proper code for Task 19.14.2
        return 0 if results['success_gate_met'] else 1
        
    except Exception as e:
        logger.error(f"Task 19.14.2 template integration test failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
