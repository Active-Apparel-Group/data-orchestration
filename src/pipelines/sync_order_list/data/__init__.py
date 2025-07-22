"""
Data Management Module  
Handles DELTA table operations and batch processing for sync_order_list pipeline
"""

# This module will contain:
# - delta_reader.py: Read ORDER_LIST_DELTA batches
# - lines_delta_reader.py: Read ORDER_LIST_LINES_DELTA batches  
# - state_updater.py: Update sync states and Monday IDs
# - batch_processor.py: Coordinate batch operations

__all__ = []
