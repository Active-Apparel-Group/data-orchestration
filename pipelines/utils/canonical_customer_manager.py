"""
Canonical Customer Manager
Purpose: Universal customer name standardization for all data pipelines
Location: utils/canonical_customer_manager.py

Integrates with existing pipelines/utils/canonical_customers.yaml configuration.
Provides standardized customer name mapping across all source systems.
"""
import yaml
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging

class CanonicalCustomerManager:
    """Universal customer name manager using canonical_customers.yaml"""
    
    def __init__(self, config_path: str = None):
        """Initialize with canonical customer configuration"""
        self.logger = logging.getLogger(__name__)
        
        # Default to pipelines/utils/canonical_customers.yaml
        if config_path is None:
            config_path = Path(__file__).parent / "canonical_customers.yaml"
        
        self.config_path = Path(config_path)
        self._load_canonical_config()
        
    def _load_canonical_config(self) -> None:
        """Load canonical customer configuration from YAML"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            
            self.customers = self.config.get('customers', [])
            self._build_lookup_maps()
            
            self.logger.info(f"Loaded {len(self.customers)} canonical customers from {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to load canonical customers config: {e}")
            raise
    
    def _build_lookup_maps(self) -> None:
        """Build efficient lookup maps for customer resolution"""
        # Alias → Canonical mapping
        self.alias_to_canonical = {}
        
        # Source system → Canonical mapping
        self.source_to_canonical = {
            'master_order_list': {},
            'packed_products': {},
            'shipped': {},
            'mon_customer_ms': {}
        }
        
        # Process each customer configuration
        for customer in self.customers:
            canonical = customer['canonical']
            
            # Add aliases
            for alias in customer.get('aliases', []):
                self.alias_to_canonical[alias.upper()] = canonical
            
            # Add source system mappings
            for source_system in self.source_to_canonical.keys():
                source_name = customer.get(source_system)
                if source_name:
                    # Handle both string and list values
                    if isinstance(source_name, list):
                        for name in source_name:
                            if name and name.strip():  # Skip empty strings
                                self.source_to_canonical[source_system][name.upper()] = canonical
                    elif isinstance(source_name, str) and source_name.strip():
                        self.source_to_canonical[source_system][source_name.upper()] = canonical
    
    def get_canonical_customer(self, customer_name: str, source_system: str = 'master_order_list') -> str:
        """
        Get canonical customer name from any source system name
        
        Args:
            customer_name: Input customer name
            source_system: Source system ('master_order_list', 'packed_products', 'shipped', 'mon_customer_ms')
            
        Returns:
            Canonical customer name
        """
        if not customer_name or not customer_name.strip():
            return customer_name
            
        customer_upper = customer_name.upper().strip()
        
        # 1. Check if already canonical
        canonical_names = {c['canonical'].upper(): c['canonical'] for c in self.customers}
        if customer_upper in canonical_names:
            return canonical_names[customer_upper]
        
        # 2. Check source system mapping (exact match)
        if source_system in self.source_to_canonical:
            canonical = self.source_to_canonical[source_system].get(customer_upper)
            if canonical:
                self.logger.debug(f"Customer mapping ({source_system}): '{customer_name}' → '{canonical}'")
                return canonical
        
        # 3. Check aliases (exact match)
        canonical = self.alias_to_canonical.get(customer_upper)
        if canonical:
            self.logger.debug(f"Customer alias mapping: '{customer_name}' → '{canonical}'")
            return canonical
        
        # 4. GATEKEEPER ENHANCEMENT: Try fuzzy matching with underscore/space normalization
        normalized_variants = [
            customer_upper.replace('_', ' '),  # BOGGI_MILANO → BOGGI MILANO
            customer_upper.replace(' ', '_'),  # BOGGI MILANO → BOGGI_MILANO
            customer_upper.replace('_', ''),   # BOGGI_MILANO → BOGGIMILANO
            customer_upper.replace(' ', ''),   # BOGGI MILANO → BOGGIMILANO
        ]
        
        for variant in normalized_variants:
            # Check source system mapping with variant
            if source_system in self.source_to_canonical:
                canonical = self.source_to_canonical[source_system].get(variant)
                if canonical:
                    self.logger.info(f"Customer fuzzy mapping ({source_system}): '{customer_name}' → '{canonical}' (via '{variant}')")
                    return canonical
            
            # Check aliases with variant
            canonical = self.alias_to_canonical.get(variant)
            if canonical:
                self.logger.info(f"Customer fuzzy alias mapping: '{customer_name}' → '{canonical}' (via '{variant}')")
                return canonical
        
        # 5. Return original if no mapping found
        self.logger.warning(f"No canonical mapping found for customer: '{customer_name}' (source: {source_system})")
        return customer_name
    
    def validate_customer(self, customer_name: str, source_system: str = 'master_order_list') -> bool:
        """
        Validate if customer has canonical mapping
        
        Args:
            customer_name: Customer name to validate
            source_system: Source system context
            
        Returns:
            True if customer has canonical mapping, False otherwise
        """
        canonical = self.get_canonical_customer(customer_name, source_system)
        return canonical != customer_name or self._is_canonical(customer_name)
    
    def _is_canonical(self, customer_name: str) -> bool:
        """Check if customer name is already canonical"""
        canonical_names = {c['canonical'].upper() for c in self.customers}
        return customer_name.upper() in canonical_names
    
    def get_approved_customers(self) -> List[str]:
        """Get list of approved canonical customers only"""
        return [c['canonical'] for c in self.customers if c.get('status') == 'approved']
    
    def get_customer_status(self, canonical_name: str) -> Optional[str]:
        """Get approval status for canonical customer"""
        for customer in self.customers:
            if customer['canonical'].upper() == canonical_name.upper():
                return customer.get('status')
        return None
    
    def get_customer_config(self, canonical_name: str) -> Optional[Dict[str, Any]]:
        """Get full configuration for canonical customer"""
        for customer in self.customers:
            if customer['canonical'].upper() == canonical_name.upper():
                return customer
        return None
    
    def list_unmapped_customers(self, source_customers: List[str], source_system: str = 'master_order_list') -> List[str]:
        """
        Identify customers that don't have canonical mappings
        
        Args:
            source_customers: List of customer names from source system
            source_system: Source system context
            
        Returns:
            List of customers without canonical mappings
        """
        unmapped = []
        for customer in source_customers:
            if not self.validate_customer(customer, source_system):
                unmapped.append(customer)
        return unmapped
    
    def generate_mapping_stats(self) -> Dict[str, Any]:
        """Generate statistics about canonical customer mappings"""
        approved_count = len(self.get_approved_customers())
        total_aliases = sum(len(c.get('aliases', [])) for c in self.customers)
        
        # Count source system mappings
        source_mapping_counts = {}
        for source_system in self.source_to_canonical.keys():
            source_mapping_counts[source_system] = len(self.source_to_canonical[source_system])
        
        return {
            'total_canonical_customers': len(self.customers),
            'approved_customers': approved_count,
            'review_customers': len(self.customers) - approved_count,
            'total_aliases': total_aliases,
            'source_systems': list(self.source_to_canonical.keys()),
            'source_mapping_counts': source_mapping_counts,
            'config_file': str(self.config_path)
        }
    
    def get_source_customer_name(self, canonical_name: str, source_system: str = 'master_order_list') -> Optional[str]:
        """
        Get the source system customer name for a canonical customer
        
        Args:
            canonical_name: Canonical customer name
            source_system: Source system to get name for
            
        Returns:
            Source system customer name or None if not found
        """
        customer_config = self.get_customer_config(canonical_name)
        if not customer_config:
            return None
            
        source_name = customer_config.get(source_system)
        
        # Handle list values - return first entry
        if isinstance(source_name, list) and source_name:
            return source_name[0]
        elif isinstance(source_name, str) and source_name.strip():
            return source_name
            
        return None


# Factory function for easy usage
def get_canonical_customer_manager(config_path: str = None) -> CanonicalCustomerManager:
    """Factory function to create CanonicalCustomerManager instance"""
    return CanonicalCustomerManager(config_path)


# Convenience functions for direct usage
def canonicalize_customer(customer_name: str, source_system: str = 'master_order_list', 
                         config_path: str = None) -> str:
    """
    Quick function to get canonical customer name
    
    Args:
        customer_name: Input customer name
        source_system: Source system context
        config_path: Optional path to canonical_customers.yaml
        
    Returns:
        Canonical customer name
    """
    manager = get_canonical_customer_manager(config_path)
    return manager.get_canonical_customer(customer_name, source_system)


def validate_canonical_customer(customer_name: str, source_system: str = 'master_order_list',
                               config_path: str = None) -> bool:
    """
    Quick function to validate customer has canonical mapping
    
    Args:
        customer_name: Customer name to validate
        source_system: Source system context
        config_path: Optional path to canonical_customers.yaml
        
    Returns:
        True if customer has canonical mapping
    """
    manager = get_canonical_customer_manager(config_path)
    return manager.validate_customer(customer_name, source_system)


def get_canonical_stats(config_path: str = None) -> Dict[str, Any]:
    """
    Quick function to get canonical customer statistics
    
    Args:
        config_path: Optional path to canonical_customers.yaml
        
    Returns:
        Dictionary with mapping statistics
    """
    manager = get_canonical_customer_manager(config_path)
    return manager.generate_mapping_stats()
