# Staging Table Refactor Plan
## Monday.com Order Sync with Robust Error Handling

**Created:** June 16, 2025  
**Purpose:** Refactor order sync workflow to use staging tables for improved reliability, error handling, and batch processing

---

## 1. Sample Schema Design

### 1.1 Staging Tables (Mirror Production with Status Tracking)

```sql
-- Staging table for main orders
CREATE TABLE [dbo].[STG_MON_CustMasterSchedule] (
    -- All columns from MON_CustMasterSchedule
    [Title] NVARCHAR(MAX) NULL,
    [CUSTOMER] NVARCHAR(MAX) NULL,
    [AAG ORDER NUMBER] NVARCHAR(MAX) NULL,
    -- ... (all other existing columns) ...
    [Item ID] BIGINT NULL,
    
    -- Staging-specific columns
    [stg_batch_id] UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID(),
    [stg_customer_batch] NVARCHAR(100) NULL,
    [stg_status] NVARCHAR(50) DEFAULT 'PENDING', -- PENDING, API_SUCCESS, API_FAILED, PROMOTED
    [stg_monday_item_id] BIGINT NULL,
    [stg_error_message] NVARCHAR(MAX) NULL,
    [stg_created_date] DATETIME2 DEFAULT GETDATE(),
    [stg_processed_date] DATETIME2 NULL
);

-- Staging table for subitems
CREATE TABLE [dbo].[STG_MON_CustMasterSchedule_Subitems] (
    -- All columns from MON_CustMasterSchedule_Subitems
    [parent_item_id] NVARCHAR(MAX) NULL,
    [subitem_id] NVARCHAR(MAX) NULL,
    [subitem_board_id] NVARCHAR(MAX) NULL,
    [Size] NVARCHAR(MAX) NULL,
    [Order Qty] NVARCHAR(MAX) NULL,
    -- ... (all other existing columns) ...
    
    -- Staging-specific columns
    [stg_batch_id] UNIQUEIDENTIFIER NOT NULL,
    [stg_parent_stg_id] BIGINT NULL, -- FK to STG_MON_CustMasterSchedule
    [stg_status] NVARCHAR(50) DEFAULT 'PENDING',
    [stg_monday_subitem_id] BIGINT NULL,
    [stg_monday_subitem_board_id] BIGINT NULL,
    [stg_error_message] NVARCHAR(MAX) NULL,
    [stg_created_date] DATETIME2 DEFAULT GETDATE(),
    [stg_processed_date] DATETIME2 NULL
);
```

### 1.2 Error Tables

```sql
-- Failed API calls for main items
CREATE TABLE [dbo].[ERR_MON_CustMasterSchedule] (
    [err_id] BIGINT IDENTITY(1,1) PRIMARY KEY,
    [original_stg_id] BIGINT NULL,
    [batch_id] UNIQUEIDENTIFIER NULL,
    [customer_batch] NVARCHAR(100) NULL,
    [order_number] NVARCHAR(100) NULL,
    [item_name] NVARCHAR(500) NULL,
    [api_payload] NVARCHAR(MAX) NULL,
    [error_type] NVARCHAR(100) NULL,
    [error_message] NVARCHAR(MAX) NULL,
    [retry_count] INT DEFAULT 0,
    [created_date] DATETIME2 DEFAULT GETDATE(),
    -- Include all original order data for reprocessing
    [original_data] NVARCHAR(MAX) NULL -- JSON of original row
);

-- Failed API calls for subitems
CREATE TABLE [dbo].[ERR_MON_CustMasterSchedule_Subitems] (
    [err_id] BIGINT IDENTITY(1,1) PRIMARY KEY,
    [original_stg_id] BIGINT NULL,
    [parent_item_id] BIGINT NULL,
    [batch_id] UNIQUEIDENTIFIER NULL,
    [size_label] NVARCHAR(50) NULL,
    [order_qty] BIGINT NULL,
    [api_payload] NVARCHAR(MAX) NULL,
    [error_type] NVARCHAR(100) NULL,
    [error_message] NVARCHAR(MAX) NULL,
    [retry_count] INT DEFAULT 0,
    [created_date] DATETIME2 DEFAULT GETDATE(),
    [original_data] NVARCHAR(MAX) NULL
);
```

