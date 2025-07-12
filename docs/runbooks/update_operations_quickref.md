# OPUS Update Boards - Quick Reference Guide
**Monday.com Bidirectional Data Flow Implementation**  
*Date: 2025-06-30*  
*Reference: OPUS_dev_update_boards.yaml*

## 🚀 **Quick Start Commands**

### **1. Deploy Database Schema**
```sql
-- Execute DDL deployment
EXEC('db/ddl/updates/deploy_opus_update_boards.sql')

-- Validate deployment
EXEC('db/ddl/updates/validate_ddl_changes.sql')
```

### **2. Test Single Update Workflow**
```bash
# Run comprehensive test
python tests/debug/test_single_update_workflow.py

# Expected output: Infrastructure ready for Phase 1
```

### **3. Create Update Operations**
```python
from pipelines.utils.update_operations import UpdateOperations

# Initialize for Planning board
update_ops = UpdateOperations(8709134353)

# Stage updates from query
result = update_ops.stage_updates_from_query(
    source_query="SELECT monday_item_id, 'Shipped' as status FROM planning",
    update_type='update_items'
)

# Validate staged data
validation = update_ops.validate_staged_updates(result['batch_id'])

# Process in dry-run mode (MANDATORY for safety)
processing = update_ops.process_staged_updates(
    batch_id=result['batch_id'],
    dry_run=True  # Never set to False without approval
)
```

## 📋 **SQL Update Patterns**

### **Basic Item Updates**
```sql
-- Update order status
SELECT 
    monday_item_id,
    'Shipped' as order_status,
    GETDATE() as shipped_date
FROM VW_OrderUpdates
WHERE status_changed = 1;
```

### **Quantity Updates**
```sql
-- Update shipped quantities
SELECT 
    monday_item_id,
    shipped_quantity,
    remaining_quantity
FROM VW_ShipmentUpdates
WHERE shipment_date >= DATEADD(day, -1, GETDATE());
```

### **Batch Updates with Validation**
```sql
-- Complex batch update with business rules
SELECT 
    monday_item_id,
    CASE 
        WHEN shipped_qty >= order_qty THEN 'Complete'
        WHEN shipped_qty > 0 THEN 'Partial'
        ELSE 'Pending'
    END as order_status,
    shipped_qty,
    order_qty - shipped_qty as remaining_qty
FROM VW_OrderStatus
WHERE last_updated >= DATEADD(hour, -1, GETDATE())
AND monday_item_id IS NOT NULL;
```

## 🛡️ **Safety Patterns**

### **Mandatory Dry-Run**
```python
# ALWAYS start with dry-run=True
processing_result = update_ops.process_staged_updates(
    batch_id=batch_id,
    dry_run=True  # REQUIRED - never remove without approval
)

# Review results before executing
if processing_result['success_rate'] >= 95:
    print("Ready for execution")
else:
    print("Review errors before proceeding")
```

### **Validation Checks**
```python
# Comprehensive validation before processing
validation_result = update_ops.validate_staged_updates(batch_id)

required_checks = [
    validation_result['success'],
    validation_result['success_rate'] >= 95,
    validation_result['invalid_records'] == 0
]

if all(required_checks):
    print("Validation passed - safe to proceed")
else:
    print("Validation failed - do not proceed")
```

### **Rollback Procedures**
```sql
-- Rollback batch if needed
EXEC SP_RollbackBatch 
    @batch_id = 'OPUS_update_items_20250630_143022_abc123de',
    @rollback_reason = 'Data correction required';

-- Verify rollback
SELECT * FROM VW_UpdateOperationSummary 
WHERE batch_id = 'OPUS_update_items_20250630_143022_abc123de';
```

## 📊 **Board Configuration Reference**

### **Planning Board (8709134353)**
```json
{
  "update_config": {
    "update_items": {
      "enabled": true,
      "batch_size": 50,
      "rate_limit_delay": 0.1,
      "validation_rules": {
        "required_fields": ["monday_item_id"],
        "max_batch_size": 100,
        "allowed_columns": ["status", "shipped_quantity"]
      }
    }
  },
  "script_mappings": {
    "update_items": {
      "status_mkp44k3t": "order_status",
      "numbers_mkrapgwv": "shipped_quantity"
    }
  }
}
```

### **Fabric Library Board (8446553051)**
```json
{
  "update_config": {
    "update_items": {
      "enabled": true,
      "batch_size": 25,
      "validation_rules": {
        "required_fields": ["monday_item_id", "fabric_status"],
        "allowed_columns": ["fabric_status", "inventory_count"]
      }
    }
  }
}
```

## 🔧 **Troubleshooting Guide**

### **Common Issues**

