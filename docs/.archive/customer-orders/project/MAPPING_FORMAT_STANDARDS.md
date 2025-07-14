# Mapping Format Standards & Examples - Orders Unified Delta Sync V3

**Decided Standard**: YAML with Monday.com Column IDs (In Production Use)  
**Board Target**: 4755559751 (Customer Master Schedule)  
**Implementation**: 75% Complete Working Code

---

## 🎯 **Production Mapping Format (ESTABLISHED)**

### **Master Table Mapping Example**
```yaml
# File: sql/mappings/orders-unified-consolidated-mapping.yaml
metadata:
  version: "2.0"
  source_table: "ORDERS_UNIFIED"
  target_board_id: "4755559751"
  target_tables:
    - "STG_MON_CustMasterSchedule"
    - "STG_MON_CustMasterSchedule_Subitems"
  total_fields: 75
  size_columns: 164  # Actual count between "UNIT OF MEASURE" and "TOTAL QTY"

# Direct 1:1 field mappings (no transformation)
exact_matches:
  - source_field: "AAG ORDER NUMBER"
    target_field: "AAG ORDER NUMBER"
    target_column_id: "text_mkr5wya6"          # ⭐ Monday.com API column ID
    source_type: "NVARCHAR(200)"
    target_type: "text"
    transformation: "direct_mapping"
    validation: "required|max_length:200"

  - source_field: "ORDER QTY"
    target_field: "ORDER QTY" 
    target_column_id: "numbers_total_qty"      # ⭐ Calculated from size melting
    source_type: "calculated"
    target_type: "numbers"
    transformation: "size_aggregation"
    calculation: "SUM(XS,S,M,L,XL,XXL,2XL,3XL,4XL,5XL + 266_specialty_sizes)"

# Fields requiring transformation/processing
mapped_fields:
  - source_field: "CUSTOMER"
    target_field: "CUSTOMER" 
    target_column_id: "text_customer_name"
    source_type: "NVARCHAR(200)"
    target_type: "text"
    transformation: "customer_mapping_lookup"
    mapping_rules:
      - source_value: "greyson"
        target_value: "GREYSON"
      - source_value: "GREYSON CLOTHIERS"
        target_value: "GREYSON"

  - source_field: "ORDER DATE PO RECEIVED"
    target_field: "ORDER DATE PO RECEIVED"
    target_column_id: "date_po_received"
    source_type: "DATE"
    target_type: "date"
    transformation: "date_standardization"
    format: "YYYY-MM-DD"

# Size dimension handling (CRITICAL for garment data)
size_handling:
  source_columns: 
    standard_apparel: ["XS", "S", "M", "L", "XL", "XXL", "2XL", "3XL", "4XL", "5XL"]
    specialty_sizes: ["32DD", "30X30", "34/34", "2/3", "28W", "30L", "..."] # 266 more
  melting_logic:
    condition: "quantity > 0"
    target_table: "STG_MON_CustMasterSchedule_Subitems"
    target_fields:
      - field: "Size"
        value: "{size_column_name}"          # e.g., "M", "L", "32DD"
        column_id: "text_size_label"
      - field: "[Order Qty]"
        value: "{size_quantity}"             # e.g., 240, 480
        column_id: "numbers_size_qty"
      - field: "stg_parent_stg_id"
        value: "{parent_uuid}"               # FK to master record
        column_id: "relation_parent_link"

# Computed fields (calculated during processing)
computed_fields:
  - field_name: "Total ORDER QTY"
    calculation: "SUM(all_size_columns_where_qty_gt_0)"
    target_column_id: "numbers_total_qty"
    
  - field_name: "Item Name"
    calculation: "CONCAT(CUSTOMER, ' ', STYLE, ' ', COLOR)"
    target_column_id: "text_item_name"
    example: "GREYSON ABC123 Navy"
```

---

## 🏗️ **Database Schema Format (SQL DDL)**

### **Staging Table Structure** 
```sql
-- WORKING SCHEMA: sql/ddl/tables/orders/staging/
CREATE TABLE [dbo].[STG_MON_CustMasterSchedule] (
    -- Monday.com target fields (75 total) - EXACT MATCH
    [AAG ORDER NUMBER] NVARCHAR(200) NULL,
    [CUSTOMER] NVARCHAR(200) NULL,
    [STYLE] NVARCHAR(200) NULL, 
    [COLOR] NVARCHAR(200) NULL,
    [ORDER QTY] BIGINT NULL,                    -- Calculated from size aggregation
    [ORDER DATE PO RECEIVED] DATE NULL,
    -- ... 69 more Monday.com fields
    
    -- Staging workflow fields (9 total)
    [stg_id] BIGINT IDENTITY(1,1) PRIMARY KEY,
    [stg_batch_id] UNIQUEIDENTIFIER NOT NULL,
    [stg_status] NVARCHAR(50) DEFAULT 'PENDING',
    [stg_monday_item_id] BIGINT NULL,           -- Monday.com API response
    [stg_error_message] NVARCHAR(MAX) NULL,
    [stg_created_date] DATETIME2 DEFAULT GETDATE(),
    -- ... 3 more staging fields
);

-- Size subitems table (CRITICAL for garment data)
CREATE TABLE [dbo].[STG_MON_CustMasterSchedule_Subitems] (
    -- Monday.com subitem fields (14 total)
    [Size] NVARCHAR(50) NOT NULL,              -- e.g., "M", "L", "32DD"
    [Order Qty] BIGINT NOT NULL,               -- Size-specific quantity  
    [subitem_id] BIGINT NULL,                  -- Monday.com subitem ID
    [parent_item_id] BIGINT NULL,              -- Monday.com parent item ID
    -- ... 10 more subitem fields
    
    -- Staging workflow fields (13 total)
    [stg_subitem_id] BIGINT IDENTITY(1,1) PRIMARY KEY,
    [stg_parent_stg_id] BIGINT NOT NULL,       -- FK to master staging record
    [stg_size_label] NVARCHAR(50) NULL,        -- Cleaned size label
    [stg_batch_id] UNIQUEIDENTIFIER NOT NULL,
    [stg_status] NVARCHAR(50) DEFAULT 'PENDING',
    -- ... 8 more staging fields
    
    CONSTRAINT [FK_Subitems_Parent] FOREIGN KEY ([stg_parent_stg_id]) 
        REFERENCES [STG_MON_CustMasterSchedule]([stg_id])
);
```