### 1.3 Batch Tracking Table

```sql
CREATE TABLE [dbo].[MON_BatchProcessing] (
    [batch_id] UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    [customer_name] NVARCHAR(100) NOT NULL,
    [batch_type] NVARCHAR(50) NOT NULL, -- 'ORDERS', 'SUBITEMS'
    [status] NVARCHAR(50) DEFAULT 'STARTED', -- STARTED, ITEMS_CREATED, SUBITEMS_CREATED, PROMOTED, FAILED
    [total_records] INT NULL,
    [successful_records] INT NULL,
    [failed_records] INT NULL,
    [start_time] DATETIME2 DEFAULT GETDATE(),
    [end_time] DATETIME2 NULL,
    [error_summary] NVARCHAR(MAX) NULL
);
```

---

## 2. Code Architecture Outline

### 2.1 Main Workflow Files

```
src/
├── order_staging/
│   ├── __init__.py
│   ├── batch_processor.py       # Main orchestrator
│   ├── staging_operations.py    # Staging table operations
│   ├── monday_api_client.py     # Monday.com API wrapper
│   ├── error_handler.py         # Error logging and retry logic
│   └── promotion_manager.py     # Staging to production promotion
├── order_sync_v2.py            # New main entry point
└── config/
    └── staging_config.yaml      # Batch sizes, retry limits, etc.
```

### 2.2 Key Functions Overview

```python
# batch_processor.py
class BatchProcessor:
    def process_customer_batch(customer_name):
        """Main workflow orchestrator"""
        
    def load_new_orders_to_staging(customer_name):
        """Step 1: Load new orders to staging"""
        
    def create_monday_items_from_staging():
        """Step 2: Create Monday.com items"""
        
    def create_monday_subitems_from_staging():
        """Step 3: Create Monday.com subitems"""
        
    def promote_successful_records():
        """Step 4: Move successful records to production"""
        
    def cleanup_staging_for_customer():
        """Step 5: Clear staging for next batch"""

# staging_operations.py
def insert_orders_to_staging(orders_df, customer_batch, batch_id):
    """Insert transformed orders to staging table"""
    
def get_pending_staging_orders(batch_id):
    """Get orders ready for Monday.com API"""
    
def update_staging_with_monday_id(stg_id, monday_item_id):
    """Update staging record with API response"""

# monday_api_client.py
class MondayApiClient:
    def create_item_with_retry(item_data):
        """Create item with retry logic"""
        
    def create_subitem_with_retry(parent_id, subitem_data):
        """Create subitem with retry logic"""

# error_handler.py
def log_api_error(stg_record, error_details, error_type):
    """Log failed API call to error table"""
    
def retry_failed_records(max_retries=3):
    """Retry failed records with exponential backoff"""

# promotion_manager.py
def promote_staging_to_production(batch_id):
    """Move successful records from staging to production tables"""
    
def archive_successful_staging_records(batch_id):
    """Archive or delete successful staging records"""
```

---

## 3. Detailed Implementation Checklist

### Phase 1: Database Schema Setup ✅ COMPLETED
- [x] **1.1** Create staging tables (STG_MON_CustMasterSchedule, STG_MON_CustMasterSchedule_Subitems)
- [x] **1.2** Create error tables (ERR_MON_CustMasterSchedule, ERR_MON_CustMasterSchedule_Subitems)
- [x] **1.3** Create batch tracking table (MON_BatchProcessing)
- [x] **1.4** Add indexes on staging tables (batch_id, customer_batch, status)
- [x] **1.5** Add foreign key constraints between staging tables
- [x] **1.6** Create deployment script and utility procedures

### Phase 2: Core Infrastructure ✅ COMPLETED
- [x] **2.1** Create staging_operations.py with database operations
- [x] **2.2** Create monday_api_client.py with retry logic
- [x] **2.3** Create error_handler.py for error logging
- [x] **2.4** Create staging_config.py for configuration (not YAML - Python module)
- [x] **2.5** Create batch_processor.py main orchestrator
- [x] **2.6** Create order_sync_v2.py new main entry point

