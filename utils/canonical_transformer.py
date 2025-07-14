"""
Canonical Data Transformer
Purpose: Transform source data to use canonical customer names upstream
Location: utils/canonical_transformer.py
"""
import pandas as pd
from typing import Dict, Any
import sys
from pathlib import Path

# Standard import pattern
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))
sys.path.insert(0, str(repo_root / "dev" / "customer-orders"))

import db_helper as db
import logger_helper
from customer_mapper import create_customer_mapper

class CanonicalTransformer:
    """Transform source data to use canonical customer names"""
    
    def __init__(self):
        self.logger = logger_helper.get_logger(__name__)
        self.customer_mapper = create_customer_mapper()
        
    def canonicalize_orders_unified(self, customer_filter: str = None, limit: int = None) -> pd.DataFrame:
        """
        Load ORDERS_UNIFIED data and transform customer names to canonical format
        
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
        FROM [dbo].[ORDERS_UNIFIED]
        WHERE [record_uuid] IS NOT NULL
        """
        
        # Add customer filter if specified (use database customer name for query)
        if customer_filter:
            # Get the database customer name for the filter
            db_customer_name = self.customer_mapper.get_database_customer_name(customer_filter)
            query += f" AND [CUSTOMER NAME] = '{db_customer_name}'"
        
        # Add limit if specified
        if limit:
            query = query.replace("SELECT ", f"SELECT TOP {limit} ")
            
        query += " ORDER BY [CUSTOMER NAME], [AAG ORDER NUMBER]"
        
        # Load data
        with db.get_connection('orders') as conn:
            df = pd.read_sql(query, conn)
            
        self.logger.info(f"Loaded {len(df)} records from ORDERS_UNIFIED")
        
        # Transform customer names to canonical
        df['CUSTOMER'] = df['original_customer_name'].apply(
            lambda x: self.customer_mapper.normalize_customer_name(x) if pd.notna(x) else x
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
        return self.customer_mapper.get_approved_customers()


def create_canonical_transformer() -> CanonicalTransformer:
    """Factory function to create CanonicalTransformer instance"""
    return CanonicalTransformer()
