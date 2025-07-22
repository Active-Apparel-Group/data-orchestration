"""
ORDER_LIST Delta Sync Pipeline Package - STEP 4 Enhanced
========================================================
Purpose: Ultra-lightweight Monday.com sync for STEP 4 of existing pipeline
Created: 2025-07-22 (Architecture Simplification)

This package provides ONLY the Monday.com sync enhancement for STEP 4:
- monday_api_client.py: TOML + GraphQL + HTTP client
- sync_engine.py: Database DELTA query + API calls + status updates  
- cli.py: Ultra-minimal command-line interface

Pipeline Integration:
STEP 0: ingest_excel.py         ← UNCHANGED (existing)
STEP 1: 003_merge_headers.sql   ← UNCHANGED (existing)  
STEP 2: 004_unpivot_sizes.sql   ← UNCHANGED (existing)
STEP 3: 005_merge_lines.sql     ← UNCHANGED (existing)
STEP 4: sync_monday.py          ← ENHANCED (this package)
STEP 5: housekeeping            ← UNCHANGED (existing)

Architecture: Ultra-lightweight (2 files total)
- Direct DELTA table execution
- TOML-driven configuration  
- Modern imports: src.pipelines.utils only

Usage:
    from src.pipelines.sync_order_list import SyncEngine, MondayAPIClient
    
    # Ultra-lightweight sync
    engine = SyncEngine("configs/pipelines/sync_order_list.toml")
    result = engine.run_sync(dry_run=True)
"""

# Keep existing imports for backward compatibility where they exist
try:
    from .config_parser import DeltaSyncConfig, load_delta_sync_config
except ImportError:
    DeltaSyncConfig = None
    load_delta_sync_config = None

try:
    from .merge_orchestrator import MergeOrchestrator  
except ImportError:
    MergeOrchestrator = None

# Ultra-lightweight Monday.com sync (STEP 4 enhancement)
from .monday_api_client import MondayAPIClient
from .sync_engine import SyncEngine
from .cli import UltraLightweightSyncCLI as SyncCLI

__version__ = "2.1.0"  # Ultra-lightweight Monday.com sync
__author__ = "Active Apparel Group - Data Engineering Team"
__description__ = "Ultra-lightweight Monday.com sync for STEP 4 enhancement"

# Export ultra-lightweight components
__all__ = [
    # Ultra-lightweight Monday.com sync (STEP 4)
    'MondayAPIClient',
    'SyncEngine',
    'SyncCLI',
    
    # Existing components (backward compatibility)
    'DeltaSyncConfig',
    'load_delta_sync_config', 
    'MergeOrchestrator'
]
