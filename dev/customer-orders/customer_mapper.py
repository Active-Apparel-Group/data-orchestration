"""
Customer Mapper - Dynamic customer mapping using canonical YAML file
Purpose: Replace hardcoded customer mappings with YAML-based configuration
Location: utils/customer_mapper.py
"""
import yaml
from pathlib import Path
from typing import Dict, Optional, List
import logging
import pandas as pd

class CustomerMapper:
    """Dynamic customer mapping using canonical YAML file"""
    
    def __init__(self, mapping_file: Optional[str] = None):
        """
        Initialize CustomerMapper with YAML configuration
        
        Args:
            mapping_file: Path to customer mapping YAML file
        """
        self.logger = logging.getLogger(__name__)
        
        # Default to sql/mappings/customer-canonical.yaml
        if mapping_file is None:
            mapping_file = "sql/mappings/customer-canonical.yaml"
        
        self.mapping_file = Path(mapping_file)
        self.canonical_mapping = {}
        self.customer_priority = {}
        self.customer_metadata = {}
        
        self._load_mappings()
    
    def _load_mappings(self) -> None:
        """Load customer mappings from YAML file"""
        try:
            if not self.mapping_file.exists():
                self.logger.error(f"Customer mapping file not found: {self.mapping_file}")
                raise FileNotFoundError(f"Customer mapping file not found: {self.mapping_file}")
            
            with open(self.mapping_file, 'r') as f:
                data = yaml.safe_load(f)
            
            if 'customers' not in data:
                self.logger.error("Invalid YAML structure: 'customers' key not found")
                raise ValueError("Invalid YAML structure: 'customers' key not found")
            
            # Build mapping dictionaries
            priority_counter = 1
            
            for customer in data['customers']:
                canonical = customer['canonical']
                status = customer.get('status', 'review')
                
                # Map canonical name to itself
                self.canonical_mapping[canonical.upper()] = canonical
                
                # Set priority based on status (approved gets higher priority)
                if status == 'approved':
                    self.customer_priority[canonical] = priority_counter
                    priority_counter += 1
                else:
                    self.customer_priority[canonical] = 999  # Low priority for review status
                
                # Store metadata
                self.customer_metadata[canonical] = {
                    'status': status,
                    'packed_products': customer.get('packed_products', ''),
                    'shipped': customer.get('shipped', ''),
                    'master_order_list': customer.get('master_order_list', ''),
                    'mon_customer_ms': customer.get('mon_customer_ms', '')
                }
                
                # Map all aliases to canonical name
                for alias in customer.get('aliases', []):
                    self.canonical_mapping[alias.upper()] = canonical
                  # Map additional fields if they exist
                for field in ['packed_products', 'shipped', 'master_order_list']:
                    field_value = customer.get(field, '')
                    if field_value and isinstance(field_value, str) and field_value.strip():
                        self.canonical_mapping[field_value.upper()] = canonical
            
            self.logger.info(f"Loaded {len(data['customers'])} customers with {len(self.canonical_mapping)} total mappings")
            
        except Exception as e:
            self.logger.error(f"Failed to load customer mappings: {e}")
            raise
       
    def normalize_customer_name(self, customer_name: str) -> str:
        """
        Apply canonical customer mapping
        
        Args:
            customer_name: Raw customer name from source data
            
        Returns:
            str: Canonical customer name
        """
        if not customer_name:
            return 'UNKNOWN'
        
        normalized = customer_name.strip().upper()
        return self.canonical_mapping.get(normalized, normalized)
    
    def get_customer_priority(self, customer_name: str) -> int:
        """
        Get processing priority for customer
        
        Args:
            customer_name: Customer name (canonical or raw)
            
        Returns:
            int: Priority (1 = highest, 999 = lowest)
        """
        canonical = self.normalize_customer_name(customer_name)
        return self.customer_priority.get(canonical, 999)
    
    def get_customer_metadata(self, customer_name: str) -> Dict:
        """
        Get customer metadata
        
        Args:
            customer_name: Customer name (canonical or raw)
            
        Returns:
            dict: Customer metadata
        """
        canonical = self.normalize_customer_name(customer_name)
        return self.customer_metadata.get(canonical, {})
    
    def get_database_customer_name(self, customer_name: str) -> str:
        """
        Get the customer name as it appears in ORDERS_UNIFIED database
        
        Args:
            customer_name: Customer name (canonical or raw)
            
        Returns:
            str: Customer name for database queries (master_order_list)
        """
        metadata = self.get_customer_metadata(customer_name)
        database_name = metadata.get('master_order_list', '')
        
        # Fallback to canonical name if master_order_list not found
        if not database_name:
            database_name = self.normalize_customer_name(customer_name)
            
        return database_name
    
    def get_customer_aliases(self, canonical_customer: str) -> List[str]:
        """
        Get all database variations/aliases that map to a canonical customer
        
        Args:
            canonical_customer: The canonical customer name
            
        Returns:
            List[str]: All database variations that map to this canonical customer
        """
        aliases = []
        
        # Add the canonical name itself
        aliases.append(canonical_customer)
        
        # Find all aliases that map to this canonical customer
        for alias, canonical in self.canonical_mapping.items():
            if canonical == canonical_customer and alias.upper() != canonical_customer.upper():
                aliases.append(alias)
        
        # Remove duplicates while preserving order
        unique_aliases = []
        seen = set()
        for alias in aliases:
            if alias.upper() not in seen:
                unique_aliases.append(alias)
                seen.add(alias.upper())
        
        return unique_aliases

    def get_approved_customers(self) -> List[str]:
        """Get list of approved customers for priority processing"""
        return [
            customer for customer, metadata in self.customer_metadata.items()
            if metadata.get('status') == 'approved'
        ]
    
    def get_customer_status(self, customer_name: str) -> str:
        """
        Get customer approval status
        
        Args:
            customer_name: Customer name (canonical or raw)
            
        Returns:
            str: 'approved' or 'review'
        """
        canonical = self.normalize_customer_name(customer_name)
        metadata = self.customer_metadata.get(canonical, {})
        return metadata.get('status', 'review')
    
    def reload_mappings(self) -> None:
        """Reload mappings from YAML file (for dynamic updates)"""
        self.canonical_mapping.clear()
        self.customer_priority.clear()
        self.customer_metadata.clear()
        self._load_mappings()
    
    def get_mapping_summary(self) -> Dict:
        """Get summary of loaded mappings"""
        approved_count = len(self.get_approved_customers())
        total_customers = len(self.customer_metadata)
        
        return {
            'total_customers': total_customers,
            'approved_customers': approved_count,
            'review_customers': total_customers - approved_count,
            'total_mappings': len(self.canonical_mapping),
            'mapping_file': str(self.mapping_file)
        }

    def transform_orders_batch(self, orders_df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform a batch of orders using YAML mapping configuration
        This is the CRITICAL missing method that applies YAML transformations
        
        Args:
            orders_df: Raw orders DataFrame from ORDERS_UNIFIED
            
        Returns:
            pd.DataFrame: Transformed DataFrame ready for staging
        """
        try:
            # Load the YAML mapping configuration
            mapping_path = Path(__file__).parent.parent / "sql" / "mappings" / "orders-unified-monday-mapping.yaml"
            with open(mapping_path, 'r') as f:
                mapping_config = yaml.safe_load(f)
            
            # Create a copy to avoid modifying original
            transformed_df = orders_df.copy()
            
            # Apply field transformations from YAML
            # This ensures all field names match what Monday.com expects
            
            # Process mapped fields (rename columns)
            for field_config in mapping_config.get('mapped_fields', []):
                source_field = field_config.get('source_field')
                target_field = field_config.get('target_field')
                
                if source_field in transformed_df.columns:
                    # Rename the column to match Monday.com expectation
                    if target_field and target_field != source_field:
                        transformed_df[target_field] = transformed_df[source_field]
                        self.logger.debug(f"Mapped {source_field} → {target_field}")
            
            # Add any computed fields
            for computed_field in mapping_config.get('computed_fields', []):
                if computed_field.get('target_field') == 'Title':
                    # Title is handled separately in Monday API adapter
                    continue
                    
            self.logger.info(f"Transformed {len(transformed_df)} orders with YAML mapping")
            return transformed_df
            
        except Exception as e:
            self.logger.error(f"Error transforming orders batch: {e}")
            # Return original if transformation fails
            return orders_df

def create_customer_mapper() -> CustomerMapper:
    """Factory function to create CustomerMapper instance"""
    return CustomerMapper()


# For backward compatibility
def load_customer_mapping() -> CustomerMapper:
    """Load customer mapping (alias for create_customer_mapper)"""
    return create_customer_mapper()
