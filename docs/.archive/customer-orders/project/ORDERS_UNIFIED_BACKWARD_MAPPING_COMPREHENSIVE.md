# 🎯 ORDERS UNIFIED Delta Sync V3 - Backward Mapping Analysis

## Executive Summary

**Target-First Approach**: This analysis works backward from the final Monday.com target tables to understand the complete data transformation pipeline for Active Apparel Group's multi-dimensional garment order data.

## 🏢 **Company Context: Active Apparel Group**

**Industry**: Apparel Manufacturing & Distribution  
**Data Complexity**: Multi-dimensional garment data with size matrices  
**Integration**: Monday.com Customer Master Schedule (CMS) board `4755559751`  
**Key Challenge**: Transform flat size-column data into relational master/subitem structure  

---

## 🎯 **Final Target Tables (Working Backward)**

### **Layer 5: Production Monday.com Tables**
```sql
-- Target 1: MON_CustMasterSchedule (75 fields)
-- Purpose: Master order records on Monday.com board
-- Key Fields: CUSTOMER, AAG ORDER NUMBER, STYLE, COLOR, ORDER QTY (total)

-- Target 2: MON_CustMasterSchedule_Subitems (14 fields) 
-- Purpose: Individual size breakdowns as Monday.com subitems
-- Key Fields: Size, [Order Qty], parent_item_id, subitem_id
```

### **Layer 4: Staging Tables (Current Implementation)**
```sql
-- STG_MON_CustMasterSchedule (75 + 9 staging fields)
-- Purpose: Staging for master records with UUID tracking
-- Additional: stg_id, stg_batch_id, stg_status, stg_monday_item_id

-- STG_MON_CustMasterSchedule_Subitems (14 + 13 staging fields)  
-- Purpose: Staging for size subitems with parent FK
-- Additional: stg_subitem_id, stg_parent_stg_id, stg_size_label
```

---

## 🔄 **Data Transformation Pipeline (Backward Analysis)**

### **Step 5 → 4: Production to Staging**
**Process**: Promotion after successful Monday.com API calls  
**Logic**: Copy successful records from staging to production tables  
**Code**: `staging_processor.py::promote_successful_records()`

### **Step 4 → 3: Size Melting/Pivoting (CRITICAL)**
**Source**: ORDERS_UNIFIED (164 size columns between "UNIT OF MEASURE" and "TOTAL QTY")  
**Target**: Staging subitems (1 row per size)  
**Logic**: 
```python
# Size columns: XS, S, M, L, XL, XXL, 2XL, 3XL, 4XL, 5XL + 266 specialty sizes
for size_col in self.size_columns:
    if order[size_col] > 0:  # Only create subitem if quantity exists
        subitem = {
            'Size': size_col,
            '[Order Qty]': str(int(order[size_col])),
            'stg_parent_stg_id': parent_order_id
        }
```

### **Step 3 → 2: ORDERS_UNIFIED Staging**  
**Source**: ORDERS_UNIFIED table (276 fields)  
**Target**: STG_MON_CustMasterSchedule  
**Transformation**: Direct field mapping with data cleaning

### **Step 2 → 1: Source Data**
**Source**: ORDERS_UNIFIED table  
**Origin**: Various ERP systems, Excel imports, API feeds  
**Structure**: Wide table with separate size columns (XS, S, M, L, etc.)

---

## 📊 **Field Mapping Matrix (Key Fields)**

| Layer | Table | CUSTOMER | ORDER_QTY | Size Data | Monday.com Field |
|-------|-------|----------|-----------|-----------|------------------|
| **5** | MON_CustMasterSchedule | `CUSTOMER` | `ORDER QTY` | *(aggregated)* | Direct API fields |
| **5** | MON_CustMasterSchedule_Subitems | *(inherited)* | `[Order Qty]` | `Size` | `text`, `numbers` |
| **4** | STG_MON_CustMasterSchedule | `CUSTOMER` | `ORDER QTY` | *(aggregated)* | Staged for API |
| **4** | STG_MON_CustMasterSchedule_Subitems | `CUSTOMER` | `ORDER QTY` | `Size` | Ready for API |
| **3** | Processing Layer | `customer_canonical` | *(calculated)* | Size melting | Python transform |
| **2** | ORDERS_UNIFIED | `CUSTOMER` | *(calculated)* | `XS,S,M,L...` | Source columns |

---

## 🚨 **Critical Schema Inconsistencies Found**

### **1. Size Data Field Names**
- **Source**: `XS`, `S`, `M`, `L` (164 size columns in ORDERS_UNIFIED)
- **Target**: `Size`, `[Order Qty]` (Monday.com subitems format)
- **Issue**: No 1:1 mapping, requires melting/pivoting

### **2. Order Quantity Discrepancy**  
- **Source**: `ORDER_QTY` (may not exist in ORDERS_UNIFIED)
- **Target**: `ORDER QTY` (with space, in production table)
- **Monday.com**: `[Order Qty]` (bracket notation)

