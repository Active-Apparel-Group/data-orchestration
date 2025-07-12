# OPUS Update Boards - TODAY'S ACTION PLAN
# Executive Summary: Immediate 4-hour implementation to get foundational components operational

## 🚀 **IMMEDIATE TASKS (4 Hours)**

### **TASK 1: Extend Staging Tables (30 minutes)** ⚡
**Priority: CRITICAL**

**Action Items:**
1. **Create ALTER TABLE scripts for STG_MON_CustMasterSchedule:**
   ```sql
   ALTER TABLE STG_MON_CustMasterSchedule ADD
       update_operation VARCHAR(50) DEFAULT 'CREATE',
       update_fields NVARCHAR(MAX),
       source_table VARCHAR(100),
       source_query NVARCHAR(MAX),
       update_batch_id VARCHAR(50),
       validation_status VARCHAR(20) DEFAULT 'PENDING',
       validation_errors NVARCHAR(MAX);
   ```

2. **Create ALTER TABLE scripts for STG_MON_CustMasterSchedule_Subitems:**
   ```sql
   ALTER TABLE STG_MON_CustMasterSchedule_Subitems ADD
       update_operation VARCHAR(50) DEFAULT 'CREATE',
       update_fields NVARCHAR(MAX),
       source_table VARCHAR(100),
       source_query NVARCHAR(MAX),
       update_batch_id VARCHAR(50),
       validation_status VARCHAR(20) DEFAULT 'PENDING',
       validation_errors NVARCHAR(MAX);
   ```

3. **Create MON_UpdateAudit table:**
   ```sql
   CREATE TABLE MON_UpdateAudit (
       audit_id INT IDENTITY(1,1) PRIMARY KEY,
       batch_id VARCHAR(50),
       update_operation VARCHAR(50),
       monday_item_id BIGINT,
       monday_board_id BIGINT,
       column_id VARCHAR(100),
       old_value NVARCHAR(MAX),
       new_value NVARCHAR(MAX),
       update_timestamp DATETIME2 DEFAULT GETUTCDATE(),
       rollback_timestamp DATETIME2,
       rollback_reason NVARCHAR(500)
   );
   ```

**Validation:**
- Execute scripts on staging environment
- Test backward compatibility with existing load_boards.py
- Verify new columns accept expected data types

**Files to Create:**
- `db/ddl/updates/extend_staging_tables.sql`
- `db/ddl/updates/create_update_audit.sql`

---

### **TASK 2: Create UpdateOperations Module (2 hours)** ⚡
**Priority: CRITICAL**

**Action Items:**
1. **Create `pipelines/scripts/order_staging/update_operations.py`** 
2. **Implement UpdateOperations class using existing staging infrastructure**
3. **Add `stage_updates_from_query()` method**
4. **Integrate with StagingOperations and MondayApiClient patterns**

**Key Implementation:**
```python
class UpdateOperations:
    def __init__(self, board_id, config_manager=None):
        self.board_id = board_id
        self.config_manager = config_manager or ConfigManager()
        self.staging_ops = StagingOperations()
        self.monday_client = MondayApiClient()
    
    def stage_updates_from_query(self, source_query, update_type='update_items'):
        """Stage updates from SQL query using existing staging infrastructure"""
    
    def validate_staged_updates(self, batch_id):
        """Validate staged updates against Monday.com metadata"""
    
    def process_staged_updates(self, batch_id, dry_run=True):
        """Process staged updates with dry-run capability"""
```

**Validation:**
- Test with sample data
- Verify integration with existing staging infrastructure
- Test dry-run mode functionality

---

### **TASK 3: Test Single Update (1 hour)** ⚡
**Priority: HIGH**

**Action Items:**
1. **Pick test board: 8709134353 (Planning)**
2. **Identify safe test item for updates**
3. **Create simple update query**
4. **Test complete staging workflow**
5. **Validate dry-run mode works correctly**

**Test Query Example:**
```sql
SELECT 
    monday_item_id,
    'In Progress' as order_status
FROM STG_MON_CustMasterSchedule 
WHERE monday_board_id = 8709134353 
AND monday_item_id = [SAFE_TEST_ITEM_ID]
LIMIT 1;
```

**Validation:**
- Dry-run produces detailed report
- No actual Monday.com updates occur in dry-run
- Staging workflow completes successfully

---

### **TASK 4: Document Patterns (30 minutes)** 📝
**Priority: MEDIUM**

**Action Items:**
1. **Document SQL patterns for update queries**
2. **Document UpdateOperations usage patterns**
3. **Create quick reference guide**
4. **Update development documentation**

**Files to Create:**
- `docs/quickref/update_operations_quickref.md`
- `docs/patterns/sql_update_patterns.md`

---

## 📊 **SUCCESS CRITERIA FOR TODAY**

### **Must Achieve:**
- ✅ Staging tables extended with update tracking columns
- ✅ UpdateOperations module created and functional
- ✅ Single update test working in dry-run mode
- ✅ Documentation patterns established

### **Quality Gates:**
- No errors in staging table schema updates
- UpdateOperations integrates cleanly with existing infrastructure
- Dry-run mode generates accurate reports
- Test update workflow completes end-to-end

---

## 🎯 **TOMORROW'S SETUP**

### **Phase 0 Continuation (Next 1-2 days):**
1. **Extend MondayApiClient** with update methods
2. **Add comprehensive validation framework**
3. **Create GraphQL mutation templates**
4. **Begin CLI integration**

### **Weekly Goals:**
- **Week 1:** Complete Phase 0 + Phase 1 (Foundation + GraphQL)
- **Week 2:** Complete Phase 2 + Phase 3 (CLI + Testing)
- **Production Ready:** 2 weeks from today

---

## 🚨 **RISK MITIGATION FOR TODAY**

### **Key Risks:**
1. **Schema changes break existing workflows**
   - **Mitigation:** Test with existing load_boards.py immediately after changes
   - **Rollback:** Have original schema backup ready

2. **UpdateOperations doesn't integrate cleanly**
   - **Mitigation:** Use exact patterns from existing StagingOperations
   - **Fallback:** Implement minimal version first, enhance later

3. **Test updates affect live data**
   - **Mitigation:** Use sandbox board or clearly identified test items
   - **Safety:** Mandatory dry-run mode, no live updates today

---

## 📞 **SUCCESS CHECKPOINTS**

### **Hour 1 Checkpoint:**
- Staging tables extended successfully ✅
- Schema changes tested with existing workflows ✅

### **Hour 3 Checkpoint:**
- UpdateOperations module created ✅
- Integration with staging infrastructure working ✅

### **Hour 4 Checkpoint:**
- Single update test completed in dry-run mode ✅
- Documentation patterns established ✅

**Final Validation:** End-to-end update workflow operational in dry-run mode, ready for Phase 0 continuation tomorrow.
