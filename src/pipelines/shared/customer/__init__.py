# Customer-related business logic modules
# Contains canonical customer management and order key generation

from .canonical_manager import CanonicalCustomerManager
from .order_key_generator import OrderKeyGenerator

__all__ = ['CanonicalCustomerManager', 'OrderKeyGenerator']
