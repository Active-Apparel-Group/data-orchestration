"""
Integration Test: Architecture Fix Validation (001_05)
Purpose: Validate that sync_state column architecture fix is working properly
Requirement: Remove DEFAULT 'NEW' to enable Python-driven NEW detection logic

SUCCESS CRITERIA:
- sync_state column allows NULL values (IS_NULLABLE = 'YES')
- No DEFAULT constraint exists on sync_state column
- All existing records have sync_state = NULL for Python re-evaluation
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

logger = logger.get_logger(__name__)

class ArchitectureFixValidator:
    """Integration test for 001_05 sync_state architecture fix"""
    
    def __init__(self, db_key: str = "orders"):
        self.db_key = db_key
        self.success_threshold = 1.0  # 100% success required
        self.validation_results = []
    
    def test_column_nullable(self) -> bool:
        """Test that sync_state column now allows NULL values"""
        try:
            with db.get_connection(self.db_key) as conn:
                cursor = conn.cursor()
                
                query = """
                SELECT 
                    COLUMN_NAME,
                    IS_NULLABLE,
                    DATA_TYPE,
                    COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'swp_ORDER_LIST_V2' 
                  AND TABLE_SCHEMA = 'dbo'
                  AND COLUMN_NAME = 'sync_state'
                """
                
                cursor.execute(query)
                result = cursor.fetchone()
                cursor.close()
                
                if not result:
                    logger.error("sync_state column not found in swp_ORDER_LIST_V2")
                    return False
                
                column_name, is_nullable, data_type, column_default = result
                
                # Validate column properties
                is_valid = (
                    is_nullable == 'YES' and
                    data_type == 'varchar' and
                    column_default is None
                )
                
                logger.info(f"Column Properties: IS_NULLABLE={is_nullable}, DATA_TYPE={data_type}, DEFAULT={column_default}")
                
                if is_valid:
                    logger.info("✅ sync_state column correctly allows NULL values with no default")
                    return True
                else:
                    logger.error("❌ sync_state column configuration is incorrect")
                    return False
                    
        except Exception as e:
            logger.error(f"Error testing column nullable: {e}")
            return False
    
    def test_no_default_constraint(self) -> bool:
        """Test that no DEFAULT constraint exists on sync_state column"""
        try:
            with db.get_connection(self.db_key) as conn:
                cursor = conn.cursor()
                
                query = """
                SELECT dc.name as constraint_name
                FROM sys.default_constraints dc
                JOIN sys.columns c ON dc.parent_column_id = c.column_id
                JOIN sys.objects o ON dc.parent_object_id = o.object_id
                WHERE o.name = 'swp_ORDER_LIST_V2' 
                  AND c.name = 'sync_state'
                """
                
                cursor.execute(query)
                result = cursor.fetchone()
                cursor.close()
                
                if result:
                    constraint_name = result[0]
                    logger.error(f"❌ DEFAULT constraint still exists: {constraint_name}")
                    return False
                else:
                    logger.info("✅ No DEFAULT constraint found on sync_state column")
                    return True
                    
        except Exception as e:
            logger.error(f"Error checking default constraint: {e}")
            return False
    
    def test_records_reset_to_null(self) -> bool:
        """Test that all existing records have sync_state = NULL for Python re-evaluation"""
        try:
            with db.get_connection(self.db_key) as conn:
                cursor = conn.cursor()
                
                # Check sync_state distribution
                query = """
                SELECT 
                    sync_state,
                    COUNT(*) as record_count
                FROM dbo.swp_ORDER_LIST_V2
                GROUP BY sync_state
                ORDER BY sync_state
                """
                
                cursor.execute(query)
                results = cursor.fetchall()
                cursor.close()
                
                total_records = sum(row[1] for row in results)
                null_records = 0
                
                logger.info(f"sync_state distribution in swp_ORDER_LIST_V2:")
                for sync_state, count in results:
                    state_display = 'NULL' if sync_state is None else sync_state
                    logger.info(f"  {state_display}: {count} records")
                    
                    if sync_state is None:
                        null_records = count
                
                # All records should be NULL for Python re-evaluation
                if null_records == total_records and total_records > 0:
                    logger.info(f"✅ All {total_records} records have sync_state = NULL for Python re-evaluation")
                    return True
                elif total_records == 0:
                    logger.info("✅ No records in table (acceptable state)")
                    return True
                else:
                    logger.error(f"❌ Not all records have NULL sync_state: {null_records}/{total_records} are NULL")
                    return False
                    
        except Exception as e:
            logger.error(f"Error checking record states: {e}")
            return False
    
    def run_comprehensive_validation(self) -> dict:
        """Run complete architecture fix validation"""
        logger.info("=" * 70)
        logger.info("🔧 Architecture Fix Validation - Migration 001_05")
        logger.info("=" * 70)
        
        # Run all validation tests
        test_results = {
            'column_nullable': self.test_column_nullable(),
            'no_default_constraint': self.test_no_default_constraint(), 
            'records_reset_null': self.test_records_reset_to_null()
        }
        
        # Calculate success metrics
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        success_rate = passed_tests / total_tests
        
        logger.info("=" * 70)
        logger.info("📊 VALIDATION RESULTS:")
        logger.info(f"   Tests Passed: {passed_tests}/{total_tests}")
        logger.info(f"   Success Rate: {success_rate:.1%}")
        
        # Determine overall success
        success_gate_met = success_rate >= self.success_threshold
        
        if success_gate_met:
            logger.info("✅ SUCCESS GATE MET: Architecture fix validation passed!")
            logger.info("🚀 Ready for Python merge_orchestrator.py NEW detection logic")
        else:
            logger.error("❌ SUCCESS GATE FAILED: Architecture fix validation failed!")
        
        logger.info("=" * 70)
        
        return {
            'success_gate_met': success_gate_met,
            'success_rate': success_rate,
            'test_results': test_results,
            'passed_tests': passed_tests,
            'total_tests': total_tests
        }

def main():
    """Run architecture fix validation test"""
    try:
        validator = ArchitectureFixValidator(db_key="orders")
        results = validator.run_comprehensive_validation()
        
        # Exit with proper code
        return 0 if results['success_gate_met'] else 1
        
    except Exception as e:
        logger.error(f"Architecture fix validation failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
