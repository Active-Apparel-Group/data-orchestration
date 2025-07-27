"""
Integration Test: NEW Order Detection Logic
Purpose: Test Python-based NEW order detection with AAG ORDER NUMBER comparison
Requirement: Detect NEW vs EXISTING orders using swp_ORDER_LIST_V2 vs ORDER_LIST_V2

SUCCESS CRITERIA:
- NEW order detection accuracy > 95%
- GREYSON PO 4755 validation included
- sync_state updated correctly in swp_ORDER_LIST_V2
- Comprehensive logging with statistics
- Real database integration (no mocks)
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
from src.pipelines.sync_order_list.merge_orchestrator import MergeOrchestrator

logger = logger.get_logger(__name__)

class NewOrderDetectionTest:
    """Integration test for NEW order detection logic with real database"""
    
    def __init__(self, config_path: str = None):
        # Use repo_root pattern like other tests
        if config_path is None:
            config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
        self.config_path = config_path
        self.success_threshold = 0.95  # 95% accuracy required
        
    def test_new_order_detection(self) -> Dict[str, Any]:
        """Test NEW order detection with real database comparison"""
        try:
            # Load real configuration
            config = DeltaSyncConfig.from_toml(self.config_path)
            logger.info(f"Configuration loaded: {config.source_table} -> {config.target_table}")
            
            # Initialize merge orchestrator
            orchestrator = MergeOrchestrator(config)
            
            # Pre-test: Check initial state of tables
            initial_state = self.get_table_states(config)
            logger.info(f"Initial state - Source: {initial_state['source_count']} records, Target: {initial_state['target_count']} records")
            
            # Execute NEW order detection
            detection_results = orchestrator.detect_new_orders()
            
            # Post-test: Validate sync_state updates
            final_state = self.validate_sync_state_updates(config, detection_results)
            
            # Validation checks
            validation_results = {
                'detection_success': detection_results.get('success', False),
                'accuracy_threshold': detection_results.get('accuracy_percentage', 0) >= (self.success_threshold * 100),
                'sync_state_updated': final_state.get('sync_state_updated_count', 0) > 0,
                'greyson_4755_tracked': 'greyson_4755_new_count' in detection_results,
                'comprehensive_logging': all(key in detection_results for key in [
                    'total_source_records', 'new_orders', 'existing_orders', 'duration_seconds'
                ]),
                'error_handling': 'error' not in detection_results
            }
            
            logger.info("NEW order detection validation:")
            for check, result in validation_results.items():
                status = "✅ PASS" if result else "❌ FAIL"
                logger.info(f"  {check}: {status}")
            
            return {
                'detection_results': detection_results,
                'initial_state': initial_state,
                'final_state': final_state,
                'validation_results': validation_results,
                'success_rate': sum(validation_results.values()) / len(validation_results)
            }
            
        except Exception as e:
            logger.error(f"NEW order detection test failed: {e}")
            return {
                'error': str(e),
                'success_rate': 0.0
            }
    
    def get_table_states(self, config: DeltaSyncConfig) -> Dict[str, Any]:
        """Get current state of source and target tables"""
        try:
            with db.get_connection(config.database_connection) as conn:
                cursor = conn.cursor()
                
                # Count records in source table
                cursor.execute(f"SELECT COUNT(*) FROM {config.source_table}")
                source_count = cursor.fetchone()[0]
                
                # Count records in target table
                cursor.execute(f"SELECT COUNT(*) FROM {config.target_table}")
                target_count = cursor.fetchone()[0]
                
                # Count existing AAG ORDER NUMBERs in target
                cursor.execute(f"""
                SELECT COUNT(DISTINCT [AAG ORDER NUMBER]) 
                FROM {config.target_table} 
                WHERE [AAG ORDER NUMBER] IS NOT NULL
                """)
                existing_aag_count = cursor.fetchone()[0]
                
                # Count source records with AAG ORDER NUMBERs
                cursor.execute(f"""
                SELECT COUNT(*) 
                FROM {config.source_table} 
                WHERE [AAG ORDER NUMBER] IS NOT NULL
                """)
                source_with_aag_count = cursor.fetchone()[0]
                
                return {
                    'source_count': source_count,
                    'target_count': target_count,
                    'existing_aag_count': existing_aag_count,
                    'source_with_aag_count': source_with_aag_count
                }
                
        except Exception as e:
            logger.error(f"Failed to get table states: {e}")
            return {
                'source_count': 0,
                'target_count': 0,
                'existing_aag_count': 0,
                'source_with_aag_count': 0,
                'error': str(e)
            }
    
    def validate_sync_state_updates(self, config: DeltaSyncConfig, detection_results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that sync_state column was updated correctly"""
        try:
            with db.get_connection(config.database_connection) as conn:
                cursor = conn.cursor()
                
                # Count records by sync_state
                cursor.execute(f"""
                SELECT sync_state, COUNT(*) 
                FROM {config.source_table} 
                WHERE [AAG ORDER NUMBER] IS NOT NULL
                GROUP BY sync_state
                """)
                
                sync_state_counts = {}
                total_updated = 0
                for row in cursor.fetchall():
                    sync_state, count = row
                    sync_state_counts[sync_state or 'NULL'] = count
                    if sync_state in ['NEW', 'EXISTING']:
                        total_updated += count
                
                # Validate against detection results
                expected_new = detection_results.get('new_orders', 0)
                expected_existing = detection_results.get('existing_orders', 0)
                
                actual_new = sync_state_counts.get('NEW', 0)
                actual_existing = sync_state_counts.get('EXISTING', 0)
                
                # Check for GREYSON PO 4755 records with NEW state
                cursor.execute(f"""
                SELECT COUNT(*) 
                FROM {config.source_table} 
                WHERE sync_state = 'NEW' 
                AND [CUSTOMER NAME] LIKE '%GREYSON%' 
                AND [PO NUMBER] LIKE '%4755%'
                """)
                greyson_4755_new_actual = cursor.fetchone()[0]
                
                logger.info("sync_state validation:")
                logger.info(f"  Expected NEW: {expected_new}, Actual: {actual_new}")
                logger.info(f"  Expected EXISTING: {expected_existing}, Actual: {actual_existing}")
                logger.info(f"  GREYSON PO 4755 NEW: {greyson_4755_new_actual}")
                logger.info(f"  All sync_state counts: {sync_state_counts}")
                
                return {
                    'sync_state_counts': sync_state_counts,
                    'sync_state_updated_count': total_updated,
                    'new_match': actual_new == expected_new,
                    'existing_match': actual_existing == expected_existing,
                    'greyson_4755_new_count': greyson_4755_new_actual,
                    'validation_success': (actual_new == expected_new) and (actual_existing == expected_existing)
                }
                
        except Exception as e:
            logger.error(f"Failed to validate sync_state updates: {e}")
            return {
                'sync_state_updated_count': 0,
                'validation_success': False,
                'error': str(e)
            }
    
    def test_greyson_4755_specific_validation(self, config: DeltaSyncConfig) -> Dict[str, Any]:
        """Test GREYSON PO 4755 specific validation and tracking"""
        try:
            with db.get_connection(config.database_connection) as conn:
                cursor = conn.cursor()
                
                # Query GREYSON PO 4755 records specifically
                cursor.execute(f"""
                SELECT 
                    record_uuid,
                    [AAG ORDER NUMBER],
                    [CUSTOMER NAME],
                    [PO NUMBER],
                    sync_state,
                    created_at,
                    updated_at
                FROM {config.source_table}
                WHERE [CUSTOMER NAME] LIKE '%GREYSON%' 
                AND [PO NUMBER] LIKE '%4755%'
                """)
                
                greyson_records = cursor.fetchall()
                
                greyson_analysis = {
                    'total_greyson_4755': len(greyson_records),
                    'new_greyson_4755': 0,
                    'existing_greyson_4755': 0,
                    'null_state_greyson_4755': 0,
                    'records_details': []
                }
                
                for record in greyson_records:
                    uuid, aag_order, customer, po, sync_state, created, updated = record
                    
                    record_detail = {
                        'record_uuid': uuid,
                        'aag_order_number': aag_order,
                        'customer_name': customer,
                        'po_number': po,
                        'sync_state': sync_state,
                        'created_at': str(created) if created else None,
                        'updated_at': str(updated) if updated else None
                    }
                    
                    greyson_analysis['records_details'].append(record_detail)
                    
                    if sync_state == 'NEW':
                        greyson_analysis['new_greyson_4755'] += 1
                    elif sync_state == 'EXISTING':
                        greyson_analysis['existing_greyson_4755'] += 1
                    else:
                        greyson_analysis['null_state_greyson_4755'] += 1
                
                logger.info(f"GREYSON PO 4755 Analysis:")
                logger.info(f"  Total records: {greyson_analysis['total_greyson_4755']}")
                logger.info(f"  NEW: {greyson_analysis['new_greyson_4755']}")
                logger.info(f"  EXISTING: {greyson_analysis['existing_greyson_4755']}")
                logger.info(f"  NULL/Other: {greyson_analysis['null_state_greyson_4755']}")
                
                return greyson_analysis
                
        except Exception as e:
            logger.error(f"GREYSON PO 4755 validation failed: {e}")
            return {
                'total_greyson_4755': 0,
                'error': str(e)
            }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run complete NEW order detection integration test"""
        logger.info("=" * 70)
        logger.info("🔍 NEW Order Detection Integration Test")
        logger.info("=" * 70)
        
        # Phase 1: NEW order detection
        logger.info("📋 Phase 1: NEW Order Detection with Real Database")
        detection_results = self.test_new_order_detection()
        
        if 'error' in detection_results:
            logger.error("NEW order detection failed - cannot continue")
            return {
                'success_gate_met': False,
                'error': detection_results['error']
            }
        
        # Phase 2: GREYSON PO 4755 specific validation
        logger.info("🎯 Phase 2: GREYSON PO 4755 Specific Validation")
        config = DeltaSyncConfig.from_toml(self.config_path)
        greyson_analysis = self.test_greyson_4755_specific_validation(config)
        
        # Calculate overall success
        validation_results = detection_results['validation_results']
        overall_success_rate = detection_results['success_rate']
        
        # Additional success criteria
        accuracy_met = detection_results['detection_results'].get('accuracy_percentage', 0) >= 95.0
        greyson_tracked = greyson_analysis.get('total_greyson_4755', 0) > 0
        
        success_gate_met = (
            overall_success_rate >= 1.0 and  # All validation checks pass
            accuracy_met and  # Accuracy >= 95%
            detection_results['detection_results'].get('success', False)  # Core detection success
        )
        
        logger.info("=" * 70)
        logger.info("📊 INTEGRATION TEST RESULTS:")
        logger.info(f"   Detection Success: {'✅ PASS' if detection_results['detection_results'].get('success', False) else '❌ FAIL'}")
        logger.info(f"   Accuracy >= 95%: {'✅ PASS' if accuracy_met else '❌ FAIL'} ({detection_results['detection_results'].get('accuracy_percentage', 0):.1f}%)")
        logger.info(f"   Validation Rate: {'✅ PASS' if overall_success_rate >= 1.0 else '❌ FAIL'} ({overall_success_rate:.1%})")
        logger.info(f"   GREYSON PO 4755 Tracked: {'✅ PASS' if greyson_tracked else '❌ FAIL'} ({greyson_analysis.get('total_greyson_4755', 0)} records)")
        
        if success_gate_met:
            logger.info("✅ SUCCESS GATE MET: NEW order detection integration passed!")
            logger.info(f"🚀 Detected {detection_results['detection_results'].get('new_orders', 0)} NEW orders with {detection_results['detection_results'].get('accuracy_percentage', 0):.1f}% accuracy")
        else:
            logger.error("❌ SUCCESS GATE FAILED: NEW order detection integration failed!")
        
        logger.info("=" * 70)
        
        return {
            'success_gate_met': success_gate_met,
            'overall_success_rate': overall_success_rate,
            'accuracy_percentage': detection_results['detection_results'].get('accuracy_percentage', 0),
            'detection_results': detection_results,
            'greyson_analysis': greyson_analysis,
            'new_orders_detected': detection_results['detection_results'].get('new_orders', 0),
            'existing_orders_found': detection_results['detection_results'].get('existing_orders', 0)
        }

def main():
    """Run NEW order detection integration test"""
    try:
        tester = NewOrderDetectionTest()
        results = tester.run_comprehensive_test()
        
        # Exit with proper code
        return 0 if results['success_gate_met'] else 1
        
    except Exception as e:
        logger.error(f"NEW order detection test failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
