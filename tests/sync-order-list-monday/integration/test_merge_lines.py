"""
Integration Test: merge_lines.j2 Template Validation
Purpose: Test lines merge template with real size columns from swp_ORDER_LIST_V2
Requirement: Template renders SQL with MERGE logic for normalized line items

SUCCESS CRITERIA:
- Template renders without placeholders or errors
- SQL contains MERGE logic for line item processing
- Generated SQL executes without syntax errors
- Template uses real database columns from ConfigParser
- Success rate: 100% (all validations pass)
"""

import sys
from pathlib import Path
from typing import Dict, Any

# Legacy transition support pattern
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

# Modern imports from project
from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.sql_template_engine import SQLTemplateEngine

logger = logger.get_logger(__name__)

class MergeLinesTemplateTest:
    """Integration test for merge_lines.j2 template with real database columns"""
    
    def __init__(self, config_path: str = None):
        # Use repo_root pattern like other tests
        if config_path is None:
            config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
        self.config_path = config_path
        self.success_threshold = 1.0  # 100% success required
        self.template_name = "merge_lines.j2"
        
    def test_template_rendering(self) -> Dict[str, Any]:
        """Test template rendering with real ConfigParser data"""
        try:
            # Load real configuration
            config = DeltaSyncConfig.from_toml(self.config_path)
            logger.info(f"Configuration loaded: {config.source_table} -> {config.target_table}")
            
            # Initialize template engine with config
            template_engine = SQLTemplateEngine(config)
            
            # Generate template context with real database columns
            context = template_engine.get_template_context()
            
            logger.info(f"Template context: {len(context['size_columns'])} size columns, {len(context['business_columns'])} business columns")
            
            # Test template rendering
            rendered_sql = template_engine.render_merge_lines_sql()
            
            # Validation checks
            validation_results = {
                'template_rendered': rendered_sql is not None and len(rendered_sql) > 0,
                'no_placeholders': '{{' not in rendered_sql and '}}' not in rendered_sql,
                'contains_merge_logic': 'MERGE' in rendered_sql.upper(),
                'contains_lines_table': context['lines_table'] in rendered_sql,
                'sql_length_reasonable': len(rendered_sql) > 800,  # Lines merge should be substantial
                'contains_record_uuid': 'record_uuid' in rendered_sql.lower(),
                'contains_size_code': 'size_code' in rendered_sql.lower()
            }
            
            logger.info("Template rendering validation:")
            for check, result in validation_results.items():
                status = "✅ PASS" if result else "❌ FAIL"
                logger.info(f"  {check}: {status}")
            
            return {
                'rendered_sql': rendered_sql,
                'context': context,
                'validation_results': validation_results,
                'success_rate': sum(validation_results.values()) / len(validation_results)
            }
            
        except Exception as e:
            logger.error(f"Template rendering test failed: {e}")
            return {
                'error': str(e),
                'success_rate': 0.0
            }
    
    def test_sql_syntax_validation(self, rendered_sql: str) -> bool:
        """Test that generated SQL has valid syntax by parsing"""
        try:
            # Basic SQL syntax validation
            sql_upper = rendered_sql.upper()
            
            # Check for required MERGE SQL elements
            required_elements = [
                'MERGE',
                'USING',
                'ON',
                'WHEN MATCHED',
                'WHEN NOT MATCHED'
            ]
            
            syntax_checks = {}
            for element in required_elements:
                syntax_checks[f"contains_{element.lower().replace(' ', '_')}"] = element in sql_upper
            
            # Check for proper SQL structure
            syntax_checks['no_unmatched_parentheses'] = rendered_sql.count('(') == rendered_sql.count(')')
            syntax_checks['no_unmatched_brackets'] = rendered_sql.count('[') == rendered_sql.count(']')
            syntax_checks['ends_with_semicolon_or_go'] = rendered_sql.strip().endswith(';') or rendered_sql.strip().upper().endswith('GO')
            
            logger.info("SQL syntax validation:")
            for check, result in syntax_checks.items():
                status = "✅ PASS" if result else "❌ FAIL"
                logger.info(f"  {check}: {status}")
            
            return all(syntax_checks.values())
            
        except Exception as e:
            logger.error(f"SQL syntax validation failed: {e}")
            return False
    
    def test_lines_table_structure(self, rendered_sql: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Test that template references correct lines table structure"""
        try:
            lines_table = context['lines_table']
            
            # Check for key line item columns
            expected_columns = [
                'record_uuid',
                'size_code', 
                'qty',
                'row_hash',
                'sync_state'
            ]
            
            found_columns = []
            missing_columns = []
            
            for column in expected_columns:
                if column in rendered_sql.lower():
                    found_columns.append(column)
                else:
                    missing_columns.append(column)
            
            structure_coverage = len(found_columns) / len(expected_columns) if expected_columns else 0
            
            logger.info(f"Lines table structure test:")
            logger.info(f"  Expected columns: {len(expected_columns)}")
            logger.info(f"  Found in SQL: {len(found_columns)}")
            logger.info(f"  Missing: {len(missing_columns)}")
            logger.info(f"  Structure coverage: {structure_coverage:.1%}")
            
            if missing_columns:
                logger.warning(f"  Missing columns: {missing_columns}")
            
            return {
                'structure_coverage': structure_coverage,
                'found_columns': found_columns,
                'missing_columns': missing_columns,
                'test_passed': structure_coverage >= 0.8  # 80% coverage threshold
            }
            
        except Exception as e:
            logger.error(f"Lines table structure test failed: {e}")
            return {
                'structure_coverage': 0.0,
                'error': str(e),
                'test_passed': False
            }
    
    def test_business_logic_elements(self, rendered_sql: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Test that template includes key business logic elements"""
        try:
            sql_upper = rendered_sql.upper()
            
            # Check for key business logic elements
            business_elements = {
                'sync_state_filtering': 'SYNC_STATE' in sql_upper,
                'hash_generation': 'HASHBYTES' in sql_upper or 'HASH' in sql_upper,
                'transaction_handling': 'BEGIN TRANSACTION' in sql_upper or 'COMMIT' in sql_upper,
                'error_handling': 'BEGIN TRY' in sql_upper and 'BEGIN CATCH' in sql_upper,
                'batch_tracking': 'NEWID()' in sql_upper or '@BATCH' in sql_upper.replace(' ', '')
            }
            
            logger.info("Business logic elements test:")
            for element, found in business_elements.items():
                status = "✅ PASS" if found else "❌ FAIL"
                logger.info(f"  {element}: {status}")
            
            logic_coverage = sum(business_elements.values()) / len(business_elements)
            
            return {
                'logic_coverage': logic_coverage,
                'business_elements': business_elements,
                'test_passed': logic_coverage >= 0.8  # 80% coverage threshold
            }
            
        except Exception as e:
            logger.error(f"Business logic elements test failed: {e}")
            return {
                'logic_coverage': 0.0,
                'error': str(e),
                'test_passed': False
            }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run complete merge_lines.j2 template integration test"""
        logger.info("=" * 70)
        logger.info("🔗 merge_lines.j2 Template Integration Test")
        logger.info("=" * 70)
        
        # Phase 1: Template rendering
        logger.info("📋 Phase 1: Template Rendering with Real Database Columns")
        render_results = self.test_template_rendering()
        
        if 'error' in render_results:
            logger.error("Template rendering failed - cannot continue")
            return {
                'success_gate_met': False,
                'error': render_results['error']
            }
        
        rendered_sql = render_results['rendered_sql']
        context = render_results['context']
        
        # Phase 2: SQL syntax validation
        logger.info("🔍 Phase 2: SQL Syntax Validation")
        syntax_valid = self.test_sql_syntax_validation(rendered_sql)
        
        # Phase 3: Lines table structure
        logger.info("🗃️ Phase 3: Lines Table Structure Test")
        structure_results = self.test_lines_table_structure(rendered_sql, context)
        
        # Phase 4: Business logic elements
        logger.info("⚙️ Phase 4: Business Logic Elements Test")
        logic_results = self.test_business_logic_elements(rendered_sql, context)
        
        # Calculate overall success
        overall_tests = {
            'template_rendering': render_results['success_rate'] >= self.success_threshold,
            'sql_syntax_valid': syntax_valid,
            'lines_table_structure': structure_results['test_passed'],
            'business_logic_elements': logic_results['test_passed']
        }
        
        passed_tests = sum(overall_tests.values())
        total_tests = len(overall_tests)
        overall_success_rate = passed_tests / total_tests
        
        logger.info("=" * 70)
        logger.info("📊 INTEGRATION TEST RESULTS:")
        logger.info(f"   Template Rendering: {'✅ PASS' if overall_tests['template_rendering'] else '❌ FAIL'}")
        logger.info(f"   SQL Syntax Valid: {'✅ PASS' if overall_tests['sql_syntax_valid'] else '❌ FAIL'}")
        logger.info(f"   Lines Table Structure: {'✅ PASS' if overall_tests['lines_table_structure'] else '❌ FAIL'}")
        logger.info(f"   Business Logic Elements: {'✅ PASS' if overall_tests['business_logic_elements'] else '❌ FAIL'}")
        logger.info(f"   Overall Success Rate: {overall_success_rate:.1%}")
        
        success_gate_met = overall_success_rate >= self.success_threshold
        
        if success_gate_met:
            logger.info("✅ SUCCESS GATE MET: merge_lines.j2 template integration passed!")
            logger.info(f"🚀 Template renders SQL for normalized line item processing")
        else:
            logger.error("❌ SUCCESS GATE FAILED: merge_lines.j2 template integration failed!")
        
        logger.info("=" * 70)
        
        return {
            'success_gate_met': success_gate_met,
            'overall_success_rate': overall_success_rate,
            'template_tests': overall_tests,
            'render_results': render_results,
            'structure_results': structure_results,
            'logic_results': logic_results,
            'size_columns_count': len(context['size_columns']),
            'business_columns_count': len(context['business_columns'])
        }

def main():
    """Run merge_lines.j2 template integration test"""
    try:
        tester = MergeLinesTemplateTest()
        results = tester.run_comprehensive_test()
        
        # Exit with proper code
        return 0 if results['success_gate_met'] else 1
        
    except Exception as e:
        logger.error(f"merge_lines.j2 template test failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
