#!/usr/bin/env python3
"""
ORDER_LIST Delta Sync - TOML Foundation Validation Test

This test validates the TOML configuration foundation before any pipeline development.
Tests column existence, size discovery, hash generation, and Monday.com integration.

Following test.instructions.md patterns:
- Modular test phases with specific validation criteria
- Database validation using actual production data
- Measurable success criteria (95%+ thresholds)
- Clear ASCII output for Kestra compatibility

Run: python tests/debug/test_toml_foundation.py
"""

import sys
from pathlib import Path
import logging
import tomllib
import pandas as pd
from typing import Dict, Any, List

# Add project paths for imports
def find_repo_root():
    current = Path(__file__).resolve()
    while current != current.parent:
        if (current / "pyproject.toml").exists() or (current / "requirements.txt").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "src"))

# Import project utilities
from pipelines.utils import db, logger

class TOMLFoundationTestFramework:
    """TOML configuration validation framework for ORDER_LIST delta sync"""
    
    def __init__(self):
        self.test_results = {}
        self.config_path = repo_root / "configs" / "pipelines" / "order_list_delta_sync.toml"
        self.config = None
        
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(message)s',  # Simple format for clean output
            handlers=[logging.StreamHandler()]
        )
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("ORDER_LIST Delta Sync - TOML Foundation Test")
        self.logger.info("=" * 55)
    
    def test_toml_configuration_loading(self) -> Dict[str, Any]:
        """Test Phase 1: TOML configuration loading and parsing"""
        self.logger.info("\n1. TOML CONFIGURATION LOADING")
        self.logger.info("-" * 35)
        
        try:
            # Load TOML configuration
            if not self.config_path.exists():
                return {
                    'success': False, 
                    'error': f'TOML file not found: {self.config_path}'
                }
            
            with open(self.config_path, 'rb') as f:
                self.config = tomllib.load(f)
            
            # Validate required sections exist
            required_sections = [
                'phase', 'environment', 'test_data.phase1', 
                'columns.phase1', 'hash.phase1', 'monday.phase1'
            ]
            
            missing_sections = []
            for section in required_sections:
                if not self._get_nested_config(section):
                    missing_sections.append(section)
            
            if missing_sections:
                return {
                    'success': False,
                    'error': f'Missing TOML sections: {missing_sections}'
                }
            
            # Get current phase
            current_phase = self.config.get('phase', {}).get('current', 'unknown')
            sections_loaded = len(self.config)
            
            self.logger.info(f"TOML file loaded: {self.config_path.name}")
            self.logger.info(f"Current phase: {current_phase}")
            self.logger.info(f"Configuration sections: {sections_loaded}")
            self.logger.info("Required sections: ALL PRESENT")
            
            return {
                'success': True,
                'current_phase': current_phase,
                'sections_loaded': sections_loaded,
                'config_file': str(self.config_path)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'TOML loading failed: {str(e)}'
            }
    
    def test_source_column_validation(self) -> Dict[str, Any]:
        """Test Phase 2: Validate phase1 columns exist in source table"""
        self.logger.info("\n2. SOURCE COLUMN VALIDATION")
        self.logger.info("-" * 30)
        
        try:
            if not self.config:
                return {'success': False, 'error': 'TOML configuration not loaded'}
            
            # Get phase1 columns from TOML
            phase1_columns = self._get_nested_config('columns.phase1.order_list')
            if not phase1_columns:
                return {'success': False, 'error': 'Phase1 columns not found in TOML'}
            
            # Test GREYSON PO 4755 data availability
            test_customer = self._get_nested_config('test_data.phase1.limit_customers[0]')
            test_po = self._get_nested_config('test_data.phase1.limit_pos[0]')
            source_table = self._get_nested_config('environment.source_table')
            
            if not source_table:
                return {'success': False, 'error': 'Source table not defined in TOML'}
            
            # Query source table for column existence
            with db.get_connection('orders') as conn:
                # Build column list for SQL query
                column_list = ", ".join([f"[{col}]" for col in phase1_columns])
                
                sql = f"""
                SELECT TOP 5 {column_list}
                FROM dbo.{source_table} 
                WHERE [CUSTOMER NAME] = ? AND [PO NUMBER] = ?
                """
                
                df = pd.read_sql(sql, conn, params=[test_customer, test_po])
                
                if df.empty:
                    return {
                        'success': False,
                        'error': f'No data found for {test_customer} PO {test_po}'
                    }
                
                # Validate all columns have data
                missing_data = []
                for col in phase1_columns:
                    if df[col].isnull().all():
                        missing_data.append(col)
                
                success_rate = ((len(phase1_columns) - len(missing_data)) / len(phase1_columns)) * 100
                
                self.logger.info(f"Source table: dbo.{source_table}")
                self.logger.info(f"Test customer: {test_customer}")
                self.logger.info(f"Test PO: {test_po}")
                self.logger.info(f"Columns tested: {len(phase1_columns)}")
                self.logger.info(f"Records found: {len(df)}")
                self.logger.info(f"Column success rate: {success_rate:.1f}%")
                
                if missing_data:
                    self.logger.info(f"Missing data columns: {missing_data}")
                
                return {
                    'success': success_rate >= 95,
                    'success_rate': success_rate,
                    'columns_tested': phase1_columns,
                    'records_found': len(df),
                    'missing_data_columns': missing_data
                }
                
        except Exception as e:
            self.logger.error(f"Column validation failed: {str(e)}")
            return {
                'success': False,
                'error': f'Column validation failed: {str(e)}'
            }
    
    def test_size_column_discovery(self) -> Dict[str, Any]:
        """Test Phase 3: Size column discovery between marker columns"""
        self.logger.info("\n3. SIZE COLUMN DISCOVERY")
        self.logger.info("-" * 25)
        
        try:
            if not self.config:
                return {'success': False, 'error': 'TOML configuration not loaded'}
            
            # Get size detection configuration
            start_after = self._get_nested_config('size_detection.phase1.start_after')
            end_before = self._get_nested_config('size_detection.phase1.end_before')
            max_sizes = self._get_nested_config('size_detection.phase1.max_sizes')
            source_table = self._get_nested_config('environment.source_table')
            
            if not source_table:
                return {'success': False, 'error': 'Source table not defined in TOML'}
            
            # Get table schema to find size columns
            with db.get_connection('orders') as conn:
                schema_sql = f"""
                SELECT COLUMN_NAME, ORDINAL_POSITION
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = '{source_table}'
                ORDER BY ORDINAL_POSITION
                """
                
                schema_df = pd.read_sql(schema_sql, conn)
                
                # Find marker positions
                start_pos = None
                end_pos = None
                
                for idx, row in schema_df.iterrows():
                    if row['COLUMN_NAME'] == start_after:
                        start_pos = row['ORDINAL_POSITION']
                    if row['COLUMN_NAME'] == end_before:
                        end_pos = row['ORDINAL_POSITION']
                
                if not start_pos or not end_pos:
                    return {
                        'success': False,
                        'error': f'Marker columns not found: {start_after}, {end_before}'
                    }
                
                # Find size columns between markers
                size_columns = schema_df[
                    (schema_df['ORDINAL_POSITION'] > start_pos) & 
                    (schema_df['ORDINAL_POSITION'] < end_pos)
                ]['COLUMN_NAME'].tolist()
                
                # Limit to max_sizes for phase1
                if len(size_columns) > max_sizes:
                    size_columns = size_columns[:max_sizes]
                
                discovery_rate = (len(size_columns) / max_sizes) * 100 if max_sizes > 0 else 0
                
                self.logger.info(f"Start marker: {start_after} (position {start_pos})")
                self.logger.info(f"End marker: {end_before} (position {end_pos})")
                self.logger.info(f"Size columns found: {len(size_columns)}")
                self.logger.info(f"Discovery rate: {discovery_rate:.1f}%")
                self.logger.info(f"Size columns: {size_columns[:5]}...")  # Show first 5
                
                return {
                    'success': len(size_columns) >= 5,  # At least 5 size columns
                    'discovery_rate': discovery_rate,
                    'size_columns_found': len(size_columns),
                    'size_columns': size_columns,
                    'start_position': start_pos,
                    'end_position': end_pos
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Size column discovery failed: {str(e)}'
            }
    
    def test_hash_generation_logic(self) -> Dict[str, Any]:
        """Test Phase 4: Hash generation from TOML configuration"""
        self.logger.info("\n4. HASH GENERATION LOGIC")
        self.logger.info("-" * 25)
        
        try:
            if not self.config:
                return {'success': False, 'error': 'TOML configuration not loaded'}
            
            # Get hash configuration
            hash_columns = self._get_nested_config('hash.phase1.columns')
            hash_algorithm = self._get_nested_config('hash.phase1.algorithm')
            
            if not hash_columns:
                return {'success': False, 'error': 'Hash columns not found in TOML'}
            
            # Get test customer data
            test_customer = self._get_nested_config('test_data.phase1.limit_customers[0]')
            test_po = self._get_nested_config('test_data.phase1.limit_pos[0]')
            source_table = self._get_nested_config('environment.source_table')
            
            if not source_table:
                return {'success': False, 'error': 'Source table not defined in TOML'}
            
            # Test hash generation with sample data
            with db.get_connection('orders') as conn:
                # Get test customer data
                column_list = ", ".join([f"[{col}]" for col in hash_columns])
                
                sql = f"""
                SELECT TOP 3 {column_list}
                FROM dbo.{source_table} 
                WHERE [CUSTOMER NAME] = ? AND [PO NUMBER] = ?
                """
                
                df = pd.read_sql(sql, conn, params=[test_customer, test_po])
                
                if df.empty:
                    return {'success': False, 'error': 'No data for hash testing'}
                
                # Generate test hashes (simplified Python version)
                import hashlib
                
                hash_success_count = 0
                for idx, row in df.iterrows():
                    # Concatenate values for hash
                    hash_input = "|".join([str(row[col]) for col in hash_columns])
                    test_hash = hashlib.sha256(hash_input.encode()).hexdigest()
                    
                    if test_hash and len(test_hash) == 64:  # SHA256 produces 64 char hex
                        hash_success_count += 1
                
                success_rate = (hash_success_count / len(df)) * 100
                
                self.logger.info(f"Source table: dbo.{source_table}")
                self.logger.info(f"Hash algorithm: {hash_algorithm}")
                self.logger.info(f"Hash columns: {len(hash_columns)}")
                self.logger.info(f"Test records: {len(df)}")
                self.logger.info(f"Hash success rate: {success_rate:.1f}%")
                
                return {
                    'success': success_rate >= 95,
                    'success_rate': success_rate,
                    'hash_columns': hash_columns,
                    'hash_algorithm': hash_algorithm,
                    'test_records': len(df)
                }
                
        except Exception as e:
            self.logger.error(f"Hash generation test failed: {str(e)}")
            return {
                'success': False,
                'error': f'Hash generation test failed: {str(e)}'
            }
    
    def test_monday_configuration(self) -> Dict[str, Any]:
        """Test Phase 5: Monday.com configuration validation"""
        self.logger.info("\n5. MONDAY.COM CONFIGURATION")
        self.logger.info("-" * 30)
        
        try:
            if not self.config:
                return {'success': False, 'error': 'TOML configuration not loaded'}
            
            # Get Monday configuration
            board_id = self._get_nested_config('monday.phase1.board_id')
            create_groups = self._get_nested_config('monday.phase1.create_groups')
            
            # Get column mappings
            header_mappings = self._get_nested_config('monday.column_mapping.phase1.headers')
            line_mappings = self._get_nested_config('monday.column_mapping.phase1.lines')
            
            if not board_id:
                return {'success': False, 'error': 'Monday board_id not found in TOML'}
            
            validation_results = {
                'board_id_valid': bool(board_id and str(board_id).isdigit()),
                'create_groups_set': create_groups is not None,
                'header_mappings_count': len(header_mappings) if header_mappings else 0,
                'line_mappings_count': len(line_mappings) if line_mappings else 0
            }
            
            # Calculate overall success
            success_checks = sum([
                validation_results['board_id_valid'],
                validation_results['create_groups_set'],
                validation_results['header_mappings_count'] >= 3,  # At least 3 header mappings
                validation_results['line_mappings_count'] >= 2     # At least 2 line mappings
            ])
            
            success_rate = (success_checks / 4) * 100
            
            self.logger.info(f"Board ID: {board_id}")
            self.logger.info(f"Auto-create groups: {create_groups}")
            self.logger.info(f"Header mappings: {validation_results['header_mappings_count']}")
            self.logger.info(f"Line mappings: {validation_results['line_mappings_count']}")
            self.logger.info(f"Configuration success rate: {success_rate:.1f}%")
            
            return {
                'success': success_rate >= 95,
                'success_rate': success_rate,
                'board_id': board_id,
                'create_groups': create_groups,
                'validation_results': validation_results
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Monday configuration test failed: {str(e)}'
            }
    
    def run_all_tests(self):
        """Execute all TOML foundation validation tests"""
        self.logger.info("Starting TOML Foundation Validation Tests...")
        
        # Run each test phase
        test_phases = [
            ('TOML Configuration Loading', self.test_toml_configuration_loading),
            ('Source Column Validation', self.test_source_column_validation),
            ('Size Column Discovery', self.test_size_column_discovery),
            ('Hash Generation Logic', self.test_hash_generation_logic),
            ('Monday.com Configuration', self.test_monday_configuration)
        ]
        
        results_summary = []
        
        for phase_name, test_method in test_phases:
            try:
                result = test_method()
                self.test_results[phase_name] = result
                
                status = "PASSED" if result['success'] else "FAILED"
                results_summary.append((phase_name, status, result.get('success_rate', 0)))
                
            except Exception as e:
                self.test_results[phase_name] = {'success': False, 'error': str(e)}
                results_summary.append((phase_name, "ERROR", 0))
        
        # Final summary
        self.logger.info("\n" + "=" * 55)
        self.logger.info("TOML FOUNDATION VALIDATION SUMMARY")
        self.logger.info("=" * 55)
        
        total_tests = len(test_phases)
        passed_tests = sum(1 for _, status, _ in results_summary if status == "PASSED")
        overall_success_rate = (passed_tests / total_tests) * 100
        
        for phase_name, status, success_rate in results_summary:
            rate_display = f"({success_rate:.1f}%)" if success_rate > 0 else ""
            self.logger.info(f"{phase_name}: {status} {rate_display}")
        
        self.logger.info(f"\nOVERALL SUCCESS RATE: {overall_success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
        
        # Determine readiness
        if overall_success_rate >= 95:
            self.logger.info("TOML FOUNDATION: READY FOR PIPELINE DEVELOPMENT")
        elif overall_success_rate >= 80:
            self.logger.info("TOML FOUNDATION: NEEDS MINOR FIXES")
        else:
            self.logger.info("TOML FOUNDATION: REQUIRES MAJOR ATTENTION")
        
        return self.test_results
    
    def _get_nested_config(self, key_path: str):
        """Helper to get nested configuration values using dot notation"""
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                if '[' in key and ']' in key:
                    # Handle array access like 'limit_customers[0]'
                    array_key = key.split('[')[0]
                    index = int(key.split('[')[1].replace(']', ''))
                    value = value[array_key][index]
                else:
                    value = value[key]
            return value
        except (KeyError, IndexError, TypeError):
            return None

if __name__ == "__main__":
    # Run TOML foundation validation tests
    framework = TOMLFoundationTestFramework()
    results = framework.run_all_tests()
    
    # Exit with appropriate code
    overall_success = all(result['success'] for result in results.values())
    sys.exit(0 if overall_success else 1)
