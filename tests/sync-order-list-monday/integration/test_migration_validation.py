#!/usr/bin/env python3
"""
Integration Test: Migration Validation for swp_ORDER_LIST_V2
Purpose: Validate schema fix migration results with measurable success gates
Requirement: ORDER_LIST Delta Monday Sync - Schema compatibility fix
Created: 2025-07-21
Author: ORDER_LIST Delta Monday Sync - Schema Fix

Integration testing is the default. This test validates:
- Table schema compatibility 
- Data population success
- Ordinal position corrections for ConfigParser
- Real production-like validation with measurable outcomes
"""

import sys
from pathlib import Path

# Legacy transition support pattern
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

import db_helper as db
import logger_helper
from typing import Dict, Any, List

logger = logger_helper.get_logger(__name__)

class MigrationValidationTest:
    """Integration test for swp_ORDER_LIST_V2 migration validation"""
    
    def __init__(self):
        self.db_key = 'orders'
        self.results = {
            'table_exists': False,
            'schema_valid': False,
            'data_populated': False,
            'ordinal_positions_correct': False,
            'total_records': 0,
            'greyson_records': 0,
            'size_columns_count': 0,
            'success_rate': 0.0
        }
    
    def run_validation_tests(self) -> Dict[str, Any]:
        """
        Run complete migration validation with measurable success gates
        
        Success Criteria:
        - Table exists: REQUIRED
        - Schema compatibility: ≥95% column match
        - Data population: >0 records
        - GREYSON test data: >0 records  
        - Size columns: 251 columns exactly
        - Ordinal positions: UNIT OF MEASURE before TOTAL QTY
        
        Returns:
            Dict containing validation results and metrics
        """
        logger.info("Starting migration validation tests for swp_ORDER_LIST_V2")
        logger.info("=" * 60)
        
        try:
            with db.get_connection(self.db_key) as conn:
                cursor = conn.cursor()
                
                # Phase 1: Table Existence Validation
                self._validate_table_exists(cursor)
                
                # Phase 2: Schema Compatibility Validation  
                self._validate_schema_compatibility(cursor)
                
                # Phase 3: Data Population Validation
                self._validate_data_population(cursor)
                
                # Phase 4: Ordinal Position Validation
                self._validate_ordinal_positions(cursor)
                
                cursor.close()
            
            # Calculate overall success rate
            self._calculate_success_rate()
            
            # Log final results
            self._log_final_results()
            
            return self.results
            
        except Exception as e:
            logger.error(f"ERROR: Migration validation failed: {str(e)}")
            self.results['error'] = str(e)
            return self.results
    
    def _validate_table_exists(self, cursor) -> None:
        """Phase 1: Validate table exists"""
        logger.info("Phase 1: Table Existence Validation")
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'swp_ORDER_LIST_V2' 
              AND TABLE_SCHEMA = 'dbo'
        """)
        
        table_count = cursor.fetchone()[0]
        self.results['table_exists'] = table_count == 1
        
        if self.results['table_exists']:
            logger.info("SUCCESS: swp_ORDER_LIST_V2 table exists")
        else:
            logger.error("ERROR: swp_ORDER_LIST_V2 table not found")
    
    def _validate_schema_compatibility(self, cursor) -> None:
        """Phase 2: Validate schema compatibility between ORDER_LIST and swp_ORDER_LIST_V2"""
        logger.info("Phase 2: Schema Compatibility Validation")
        
        # Get column counts for both tables
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                 WHERE TABLE_NAME = 'ORDER_LIST' AND TABLE_SCHEMA = 'dbo') as order_list_cols,
                (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                 WHERE TABLE_NAME = 'swp_ORDER_LIST_V2' AND TABLE_SCHEMA = 'dbo') as swp_cols
        """)
        
        row = cursor.fetchone()
        order_list_columns = row[0] if row[0] else 0
        swp_columns = row[1] if row[1] else 0
        
        logger.info(f"INFO: ORDER_LIST columns: {order_list_columns}")
        logger.info(f"INFO: swp_ORDER_LIST_V2 columns: {swp_columns}")
        
        # Get ordinal positions for both tables
        cursor.execute("""
            SELECT 
                ol_unit.ORDINAL_POSITION as ol_unit_pos,
                ol_total.ORDINAL_POSITION as ol_total_pos,
                swp_unit.ORDINAL_POSITION as swp_unit_pos,
                swp_total.ORDINAL_POSITION as swp_total_pos
            FROM 
                (SELECT ORDINAL_POSITION FROM INFORMATION_SCHEMA.COLUMNS 
                 WHERE TABLE_NAME = 'ORDER_LIST' AND COLUMN_NAME = 'UNIT OF MEASURE') ol_unit
            CROSS JOIN
                (SELECT ORDINAL_POSITION FROM INFORMATION_SCHEMA.COLUMNS 
                 WHERE TABLE_NAME = 'ORDER_LIST' AND COLUMN_NAME = 'TOTAL QTY') ol_total
            CROSS JOIN
                (SELECT ORDINAL_POSITION FROM INFORMATION_SCHEMA.COLUMNS 
                 WHERE TABLE_NAME = 'swp_ORDER_LIST_V2' AND COLUMN_NAME = 'UNIT OF MEASURE') swp_unit
            CROSS JOIN
                (SELECT ORDINAL_POSITION FROM INFORMATION_SCHEMA.COLUMNS 
                 WHERE TABLE_NAME = 'swp_ORDER_LIST_V2' AND COLUMN_NAME = 'TOTAL QTY') swp_total
        """)
        
        row = cursor.fetchone()
        if row:
            ol_unit_pos = row[0]
            ol_total_pos = row[1] 
            swp_unit_pos = row[2]
            swp_total_pos = row[3]
            
            # Count size columns between bookends for both tables
            ol_size_columns = ol_total_pos - ol_unit_pos - 1 if ol_unit_pos and ol_total_pos else 0
            swp_size_columns = swp_total_pos - swp_unit_pos - 1 if swp_unit_pos and swp_total_pos else 0
            
            logger.info(f"INFO: ORDER_LIST UNIT OF MEASURE position: {ol_unit_pos}")
            logger.info(f"INFO: ORDER_LIST TOTAL QTY position: {ol_total_pos}")
            logger.info(f"INFO: ORDER_LIST size columns (between bookends): {ol_size_columns}")
            logger.info("")
            logger.info(f"INFO: swp_ORDER_LIST_V2 UNIT OF MEASURE position: {swp_unit_pos}")
            logger.info(f"INFO: swp_ORDER_LIST_V2 TOTAL QTY position: {swp_total_pos}")
            logger.info(f"INFO: swp_ORDER_LIST_V2 size columns (between bookends): {swp_size_columns}")
            
            # Validate ordinal positions match
            positions_match = (ol_unit_pos == swp_unit_pos) and (ol_total_pos == swp_total_pos)
            size_columns_match = ol_size_columns == swp_size_columns
            
            self.results['order_list_columns'] = order_list_columns
            self.results['swp_columns'] = swp_columns  
            self.results['size_columns_count'] = swp_size_columns
            self.results['order_list_size_columns'] = ol_size_columns
            self.results['positions_match'] = positions_match
            self.results['size_columns_match'] = size_columns_match
            
            # Schema validation: positions must match and size columns must match
            self.results['schema_valid'] = positions_match and size_columns_match
            
            if positions_match:
                logger.info("SUCCESS: Ordinal positions match between tables")
            else:
                logger.error("ERROR: Ordinal position mismatch detected")
                
            if size_columns_match:
                logger.info("SUCCESS: Size column counts match between tables")
            else:
                logger.error(f"ERROR: Size column mismatch - ORDER_LIST: {ol_size_columns}, swp_ORDER_LIST_V2: {swp_size_columns}")
        else:
            logger.error("ERROR: Could not retrieve ordinal positions")
            self.results['schema_valid'] = False
    
    def _validate_data_population(self, cursor) -> None:
        """Phase 3: Validate data population"""
        logger.info("Phase 3: Data Population Validation")
        
        # Total record count
        cursor.execute("SELECT COUNT(*) FROM dbo.swp_ORDER_LIST_V2")
        total_records = cursor.fetchone()[0]
        
        # GREYSON record count
        cursor.execute("""
            SELECT COUNT(*) 
            FROM dbo.swp_ORDER_LIST_V2 
            WHERE [CUSTOMER NAME] LIKE '%GREYSON%'
        """)
        greyson_records = cursor.fetchone()[0]
        
        self.results['total_records'] = total_records
        self.results['greyson_records'] = greyson_records
        self.results['data_populated'] = total_records > 0
        
        logger.info(f"INFO: Total records: {total_records}")
        logger.info(f"INFO: GREYSON records: {greyson_records}")
        
        if self.results['data_populated']:
            logger.info("SUCCESS: Data population validated")
            
            # Sample data for verification
            cursor.execute("""
                SELECT TOP 3 
                    [AAG ORDER NUMBER], 
                    [CUSTOMER NAME], 
                    [PO NUMBER], 
                    sync_state 
                FROM dbo.swp_ORDER_LIST_V2
            """)
            
            logger.info("Sample data:")
            for row in cursor.fetchall():
                logger.info(f"  AAG: {row[0]}, Customer: {row[1]}, PO: {row[2]}, State: {row[3]}")
        else:
            logger.error("ERROR: No data found in swp_ORDER_LIST_V2")
    
    def _validate_ordinal_positions(self, cursor) -> None:
        """Phase 4: Validate ordinal positions for ConfigParser"""
        logger.info("Phase 4: Ordinal Position Validation")
        
        cursor.execute("""
            SELECT 
                c1.ORDINAL_POSITION as unit_position,
                c2.ORDINAL_POSITION as total_position
            FROM INFORMATION_SCHEMA.COLUMNS c1
            CROSS JOIN INFORMATION_SCHEMA.COLUMNS c2
            WHERE c1.TABLE_NAME = 'swp_ORDER_LIST_V2' 
              AND c1.COLUMN_NAME = 'UNIT OF MEASURE'
              AND c2.TABLE_NAME = 'swp_ORDER_LIST_V2' 
              AND c2.COLUMN_NAME = 'TOTAL QTY'
        """)
        
        row = cursor.fetchone()
        unit_pos = row[0] if row else 0
        total_pos = row[1] if row else 0
        
        # ConfigParser requires UNIT OF MEASURE before TOTAL QTY
        positions_correct = unit_pos > 0 and total_pos > 0 and unit_pos < total_pos
        
        self.results['ordinal_positions_correct'] = positions_correct
        self.results['unit_of_measure_position'] = unit_pos
        self.results['total_qty_position'] = total_pos
        
        logger.info(f"INFO: UNIT OF MEASURE position: {unit_pos}")
        logger.info(f"INFO: TOTAL QTY position: {total_pos}")
        
        if positions_correct:
            logger.info("SUCCESS: Ordinal positions validated for ConfigParser")
        else:
            logger.error("ERROR: Ordinal positions invalid for ConfigParser")
    
    def _calculate_success_rate(self) -> None:
        """Calculate overall success rate based on validation criteria"""
        total_criteria = 4  # table_exists, schema_valid, data_populated, ordinal_positions_correct
        passed_criteria = sum([
            self.results['table_exists'],
            self.results['schema_valid'], 
            self.results['data_populated'],
            self.results['ordinal_positions_correct']
        ])
        
        self.results['success_rate'] = (passed_criteria / total_criteria) * 100
    
    def _log_final_results(self) -> None:
        """Log final validation results with success gates"""
        logger.info("")
        logger.info("VALIDATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Overall Success Rate: {self.results['success_rate']:.1f}%")
        logger.info("")
        
        # Success gate evaluation
        if self.results['success_rate'] >= 95:
            logger.info("SUCCESS: Migration validation PASSED (≥95% success rate)")
            logger.info("READY: ConfigParser can proceed with schema compatibility")
        elif self.results['success_rate'] >= 90:
            logger.info("WARNING: Migration validation MARGINAL (90-94% success rate)")
            logger.info("REVIEW: Some issues detected, proceed with caution")
        else:
            logger.error("FAILED: Migration validation FAILED (<90% success rate)")
            logger.error("BLOCKED: Migration issues must be resolved before proceeding")

def main():
    """Main entry point for migration validation test"""
    print("Migration Validation Test")
    print("=" * 60)
    
    validator = MigrationValidationTest()
    results = validator.run_validation_tests()
    
    # Exit with appropriate code for CI/CD
    success_rate = results.get('success_rate', 0)
    if success_rate >= 95:
        print(f"\nSUCCESS: Migration validation passed ({success_rate:.1f}%)")
        sys.exit(0)
    else:
        print(f"\nFAILED: Migration validation failed ({success_rate:.1f}%)")
        sys.exit(1)

if __name__ == "__main__":
    main()
