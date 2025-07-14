"""
Order Sync V2 - Monday.com Integration with Staging Tables
Enterprise-grade workflow with proper error handling and batch processing

Workflow:
1. Process customers in batches
2. Load orders to staging tables 
3. Create Monday.com items with retry logic
4. Create subitems for successful items
5. Promote successful records to production
6. Clean up staging tables

This replaces the original order_sync.py with a robust staging-based approach.
"""

import os
import sys
import logging
from datetime import datetime
from typing import List, Dict, Optional
import base64

# Add src to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from order_staging.batch_processor import BatchProcessor
from order_staging.staging_config import get_config

# Configure logging
def setup_logging():
    """Set up logging configuration"""
    config = get_config()
    log_config = config['logging']
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_config['file_path'])
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_config['level']),
        format=log_config['format'],
        handlers=[
            logging.FileHandler(log_config['file_path']),
            logging.StreamHandler()  # Also log to console
        ]
    )
    
    return logging.getLogger(__name__)

def get_db_connection_string() -> str:
    """Get database connection string using environment variables"""
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
        load_dotenv(dotenv_path=env_path)
    except:
        pass
    
    # Get password - try encoded first, then plain text
    password = os.getenv('SECRET_ORDERS_PWD')
    if password:
        try:
            password = base64.b64decode(password).decode()
        except:
            pass
    else:
        password = os.getenv('DB_ORDERS_PASSWORD')
    
    host = os.getenv('DB_ORDERS_HOST')
    port = int(os.getenv('DB_ORDERS_PORT', 1433))
    database = os.getenv('DB_ORDERS_DATABASE')
    username = os.getenv('DB_ORDERS_USERNAME')
    
    if not all([host, database, username, password]):
        raise ValueError("Missing required database connection environment variables")
    
    # Use working driver detection
    import pyodbc
    driver = "{ODBC Driver 17 for SQL Server}"
    try:
        test_conn_str = f"DRIVER={driver};SERVER=test;DATABASE=test;"
        pyodbc.connect(test_conn_str, timeout=1)
    except:
        driver = "{SQL Server}"
    
    conn_str = (
        f"DRIVER={driver};"
        f"SERVER={host},{port};"
        f"DATABASE={database};"
        f"UID={username};PWD={password};"
        "Encrypt=no;TrustServerCertificate=yes;"
    )
    
    return conn_str

def process_single_customer(processor: BatchProcessor, customer_name: str) -> Dict:
    """Process a single customer batch"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Processing customer: {customer_name}")
        result = processor.process_customer_batch(customer_name)
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"Customer: {customer_name}")
        print(f"Batch ID: {result['batch_id']}")
        print(f"Status: {result['status']}")
        print(f"Orders Loaded: {result['orders_loaded']}")
        print(f"Items Created: {result['items_created']} (Errors: {result.get('items_errors', 0)})")
        print(f"Subitems Created: {result['subitems_created']} (Errors: {result.get('subitems_errors', 0)})")
        print(f"Records Promoted: {result.get('orders_promoted', 0)} orders, {result.get('subitems_promoted', 0)} subitems")
        print(f"{'='*60}\n")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to process customer {customer_name}: {e}")
        return {
            'customer_name': customer_name,
            'status': 'FAILED',
            'error': str(e)
        }

def process_all_customers(processor: BatchProcessor) -> List[Dict]:
    """Process all customers with new orders"""
    logger = logging.getLogger(__name__)
    
    # Get customers with new orders
    customers = processor.get_customers_with_new_orders()
    
    if not customers:
        logger.info("No customers with new orders found")
        return []
    
    logger.info(f"Found {len(customers)} customers with new orders: {customers}")
    
    results = []
    for customer in customers:
        result = process_single_customer(processor, customer)
        results.append(result)
    
    return results

def process_specific_customers(processor: BatchProcessor, customer_list: List[str]) -> List[Dict]:
    """Process specific customers"""
    logger = logging.getLogger(__name__)
    
    logger.info(f"Processing specific customers: {customer_list}")
    
    results = []
    for customer in customer_list:
        result = process_single_customer(processor, customer)
        results.append(result)
    
    return results

def print_final_summary(results: List[Dict]):
    """Print final processing summary"""
    if not results:
        print("No customers processed.")
        return
    
    print(f"\n{'='*80}")
    print("FINAL PROCESSING SUMMARY")
    print(f"{'='*80}")
    
    total_customers = len(results)
    successful_customers = len([r for r in results if r.get('status') not in ['FAILED']])
    failed_customers = total_customers - successful_customers
    
    total_orders = sum(r.get('orders_loaded', 0) for r in results)
    total_items = sum(r.get('items_created', 0) for r in results)
    total_subitems = sum(r.get('subitems_created', 0) for r in results)
    
    print(f"Customers Processed: {total_customers}")
    print(f"Successful: {successful_customers}")
    print(f"Failed: {failed_customers}")
    print(f"Total Orders Loaded: {total_orders}")
    print(f"Total Items Created: {total_items}")
    print(f"Total Subitems Created: {total_subitems}")
    
    # Show customer-by-customer results
    print(f"\nCustomer Results:")
    print("-" * 80)
    for result in results:
        status_icon = "✓" if result.get('status') not in ['FAILED'] else "✗"
        print(f"{status_icon} {result['customer_name']:<30} {result.get('status', 'UNKNOWN'):<20} "
              f"Orders: {result.get('orders_loaded', 0):<3} Items: {result.get('items_created', 0):<3}")
    
    if failed_customers > 0:
        print(f"\nFailed Customers:")
        print("-" * 80)
        for result in results:
            if result.get('status') == 'FAILED':
                print(f"✗ {result['customer_name']}: {result.get('error', 'Unknown error')}")
    
    print(f"{'='*80}")

def main():
    """Main entry point"""
    # Set up logging
    logger = setup_logging()
    
    print("=" * 60)
    print("Order Sync V2 - Monday.com Integration")
    print("Enterprise Staging Workflow")
    print("=" * 60)
    
    try:
        # Get database connection
        connection_string = get_db_connection_string()
        
        # Initialize batch processor
        processor = BatchProcessor(connection_string)
        
        # Test connections first
        print("Testing connections...")
        connection_results = processor.test_connections()
        
        if not all(connection_results.values()):
            print("❌ Connection tests failed:")
            for service, success in connection_results.items():
                status = "✓" if success else "✗"
                print(f"  {status} {service}")
            return 1
        
        print("✅ All connections successful")
        
        # Check command line arguments for specific customers
        if len(sys.argv) > 1:
            # Process specific customers from command line
            customer_list = sys.argv[1:]
            print(f"Processing specific customers: {customer_list}")
            results = process_specific_customers(processor, customer_list)
        else:
            # Process all customers with new orders
            print("Processing all customers with new orders...")
            results = process_all_customers(processor)
        
        # Print final summary
        print_final_summary(results)
        
        # Return appropriate exit code
        failed_count = len([r for r in results if r.get('status') == 'FAILED'])
        return 1 if failed_count > 0 else 0
        
    except Exception as e:
        logger.error(f"Critical error in main workflow: {e}")
        print(f"❌ Critical error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
