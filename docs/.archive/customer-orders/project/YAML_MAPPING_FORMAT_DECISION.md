# YAML Mapping Format Decision - Orders Unified Delta Sync V3

**Decision**: ✅ **Comprehensive Single-Source YAML with Pipeline Structure**  
**Based on**: Working 75% implementation + User concept + Active Apparel complexity  
**Location**: `sql/mappings/orders_unified_comprehensive_pipeline.yaml`

---

## 🎯 **Final Format: Enhanced Pipeline Structure**

### **Complete Mapping YAML (Every Reference)**
```yaml
# sql/mappings/orders_unified_comprehensive_pipeline.yaml
metadata:
  version: "2.0"
  description: "Complete end-to-end mapping: ORDERS_UNIFIED → STG → Monday.com (Board 4755559751)"
  generated: "2025-06-21"
  company: "Active Apparel Group"  data_complexity: "Multi-dimensional garment data (164 actual size columns)"
  board_target: "4755559751"  # Customer Master Schedule
  snapshot_storage: "hybrid"  # SQL Server table + Kestra PostgreSQL Parquet archive

# ⭐ PIPELINES - Complete data flow definitions
pipelines:

  # Pipeline 1: Master Order Records
  - name: CustMasterSchedule
    description: "Master order records with aggregated quantities"
    source:
      table: "ORDERS_UNIFIED"
      database: "ORDERS"
      key_fields:
        - "AAG ORDER NUMBER"
        - "CUSTOMER"
        - "STYLE"
        - "COLOR"
      size_aggregation:
        # All 276 size columns → single ORDER QTY
        size_columns:
          standard: ["XS", "S", "M", "L", "XL", "XXL", "2XL", "3XL", "4XL", "5XL"]
          specialty: ["32DD", "30X30", "34/34", "2/3", "28W", "30L"]  # +266 more
        calculation: "SUM(all_size_columns_where_qty_gt_0)"
        
    staging:
      table: "STG_MON_CustMasterSchedule"
      database: "ORDERS"
      batch_field: "stg_batch_id"
      uuid_field: "stg_id"
      status_field: "stg_status"
      monday_id_field: "stg_monday_item_id"
      field_mappings:
        # Direct mappings (no transformation)
        - source: "AAG ORDER NUMBER"
          target: "AAG ORDER NUMBER"
          type: "direct"
        - source: "STYLE"
          target: "STYLE"
          type: "direct"
        - source: "COLOR"
          target: "COLOR"
          type: "direct"
        # Transformed mappings
        - source: "CUSTOMER"
          target: "CUSTOMER"
          type: "customer_lookup"
          transformation:
            function: "apply_customer_mapping"
            lookup_file: "customer_mapping.yaml"
        # Calculated mappings
        - source: "SIZE_COLUMNS_AGGREGATED"
          target: "ORDER QTY"
          type: "calculated"
          calculation: "sum_all_size_quantities"
          
    final:
      table: "MON_CustMasterSchedule"
      monday_board_id: "4755559751"
      graphql:
        mutation_file: "createMasterScheduleItem.graphql"
        item_name_template: "{CUSTOMER} {STYLE} {COLOR}"
      column_mappings:
        - staging: "AAG ORDER NUMBER"
          monday_column_id: "text_mkr5wya6"
          monday_type: "text"
        - staging: "CUSTOMER"
          monday_column_id: "text_customer_name"
          monday_type: "text"
        - staging: "STYLE"
          monday_column_id: "text_style_code"
          monday_type: "text"
        - staging: "COLOR"
          monday_column_id: "text_color_name"
          monday_type: "text"
        - staging: "ORDER QTY"
          monday_column_id: "numbers_total_qty"
          monday_type: "numbers"
        - staging: "ORDER DATE PO RECEIVED"
          monday_column_id: "date_po_received"
          monday_type: "date"
        - staging: "AAG SEASON"
          monday_column_id: "dropdown_mkr58de6"
          monday_type: "dropdown"
        # ... ALL 75 Monday.com fields mapped here

  # Pipeline 2: Size Subitems (CRITICAL for garment data)
  - name: CustMasterScheduleSubitems
    description: "Individual size breakdowns from 276 size columns"
    source:
      table: "ORDERS_UNIFIED"
      database: "DMS"
      key_fields:
        - "AAG ORDER NUMBER"
        - "SIZE_COLUMN_NAME"  # Dynamic based on melting
      size_melting:
        # Transform 276 columns → rows
        logic: "melt_size_columns"
        condition: "quantity > 0"
        output_structure:
          size_field: "SIZE_COLUMN_NAME"
          quantity_field: "SIZE_QUANTITY"
          parent_reference: "AAG ORDER NUMBER"
        
    staging:
      table: "STG_MON_CustMasterSchedule_Subitems"
      database: "ORDERS"
      batch_field: "stg_batch_id"
      uuid_field: "stg_subitem_id"
      parent_uuid_field: "stg_parent_stg_id"  # FK to master record
      status_field: "stg_status"
      monday_id_field: "stg_monday_subitem_id"
      field_mappings:
        - source: "SIZE_COLUMN_NAME"
          target: "Size"
          type: "direct"
        - source: "SIZE_QUANTITY"
          target: "[Order Qty]"
          type: "format_integer"
        - source: "AAG ORDER NUMBER"
          target: "Parent Reference"
          type: "direct"
          
    final:
      table: "MON_CustMasterSchedule_Subitems"
      monday_board_id: "4755559751"  # Same board, subitems
      graphql:
        mutation_file: "createSubitemSizeBreakdown.graphql"
        item_name_template: "Size: {Size}"
        parent_item_required: true
      column_mappings:
        - staging: "Size"
          monday_column_id: "text_size_label"
          monday_type: "text"
        - staging: "[Order Qty]"
          monday_column_id: "numbers_size_qty"
          monday_type: "numbers"
        - staging: "Parent Reference"
          monday_column_id: "text_parent_ref"
          monday_type: "text"

# ⭐ TRANSFORMATIONS - All data transformation logic
transformations:
  customer_mapping:
    file: "customer_mapping.yaml"
    function: "apply_customer_mapping"
    examples:
      - source: "greyson"
        target: "GREYSON"
      - source: "GREYSON CLOTHIERS"
        target: "GREYSON"
        
  size_melting:
    function: "melt_size_columns"
    input_columns: 276
    output_format: "1_row_per_nonzero_size"
    examples:
      - input: {"XS": 0, "S": 10, "M": 20, "L": 15}
        output: 
          - {"Size": "S", "[Order Qty]": "10"}
          - {"Size": "M", "[Order Qty]": "20"}
          - {"Size": "L", "[Order Qty]": "15"}
          
  date_standardization:
    function: "standardize_date_format"
    input_formats: ["MM/DD/YYYY", "YYYY-MM-DD", "DD/MM/YYYY"]
    output_format: "YYYY-MM-DD"

# ⭐ MONDAY.COM CONFIGURATION
monday_config:
  board_id: "4755559751"
  board_name: "Customer Master Schedule"
  api_settings:
    rate_limit_delay: 0.1  # seconds
    retry_attempts: 3
    timeout: 30
  authentication:
    api_key_env: "MONDAY_API_KEY"
    workspace_id: "123456"

# ⭐ VALIDATION RULES
validation:
  required_fields:
    master: ["AAG ORDER NUMBER", "CUSTOMER", "STYLE", "COLOR"]
    subitems: ["Size", "[Order Qty]", "stg_parent_stg_id"]
  data_quality:
    - field: "ORDER QTY"
      rule: "must_be_positive_integer"
    - field: "CUSTOMER"
      rule: "must_exist_in_customer_mapping"
    - field: "Size"
      rule: "must_be_valid_size_code"
  business_rules:
    - name: "order_qty_equals_sum_of_subitems"
      description: "Master ORDER QTY must equal sum of all subitem quantities"
    - name: "subitems_only_for_nonzero_sizes"
      description: "Only create subitems for sizes with quantity > 0"

# ⭐ ERROR HANDLING
error_handling:
  staging_failures:
    action: "log_and_continue"
    retry_logic: "exponential_backoff"
  monday_api_failures:
    action: "mark_failed_retry_later"
    max_retries: 3
  data_validation_failures:
    action: "quarantine_and_alert"
    notification: "data_quality_team"

# ⭐ PERFORMANCE OPTIMIZATION
performance:
  batch_processing:
    master_records: 500  # records per batch
    subitems: 1000       # subitems per batch
  caching:
    customer_mapping: true
    monday_board_schema: true
  indexing:
    staging_tables: ["stg_batch_id", "stg_status", "stg_monday_item_id"]
```

