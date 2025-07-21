"""
ORDER_LIST Delta Sync Pipeline Package
=====================================
Purpose: Excel → Azure SQL → Monday.com unified sync pipeline with business key matching
Created: 2025-07-19 (Milestone 1: Foundation)
Updated: 2025-07-20 (Milestone 2: Business Key Implementation)

This package provides a complete pipeline for syncing ORDER_LIST data from Excel sources
to Azure SQL Server with Monday.com integration. It uses business key-based matching
instead of UUIDs for Excel compatibility.

Key Components:
- config_parser.py: TOML configuration management
- merge_orchestrator.py: SQL merge operations (003-005 sequence)
- monday_sync.py: Two-pass Monday.com synchronization
- cli.py: Command line interface for complete pipeline

Development Strategy:
- Milestone 1: Shadow tables and configuration (ORDER_LIST_V2, TOML config) ✅
- Milestone 2: Business key delta engine and Monday integration 🔄
- Milestone 3: Automation and monitoring
- Milestone 4: Production deployment

Architecture Integration:
- Uses pipelines.shared.customer for business key resolution
- Leverages pipelines.utils for database, logging, configuration
- Integrates with pipelines.integrations.monday for API client
- Compatible with pipelines.load_order_list for Excel ingestion

Usage:
    from pipelines.sync_order_list import DeltaSyncConfig, create_merge_orchestrator, create_monday_sync
    
    config = load_delta_sync_config('dev')
    orchestrator = create_merge_orchestrator('dev') 
    sync_engine = create_monday_sync('dev')
    
    # Complete pipeline
    cli = SyncOrderListCLI('dev')
    result = cli.execute_complete_pipeline(dry_run=True)
"""

from .config_parser import DeltaSyncConfig, load_delta_sync_config
from .merge_orchestrator import MergeOrchestrator
from .monday_sync import MondaySync, create_monday_sync
from .cli import SyncOrderListCLI

__version__ = "2.0.0"  # Milestone 2: Business Key Implementation
__author__ = "Active Apparel Group - Data Engineering Team"
__description__ = "ORDER_LIST Delta Sync Pipeline with Business Key Matching"

# Export key components for easy importing
__all__ = [
    # Configuration
    'DeltaSyncConfig',
    'load_delta_sync_config',
    
    # Core pipeline components
    'MergeOrchestrator',
    'MondaySync', 
    'create_monday_sync',
    
    # Command line interface
    'SyncOrderListCLI'
]
