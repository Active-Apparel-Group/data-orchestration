"""
ORDER_LIST Monday Sync Configuration Parser
Purpose: Parse TOML configuration for ORDER_LIST → Monday.com sync pipeline
Location: src/pipelines/sync_order_list/config_parser.py
Dependencies: toml, pathlib, typing

Usage:
    from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
    
    config = DeltaSyncConfig.from_toml('configs/pipelines/sync_order_list_dev.toml')
    print(f"Target table: {config.target_table}")
    print(f"Monday board ID: {config.monday_board_id}")
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import tomli

# Modern import pattern for project utilities
from pipelines.utils import db, logger

class DeltaSyncConfig:
    """
    Configuration parser for ORDER_LIST Monday Sync pipeline
    Loads TOML configuration and provides structured access to settings
    Supports environment-specific configuration (development/production)
    """
    
    def __init__(self, config_data: Dict[str, Any], environment: str = 'development'):
        """Initialize configuration from parsed TOML data"""
        self.logger = logger.get_logger(__name__)
        self._config = config_data
        self._environment = environment
        self._validate_config()
    
    @classmethod
    def from_toml(cls, config_path: str, environment: str = 'development') -> 'DeltaSyncConfig':
        """Load configuration from TOML file with environment selection"""
        """Load configuration from TOML file"""
        config_file = Path(config_path)
        
        # Handle both absolute and relative paths
        if not config_file.is_absolute():
            # Find repository root
            current = Path(__file__).parent
            while current != current.parent:
                if (current / "pipelines" / "utils").exists():
                    repo_root = current
                    break
                current = current.parent
            else:
                raise FileNotFoundError("Could not find repository root")
                
            config_file = repo_root / config_path
            
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
            
        try:
            with open(config_file, 'rb') as f:  # tomli requires binary mode
                config_data = tomli.load(f)
            return cls(config_data, environment)
        except Exception as e:
            raise ValueError(f"Failed to parse TOML configuration: {e}")
    
    def _validate_config(self):
        """Validate required configuration sections and values"""
        required_sections = ['phase', 'environment']
        missing_sections = [section for section in required_sections 
                          if section not in self._config]
        
        if missing_sections:
            raise ValueError(f"Missing required configuration sections: {missing_sections}")
        
        # Validate environment-specific section exists
        env_section = f"environment.{self._environment}"
        if env_section not in self._config:
            raise ValueError(f"Missing environment configuration section: [{env_section}]")
        
        self.logger.info(f"Configuration validated successfully for environment: {self._environment}")
    
    # Environment Properties
    @property
    def environment(self) -> str:
        """Current environment (development/production)"""
        return self._environment
    
    def _get_env_config(self) -> Dict[str, Any]:
        """Get environment-specific configuration section"""
        env_key = f"environment.{self._environment}"
        return self._config.get(env_key, {})
    
    # Environment Configuration (using environment-specific sections)
    @property
    def source_table(self) -> str:
        """Source table name from environment-specific configuration"""
        env_config = self._get_env_config()
        return env_config.get('source_table', 'swp_ORDER_LIST_V2')
    
    @property
    def target_table(self) -> str:
        """Primary table for ORDER_LIST data (environment-specific)"""
        env_config = self._get_env_config()
        return env_config.get('target_table', 'ORDER_LIST_V2')
    
    @property
    def lines_table(self) -> str:
        """Table for size/quantity lines (ORDER_LIST_LINES)"""
        env_config = self._get_env_config()
        return env_config.get('lines_table', 'ORDER_LIST_LINES')
    
    @property
    def source_lines_table(self) -> str:
        """Staging table for size/quantity lines (environment-specific)"""
        env_config = self._get_env_config()
        return env_config.get('source_lines_table', 'swp_ORDER_LIST_LINES')
    
    @property
    def delta_table(self) -> str:
        """Table for tracking header changes (ORDER_LIST_DELTA)"""
        return self._config.get('delta_table', 'ORDER_LIST_DELTA')
    
    @property
    def lines_delta_table(self) -> str:
        """Table for tracking line changes (ORDER_LIST_LINES_DELTA)"""
        return self._config.get('lines_delta_table', 'ORDER_LIST_LINES_DELTA')
    
    @property
    def board_type(self) -> str:
        """Board type: development or production (same as environment)"""
        return self._environment
    
    # Database Configuration (using environment-specific sections)
    @property
    def database_connection(self) -> str:
        """Database connection name from environment-specific configuration"""
        env_config = self._get_env_config()
        return env_config.get('database', 'orders')
    
    @property
    def db_key(self) -> str:
        """Database key for db.get_connection() - consistent naming"""
        return self.database_connection
    
    @property
    def database_schema(self) -> str:
        """Database schema (default: dbo)"""
        return 'dbo'
    
    # Hash Configuration for Change Detection (adapted to actual TOML structure)
    @property
    def hash_columns(self) -> List[str]:
        """Columns used for hash-based change detection"""
        hash_config = self._config.get('hash', {}).get('phase1', {})
        return hash_config.get('columns', [])
    
    @property
    def hash_algorithm(self) -> str:
        """Hash algorithm (SHA2_256)"""
        return "SHA2_256"
    
    # Monday.com Configuration (using environment-aware sections)
    @property
    def monday_board_id(self) -> int:
        """Monday.com board ID for the current environment"""
        monday_config = self._config.get('monday', {}).get(self._environment, {})
        # Fallback to legacy phase1 config if environment config not found
        if not monday_config:
            monday_config = self._config.get('monday', {}).get('phase1', {})
        return monday_config.get('board_id', 9609317401)  # Default dev board
    
    @property
    def monday_group_id(self) -> str:
        """Monday.com group ID"""
        monday_config = self._config.get('monday', {}).get(self._environment, {})
        return monday_config.get('group_id', '')
    
    # Business Columns (adapted to actual TOML structure) 
    def get_business_columns(self) -> List[str]:
        """Get list of business columns from TOML configuration"""
        # Get business columns from phase1 configuration
        columns_config = self._config.get('columns', {}).get('phase1', {})
        business_columns = columns_config.get('order_list', [])
        
        # If no specific columns defined, use hash columns
        if not business_columns:
            business_columns = self.hash_columns
            
        return business_columns
    
    # Utility Methods (simplified for actual TOML structure)
    def get_full_table_name(self, table_type: str) -> str:
        """Get fully qualified table name from TOML configuration"""
        table_map = {
            'source': self.source_table,
            'target': self.target_table,
            'lines': self.lines_table,
            'source_lines': self.source_lines_table,
            'delta': self.delta_table,
            'lines_delta': self.lines_delta_table
        }
        
        table_name = table_map.get(table_type)
        if not table_name:
            raise ValueError(f"Unknown table type: {table_type}")
            
        return f"{self.database_schema}.{table_name}"
    
    def get_hash_sql(self) -> str:
        """Generate SQL for hash calculation using CONCAT function"""
        if not self.hash_columns:
            return "CONVERT(CHAR(64), HASHBYTES('SHA2_256', 'DEFAULT'), 2)"
            
        hash_parts = []
        for column in self.hash_columns:
            hash_parts.append(f"ISNULL([{column}], '')")
        
        concat_expr = f"CONCAT({', \'|\', '.join(hash_parts)})"
        return f"CONVERT(CHAR(64), HASHBYTES('{self.hash_algorithm}', {concat_expr}), 2)"
    
    def __str__(self) -> str:
        """String representation for debugging"""
        return (f"DeltaSyncConfig("
                f"source_table={self.source_table}, "
                f"target_table={self.target_table}, "
                f"board_type={self.board_type}, "
                f"monday_board_id={self.monday_board_id})")


    def get_dynamic_size_columns(self) -> List[str]:
        """
        Get dynamic size columns from actual swp_ORDER_LIST_V2 table schema
        Uses INFORMATION_SCHEMA to discover columns between markers
        
        Returns:
            List of actual size column names from database (e.g., ['XS', 'S', 'M', 'L', 'XL', '[2T]', '[3T]', etc.])
        """
        try:
            # Get size column configuration from TOML
            size_config = self._config.get('size_detection', {}).get('phase1', {})
            start_after = size_config.get('start_after', 'UNIT OF MEASURE')
            end_before = size_config.get('end_before', 'TOTAL QTY')
            max_sizes = size_config.get('max_sizes', 300)
            
            # Get the actual source table name from environment-specific config
            source_table = self.source_table
            
            self.logger.info(f"Discovering size columns from {source_table} between '{start_after}' and '{end_before}' (env: {self._environment})")
            
            # Query INFORMATION_SCHEMA for actual column names and ordinal positions
            with db.get_connection(self.db_key) as conn:
                size_discovery_sql = """
                SELECT COLUMN_NAME, ORDINAL_POSITION
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = ? 
                  AND TABLE_SCHEMA = ?
                  AND ORDINAL_POSITION > (
                      SELECT ORDINAL_POSITION 
                      FROM INFORMATION_SCHEMA.COLUMNS 
                      WHERE TABLE_NAME = ? AND TABLE_SCHEMA = ? 
                        AND COLUMN_NAME = ?
                  )
                  AND ORDINAL_POSITION < (
                      SELECT ORDINAL_POSITION 
                      FROM INFORMATION_SCHEMA.COLUMNS 
                      WHERE TABLE_NAME = ? AND TABLE_SCHEMA = ? 
                        AND COLUMN_NAME = ?
                  )
                ORDER BY ORDINAL_POSITION
                """
                
                import pandas as pd
                result_df = pd.read_sql(
                    size_discovery_sql, 
                    conn, 
                    params=[
                        source_table, self.database_schema,  # Main table
                        source_table, self.database_schema, start_after,  # Start marker
                        source_table, self.database_schema, end_before   # End marker
                    ]
                )
                
                if result_df.empty:
                    self.logger.warning(f"No size columns found between '{start_after}' and '{end_before}'")
                    return []
                
                # Get column names and apply size limit
                size_columns = result_df['COLUMN_NAME'].tolist()[:max_sizes]
                
                self.logger.info(f"Discovered {len(size_columns)} size columns from database schema")
                self.logger.debug(f"First 5 size columns: {size_columns[:5]}")
                
                return size_columns
                
        except Exception as e:
            self.logger.error(f"Failed to discover dynamic size columns from database: {e}")
            self.logger.warning("Falling back to empty size columns list")
            return []
    
    def get_size_columns_config(self) -> Dict[str, Any]:
        """
        Get complete size columns configuration from actual database schema
        
        Returns:
            Dictionary with real size columns details and metadata
        """
        try:
            # Get real size columns from database
            size_columns = self.get_dynamic_size_columns()
            
            return {
                'size_columns': size_columns,
                'total_count': len(size_columns),
                'detection_method': 'database_information_schema',
                'source_table': self.source_table,
                'environment': self._environment,
                'start_marker': self._config.get('size_detection', {}).get('phase1', {}).get('start_after', 'UNIT OF MEASURE'),
                'end_marker': self._config.get('size_detection', {}).get('phase1', {}).get('end_before', 'TOTAL QTY'),
                'discovery_successful': len(size_columns) > 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get size columns config from database: {e}")
            return {
                'size_columns': [],
                'total_count': 0,
                'error': str(e),
                'detection_method': 'database_information_schema',
                'discovery_successful': False
            }


# Utility function for easy config loading with environment support
def load_delta_sync_config(environment: str = 'development') -> DeltaSyncConfig:
    """
    Load delta sync configuration for specified environment
    
    Args:
        environment: 'development', 'production', or path to TOML file
        
    Returns:
        DeltaSyncConfig instance
    """
    logger_instance = logger.get_logger(__name__)
    
    if environment.endswith('.toml'):
        config_path = environment
        environment = 'development'  # Default environment when loading from file path
    else:
        # Find repository root - go up from src/pipelines/sync_order_list/
        current = Path(__file__).parent.parent.parent.parent  # Go up 4 levels
        
        if not (current / "configs" / "pipelines").exists():
            raise FileNotFoundError(f"Could not find configs/pipelines directory from {current}")
        
        # Use the actual TOML file name
        config_path = str(current / "configs" / "pipelines" / "sync_order_list.toml")
    
    logger_instance.info(f"Loading sync configuration: {config_path} (environment: {environment})")
    return DeltaSyncConfig.from_toml(config_path, environment)


# Main execution for testing
if __name__ == "__main__":
    # Test configuration loading with both environments
    try:
        # Test development environment
        print("🧪 Testing Development Environment:")
        config_dev = load_delta_sync_config('development')
        print(f"✅ Development config loaded: {config_dev}")
        print(f"  Source table: {config_dev.source_table}")
        print(f"  Target table: {config_dev.target_table}")
        print(f"  Monday board ID: {config_dev.monday_board_id}")
        print(f"  Environment: {config_dev.environment}")
        print()
        
        # Test production environment
        print("🏭 Testing Production Environment:")
        config_prod = load_delta_sync_config('production')
        print(f"✅ Production config loaded: {config_prod}")
        print(f"  Source table: {config_prod.source_table}")
        print(f"  Target table: {config_prod.target_table}")
        print(f"  Monday board ID: {config_prod.monday_board_id}")
        print(f"  Environment: {config_prod.environment}")
        print()
        
        # Verify environment switching works correctly
        assert config_dev.target_table != config_prod.target_table, "Environment tables should be different"
        print("✅ Environment switching validation passed")
        
    except Exception as e:
        print(f"❌ Configuration testing failed: {e}")
        sys.exit(1)
