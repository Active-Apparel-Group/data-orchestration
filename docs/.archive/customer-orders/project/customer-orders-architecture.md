# Customer Orders Pipeline - Technical Architecture

## Overview
UUID-based delta detection with staging tables and customer batching approach for Monday.com integration.

## Business Requirements

### Primary Goals
- **Accuracy**: 100% data consistency between ORDERS_UNIFIED and Monday.com
- **Performance**: Process 10,000+ orders efficiently with minimal system impact
- **Reliability**: Zero data loss with complete audit trail and rollback capability
- **Scalability**: Support for multiple customers and seasonal volume spikes

### Test Focus
- **Primary Test Case**: GREYSON PO 4755 end-to-end API integration validation
- **Test Strategy**: Validate 5 records from GREYSON customer, PO 4755 specifically

## Technical Architecture

### Approach
UUID-based delta detection with staging tables and customer batching:

1. **UUID Integration**: Add `record_uuid` to ORDERS_UNIFIED for unique identification
2. **Delta Detection**: Hash-based change detection comparing current vs snapshot
3. **Customer Batching**: Process orders by customer groups for efficiency
4. **Staging Workflow**: Stage → Transform → Monday.com → Production
5. **Audit Trail**: Complete tracking of all changes and processing results

### Hash Pipeline Workflow
```
ORDERS_UNIFIED → ChangeDetector → Hash Generation → Compare with Snapshot → Detect Changes
```

**Hash Generation Process:**
1. **Source**: ORDERS_UNIFIED table (no hash column stored)
2. **Generation**: `change_detector.py` → `_generate_row_hash()`
3. **Method**: SHA256 hash of concatenated field values
4. **Exclusions**: System fields (record_uuid, snapshot_date, row_hash, customer_filter)
5. **Usage**: Change detection by comparing current vs snapshot hashes
6. **Storage**: Hash stored in ORDERS_UNIFIED_SNAPSHOT for comparison

**Change Detection Methods:**
- Method 1: Outer Join with _merge indicator (comprehensive classification)
- Method 2: Hash Comparison (quick detection with field-level analysis)

## Reference Files

### Existing Schemas
- `sql/ddl/tables/orders/dbo_ORDERS_UNIFIED_ddl.sql` - Main source table
- `sql/ddl/tables/orders/dbo_orders_unified_snapshot.sql` - Snapshot/history table
- `sql/ddl/tables/orders/dbo_MON_CustMasterSchedule_ddl.sql` - Monday.com staging

### Field Mappings
- `sql/mappings/orders-unified-comprehensive-mapping.yaml` - Complete field mapping (source of truth)
- `sql/mappings/simple-orders-mapping.yaml` - Simplified mapping for basic operations
- `sql/mappings/customer-canonical.yaml` - Customer name normalization

### GraphQL Templates
- `sql/graphql/mutations/create-master-item.graphql` - Monday.com item creation
- `sql/graphql/queries/get-board-items.graphql` - Existing item queries

## Implementation Phases

### Phase 1: Foundation ✅ COMPLETED
- UUID columns added to ORDERS_UNIFIED
- Snapshot table created with proper schema
- Change detection logic implemented

### Phase 2: Core Processing ✅ COMPLETED  
- Customer batching system implemented
- Hash-based change detection working
- Staging processor with robust data handling

### Phase 3: Integration 🚧 IN PROGRESS
- Monday.com API integration
- End-to-end testing with GREYSON PO 4755
- Performance validation

### Phase 4: Production Deployment 📅 PLANNED
- Schema deployment validation
- Production rollout strategy
- Monitoring and alerting setup

## Success Metrics

### Performance
- Process 10,000+ orders in under 10 minutes
- Change detection completes in under 2 minutes
- API rate limiting compliance (0.1s delays)

### Accuracy
- 100% data consistency validation
- Zero duplicate items in Monday.com
- Complete audit trail for all changes

### Reliability
- Rollback capability for failed batches
- Error handling for all edge cases
- Complete logging and monitoring