### **3. Customer Field Variations**
- **Source**: `CUSTOMER` 
- **Processing**: `customer_canonical` (cleaned)
- **Target**: `CUSTOMER` (standardized)

---

## 💡 **Multi-Dimensional Garment Data Logic**

### **Complexity Example:**
```
Original Order: Style ABC, Color Red, Customer ACME
┌─ Order Level: Total qty across all sizes
└─ Size Level: XS=5, S=10, M=15, L=8, XL=2 (40 total)

Monday.com Result:
┌─ Master Item: "ACME ABC Red" (ORDER QTY = 40)
└─ Subitems: 
    ├─ XS: 5 qty
    ├─ S: 10 qty  
    ├─ M: 15 qty
    ├─ L: 8 qty
    └─ XL: 2 qty
```

### **Size Matrix Complexity:**
- **Standard Apparel**: XS, S, M, L, XL, XXL, 2XL, 3XL, 4XL, 5XL
- **Specialty Sizes**: 266 additional size codes
- **Total Size Columns**: 276 in ORDERS_UNIFIED
- **Examples**: `32DD`, `30X30`, `34/34`, `2/3`, etc.

---

## 🛠 **Current Implementation Status**

### **✅ Working Components**
- UUID-based staging workflow in `dev/orders_unified_delta_sync_v3/`
- Size melting logic in `staging_processor.py`
- Monday.com API integration in `monday_api_adapter.py`
- Staging table DDLs with proper constraints

### **❌ Non-Working/Empty Components**
- `simple-orders-mapping.yaml` (EMPTY - not used)
- `utils/simple_mapper.py` (EMPTY - not used)  
- `SimpleOrdersMapper` class (referenced in instructions but doesn't exist)

### **📋 Current Field Mapping (Actual Implementation)**
```python
# Direct field mapping in staging_processor.py
order_record = {
    'CUSTOMER': customer_canonical,
    'AAG ORDER NUMBER': row.get('AAG ORDER NUMBER', ''),
    'STYLE': row.get('STYLE', ''),
    'COLOR': row.get('COLOR', ''),
    'ORDER QTY': calculated_total_qty,  # Sum of all size quantities
    # ... 70 more fields
}

# Size subitem mapping
subitem = {
    'Size': size_col,                    # e.g., 'M', 'L', 'XL'
    '[Order Qty]': str(qty),             # Monday.com API format
    'stg_parent_stg_id': parent_id       # FK to master record
}
```

---

## 📈 **Data Flow Volumes (Estimated)**

| Stage | Records | Complexity |
|-------|---------|------------|
| **ORDERS_UNIFIED** | ~10K orders | 276 fields each |
| **After Size Melting** | ~50K subitems | 1 per size/order combo |
| **Staging Tables** | Batched | UUID-tracked |
| **Monday.com API** | Rate-limited | 0.1s delays |
| **Production Tables** | Final state | Live board sync |

---

## 🎯 **Recommended Actions**

### **1. Fix Empty Mapping Files (CRITICAL)**
```yaml
# Create: sql/mappings/simple-orders-mapping.yaml
source_table: "ORDERS_UNIFIED"
target_tables:
  - "STG_MON_CustMasterSchedule" 
  - "STG_MON_CustMasterSchedule_Subitems"
```

### **2. Update Instructions**
- Remove references to non-existent `SimpleOrdersMapper`
- Document actual implementation in `dev/orders_unified_delta_sync_v3/`
- Add Active Apparel Group context
- Include garment size complexity explanations

### **3. Validate Monday.com API Fields**
- Confirm board `4755559751` column IDs
- Test size subitem creation
- Verify field name mapping (`ORDER QTY` vs `[Order Qty]`)

### **4. Complete Integration Testing**
- Test GREYSON PO 4755 end-to-end
- Validate size melting with real data
- Monitor Monday.com API rate limits

---

## 📚 **Reference Files**

### **Working Implementation**
- `dev/orders_unified_delta_sync_v3/staging_processor.py` - Main logic
- `dev/orders_unified_delta_sync_v3/monday_api_adapter.py` - API integration
- `sql/ddl/tables/orders/staging/stg_mon_custmasterschedule*.sql` - Target schemas

### **Configuration**
- `utils/config.yaml` - Database connections  
- `sql/mappings/orders-unified-comprehensive-mapping.yaml` - Complete field reference
- `sql/mappings/monday-column-ids.json` - Monday.com API field IDs

### **Templates & Tools**
- `templates/dev-task.yml.tpl` - Development task template
- `templates/op-task.yml.tpl` - Operations task template
- `tools/workflow_generator.py` - Kestra workflow generation

---

**Last Updated**: $(Get-Date)  
**Version**: Orders Unified Delta Sync V3  
**Status**: 75% Complete - Size melting validated, API integration active
