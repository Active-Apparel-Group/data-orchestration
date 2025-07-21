"""
Order Key Generator Module
=========================
Purpose: Generate Excel-compatible business keys for ORDER_LIST delta sync
Location: src/pipelines/shared/customer/order_key_generator.py
Created: 2025-07-19 (Milestone 2: Business Key Implementation)
Moved: 2025-07-20 (Architecture refactor: separate functional logic from utils)

This module generates order business keys for ORDER_LIST records using customer-specific
configuration and Excel-compatible logic. It replaces UUID-based matching with
composite keys that work with Excel data sources.

Business Key Strategy:
- NEW detection: Check if AAG ORDER NUMBER exists in production ORDER_LIST
- Customer-specific unique keys from canonical_customers.yaml
- Composite key generation for duplicate resolution
- Hash-based change detection for existing records

This utility is designed to be reusable across different order-related tables
and will be extended for shipment and inventory key generation in future milestones.
"""
import hashlib
import pandas as pd
from typing import Dict, List, Optional, Tuple, Set
import logging
from pathlib import Path
import sys

# Import canonical customer manager with new location
from .canonical_manager import canonicalize_customer, get_canonical_stats
import yaml

class OrderKeyGenerator:
    """
    Generates order business keys for ORDER_LIST records using customer-specific logic
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize order key generator
        
        Args:
            config_path: Path to canonical_customers.yaml (uses default if None)
        """
        self.logger = logging.getLogger(__name__)
        
        # Set up configuration path - use shared location
        if config_path is None:
            # Default to shared location (same directory as canonical_manager)
            config_path = Path(__file__).parent / "canonical_customers.yaml"
        
        self.config_path = Path(config_path)
        
        # Load customer configuration
        try:
            with open(self.config_path, 'r') as f:
                self.customer_config = yaml.safe_load(f)
                self.logger.info(f"Loaded customer configuration from {self.config_path}")
        except Exception as e:
            self.logger.error(f"Failed to load customer config: {e}")
            raise
        
        # Build customer lookup for performance
        self._build_customer_lookup()
        
        # Track generated keys for duplicate detection
        self.generated_keys = set()
        self.duplicate_count = 0
        
        self.logger.info("Order key generator initialized")
    
    def _build_customer_lookup(self):
        """Build customer lookup dictionary for fast access"""
        self.customer_lookup = {}
        
        if 'customers' in self.customer_config:
            for customer in self.customer_config['customers']:
                canonical = customer.get('canonical', '')
                self.customer_lookup[canonical] = customer
                
                # Add aliases for lookup
                for alias in customer.get('aliases', []):
                    self.customer_lookup[alias] = customer
        
        self.logger.info(f"Built customer lookup with {len(self.customer_lookup)} entries")
    
    def resolve_canonical_customer(self, customer_name: str) -> str:
        """
        Resolve customer name to canonical form using existing utility
        
        Args:
            customer_name: Customer name from source data
            
        Returns:
            Canonical customer name
        """
        try:
            # Use canonical customer manager from new shared location
            if not hasattr(self, '_canonical_manager'):
                self._canonical_manager = True  # Flag to avoid repeated initialization logs
            
            canonical = canonicalize_customer(customer_name, 'master_order_list')
            return canonical
        except Exception as e:
            self.logger.warning(f"Failed to canonicalize customer '{customer_name}': {e}")
            return customer_name
    
    def get_customer_config(self, canonical_customer: str) -> Dict:
        """
        Get customer configuration for canonical customer name
        
        Args:
            canonical_customer: Canonical customer name
            
        Returns:
            Customer configuration dictionary
        """
        return self.customer_lookup.get(canonical_customer, {})
    
    def get_unique_keys(self, canonical_customer: str) -> List[str]:
        """
        Get unique key fields for customer
        
        Args:
            canonical_customer: Canonical customer name
            
        Returns:
            List of unique key field names
        """
        customer_config = self.get_customer_config(canonical_customer)
        order_key_config = customer_config.get('order_key_config', {})
        return order_key_config.get('unique_keys', ['AAG ORDER NUMBER', 'PLANNED DELIVERY METHOD', 'CUSTOMER STYLE'])
    
    def get_extra_check_columns(self, canonical_customer: str) -> List[str]:
        """
        Get extra check columns for duplicate resolution
        
        Args:
            canonical_customer: Canonical customer name
            
        Returns:
            List of extra check column names
        """
        customer_config = self.get_customer_config(canonical_customer)
        order_key_config = customer_config.get('order_key_config', {})
        return order_key_config.get('extra_checks', ['PO NUMBER', 'ORDER TYPE'])
    
    def generate_order_key(self, row_data: Dict, customer_name: str) -> str:
        """
        Generate order business key for a single ORDER_LIST record
        
        Args:
            row_data: Dictionary containing ORDER_LIST row data
            customer_name: Customer name from source data
            
        Returns:
            Order business key string for the record
        """
        # Resolve to canonical customer name
        canonical_customer = self.resolve_canonical_customer(customer_name)
        
        # Get customer-specific unique keys
        unique_keys = self.get_unique_keys(canonical_customer)
        
        # Build key components
        key_components = []
        
        # Always include canonical customer as first component
        key_components.append(canonical_customer)
        
        # Add customer-specific unique key values
        for key_column in unique_keys:
            value = str(row_data.get(key_column, '')).strip()
            if value:
                key_components.append(value)
        
        # Create composite order business key
        order_key = '|'.join(key_components)
        
        # Handle potential duplicates
        if order_key in self.generated_keys:
            order_key = self._resolve_duplicate_key(order_key, row_data, canonical_customer)
        
        self.generated_keys.add(order_key)
        return order_key
    
    def _resolve_duplicate_key(self, base_key: str, row_data: Dict, canonical_customer: str) -> str:
        """
        Resolve duplicate order business keys using extra check columns
        
        Args:
            base_key: Original order business key that was duplicated
            row_data: Dictionary containing row data
            canonical_customer: Canonical customer name
            
        Returns:
            Unique order business key with additional components
        """
        self.duplicate_count += 1
        self.logger.warning(f"Duplicate order business key detected: {base_key}")
        
        # Get extra check columns for this customer
        extra_checks = self.get_extra_check_columns(canonical_customer)
        
        # Add extra check values to make key unique
        key_components = [base_key]
        
        for check_column in extra_checks:
            value = str(row_data.get(check_column, '')).strip()
            if value:
                key_components.append(value)
        
        # If still not unique, add a sequence number
        resolved_key = '|'.join(key_components)
        sequence = 1
        
        while resolved_key in self.generated_keys:
            resolved_key = f"{resolved_key}|SEQ_{sequence:03d}"
            sequence += 1
        
        self.logger.info(f"Resolved duplicate key: {base_key} -> {resolved_key}")
        return resolved_key
    
    def generate_row_hash(self, row_data: Dict, hash_columns: List[str]) -> str:
        """
        Generate content hash for change detection
        
        Args:
            row_data: Dictionary containing row data
            hash_columns: List of columns to include in hash
            
        Returns:
            SHA-256 hash of specified columns
        """
        # Extract values for hash columns in consistent order
        hash_values = []
        for col in sorted(hash_columns):  # Sort for consistency
            value = str(row_data.get(col, '')).strip()
            hash_values.append(value)
        
        # Create hash of concatenated values
        content = '|'.join(hash_values)
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def is_new_order(self, aag_order_number: str, existing_orders: Set[str]) -> bool:
        """
        Determine if an order is NEW using AAG ORDER NUMBER
        
        Args:
            aag_order_number: AAG ORDER NUMBER from source data
            existing_orders: Set of existing AAG ORDER NUMBERs from production
            
        Returns:
            True if order is new, False if exists
        """
        if not aag_order_number or not aag_order_number.strip():
            return False
        
        return aag_order_number.strip() not in existing_orders
    
    def process_dataframe(self, df: pd.DataFrame, hash_columns: List[str], 
                         existing_orders: Set[str]) -> pd.DataFrame:
        """
        Process entire DataFrame to add order business keys and sync state
        
        Args:
            df: DataFrame containing ORDER_LIST data
            hash_columns: List of columns to include in content hash
            existing_orders: Set of existing AAG ORDER NUMBERs
            
        Returns:
            DataFrame with added order_business_key, row_hash, and sync_state columns
        """
        self.logger.info(f"Processing {len(df)} records for order key generation")
        
        # Initialize result columns
        order_business_keys = []
        row_hashes = []
        sync_states = []
        
        # Process each row
        for idx, row in df.iterrows():
            try:
                row_dict = row.to_dict()
                
                # Generate order business key
                customer_name = row_dict.get('CUSTOMER', '')
                order_business_key = self.generate_order_key(row_dict, customer_name)
                order_business_keys.append(order_business_key)
                
                # Generate content hash
                row_hash = self.generate_row_hash(row_dict, hash_columns)
                row_hashes.append(row_hash)
                
                # Determine sync state (NEW vs existing)
                aag_order_number = row_dict.get('AAG ORDER NUMBER', '')
                is_new = self.is_new_order(aag_order_number, existing_orders)
                sync_state = 'NEW' if is_new else 'EXISTING'
                sync_states.append(sync_state)
                
            except Exception as e:
                self.logger.error(f"Error processing row {idx}: {e}")
                # Set default values for failed rows
                order_business_keys.append(f"ERROR_{idx}")
                row_hashes.append("")
                sync_states.append("ERROR")
        
        # Add columns to DataFrame
        df_result = df.copy()
        df_result['order_business_key'] = order_business_keys
        df_result['row_hash'] = row_hashes
        df_result['sync_state'] = sync_states
        
        # Log statistics
        self._log_processing_stats(df_result)
        
        return df_result
    
    def _log_processing_stats(self, df: pd.DataFrame):
        """Log processing statistics"""
        total_records = len(df)
        new_records = len(df[df['sync_state'] == 'NEW'])
        existing_records = len(df[df['sync_state'] == 'EXISTING'])
        error_records = len(df[df['sync_state'] == 'ERROR'])
        
        self.logger.info("Order Key Generation Statistics:")
        self.logger.info(f"  Total records: {total_records}")
        self.logger.info(f"  NEW records: {new_records}")
        self.logger.info(f"  EXISTING records: {existing_records}")
        self.logger.info(f"  ERROR records: {error_records}")
        self.logger.info(f"  Duplicate keys resolved: {self.duplicate_count}")
        
        # Customer breakdown
        if 'CUSTOMER' in df.columns:
            customer_stats = df.groupby('CUSTOMER')['sync_state'].value_counts()
            self.logger.info("Customer breakdown:")
            for (customer, state), count in customer_stats.items():
                self.logger.info(f"  {customer} - {state}: {count}")
    
    def validate_order_keys(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Validate generated order business keys for quality and uniqueness
        
        Args:
            df: DataFrame with order_business_key column
            
        Returns:
            Validation results dictionary
        """
        if 'order_business_key' not in df.columns:
            return {'valid': False, 'error': 'No order_business_key column found'}
        
        order_business_keys = df['order_business_key'].tolist()
        
        # Check for duplicates
        unique_keys = set(order_business_keys)
        duplicate_count = len(order_business_keys) - len(unique_keys)
        
        # Check for empty/invalid keys
        empty_keys = sum(1 for key in order_business_keys if not key or key.startswith('ERROR_'))
        
        # Calculate key length statistics
        key_lengths = [len(key) for key in order_business_keys if key and not key.startswith('ERROR_')]
        avg_length = sum(key_lengths) / len(key_lengths) if key_lengths else 0
        
        validation_result = {
            'valid': duplicate_count == 0 and empty_keys == 0,
            'total_records': len(df),
            'unique_keys': len(unique_keys),
            'duplicate_count': duplicate_count,
            'empty_keys': empty_keys,
            'average_key_length': round(avg_length, 2),
            'min_key_length': min(key_lengths) if key_lengths else 0,
            'max_key_length': max(key_lengths) if key_lengths else 0
        }
        
        return validation_result
    
    def get_key_generation_stats(self) -> Dict[str, int]:
        """
        Get statistics about key generation process
        
        Returns:
            Dictionary with generation statistics
        """
        return {
            'total_keys_generated': len(self.generated_keys),
            'duplicate_keys_resolved': self.duplicate_count
        }

# Factory function for easy usage
def create_order_key_generator(config_path: Optional[str] = None) -> OrderKeyGenerator:
    """
    Factory function to create OrderKeyGenerator instance
    
    Args:
        config_path: Path to canonical_customers.yaml (uses default if None)
        
    Returns:
        Configured OrderKeyGenerator instance
    """
    return OrderKeyGenerator(config_path)

# Example usage and testing functions
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Test order key generation
    generator = create_order_key_generator()
    
    # Test data
    test_data = [
        {
            'AAG ORDER NUMBER': 'JOO-00505',
            'CUSTOMER': 'GREYSON',
            'CUSTOMER STYLE': 'GREYSON-SWEATER-001',
            'PO NUMBER': '4755',
            'ORDER TYPE': 'DEVELOPMENT',
            'ORDER QTY': 720
        },
        {
            'AAG ORDER NUMBER': 'TRK-00234',
            'CUSTOMER': 'TRACKSMITH',
            'CUSTOMER STYLE': 'TRK-SHORTS-001',
            'PO NUMBER': '9876',
            'ORDER TYPE': 'PRODUCTION',
            'ORDER QTY': 500
        },
        {
            'AAG ORDER NUMBER': 'UNKNOWN-001',
            'CUSTOMER': 'NEW CUSTOMER',
            'CUSTOMER STYLE': 'STYLE-001',
            'PO NUMBER': '1234',
            'ORDER TYPE': 'SAMPLE',
            'ORDER QTY': 100
        }
    ]
    
    # Test key generation
    print("Order Key Generation Test:")
    print("-" * 50)
    
    for i, row_data in enumerate(test_data):
        customer = row_data['CUSTOMER']
        order_business_key = generator.generate_order_key(row_data, customer)
        
        # Test hash generation
        hash_columns = ['CUSTOMER STYLE', 'ORDER QTY', 'ORDER TYPE']
        row_hash = generator.generate_row_hash(row_data, hash_columns)
        
        # Test NEW detection
        existing_orders = {'JOO-00505'}  # Simulate existing order
        aag_number = row_data['AAG ORDER NUMBER']
        is_new = generator.is_new_order(aag_number, existing_orders)
        
        print(f"Record {i+1}:")
        print(f"  Customer: {customer}")
        print(f"  Order Business Key: {order_business_key}")
        print(f"  Row Hash: {row_hash[:16]}...")
        print(f"  Is NEW: {is_new}")
        print()
    
    # Test DataFrame processing
    print("DataFrame Processing Test:")
    print("-" * 50)
    
    df = pd.DataFrame(test_data)
    hash_columns = ['CUSTOMER STYLE', 'ORDER QTY', 'ORDER TYPE']
    existing_orders = {'JOO-00505'}
    
    result_df = generator.process_dataframe(df, hash_columns, existing_orders)
    
    print("Processed DataFrame:")
    print(result_df[['CUSTOMER', 'AAG ORDER NUMBER', 'order_business_key', 'sync_state']].to_string())
    print()
    
    # Validation test
    validation = generator.validate_order_keys(result_df)
    print("Validation Results:")
    for key, value in validation.items():
        print(f"  {key}: {value}")
