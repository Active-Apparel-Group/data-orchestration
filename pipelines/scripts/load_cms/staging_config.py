"""
Configuration settings for Monday.com staging workflow
"""

import os
from typing import Dict, Any

# Monday.com API Configuration
MONDAY_CONFIG = {
    'api_url': 'https://api.monday.com/v2',
    'api_key': os.getenv('MONDAY_API_KEY', ''),  # Load from .env file
    'api_key': "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjE5NzM0MzUxMiwiYWFpIjoxMSwidWlkIjozMTk3MDg4OSwiaWFkIjoiMjAyMi0xMS0yMVQwNTo1MTowNi4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MTI3NDEyODgsInJnbiI6InVzZTEifQ.K2zXiugzNiYW5xo0tuXpAuZexBdv5xaAXPxubwxhNAM",
    'api_version': '2025-04',
    'board_id': '9200517329',
    'user_id': '31970889',
    'timeout_seconds': 30,
    'verify_ssl': False  # For corporate networks
}

# Batch Processing Configuration
BATCH_CONFIG = {
    'max_batch_size': 100,  # Maximum orders per customer batch
    'max_concurrent_api_calls': 5,  # Limit concurrent API calls
    'retry_config': {
        'max_retries': 3,
        'base_delay_seconds': 2,
        'max_delay_seconds': 60,
        'exponential_base': 2
    },
    'cleanup_config': {
        'keep_successful_staging_days': 7,
        'keep_error_records_days': 30,
        'keep_batch_history_days': 90
    }
}

# Database Configuration
DATABASE_CONFIG = {
    'connection_timeout': 30,
    'command_timeout': 120,
    'bulk_insert_batch_size': 500,  # Smaller chunks for concurrent processing
    'max_concurrent_workers': 4,  # Max concurrent database connections
    'staging_table_prefix': 'STG_MON_',
    'error_table_prefix': 'ERR_MON_'
}

# Column mappings for Monday.com
MONDAY_COLUMN_MAPPINGS = {
    # Size column mapping for subitems
    'subitem_columns': {
        'size_dropdown': 'dropdown_mkrak7qp',
        'order_qty': 'numeric_mkra7j8e',
        'cut_qty': 'numeric_mkraepx7',
        'sew_qty': 'numeric_mkrapgwv'
    }
}

# Error handling configuration
ERROR_CONFIG = {
    'critical_errors': [
        'AUTHENTICATION_ERROR',
        'INVALID_API_KEY',
        'BOARD_NOT_FOUND'
    ],
    'retryable_errors': [
        'NETWORK_ERROR',
        'TIMEOUT_ERROR',
        'RATE_LIMIT_ERROR',
        'TEMPORARY_SERVER_ERROR'
    ],
    'validation_errors': [
        'INVALID_COLUMN_VALUE',
        'MISSING_REQUIRED_FIELD',
        'INVALID_ITEM_NAME'
    ]
}

# Logging configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file_path': 'logs/staging_workflow.log',
    'max_file_size_mb': 10,
    'backup_count': 5
}

def get_config() -> Dict[str, Any]:
    """Get complete configuration dictionary"""
    return {
        'monday': MONDAY_CONFIG,
        'batch': BATCH_CONFIG,
        'database': DATABASE_CONFIG,
        'monday_columns': MONDAY_COLUMN_MAPPINGS,
        'error': ERROR_CONFIG,
        'logging': LOGGING_CONFIG
    }

def get_monday_headers() -> Dict[str, str]:
    """Get Monday.com API headers"""
    return {
        "Content-Type": "application/json",
        "API-Version": MONDAY_CONFIG['api_version'],
        "Authorization": f"Bearer {MONDAY_CONFIG['api_key']}"
    }
