"""
Customer Batch Processor - Enterprise-grade batch processing for customer orders
Purpose: Main orchestrator for customer-based order processing following order-staging patterns
Location: dev/customer-orders/customer_batch_processor.py
"""
import pandas as pd
import uuid
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import logging
from pathlib import Path
import yaml

# Add project root for imports
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

# Import utilities using working production pattern
import db_helper as db
import logger_helper

# Import package modules (same directory)
from integration_monday import MondayIntegrationClient
from staging_processor import StagingProcessor

class CustomerBatchProcessor:
    """Main orchestrator for customer batch processing with enterprise patterns"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize customer batch processor
        
        Args:
            config_path: Path to configuration file (defaults to utils/config.yaml)
        """
        self.logger = logger_helper.get_logger(__name__)
          # Load configuration
        if config_path is None:
            config_path = str(repo_root / "utils" / "config.yaml")
        
        self._load_config(config_path)
        
        # Initialize components with explicit local file import
        try:
            import sys
            from pathlib import Path
            local_dir = Path(__file__).parent
            sys.path.insert(0, str(local_dir))
            import customer_mapper
            self.customer_mapper = customer_mapper.CustomerMapper()
            sys.path.pop(0)  # Clean up path
            self.logger.info("CustomerMapper loaded successfully")
        except Exception as e:
            self.logger.warning(f"Could not load CustomerMapper: {e}, using fallback")
            self.customer_mapper = None
        
        self.monday_client = MondayIntegrationClient(str(repo_root / "utils" / "config.yaml"))
        
        # Batch configuration
        self.max_batch_size = self.config.get('batch_processing', {}).get('max_batch_size', 500)
        self.chunk_size = self.config.get('batch_processing', {}).get('chunk_size', 100)
        
        self.logger.info("Customer Batch Processor initialized")
    
    def _load_config(self, config_path: str) -> None:
        """Load configuration from YAML file"""
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                self.logger.error(f"Configuration file not found: {config_path}")
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
            with open(config_file, 'r') as f:
                self.config = yaml.safe_load(f)
            
            self.logger.info("Configuration loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise
    
    def start_batch(self, customer_name: str, batch_type: str = 'CUSTOMER_DELTA') -> str:
        """Start a new batch and return batch_id"""        
        batch_id = str(uuid.uuid4())
        try:
            with db.get_connection('orders') as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO [dbo].[MON_BatchProcessing] 
                    ([batch_id], [customer_name], [batch_type], [status], [start_time])
                    VALUES (?, ?, ?, 'STARTED', GETDATE())
                """, (batch_id, customer_name, batch_type))
                conn.commit()
            
            self.logger.info(f"Started batch {batch_id} for customer {customer_name}")
            return batch_id
            
        except Exception as e:
            self.logger.error(f"Failed to start batch for {customer_name}: {e}")
            raise
    
    def update_batch_status(self, batch_id: str, status: str, 
                           total_records: Optional[int] = None,
                           successful_records: Optional[int] = None,
                           failed_records: Optional[int] = None,
                           error_summary: Optional[str] = None) -> None:
        """Update batch processing status"""
        try:
            with db.get_connection('orders') as conn:
                cursor = conn.cursor()
                
                update_parts = ["[status] = ?", "[end_time] = CASE WHEN ? IN ('COMPLETED', 'FAILED') THEN GETDATE() ELSE [end_time] END"]
                params = [status, status]
                
                if total_records is not None:
                    update_parts.append("[total_records] = ?")
                    params.append(total_records)
                
                if successful_records is not None:
                    update_parts.append("[successful_records] = ?")
                    params.append(successful_records)
                
                if failed_records is not None:
                    update_parts.append("[failed_records] = ?")
                    params.append(failed_records)
                if error_summary is not None:
                    update_parts.append("[error_summary] = ?")
                    params.append(error_summary)
                
                params.append(batch_id)
                
                query = f"""
                    UPDATE [dbo].[MON_BatchProcessing] 
                    SET {', '.join(update_parts)}
                    WHERE [batch_id] = ?
                """
                cursor.execute(query, params)
                conn.commit()                
            self.logger.info(f"Updated batch {batch_id} status to {status}")            
        except Exception as e:
            self.logger.error(f"Failed to update batch status for {batch_id}: {e}")
            raise

    def get_customers_with_changes(self, customer_filter: str = None, po_number_filter: str = None) -> List[str]:
        """PHASE 1 FIX - Direct comparison only, no SNAPSHOT table"""
        
        try:
            # SIMPLIFIED PHASE 1 - Direct SQL comparison against production
            where_conditions = [
                "ou.[CUSTOMER NAME] IS NOT NULL",
                "ou.[AAG ORDER NUMBER] IS NOT NULL"
            ]
            
            # Handle customer filtering with database name (GREYSON -> GREYSON CLOTHIERS)
            customer_params = []
            if customer_filter:
                database_customer = self._get_database_customer_name(customer_filter)
                customer_params.append(database_customer)
                where_conditions.append("ou.[CUSTOMER NAME] = ?")
                
            if po_number_filter:
                where_conditions.append(f"ou.[PO NUMBER] = '{po_number_filter}'")
            
            where_clause = " AND ".join(where_conditions)
            
            # DIRECT COMPARISON - NO SNAPSHOT TABLE
            query = f"""
            SELECT DISTINCT 
                ou.[CUSTOMER NAME] as customer_name,
                COUNT(*) as change_count
            FROM [dbo].[ORDERS_UNIFIED] ou
            LEFT JOIN [dbo].[MON_CustMasterSchedule] mc
                ON ou.[AAG ORDER NUMBER] = mc.[AAG ORDER NUMBER]
            WHERE {where_clause}
                AND mc.[AAG ORDER NUMBER] IS NULL  -- NEW orders only for Phase 1
            GROUP BY ou.[CUSTOMER NAME]
            ORDER BY change_count DESC
            """
            
            with db.get_connection('orders') as conn:
                if customer_params:
                    df = pd.read_sql(query, conn, params=customer_params)
                else:
                    df = pd.read_sql(query, conn)
            
            customers = df['customer_name'].tolist()
            
            # Apply customer mapping to get canonical names
            canonical_customers = [
                self._get_canonical_customer_name(customer)
                for customer in customers
            ]
            
            # Remove duplicates and sort by priority
            unique_customers = list(set(canonical_customers))
            unique_customers.sort(key=lambda c: (
                self._get_customer_priority(c),
                c            ))
            self.logger.info(f"Found {len(unique_customers)} customers with changes: {unique_customers[:5]}...")
            return unique_customers
            
        except Exception as e:
            self.logger.error(f"Failed to get customers with changes: {e}")
            return []
    
    def get_customer_changes(self, customer_name: str, limit: Optional[int] = None, po_number_filter: Optional[str] = None) -> pd.DataFrame:
        """Get NEW orders for a specific customer - Phase 1 Production Fix"""
        
        try:
            canonical_customer = self._get_canonical_customer_name(customer_name)
            database_customer = self._get_database_customer_name(customer_name)
            
            # Build optional PO filter
            po_filter = ""
            if po_number_filter:
                po_filter = f"AND ou.[PO NUMBER] = '{po_number_filter}'"
            
            # PHASE 1 FIX: Direct comparison against Monday.com production table
            # Use database customer name (GREYSON CLOTHIERS) for query
            query = f"""
            SELECT TOP {limit if limit else 10000}
                ou.*,
                CASE 
                    WHEN mc.[AAG ORDER NUMBER] IS NULL THEN 'NEW'
                    ELSE 'EXISTING'
                END as change_type
            FROM [dbo].[ORDERS_UNIFIED] ou
            LEFT JOIN [dbo].[MON_CustMasterSchedule] mc
                ON ou.[AAG ORDER NUMBER] = mc.[AAG ORDER NUMBER]
            WHERE ou.[CUSTOMER NAME] = ?
                AND ou.[AAG ORDER NUMBER] IS NOT NULL
                AND mc.[AAG ORDER NUMBER] IS NULL  -- NEW orders only (Phase 1)
                {po_filter}
            ORDER BY ou.[ORDER DATE PO RECEIVED] DESC
            """
            
            with db.get_connection('orders') as conn:
                df = pd.read_sql(query, conn, params=[database_customer])
        
            # ADD THIS CRITICAL SECTION - YAML TRANSFORMATION
            if self.customer_mapper and not df.empty:
                self.logger.info(f"Applying YAML transformation to {len(df)} orders")
                # THIS IS THE MISSING STEP - TRANSFORM THE DATA!
                transformed_df = self.customer_mapper.transform_orders_batch(df)
                self.logger.info(f"Transformation complete: {len(df)} → {len(transformed_df)} records")
                return transformed_df
            else:
                self.logger.warning("No customer mapper available or empty DataFrame, returning raw data")
                return df
            
        except Exception as e:
            self.logger.error(f"Error getting customer changes for {customer_name}: {str(e)}")
            return pd.DataFrame()

        self.logger.info(f"Found {len(df)} NEW orders for customer {canonical_customer} (Phase 1: NEW orders only)")
        return df

    def process_customer_batch(self, customer_name: str, limit: Optional[int] = None, po_number_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a complete customer batch: detect changes → stage → Monday.com → production
        
        Args:
            customer_name: Customer to process
            limit: Optional limit on number of records
            po_number_filter: Optional PO number filter for testing
            
        Returns:
            dict: Processing results
        """
        
        canonical_customer = self._get_canonical_customer_name(customer_name)
        batch_id = None
        
        try:
            self.logger.info(f"Processing customer batch: {canonical_customer}")
            
            # Start batch tracking
            batch_id = self.start_batch(canonical_customer)
            
            # Get customer changes with optional PO filter
            changes_df = self.get_customer_changes(customer_name, limit, po_number_filter)
            
            if changes_df.empty:
                self.update_batch_status(batch_id, 'COMPLETED', 0, 0, 0)
                return {
                    'status': 'SUCCESS',
                    'batch_id': batch_id,
                    'customer': canonical_customer,
                    'total_records': 0,
                    'message': 'No changes detected'
                }
            
            # Update batch with total records
            self.update_batch_status(batch_id, 'PROCESSING', len(changes_df))
            
            # Process in chunks for better performance
            successful_records = 0
            failed_records = 0
            errors = []
            
            for chunk_start in range(0, len(changes_df), self.chunk_size):
                chunk_end = min(chunk_start + self.chunk_size, len(changes_df))
                chunk_df = changes_df.iloc[chunk_start:chunk_end]
                
                try:
                    # Process chunk (placeholder for actual processing logic)
                    chunk_result = self._process_chunk(chunk_df, batch_id)
                    successful_records += chunk_result.get('successful', 0)
                    failed_records += chunk_result.get('failed', 0)
                    
                    if chunk_result.get('errors'):
                        errors.extend(chunk_result['errors'])
                    
                    self.logger.info(f"Processed chunk {chunk_start}-{chunk_end} for {canonical_customer}")
                    
                except Exception as e:
                    error_msg = f"Chunk {chunk_start}-{chunk_end} failed: {str(e)}"
                    errors.append(error_msg)
                    failed_records += len(chunk_df)
                    self.logger.error(error_msg)
            
            # Update final batch status
            final_status = 'COMPLETED' if failed_records == 0 else 'COMPLETED_WITH_ERRORS'
            error_summary = '; '.join(errors[:5]) if errors else None  # Limit error summary length
            
            self.update_batch_status(
                batch_id, 
                final_status, 
                len(changes_df),
                successful_records, 
                failed_records,
                error_summary
            )
            
            return {
                'status': 'SUCCESS',
                'batch_id': batch_id,
                'customer': canonical_customer,
                'total_records': len(changes_df),
                'successful_records': successful_records,
                'failed_records': failed_records,
                'errors': errors
            }
            
        except Exception as e:
            error_msg = f"Customer batch processing failed for {canonical_customer}: {str(e)}"
            self.logger.error(error_msg)
            
            if batch_id:
                self.update_batch_status(batch_id, 'FAILED', error_summary=str(e))
            
            return {
                'status': 'ERROR',
                'batch_id': batch_id,
                'customer': canonical_customer,
                'error': error_msg
            }
    
    def _process_chunk(self, chunk_df: pd.DataFrame, batch_id: str) -> Dict[str, Any]:
        """
        Process a chunk of records with Monday.com integration and subitem creation
        
        Args:
            chunk_df: Chunk of records to process
            batch_id: Batch ID for tracking
            
        Returns:
            dict: Chunk processing results
        """
        
        try:
            self.logger.info(f"Processing chunk with {len(chunk_df)} records for batch {batch_id}")
            
            successful = 0
            failed = 0
            errors = []

            # Get customer name from the chunk data
            customer_name = None
            if not chunk_df.empty and 'CUSTOMER NAME' in chunk_df.columns:
                customer_name = chunk_df.iloc[0]['CUSTOMER NAME']

            if not customer_name:
                self.logger.error("No customer name found in chunk data")
                return {
                    'successful': 0,
                    'failed': len(chunk_df),
                    'errors': ['No customer name in data']
                }

            # PHASE 1 WORKFLOW: NEW orders need master items created first
            self.logger.info(f"Phase 1 NEW order workflow: Create master items then subitems")
            
            # Initialize staging processor for complete workflow
            staging_processor = StagingProcessor()
            
            # Step 1: Stage the customer batch (orders + subitems)
            stage_batch_id = staging_processor.stage_customer_batch(customer_name, chunk_df)  # Use actual customer!
            self.logger.info(f"Staged batch {stage_batch_id} with {len(chunk_df)} orders")
            
            # Step 2: Process master schedule (create Monday.com master items)
            master_results = staging_processor.process_master_schedule(stage_batch_id)
            self.logger.info(f"Master items: {master_results.get('processed', 0)}/{master_results.get('total', 0)} successful")
            
            # Step 3: Process subitems (create Monday.com subitems using master item IDs)
            subitem_results = staging_processor.process_subitems(stage_batch_id)
            self.logger.info(f"Subitems: {subitem_results.get('processed', 0)}/{subitem_results.get('total', 0)} successful")

            # Calculate totals
            successful = master_results.get('processed', 0) + subitem_results.get('processed', 0)
            failed = (master_results.get('total', 0) - master_results.get('processed', 0)) + (subitem_results.get('total', 0) - subitem_results.get('processed', 0))
            
            # Stage 3: Update processing status
            self.logger.info(f"Chunk processed: {successful} successful, {failed} failed")
            
            return {
                'successful': successful,
                'failed': failed,
                'errors': errors,
                'subitem_results': subitem_results
            }
            
        except Exception as e:
            error_msg = f"Failed to process chunk: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                'successful': 0,
                'failed': len(chunk_df),
                'errors': [{'error': error_msg, 'chunk_size': len(chunk_df)}]
            }
    
    def _process_subitems(self, df: pd.DataFrame, batch_id: str) -> Dict[str, Any]:
        """
        Process subitem creation for the given DataFrame with complete staging workflow
        
        Args:
            df: DataFrame with order data
            batch_id: Batch ID for tracking
            
        Returns:
            dict: Subitem processing results
        """
        
        try:
            self.logger.info(f"Starting complete subitem processing workflow for {len(df)} records (batch: {batch_id})")
            
            # STEP 1: Initialize staging processor for database operations
            staging_processor = StagingProcessor()
            
            # STEP 2: Detect size columns and melt data (preparation for staging)
            size_columns = self.monday_client.detect_size_columns(df)
            if not size_columns:
                return {
                    'success': False,
                    'error': 'No size columns detected',
                    'subitems_created': 0,
                    'errors': 1,
                    'staging_records': 0
                }
            
            melted_df = self.monday_client.melt_size_columns(df, size_columns)
            if melted_df.empty:
                return {
                    'success': False,
                    'error': 'No valid size data after melting',
                    'subitems_created': 0,
                    'errors': 1,
                    'staging_records': 0
                }
            
            self.logger.info(f"Size detection successful: {len(size_columns)} columns → {len(melted_df)} subitem records")
            
            # STEP 3: Create staging data and insert to STG_MON_CustMasterSchedule_Subitems
            # We'll use the melted data directly and prepare it for staging format
            subitems_staging_data = melted_df.copy()
            
            # Fix column names to match actual staging table schema
            column_renames = {
                'AAG ORDER NUMBER': 'AAG_ORDER_NUMBER'  # The main mismatch
            }
            subitems_staging_data = subitems_staging_data.rename(columns=column_renames)
            
            # Add required staging columns
            subitems_staging_data['stg_batch_id'] = batch_id
            subitems_staging_data['stg_status'] = 'PENDING'
            subitems_staging_data['stg_created_date'] = datetime.now()
            subitems_staging_data['stg_retry_count'] = 0
            subitems_staging_data['parent_source_uuid'] = subitems_staging_data.apply(lambda row: str(uuid.uuid4()), axis=1)
            subitems_staging_data['stg_parent_stg_id'] = range(1, len(subitems_staging_data) + 1)  # Temporary for staging
            
            # Map melted columns to staging format (match actual staging table schema)
            if 'Size' in subitems_staging_data.columns:
                subitems_staging_data['stg_size_label'] = subitems_staging_data['Size']
                # Keep Size column for Monday.com API
            if 'Order_Qty' in subitems_staging_data.columns:
                subitems_staging_data['ORDER_QTY'] = subitems_staging_data['Order_Qty'].astype(int)
                subitems_staging_data['[Order Qty]'] = subitems_staging_data['Order_Qty'].astype(str)
                # Remove the original Order_Qty column
                subitems_staging_data = subitems_staging_data.drop(columns=['Order_Qty'])
            
            # Add customer and order context from original data (fill missing fields)
            if len(df) > 0:
                first_order = df.iloc[0]
                # Fill any missing values with data from the first order
                for field_mapping in [
                    ('CUSTOMER', 'CUSTOMER NAME'),
                    ('STYLE', 'STYLE'),
                    ('COLOR', 'COLOR'),
                    ('PO_NUMBER', 'PO NUMBER'),
                    ('CUSTOMER_ALT_PO', 'CUSTOMER ALT PO'),
                    ('UNIT_OF_MEASURE', 'UNIT OF MEASURE')
                ]:
                    staging_col, source_col = field_mapping
                    if staging_col not in subitems_staging_data.columns or subitems_staging_data[staging_col].isna().all():
                        subitems_staging_data[staging_col] = first_order.get(source_col, first_order.get(staging_col, ''))
            
            staging_count = staging_processor._insert_to_staging_subitems(subitems_staging_data, batch_id)
            
            self.logger.info(f"Staging insertion successful: {staging_count} records inserted to STG_MON_CustMasterSchedule_Subitems")
            
            # STEP 4: Process subitems via Monday.com API (using original melted data)
            success_count, error_count, error_records = self.monday_client.create_subitems_from_melted_data(melted_df)
            
            # STEP 5: Compile comprehensive results
            total_operations = success_count + error_count
            success_rate = success_count / total_operations if total_operations > 0 else 0
            
            if success_count > 0:
                self.logger.info(f"Subitem processing successful: {success_count} API calls completed")
            else:
                self.logger.warning(f"Subitem processing had issues: {error_count} errors")
            
            # Log processing summary
            self.logger.info(f"Complete subitem workflow - Size columns: {len(size_columns)}, "
                           f"Staging records: {staging_count}, "
                           f"API success: {success_count}, "
                           f"Success rate: {success_rate:.2%}")
            
            return {
                'success': success_count > 0,
                'size_columns_detected': len(size_columns),
                'size_columns': size_columns,
                'melted_records': len(melted_df),
                'staging_records': staging_count,
                'subitems_created': success_count,
                'errors': error_count,
                'error_records': error_records,
                'processing_summary': {
                    'total_size_columns': len(size_columns),
                    'valid_size_records': len(melted_df),
                    'staging_records': staging_count,
                    'api_calls_successful': success_count,
                    'success_rate': success_rate
                }
            }
            
        except Exception as e:
            error_msg = f"Failed to process subitems: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                'success': False,
                'error': error_msg,
                'subitems_created': 0,
                'errors': 1,
                'error_records': [{'error': error_msg, 'batch_id': batch_id}]
            }
    
    def process_all_customers(self, limit_per_customer: Optional[int] = None) -> Dict[str, Any]:
        """Process all customers with changes"""
        
        try:
            customers = self.get_customers_with_changes()
            
            if not customers:
                self.logger.info("No customers with changes found")
                return {
                    'status': 'SUCCESS',
                    'message': 'No customers with changes',
                    'results': []
                }
            
            results = []
            total_successful = 0
            total_failed = 0
            
            for customer in customers:
                self.logger.info(f"Processing customer: {customer}")
                
                result = self.process_customer_batch(customer, limit_per_customer)
                results.append(result)
                
                if result['status'] == 'SUCCESS':
                    total_successful += result.get('successful_records', 0)
                    total_failed += result.get('failed_records', 0)
            
            self.logger.info(f"Completed processing {len(customers)} customers")
            
            return {
                'status': 'SUCCESS',
                'customers_processed': len(customers),
                'total_successful_records': total_successful,
                'total_failed_records': total_failed,
                'results': results
            }
            
        except Exception as e:
            error_msg = f"Failed to process all customers: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                'status': 'ERROR',
                'error': error_msg
            }
    
    def _get_customer_sample_data(self, customer_name: str, limit: int = 5) -> pd.DataFrame:
        """Get sample customer data for testing purposes"""
        
        try:
            self.logger.info(f"Getting sample data for customer: {customer_name} (limit: {limit})")
            
            # Use existing get_customer_changes method
            sample_data = self.get_customer_changes(customer_name, limit=limit)
            
            if not sample_data.empty:
                self.logger.info(f"Retrieved {len(sample_data)} sample records for {customer_name}")
            else:
                self.logger.warning(f"No sample data found for {customer_name}")
            
            return sample_data
            
        except Exception as e:
            self.logger.error(f"Failed to get sample data for {customer_name}: {str(e)}")
            return pd.DataFrame()

    def _get_canonical_customer_name(self, customer_name: str) -> str:
        """Get canonical customer name with fallback"""
        if self.customer_mapper:
            return self._get_canonical_customer_name(customer_name)
        else:
            # Fallback: simple normalization
            return customer_name.upper().strip()
    
    def _get_database_customer_name(self, customer_name: str) -> str:
        """Get database customer name with fallback"""
        if self.customer_mapper:
            return self._get_database_customer_name(customer_name)
        else:
            # Fallback: use customer name as-is
            return customer_name
    
    def _get_customer_priority(self, customer_name: str) -> int:
        """Get customer priority with fallback"""
        if self.customer_mapper:
            return self._get_customer_priority(customer_name)
        else:
            # Fallback: default priority
            return 1
def create_customer_batch_processor() -> CustomerBatchProcessor:
    """Factory function to create CustomerBatchProcessor instance"""
    return CustomerBatchProcessor()
