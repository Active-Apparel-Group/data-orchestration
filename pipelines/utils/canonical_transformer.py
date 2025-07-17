"""
Canonical Data Transformer
Purpose: Transform source data to use canonical customer names upstream
Location: pipelines/utils/canonical_transformer.py
"""
import pandas as pd
from typing import Dict, Any
import sys
from pathlib import Path

# Standard import pattern for pipelines
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "pipelines").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

import db_helper as db
import logger_helper
from canonical_customer_manager import CanonicalCustomerManager

class CanonicalTransformer:
    """Transform source data to use canonical customer names"""
    
    def __init__(self):
        self.logger = logger_helper.get_logger(__name__)
        self.canonical_manager = CanonicalCustomerManager()
        
    def canonicalize_orders_unified(self, customer_filter: str = None, limit: int = None) -> pd.DataFrame:
        """
        Load ORDER_LIST data and transform customer names to canonical format
        
        Args:
            customer_filter: Optional canonical customer name to filter by
            limit: Optional limit on number of records
            
        Returns:
            pd.DataFrame: Orders data with canonical customer names
        """
        
        # Build base query
        query = """
        SELECT 
            [record_uuid],
            [AAG ORDER NUMBER],
            [CUSTOMER NAME] as original_customer_name,
            [CUSTOMER STYLE],
            [CUSTOMER COLOUR DESCRIPTION],
            [TOTAL QTY],
            [ORDER DATE PO RECEIVED],
            [PO NUMBER],
            [CUSTOMER ALT PO],
            [DESTINATION],
            [DELIVERY TERMS],
            [CUSTOMER SEASON],
            [DROP],
            [CATEGORY],
            [PATTERN ID]
        FROM [dbo].[ORDER_LIST]
        WHERE [record_uuid] IS NOT NULL
        """
        
        # Add customer filter if specified (use canonical customer name for query)
        if customer_filter:
            # Get canonical customer's database variants for the filter
            canonical_customer = self.canonical_manager.canonicalize_customer(customer_filter, 'master_order_list')
            # Use the canonical customer name for filtering
            query += f" AND [CUSTOMER NAME] = '{canonical_customer}'"
        
        # Add limit if specified
        if limit:
            query = query.replace("SELECT ", f"SELECT TOP {limit} ")
            
        query += " ORDER BY [CUSTOMER NAME], [AAG ORDER NUMBER]"
        
        # Load data
        with db.get_connection('orders') as conn:
            df = pd.read_sql(query, conn)
            
        self.logger.info(f"Loaded {len(df)} records from ORDER_LIST")
        
        # Transform customer names to canonical
        df['CUSTOMER'] = df['original_customer_name'].apply(
            lambda x: self.canonical_manager.canonicalize_customer(x, 'master_order_list') if pd.notna(x) else x
        )
        
        # Log transformation results
        transformations = df.groupby(['original_customer_name', 'CUSTOMER']).size().reset_index(name='count')
        for _, row in transformations.iterrows():
            if row['original_customer_name'] != row['CUSTOMER']:
                self.logger.info(f"Transformed '{row['original_customer_name']}' -> '{row['CUSTOMER']}' ({row['count']} records)")
        
        # Drop the original customer name column as we now have canonical
        df = df.drop('original_customer_name', axis=1)
        
        self.logger.info(f"Canonical transformation complete: {len(df)} records with canonical customer names")
        
        return df
    
    def get_canonical_customers(self) -> list:
        """Get list of all canonical customer names"""
        return self.canonical_manager.get_approved_customers()


def create_canonical_transformer() -> CanonicalTransformer:
    """Factory function to create CanonicalTransformer instance"""
    return CanonicalTransformer()
