"""
Test: Size Column Detection Issue Analysis
=========================================
Purpose: Diagnose why XL column isn't being detected in template size discovery
Context: Template generates 245 size columns but excludes XL which has 52 records with data
Strategy: Test size detection logic vs actual data availability

CRITICAL ISSUE:
- ORDER_LIST_V2 has 52 records with XL > 0
- Template discovers 245 size columns but creates 0 records
- Root cause: XL column might not be in size detection range

TEST OUTCOMES:
✅ PASS: XL is in detected size columns AND has data
❌ FAIL: XL is missing from detected columns OR detection logic is wrong
"""

import sys
from pathlib import Path

# Legacy transition support pattern (VALIDATED)
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

# Modern imports from project (VALIDATED PATTERN)
from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.sql_template_engine import SQLTemplateEngine

logger = logger.get_logger(__name__)

class SizeColumnDetectionTest:
    """Test size column detection vs actual data availability"""
    
    def __init__(self):
        # Use same config pattern as working integration test
        config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
        self.config = DeltaSyncConfig.from_toml(config_path)
        self.template_engine = SQLTemplateEngine(self.config)
        
        logger.info("🔍 Size Column Detection Test Initialized")
    
    def run_complete_test(self):
        """Run complete size column detection analysis"""
        
        results = {
            'size_detection_results': None,
            'xl_data_validation': None,
            'column_range_analysis': None,
            'template_validation': None,
            'final_diagnosis': None
        }
        
        print("="*80)
        print("🧪 SIZE COLUMN DETECTION ISSUE ANALYSIS")
        print("="*80)
        
        # Test 1: Size detection results
        print("\n📋 Test 1: Size Column Detection Results")
        results['size_detection_results'] = self._test_size_detection()
        
        # Test 2: XL data validation
        print("\n📋 Test 2: XL Column Data Validation")
        results['xl_data_validation'] = self._validate_xl_data()
        
        # Test 3: Column range analysis
        print("\n📋 Test 3: Column Range Analysis")
        results['column_range_analysis'] = self._analyze_column_range()
        
        # Test 4: Template validation
        print("\n📋 Test 4: Template Generation Validation")
        results['template_validation'] = self._validate_template_generation()
        
        # Final diagnosis
        print("\n📋 Final Diagnosis")
        results['final_diagnosis'] = self._generate_final_diagnosis(results)
        
        return results
    
    def _test_size_detection(self):
        """Test the size column detection logic"""
        
        try:
            # Get detected size columns
            size_columns = self.config.get_dynamic_size_columns()
            
            results = {
                'total_detected': len(size_columns),
                'xl_detected': 'XL' in size_columns,
                'xl_variations_detected': [col for col in size_columns if 'XL' in col.upper()],
                'sample_columns': size_columns[:10] if size_columns else [],
                'detection_successful': len(size_columns) > 0
            }
            
            print(f"✅ Total columns detected: {results['total_detected']}")
            print(f"✅ XL in detected columns: {results['xl_detected']}")
            print(f"✅ XL variations found: {results['xl_variations_detected']}")
            print(f"✅ Sample columns: {results['sample_columns']}")
            
            return results
            
        except Exception as e:
            error_result = {
                'total_detected': 0,
                'xl_detected': False,
                'xl_variations_detected': [],
                'sample_columns': [],
                'detection_successful': False,
                'error': str(e)
            }
            
            print(f"❌ Size detection failed: {str(e)}")
            return error_result
    
    def _validate_xl_data(self):
        """Validate XL column has data in ORDER_LIST_V2"""
        
        queries = {
            'xl_column_exists': """
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'ORDER_LIST_V2' 
                AND COLUMN_NAME = 'XL'
            """,
            'xl_data_count': """
                SELECT COUNT(*) 
                FROM ORDER_LIST_V2 
                WHERE [XL] IS NOT NULL
            """,
            'xl_nonzero_count': """
                SELECT COUNT(*) 
                FROM ORDER_LIST_V2 
                WHERE [XL] > 0
            """,
            'xl_pending_nonzero': """
                SELECT COUNT(*) 
                FROM ORDER_LIST_V2 
                WHERE sync_state = 'PENDING' AND [XL] > 0
            """
        }
        
        results = {}
        
        with db.get_connection(self.config.db_key) as conn:
            cursor = conn.cursor()
            
            for test_name, query in queries.items():
                try:
                    cursor.execute(query)
                    result = cursor.fetchone()
                    count = result[0] if result else 0
                    results[test_name] = count
                    print(f"✅ {test_name}: {count}")
                    
                except Exception as e:
                    results[test_name] = f"ERROR: {str(e)}"
                    print(f"❌ {test_name}: {str(e)}")
        
        return results
    
    def _analyze_column_range(self):
        """Analyze what columns exist between UNIT OF MEASURE and TOTAL QTY markers"""
        
        column_range_query = """
        SELECT COLUMN_NAME, ORDINAL_POSITION
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'ORDER_LIST_V2'
        ORDER BY ORDINAL_POSITION
        """
        
        results = {
            'all_columns': [],
            'unit_of_measure_position': None,
            'total_qty_position': None,
            'xl_position': None,
            'columns_in_range': [],
            'xl_in_detection_range': False
        }
        
        with db.get_connection(self.config.db_key) as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute(column_range_query)
                columns = cursor.fetchall()
                
                for column_name, position in columns:
                    results['all_columns'].append((column_name, position))
                    
                    if column_name == 'UNIT OF MEASURE':
                        results['unit_of_measure_position'] = position
                    elif column_name == 'TOTAL QTY':
                        results['total_qty_position'] = position
                    elif column_name == 'XL':
                        results['xl_position'] = position
                
                # Determine columns in detection range
                if results['unit_of_measure_position'] and results['total_qty_position']:
                    start_pos = results['unit_of_measure_position']
                    end_pos = results['total_qty_position']
                    
                    results['columns_in_range'] = [
                        col for col, pos in results['all_columns']
                        if start_pos < pos < end_pos
                    ]
                    
                    # Check if XL is in range
                    if results['xl_position']:
                        results['xl_in_detection_range'] = start_pos < results['xl_position'] < end_pos
                
                print(f"✅ Total columns in table: {len(results['all_columns'])}")
                print(f"✅ UNIT OF MEASURE position: {results['unit_of_measure_position']}")
                print(f"✅ TOTAL QTY position: {results['total_qty_position']}")
                print(f"✅ XL position: {results['xl_position']}")
                print(f"✅ Columns in detection range: {len(results['columns_in_range'])}")
                print(f"✅ XL in detection range: {results['xl_in_detection_range']}")
                
                return results
                
            except Exception as e:
                results['error'] = str(e)
                print(f"❌ Column range analysis failed: {str(e)}")
                return results
    
    def _validate_template_generation(self):
        """Validate template generation includes XL column"""
        
        try:
            # Generate template SQL
            template_sql = self.template_engine.render_unpivot_sizes_direct_sql()
            
            results = {
                'template_generated': True,
                'sql_length': len(template_sql),
                'xl_in_template': '[XL]' in template_sql,
                'unpivot_clause_found': 'UNPIVOT' in template_sql,
                'template_preview': template_sql[:200] + "..." if len(template_sql) > 200 else template_sql
            }
            
            print(f"✅ Template generated: {results['template_generated']}")
            print(f"✅ SQL length: {results['sql_length']:,} characters")
            print(f"✅ XL in template: {results['xl_in_template']}")
            print(f"✅ UNPIVOT clause found: {results['unpivot_clause_found']}")
            
            return results
            
        except Exception as e:
            results = {
                'template_generated': False,
                'sql_length': 0,
                'xl_in_template': False,
                'unpivot_clause_found': False,
                'error': str(e)
            }
            
            print(f"❌ Template generation failed: {str(e)}")
            return results
    
    def _generate_final_diagnosis(self, results):
        """Generate final diagnosis based on all test results"""
        
        diagnosis = {
            'root_cause_identified': False,
            'root_cause': None,
            'recommended_fix': None,
            'test_summary': {}
        }
        
        # Analyze results
        size_detection = results.get('size_detection_results', {})
        xl_validation = results.get('xl_data_validation', {})
        column_range = results.get('column_range_analysis', {})
        template_validation = results.get('template_validation', {})
        
        # Test summary
        diagnosis['test_summary'] = {
            'xl_has_data': xl_validation.get('xl_pending_nonzero', 0) > 0,
            'xl_detected_in_config': size_detection.get('xl_detected', False),
            'xl_in_detection_range': column_range.get('xl_in_detection_range', False),
            'xl_in_template': template_validation.get('xl_in_template', False)
        }
        
        # Determine root cause
        if not diagnosis['test_summary']['xl_has_data']:
            diagnosis['root_cause'] = "No XL data available in PENDING records"
            diagnosis['recommended_fix'] = "Check data loading process"
        elif not diagnosis['test_summary']['xl_in_detection_range']:
            diagnosis['root_cause'] = "XL column is outside detection range (UNIT OF MEASURE to TOTAL QTY)"
            diagnosis['recommended_fix'] = "Update size detection range in TOML config or move XL column"
        elif not diagnosis['test_summary']['xl_detected_in_config']:
            diagnosis['root_cause'] = "Size detection logic is not finding XL column"
            diagnosis['recommended_fix'] = "Debug get_dynamic_size_columns() method"
        elif not diagnosis['test_summary']['xl_in_template']:
            diagnosis['root_cause'] = "Template generation is excluding XL column"
            diagnosis['recommended_fix'] = "Debug template rendering logic"
        else:
            diagnosis['root_cause'] = "All validation passes but template still fails - complex MERGE issue"
            diagnosis['recommended_fix'] = "Simplify MERGE template logic"
        
        diagnosis['root_cause_identified'] = diagnosis['root_cause'] is not None
        
        print(f"\n🎯 ROOT CAUSE: {diagnosis['root_cause']}")
        print(f"🔧 RECOMMENDED FIX: {diagnosis['recommended_fix']}")
        
        print(f"\n📊 TEST SUMMARY:")
        for test_name, result in diagnosis['test_summary'].items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name}: {status}")
        
        return diagnosis


def main():
    """Run the complete size column detection test"""
    
    try:
        test = SizeColumnDetectionTest()
        results = test.run_complete_test()
        
        # Print final results
        final_diagnosis = results['final_diagnosis']
        
        if final_diagnosis['root_cause_identified']:
            print(f"\n🎉 SUCCESS: Root cause identified!")
            print(f"🚨 ISSUE: {final_diagnosis['root_cause']}")
            print(f"🔧 FIX: {final_diagnosis['recommended_fix']}")
            return True
        else:
            print(f"\n❌ FAILURE: Could not identify root cause")
            return False
        
    except Exception as e:
        logger.exception(f"❌ Size column detection test failed: {e}")
        print(f"❌ Test execution failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
