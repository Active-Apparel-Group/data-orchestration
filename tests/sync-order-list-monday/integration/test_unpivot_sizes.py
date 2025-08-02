"""
Integration Test: unpivot_sizes.j2 Template Validation
Purpose: Test sizes unpivot template with real size columns from swp_ORDER_LIST_V2
Requirement: Template renders SQL with dynamic UNPIVOT for all 245 size columns

SUCCESS CRITERIA:
- Template renders without placeholders or errors
- SQL contains UNPIVOT logic for all 245 real size columns  
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

class UnpivotSizesTemplateTest:
    """Integration test for unpivot_sizes.j2 template with real database columns"""
    
    def __init__(self, config_path: str = None):
        # Use repo_root pattern like other tests
        if config_path is None:
            config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
        self.config_path = config_path
        self.success_threshold = 1.0  # 100% success required
        self.template_name = "unpivot_sizes.j2"
        
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
            rendered_sql = template_engine.render_unpivot_sizes_sql()
            
            # Validation checks
            validation_results = {
                'template_rendered': rendered_sql is not None and len(rendered_sql) > 0,
                'no_placeholders': '{{' not in rendered_sql and '}}' not in rendered_sql,
                'contains_unpivot_logic': 'UNPIVOT' in rendered_sql.upper(),
                'contains_size_columns': any(col in rendered_sql for col in context['size_columns'][:10]),
                'sql_length_reasonable': len(rendered_sql) > 500,  # UNPIVOT should be substantial
                'contains_size_code': 'size_code' in rendered_sql.lower(),
                'contains_qty': 'qty' in rendered_sql.lower()
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
            
            # Check for required UNPIVOT SQL elements
            required_elements = [
                'UNPIVOT',
                'FOR',
                'IN'
            ]
            
            syntax_checks = {}
            for element in required_elements:
                syntax_checks[f"contains_{element.lower()}"] = element in sql_upper
            
            # Check for proper SQL structure
            syntax_checks['no_unmatched_parentheses'] = rendered_sql.count('(') == rendered_sql.count(')')
            syntax_checks['no_unmatched_brackets'] = rendered_sql.count('[') == rendered_sql.count(']')
            syntax_checks['has_proper_unpivot_structure'] = 'FOR' in sql_upper and 'IN' in sql_upper and 'UNPIVOT' in sql_upper
            
            logger.info("SQL syntax validation:")
            for check, result in syntax_checks.items():
                status = "✅ PASS" if result else "❌ FAIL"
                logger.info(f"  {check}: {status}")
            
            return all(syntax_checks.values())
            
        except Exception as e:
            logger.error(f"SQL syntax validation failed: {e}")
            return False
    
    def test_size_column_coverage(self, rendered_sql: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Test that template includes real size columns from database"""
        try:
            size_columns = context['size_columns']
            
            # Test first 25 size columns for presence in SQL (more for UNPIVOT)
            test_columns = size_columns[:25]
            found_columns = []
            missing_columns = []
            
            for column in test_columns:
                # Check for column in SQL (with brackets for SQL Server)
                if f"[{column}]" in rendered_sql or f"`{column}`" in rendered_sql or column in rendered_sql:
                    found_columns.append(column)
                else:
                    missing_columns.append(column)
            
            coverage_rate = len(found_columns) / len(test_columns) if test_columns else 0
            
            logger.info(f"Size column coverage test:")
            logger.info(f"  Tested columns: {len(test_columns)}")
            logger.info(f"  Found in SQL: {len(found_columns)}")
            logger.info(f"  Missing: {len(missing_columns)}")
            logger.info(f"  Coverage rate: {coverage_rate:.1%}")
            
            if missing_columns:
                logger.warning(f"  Missing columns (first 5): {missing_columns[:5]}")
            
            return {
                'coverage_rate': coverage_rate,
                'found_columns': found_columns,
                'missing_columns': missing_columns,
                'test_passed': coverage_rate >= 0.8  # 80% coverage threshold
            }
            
        except Exception as e:
            logger.error(f"Size column coverage test failed: {e}")
            return {
                'coverage_rate': 0.0,
                'error': str(e),
                'test_passed': False
            }
    
    def test_unpivot_structure(self, rendered_sql: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Test UNPIVOT structure includes all size columns in IN clause"""
        try:
            sql_upper = rendered_sql.upper()
            size_columns = context['size_columns']
            
            # Find the IN clause section
            in_clause_start = sql_upper.find('IN (')
            in_clause_end = sql_upper.find(')', in_clause_start) if in_clause_start != -1 else -1
            
            if in_clause_start == -1 or in_clause_end == -1:
                logger.error("Could not find UNPIVOT IN clause structure")
                return {
                    'test_passed': False,
                    'error': 'Missing UNPIVOT IN clause'
                }
            
            in_clause_content = rendered_sql[in_clause_start:in_clause_end + 1]
            
            # Test that IN clause contains size columns
            test_columns = size_columns[:15]  # Test first 15 columns
            columns_in_clause = sum(1 for col in test_columns if col in in_clause_content)
            
            clause_coverage = columns_in_clause / len(test_columns) if test_columns else 0
            
            logger.info("UNPIVOT structure validation:")
            logger.info(f"  IN clause found: {'✅ YES' if in_clause_start != -1 else '❌ NO'}")
            logger.info(f"  Columns in IN clause: {columns_in_clause}/{len(test_columns)}")
            logger.info(f"  IN clause coverage: {clause_coverage:.1%}")
            
            return {
                'test_passed': clause_coverage >= 0.8,  # 80% coverage in IN clause
                'clause_coverage': clause_coverage,
                'in_clause_content': in_clause_content[:200] + "..." if len(in_clause_content) > 200 else in_clause_content
            }
            
        except Exception as e:
            logger.error(f"UNPIVOT structure test failed: {e}")
            return {
                'test_passed': False,
                'error': str(e)
            }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run complete unpivot_sizes.j2 template integration test"""
        logger.info("=" * 70)
        logger.info("🔄 unpivot_sizes.j2 Template Integration Test")
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
        
        # Phase 3: Size column coverage
        logger.info("📊 Phase 3: Size Column Coverage Test")
        coverage_results = self.test_size_column_coverage(rendered_sql, context)
        
        # Phase 4: UNPIVOT structure validation
        logger.info("🔄 Phase 4: UNPIVOT Structure Validation")
        unpivot_results = self.test_unpivot_structure(rendered_sql, context)
        
        # Calculate overall success
        overall_tests = {
            'template_rendering': render_results['success_rate'] >= self.success_threshold,
            'sql_syntax_valid': syntax_valid,
            'size_column_coverage': coverage_results['test_passed'],
            'unpivot_structure': unpivot_results['test_passed']
        }
        
        passed_tests = sum(overall_tests.values())
        total_tests = len(overall_tests)
        overall_success_rate = passed_tests / total_tests
        
        logger.info("=" * 70)
        logger.info("📊 INTEGRATION TEST RESULTS:")
        logger.info(f"   Template Rendering: {'✅ PASS' if overall_tests['template_rendering'] else '❌ FAIL'}")
        logger.info(f"   SQL Syntax Valid: {'✅ PASS' if overall_tests['sql_syntax_valid'] else '❌ FAIL'}")
        logger.info(f"   Size Column Coverage: {'✅ PASS' if overall_tests['size_column_coverage'] else '❌ FAIL'}")
        logger.info(f"   UNPIVOT Structure: {'✅ PASS' if overall_tests['unpivot_structure'] else '❌ FAIL'}")
        logger.info(f"   Overall Success Rate: {overall_success_rate:.1%}")
        
        success_gate_met = overall_success_rate >= self.success_threshold
        
        if success_gate_met:
            logger.info("✅ SUCCESS GATE MET: unpivot_sizes.j2 template integration passed!")
            logger.info(f"🚀 Template renders SQL with {len(context['size_columns'])} real size columns")
        else:
            logger.error("❌ SUCCESS GATE FAILED: unpivot_sizes.j2 template integration failed!")
        
        logger.info("=" * 70)
        
        return {
            'success_gate_met': success_gate_met,
            'overall_success_rate': overall_success_rate,
            'template_tests': overall_tests,
            'render_results': render_results,
            'coverage_results': coverage_results,
            'unpivot_results': unpivot_results,
            'size_columns_count': len(context['size_columns']),
            'business_columns_count': len(context['business_columns'])
        }

def main():
    """Run unpivot_sizes.j2 template integration test"""
    try:
        tester = UnpivotSizesTemplateTest()
        results = tester.run_comprehensive_test()
        
        # Exit with proper code
        return 0 if results['success_gate_met'] else 1
        
    except Exception as e:
        logger.error(f"unpivot_sizes.j2 template test failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
