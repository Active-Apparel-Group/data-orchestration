"""
ORDER_LIST Delta Monday Sync - Milestone 1 Simple Test
Purpose: Validate foundation components with simplified approach
Created: 2025-07-18 (Fixed Unicode/Emoji violations)

SUCCESS CRITERIA:
1. TOML configuration loads without errors
2. Config parser initializes successfully  
3. Database connection configuration is valid
4. Hash generation SQL produces valid syntax
5. Basic infrastructure integration works

NO UNICODE/EMOJI IN OUTPUT - ASCII ONLY PER COPILOT INSTRUCTIONS
"""

import sys
from pathlib import Path

# Add project utilities to path
repo_root = Path.cwd()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

try:
    import logger_helper
    import db_helper as db
    print("SUCCESS: Core utilities imported")
except ImportError as e:
    print(f"FAILED: Import error - {e}")
    sys.exit(1)

def test_toml_configuration():
    """Test Phase 1: TOML Configuration Loading"""
    print("\n--- PHASE 1: TOML CONFIGURATION ---")
    
    try:
        import tomli
        config_path = repo_root / "configs" / "pipelines" / "order_list_delta_sync_dev.toml"
        
        if not config_path.exists():
            print(f"FAILED: Config file not found: {config_path}")
            return False
            
        with open(config_path, 'rb') as f:
            config = tomli.load(f)
            
        print(f"SUCCESS: TOML loaded with {len(config)} sections")
        
        # Validate required sections
        required_sections = ['environment', 'database', 'hash', 'sizes']
        missing_sections = [s for s in required_sections if s not in config]
        
        if missing_sections:
            print(f"FAILED: Missing sections: {missing_sections}")
            return False
            
        print("SUCCESS: All required sections present")
        return True
        
    except Exception as e:
        print(f"FAILED: TOML loading error - {e}")
        return False

def test_config_parser():
    """Test Phase 2: Configuration Parser"""
    print("\n--- PHASE 2: CONFIG PARSER ---")
    
    try:
        # Import the config parser module
        sys.path.insert(0, str(repo_root / "src" / "pipelines" / "order_delta_sync"))
        from config_parser import DeltaSyncConfig
        import tomli
        
        # Load TOML config
        config_path = repo_root / "configs" / "pipelines" / "order_list_delta_sync_dev.toml"
        with open(config_path, 'rb') as f:
            config_data = tomli.load(f)
        
        # Initialize config parser
        config = DeltaSyncConfig(config_data)
        
        print("SUCCESS: Config parser initialized")
        
        # Test hash SQL generation
        hash_sql = config.get_hash_sql()
        if "CONCAT" not in hash_sql:
            print("FAILED: Hash SQL missing CONCAT function")
            return False
            
        print("SUCCESS: Hash SQL generated with CONCAT")
        return True
        
    except Exception as e:
        print(f"FAILED: Config parser error - {e}")
        return False

def test_database_config():
    """Test Phase 3: Database Configuration"""
    print("\n--- PHASE 3: DATABASE CONFIG ---")
    
    try:
        # Load database configuration
        config = db.load_config()
        
        if 'orders' not in config.get('databases', {}):
            print("FAILED: 'orders' database not found in config")
            return False
            
        print("SUCCESS: Database configuration valid")
        return True
        
    except Exception as e:
        print(f"FAILED: Database config error - {e}")
        return False

def test_migration_ddl():
    """Test Phase 4: Migration DDL Validation"""
    print("\n--- PHASE 4: MIGRATION DDL ---")
    
    try:
        ddl_path = repo_root / "db" / "migrations" / "001_create_shadow_tables.sql"
        
        if not ddl_path.exists():
            print(f"FAILED: Migration DDL not found: {ddl_path}")
            return False
            
        with open(ddl_path, 'r') as f:
            ddl_content = f.read()
            
        # Check for hardcoded hash logic (should not exist)
        if "HASHBYTES('SHA2_256'" in ddl_content:
            print("FAILED: Hardcoded hash logic found in DDL")
            return False
            
        # Check for required tables
        required_tables = ["ORDER_LIST_V2", "ORDER_LIST_LINES"]
        missing_tables = [t for t in required_tables if f"CREATE TABLE dbo.{t}" not in ddl_content]
        
        if missing_tables:
            print(f"FAILED: Missing table definitions: {missing_tables}")
            return False
            
        print("SUCCESS: Migration DDL validation passed")
        return True
        
    except Exception as e:
        print(f"FAILED: DDL validation error - {e}")
        return False

def main():
    """Main test execution"""
    print("ORDER_LIST Delta Monday Sync - Milestone 1 Foundation Test")
    print("=" * 60)
    
    # Track test results
    test_results = []
    
    # Run all test phases
    test_results.append(("TOML Configuration", test_toml_configuration()))
    test_results.append(("Config Parser", test_config_parser()))
    test_results.append(("Database Config", test_database_config()))
    test_results.append(("Migration DDL", test_migration_ddl()))
    
    # Generate final report
    print("\n" + "=" * 60)
    print("FINAL TEST REPORT")
    print("=" * 60)
    
    passed_tests = 0
    for test_name, result in test_results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed_tests += 1
    
    success_rate = (passed_tests / len(test_results)) * 100
    print(f"\nOVERALL SUCCESS RATE: {success_rate:.1f}% ({passed_tests}/{len(test_results)} tests passed)")
    
    if success_rate >= 75:
        print("MILESTONE 1 FOUNDATION: READY FOR DEVELOPMENT")
    else:
        print("MILESTONE 1 FOUNDATION: NEEDS FIXES BEFORE PROCEEDING")
    
    return success_rate >= 75

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
