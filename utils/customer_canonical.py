"""
Customer Canonical Mapping Utility
Purpose: Universal customer name standardization for all workflows
Location: utils/customer_canonical.py

This utility provides canonical customer name mapping to ensure consistency
across all data sources and workflows in the data orchestration project.
"""
from typing import Dict, Optional
import logging

class CustomerCanonicalMapper:
    """Universal customer name mapper for canonical transformation"""
    
    def __init__(self):
        """Initialize with canonical customer mappings"""
        self.logger = logging.getLogger(__name__)
        
        # Canonical customer mappings - upstream transformation
        # Maps common names to their canonical form in ORDERS_UNIFIED
        self._canonical_mappings = {
            'GREYSON': 'GREYSON CLOTHIERS',
            'GREYSON CLOTHIERS': 'GREYSON CLOTHIERS',  # Already canonical
            # Add more mappings as needed
            # 'ACME': 'ACME CORPORATION',
            # 'TEST': 'TEST CUSTOMER',
        }
        
        # Reverse lookup for validation
        self._reverse_mappings = {v: k for k, v in self._canonical_mappings.items()}
        
    def get_canonical_name(self, customer_name: str) -> str:
        """
        Get canonical customer name for database queries
        
        Args:
            customer_name: Input customer name (e.g., 'GREYSON')
            
        Returns:
            Canonical customer name for ORDERS_UNIFIED (e.g., 'GREYSON CLOTHIERS')
        """
        if not customer_name:
            return customer_name
            
        canonical = self._canonical_mappings.get(customer_name.upper(), customer_name)
        
        if canonical != customer_name:
            self.logger.info(f"Customer mapping: '{customer_name}' → '{canonical}'")
            
        return canonical
    
    def get_display_name(self, canonical_name: str) -> str:
        """
        Get display/short name from canonical name
        
        Args:
            canonical_name: Canonical database name (e.g., 'GREYSON CLOTHIERS')
            
        Returns:
            Display name (e.g., 'GREYSON')
        """
        if not canonical_name:
            return canonical_name
            
        # Look up the short name that maps to this canonical name
        for short_name, canonical in self._canonical_mappings.items():
            if canonical == canonical_name:
                return short_name
                
        # If no mapping found, return original
        return canonical_name
    
    def validate_customer(self, customer_name: str) -> bool:
        """
        Validate if customer name exists in mappings
        
        Args:
            customer_name: Customer name to validate
            
        Returns:
            True if customer is recognized, False otherwise
        """
        if not customer_name:
            return False
            
        upper_name = customer_name.upper()
        
        # Check if it's a known input name or canonical name
        return (upper_name in self._canonical_mappings or 
                upper_name in self._reverse_mappings)
    
    def list_supported_customers(self) -> Dict[str, str]:
        """
        Get all supported customer mappings
        
        Returns:
            Dictionary of input_name -> canonical_name mappings
        """
        return self._canonical_mappings.copy()
    
    def add_mapping(self, input_name: str, canonical_name: str) -> None:
        """
        Add new customer mapping (for dynamic configuration)
        
        Args:
            input_name: Input customer name
            canonical_name: Canonical database name
        """
        self._canonical_mappings[input_name.upper()] = canonical_name
        self.logger.info(f"Added customer mapping: '{input_name}' → '{canonical_name}'")


# Factory function for easy usage
def get_customer_mapper() -> CustomerCanonicalMapper:
    """Factory function to create customer mapper instance"""
    return CustomerCanonicalMapper()


# Convenience functions for direct usage
def canonicalize_customer(customer_name: str) -> str:
    """
    Quick function to get canonical customer name
    
    Args:
        customer_name: Input customer name
        
    Returns:
        Canonical customer name for database queries
    """
    mapper = get_customer_mapper()
    return mapper.get_canonical_name(customer_name)


def display_customer(canonical_name: str) -> str:
    """
    Quick function to get display customer name
    
    Args:
        canonical_name: Canonical database name
        
    Returns:
        Display/short customer name
    """
    mapper = get_customer_mapper()
    return mapper.get_display_name(canonical_name)
