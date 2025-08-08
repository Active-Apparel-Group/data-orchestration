""""
Pipelines utilities package
Modern Python package structure for data orchestration utilities

This package provides clean imports for database, logging, and configuration utilities
following the consolidated structure from structure-consolidation-reference.md
"""

from . import db
from . import logger  
from . import config
from . import monday_config

# Export commonly used functions for convenient imports
# Usage: from pipelines.utils import get_connection, get_logger, MondayConfig
try:
    from .db import get_connection, load_config
    from .logger import get_logger
    from .monday_config import MondayConfig, load_monday_config, get_board_settings
except ImportError:
    # Graceful fallback if underlying utils aren't available
    pass

__all__ = ['db', 'logger', 'config', 'monday_config', 'get_connection', 'get_logger', 'load_config', 'MondayConfig', 'load_monday_config', 'get_board_settings']
