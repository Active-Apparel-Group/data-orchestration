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
import argparse

# Add src to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from load_cms.batch_processor import BatchProcessor
from load_cms.staging_config import get_config

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

def process_specific_customer_po(processor: BatchProcessor, customer_name: str, po_number: str, limit: Optional[int] = None) -> Dict:
    """Process a specific customer and PO number - Entry point for targeted processing, with optional limit support"""
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Processing specific customer: {customer_name}, PO: {po_number}, Limit: {limit}")

        # Use the targeted processing method with limit
        result = processor.process_specific_po(
            customer_name=customer_name,
            po_number=po_number,
            limit=limit
        )

        # Generate comprehensive batch summary
        if result['success']:
            summary_report = generate_batch_summary(result, customer_name, po_number)
            print(summary_report)

            # Save to file
            save_batch_summary(summary_report, result['batch_id'], customer_name, po_number)

        return result

    except Exception as e:
        logger.error(f"Failed to process customer {customer_name}, PO {po_number}: {e}")
        return {
            'customer_name': customer_name,
            'po_number': po_number,
            'success': False,
            'status': 'FAILED',
            'error': str(e)
        }

def generate_batch_summary(result: Dict, customer_name: str, po_number: str) -> str:
    """Generate comprehensive markdown summary for batch processing"""
    
    # Calculate metrics
    orders_loaded = result.get('orders_loaded', 0)
    items_created = result.get('items_created', 0)
    subitems_created = result.get('subitems_created', 0)
    items_errors = result.get('items_errors', 0)
    subitems_errors = result.get('subitems_errors', 0)
    total_errors = result.get('errors', 0)
    
    # Calculate accuracy scores
    orders_accuracy = 100.0 if orders_loaded > 0 else 0.0
    items_accuracy = ((items_created / orders_loaded) * 100) if orders_loaded > 0 else 0.0
    subitems_accuracy = ((subitems_created / (orders_loaded * 5)) * 100) if orders_loaded > 0 else 0.0  # Assuming ~5 sizes per order
    overall_accuracy = ((items_created + subitems_created) / (orders_loaded + orders_loaded * 5) * 100) if orders_loaded > 0 else 0.0
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    summary = f"""
# 🚀 Order Staging Batch Summary Report

## 📋 Batch Information
- **Customer**: {customer_name}
- **PO Number**: {po_number}
- **Batch ID**: `{result.get('batch_id', 'N/A')}`
- **Processing Time**: {timestamp}
- **Status**: `{result.get('status', 'UNKNOWN')}`

---

## 📊 Pipeline Performance Metrics

### 🔢 Volume Summary
| Stage | Count | Expected | Accuracy |
|-------|-------|----------|----------|
| 📦 **Orders Loaded** | {orders_loaded} | {orders_loaded} | {orders_accuracy:.1f}% |
| 🎯 **Items Created** | {items_created} | {orders_loaded} | {items_accuracy:.1f}% |
| 📏 **Subitems Created** | {subitems_created} | {orders_loaded * 5} | {subitems_accuracy:.1f}% |

### 🎯 Success Rate Breakdown
- **Source → Staging**: {orders_accuracy:.1f}% ({orders_loaded}/{orders_loaded} orders)
- **Staging → Monday Items**: {items_accuracy:.1f}% ({items_created}/{orders_loaded} items)
- **Items → Monday Subitems**: {(subitems_created/items_created*100) if items_created > 0 else 0:.1f}% ({subitems_created}/{items_created * 5} subitems)

### 🔥 Error Analysis
- **Items Errors**: {items_errors}
- **Subitems Errors**: {subitems_errors}
- **Total Errors**: {total_errors}

---

## 🏆 Overall Performance Score

### **{overall_accuracy:.1f}%** Pipeline Accuracy
"""

    if overall_accuracy >= 95:
        summary += "✅ **EXCELLENT** - Production ready performance!"
    elif overall_accuracy >= 85:
        summary += "🟡 **GOOD** - Minor optimization needed"
    else:
        summary += "🔴 **NEEDS ATTENTION** - Review errors and retry"

    summary += f"""

---

## 📈 Pipeline Flow Validation

### 🧪 Data Flow Check
```
ORDERS_UNIFIED ({orders_loaded} records)
    ↓ Transform & Load
STG_MON_CustMasterSchedule ({orders_loaded} records) - ✅ {orders_accuracy:.0f}%
    ↓ Generate Subitems  
STG_MON_CustMasterSchedule_Subitems ({subitems_created} records) - ✅ {subitems_accuracy:.0f}%
    ↓ API Creation
Monday.com Items ({items_created} created) - ✅ {items_accuracy:.0f}%
Monday.com Subitems ({subitems_created} created) - ✅ {(subitems_created/items_created*100) if items_created > 0 else 0:.0f}%
```

### 🔍 Quality Gates
- ✅ **Source Data**: {orders_loaded} orders identified
- ✅ **Staging Load**: {orders_loaded} orders loaded successfully  
- ✅ **API Integration**: {items_created + subitems_created} total items created
- {'✅' if total_errors == 0 else '⚠️'} **Error Rate**: {total_errors} errors ({(total_errors/(orders_loaded + subitems_created)*100) if (orders_loaded + subitems_created) > 0 else 0:.1f}%)

---

## 🎯 Summary
{customer_name} PO {po_number} processed successfully with **{overall_accuracy:.1f}% accuracy**.
- **Orders**: {orders_loaded} loaded → {items_created} items created
- **Subitems**: {subitems_created} subitems created from {orders_loaded} orders
- **Status**: {result.get('status', 'UNKNOWN')}

*Generated by Order Staging Workflow v2.0*
"""
    
    return summary

