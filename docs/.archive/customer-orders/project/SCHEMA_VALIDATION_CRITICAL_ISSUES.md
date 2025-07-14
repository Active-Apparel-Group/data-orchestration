# CRITICAL: Schema Validation Issues Found
## Milestone 1.1 Status: INCOMPLETE

**Date**: January 20, 2024  
**Status**: ❌ INCOMPLETE - Critical schema discrepancies identified  
**Revised Completion**: 50% (down from claimed 100%)

---

## 🚨 **CRITICAL ISSUES IDENTIFIED**

### **Issue 1: Field Name Mismatches Throughout YAML Mapping**

**Problem**: Our comprehensive YAML mapping file uses incorrect field names that don't exist in actual DDL schemas.

**Examples**:
```yaml
# YAML Mapping (WRONG):
field_mappings:
  - source: "CUSTOMER NAME"
    target: "customer_name"  # ❌ WRONG
    
  - source: "AAG ORDER NUMBER"  
    target: "aag_order_number"  # ❌ WRONG
    
  - source: "CUSTOMER STYLE"
    target: "customer_style"  # ❌ WRONG

# Actual DDL Schema (CORRECT):
[CUSTOMER] NVARCHAR(200) NULL,           # ✅ CORRECT field name
[AAG ORDER NUMBER] NVARCHAR(200) NULL,  # ✅ CORRECT field name  
[STYLE] NVARCHAR(200) NULL,              # ✅ CORRECT (not CUSTOMER STYLE)
```

**Impact**: Every field mapping in our YAML is potentially wrong.

### **Issue 2: Missing ORDERS_UNIFIED_STAGING Table**

**Problem**: No staging table exists for ORDERS_UNIFIED source data.

**Expected Architecture**:
```
ORDERS_UNIFIED → ORDERS_UNIFIED_STAGING → STG_MON_CustMasterSchedule → MON_CustMasterSchedule
```

**Actual Architecture** (Missing Layer):
```
ORDERS_UNIFIED → ??? → STG_MON_CustMasterSchedule → MON_CustMasterSchedule
                 ❌ MISSING STAGING LAYER
```

**Impact**: No intermediate validation/transformation layer for source data.

### **Issue 3: Table Name Case Inconsistencies**

**YAML Uses** (Wrong):
- `stg_mon_custmasterschedule` (lowercase/snake_case)
- `stg_mon_custmasterschedule_subitems` (lowercase/snake_case)

**DDL Reality** (Correct):
- `STG_MON_CustMasterSchedule` (PascalCase)
- `STG_MON_CustMasterSchedule_Subitems` (PascalCase)

### **Issue 4: Staging Column Mismatches**

**Subitems Staging Table Issues**:

**YAML Expects**:
```yaml
- source: "AAG ORDER NUMBER"
  target: "parent_aag_order_number"  # ❌ WRONG
```

**DDL Reality**:
```sql
[stg_source_order_number] NVARCHAR(100) NULL, -- ✅ CORRECT field name
[stg_source_style] NVARCHAR(100) NULL,
[stg_source_color] NVARCHAR(100) NULL,
```

---

## 📊 **ACTUAL vs DOCUMENTED SCHEMAS**

### **STG_MON_CustMasterSchedule (84 total columns)**
- **Production fields**: 75 (mirror of MON_CustMasterSchedule)
- **Staging fields**: 9 technical columns
  - `stg_id` (IDENTITY PRIMARY KEY)
  - `stg_batch_id` (UNIQUEIDENTIFIER)
  - `stg_customer_batch` (NVARCHAR(100))
  - `stg_status` (NVARCHAR(50)) - PENDING/API_SUCCESS/API_FAILED/PROMOTED
  - `stg_monday_item_id` (BIGINT)
  - `stg_error_message` (NVARCHAR(MAX))
  - `stg_api_payload` (NVARCHAR(MAX))
  - `stg_retry_count` (INT)
  - `stg_created_date` (DATETIME2)
  - `stg_processed_date` (DATETIME2)

### **STG_MON_CustMasterSchedule_Subitems (27 total columns)**
- **Production fields**: 13 (mirror of MON_CustMasterSchedule_Subitems)
- **Staging fields**: 14 technical columns including:
  - `stg_parent_stg_id` (FK to parent staging table)
  - `stg_source_order_number` (from ORDERS_UNIFIED)
  - `stg_source_style` (from ORDERS_UNIFIED)
  - `stg_source_color` (from ORDERS_UNIFIED)
  - `stg_size_label` (cleaned size)
  - `stg_order_qty_numeric` (numeric quantity)

