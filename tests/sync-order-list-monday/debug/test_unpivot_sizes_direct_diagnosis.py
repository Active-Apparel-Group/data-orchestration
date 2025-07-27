"""
Debug Test: unpivot_sizes_direct.j2 Diagnostic Analysis
=====================================================
Purpose: Diagnose why unpivot_sizes_direct.j2 creates 0 records despite 52/69 XL > 0 availability
Context: Task 19.14.3 - MERGE logic is correct, but UNPIVOT operation fails
Strategy: Step-by-step analysis of UNPIVOT source data, filtering, and business key matching

TEST FOCUS:
1. Validate ORDER_LIST_V2 has sync_state = 'PENDING' records (should be 69)
2. Check XL column values in those records (should be 52 > 0)
3. Test UNPIVOT operation manually to see what it produces
4. Analyze MERGE business key logic (record_uuid + size_code)
5. Identify exact point where records are lost in the pipeline

ARCHITECTURE: Keep MERGE approach, fix query logic issue
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd

# Legacy transition support pattern (PROVEN SUCCESSFUL)
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

# Modern imports from project
from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.sql_template_engine import SQLTemplateEngine

logger = logger.get_logger(__name__)

class UnpivotSizesDirectDiagnosticTest:
    """Diagnostic test for unpivot_sizes_direct.j2 template failure analysis"""
    
    def __init__(self):
        # Use the same config pattern as the working integration test
        config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
        self.config_path = config_path
        
        # Use the from_toml method like the working integration test
        self.config = DeltaSyncConfig.from_toml(self.config_path)
        self.template_engine = SQLTemplateEngine(self.config)
        
        # Table references - use property syntax like the integration test
        self.target_table = self.config.target_table      # ORDER_LIST_V2
        self.lines_table = self.config.lines_table        # ORDER_LIST_LINES
        
        logger.info(f"🔍 Diagnostic Test Initialized")
        logger.info(f"  Source Table: {self.target_table}")
        logger.info(f"  Target Table: {self.lines_table}")
    
    def run_complete_diagnosis(self) -> Dict[str, Any]:
        """Run complete diagnostic analysis of unpivot_sizes_direct template failure"""
        
        results = {
            'step1_source_validation': None,
            'step2_xl_column_analysis': None,
            'step3_unpivot_manual_test': None,
            'step4_business_key_analysis': None,
            'step5_full_template_debug': None,
            'diagnosis_summary': {}
        }
        
        logger.info("="*80)
        logger.info("🧪 UNPIVOT_SIZES_DIRECT DIAGNOSTIC TEST")
        logger.info("="*80)
        
        # Step 1: Validate source data exists with correct sync_state
        logger.info("📋 Step 1: Source Data Validation")
        results['step1_source_validation'] = self._validate_source_data()
        
        # Step 2: Analyze XL column specifically (we know 52 records have XL > 0)
        logger.info("📋 Step 2: XL Column Analysis")
        results['step2_xl_column_analysis'] = self._analyze_xl_column()
        
        # Step 3: Manual UNPIVOT test with minimal logic
        logger.info("📋 Step 3: Manual UNPIVOT Test")
        results['step3_unpivot_manual_test'] = self._test_unpivot_manually()
        
        # Step 4: Business key analysis (record_uuid + size_code uniqueness)
        logger.info("📋 Step 4: Business Key Analysis")
        results['step4_business_key_analysis'] = self._analyze_business_keys()
        
        # Step 5: Full template debug with sub-query analysis
        logger.info("📋 Step 5: Full Template Debug")
        results['step5_full_template_debug'] = self._debug_full_template()
        
        # Generate diagnosis summary
        results['diagnosis_summary'] = self._generate_diagnosis_summary(results)
        
        logger.info("="*80)
        logger.info("🎯 DIAGNOSTIC COMPLETE")
        logger.info("="*80)
        
        return results
    
    def _validate_source_data(self) -> Dict[str, Any]:
        """Step 1: Validate ORDER_LIST_V2 has expected records with sync_state = 'PENDING'"""
        
        validation_queries = {
            'total_records': f"SELECT COUNT(*) FROM {self.target_table}",
            'pending_records': f"SELECT COUNT(*) FROM {self.target_table} WHERE sync_state = 'PENDING'",
            'sync_states': f"""
                SELECT sync_state, COUNT(*) as count
                FROM {self.target_table}
                GROUP BY sync_state
                ORDER BY count DESC
            """,
            'greyson_po_4755': f"""
                SELECT COUNT(*) 
                FROM {self.target_table} 
                WHERE [CUSTOMER NAME] = 'GREYSON CLOTHIERS' 
                AND [AAG ORDER NUMBER] = '4755'
            """
        }
        
        results = {}
        
        for query_name, query_sql in validation_queries.items():
            try:
                result = db.execute(query_sql)
                if query_name == 'sync_states':
                    results[query_name] = [(row[0], row[1]) for row in result]
                else:
                    results[query_name] = result[0][0] if result else 0
                
                logger.info(f"  ✅ {query_name}: {results[query_name]}")
                
            except Exception as e:
                results[query_name] = f"ERROR: {str(e)}"
                logger.error(f"  ❌ {query_name}: {str(e)}")
        
        return results
    
    def _analyze_xl_column(self) -> Dict[str, Any]:
        """Step 2: Analyze XL column values in PENDING records"""
        
        xl_analysis_queries = {
            'xl_total_pending': f"""
                SELECT COUNT(*) 
                FROM {self.target_table} 
                WHERE sync_state = 'PENDING'
                AND [XL] IS NOT NULL
            """,
            'xl_nonzero_pending': f"""
                SELECT COUNT(*) 
                FROM {self.target_table} 
                WHERE sync_state = 'PENDING'
                AND [XL] > 0
            """,
            'xl_values_distribution': f"""
                SELECT [XL], COUNT(*) as count
                FROM {self.target_table} 
                WHERE sync_state = 'PENDING'
                AND [XL] IS NOT NULL
                GROUP BY [XL]
                ORDER BY count DESC
            """,
            'xl_sample_records': f"""
                SELECT TOP 5 record_uuid, [AAG ORDER NUMBER], [XL], sync_state
                FROM {self.target_table} 
                WHERE sync_state = 'PENDING'
                AND [XL] > 0
            """
        }
        
        results = {}
        
        for query_name, query_sql in xl_analysis_queries.items():
            try:
                result = db.execute(query_sql)
                
                if query_name in ['xl_values_distribution', 'xl_sample_records']:
                    results[query_name] = [(row[0], row[1]) for row in result] if query_name == 'xl_values_distribution' else result
                else:
                    results[query_name] = result[0][0] if result else 0
                
                logger.info(f"  ✅ {query_name}: {results[query_name]}")
                
            except Exception as e:
                results[query_name] = f"ERROR: {str(e)}"
                logger.error(f"  ❌ {query_name}: {str(e)}")
        
        return results
    
    def _test_unpivot_manually(self) -> Dict[str, Any]:
        """Step 3: Test UNPIVOT operation manually with simplified logic"""
        
        # Test just XL column unpivot first
        simple_unpivot_query = f"""
        SELECT 
            record_uuid,
            size_code,
            qty,
            sync_state
        FROM {self.target_table}
        UNPIVOT (
            qty FOR size_code IN ([XL])
        ) AS sizes
        WHERE sync_state = 'PENDING'
        AND qty > 0
        """
        
        # Test multiple size columns
        multi_size_unpivot_query = f"""
        SELECT 
            record_uuid,
            size_code,
            qty,
            sync_state
        FROM {self.target_table}
        UNPIVOT (
            qty FOR size_code IN ([XS], [S], [M], [L], [XL], [XXL])
        ) AS sizes
        WHERE sync_state = 'PENDING'
        AND qty > 0
        """
        
        results = {}
        
        # Test simple XL-only UNPIVOT
        try:
            xl_result = db.execute(simple_unpivot_query)
            results['xl_unpivot_count'] = len(xl_result)
            results['xl_unpivot_sample'] = xl_result[:5] if xl_result else []
            logger.info(f"  ✅ XL-only UNPIVOT: {results['xl_unpivot_count']} records")
            
        except Exception as e:
            results['xl_unpivot_count'] = f"ERROR: {str(e)}"
            logger.error(f"  ❌ XL-only UNPIVOT failed: {str(e)}")
        
        # Test multi-size UNPIVOT
        try:
            multi_result = db.execute_query(multi_size_unpivot_query)
            results['multi_unpivot_count'] = len(multi_result)
            results['multi_unpivot_sample'] = multi_result[:10] if multi_result else []
            logger.info(f"  ✅ Multi-size UNPIVOT: {results['multi_unpivot_count']} records")
            
        except Exception as e:
            results['multi_unpivot_count'] = f"ERROR: {str(e)}"
            logger.error(f"  ❌ Multi-size UNPIVOT failed: {str(e)}")
        
        return results
    
    def _analyze_business_keys(self) -> Dict[str, Any]:
        """Step 4: Analyze business key uniqueness (record_uuid + size_code)"""
        
        # Check if record_uuid values are unique and valid
        business_key_queries = {
            'unique_record_uuids': f"""
                SELECT COUNT(DISTINCT record_uuid) as unique_uuids,
                       COUNT(*) as total_records
                FROM {self.target_table} 
                WHERE sync_state = 'PENDING'
            """,
            'null_record_uuids': f"""
                SELECT COUNT(*) 
                FROM {self.target_table} 
                WHERE sync_state = 'PENDING' 
                AND record_uuid IS NULL
            """,
            'duplicate_business_keys': f"""
                SELECT record_uuid, COUNT(*) as duplicate_count
                FROM {self.target_table} 
                WHERE sync_state = 'PENDING'
                GROUP BY record_uuid
                HAVING COUNT(*) > 1
            """
        }
        
        results = {}
        
        for query_name, query_sql in business_key_queries.items():
            try:
                result = db.execute(query_sql)
                
                if query_name == 'unique_record_uuids':
                    results[query_name] = {'unique_uuids': result[0][0], 'total_records': result[0][1]}
                elif query_name == 'duplicate_business_keys':
                    results[query_name] = len(result)  # Count of duplicates
                else:
                    results[query_name] = result[0][0] if result else 0
                
                logger.info(f"  ✅ {query_name}: {results[query_name]}")
                
            except Exception as e:
                results[query_name] = f"ERROR: {str(e)}"
                logger.error(f"  ❌ {query_name}: {str(e)}")
        
        return results
    
    def _debug_full_template(self) -> Dict[str, Any]:
        """Step 5: Debug the actual template SQL generation and execution"""
        
        try:
            # Get the actual generated SQL
            generated_sql = self.template_engine.render_unpivot_sizes_direct_sql()
            
            # Extract the source subquery from the MERGE for isolated testing
            source_subquery = self._extract_source_subquery(generated_sql)
            
            results = {
                'template_generation': 'SUCCESS',
                'sql_length': len(generated_sql),
                'source_subquery_test': None
            }
            
            # Test the source subquery in isolation
            if source_subquery:
                try:
                    source_result = db.execute(f"SELECT COUNT(*) FROM ({source_subquery}) AS test_source")
                    results['source_subquery_test'] = source_result[0][0] if source_result else 0
                    logger.info(f"  ✅ Source subquery produces: {results['source_subquery_test']} records")
                    
                except Exception as e:
                    results['source_subquery_test'] = f"ERROR: {str(e)}"
                    logger.error(f"  ❌ Source subquery failed: {str(e)}")
            
            return results
            
        except Exception as e:
            logger.error(f"  ❌ Template generation failed: {str(e)}")
            return {
                'template_generation': f"ERROR: {str(e)}",
                'sql_length': 0,
                'source_subquery_test': None
            }
    
    def _extract_source_subquery(self, full_sql: str) -> str:
        """Extract the source subquery from the MERGE statement for isolated testing"""
        
        try:
            # Look for the USING clause and extract the subquery
            using_start = full_sql.find("USING (")
            if using_start == -1:
                return None
            
            # Find the matching closing parenthesis
            paren_count = 0
            start_pos = using_start + 7  # Start after "USING ("
            
            for i, char in enumerate(full_sql[start_pos:], start_pos):
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    if paren_count == 0:
                        return full_sql[start_pos:i]
                    paren_count -= 1
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract source subquery: {str(e)}")
            return None
    
    def _generate_diagnosis_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive diagnosis summary with recommendations"""
        
        summary = {
            'critical_findings': [],
            'likely_root_cause': None,
            'recommended_fix': None,
            'success_metrics': {}
        }
        
        # Analyze Step 1: Source validation
        step1 = results.get('step1_source_validation', {})
        if isinstance(step1, dict):
            pending_count = step1.get('pending_records', 0)
            if pending_count == 0:
                summary['critical_findings'].append("❌ No records with sync_state = 'PENDING' found")
                summary['likely_root_cause'] = "Source data filter issue - no PENDING records"
            elif pending_count > 0:
                summary['critical_findings'].append(f"✅ Found {pending_count} PENDING records")
        
        # Analyze Step 2: XL column analysis
        step2 = results.get('step2_xl_column_analysis', {})
        if isinstance(step2, dict):
            xl_nonzero = step2.get('xl_nonzero_pending', 0)
            if xl_nonzero == 0:
                summary['critical_findings'].append("❌ No XL > 0 values in PENDING records")
            elif xl_nonzero > 0:
                summary['critical_findings'].append(f"✅ Found {xl_nonzero} XL > 0 values in PENDING records")
        
        # Analyze Step 3: UNPIVOT test
        step3 = results.get('step3_unpivot_manual_test', {})
        if isinstance(step3, dict):
            xl_unpivot = step3.get('xl_unpivot_count', 0)
            if isinstance(xl_unpivot, int) and xl_unpivot == 0:
                summary['critical_findings'].append("❌ UNPIVOT operation produces 0 records")
                summary['likely_root_cause'] = "UNPIVOT logic or filtering issue"
            elif isinstance(xl_unpivot, int) and xl_unpivot > 0:
                summary['critical_findings'].append(f"✅ UNPIVOT produces {xl_unpivot} records")
        
        # Determine likely root cause and recommendation
        if not summary['likely_root_cause']:
            if pending_count > 0 and xl_nonzero > 0:
                summary['likely_root_cause'] = "MERGE business key logic or template complexity"
                summary['recommended_fix'] = "Simplify MERGE logic, test business key matching"
            else:
                summary['likely_root_cause'] = "Data filtering or sync_state mismatch"
                summary['recommended_fix'] = "Fix sync_state filter logic in template"
        
        # Success metrics for tracking
        summary['success_metrics'] = {
            'source_records_available': pending_count if isinstance(pending_count, int) else 0,
            'xl_nonzero_available': xl_nonzero if isinstance(xl_nonzero, int) else 0,
            'unpivot_records_produced': xl_unpivot if isinstance(xl_unpivot, int) else 0
        }
        
        logger.info("📊 DIAGNOSIS SUMMARY:")
        for finding in summary['critical_findings']:
            logger.info(f"  {finding}")
        
        if summary['likely_root_cause']:
            logger.info(f"🎯 LIKELY ROOT CAUSE: {summary['likely_root_cause']}")
        
        if summary['recommended_fix']:
            logger.info(f"🔧 RECOMMENDED FIX: {summary['recommended_fix']}")
        
        return summary


def main():
    """Run the complete unpivot_sizes_direct diagnostic test"""
    
    try:
        diagnostic_test = UnpivotSizesDirectDiagnosticTest()
        results = diagnostic_test.run_complete_diagnosis()
        
        # Print summary for easy analysis
        summary = results['diagnosis_summary']
        print("\n" + "="*80)
        print("🎯 FINAL DIAGNOSIS SUMMARY")
        print("="*80)
        
        for finding in summary['critical_findings']:
            print(f"  {finding}")
        
        if summary['likely_root_cause']:
            print(f"\n🚨 ROOT CAUSE: {summary['likely_root_cause']}")
        
        if summary['recommended_fix']:
            print(f"🔧 RECOMMENDED FIX: {summary['recommended_fix']}")
        
        metrics = summary['success_metrics']
        print(f"\n📊 SUCCESS METRICS:")
        print(f"  Source records: {metrics['source_records_available']}")
        print(f"  XL > 0 records: {metrics['xl_nonzero_available']}")
        print(f"  UNPIVOT output: {metrics['unpivot_records_produced']}")
        
        return True
        
    except Exception as e:
        logger.exception(f"❌ Diagnostic test failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
