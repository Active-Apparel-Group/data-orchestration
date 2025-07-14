# ORDERS_UNIFIED → STG_MON_CustMasterSchedule_Subitems → Monday.com API Mapping

## **COMPLETE FIELD MAPPING & API INTEGRATION ANALYSIS**

### **UPDATED STAGING TABLE SCHEMA**
```sql
-- STG_MON_CustMasterSchedule_Subitems (Updated Schema)
stg_id                         bigint          NO    -- PK, identity
stg_batch_id                   nvarchar        NO    -- Batch tracking
stg_parent_stg_id              bigint          YES   -- Links to parent staging record
stg_status                     nvarchar        NO    -- Processing status
stg_created_date               datetime2       NO    -- System timestamp
stg_processed_date             datetime2       YES   -- API call timestamp
stg_monday_subitem_id          bigint          YES   -- Monday.com subitem ID
stg_monday_parent_item_id      bigint          YES   -- Monday.com parent item ID
stg_monday_subitem_board_id    bigint          YES   -- ✅ NEW: Monday.com board ID
stg_error_message              nvarchar        YES   -- Error tracking
stg_retry_count                int             NO    -- Retry logic
stg_api_payload                nvarchar        YES   -- JSON payload for debugging
parent_source_uuid             uniqueidentifier YES  -- ✅ NEW: Links to parent UUID
stg_size_label                 nvarchar        YES   -- ✅ NEW: Raw size value
-- Business data fields (streamlined)
AAG_ORDER_NUMBER               nvarchar        YES   -- KEEP: Debugging/audit
STYLE                          nvarchar        YES   -- KEEP: Debugging/audit  
COLOR                          nvarchar        YES   -- KEEP: Debugging/audit
Size                           nvarchar        NO    -- KEEP: API requirement
ORDER_QTY                      decimal         NO    -- KEEP: API requirement
UNIT_OF_MEASURE                nvarchar        YES   -- KEEP: Validation reference
CUSTOMER                       nvarchar        YES   -- KEEP: Debugging/audit
PO_NUMBER                      nvarchar        YES   -- KEEP: Debugging/audit
CUSTOMER_ALT_PO                nvarchar        YES   -- KEEP: Debugging/audit
-- Fields to remove/deprecate
CUSTOMER_STYLE                 nvarchar        YES   -- ❌ REMOVE: Not used in API
GROUP_NAME                     nvarchar        YES   -- ❌ REMOVE: Not used
ITEM_NAME                      nvarchar        YES   -- ❌ REMOVE: Not used
```

### **MONDAY.COM API INTEGRATION MAPPING**

| **Staging Column** | **Data Type** | **Required** | **Monday API Usage** | **API Field/Column** | **Monday Column ID** | **Purpose** | **Notes** |
|-------------------|---------------|--------------|---------------------|-------------------|-------------------|-----------|-----------|
| **SYSTEM TRACKING FIELDS** |
| `stg_monday_subitem_id` | bigint | YES | ✅ **Response Storage** | `id` | N/A | Store subitem ID after creation | **CRITICAL for updates** |
| `stg_monday_parent_item_id` | bigint | YES | ✅ **Create Request** | `parent_item_id` | N/A | Parent item for subitem creation | **CRITICAL for creation** |
| `stg_monday_subitem_board_id` | bigint | YES | ✅ **Update Request** | `board_id` | N/A | Board ID for subitem updates | **CRITICAL for updates** |
| `parent_source_uuid` | uniqueidentifier | YES | ❌ Not sent | N/A | N/A | UUID linking to parent record | Internal tracking only |
| **API CREATION FIELDS** |
| `Size` | nvarchar | YES | ✅ **Create Request** | `item_name` | N/A | Subitem name: "Size {SIZE_LABEL}" | **CRITICAL for creation** |
| `stg_size_label` | nvarchar | YES | ✅ **Create/Update** | `column_values` | `dropdown_mkrak7qp` | Size dropdown value | **CRITICAL for creation** |
| `ORDER_QTY` | decimal | YES | ✅ **Create/Update** | `column_values` | `numeric_mkra7j8e` | Order quantity | **CRITICAL for creation** |
| **UPDATE-ONLY FIELDS (Post-Creation)** |
| N/A | N/A | N/A | ✅ **Update Only** | `column_values` | `numeric_mkrapgwv` | Shipped Qty | From external systems |
| N/A | N/A | N/A | ✅ **Update Only** | `column_values` | `numeric_mkraepx7` | Packed Qty | From external systems |
| N/A | N/A | N/A | ✅ **Update Only** | `column_values` | `numeric_mkrbgdat` | Cut Qty | From external systems |
| N/A | N/A | N/A | ✅ **Update Only** | `column_values` | `numeric_mkrc5ryb` | Sew Qty | From external systems |
| N/A | N/A | N/A | ✅ **Update Only** | `column_values` | `numeric_mkrc7jfj` | Finishing Qty | From external systems |
| N/A | N/A | N/A | ✅ **Update Only** | `column_values` | `numeric_mkrcq53k` | Received not Shipped Qty | From external systems |
| N/A | N/A | N/A | ✅ **Update Only** | `column_values` | `color_mkrbezbh` | ORDER LINE STATUS | From external systems |
| N/A | N/A | N/A | ✅ **Update Only** | `column_values` | `pulse_id_mkrag4a3` | Item ID | From external systems |
| **AUDIT/DEBUG FIELDS (NOT SENT TO API)** |
| `AAG_ORDER_NUMBER` | nvarchar | YES | ❌ Not sent | N/A | N/A | Reference for debugging | Keep for audit trail |
| `STYLE` | nvarchar | YES | ❌ Not sent | N/A | N/A | Reference for debugging | Keep for audit trail |
| `COLOR` | nvarchar | YES | ❌ Not sent | N/A | N/A | Reference for debugging | Keep for audit trail |
| `CUSTOMER` | nvarchar | YES | ❌ Not sent | N/A | N/A | Reference for debugging | Keep for audit trail |
| `PO_NUMBER` | nvarchar | YES | ❌ Not sent | N/A | N/A | Reference for debugging | Keep for audit trail |
| `CUSTOMER_ALT_PO` | nvarchar | YES | ❌ Not sent | N/A | N/A | Reference for debugging | Keep for audit trail |
| `UNIT_OF_MEASURE` | nvarchar | YES | ❌ Not sent | N/A | N/A | Reference for validation | Keep for validation |

