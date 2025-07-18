"""
ORDER_LIST Delta Sync Configuration Parser
Purpose: Parse TOML configuration for ORDER_LIST → Monday.com delta sync pipeline
Location: src/pipelines/order_delta_sync/config_parser.py
Dependencies: toml, pathlib, typing

Usage:
    from src.pipelines.order_delta_sync.config_parser import DeltaSyncConfig
    
    config = DeltaSyncConfig.from_toml('configs/pipelines/order_list_delta_sync_dev.toml')
    print(f"Target table: {config.target_table}")
    print(f"Monday board ID: {config.monday_board_id}")
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import toml

# Standard import pattern for project utilities
def find_repo_root() -> Path:
    """Find repository root by looking for pipelines/utils/ directory"""
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "pipelines" / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

# Import project utilities
import logger_helper

class DeltaSyncConfig:
    """
    Configuration parser for ORDER_LIST Delta Monday Sync pipeline
    Loads TOML configuration and provides structured access to settings
    """
    
    def __init__(self, config_data: Dict[str, Any]):
        """Initialize configuration from parsed TOML data"""
        self.logger = logger_helper.get_logger(__name__)
        self._config = config_data
        self._validate_config()
    
    @classmethod
    def from_toml(cls, config_path: str) -> 'DeltaSyncConfig':
        """Load configuration from TOML file"""
        config_file = Path(config_path)
        
        # Handle both absolute and relative paths
        if not config_file.is_absolute():
            config_file = repo_root / config_path
            
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
            
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = toml.load(f)
            return cls(config_data)
        except Exception as e:
            raise ValueError(f"Failed to parse TOML configuration: {e}")
    
    def _validate_config(self):
        """Validate required configuration sections and values"""
        required_sections = ['environment', 'database', 'hash', 'monday']
        missing_sections = [section for section in required_sections 
                          if section not in self._config]
        
        if missing_sections:
            raise ValueError(f"Missing required configuration sections: {missing_sections}")
        
        self.logger.info(f"Configuration validated successfully")
    
    # Environment Configuration
    @property
    def target_table(self) -> str:
        """Primary table for ORDER_LIST data (ORDER_LIST_V2 for development)"""
        return self._config['environment']['target_table']
    
    @property
    def lines_table(self) -> str:
        """Table for size/quantity lines (ORDER_LIST_LINES)"""
        return self._config['environment']['lines_table']
    
    @property
    def delta_table(self) -> str:
        """Table for tracking header changes (ORDER_LIST_DELTA)"""
        return self._config['environment']['delta_table']
    
    @property
    def lines_delta_table(self) -> str:
        """Table for tracking line changes (ORDER_LIST_LINES_DELTA)"""
        return self._config['environment']['lines_delta_table']
    
    @property
    def board_type(self) -> str:
        """Board type: development or production"""
        return self._config['environment']['board_type']
    
    # Database Configuration
    @property
    def database_connection(self) -> str:
        """Database connection name from config.yaml"""
        return self._config['database']['connection_name']
    
    @property
    def database_schema(self) -> str:
        """Database schema (default: dbo)"""
        return self._config['database'].get('schema', 'dbo')
    
    # Hash Configuration for Change Detection
    @property
    def hash_columns(self) -> List[str]:
        """Columns used for hash-based change detection"""
        return self._config['hash']['columns']
    
    @property
    def hash_algorithm(self) -> str:
        """Hash algorithm (SHA2_256)"""
        return self._config['hash']['algorithm']
    
    # Size Column Configuration
    @property
    def size_start_marker(self) -> str:
        """Column that precedes size columns in Excel"""
        return self._config['sizes']['start_marker']
    
    @property
    def size_end_marker(self) -> str:
        """Column that follows size columns in Excel"""
        return self._config['sizes']['end_marker']
    
    @property
    def known_size_codes(self) -> List[str]:
        """Known size codes for fallback detection"""
        return self._config['sizes']['codes']
    
    @property
    def min_size_qty(self) -> int:
        """Minimum quantity for size validation"""
        return self._config['sizes']['min_qty']
    
    @property
    def max_size_qty(self) -> int:
        """Maximum quantity for size validation"""
        return self._config['sizes']['max_qty']
    
    # Monday.com Configuration
    @property
    def monday_board_id(self) -> int:
        """Monday.com board ID for the current environment"""
        board_config = self._config['monday'][self.board_type]
        return board_config['board_id']
    
    @property
    def monday_group_id(self) -> str:
        """Monday.com group ID"""
        board_config = self._config['monday'][self.board_type]
        return board_config['group_id']
    
    @property
    def monday_api_timeout(self) -> int:
        """Monday.com API timeout in seconds"""
        board_config = self._config['monday'][self.board_type]
        return board_config.get('api_timeout', 30)
    
    @property
    def monday_retry_count(self) -> int:
        """Number of retry attempts for Monday.com API"""
        board_config = self._config['monday'][self.board_type]
        return board_config.get('retry_count', 3)
    
    @property
    def monday_batch_size(self) -> int:
        """Items per batch for Monday.com operations"""
        board_config = self._config['monday'][self.board_type]
        return board_config.get('batch_size', 15)
    
    # Monday.com Column Mapping
    @property
    def monday_header_columns(self) -> Dict[str, str]:
        """Mapping of ORDER_LIST columns to Monday.com item column IDs"""
        return self._config['monday']['column_mapping']['headers']
    
    @property
    def monday_line_columns(self) -> Dict[str, str]:
        """Mapping of ORDER_LIST_LINES columns to Monday.com subitem column IDs"""
        return self._config['monday']['column_mapping']['lines']
    
    # GraphQL Template Configuration
    @property
    def graphql_create_item(self) -> str:
        """GraphQL template name for creating Monday.com items"""
        return self._config['monday']['graphql_templates']['create_item']
    
    @property
    def graphql_update_item(self) -> str:
        """GraphQL template name for updating Monday.com items"""
        return self._config['monday']['graphql_templates']['update_item']
    
    @property
    def graphql_create_subitem(self) -> str:
        """GraphQL template name for creating Monday.com subitems"""
        return self._config['monday']['graphql_templates']['create_subitem']
    
    @property
    def graphql_update_subitem(self) -> str:
        """GraphQL template name for updating Monday.com subitems"""
        return self._config['monday']['graphql_templates']['update_subitem']
    
    # Batch Processing Configuration
    @property
    def async_batch_size(self) -> int:
        """Records per batch for async processing"""
        return self._config['monday']['graphql_templates'].get('batch_size', 15)
    
    @property
    def max_concurrent_batches(self) -> int:
        """Maximum parallel batches"""
        return self._config['monday']['graphql_templates'].get('max_concurrent_batches', 3)
    
    @property
    def batch_delay_ms(self) -> int:
        """Delay between batches in milliseconds"""
        return self._config['monday']['graphql_templates'].get('batch_delay_ms', 100)
    
    # Delta Table Management
    @property
    def delta_retention_days(self) -> int:
        """Days to keep delta records after sync"""
        return self._config['delta_tables']['retention_days']
    
    @property
    def delta_batch_size(self) -> int:
        """Records per delta processing batch"""
        return self._config['delta_tables']['batch_size']
    
    @property
    def max_retry_count(self) -> int:
        """Maximum retry attempts for failed syncs"""
        return self._config['delta_tables']['max_retry_count']
    
    @property
    def retry_delay_minutes(self) -> int:
        """Delay between retry attempts in minutes"""
        return self._config['delta_tables']['retry_delay_minutes']
    
    # Validation Configuration
    @property
    def required_fields(self) -> List[str]:
        """Required fields for data validation"""
        return self._config['validation']['required_fields']
    
    @property
    def max_total_qty(self) -> int:
        """Maximum reasonable total quantity"""
        return self._config['validation']['max_total_qty']
    
    @property
    def min_total_qty(self) -> int:
        """Minimum total quantity"""
        return self._config['validation']['min_total_qty']
    
    # Development Settings
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.board_type == 'development'
    
    @property
    def dry_run_default(self) -> bool:
        """Default to dry-run mode in development"""
        return self._config.get('development', {}).get('dry_run_default', True)
    
    @property
    def test_data_limit(self) -> int:
        """Limit for test data processing"""
        return self._config.get('development', {}).get('test_data_limit', 100)
    
    @property
    def debug_mode(self) -> bool:
        """Enable verbose debugging"""
        return self._config.get('development', {}).get('debug_mode', True)
    
    @property
    def test_customer(self) -> str:
        """Default test customer"""
        return self._config.get('development', {}).get('test_customer', 'GREYSON')
    
    @property
    def test_po(self) -> str:
        """Default test PO"""
        return self._config.get('development', {}).get('test_po', '4755')
    
    @property
    def test_record_limit(self) -> int:
        """Limit for focused testing"""
        return self._config.get('development', {}).get('test_record_limit', 5)
    
    # Milestone Tracking
    @property
    def milestone_1_complete(self) -> bool:
        """Check if Milestone 1 is complete"""
        return self._config.get('milestones', {}).get('milestone_1_complete', False)
    
    @property
    def milestone_1_requirements(self) -> List[str]:
        """Requirements for Milestone 1"""
        return self._config.get('milestones', {}).get('milestone_1_requirements', [])
    
    def mark_milestone_complete(self, milestone: int) -> None:
        """Mark a milestone as complete (for future TOML updates)"""
        milestone_key = f'milestone_{milestone}_complete'
        self.logger.info(f"Milestone {milestone} marked complete")
        # Note: This would require TOML file writing for persistence
    
    # Utility Methods
    def get_full_table_name(self, table_type: str) -> str:
        """Get fully qualified table name"""
        table_map = {
            'target': self.target_table,
            'lines': self.lines_table,
            'delta': self.delta_table,
            'lines_delta': self.lines_delta_table
        }
        
        table_name = table_map.get(table_type)
        if not table_name:
            raise ValueError(f"Unknown table type: {table_type}")
            
        return f"{self.database_schema}.{table_name}"
    
    def get_hash_sql(self) -> str:
        """Generate SQL for hash calculation using CONCAT function"""
        hash_parts = []
        for column in self.hash_columns:
            hash_parts.append(f"ISNULL([{column}], '')")
        
        concat_expr = f"CONCAT({', \'|\', '.join(hash_parts)})"
        return f"CONVERT(CHAR(64), HASHBYTES('{self.hash_algorithm}', {concat_expr}), 2)"
    
    def validate_monday_config(self) -> bool:
        """Validate Monday.com configuration completeness"""
        try:
            # Check if board_id is not placeholder
            if self.monday_board_id == 123456789:
                self.logger.warning("Monday.com board_id is still placeholder value")
                return False
                
            # Check column mappings are not placeholders
            if any('placeholder' in str(v).lower() for v in self.monday_header_columns.values()):
                self.logger.warning("Monday.com column mappings contain placeholder values")
                return False
                
            return True
        except Exception as e:
            self.logger.error(f"Monday.com configuration validation failed: {e}")
            return False
    
    def __str__(self) -> str:
        """String representation for debugging"""
        return (f"DeltaSyncConfig("
                f"target_table={self.target_table}, "
                f"board_type={self.board_type}, "
                f"monday_board_id={self.monday_board_id})")


# Utility function for easy config loading
def load_delta_sync_config(environment: str = 'dev') -> DeltaSyncConfig:
    """
    Load delta sync configuration for specified environment
    
    Args:
        environment: 'dev', 'prod', or path to TOML file
        
    Returns:
        DeltaSyncConfig instance
    """
    logger = logger_helper.get_logger(__name__)
    
    if environment.endswith('.toml'):
        config_path = environment
    else:
        # Use absolute path from repository root
        repo_root = find_repo_root()
        config_path = str(repo_root / "configs" / "pipelines" / f"order_list_delta_sync_{environment}.toml")
    
    logger.info(f"Loading delta sync configuration: {config_path}")
    return DeltaSyncConfig.from_toml(config_path)


# Main execution for testing
if __name__ == "__main__":
    # Test configuration loading
    try:
        config = load_delta_sync_config('dev')
        print(f"✅ Configuration loaded: {config}")
        print(f"Target table: {config.target_table}")
        print(f"Monday board ID: {config.monday_board_id}")
        print(f"Hash columns: {config.hash_columns}")
        print(f"Development mode: {config.is_development}")
        print(f"Test customer: {config.test_customer}")
        
        # Test validation
        if config.validate_monday_config():
            print("✅ Monday.com configuration valid")
        else:
            print("⚠️  Monday.com configuration contains placeholders")
            
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        sys.exit(1)