#### **Import Errors**
```python
# ✗ WRONG - will cause ModuleNotFoundError
from sql.something import Module

# ✓ CORRECT - use utils/ folder
from utils.db_helper import get_connection
```

#### **Database Connection Issues**
```python
# Check available databases
config = db.load_config()
print(config['databases'].keys())

# Use correct database
with db.get_connection('dms') as conn:  # Not 'monday' or 'staging'
    # database operations
```

#### **Staging Table Not Found**
```sql
-- Verify staging tables exist with update columns
SELECT TABLE_NAME, COLUMN_NAME 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME IN ('STG_MON_CustMasterSchedule', 'STG_MON_CustMasterSchedule_Subitems')
AND COLUMN_NAME = 'update_operation';

-- If empty, run deployment script
-- EXEC('db/ddl/updates/deploy_opus_update_boards.sql')
```

#### **Validation Failures**
```python
# Debug validation issues
validation_result = update_ops.validate_staged_updates(batch_id)

for result in validation_result['validation_results']:
    if result['validation_status'] == 'INVALID':
        print(f"Item {result['monday_item_id']}: {result['errors']}")
```

### **Performance Optimization**

#### **Batch Size Guidelines**
- **Small batches** (≤25): Complex updates, high validation requirements
- **Medium batches** (26-50): Standard updates, moderate complexity
- **Large batches** (51-100): Simple updates, high confidence data

#### **Rate Limiting**
```python
# Conservative rate limiting for API protection
update_config = {
    'rate_limit_delay': 0.2,  # 200ms between calls
    'max_concurrent': 1,      # Sequential processing only
    'circuit_breaker': True   # Stop on multiple failures
}
```

## 🎯 **Phase 1 Preparation**

### **GraphQL Template Structure**
```
integrations/graphql/
├── mutations/
│   ├── update_item.graphql
│   ├── update_subitem.graphql
│   ├── update_group.graphql
│   └── batch_update_items.graphql
├── queries/
│   ├── get_items_for_update.graphql
│   └── validate_item_exists.graphql
└── loader.py
```

### **Monday.com API Integration**
```python
# Phase 1 implementation pattern
class MondayApiClient:
    def update_item(self, board_id, item_id, column_values):
        # GraphQL mutation: change_multiple_column_values
        # Rate limiting: 0.1s delay between calls
        # Error handling: exponential backoff
        # Audit logging: before/after values
        pass
    
    def batch_update_items(self, updates):
        # Batch processing with rate limiting
        # Comprehensive error collection
        # Progress reporting
        pass
```

### **CLI Integration**
```bash
# Phase 2 command patterns
python update_monday_items.py --board-id 8709134353 --update-type update_items --dry-run
python update_monday_items.py --board-id 8709134353 --update-type update_items --execute
python update_monday_items.py --validate-batch ABC123DEF456
python update_monday_items.py --rollback-batch ABC123DEF456 --reason "Data error"
```

## 📈 **Success Metrics**

### **Phase 0 Completion Criteria**
- ✅ Staging tables extended with update columns
- ✅ UpdateOperations module functional
- ✅ Single update test passes with >95% success
- ✅ Dry-run mode generates accurate reports
- ✅ Validation framework catches schema mismatches
- ✅ Audit trail captures all operations

### **Production Readiness Checklist**
- [ ] Dry run mode working (all operations default to dry-run=True)
- [ ] Validation passing for all update types
- [ ] Rate limiting tested (no API throttling errors)
- [ ] Error handling comprehensive (all scenarios handled gracefully)
- [ ] Rollback tested (capability verified with test data)
- [ ] Audit trail complete (all updates logged with before/after values)
- [ ] Performance acceptable (>100 updates/minute sustained throughput)
- [ ] Documentation complete (user guides, API docs, troubleshooting)

## 🚨 **Critical Reminders**

### **NEVER DO THIS**
- ❌ Set `dry_run=False` without explicit approval
- ❌ Process updates without validation
- ❌ Skip batch size limits (>100 records)
- ❌ Ignore API rate limiting
- ❌ Update production data in testing

### **ALWAYS DO THIS**
- ✅ Start with `dry_run=True` (mandatory safety)
- ✅ Validate staged data before processing
- ✅ Check success rates before execution
- ✅ Log all operations to audit trail
- ✅ Use conservative batch sizes and rate limits

---

## 📞 **Support & Next Steps**

**Current Status:** Phase 0 Foundation Complete ✅  
**Next Phase:** Phase 1 GraphQL Operations (1 day)  
**Timeline:** Production ready in 2 weeks  

**Immediate Focus:**
1. Execute immediate action plan (today)
2. Validate single update workflow
3. Proceed to GraphQL template creation
4. Begin Monday.com API integration

**Documentation:** See `docs/changelogs/updateBoards/OPUS_update_boards.md` for comprehensive implementation guide.