### **MONDAY.COM API WORKFLOWS**

#### **1. SUBITEM CREATION WORKFLOW**
```graphql
mutation {
    create_subitem(
        parent_item_id: {stg_monday_parent_item_id},
        item_name: "Size {stg_size_label}",
        column_values: "{
            \"dropdown_mkrak7qp\": {\"labels\": [\"{stg_size_label}\"]},
            \"numeric_mkra7j8e\": \"{ORDER_QTY}\"
        }",
        create_labels_if_missing: true
    ) {
        id                    # → stg_monday_subitem_id
        board { id }         # → stg_monday_subitem_board_id
        parent_item { id }   # → stg_monday_parent_item_id (verification)
    }
}
```

#### **2. SUBITEM UPDATE WORKFLOW**
```graphql
mutation {
    change_multiple_column_values(
        item_id: {stg_monday_subitem_id},
        board_id: {stg_monday_subitem_board_id},
        column_values: "{
            \"numeric_mkrapgwv\": \"{shipped_qty}\",
            \"numeric_mkraepx7\": \"{packed_qty}\",
            \"numeric_mkrbgdat\": \"{cut_qty}\",
            \"numeric_mkrc5ryb\": \"{sew_qty}\",
            \"numeric_mkrc7jfj\": \"{finishing_qty}\",
            \"numeric_mkrcq53k\": \"{received_not_shipped_qty}\",
            \"color_mkrbezbh\": \"{order_line_status}\"
        }"
    ) {
        id
    }
}
```

### **API PAYLOAD SCHEMA DEFINITION**

#### **Creation Payload Structure**
```json
{
    "mutation_type": "create_subitem",
    "required_fields": {
        "parent_item_id": "stg_monday_parent_item_id",
        "item_name": "Size {stg_size_label}",
        "column_values": {
            "dropdown_mkrak7qp": {
                "labels": ["stg_size_label"]
            },
            "numeric_mkra7j8e": "ORDER_QTY"
        }
    },
    "response_mapping": {
        "id": "stg_monday_subitem_id",
        "board.id": "stg_monday_subitem_board_id", 
        "parent_item.id": "stg_monday_parent_item_id"
    }
}
```

#### **Update Payload Structure**
```json
{
    "mutation_type": "change_multiple_column_values",
    "required_fields": {
        "item_id": "stg_monday_subitem_id",
        "board_id": "stg_monday_subitem_board_id"
    },
    "optional_columns": {
        "numeric_mkrapgwv": "shipped_qty",
        "numeric_mkraepx7": "packed_qty",
        "numeric_mkrbgdat": "cut_qty",
        "numeric_mkrc5ryb": "sew_qty",
        "numeric_mkrc7jfj": "finishing_qty",
        "numeric_mkrcq53k": "received_not_shipped_qty",
        "color_mkrbezbh": "order_line_status",
        "pulse_id_mkrag4a3": "item_id"
    }
}
```

### **OPTIMIZATION RECOMMENDATIONS**

#### **KEEP THESE COLUMNS**
- **`stg_monday_subitem_id`** → Essential for updates
- **`stg_monday_parent_item_id`** → Essential for creation  
- **`stg_monday_subitem_board_id`** → Essential for updates
- **`parent_source_uuid`** → Essential for UUID tracking
- **`stg_size_label`** → Essential for API creation/updates
- **`ORDER_QTY`** → Essential for API creation/updates
- **`AAG_ORDER_NUMBER`, `STYLE`, `COLOR`, `CUSTOMER`, `PO_NUMBER`** → Keep for debugging/audit

#### **REMOVE THESE COLUMNS**
- **`CUSTOMER_STYLE`** → Not used in API or business logic
- **`GROUP_NAME`** → Not used anywhere
- **`ITEM_NAME`** → Not used anywhere

### **UUID-BASED ADVANTAGES**

1. **Simplified Lookups**: Use `parent_source_uuid` to link subitems to parent orders
2. **Efficient Updates**: Direct Monday.com ID lookups using staging table
3. **Change Detection**: Hash-based change detection for update determination
4. **Error Recovery**: UUID-based retry logic and rollback capability
5. **Performance**: Indexed UUID columns for fast joins and lookups

### **NEXT STEPS**

1. ✅ **Schema Updated**: Added `stg_monday_subitem_board_id` column
2. **Update API Functions**: Capture board ID in response handling
3. **Create JSON Mapping System**: Comprehensive field mapping configuration
4. **Update Documentation**: Reflect new schema and workflows
5. **Testing**: Validate complete create/update workflow
