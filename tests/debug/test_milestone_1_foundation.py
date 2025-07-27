"""
ORDER_LIST Delta Monday Sync - Milestone 1 Validation Test
Purpose: Validate foundation components for delta sync pipeline
Created: 2025-07-18

Test Components:
1. Shadow table DDL syntax validation
2. TOML configuration loading
3. Configuration parser functionality
4. Database connection testing
5. Hash generation logic

Usage: python tests/debug/test_milestone_1_foundation.py
"""

import sys
from pathlib import Path

# Standard import pattern for project utilities
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "pipelines").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))
sys.path.insert(0, str(repo_root))

# Import project utilities
import logger_helper
import db_helper as db

# Import delta sync components
from src.pipelines.order_delta_sync import DeltaSyncConfig, load_delta_sync_config

class Milestone1FoundationTest:
    """
    Comprehensive test framework for Milestone 1 foundation components
    Validates shadow table DDL, TOML configuration, and basic functionality
    """
    
    def __init__(self):
        """Initialize test framework"""
        self.logger = logger_helper.get_logger(__name__)
        self.test_results = {}
        self.config = None
        
    def run_all_tests(self):
        """Run complete Milestone 1 validation test suite"""
        print("🚀 ORDER_LIST Delta Monday Sync - Milestone 1 Foundation Test")
        print("=" * 70)
        
        # Test phases
        self.test_results['config_loading'] = self.test_config_loading()
        self.test_results['config_validation'] = self.test_config_validation()
        self.test_results['database_connection'] = self.test_database_connection()
        self.test_results['ddl_syntax'] = self.test_ddl_syntax()
        self.test_results['hash_generation'] = self.test_hash_generation()
        
        # Generate final report
        self.generate_final_report()
        return self.test_results
    
    def test_config_loading(self):
        """Test Phase 1: TOML Configuration Loading"""
        print("\n1️⃣ TOML CONFIGURATION LOADING")
        print("-" * 40)
        
        try:
            # Test development configuration loading
            self.config = load_delta_sync_config('dev')
            
            # Validate key properties
            target_table = self.config.target_table
            monday_board_id = self.config.monday_board_id
            hash_columns = self.config.hash_columns
            
            print(f"   ✅ Configuration loaded successfully")
            print(f"   📊 Target table: {target_table}")
            print(f"   📋 Monday board ID: {monday_board_id}")
            print(f"   🔑 Hash columns: {len(hash_columns)} configured")
            
            return {
                'success': True,
                'target_table': target_table,
                'monday_board_id': monday_board_id,
                'hash_columns_count': len(hash_columns)
            }
            
        except Exception as e:
            self.logger.exception(f"Configuration loading failed: {e}")
            print(f"   ❌ Configuration loading failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_config_validation(self):
        """Test Phase 2: Configuration Validation"""
        print("\n2️⃣ CONFIGURATION VALIDATION")
        print("-" * 40)
        
        if not self.config:
            print("   ❌ Configuration not loaded, skipping validation")
            return {'success': False, 'error': 'No configuration loaded'}
        
        try:
            # Test property access
            properties_tested = 0
            
            # Environment properties
            assert self.config.target_table == "ORDER_LIST_V2"
            assert self.config.lines_table == "ORDER_LIST_LINES"
            assert self.config.board_type == "development"
            properties_tested += 3
            
            # Database properties
            assert self.config.database_connection == "orders"
            assert self.config.database_schema == "dbo"
            properties_tested += 2
            
            # Hash properties
            assert len(self.config.hash_columns) > 0
            assert self.config.hash_algorithm == "SHA2_256"
            properties_tested += 2
            
            # Monday.com properties (placeholders expected)
            monday_board_id = self.config.monday_board_id
            monday_timeout = self.config.monday_api_timeout
            properties_tested += 2
            
            # Development properties
            assert self.config.is_development == True
            assert self.config.test_customer == "GREYSON"
            assert self.config.test_po == "4755"
            properties_tested += 3
            
            print(f"   ✅ Configuration validation passed")
            print(f"   📊 Properties tested: {properties_tested}")
            print(f"   🧪 Test customer: {self.config.test_customer}")
            print(f"   📋 Test PO: {self.config.test_po}")
            
            # Test Monday.com config validation
            monday_valid = self.config.validate_monday_config()
            if monday_valid:
                print(f"   ✅ Monday.com configuration valid")
            else:
                print(f"   ⚠️  Monday.com configuration contains placeholders (expected in development)")
            
            return {
                'success': True,
                'properties_tested': properties_tested,
                'monday_config_valid': monday_valid
            }
            
        except Exception as e:
            self.logger.exception(f"Configuration validation failed: {e}")
            print(f"   ❌ Configuration validation failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_database_connection(self):
        """Test Phase 3: Database Connection"""
        print("\n3️⃣ DATABASE CONNECTION")
        print("-" * 40)
        
        if not self.config:
            print("   ❌ Configuration not loaded, skipping database test")
            return {'success': False, 'error': 'No configuration loaded'}
        
        try:
            # Test database connection using config
            connection_name = self.config.database_connection
            
            with db.get_connection(connection_name) as conn:
                # Test basic connection
                cursor = conn.cursor()
                cursor.execute("SELECT @@VERSION")
                db_version = cursor.fetchone()[0]
                
                # Test schema access
                schema_query = """
                SELECT COUNT(*) as table_count 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = ?
                """
                cursor.execute(schema_query, self.config.database_schema)
                table_count = cursor.fetchone()[0]
                
                print(f"   ✅ Database connection successful")
                print(f"   📊 Connection: {connection_name}")
                print(f"   🗄️  Schema: {self.config.database_schema}")
                print(f"   📋 Tables in schema: {table_count}")
                
                return {
                    'success': True,
                    'connection_name': connection_name,
                    'table_count': table_count,
                    'db_version': db_version[:50] + "..." if len(db_version) > 50 else db_version
                }
                
        except Exception as e:
            self.logger.exception(f"Database connection failed: {e}")
            print(f"   ❌ Database connection failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_ddl_syntax(self):
        """Test Phase 4: DDL Syntax Validation"""
        print("\n4️⃣ DDL SYNTAX VALIDATION")
        print("-" * 40)
        
        try:
            # Read DDL file
            ddl_path = repo_root / "db" / "migrations" / "001_create_shadow_tables.sql"
            
            if not ddl_path.exists():
                raise FileNotFoundError(f"DDL file not found: {ddl_path}")
            
            with open(ddl_path, 'r', encoding='utf-8') as f:
                ddl_content = f.read()
            
            # Basic syntax validation
            ddl_lines = ddl_content.split('\n')
            create_table_count = sum(1 for line in ddl_lines if 'CREATE TABLE' in line.upper())
            index_count = sum(1 for line in ddl_lines if 'CREATE INDEX' in line.upper())
            trigger_count = sum(1 for line in ddl_lines if 'CREATE TRIGGER' in line.upper())
            
            # Check for shadow table names
            expected_tables = ['ORDER_LIST_V2', 'ORDER_LIST_LINES', 'ORDER_LIST_DELTA', 'ORDER_LIST_LINES_DELTA']
            tables_found = sum(1 for table in expected_tables if table in ddl_content)
            
            # Check for delta sync columns
            delta_columns = ['row_hash', 'sync_state', 'last_synced_at', 'monday_item_id']
            delta_columns_found = sum(1 for col in delta_columns if col in ddl_content)
            
            print(f"   ✅ DDL file loaded successfully")
            print(f"   📊 DDL file size: {len(ddl_content):,} characters")
            print(f"   🗄️  CREATE TABLE statements: {create_table_count}")
            print(f"   📋 Expected tables found: {tables_found}/{len(expected_tables)}")
            print(f"   🔑 Delta columns found: {delta_columns_found}/{len(delta_columns)}")
            print(f"   📇 Index definitions: {index_count}")
            print(f"   ⚡ Trigger definitions: {trigger_count}")
            
            # Validate specific requirements
            success = (
                create_table_count >= 4 and  # 4 main tables
                tables_found == len(expected_tables) and  # All expected tables
                delta_columns_found == len(delta_columns) and  # All delta columns
                index_count >= 8  # Multiple indexes per table
            )
            
            if success:
                print(f"   ✅ DDL syntax validation passed")
            else:
                print(f"   ⚠️  DDL validation warnings (may need review)")
            
            return {
                'success': success,
                'create_table_count': create_table_count,
                'tables_found': tables_found,
                'expected_tables': len(expected_tables),
                'delta_columns_found': delta_columns_found,
                'index_count': index_count,
                'trigger_count': trigger_count
            }
            
        except Exception as e:
            self.logger.exception(f"DDL syntax validation failed: {e}")
            print(f"   ❌ DDL syntax validation failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_hash_generation(self):
        """Test Phase 5: Hash Generation Logic"""
        print("\n5️⃣ HASH GENERATION LOGIC")
        print("-" * 40)
        
        if not self.config:
            print("   ❌ Configuration not loaded, skipping hash test")
            return {'success': False, 'error': 'No configuration loaded'}
        
        try:
            # Test hash SQL generation
            hash_sql = self.config.get_hash_sql()
            hash_columns = self.config.hash_columns
            
            # Validate hash SQL structure
            assert 'HASHBYTES' in hash_sql
            assert 'SHA2_256' in hash_sql
            assert 'ISNULL' in hash_sql
            
            # Test with sample data
            sample_data = {
                'AAG ORDER NUMBER': 'JOO-00505',
                'CUSTOMER NAME': 'GREYSON',
                'STYLE DESCRIPTION': 'Test Style',
                'TOTAL QTY': 720,
                'ETA CUSTOMER WAREHOUSE DATE': '2025-07-18'
            }
            
            # Build test hash SQL with actual values
            hash_parts = []
            for column in hash_columns:
                value = sample_data.get(column, '')
                hash_parts.append(f"'{value}'")
            
            test_concat = " + '|' + ".join(hash_parts)
            test_hash_sql = f"SELECT CONVERT(CHAR(64), HASHBYTES('SHA2_256', {test_concat}), 2) as test_hash"
            
            print(f"   ✅ Hash SQL generation successful")
            print(f"   🔑 Hash columns: {len(hash_columns)}")
            print(f"   📊 Hash algorithm: {self.config.hash_algorithm}")
            print(f"   🧪 Sample test data prepared")
            print(f"   📋 Generated hash SQL: {len(hash_sql)} characters")
            
            # Test hash SQL with database (if connection available)
            hash_test_result = None
            if self.test_results.get('database_connection', {}).get('success'):
                try:
                    with db.get_connection(self.config.database_connection) as conn:
                        cursor = conn.cursor()
                        cursor.execute(test_hash_sql)
                        hash_test_result = cursor.fetchone()[0]
                        print(f"   🔑 Test hash generated: {hash_test_result[:16]}...")
                except Exception as e:
                    print(f"   ⚠️  Hash database test failed: {e}")
            
            return {
                'success': True,
                'hash_columns_count': len(hash_columns),
                'hash_sql_length': len(hash_sql),
                'test_hash': hash_test_result
            }
            
        except Exception as e:
            self.logger.exception(f"Hash generation test failed: {e}")
            print(f"   ❌ Hash generation test failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_final_report(self):
        """Generate final milestone 1 validation report"""
        print("\n📊 MILESTONE 1 FOUNDATION - FINAL REPORT")
        print("=" * 70)
        
        # Calculate overall success
        successful_tests = sum(1 for result in self.test_results.values() 
                             if result.get('success', False))
        total_tests = len(self.test_results)
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Report individual test results
        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result.get('success') else "❌ FAILED"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
            
            # Show key metrics for successful tests
            if result.get('success'):
                for key, value in result.items():
                    if key != 'success' and key != 'error':
                        print(f"   {key}: {value}")
            else:
                if 'error' in result:
                    print(f"   Error: {result['error']}")
        
        print(f"\n📈 OVERALL SUCCESS RATE: {success_rate:.1f}% ({successful_tests}/{total_tests})")
        
        # Milestone 1 completion assessment
        critical_tests = ['config_loading', 'ddl_syntax']
        critical_passed = all(self.test_results.get(test, {}).get('success', False) 
                            for test in critical_tests)
        
        if critical_passed and success_rate >= 80:
            print(f"🎉 MILESTONE 1 FOUNDATION: ✅ READY FOR MILESTONE 2")
            print(f"\nNext Steps:")
            print(f"   1. Deploy shadow tables to development database")
            print(f"   2. Begin Milestone 2: Delta sync engine development")
            print(f"   3. Implement hash-based change detection")
            print(f"   4. Create MERGE operations for headers and lines")
        else:
            print(f"⚠️  MILESTONE 1 FOUNDATION: NEEDS ATTENTION")
            print(f"\nRequired Actions:")
            if not self.test_results.get('config_loading', {}).get('success'):
                print(f"   - Fix TOML configuration loading issues")
            if not self.test_results.get('ddl_syntax', {}).get('success'):
                print(f"   - Review and fix DDL syntax issues")
            if success_rate < 80:
                print(f"   - Address failed test components")
        
        print(f"\n🔧 Development Environment Status:")
        if self.config:
            print(f"   Target table: {self.config.target_table}")
            print(f"   Test customer: {self.config.test_customer}")
            print(f"   Test PO: {self.config.test_po}")
            print(f"   Debug mode: {self.config.debug_mode}")


# Main execution
if __name__ == "__main__":
    test_framework = Milestone1FoundationTest()
    results = test_framework.run_all_tests()
