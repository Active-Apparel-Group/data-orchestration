# Customer Master Schedule - Add Order Workflow Design

**Created:** June 15, 2025  
**Status:** In Development  
**Version:** 1.0

## Overview

This document outlines the design for adding new orders from ORDERS_UNIFIED to the Monday.com Customer Master Schedule board through our MON_CustMasterSchedule staging table.

## Current State Analysis

The existing `add_order.py` file has several issues:
- ❌ Tries to read from `MON_CustMasterSchedule` instead of `ORDERS_UNIFIED`
- ❌ Missing proper field mapping from the YAML configuration
- ❌ Hard-coded board ID (should be dynamic)
- ❌ Incomplete column mapping implementation
- ❌ Missing database update logic for item IDs

## Goal

**Primary Objective:** Add new order records from ORDERS_UNIFIED to Monday.com Customer Master Schedule board and maintain synchronization through MON_CustMasterSchedule table.

## Workflow Design

### Step 1: Identify New Records
```sql
-- Compare ORDERS_UNIFIED with MON_CustMasterSchedule
-- Find records that exist in ORDERS_UNIFIED but not in MON_CustMasterSchedule
SELECT ou.*
FROM [dbo].[ORDERS_UNIFIED] ou
LEFT JOIN [dbo].[MON_CustMasterSchedule] cms 
    ON ou.[AAG ORDER NUMBER] = cms.[AAG ORDER NUMBER]
    AND ou.[CUSTOMER STYLE] = cms.[CUSTOMER STYLE] 
    AND ou.[CUSTOMER'S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS] = cms.[COLOR]
WHERE cms.[AAG ORDER NUMBER] IS NULL
```

### Step 2: Transform Data Using Mapping YAML
- Load `orders_unified_monday_mapping.yaml`
- Apply field transformations:
  - **Direct mappings:** Copy values as-is
  - **Computed fields:** Calculate aggregated values (e.g., TOTAL QTY)
  - **Lookup mappings:** Customer name standardization
  - **Value mappings:** Status transformations

### Step 3: Insert into MON_CustMasterSchedule
- Insert transformed records into MON_CustMasterSchedule table
- **MONDAY_ITEM_ID** remains NULL (will be populated after Monday.com creation)
- Records are now staged for Monday.com upload

### Step 4: Create Monday.com Items
- For each record in MON_CustMasterSchedule where MONDAY_ITEM_ID IS NULL:
  - Determine appropriate group (by customer, season, etc.)
  - Ensure group exists using `ensure_group_exists()`
  - Create item in Monday.com using proper column mapping
  - Receive item_id from Monday.com API response

### Step 5: Update Database with Item IDs
- Update MON_CustMasterSchedule.MONDAY_ITEM_ID with returned item_id
- Mark records as synchronized

## Technical Implementation

### Database Schema Requirements

**MON_CustMasterSchedule Table Structure:**
```sql
-- Primary identification
[AAG ORDER NUMBER] NVARCHAR(MAX)
[CUSTOMER STYLE] NVARCHAR(MAX)  
[COLOR] NVARCHAR(MAX)
[CUSTOMER] NVARCHAR(MAX)

-- Monday.com integration
[MONDAY_ITEM_ID] NVARCHAR(50) NULL  -- Populated after Monday.com creation
[MONDAY_GROUP_ID] NVARCHAR(50) NULL -- Track which group the item belongs to
[CREATED_DATE] DATETIME2 DEFAULT GETDATE()
[UPDATED_DATE] DATETIME2 DEFAULT GETDATE()
[SYNC_STATUS] NVARCHAR(20) DEFAULT 'PENDING' -- PENDING, SYNCED, ERROR

-- All mapped fields from YAML configuration
-- (See orders_unified_monday_mapping.yaml for complete list)
```

### File Structure

```
src/customer_master_schedule/
├── add_order.py              # Main script (to be refactored)
├── order_mapping.py          # YAML mapping logic
├── order_queries.py          # Database query functions  
├── monday_integration.py     # Monday.com API functions
└── README.md                 # Documentation
```

### Core Components

#### 1. Order Mapping Module (`order_mapping.py`)
```python
def load_mapping_config() -> dict
def transform_order_data(order_row: dict, mapping_config: dict) -> dict
def apply_customer_mapping(customer_name: str) -> str
def calculate_total_qty(order_row: dict) -> int
def format_monday_column_values(transformed_data: dict) -> str
```

#### 2. Database Queries Module (`order_queries.py`)
```python
def get_new_orders_from_unified() -> pd.DataFrame
def insert_orders_to_staging(orders_df: pd.DataFrame) -> bool
def get_pending_monday_sync() -> pd.DataFrame  
def update_monday_item_id(order_key: dict, item_id: str) -> bool
def mark_sync_status(order_key: dict, status: str) -> bool
```