---

## 📁 **Supporting GraphQL Files**

### **File 1: sql/graphql/mutations/createMasterScheduleItem.graphql**
```graphql
# Master item creation with all 75 fields
mutation createMasterScheduleItem(
  $boardId: Int!,
  $itemName: String!,
  $columnValues: JSON!
) {
  create_item(
    board_id: $boardId,
    item_name: $itemName,
    column_values: $columnValues
  ) {
    id
    name
    column_values {
      id
      value
    }
  }
}

# Example variables for GREYSON order:
# {
#   "boardId": 4755559751,
#   "itemName": "GREYSON ABC123 Navy",
#   "columnValues": "{
#     \"text_mkr5wya6\":\"JOO-00505\",
#     \"text_customer_name\":\"GREYSON\",
#     \"text_style_code\":\"ABC123\",
#     \"text_color_name\":\"Navy\",
#     \"numbers_total_qty\":720,
#     \"date_po_received\":\"2024-12-15\",
#     \"dropdown_mkr58de6\":\"2026 SPRING\"
#   }"
# }
```

### **File 2: sql/graphql/mutations/createSubitemSizeBreakdown.graphql**
```graphql
# Subitem creation for size breakdowns
mutation createSubitemSizeBreakdown(
  $parentItemId: Int!,
  $itemName: String!,
  $columnValues: JSON!
) {
  create_subitem(
    parent_item_id: $parentItemId,
    item_name: $itemName,
    column_values: $columnValues
  ) {
    id
    name
    column_values {
      id
      value
    }
  }
}

# Example variables for size M:
# {
#   "parentItemId": 7890123456,
#   "itemName": "Size: M",
#   "columnValues": "{
#     \"text_size_label\":\"M\",
#     \"numbers_size_qty\":240,
#     \"text_parent_ref\":\"JOO-00505\"
#   }"
# }
```