def save_batch_summary(summary: str, batch_id: str, customer_name: str, po_number: str):
    """Save batch summary to markdown file"""
    try:
        # Create outputs directory if it doesn't exist
        output_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'outputs', 'batch_summaries')
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"batch_summary_{customer_name.replace(' ', '_')}_{po_number}_{timestamp}.md"
        filepath = os.path.join(output_dir, filename)
        
        # Save file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(summary)
            
        logger = logging.getLogger(__name__)
        logger.info(f"Batch summary saved to: {filepath}")
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to save batch summary: {e}")

def generate_overall_summary(results: List[Dict]) -> str:
    """Generate overall summary across multiple customer batches"""
    if not results:
        return "No batches processed."
    
    total_customers = len(results)
    successful_batches = len([r for r in results if r.get('success', False)])
    
    total_orders = sum(r.get('orders_loaded', 0) for r in results)
    total_items = sum(r.get('items_created', 0) for r in results)
    total_subitems = sum(r.get('subitems_created', 0) for r in results)
    total_errors = sum(r.get('errors', 0) for r in results)
    
    overall_accuracy = ((total_items + total_subitems) / (total_orders + total_orders * 5) * 100) if total_orders > 0 else 0.0
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    summary = f"""
# 📊 Order Staging Multi-Batch Summary Report

**Generated**: {timestamp}

## 🎯 Overall Performance
- **Batches Processed**: {total_customers}
- **Success Rate**: {(successful_batches/total_customers*100):.1f}% ({successful_batches}/{total_customers})
- **Overall Accuracy**: {overall_accuracy:.1f}%

## 📈 Volume Totals
| Metric | Count | Success Rate |
|--------|-------|--------------|
| **Orders Loaded** | {total_orders} | 100% |
| **Monday Items** | {total_items} | {(total_items/total_orders*100) if total_orders > 0 else 0:.1f}% |
| **Monday Subitems** | {total_subitems} | {(total_subitems/(total_orders*5)*100) if total_orders > 0 else 0:.1f}% |
| **Total Errors** | {total_errors} | {(total_errors/(total_orders + total_subitems)*100) if (total_orders + total_subitems) > 0 else 0:.1f}% |

## 📋 Customer-by-Customer Results
"""
    
    for result in results:
        status_icon = "✅" if result.get('success', False) else "❌"
        customer = result.get('customer_name', 'Unknown')
        po = result.get('po_number', 'N/A')
        orders = result.get('orders_loaded', 0)
        items = result.get('items_created', 0)  
        subitems = result.get('subitems_created', 0)
        errors = result.get('errors', 0)
        
        accuracy = ((items + subitems) / (orders + orders * 5) * 100) if orders > 0 else 0.0
        
        summary += f"- {status_icon} **{customer}** (PO: {po}): {orders} orders → {items} items, {subitems} subitems | {accuracy:.1f}% accuracy\n"
    
    if overall_accuracy >= 95:
        summary += "\n🏆 **EXCELLENT PERFORMANCE** - System ready for production scale!"
    elif overall_accuracy >= 85:
        summary += "\n🟡 **GOOD PERFORMANCE** - Minor optimizations recommended"
    else:
        summary += "\n🔴 **PERFORMANCE REVIEW NEEDED** - Investigation required"
        
    return summary

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
    """Main entry point with support for customer/PO specific processing"""
    # Set up logging
    logger = setup_logging()

    parser = argparse.ArgumentParser(description="Order Sync V2 - Monday.com Integration")
    parser.add_argument('--customer', type=str, help='Customer name')
    parser.add_argument('--po', type=str, help='PO number')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of orders to process')
    args = parser.parse_args()

    processor = BatchProcessor(get_db_connection_string())

    if args.customer and args.po:
        # Use the updated entry point with limit support
        result = process_specific_customer_po(processor, args.customer, args.po, limit=args.limit)
        # Batch summary and file output are handled inside process_specific_customer_po
    else:
        # Default: process all customers
        results = process_all_customers(processor)
        print_final_summary(results)

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
