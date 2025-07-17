"""
Enhanced ORDER_LIST Transformer with Canonical Customer Integration
Purpose: Transform ORDER_LIST data with canonical customer name injection
Location: utils/canonical_order_list_transformer.py

Integrates canonical customer mapping into the ORDER_LIST transformation process.
Ensures all customer names are standardized before database insertion.
"""
import sys
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import logging

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

import db_helper as db
import logger_helper
from canonical_customer_manager import get_canonical_customer_manager

class CanonicalOrderListTransformer:
    """Enhanced ORDER_LIST transformer with canonical customer integration"""
    
    def __init__(self):
        self.logger = logger_helper.get_logger(__name__)
        self.canonical_manager = get_canonical_customer_manager()
        
    def generate_canonical_transform_sql(self, table_name: str, ddl_columns: list) -> str:
        """
        Generate SQL for transforming raw table with canonical customer names
        
        Args:
            table_name: Raw table name (e.g., 'GREYSON_ORDER_LIST_RAW')
            ddl_columns: DDL column definitions
            
        Returns:
            SQL query with canonical customer transformation
        """
        
        # Extract customer name from table name
        customer_from_table = table_name.replace('_ORDER_LIST_RAW', '').replace('x', '')
        
        # Get canonical customer name
        canonical_customer = self.canonical_manager.get_canonical_customer(
            customer_from_table, 
            source_system='master_order_list'
        )
        
        # Get source customer name from canonical mapping
        source_customer_name = self.canonical_manager.get_source_customer_name(
            canonical_customer,
            source_system='master_order_list'
        )
        
        self.logger.info(f"Customer canonicalization: '{customer_from_table}' → '{canonical_customer}'")
        self.logger.info(f"Source customer name: '{source_customer_name}'")
        
        # Build SELECT expressions with canonical customer injection
        select_expressions = [
            f"'{canonical_customer}' AS [CANONICAL_CUSTOMER]",  # Inject canonical customer
            f"'{source_customer_name or customer_from_table}' AS [SOURCE_CUSTOMER_NAME]",  # Original from config or table
            f"'{customer_from_table}' AS [customer_source]"  # Table source identifier
        ]
        
        # Add other column mappings (existing logic)
        for col in ddl_columns:
            if col["name"] in ["CANONICAL_CUSTOMER", "SOURCE_CUSTOMER_NAME", "customer_source"]:
                continue  # Skip - already added above
                
            canonical_name = col["name"]
            candidates = [canonical_name] + col.get("aliases", [])
            
            # Find column match in raw table
            matched_column = self._find_column_match(table_name, candidates)
            
            if matched_column:
                # Apply data type transformations
                if col["type"] == "INT":
                    select_expressions.append(f"TRY_CAST([{matched_column}] AS INT) AS [{canonical_name}]")
                elif col["type"] == "DECIMAL(38,4)":
                    select_expressions.append(f"TRY_CAST([{matched_column}] AS DECIMAL(38,4)) AS [{canonical_name}]")
                elif col["type"] == "DATE":
                    select_expressions.append(f"TRY_CAST([{matched_column}] AS DATE) AS [{canonical_name}]")
                else:  # NVARCHAR
                    select_expressions.append(f"CAST([{matched_column}] AS NVARCHAR(255)) AS [{canonical_name}]")
            else:
                # NULL placeholder for missing columns
                if col["type"] == "INT":
                    select_expressions.append(f"CAST(NULL AS INT) AS [{canonical_name}]")
                elif col["type"] == "DECIMAL(38,4)":
                    select_expressions.append(f"CAST(NULL AS DECIMAL(38,4)) AS [{canonical_name}]")
                elif col["type"] == "DATE":
                    select_expressions.append(f"CAST(NULL AS DATE) AS [{canonical_name}]")
                else:
                    select_expressions.append(f"CAST(NULL AS NVARCHAR(255)) AS [{canonical_name}]")
        
        # Generate final SQL with canonical customer integration
        sql = f"""
        INSERT INTO [dbo].[swp_ORDER_LIST] 
        SELECT 
            {','.join(select_expressions)}
        FROM [dbo].[{table_name}]
        WHERE [CUSTOMER NAME] IS NOT NULL  -- Data quality filter
        """
        
        return sql
    
    def _find_column_match(self, table_name: str, candidates: list) -> str:
        """Find first matching column in raw table"""
        try:
            # Query table schema
            with db.get_connection('orders') as conn:
                schema_query = f"""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = '{table_name}'
                """
                columns_df = pd.read_sql(schema_query, conn)
                available_columns = [col.upper() for col in columns_df['COLUMN_NAME'].tolist()]
            
            # Find first match
            for candidate in candidates:
                if candidate.upper() in available_columns:
                    return candidate
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding column match for table {table_name}: {e}")
            return None
    
    def validate_canonical_customers(self, raw_tables: list) -> Dict[str, Any]:
        """
        Validate all customers in pipeline have canonical mappings
        
        Args:
            raw_tables: List of raw table names
            
        Returns:
            Validation results with detailed mapping information
        """
        validation_results = {
            'valid_customers': [],
            'invalid_customers': [],
            'canonical_mappings': {},
            'approval_status': {},
            'unmapped_details': []
        }
        
        for table_name in raw_tables:
            customer_from_table = table_name.replace('_ORDER_LIST_RAW', '').replace('x', '')
            
            # Check if customer has canonical mapping
            is_valid = self.canonical_manager.validate_customer(customer_from_table, 'master_order_list')
            canonical_name = self.canonical_manager.get_canonical_customer(customer_from_table, 'master_order_list')
            status = self.canonical_manager.get_customer_status(canonical_name)
            
            if is_valid:
                validation_results['valid_customers'].append(customer_from_table)
                validation_results['canonical_mappings'][customer_from_table] = canonical_name
                validation_results['approval_status'][canonical_name] = status
                
                self.logger.info(f"✅ Customer '{customer_from_table}' → '{canonical_name}' (status: {status})")
            else:
                validation_results['invalid_customers'].append(customer_from_table)
                validation_results['unmapped_details'].append({
                    'table_name': table_name,
                    'customer_from_table': customer_from_table,
                    'attempted_canonical': canonical_name
                })
                self.logger.warning(f"❌ Customer '{customer_from_table}' has no canonical mapping")
        
        # Calculate success metrics
        total_customers = len(raw_tables)
        valid_count = len(validation_results['valid_customers'])
        success_rate = (valid_count / total_customers * 100) if total_customers > 0 else 0
        
        validation_results.update({
            'total_customers': total_customers,
            'valid_count': valid_count,
            'invalid_count': len(validation_results['invalid_customers']),
            'success_rate': success_rate,
            'all_valid': len(validation_results['invalid_customers']) == 0
        })
        
        return validation_results
    
    def get_customer_mapping_summary(self, raw_tables: list) -> Dict[str, Any]:
        """
        Generate summary of customer mappings for reporting
        
        Args:
            raw_tables: List of raw table names
            
        Returns:
            Summary of customer mappings with statistics
        """
        mapping_summary = {
            'total_tables': len(raw_tables),
            'customer_mappings': [],
            'canonical_customers': set(),
            'approval_status_counts': {'approved': 0, 'review': 0, 'unknown': 0}
        }
        
        for table_name in raw_tables:
            customer_from_table = table_name.replace('_ORDER_LIST_RAW', '').replace('x', '')
            canonical_customer = self.canonical_manager.get_canonical_customer(customer_from_table, 'master_order_list')
            status = self.canonical_manager.get_customer_status(canonical_customer)
            source_customer = self.canonical_manager.get_source_customer_name(canonical_customer, 'master_order_list')
            
            mapping_info = {
                'table_name': table_name,
                'customer_from_table': customer_from_table,
                'canonical_customer': canonical_customer,
                'source_customer_name': source_customer,
                'approval_status': status or 'unknown',
                'has_mapping': canonical_customer != customer_from_table or self.canonical_manager._is_canonical(customer_from_table)
            }
            
            mapping_summary['customer_mappings'].append(mapping_info)
            mapping_summary['canonical_customers'].add(canonical_customer)
            
            # Count approval statuses
            status_key = status if status in ['approved', 'review'] else 'unknown'
            mapping_summary['approval_status_counts'][status_key] += 1
        
        # Convert set to list for JSON serialization
        mapping_summary['canonical_customers'] = list(mapping_summary['canonical_customers'])
        mapping_summary['unique_canonical_count'] = len(mapping_summary['canonical_customers'])
        
        return mapping_summary
    
    def validate_customer_data_quality(self, table_name: str) -> Dict[str, Any]:
        """
        Validate data quality for a specific customer table
        
        Args:
            table_name: Raw table name to validate
            
        Returns:
            Data quality metrics
        """
        try:
            with db.get_connection('orders') as conn:
                # Check basic data quality metrics
                quality_query = f"""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT([CUSTOMER NAME]) as records_with_customer,
                    COUNT(DISTINCT [CUSTOMER NAME]) as unique_customers,
                    COUNT([AAG ORDER NUMBER]) as records_with_order_number,
                    COUNT(DISTINCT [AAG ORDER NUMBER]) as unique_order_numbers
                FROM [dbo].[{table_name}]
                """
                
                quality_df = pd.read_sql(quality_query, conn)
                quality_metrics = quality_df.iloc[0].to_dict()
                
                # Calculate quality percentages
                total = quality_metrics['total_records']
                if total > 0:
                    quality_metrics['customer_completeness_pct'] = (quality_metrics['records_with_customer'] / total) * 100
                    quality_metrics['order_number_completeness_pct'] = (quality_metrics['records_with_order_number'] / total) * 100
                else:
                    quality_metrics['customer_completeness_pct'] = 0
                    quality_metrics['order_number_completeness_pct'] = 0
                
                quality_metrics['table_name'] = table_name
                quality_metrics['validation_timestamp'] = pd.Timestamp.now()
                
                return quality_metrics
                
        except Exception as e:
            self.logger.error(f"Error validating data quality for table {table_name}: {e}")
            return {
                'table_name': table_name,
                'error': str(e),
                'validation_timestamp': pd.Timestamp.now()
            }


def create_canonical_order_list_transformer() -> CanonicalOrderListTransformer:
    """Factory function for CanonicalOrderListTransformer"""
    return CanonicalOrderListTransformer()
