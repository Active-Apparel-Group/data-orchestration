#!/usr/bin/env python3
"""
Pytest-compatible test for database configuration connections
"""

import sys
import os
import pytest
from typing import Dict, List, Tuple

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from audit_pipeline.config import get_db_config, get_connection

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

class TestDatabaseConnections:
    """Test class for database connections"""
    
    @pytest.mark.parametrize("db_key", DATABASE_KEYS)
    def test_database_connection(self, db_key: str):
        """Test individual database connection"""
        
        # Test configuration loading
        config = get_db_config(db_key)
        
        # Validate configuration
        required_fields = ['host', 'port', 'database', 'username', 'password']
        missing_fields = [field for field in required_fields if not config.get(field)]
        
        assert not missing_fields, f"Missing configuration fields for {db_key}: {', '.join(missing_fields)}"
        
        # Test connection
        with get_connection(db_key) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test_connection")
            result = cursor.fetchone()
            
            assert result is not None, f"Connection test query failed for {db_key}"
            assert result[0] == 1, f"Connection test query returned unexpected result for {db_key}"
            
            # Get database version info for logging
            cursor.execute("SELECT @@VERSION")
            version_info = cursor.fetchone()[0].split('\n')[0]  # First line only
            print(f"\n✅ {db_key}: {version_info}")
    
    def test_configuration_loading(self):
        """Test that configuration is loading properly from .env file"""
        
        # Test that we can read configuration for all databases
        for db_key in DATABASE_KEYS:
            config = get_db_config(db_key)
            assert config.get('host'), f"Failed to read host configuration for {db_key}"
            assert config.get('database'), f"Failed to read database configuration for {db_key}"
            assert config.get('username'), f"Failed to read username configuration for {db_key}"
            assert config.get('password'), f"Failed to read password configuration for {db_key}"

if __name__ == "__main__":
    # Run pytest with verbose output if called directly
    pytest.main([__file__, "-v", "-s"])