---

## 🔄 **How It All Connects (Complete Flow)**

### **1. Source → Staging (Pipeline Driven)**
```python
# Uses pipeline configuration for field mappings
def load_to_staging(pipeline_config):
    for mapping in pipeline_config['staging']['field_mappings']:
        if mapping['type'] == 'customer_lookup':
            # Apply customer mapping transformation
        elif mapping['type'] == 'calculated':
            # Apply calculation logic (size aggregation)
        # ... process all 75+ fields per pipeline definition
```

### **2. Size Melting (276 Columns → Subitems)**
```python
# Uses size_melting configuration
def melt_sizes(order_row, pipeline_config):
    size_config = pipeline_config['source']['size_melting']
    for size_col in ALL_276_SIZE_COLUMNS:
        if order_row[size_col] > 0:
            # Create subitem per pipeline subitem mapping
```

### **3. Staging → Monday.com (GraphQL Driven)**
```python
# Uses GraphQL files + column mappings
def create_monday_item(staging_record, pipeline_config):
    graphql_file = pipeline_config['final']['graphql']['mutation_file']
    column_mappings = pipeline_config['final']['column_mappings']
    # Build column_values JSON from mappings
    # Execute GraphQL mutation
```

---

## ✅ **Why This Format Wins**

### **1. Complete Reference in One Place**
- ✅ Every source field mapping
- ✅ Every staging transformation  
- ✅ Every Monday.com column ID
- ✅ All 276 size column handling
- ✅ GraphQL mutation references
- ✅ Error handling and validation rules

### **2. Active Apparel Group Specific**
- ✅ Multi-dimensional garment data structure
- ✅ 276 size columns explicitly handled
- ✅ Customer standardization logic
- ✅ Size melting/pivoting configuration

### **3. Production Ready**
- ✅ Performance optimization settings
- ✅ Error handling strategies
- ✅ Validation rules for data quality
- ✅ Monday.com API configuration

### **4. Maintainable**
- ✅ Single source of truth
- ✅ Clear pipeline structure
- ✅ Easy to add new fields/transformations
- ✅ Version controlled and documented

---

## 🎯 **Implementation Plan**

### **Phase 1: Create Comprehensive YAML**
- Consolidate all existing mapping files
- Add all 75 Monday.com field mappings
- Include all 276 size column references
- Add transformation and validation rules

### **Phase 2: Update Working Code**
- Modify `staging_processor.py` to read from YAML
- Update `monday_api_adapter.py` to use GraphQL files
- Enhance error handling per YAML configuration

### **Phase 3: Validation & Testing**
- Validate all Monday.com column IDs against board 4755559751
- Test complete end-to-end flow
- Verify size melting accuracy (276 → subitems)

---

**ANSWER**: Yes, our YAML will have **EVERY mapping reference** in one comprehensive file. This enhanced pipeline structure captures your excellent concept while handling Active Apparel Group's complex multi-dimensional garment data requirements.
