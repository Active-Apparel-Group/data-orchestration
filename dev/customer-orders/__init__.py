"""
Customer Orders Package - UUID & Hash-Based Delta Synchronization
Enterprise-grade Monday.com integration with staging-based processing

Components:
- CustomerMapper: Dynamic YAML-based customer mapping
- MondayIntegrationClient: Robust Monday.com API client with retry logic
- CustomerBatchProcessor: Enterprise batch processing orchestrator
- CustomerBatcher: Customer-based batching logic
- ChangeDetector: Hash-based change detection
- StagingProcessor: Staging workflow management
- UUIDManager: UUID system management
- MainCustomerOrders: Main orchestrator (entry point)
"""

from .customer_mapper import CustomerMapper, create_customer_mapper
from .integration_monday import MondayIntegrationClient, create_monday_client
from .customer_batch_processor import CustomerBatchProcessor
from .change_detector import ChangeDetector
from .staging_processor import StagingProcessor

__all__ = [
    'CustomerMapper',
    'create_customer_mapper',
    'MondayIntegrationClient', 
    'create_monday_client',
    'CustomerBatchProcessor',
    'CustomerBatcher',
    'ChangeDetector',
    'StagingProcessor',
    'UUIDManager'
]

__version__ = '3.0.0'
__description__ = 'Customer Orders - UUID & Hash-Based Delta Synchronization'
