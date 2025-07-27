"""
Template-Driven Merge Orchestrator Test Suite
Test the complete V2 delta sync pipeline with Jinja2 templates and TOML configuration

Test Structure (Sub-Sub Tasks):
1. Template Engine Validation (individual template testing)
2. Orchestrator Integration Testing  
3. Complete Pipeline Dry Run
4. Individual SQL Template Rendering
5. TOML Configuration Validation

Modern Architecture: 100% TOML-driven, no hardcoded sizes, Jinja2 templates
"""

import sys
from pathlib import Path
import logging
import json
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import project modules
from src.pipelines.sync_order_list.merge_orchestrator import create_merge_orchestrator
from src.pipelines.sync_order_list.sql_template_engine import SQLTemplateEngine
from src.pipelines.sync_order_list.config_parser import load_delta_sync_config

class TemplateOrchestrorTestFramework:
    """Modern test framework for template-driven ORDER_LIST V2 pipeline"""
    
    def __init__(self):
        self.test_results = {}
        # Setup logging for test visibility
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def test_phase_1_template_engine_validation(self) -> Dict[str, Any]:
        """Phase 1: Validate SQLTemplateEngine and individual templates"""
        self.logger.info("\n🧪 PHASE 1: Template Engine Validation")
        self.logger.info("-" * 60)
        
        try:
            # Load configuration
            config = load_delta_sync_config('dev')  # Use dev environment
            template_engine = SQLTemplateEngine(config)
            
            # Test 1A: Template context validation
            self.logger.info("1A. Testing template context validation...")
            context_validation = template_engine.validate_template_context()
            
            validation_success = context_validation.get('valid', False)
            self.logger.info(f"Template context valid: {validation_success}")
            
            if validation_success:
                context_summary = context_validation.get('context_summary', {})
                self.logger.info(f"  Size columns detected: {context_summary.get('size_columns_count', 0)}")
                self.logger.info(f"  Database config: {context_summary.get('database_configured', False)}")
                self.logger.info(f"  Table names: {context_summary.get('table_names_configured', False)}")
            
            # Test 1B: Individual template rendering
            template_tests = {
                'merge_headers': template_engine.render_merge_headers_sql,
                'unpivot_sizes': template_engine.render_unpivot_sizes_sql,
                'merge_lines': template_engine.render_merge_lines_sql
            }
            
            template_results = {}
            for template_name, render_method in template_tests.items():
                self.logger.info(f"1B. Testing {template_name} template rendering...")
                try:
                    sql_output = render_method()
                    template_results[template_name] = {
                        'success': True,
                        'sql_length': len(sql_output),
                        'has_dynamic_sizes': 'SIZE_' in sql_output,
                        'has_placeholders': '{{' not in sql_output  # Should be rendered
                    }
                    self.logger.info(f"  ✅ {template_name}: {len(sql_output)} chars generated")
                    
                except Exception as e:
                    template_results[template_name] = {
                        'success': False,
                        'error': str(e)
                    }
                    self.logger.error(f"  ❌ {template_name}: {e}")
            
            # Calculate phase success
            all_templates_success = all(result['success'] for result in template_results.values())
            phase_success = validation_success and all_templates_success
            
            return {
                'success': phase_success,
                'context_validation': context_validation,
                'template_results': template_results,
                'phase': 'template_engine_validation'
            }
            
        except Exception as e:
            self.logger.exception(f"Phase 1 failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'phase': 'template_engine_validation'
            }
    
    def test_phase_2_orchestrator_integration(self) -> Dict[str, Any]:
        """Phase 2: Test MergeOrchestrator integration with templates"""
        self.logger.info("\n🔧 PHASE 2: Orchestrator Integration")
        self.logger.info("-" * 60)
        
        try:
            # Create orchestrator
            self.logger.info("2A. Creating merge orchestrator...")
            orchestrator = create_merge_orchestrator('dev')
            
            # Test 2B: Prerequisites validation
            self.logger.info("2B. Testing prerequisites validation...")
            prerequisites = orchestrator.validate_prerequisites()
            
            prereq_success = prerequisites.get('success', False)
            self.logger.info(f"Prerequisites validation: {prereq_success}")
            
            if prereq_success:
                validations = prerequisites.get('validations', {})
                for validation_name, details in validations.items():
                    status = "✅" if details.get('success', False) else "❌"
                    self.logger.info(f"  {status} {validation_name}")
            
            # Test 2C: NEW order detection capability
            self.logger.info("2C. Testing NEW order detection...")
            if prereq_success:
                try:
                    # This tests the logic but won't modify data
                    existing_orders = orchestrator.get_existing_aag_orders()
                    detection_success = isinstance(existing_orders, set)
                    self.logger.info(f"  Existing orders retrieved: {len(existing_orders)} records")
                except Exception as e:
                    detection_success = False
                    self.logger.error(f"  NEW order detection failed: {e}")
            else:
                detection_success = False
                self.logger.warning("  Skipping NEW order detection - prerequisites failed")
            
            return {
                'success': prereq_success and detection_success,
                'prerequisites': prerequisites,
                'detection_capability': detection_success,
                'phase': 'orchestrator_integration'
            }
            
        except Exception as e:
            self.logger.exception(f"Phase 2 failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'phase': 'orchestrator_integration'
            }
    
    def test_phase_3_complete_dry_run(self) -> Dict[str, Any]:
        """Phase 3: Execute complete pipeline in dry run mode"""
        self.logger.info("\n🏃‍♂️ PHASE 3: Complete Pipeline Dry Run")
        self.logger.info("-" * 60)
        
        try:
            # Create orchestrator and execute dry run
            orchestrator = create_merge_orchestrator('dev')
            
            self.logger.info("3A. Executing complete merge sequence (DRY RUN)...")
            
            # Execute complete pipeline in dry run
            result = orchestrator.execute_merge_sequence(
                new_orders_only=True,  # Focus on NEW orders
                dry_run=True          # Safe validation mode
            )
            
            success = result.get('success', False)
            self.logger.info(f"Complete pipeline dry run: {success}")
            
            # Analyze operation results
            if success:
                operations = result.get('operations', {})
                for op_name, op_result in operations.items():
                    op_success = op_result.get('success', False)
                    status = "✅" if op_success else "❌"
                    
                    if op_result.get('dry_run', False):
                        sql_generated = op_result.get('sql_generated', 0)
                        self.logger.info(f"  {status} {op_name}: {sql_generated} chars SQL generated")
                    else:
                        records = op_result.get('records_affected', 0)
                        self.logger.info(f"  {status} {op_name}: {records} records")
                
                total_duration = result.get('total_duration_seconds', 0)
                self.logger.info(f"Total pipeline duration: {total_duration}s")
            else:
                error = result.get('error', 'Unknown error')
                self.logger.error(f"Pipeline failed: {error}")
            
            return {
                'success': success,
                'pipeline_result': result,
                'phase': 'complete_dry_run'
            }
            
        except Exception as e:
            self.logger.exception(f"Phase 3 failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'phase': 'complete_dry_run'
            }
    
    def test_phase_4_individual_sql_validation(self) -> Dict[str, Any]:
        """Phase 4: Validate individual SQL templates (sub-sub task approach)"""
        self.logger.info("\n📝 PHASE 4: Individual SQL Template Validation")
        self.logger.info("-" * 60)
        
        try:
            config = load_delta_sync_config('dev')
            template_engine = SQLTemplateEngine(config)
            
            # Test each template individually for SQL validity
            sql_tests = {
                'merge_headers': {
                    'method': template_engine.render_merge_headers_sql,
                    'expected_keywords': ['MERGE', 'ORDER_LIST_V2', 'OUTPUT', 'INSERTED', 'DELETED']
                },
                'unpivot_sizes': {
                    'method': template_engine.render_unpivot_sizes_sql,
                    'expected_keywords': ['UNPIVOT', 'ORDER_LIST_LINES', 'SIZE_', 'size_code']
                },
                'merge_lines': {
                    'method': template_engine.render_merge_lines_sql,
                    'expected_keywords': ['MERGE', 'ORDER_LIST_LINES', 'record_uuid', 'OUTPUT']
                }
            }
            
            sql_validation_results = {}
            
            for template_name, test_config in sql_tests.items():
                self.logger.info(f"4A. Validating {template_name} SQL template...")
                
                try:
                    # Render SQL
                    sql_output = test_config['method']()
                    
                    # Check for expected keywords
                    keyword_checks = {}
                    for keyword in test_config['expected_keywords']:
                        keyword_checks[keyword] = keyword in sql_output
                    
                    all_keywords_present = all(keyword_checks.values())
                    
                    # Check for no unrendered placeholders
                    no_placeholders = '{{' not in sql_output and '}}' not in sql_output
                    
                    sql_validation_results[template_name] = {
                        'success': all_keywords_present and no_placeholders,
                        'sql_length': len(sql_output),
                        'keyword_checks': keyword_checks,
                        'no_placeholders': no_placeholders,
                        'sql_preview': sql_output[:200] + '...' if len(sql_output) > 200 else sql_output
                    }
                    
                    if all_keywords_present and no_placeholders:
                        self.logger.info(f"  ✅ {template_name}: Valid SQL generated ({len(sql_output)} chars)")
                    else:
                        self.logger.warning(f"  ⚠️ {template_name}: SQL validation issues detected")
                        
                except Exception as e:
                    sql_validation_results[template_name] = {
                        'success': False,
                        'error': str(e)
                    }
                    self.logger.error(f"  ❌ {template_name}: {e}")
            
            all_sql_valid = all(result['success'] for result in sql_validation_results.values())
            
            return {
                'success': all_sql_valid,
                'sql_validations': sql_validation_results,
                'phase': 'individual_sql_validation'
            }
            
        except Exception as e:
            self.logger.exception(f"Phase 4 failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'phase': 'individual_sql_validation'
            }
    
    def test_phase_5_toml_configuration_analysis(self) -> Dict[str, Any]:
        """Phase 5: Deep TOML configuration validation"""
        self.logger.info("\n⚙️ PHASE 5: TOML Configuration Analysis")
        self.logger.info("-" * 60)
        
        try:
            # Load and analyze TOML configuration
            config = load_delta_sync_config('dev')
            
            # Test 5A: Size column detection
            self.logger.info("5A. Analyzing size column configuration...")
            size_config = config.get_size_columns_config()
            
            size_columns_detected = len(size_config.get('size_columns', []))
            self.logger.info(f"  Size columns detected: {size_columns_detected}")
            
            if size_columns_detected > 0:
                # Show first few size columns
                first_few = size_config['size_columns'][:5]
                self.logger.info(f"  First 5 size columns: {first_few}")
            
            # Test 5B: Database configuration
            self.logger.info("5B. Validating database configuration...")
            db_config = {
                'source_table': config.get_full_table_name('source'),
                'target_table': config.get_full_table_name('target'), 
                'lines_table': config.get_full_table_name('lines'),
                'database_connection': config.database_connection
            }
            
            for config_name, config_value in db_config.items():
                self.logger.info(f"  {config_name}: {config_value}")
            
            # Test 5C: Template context generation
            self.logger.info("5C. Testing template context generation...")
            template_engine = SQLTemplateEngine(config)
            context = template_engine.get_template_context()
            
            context_keys = list(context.keys())
            self.logger.info(f"  Template context keys: {context_keys}")
            self.logger.info(f"  Size columns in context: {len(context.get('size_columns', []))}")
            
            # Success criteria
            config_success = (
                size_columns_detected > 0 and
                all(db_config.values()) and
                len(context_keys) > 0
            )
            
            return {
                'success': config_success,
                'size_columns_detected': size_columns_detected,
                'database_config': db_config,
                'template_context_keys': context_keys,
                'phase': 'toml_configuration_analysis'
            }
            
        except Exception as e:
            self.logger.exception(f"Phase 5 failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'phase': 'toml_configuration_analysis'
            }
    
    def run_complete_test_suite(self) -> Dict[str, Any]:
        """Execute all test phases and compile comprehensive results"""
        self.logger.info("🚀 Starting Template-Driven Merge Orchestrator Test Suite")
        self.logger.info("=" * 80)
        
        # Execute all test phases
        test_phases = [
            self.test_phase_1_template_engine_validation,
            self.test_phase_2_orchestrator_integration,
            self.test_phase_3_complete_dry_run,
            self.test_phase_4_individual_sql_validation,
            self.test_phase_5_toml_configuration_analysis
        ]
        
        phase_results = {}
        overall_success = True
        
        for phase_method in test_phases:
            try:
                result = phase_method()
                phase_name = result.get('phase', phase_method.__name__)
                phase_results[phase_name] = result
                
                if not result.get('success', False):
                    overall_success = False
                    
            except Exception as e:
                phase_name = phase_method.__name__
                phase_results[phase_name] = {
                    'success': False,
                    'error': str(e),
                    'phase': phase_name
                }
                overall_success = False
                self.logger.exception(f"Test phase {phase_name} crashed: {e}")
        
        # Compile final results
        self.logger.info("\n📊 TEST SUITE SUMMARY")
        self.logger.info("=" * 80)
        
        successful_phases = 0
        total_phases = len(phase_results)
        
        for phase_name, result in phase_results.items():
            success = result.get('success', False)
            status = "✅ PASS" if success else "❌ FAIL"
            self.logger.info(f"  {status} {phase_name}")
            
            if success:
                successful_phases += 1
            else:
                error = result.get('error', 'Phase validation failed')
                self.logger.info(f"    Error: {error}")
        
        success_rate = (successful_phases / total_phases * 100) if total_phases > 0 else 0
        
        self.logger.info(f"\nOverall Success Rate: {success_rate:.1f}% ({successful_phases}/{total_phases} phases)")
        
        if overall_success:
            self.logger.info("🎉 ALL TESTS PASSED - Template-driven pipeline ready!")
        else:
            self.logger.warning("⚠️ Some tests failed - Review phase results above")
        
        return {
            'success': overall_success,
            'success_rate': success_rate,
            'successful_phases': successful_phases,
            'total_phases': total_phases,
            'phase_results': phase_results,
            'test_suite': 'template_driven_merge_orchestrator'
        }


def main():
    """Run template-driven merge orchestrator test suite"""
    try:
        # Create and run test framework
        test_framework = TemplateOrchestrorTestFramework()
        results = test_framework.run_complete_test_suite()
        
        # Export results for analysis
        results_file = Path(__file__).parent.parent / 'test_results' / 'template_orchestrator_results.json'
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📁 Test results saved to: {results_file}")
        
        # Exit with appropriate code
        exit_code = 0 if results['success'] else 1
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"❌ Test suite crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