#### 3. Monday.com Integration Module (`monday_integration.py`)
```python
def get_board_id_from_name(board_name: str) -> str
def create_order_item(board_id: str, group_id: str, order_data: dict) -> str
def determine_group_name(order_data: dict) -> str
def batch_create_orders(orders_list: list) -> list
```

#### 4. Main Orchestration (`add_order.py`)
```python
def main():
    # Step 1: Get new orders from ORDERS_UNIFIED
    new_orders = get_new_orders_from_unified()
    
    # Step 2: Transform using YAML mapping
    transformed_orders = transform_orders_batch(new_orders)
    
    # Step 3: Insert into MON_CustMasterSchedule  
    insert_orders_to_staging(transformed_orders)
    
    # Step 4: Sync to Monday.com
    sync_pending_orders_to_monday()
    
    # Step 5: Update item IDs
    update_sync_status()
```

## Monday.com Integration Details

### Board Configuration
- **Board Name:** "Customer Master Schedule"
- **Board ID:** Retrieved dynamically from MON_Board_Groups table
- **Group Strategy:** By customer name (e.g., "JOHNNIE O ORDERS", "GREYSON ORDERS")

### Column Mapping Strategy
Based on `orders_unified_monday_mapping.yaml`:

**Direct Mappings (37 fields):**
- `AAG ORDER NUMBER` → `text_mkr5wya6`
- `AAG SEASON` → `dropdown_mkr58de6`
- `PO NUMBER` → `text_mkr5ej2x`
- etc.

**Computed Fields:**
- `Name` = `CUSTOMER_STYLE + COLOR + AAG_ORDER_NUMBER`
- `TOTAL QTY` = Sum of all size columns

**Lookup Mappings:**
- `CUSTOMER_NAME` → `CUSTOMER` (via customer_mapping.yaml)

### API Payload Example
```json
{
  "query": "mutation { create_item(board_id: 9200517329, group_id: \"group_xyz\", item_name: \"JWHD100120WHITEJOO-00505\", column_values: \"{\\\"text_mkr5wya6\\\": \\\"JOO-00505\\\", \\\"dropdown_mkr542p2\\\": {\\\"ids\\\":[12345]}}\", create_labels_if_missing: true) { id name } }"
}
```

## Error Handling & Recovery

### Data Validation
- Validate required fields before Monday.com creation
- Check for duplicate orders in staging table
- Verify customer mapping exists

### Retry Logic
- Retry failed Monday.com API calls (rate limiting, temporary failures)
- Separate error records for manual review
- Maintain audit trail of all operations

### Monitoring
- Log successful/failed operations
- Track sync status in database
- Generate reports on sync performance

## Success Criteria

✅ **Functional Requirements:**
1. Identify new orders from ORDERS_UNIFIED not in MON_CustMasterSchedule
2. Transform data using YAML mapping configuration  
3. Insert transformed records into staging table
4. Create items in Monday.com with proper column values
5. Update staging table with Monday.com item IDs
6. Handle groups creation automatically

✅ **Performance Requirements:**
- Process 100+ orders in batch within 5 minutes
- Handle API rate limiting gracefully
- Minimal impact on production database

✅ **Reliability Requirements:**
- 99% success rate for valid order data
- Complete audit trail of all operations
- Graceful handling of Monday.com API failures

## Implementation Phases

### Phase 1: Core Infrastructure ✅
- [x] Group management system (`add_board_groups.py`)
- [x] Database integration patterns
- [x] YAML mapping configuration

### Phase 2: Data Pipeline (Current)
- [ ] Refactor `add_order.py` into modular components
- [ ] Implement YAML-based field mapping
- [ ] Create database query functions
- [ ] Build Monday.com integration layer

### Phase 3: Production Deployment
- [ ] End-to-end testing with real data
- [ ] Error handling and monitoring
- [ ] Performance optimization
- [ ] Documentation and training

### Phase 4: Enhancement
- [ ] Batch processing optimization
- [ ] Real-time sync capabilities  
- [ ] Advanced error recovery
- [ ] Reporting and analytics

## Dependencies

**External Systems:**
- ORDERS_UNIFIED table (source data)
- MON_CustMasterSchedule table (staging)
- Monday.com Customer Master Schedule board
- MON_Board_Groups table (group management)

**Configuration Files:**
- `orders_unified_monday_mapping.yaml`
- `customer_mapping.yaml`
- Environment variables for database/API access

**Python Modules:**
- `add_board_groups.py` (group management)
- `pandas` (data manipulation)
- `requests` (Monday.com API)
- `yaml` (configuration parsing)

## Next Steps

1. **Immediate:** Refactor `add_order.py` into modular components
2. **Priority:** Implement YAML-based field mapping logic
3. **Testing:** Create test data pipeline with sample orders
4. **Validation:** Verify Monday.com column mappings with actual board structure