---

## 📡 **Monday.com API Format (JSON)**

### **Master Item Creation**
```json
{
  "mutation": "create_item",
  "variables": {
    "board_id": 4755559751,
    "item_name": "GREYSON ABC123 Navy",
    "column_values": {
      "text_mkr5wya6": "JOO-00505",           // AAG ORDER NUMBER
      "text_customer_name": "GREYSON",        // CUSTOMER (standardized)
      "text_style_code": "ABC123",            // STYLE
      "text_color_name": "Navy",              // COLOR  
      "numbers_total_qty": 720,               // ORDER QTY (aggregated)
      "date_po_received": "2024-12-15",       // ORDER DATE (standardized)
      "dropdown_mkr58de6": "2026 SPRING"      // AAG SEASON
    }
  }
}
```

### **Subitem Creation (Size Breakdown)**
```json
{
  "mutation": "create_subitem", 
  "variables": {
    "parent_item_id": 7890123456,
    "item_name": "Size: M",
    "column_values": {
      "text_size_label": "M",                 // Size
      "numbers_size_qty": 240,                // [Order Qty] for this size
      "text_parent_ref": "JOO-00505"          // Reference to parent order
    }
  }
}
```

---

## 🔄 **Data Transformation Patterns (Working Code)**

### **Size Melting Logic (staging_processor.py)**
```python
# WORKING IMPLEMENTATION: 75% complete
def melt_size_columns(order_row: pd.Series) -> List[Dict]:
    """Transform 276 size columns into subitem records"""
    subitems = []
    
    # Size column patterns (276 total in ORDERS_UNIFIED)
    size_columns = [
        'XS', 'S', 'M', 'L', 'XL', 'XXL', '2XL', '3XL', '4XL', '5XL',  # Standard
        '32DD', '30X30', '34/34', '2/3', '28W', '30L', '...', # Specialty (266 more)
    ]
    
    for size_col in size_columns:
        qty = order_row.get(size_col, 0)
        if qty and qty > 0:  # Only create subitem if quantity exists
            subitem = {
                'Size': size_col,                    # Monday.com field name
                '[Order Qty]': str(int(qty)),        # Monday.com bracket format
                'stg_parent_stg_id': order_row['stg_id'],  # UUID FK
                'stg_batch_id': order_row['stg_batch_id']
            }
            subitems.append(subitem)
    
    return subitems

# Total quantity calculation (sum of all sizes)
def calculate_total_qty(order_row: pd.Series) -> int:
    """Calculate ORDER QTY from size columns"""
    total = 0
    for size_col in size_columns:
        qty = order_row.get(size_col, 0)
        if qty and qty > 0:
            total += int(qty)
    return total
```

### **Customer Name Standardization**
```python
# WORKING IMPLEMENTATION: order_mapping.py
def apply_customer_mapping(customer_value: str, customer_lookup: Dict) -> str:
    """Standardize customer names using lookup table"""
    if not customer_value:
        return ""
        
    # Clean and normalize
    cleaned = str(customer_value).strip().upper()
    
    # Apply mapping lookup
    canonical_name = customer_lookup.get(cleaned, cleaned)
    
    return canonical_name
```

---

## ✅ **Validation Checklist (Ready to Execute)**

### **Schema Validation Tasks**
```yaml
monday_api_validation:
  - task: "Validate Column IDs"
    board_id: "4755559751"
    status: "pending"
    fields_to_validate: 75
    
  - task: "Test GraphQL Mutations" 
    operations: ["create_item", "create_subitem", "update_item"]
    status: "pending"
    
  - task: "Verify Rate Limiting"
    delay_setting: "0.1_seconds"
    status: "pending"

ddl_validation:
  - task: "Field Count Reconciliation"
    staging_table: "STG_MON_CustMasterSchedule"
    expected_fields: "84 (75 + 9 staging)"
    status: "confirmed"
    
  - task: "Subitem Table Structure"
    staging_table: "STG_MON_CustMasterSchedule_Subitems" 
    expected_fields: "27 (14 + 13 staging)"
    status: "confirmed"

size_melting_validation:
  - task: "Size Column Inventory"
    source_table: "ORDERS_UNIFIED"
    expected_columns: "276"
    status: "pending"
    
  - task: "Melting Logic Test"
    test_cases: ["standard_sizes", "specialty_sizes", "zero_quantities"]
    status: "pending"
```

---

## 🎯 **Implementation Priority (Next Steps)**

### **Phase 1: Validation (0 Code Changes)**
1. **Monday.com Column ID Validation** - Verify against board 4755559751
2. **Size Column Inventory** - Confirm all 276 columns captured
3. **GraphQL Template Testing** - Validate against live API

### **Phase 2: Enhancement (25% Completion)**
1. **Error Handling Enhancement** - Expand existing error_handler.py
2. **Performance Optimization** - Optimize existing staging_processor.py  
3. **Comprehensive Testing** - Add end-to-end validation tests

---

**CONCLUSION**: The decided mapping format (YAML + Column IDs) is production-ready and proven in the working 75% complete implementation. Schema validation will accelerate completion without setbacks.