### **MON_CustMasterSchedule (75 fields)**
Key business fields:
- `[CUSTOMER]`, `[AAG ORDER NUMBER]`, `[STYLE]`, `[COLOR]`
- `[ORDER QTY]`, `[PACKED QTY]`, `[SHIPPED QTY]`
- Date fields: `[ORDER DATE PO RECEIVED]`, `[CUSTOMER REQ IN DC DATE]`
- Pricing: `[CUSTOMER PRICE]`, `[EX WORKS (USD)]`, `[FINAL FOB (USD)]`

### **MON_CustMasterSchedule_Subitems (13 fields)**
Size breakdown fields:
- `[Size]`, `[Order Qty]`, `[Cut Qty]`, `[Sew Qty]`
- `[Packed Qty]`, `[Shipped Qty]`
- Relationship: `[parent_item_id]`, `[subitem_id]`

---

## 🔧 **REQUIRED CORRECTIONS**

### **1. Fix YAML Field Mappings**
Update `sql/mappings/orders_unified_comprehensive_pipeline.yaml` with correct field names:

```yaml
staging_layer:
  tables:
    main_staging:
      name: "STG_MON_CustMasterSchedule"  # Correct case
      
      field_mappings:
        - source: "AAG ORDER NUMBER"
          target: "[AAG ORDER NUMBER]"  # Use exact DDL field names
          
        - source: "CUSTOMER NAME"  
          target: "[CUSTOMER]"  # Correct field name
          
        - source: "CUSTOMER STYLE"
          target: "[STYLE]"  # Correct field name
```

### **2. Create Missing ORDERS_UNIFIED_STAGING Table**
Need DDL for intermediate staging table:

```sql
CREATE TABLE [dbo].[STG_ORDERS_UNIFIED] (
    -- All 276 columns from ORDERS_UNIFIED
    -- Plus staging technical columns
    [stg_id] BIGINT IDENTITY(1,1) PRIMARY KEY,
    [stg_batch_id] UNIQUEIDENTIFIER NOT NULL,
    [stg_status] NVARCHAR(50) DEFAULT 'PENDING',
    -- ... other staging fields
);
```

### **3. Update Documentation**
All documentation references must be corrected:
- Field name corrections
- Table name case corrections  
- Missing staging layer acknowledgment

### **4. Schema Validation Implementation**
Before proceeding, implement actual schema validation:

```python
# utils/schema_validator.py
def validate_ddl_vs_yaml():
    """Validate YAML mappings against actual DDL schemas"""
    # Load DDL schema from database
    # Load YAML mappings
    # Compare field names
    # Report mismatches
```

---

## 🎯 **REVISED MILESTONE PLAN**

### **Milestone 1.1: INCOMPLETE - Requires Remediation**
- [❌] Fix all field name mappings in YAML
- [❌] Create missing ORDERS_UNIFIED_STAGING DDL
- [❌] Update table name case consistency  
- [❌] Implement schema validation utilities
- [❌] Correct all documentation references

### **Milestone 1.2: Schema Validation (Blocked)**
Cannot proceed until 1.1 is properly completed with correct schemas.

---

## 📞 **Impact Assessment**

### **Technical Impact**
- **Critical**: All current mappings are potentially incorrect
- **Blocking**: Cannot implement validation utilities with wrong field names
- **Risk**: Production deployment would fail with current mappings

### **Business Impact**  
- **Delivery Risk**: Milestone completion delayed
- **Quality Risk**: Documentation vs reality mismatch undermines confidence
- **Integration Risk**: Monday.com API calls would fail with incorrect field mappings

---

## ✅ **Immediate Action Plan**

1. **Schema Audit** (URGENT)
   - Compare every field in YAML vs DDL
   - Document all mismatches
   - Create field mapping correction table

2. **DDL Creation** (REQUIRED)  
   - Create ORDERS_UNIFIED_STAGING table DDL
   - Ensure proper staging workflow

3. **YAML Correction** (CRITICAL)
   - Fix all field name mappings
   - Correct table name cases
   - Validate against actual DDL

4. **Documentation Update** (ESSENTIAL)
   - Update all markdown files with correct field names
   - Revise milestone completion status
   - Create schema validation checklist

**Status**: Milestone 1.1 is INCOMPLETE and requires immediate remediation before proceeding.
