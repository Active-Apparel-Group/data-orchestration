#!/usr/bin/env python3
"""
Test Configuration Connections

This script tests all database connections defined in the .env file
to ensure they are properly configured and accessible.
"""

import sys
import os
import logging
import traceback
from typing import Dict, List, Tuple
import pyodbc
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from audit_pipeline.config import get_db_config, get_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database connection keys from .env file
DATABASE_KEYS = [
    'DMS',
    'DMS_ITEM', 
    'ORDERS',
    'INFOR_132',
    'INFOR_134',
    'GFS',
    'GWS',
    'WMS',
    'DISTRIBUTION',
    'QUICKDATA',
    'WAH'
]

def test_single_connection(db_key: str) -> Tuple[bool, str]:
    """
    Test a single database connection.
    
    Args:
        db_key: Database key from environment variables
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        logger.info(f"Testing connection to {db_key}...")
        
        # Get configuration
        config = get_db_config(db_key)
        
        # Validate configuration
        required_fields = ['host', 'port', 'database', 'username', 'password']
        missing_fields = [field for field in required_fields if not config.get(field)]
        
        if missing_fields:
            return False, f"Missing configuration fields: {', '.join(missing_fields)}"
        
        # Test connection
        with get_connection(db_key) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test_connection")
            result = cursor.fetchone()
            
            if result and result[0] == 1:
                # Get database version info
                cursor.execute("SELECT @@VERSION")
                version_info = cursor.fetchone()[0].split('\n')[0]  # First line only
                return True, f"Connection successful - {version_info}"
            else:
                return False, "Connection test query failed"
                
    except pyodbc.Error as e:
        error_msg = str(e)
        if "Login timeout expired" in error_msg:
            return False, "Connection timeout - check network connectivity"
        elif "Login failed" in error_msg:
            return False, "Authentication failed - check credentials"
        elif "Cannot open database" in error_msg:
            return False, "Database not found or access denied"
        else:
            return False, f"Database error: {error_msg}"
            
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def test_all_connections() -> Dict[str, Tuple[bool, str]]:
    """
    Test all database connections.
    
    Returns:
        Dictionary mapping db_key to (success, message) tuples
    """
    results = {}
    
    for db_key in DATABASE_KEYS:
        try:
            success, message = test_single_connection(db_key)
            results[db_key] = (success, message)
        except Exception as e:
            results[db_key] = (False, f"Test failed: {str(e)}")
            logger.error(f"Error testing {db_key}: {traceback.format_exc()}")
    
    return results

def print_connection_summary(results: Dict[str, Tuple[bool, str]]) -> None:
    """Print a formatted summary of connection test results."""
    
    print("\n" + "="*80)
    print("DATABASE CONNECTION TEST RESULTS")
    print("="*80)
    
    successful = []
    failed = []
    
    for db_key, (success, message) in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"\n{db_key:15} | {status}")
        print(f"{'':15} | {message}")
        
        if success:
            successful.append(db_key)
        else:
            failed.append(db_key)
    
    print("\n" + "="*80)
    print(f"SUMMARY: {len(successful)} successful, {len(failed)} failed")
    
    if successful:
        print(f"\n✅ Successful connections: {', '.join(successful)}")
    
    if failed:
        print(f"\n❌ Failed connections: {', '.join(failed)}")
        print("\nTroubleshooting tips for failed connections:")
        print("- Check network connectivity to the database server")
        print("- Verify credentials are correct in .env file")
        print("- Ensure database server is running and accessible")
        print("- Check firewall settings")
        print("- Verify database name exists")
    
    print("="*80)

def test_configuration_loading() -> bool:
    """Test that configuration is loading properly from .env file."""
    try:
        # Load environment
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if not os.path.exists(env_path):
            logger.error(f".env file not found at {env_path}")
            return False
        
        load_dotenv(env_path)
        logger.info("✅ .env file loaded successfully")
        
        # Test that we can read at least one configuration
        test_config = get_db_config('DMS')
        if not test_config.get('host'):
            logger.error("❌ Failed to read configuration from .env")
            return False
        
        logger.info("✅ Configuration reading test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration loading failed: {str(e)}")
        return False

def main():
    """Main function to run all connection tests."""
    print("Starting Database Connection Tests...")
    print(f"Testing {len(DATABASE_KEYS)} database connections...")
    
    # Test configuration loading first
    if not test_configuration_loading():
        print("\n❌ Configuration loading failed. Please check your .env file.")
        sys.exit(1)
    
    # Test all connections
    results = test_all_connections()
    
    # Print summary
    print_connection_summary(results)
    
    # Set exit code based on results
    failed_count = sum(1 for success, _ in results.values() if not success)
    if failed_count > 0:
        print(f"\n⚠️  {failed_count} connection(s) failed. See details above.")
        sys.exit(1)
    else:
        print("\n🎉 All database connections successful!")
        sys.exit(0)

if __name__ == "__main__":
    main()
