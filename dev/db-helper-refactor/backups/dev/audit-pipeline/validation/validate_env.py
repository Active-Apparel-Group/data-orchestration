#!/usr/bin/env python3
"""
Final environment validation script
Tests configuration loading and Azure SQL connectivity
"""

# Standard repository root finding pattern
import sys
from pathlib import Path

def find_repo_root() -> Path:
    """Find repository root by looking for marker files"""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if any((parent / marker).exists() for marker in ['.git', 'pyproject.toml', 'requirements.txt']):
            return parent
    return current.parent

# Add utils to path for consistent imports
repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))
sys.path.insert(0, str(repo_root / "scripts"))

from audit_pipeline.config import get_connection, get_db_config
import logger_helper
import os

# Initialize logger
logger = logger_helper.get_logger("validate_env")

def test_azure_databases():
    """Test Azure SQL database connections"""
    logger.info("🔧 Testing Azure SQL databases...")
    logger.info("-" * 40)
    
    azure_dbs = ['dms', 'orders']
    results = {}
    
    for db in azure_dbs:
        try:
            config = get_db_config(db)
            logger.info(f"✅ {db.upper():8} | Config loaded: {config['host']}")
            
            # Test connection (with timeout)
            conn = get_connection(db)
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result and result[0] == 1:
                logger.info(f"✅ {db.upper():8} | Connection successful")
                results[db] = True
            else:
                results[db] = False
                
        except Exception as e:
            logger.error(f"❌ {db.upper():8} | Error: {str(e)}")
            results[db] = False
    
    return results

def test_environment_loading():
    """Test environment variable loading"""
    logger.info("🌍 Testing environment configuration...")
    logger.info("-" * 40)
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Test key variables
    test_vars = [
        'DB_DMS_HOST',
        'DB_ORDERS_HOST', 
        'SECRET_DMS_PWD',
        'SECRET_ORDERS_PWD'
    ]
    
    all_good = True
    for var in test_vars:
        value = os.getenv(var)
        if value:
            masked_value = value[:10] + "..." if len(value) > 10 else value
            logger.info(f"✅ {var:20} | {masked_value}")
        else:
            logger.error(f"❌ {var:20} | Missing")
            all_good = False
    
    return all_good

def main():
    """Main validation function"""
    logger.info("🚀 Data Orchestration Environment Validation")
    logger.info("=" * 50)
    
    # Test environment loading
    env_ok = test_environment_loading()
    logger.info("")
    
    # Test Azure databases
    azure_results = test_azure_databases()
    logger.info("")
    
    # Summary
    logger.info("=" * 50)
    logger.info("📊 Validation Summary:")
    
    azure_success = sum(azure_results.values())
    azure_total = len(azure_results)
    
    logger.info(f"  Environment Variables | {'✅ PASS' if env_ok else '❌ FAIL'}")
    logger.info(f"  Azure SQL Connections | {azure_success}/{azure_total} successful")
    
    if env_ok and azure_success == azure_total:
        logger.info("\n🎉 Environment is ready for development!")
        logger.info("💡 Note: On-premise databases (Distribution, WAH) require VPN access")
        return True
    else:
        logger.error("\n⚠️  Environment validation failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
