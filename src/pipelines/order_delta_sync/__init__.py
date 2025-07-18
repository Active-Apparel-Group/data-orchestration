"""
ORDER_LIST Delta Monday Sync Pipeline Package
Purpose: Delta synchronization between ORDER_LIST and Monday.com
Strategy: Hash-based change detection with shadow tables for zero-downtime development

Key Components:
- config_parser.py: TOML configuration management
- run_merges.py: SQL merge operations (headers and lines)
- sync_monday.py: Monday.com API synchronization
- cli.py: Command-line interface for pipeline execution

Development Strategy:
- Milestone 1: Shadow tables and configuration (ORDER_LIST_V2, TOML config)
- Milestone 2: Delta sync engine and Monday integration
- Milestone 3: Automation and monitoring
- Milestone 4: Production deployment

Usage:
    from src.pipelines.order_delta_sync import DeltaSyncConfig, sync_monday
    
    config = DeltaSyncConfig.from_toml('configs/pipelines/order_list_delta_sync_dev.toml')
    sync_monday.run_delta_sync(config, dry_run=True)
"""

from .config_parser import DeltaSyncConfig, load_delta_sync_config

__version__ = "1.0.0"
__author__ = "ORDER_LIST Delta Monday Sync - Milestone 1"

# Export key components for easy importing
__all__ = [
    'DeltaSyncConfig',
    'load_delta_sync_config'
]
