# TARGETED ORDER PROCESSING - QUICK REFERENCE

## Overview
The enhanced `BatchProcessor.process_specific_po()` method allows safe, targeted processing of orders with flexible filtering. All parameters are optional, but at least one must be provided for safety.

## Method Signature
```python
processor.process_specific_po(
    customer_name=None,     # Filter by customer name (e.g., 'GREYSON CLOTHIERS')
    po_number=None,         # Filter by PO number (e.g., '4755')
    aag_season=None,        # Filter by AAG SEASON (e.g., '2026 SPRING')
    customer_season=None    # Filter by CUSTOMER SEASON (e.g., 'SP26')
)
```

## Common Usage Patterns

### 1. Process Specific PO for Customer (Most Common)
```python
result = processor.process_specific_po(
    customer_name='GREYSON CLOTHIERS',
    po_number='4755'
)
```

### 2. Process All Orders for Customer + Season
```python
result = processor.process_specific_po(
    customer_name='GREYSON CLOTHIERS',
    customer_season='SP26'
)
```

### 3. Process Any Customer with Specific PO
```python
result = processor.process_specific_po(
    po_number='4755'
)
```

### 4. Process by AAG Season
```python
result = processor.process_specific_po(
    customer_name='GREYSON CLOTHIERS',
    aag_season='2026 SPRING'
)
```

## Return Value
The method returns a dictionary:
```python
{
    'success': True/False,           # Whether processing succeeded
    'batch_id': 'unique_id',         # Batch identifier for tracking
    'orders_loaded': 25,             # Number of orders loaded to staging
    'items_created': 25,             # Number of Monday.com items created
    'errors': 0,                     # Number of errors encountered
    'status': 'COMPLETED',           # Final batch status
    'error': 'error message'         # Error details if success=False
}
```

## How to Run for GREYSON PO 4755

### Option A: Use the Ready-Made Script
```bash
cd dev/order_staging
python run_greyson_po_4755.py
```

### Option B: Interactive Python
```python
from order_staging.batch_processor import BatchProcessor

# Initialize
processor = BatchProcessor()

# Test connections
status = processor.test_connections()
print(f"Connections: {status}")

# Process GREYSON PO 4755
result = processor.process_specific_po(
    customer_name='GREYSON CLOTHIERS',
    po_number='4755'
)

print(f"Result: {result}")
```

## Safety Features

- ✅ **No Accidental Bulk Processing** - Required filter validation
- ✅ **Targeted Processing Only** - Precise control over what gets processed  
- ✅ **Connection Validation** - Tests before processing
- ✅ **Comprehensive Logging** - Full audit trail
- ✅ **Error Recovery** - Graceful handling of failures

## Performance Enhancements

- **Ultra-Fast Bulk Insert**: >1000 records/second (vs 12-14 records/sec previously)
- **Batch Processing**: Group orders by customer for API efficiency
- **Staging Tables**: Failed API calls don't corrupt production data