### Phase 3: Batch Processing Logic
- [ ] **3.1** Create batch_processor.py main orchestrator
- [ ] **3.2** Implement customer batch detection logic
- [ ] **3.3** Implement order loading to staging (with transformation)
- [ ] **3.4** Implement Monday.com item creation from staging
- [ ] **3.5** Implement subitem unpivoting and creation logic
- [ ] **3.6** Implement promotion logic (staging -> production)
- [ ] **3.7** Implement cleanup logic for completed batches

### Phase 4: Error Handling & Monitoring
- [ ] **4.1** Implement comprehensive error logging
- [ ] **4.2** Add retry logic with exponential backoff
- [ ] **4.3** Create error summary reporting
- [ ] **4.4** Add batch status tracking and monitoring
- [ ] **4.5** Create manual retry mechanism for failed records
- [ ] **4.6** Add data validation before API calls

### Phase 5: Integration & Testing
- [ ] **5.1** Create order_sync_v2.py main entry point
- [ ] **5.2** Integration testing with small customer batches
- [ ] **5.3** Test error scenarios (API failures, network issues)
- [ ] **5.4** Test retry mechanisms
- [ ] **5.5** Performance testing with larger batches
- [ ] **5.6** Create rollback procedures for failed batches

### Phase 6: Migration & Deployment
- [ ] **6.1** Backup existing MON_CustMasterSchedule data
- [ ] **6.2** Create migration script from old to new workflow
- [ ] **6.3** Parallel run testing (old vs new workflow)
- [ ] **6.4** Create operational runbooks
- [ ] **6.5** Train users on new error handling procedures
- [ ] **6.6** Deploy to production with monitoring

---

## 4. Workflow Sequence

```
1. Customer Batch Selection
   ├── Query ORDERS_UNIFIED for new orders
   ├── Group by customer
   └── Process one customer at a time

2. Load to Staging
   ├── Transform orders using YAML mapping
   ├── Insert to STG_MON_CustMasterSchedule
   ├── Generate batch_id and customer_batch
   └── Log batch start in MON_BatchProcessing

3. Create Monday.com Items
   ├── For each staging record (status='PENDING')
   ├── Call Monday.com API to create item
   ├── On success: update stg_status='API_SUCCESS', store monday_item_id
   ├── On failure: update stg_status='API_FAILED', log to error table
   └── Update batch tracking with item creation results

4. Create Subitems
   ├── For each successful item (stg_status='API_SUCCESS')
   ├── Join to ORDERS_UNIFIED, unpivot sizes
   ├── Insert size records to STG_MON_CustMasterSchedule_Subitems
   ├── Create subitems via Monday.com API
   ├── Handle success/failure same as items
   └── Update batch tracking with subitem creation results

5. Promote to Production
   ├── Move all successful records to production tables
   ├── Update stg_status='PROMOTED'
   ├── Update batch status='PROMOTED'
   └── Generate success summary

6. Cleanup
   ├── Archive/delete successful staging records
   ├── Keep failed records for manual review
   └── Clear staging for next customer batch
```

---

## 5. Benefits of This Approach

- **Atomicity:** Each customer batch is processed as a unit
- **Reliability:** Failed records don't corrupt production data
- **Auditability:** Complete tracking of what succeeded/failed
- **Retry Logic:** Failed records can be retried without duplicates
- **Performance:** Bulk operations instead of row-by-row
- **Monitoring:** Clear visibility into batch processing status
- **Rollback:** Easy to rollback failed batches
- **Scalability:** Can process multiple customers in parallel (future)

---

## 6. Risk Mitigation

- **API Rate Limits:** Implement throttling and retry with backoff
- **Network Issues:** Comprehensive retry logic with exponential backoff
- **Data Corruption:** Staging isolation prevents production corruption
- **Partial Failures:** Failed records isolated and trackable
- **Performance:** Batch processing reduces API call overhead
- **Monitoring:** Real-time tracking of batch progress and failures

---

## 7. Success Metrics

- **Reliability:** >99% success rate for API calls
- **Performance:** Process 1000+ orders per hour
- **Error Recovery:** <1% manual intervention required
- **Data Quality:** Zero production data corruption incidents
- **Auditability:** 100% traceability of all operations

---

This plan provides a robust, enterprise-grade approach to your Monday.com integration with proper error handling, monitoring, and scalability.
