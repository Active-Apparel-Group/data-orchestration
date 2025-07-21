"""
Canonical Customer Manager
=========================
Purpose: Canonical customer name management using YAML configuration
Location: src/pipelines/shared/customer/canonical_manager.py
Created: 2025-07-19 (Milestone 2: Business Key Implementation)
Moved: 2025-07-20 (Architecture refactor: separate functional logic from utils)

This module manages canonical customer names using the existing canonical_customers.yaml 
configuration file. It provides customer-specific configuration for unique key generation 
and duplicate resolution.

Architecture Integration:
- Uses existing pipelines/utils/canonical_customers.yaml
- Provides customer config for business key generation  
- Supports alias-based customer name resolution
- Handles missing customer configurations gracefully

NOTE: This utility is designed to be reusable across different order-related tables
and will be extended for shipment and inventory customer resolution in future milestones.
"""
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Set
import logging

class CanonicalCustomerManager:
    """
    Manages customer names to canonical form and provides customer-specific configuration
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize customer resolver with YAML configuration
        
        Args:
            config_path: Path to canonical_customers.yaml (uses default if None)
        """
        self.logger = logging.getLogger(__name__)
        
        # Use shared canonical_customers.yaml location
        if config_path is None:
            # Default to shared location (same directory as this file)
            config_path = Path(__file__).parent / "canonical_customers.yaml"
        
        self.config_path = Path(config_path)
        self.customer_config = self._load_yaml_config()
        self.alias_lookup = self._build_alias_lookup()
        
        self.logger.info(f"Loaded {len(self.customer_config.get('customers', []))} customer configurations")
        self.logger.info(f"Built alias lookup with {len(self.alias_lookup)} mappings")
    
    def _find_repo_root(self) -> Path:
        """Find repository root directory"""
        current = Path(__file__).parent.parent.parent.parent
        while current != current.parent:
            if (current / "pipelines" / "utils").exists():
                return current
            current = current.parent
        raise FileNotFoundError("Could not find repository root")
    
    def _load_yaml_config(self) -> Dict:
        """Load canonical customers YAML configuration"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if not config or 'customers' not in config:
                raise ValueError("Invalid YAML structure: missing 'customers' section")
            
            return config
            
        except FileNotFoundError:
            self.logger.error(f"Customer config file not found: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            self.logger.error(f"YAML parsing error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error loading customer config: {e}")
            raise
    
    def _build_alias_lookup(self) -> Dict[str, str]:
        """
        Build alias lookup dictionary for fast customer resolution
        
        Returns:
            Dict mapping alias names to canonical names
        """
        alias_lookup = {}
        
        for customer in self.customer_config.get('customers', []):
            canonical = customer.get('canonical')
            if not canonical:
                continue
            
            # Add canonical name as self-reference
            alias_lookup[canonical] = canonical
            
            # Add aliases if they exist
            aliases = customer.get('aliases', [])
            for alias in aliases:
                if alias and alias != canonical:
                    alias_lookup[alias] = canonical
            
            # Add case-insensitive mappings for robustness
            alias_lookup[canonical.upper()] = canonical
            for alias in aliases:
                if alias:
                    alias_lookup[alias.upper()] = canonical
        
        return alias_lookup
    
    def resolve_canonical_customer(self, source_name: str) -> str:
        """
        Resolve source customer name to canonical name
        
        Args:
            source_name: Customer name from source data
            
        Returns:
            Canonical customer name or original name if not found
        """
        if not source_name:
            return source_name
        
        # Try exact match first
        if source_name in self.alias_lookup:
            return self.alias_lookup[source_name]
        
        # Try case-insensitive match
        if source_name.upper() in self.alias_lookup:
            return self.alias_lookup[source_name.upper()]
        
        # Return original name if no mapping found
        self.logger.warning(f"No canonical mapping found for customer: {source_name}")
        return source_name
    
    def get_customer_config(self, canonical_name: str) -> Dict:
        """
        Get customer-specific configuration for business key generation
        
        Args:
            canonical_name: Canonical customer name
            
        Returns:
            Customer configuration dict or default config if not found
        """
        for customer in self.customer_config.get('customers', []):
            if customer.get('canonical') == canonical_name:
                return customer
        
        # Return default configuration for unknown customers
        self.logger.warning(f"No specific config found for customer: {canonical_name}, using default")
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """
        Get default customer configuration for unknown customers
        
        Returns:
            Default configuration with standard unique keys
        """
        return {
            'canonical': 'UNKNOWN',
            'status': 'review',
            'order_key_config': {
                'unique_keys': [
                    'AAG ORDER NUMBER',
                    'CUSTOMER STYLE'  # Minimal set for unknown customers
                ],
                'extra_checks': [
                    'PO NUMBER',
                    'ORDER TYPE'
                ]
            }
        }
    
    def get_unique_keys(self, canonical_name: str) -> List[str]:
        """
        Get unique keys for business key generation for a specific customer
        
        Args:
            canonical_name: Canonical customer name
            
        Returns:
            List of column names to use for unique key generation
        """
        customer_config = self.get_customer_config(canonical_name)
        order_config = customer_config.get('order_key_config', {})
        return order_config.get('unique_keys', ['AAG ORDER NUMBER'])
    
    def get_extra_check_columns(self, canonical_name: str) -> List[str]:
        """
        Get extra check columns for duplicate resolution
        
        Args:
            canonical_name: Canonical customer name
            
        Returns:
            List of column names for additional duplicate resolution
        """
        customer_config = self.get_customer_config(canonical_name)
        order_config = customer_config.get('order_key_config', {})
        return order_config.get('extra_checks', [])
    
    def get_customer_status(self, canonical_name: str) -> str:
        """
        Get customer approval status
        
        Args:
            canonical_name: Canonical customer name
            
        Returns:
            Customer status ('approved', 'review', etc.)
        """
        customer_config = self.get_customer_config(canonical_name)
        return customer_config.get('status', 'review')
    
    def list_all_canonical_customers(self) -> List[str]:
        """
        Get list of all canonical customer names
        
        Returns:
            List of canonical customer names
        """
        return [
            customer.get('canonical') 
            for customer in self.customer_config.get('customers', [])
            if customer.get('canonical')
        ]
    
    def get_customer_stats(self) -> Dict[str, int]:
        """
        Get statistics about customer configuration
        
        Returns:
            Dict with customer counts by status and total aliases
        """
        customers = self.customer_config.get('customers', [])
        stats = {
            'total_customers': len(customers),
            'approved_customers': len([c for c in customers if c.get('status') == 'approved']),
            'review_customers': len([c for c in customers if c.get('status') == 'review']),
            'total_aliases': len(self.alias_lookup)
        }
        return stats

# Factory function for easy usage
def create_canonical_customer_manager(config_path: Optional[str] = None) -> CanonicalCustomerManager:
    """
    Factory function to create CanonicalCustomerManager instance
    
    Args:
        config_path: Optional path to canonical_customers.yaml
        
    Returns:
        Configured CanonicalCustomerManager instance
    """
    return CanonicalCustomerManager(config_path)

# Example usage and testing functions
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Test customer management
    manager = create_canonical_customer_manager()
    
    # Test cases
    test_cases = [
        "GREYSON",
        "GREYSON CLOTHIERS", 
        "AJE ATHLETICA (AU)",
        "TRACKSMITH",
        "UNKNOWN CUSTOMER"
    ]
    
    print("Customer Management Test:")
    print("-" * 40)
    
    for source_name in test_cases:
        canonical = manager.resolve_canonical_customer(source_name)
        unique_keys = manager.get_unique_keys(canonical)
        status = manager.get_customer_status(canonical)
        
        print(f"Source: {source_name}")
        print(f"  -> Canonical: {canonical}")
        print(f"  -> Status: {status}")
        print(f"  -> Unique Keys: {unique_keys}")
        print()
    
    # Show statistics
    stats = manager.get_customer_stats()
    print("Customer Configuration Statistics:")
    print("-" * 40)
    for key, value in stats.items():
        print(f"{key}: {value}")


# Convenience functions for backward compatibility with order_key_generator.py
def canonicalize_customer(customer_name: str, source_system: str = 'master_order_list') -> str:
    """
    Convenience function to get canonical customer name
    
    Args:
        customer_name: Input customer name
        source_system: Source system context (not used in this implementation)
        
    Returns:
        Canonical customer name
    """
    manager = create_canonical_customer_manager()
    return manager.resolve_canonical_customer(customer_name)


def get_canonical_stats() -> Dict[str, int]:
    """
    Convenience function to get customer statistics
    
    Returns:
        Dictionary with customer statistics
    """
    manager = create_canonical_customer_manager()
    return manager.get_customer_stats()
