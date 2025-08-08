#!/usr/bin/env python3
"""
Monday.com Configuration Manager
===============================

Centralized configuration loader for Monday.com API operations.
Provides consistent rate limiting, error handling, and performance optimization
across all ingestion and update scripts.

Usage:
    from pipelines.utils.monday_config import MondayConfig
    
    config = MondayConfig()
    batch_size = config.get_optimal_batch_size(board_id="8446553051")
    concurrency = config.get_optimal_concurrency(operation="ingestion")
    
    # Error handling with retry delays
    retry_delay = config.get_retry_delay(error_response)
"""

import logging
import tomli
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RateLimitSettings:
    """Rate limiting configuration"""
    batch_size: int
    max_concurrency: int
    delay_between_batches: float
    requests_per_minute: int
    respect_retry_in_seconds: bool

@dataclass
class RetrySettings:
    """Retry configuration for Monday.com errors"""
    max_retries: int
    base_delay: float
    max_delay: float
    exponential_multiplier: float
    jitter_factor: float

class MondayConfig:
    """Centralized Monday.com configuration manager"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration from TOML file"""
        if config_path is None:
            # Auto-discover config path
            config_path = self._find_config_path()
        
        self.config_path = config_path
        self.config = self._load_config()
        self._validate_config()
    
    def _find_config_path(self) -> Path:
        """Find monday_boards.toml configuration file"""
        # Start from current script location and work up to find project root
        current = Path(__file__).resolve()
        
        # Since we're in src/pipelines/utils/, we need to go up to project root
        while current.parent != current:
            # Look for configs directory at project root level
            config_file = current / "configs" / "pipelines" / "monday_boards.toml"
            if config_file.exists():
                return config_file
            current = current.parent
        
        # Fallback: check common locations relative to project structure
        fallback_paths = [
            Path("configs/pipelines/monday_boards.toml"),
            Path("../configs/pipelines/monday_boards.toml"),
            Path("../../configs/pipelines/monday_boards.toml"),
            Path("../../../configs/pipelines/monday_boards.toml"),
            Path("../../../../configs/pipelines/monday_boards.toml")
        ]
        
        for path in fallback_paths:
            if path.exists():
                return path.resolve()
        
        raise FileNotFoundError(
            "Could not find monday_boards.toml configuration file. "
            "Expected location: configs/pipelines/monday_boards.toml"
        )
    
    def _load_config(self) -> Dict[str, Any]:
        """Load TOML configuration file"""
        try:
            with open(self.config_path, 'rb') as f:
                config = tomli.load(f)
            logger.info(f"Loaded Monday.com config from: {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load Monday.com config: {e}")
            raise
    
    def _validate_config(self):
        """Validate required configuration sections"""
        required_sections = ['api', 'rate_limits', 'retry', 'performance']
        
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required config section: [{section}]")
    
    # ─────────────────── API Configuration ───────────────────
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration (URL, version, timeout)"""
        return self.config.get('api', {})
    
    def get_api_url(self) -> str:
        """Get Monday.com API URL"""
        return self.config['api'].get('base_url', 'https://api.monday.com/v2')
    
    def get_api_version(self) -> str:
        """Get API version"""
        return self.config['api'].get('api_version', '2025-04')
    
    def get_timeout(self) -> int:
        """Get request timeout in seconds"""
        return self.config['api'].get('timeout_seconds', 60)
    
    # ─────────────────── Rate Limiting ───────────────────
    
    def get_rate_limits(self) -> RateLimitSettings:
        """Get global rate limiting settings"""
        limits = self.config.get('rate_limits', {})
        perf = self.config.get('performance', {})
        
        return RateLimitSettings(
            batch_size=perf.get('optimal_batch_size', 25),
            max_concurrency=perf.get('optimal_concurrency_ingestion', 8),
            delay_between_batches=0.5,
            requests_per_minute=limits.get('requests_per_minute', 500),
            respect_retry_in_seconds=True
        )
    
    def get_optimal_batch_size(self, board_id: Optional[str] = None, 
                              operation: str = "ingestion") -> int:
        """Get optimal batch size for board/operation"""
        
        # Check board-specific settings first
        if board_id:
            board_config = self.config.get('boards', {}).get('registry', {}).get(board_id, {})
            if 'optimal_batch_size' in board_config:
                return board_config['optimal_batch_size']
            
            # Check board complexity category
            category = board_config.get('complexity_category', 'medium')
            category_config = self.config.get('boards', {}).get(category, {})
            if 'batch_size' in category_config:
                return category_config['batch_size']
        
        # Operation-specific defaults
        op_config = self.config.get('operations', {}).get(operation, {})
        if 'default_batch_size' in op_config:
            return op_config['default_batch_size']
        
        # Global default
        return self.config.get('performance', {}).get('optimal_batch_size', 25)
    
    def get_optimal_concurrency(self, board_id: Optional[str] = None,
                               operation: str = "ingestion") -> int:
        """Get optimal concurrency for board/operation"""
        
        # Check board-specific settings first  
        if board_id:
            board_config = self.config.get('boards', {}).get('registry', {}).get(board_id, {})
            if 'optimal_concurrency' in board_config:
                return board_config['optimal_concurrency']
            
            # Check board complexity category
            category = board_config.get('complexity_category', 'medium')
            category_config = self.config.get('boards', {}).get(category, {})
            if 'max_concurrency' in category_config:
                return category_config['max_concurrency']
        
        # Operation-specific defaults
        op_config = self.config.get('operations', {}).get(operation, {})
        if 'default_concurrency' in op_config:
            return op_config['default_concurrency']
        
        # Global default based on operation
        perf = self.config.get('performance', {})
        if operation == "ingestion":
            return perf.get('optimal_concurrency_ingestion', 8)
        elif operation == "updates":
            return perf.get('optimal_concurrency_updates', 5)
        else:
            return 5  # Conservative default
    
    # ─────────────────── Error Handling & Retry Logic ───────────────────
    
    def get_retry_settings(self) -> RetrySettings:
        """Get retry configuration"""
        retry = self.config.get('retry', {})
        
        return RetrySettings(
            max_retries=self.config.get('api', {}).get('max_retries', 5),
            base_delay=retry.get('base_delay_seconds', 1.0),
            max_delay=retry.get('max_delay_seconds', 60.0),
            exponential_multiplier=retry.get('exponential_backoff_multiplier', 2.0),
            jitter_factor=retry.get('jitter_factor', 0.1)
        )
    
    def get_retry_delay(self, error_response: Dict[str, Any]) -> float:
        """
        Calculate retry delay from Monday.com error response
        
        Handles FIELD_MINUTE_RATE_LIMIT_EXCEEDED with retry_in_seconds
        """
        retry_config = self.config.get('retry', {})
        
        # Check if this is a Monday.com rate limit error with retry_in_seconds
        if isinstance(error_response, dict):
            errors = error_response.get('errors', [])
            if errors and isinstance(errors, list):
                for error in errors:
                    extensions = error.get('extensions', {})
                    if extensions.get('code') in retry_config.get('field_rate_limit_codes', []):
                        # Monday.com provided retry_in_seconds
                        retry_seconds = extensions.get('retry_in_seconds')
                        if retry_seconds:
                            buffer = retry_config.get('retry_in_seconds_buffer', 2.0)
                            max_retry = retry_config.get('max_retry_in_seconds', 300)
                            
                            delay = min(retry_seconds + buffer, max_retry)
                            logger.warning(f"Monday.com rate limit: waiting {delay}s (suggested: {retry_seconds}s)")
                            return delay
        
        # Fallback to standard exponential backoff
        return retry_config.get('base_delay_seconds', 1.0)
    
    def is_rate_limit_error(self, error_response: Dict[str, Any]) -> bool:
        """Check if error is a Monday.com rate limit error"""
        retry_config = self.config.get('retry', {})
        rate_limit_codes = retry_config.get('field_rate_limit_codes', [])
        
        if isinstance(error_response, dict):
            errors = error_response.get('errors', [])
            if errors and isinstance(errors, list):
                for error in errors:
                    extensions = error.get('extensions', {})
                    if extensions.get('code') in rate_limit_codes:
                        return True
        
        return False
    
    # ─────────────────── Board Information ───────────────────
    
    def get_board_info(self, board_id: str) -> Dict[str, Any]:
        """Get board-specific configuration"""
        return self.config.get('boards', {}).get('registry', {}).get(board_id, {})
    
    def get_board_table_name(self, board_id: str) -> Optional[str]:
        """Get database table name for board"""
        board_info = self.get_board_info(board_id)
        return board_info.get('database_table')
    
    # ─────────────────── Performance Monitoring ───────────────────
    
    def should_track_performance(self) -> bool:
        """Check if performance monitoring is enabled"""
        return self.config.get('monitoring', {}).get('enable_performance_logging', True)
    
    def should_track_rate_limits(self) -> bool:
        """Check if rate limit tracking is enabled"""
        return self.config.get('monitoring', {}).get('enable_rate_limit_tracking', True)
    
    # ─────────────────── Environment Configuration ───────────────────
    
    def get_environment_config(self, environment: str = "production") -> Dict[str, Any]:
        """Get environment-specific configuration"""
        return self.config.get('environments', {}).get(environment, {})
    
    def apply_environment_overrides(self, settings: Dict[str, Any], 
                                   environment: str = "production") -> Dict[str, Any]:
        """Apply environment-specific overrides to settings"""
        env_config = self.get_environment_config(environment)
        
        # Apply concurrency multiplier
        multiplier = env_config.get('default_concurrency_multiplier', 1.0)
        if 'max_concurrency' in settings:
            settings['max_concurrency'] = int(settings['max_concurrency'] * multiplier)
        
        return settings

# ─────────────────── Convenience Functions ───────────────────

def load_monday_config(config_path: Optional[Path] = None) -> MondayConfig:
    """Load Monday.com configuration (convenience function)"""
    return MondayConfig(config_path)

def get_board_settings(board_id: str, operation: str = "ingestion") -> Dict[str, Any]:
    """Get optimal settings for a specific board and operation"""
    config = MondayConfig()
    
    return {
        'batch_size': config.get_optimal_batch_size(board_id, operation),
        'max_concurrency': config.get_optimal_concurrency(board_id, operation),
        'api_url': config.get_api_url(),
        'timeout': config.get_timeout(),
        'retry_settings': config.get_retry_settings()
    }

# ─────────────────── Usage Example ───────────────────

if __name__ == "__main__":
    # Example usage
    config = MondayConfig()
    
    print("🔧 Monday.com Configuration Test")
    print(f"API URL: {config.get_api_url()}")
    print(f"API Version: {config.get_api_version()}")
    
    # Test board-specific settings
    board_id = "8446553051"  # Fabric Library
    print(f"\n📋 Board {board_id} (Fabric Library):")
    print(f"Optimal Batch Size: {config.get_optimal_batch_size(board_id)}")
    print(f"Optimal Concurrency: {config.get_optimal_concurrency(board_id)}")
    
    # Test error handling
    mock_error = {
        "errors": [{
            "message": "Rate limit exceeded for the field.",
            "extensions": {
                "code": "FIELD_MINUTE_RATE_LIMIT_EXCEEDED",
                "retry_in_seconds": 18
            }
        }]
    }
    
    print(f"\n⚠️ Rate Limit Error Test:")
    print(f"Is Rate Limit Error: {config.is_rate_limit_error(mock_error)}")
    print(f"Retry Delay: {config.get_retry_delay(mock_error)}s")
