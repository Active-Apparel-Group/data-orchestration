# ORDERS_UNIFIED Delta Sync V3 - Development

This directory contains the UUID & Hash-Based Change Detection implementation for synchronizing ORDERS_UNIFIED with Monday.com.

## 🎯 Project Overview

A robust, production-ready delta synchronization system that:
- Uses UUID primary keys to eliminate complex multi-column joins
- Implements hash-based change detection (Methods 1 & 2)
- Processes customers in batches with staging-first workflow
- Provides complete audit trail and rollback capability

## 📁 Project Structure

```
dev/orders_unified_delta_sync_v3/
├── 📄 Core Components
│   ├── delta_sync_main.py          # Main orchestrator
│   ├── uuid_manager.py             # UUID operations for ORDERS_UNIFIED
│   ├── change_detector.py          # Hash-based change detection (Methods 1 & 2)
│   ├── customer_batcher.py         # Customer batching logic
│   ├── staging_processor.py        # Staging workflow and database operations
│   └── monday_api_adapter.py       # Monday.com API integration with UUID tracking
│
├── 🧪 testing/
│   ├── test_staging_only.py        # ✅ Staging workflow test (NO API calls)
│   ├── test_greyson_po_4755_api.py # ✅ GREYSON PO 4755 end-to-end test
│   └── test_integrated_workflow.py # Full integration test
│
├── 🔍 debugging/
│   ├── check_customers.py          # Customer data verification
│   ├── check_greyson_po_4755.py    # GREYSON PO 4755 data lookup
│   ├── inspect_schemas.py          # DDL schema inspection
│   └── monday_integration.log      # API integration logs
│
├── ✅ validation/
│   ├── validate_setup.py           # Environment validation
│   └── validate_staging_data.py    # ✅ Staging data validation
│
└── README.md                       # This file
```

## 🎯 **STATUS: STAGING WORKFLOW COMPLETE** ✅

### ✅ Completed Components
- **Customer Batching**: Processes multiple customers with change detection
- **Staging Processor**: Robust data type handling and DDL compliance
- **Schema Validation**: All queries use exact table/column names from DDL
- **Data Type Conversion**: Comprehensive SQL Server compatibility layer
- **Database Operations**: UUID-based joins with IDENTITY column handling

### 🔄 Next Steps
- Complete Monday.com API integration testing
- End-to-end workflow validation with GREYSON PO 4755
- Production deployment preparation

## 🚀 Quick Start

### 1. Prerequisites

Ensure you have:
- Access to ORDERS database
- Monday.com API credentials
- Required Python packages: `pandas`, `pyodbc`, `hashlib`, `uuid`

### 2. Initial Setup

```bash
# Test the pilot case
cd dev/orders_unified_delta_sync_v3/testing
python test_greyson_pilot.py
```

### 3. Development Workflow

1. **Phase 1**: UUID Management
   - Test `uuid_manager.py` 
   - Add UUID column to ORDERS_UNIFIED (coordinate with DBA)

2. **Phase 2**: Change Detection
   - Test `change_detector.py` with GREYSON data
   - Validate Methods 1 & 2 hash comparison

3. **Phase 3**: Staging Workflow
   - Test `staging_processor.py` 
   - Validate customer batching with `customer_batcher.py`

4. **Phase 4**: Monday.com Integration
   - Integrate with existing Monday.com API modules
   - Test master schedule → subitems workflow

5. **Phase 5**: Production Deployment
   - Deploy to `scripts/orders_unified_delta_sync_v3/`
   - Create Kestra workflow

## 🔧 Key Features

### UUID System
- **Non-breaking** UUID column addition to ORDERS_UNIFIED
- UUID-based joins eliminate complex multi-column relationships
- Better performance and reliability

### Hash-Based Change Detection
- **Method 1**: Outer join with merge indicator (comprehensive classification)
- **Method 2**: Hash comparison (quick detection)
- Clear status: NEW, UNCHANGED, CHANGED, DELETED

### Staging-First Workflow
- Customer batching for manageable processing
- Staging tables provide rollback capability
- Complete audit trail of all operations

### Customer Batching
- Process one customer at a time
- Canonical customer mapping (GREYSON vs GREYSON CLOTHIERS)
- Start with NEW records only (Phase 1)

## 🧪 Testing

### GREYSON Pilot Case
The implementation starts with GREYSON PO 4755 as the pilot case:

```bash
python delta_sync_main.py --mode TEST --customer GREYSON --limit 10
```

### Module Testing
Each module has built-in test functions:

```bash
python uuid_manager.py          # Test UUID operations
python change_detector.py       # Test change detection
python customer_batcher.py      # Test customer batching
python staging_processor.py     # Test staging workflow
```

## 📊 Database Schema Changes

### ORDERS_UNIFIED Updates
```sql
-- Add UUID column (non-breaking)
ALTER TABLE [dbo].[ORDERS_UNIFIED] 
ADD [record_uuid] UNIQUEIDENTIFIER DEFAULT NEWID()

-- Add hash column for change detection
ALTER TABLE [dbo].[ORDERS_UNIFIED] 
ADD [record_hash] NVARCHAR(64) NULL

-- Create indexes
CREATE INDEX IX_ORDERS_UNIFIED_record_uuid ON [dbo].[ORDERS_UNIFIED] ([record_uuid])
CREATE INDEX IX_ORDERS_UNIFIED_record_hash ON [dbo].[ORDERS_UNIFIED] ([record_hash])
```

### Staging Table Updates
```sql
-- Add to STG_MON_CustMasterSchedule
ALTER TABLE [dbo].[STG_MON_CustMasterSchedule] 
ADD [source_uuid] UNIQUEIDENTIFIER NULL,
    [source_hash] NVARCHAR(64) NULL,
    [change_type] NVARCHAR(20) NULL -- NEW, UNCHANGED, CHANGED, DELETED
```

## 🔗 Integration Points

### Existing Scripts (Reference Only)
- `scripts/customer_master_schedule/` - Monday.com API patterns
- `scripts/order_staging/` - Staging table operations
- `scripts/customer_master_schedule_subitems/` - Subitem processing

### Existing Infrastructure
- `sql/ddl/deploy_staging_infrastructure.sql` - Staging tables
- `utils/db_helper.py` - Database operations
- `utils/logger_helper.py` - Logging
- `utils/data_mapping.yaml` - Field mappings

## 📋 Implementation Status

- [x] **Project Structure**: Dev folders and initial files created
- [ ] **Phase 1**: UUID system implementation
- [ ] **Phase 2**: Change detection implementation  
- [ ] **Phase 3**: Staging workflow implementation
- [ ] **Phase 4**: Monday.com API integration
- [ ] **Phase 5**: Production deployment

## 🎯 Success Criteria

- Process 1000+ orders efficiently in customer batches
- < 5% error rate with automatic retry logic
- Complete order→subitem workflow in < 30 minutes
- UUID-based joins eliminate complex multi-column joins
- GREYSON PO 4755 pilot case processes successfully

## 📚 Related Documentation

- **Task File**: `tasks/dev/dev-orders_unified_delta_sync_v3.yml`
- **Design Docs**: `docs/design/customer_master_schedule_add_order_design.md`
- **Staging Plan**: `docs/plans/staging_table_refactor_plan.md`
- **Change Detection Methods**: Documented in task file

---

**Next Steps**: Run the pilot test and start Phase 1 implementation! 🚀
