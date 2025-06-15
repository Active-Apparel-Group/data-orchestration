# ORDERS_UNIFIED vs Monday.com Column Comparison

## Exact Matches (Direct Mapping)

| ORDERS_UNIFIED Column        | Monday.com Column            | Data Type                 | Notes        |
| ---------------------------- | ---------------------------- | ------------------------- | ------------ |
| `AAG ORDER NUMBER`           | `AAG ORDER NUMBER`           | NVARCHAR(MAX) / text      | Direct match |
| `AAG SEASON`                 | `AAG SEASON`                 | NVARCHAR(MAX) / dropdown  | Direct match |
| `CUSTOMER ALT PO`            | `CUSTOMER ALT PO`            | NVARCHAR(MAX) / text      | Direct match |
| `CUSTOMER SEASON`            | `CUSTOMER SEASON`            | NVARCHAR(MAX) / dropdown  | Direct match |
| `ORDER DATE PO RECEIVED`     | `ORDER DATE PO RECEIVED`     | DATE / date               | Direct match |
| `DROP`                       | `DROP`                       | NVARCHAR(MAX) / dropdown  | Direct match |
| `PO NUMBER`                  | `PO NUMBER`                  | NVARCHAR(MAX) / text      | Direct match |
| `PATTERN ID`                 | `PATTERN ID`                 | NVARCHAR(MAX) / text      | Direct match |
| `STYLE DESCRIPTION`          | `STYLE DESCRIPTION`          | NVARCHAR(MAX) / long_text | Direct match |
| `CATEGORY`                   | `CATEGORY`                   | NVARCHAR(MAX) / dropdown  | Direct match |
| `UNIT OF MEASURE`            | `UNIT OF MEASURE`            | NVARCHAR(MAX) / status    | Direct match |
| `ORDER TYPE`                 | `ORDER TYPE`                 | NVARCHAR(MAX) / dropdown  | Direct match |
| `DESTINATION`                | `DESTINATION`                | NVARCHAR(MAX) / text      | Direct match |
| `DESTINATION WAREHOUSE`      | `DESTINATION WAREHOUSE`      | NVARCHAR(MAX) / text      | Direct match |
| `DELIVERY TERMS`             | `DELIVERY TERMS`             | NVARCHAR(MAX) / dropdown  | Direct match |
| `PLANNED DELIVERY METHOD`    | `PLANNED DELIVERY METHOD`    | NVARCHAR(MAX) / text      | Direct match |
| `NOTES`                      | `NOTES`                      | NVARCHAR(MAX) / long_text | Direct match |
| `CUSTOMER PRICE`             | `CUSTOMER PRICE`             | NVARCHAR(MAX) / numbers   | Direct match |
| `USA ONLY LSTP 75% EX WORKS` | `USA ONLY LSTP 75% EX WORKS` | NVARCHAR(MAX) / numbers   | Direct match |
| `EX WORKS (USD)`             | `EX WORKS (USD)`             | NVARCHAR(MAX) / numbers   | Direct match |
| `ADMINISTRATION FEE`         | `ADMINISTRATION FEE`         | NVARCHAR(MAX) / numbers   | Direct match |
| `DESIGN FEE`                 | `DESIGN FEE`                 | NVARCHAR(MAX) / numbers   | Direct match |
| `FX CHARGE`                  | `FX CHARGE`                  | NVARCHAR(MAX) / numbers   | Direct match |
| `HANDLING`                   | `HANDLING`                   | NVARCHAR(MAX) / text      | Direct match |
| `SURCHARGE FEE`              | `SURCHARGE FEE`              | NVARCHAR(MAX) / numbers   | Direct match |
| `DISCOUNT`                   | `DISCOUNT`                   | NVARCHAR(MAX) / numbers   | Direct match |
| `FINAL FOB (USD)`            | `FINAL FOB (USD)`            | NVARCHAR(MAX) / numbers   | Direct match |
| `HS CODE`                    | `HS CODE`                    | NVARCHAR(MAX) / dropdown  | Direct match |
| `US DUTY RATE`               | `US DUTY RATE`               | NVARCHAR(MAX) / numbers   | Direct match |
| `US DUTY`                    | `US DUTY`                    | NVARCHAR(MAX) / numbers   | Direct match |
| `FREIGHT`                    | `FREIGHT`                    | NVARCHAR(MAX) / text      | Direct match |
| `US TARIFF RATE`             | `US TARIFF RATE`             | NVARCHAR(MAX) / numbers   | Direct match |
| `US TARIFF`                  | `US TARIFF`                  | NVARCHAR(MAX) / numbers   | Direct match |
| `DDP US (USD)`               | `DDP US (USD)`               | NVARCHAR(MAX) / numbers   | Direct match |
| `SMS PRICE USD`              | `SMS PRICE USD`              | NVARCHAR(MAX) / numbers   | Direct match |
| `FINAL PRICES Y/N`           | `FINAL PRICES Y/N`           | NVARCHAR(MAX) / status    | Direct match |
| `NOTES FOR PRICE`            | `NOTES FOR PRICE`            | NVARCHAR(MAX) / text      | Direct match |

## Close Matches (Mapping with Translation)

| ORDERS_UNIFIED Column                                          | Monday.com Column          | Mapping Notes                                       |
| -------------------------------------------------------------- | -------------------------- | --------------------------------------------------- |
| `CUSTOMER NAME`                                                | `CUSTOMER`                 | Customer name vs customer dropdown                  |
| `CUSTOMER STYLE`                                               | `STYLE`                    | Customer style vs style dropdown                    |
| `ALIAS/RELATED ITEM`                                           | `ALIAS RELATED ITEM`       | Minor naming difference                             |
| `CUSTOMER'S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS` | `COLOR`                    | Color code vs color dropdown                        |
| `ETA CUSTOMER WAREHOUSE DATE`                                  | `CUSTOMER REQ IN DC DATE`  | Similar delivery date concepts                      |
| `EX FACTORY DATE`                                              | `CUSTOMER EX FACTORY DATE` | Same concept, slight naming difference              |
| `ORDER TYPE`                                                   | `ORDER STATUS`             | Value mapping: ACTIVE→RECEIVED, CANCELLED→CANCELLED |

## Value Mappings Required

### ORDER TYPE → ORDER STATUS
| ORDERS_UNIFIED Value | Monday.com Value | Notes                         |
| -------------------- | ---------------- | ----------------------------- |
| `ACTIVE`             | `RECEIVED`       | Active orders map to received |
| `CANCELLED`          | `CANCELLED`      | Direct mapping                |

### Customer Name Standardization (from Power Query)
| Original Value | Standardized Value | Notes                   |
| -------------- | ------------------ | ----------------------- |
| `RHYTHM (AU)`  | `RHYTHM`           | Remove country suffix   |
| `RHYTHM (US)`  | `RHYTHM`           | Remove country suffix   |
| `TITLE 9`      | `TITLE NINE`       | Standardize name format |

### Data Type Conversions (from Power Query)
| Field                    | ORDERS_UNIFIED Type | Monday.com Type | Conversion Notes                          |
| ------------------------ | ------------------- | --------------- | ----------------------------------------- |
| `US TARIFF RATE`         | NVARCHAR(MAX)       | numbers         | Replace "TRUE" with "0" before conversion |
| `ORDER DATE PO RECEIVED` | DATE                | date            | Direct date mapping                       |
| `CUSTOMER PRICE`         | NVARCHAR(MAX)       | numbers         | Convert to numeric                        |
| `US DUTY RATE`           | NVARCHAR(MAX)       | numbers         | Convert to percentage                     |
| `US TARIFF RATE`         | NVARCHAR(MAX)       | numbers         | Convert to percentage                     |

## Monday.com Only Fields (Not in ORDERS_UNIFIED)

| Monday.com Column   | Type     | Notes               |
| ------------------- | -------- | ------------------- |
| `Subitems`          | subtasks | Monday.com specific |
| `ADD TO PLANNING`   | checkbox | Planning workflow   |
| `FCST CONSUMED QTY` | numbers  | Forecasting         |
| `FCST QTY`          | numbers  | Forecasting         |
| `Item ID`           | text     | Monday.com specific |
| `matchAlias`        | text     | Monday.com specific |
| `ORDER STATUS`      | status   | Status tracking     |
| `PPS CMT DUE`       | date     | Production planning |
| `PPS CMT RCV`       | date     | Production planning |
| `PPS STATUS`        | status   | Production planning |

## ORDERS_UNIFIED Only Fields (Not in Monday.com)

| ORDERS_UNIFIED Column                        | Type          | Notes                     |
| -------------------------------------------- | ------------- | ------------------------- |
| `MONTH`                                      | NVARCHAR(MAX) | Time dimension            |
| `RANGE / COLLECTION`                         | NVARCHAR(MAX) | Product grouping          |
| `PROMO GROUP / CAMPAIGN (HOT 30/GLOBAL EDIT` | NVARCHAR(MAX) | Marketing                 |
| `MAKE OR BUY`                                | NVARCHAR(MAX) | Sourcing decision         |
| `PLANNER`                                    | NVARCHAR(MAX) | Personnel                 |
| `PLANNER2`                                   | NVARCHAR(MAX) | Personnel                 |
| `ORIGINAL ALIAS/RELATED ITEM`                | NVARCHAR(MAX) | Product reference         |
| `PRICING ALIAS/RELATED ITEM`                 | NVARCHAR(MAX) | Product reference         |
| `ACTIVE`                                     | NVARCHAR(MAX) | Status flag               |
| `All`                                        | NVARCHAR(MAX) | Unknown purpose           |
| `Multiple Items`                             | NVARCHAR(MAX) | Unknown purpose           |
| `FACILITY CODE`                              | NVARCHAR(MAX) | Location                  |
| `BULK AGREEMENT NUMBER`                      | NVARCHAR(MAX) | Contract reference        |
| `BULK AGREEMENT DESCRIPTION`                 | NVARCHAR(MAX) | Contract details          |
| `CUSTOMER CODE`                              | NVARCHAR(MAX) | Customer identifier       |
| `CO NUMBER - INITIAL DISTRO`                 | NVARCHAR(MAX) | Distribution              |
| `CO NUMBER (INITIAL DISTRO)`                 | NVARCHAR(MAX) | Distribution              |
| `CO NUMBER (ALLOCATION DISTRO)`              | NVARCHAR(MAX) | Distribution              |
| `CO NUMBER - ALLOCATION DISTRO`              | NVARCHAR(MAX) | Distribution              |
| `AAG SEASON CODE`                            | NVARCHAR(MAX) | Season identifier         |
| `INFOR MAKE/BUY CODE`                        | NVARCHAR(MAX) | ERP system codes          |
| `ITEM TYPE CODE`                             | NVARCHAR(MAX) | Product classification    |
| `INFOR ITEM TYPE CODE`                       | NVARCHAR(MAX) | ERP system codes          |
| `PRODUCT GROUP CODE`                         | NVARCHAR(MAX) | Product classification    |
| `MAKE/BUY CODE`                              | NVARCHAR(MAX) | Sourcing                  |
| `INFOR PRODUCT GROUP CODE`                   | NVARCHAR(MAX) | ERP system codes          |
| `ITEM GROUP CODE`                            | NVARCHAR(MAX) | Product classification    |
| `INFOR ITEM GROUP CODE`                      | NVARCHAR(MAX) | ERP system codes          |
| `GENDER GROUP CODE`                          | NVARCHAR(MAX) | Product classification    |
| `INFOR GENDER GROUP CODE`                    | NVARCHAR(MAX) | ERP system codes          |
| `FABRIC TYPE CODE`                           | NVARCHAR(MAX) | Material classification   |
| `INFOR FABRIC TYPE CODE`                     | NVARCHAR(MAX) | ERP system codes          |
| `CUSTOMER COLOUR DESCRIPTION`                | NVARCHAR(MAX) | Color description         |
| `INFOR COLOUR CODE`                          | NVARCHAR(MAX) | ERP system codes          |
| All size columns (XXXS through 60, etc.)     | INT           | Size breakdown quantities |
| `Sum of TOTAL QTY`                           | INT           | Quantity aggregation      |
| `TOTAL QTY`                                  | INT           | Total quantity            |
| `ALLOCATION (CHANNEL)`                       | NVARCHAR(MAX) | Distribution channel      |
| `SHOP NAME`                                  | NVARCHAR(MAX) | Retail location           |
| `COLLECTION DELIVERY`                        | NVARCHAR(MAX) | Delivery method           |
| `SHOP CODE`                                  | NVARCHAR(MAX) | Retail identifier         |
| `TRACKING NUMBER`                            | NVARCHAR(MAX) | Shipping tracking         |
| `DELIVERY CODE (MODL)`                       | NVARCHAR(MAX) | Delivery classification   |
| `VALIDATION` through `VALIDATION4`           | NVARCHAR(MAX) | Data validation flags     |
| `PNP`                                        | NVARCHAR(MAX) | Unknown                   |
| `UK DUTY RATE` through `DDP CAN (USD)`       | NVARCHAR(MAX) | International pricing     |
| `PRICING NOTES`                              | NVARCHAR(MAX) | Pricing details           |
| `Delta`                                      | NVARCHAR(MAX) | Change tracking           |
| `Warehouse`                                  | NVARCHAR(MAX) | Storage location          |
| `ORTP (ORDER TYPE)`                          | NVARCHAR(MAX) | Order type classification |
| `Longson Alias`                              | NVARCHAR(MAX) | Product alias             |
| `BUAR (BUSINESS AREA UNIT)`                  | NVARCHAR(MAX) | Business classification   |
| `ADID`                                       | NVARCHAR(MAX) | Identifier                |

## Summary Statistics

- **Total ORDERS_UNIFIED columns**: 183
- **Total Monday.com columns**: 72  
- **Exact matches**: 34 columns
- **Close matches requiring mapping**: 7 columns (including ORDER TYPE→ORDER STATUS)
- **Monday.com only (mappable)**: 10 columns
- **ORDERS_UNIFIED only**: 143 columns
- **Monday.com excluded (mirror/formula/board_relation)**: 28 columns

## Power Query Transformation Insights

The existing Power Query script reveals the current transformation logic from ORDERS_UNIFIED to Monday.com format:

### Key Transformations Applied:
1. **Data Filtering**: Only current year orders (`Date.IsInCurrentYear`)
2. **Customer Mapping**: Uses lookup table to map customer names to Monday.com dropdown values
3. **Column Removal**: Eliminates ~143 ORDERS_UNIFIED-only columns (ERP codes, detailed size breakdowns, validation fields)
4. **Size Aggregation**: Consolidates individual size columns into `TOTAL QTY`
5. **Field Renaming**: Standardizes column names to match Monday.com schema
6. **Data Cleansing**: Trims and cleans text fields (`CUSTOMER STYLE`, `STYLE DESCRIPTION`, `COLOR`)
7. **Value Standardization**: Normalizes customer names and values
8. **Generated Fields**: Creates composite `Name` field from `CUSTOMER STYLE` + `COLOR` + `AAG ORDER NUMBER`

### Columns Retained in Current Process:
- Core order identification (AAG ORDER NUMBER, CUSTOMER, etc.)
- Product details (STYLE, COLOR, PATTERN ID, etc.)
- Dates (ORDER DATE PO RECEIVED, delivery dates)
- Quantities (TOTAL QTY - aggregated from size breakdown)
- Pricing (all USD pricing fields)
- Logistics (DESTINATION, DELIVERY TERMS, etc.)
- Notes fields

### Columns Eliminated in Current Process:
- All individual size columns (XS, S, M, L, etc.) - aggregated to TOTAL QTY
- All INFOR ERP system codes
- Internal tracking fields (VALIDATION1-4, Delta, etc.)
- Regional pricing (UK, CAN)
- Distribution tracking (SHOP NAME, ALLOCATION CHANNEL, etc.)
- Internal references (ORTP, BUAR, ADID, etc.)

## Data Type Mapping

| ORDERS_UNIFIED Type | Monday.com Type  | Conversion Notes                  |
| ------------------- | ---------------- | --------------------------------- |
| `NVARCHAR(MAX)`     | `text`           | Direct string mapping             |
| `NVARCHAR(MAX)`     | `dropdown`       | String to dropdown selection      |
| `NVARCHAR(MAX)`     | `long_text`      | String to rich text               |
| `NVARCHAR(MAX)`     | `status`         | String to status selection        |
| `NVARCHAR(MAX)`     | `numbers`        | String to numeric (needs parsing) |
| `DATE`              | `date`           | Direct date mapping               |
| `INT`               | `numbers`        | Direct numeric mapping            |
| N/A                 | `mirror`         | Monday.com mirrored columns       |
| N/A                 | `subtasks`       | Monday.com subitems               |
| N/A                 | `board_relation` | Monday.com board connections      |

---

## Monday.com Excluded Fields (Mirror/Formula/Board Relations)

*These fields are excluded from mapping as they are computed, mirrored from other boards, or represent internal Monday.com relationships.*

### Mirror Columns (Mirrored from other boards)
| Monday.com Column         | Type   | Notes               |
| ------------------------- | ------ | ------------------- |
| `QTY ORDERED`             | mirror | Quantity tracking   |
| `QTY SHIPPED`             | mirror | Quantity tracking   |
| `QTY PACKED`              | mirror | Quantity tracking   |
| `EX-FTY (Change Request)` | mirror | Factory dates       |
| `REQUESTED XFD STATUS`    | mirror | Status tracking     |
| `EX-FTY (Forecast)`       | mirror | Factory dates       |
| `EX-FTY (Partner PO)`     | mirror | Factory dates       |
| `EX-FTY (Revised LS)`     | mirror | Factory dates       |
| `PRODUCTION TYPE`         | mirror | Production          |
| `AQL INSPECTION`          | mirror | Quality control     |
| `AQL TYPE`                | mirror | Quality control     |
| `PLANNED CUT DATE`        | mirror | Production planning |
| `MO NUMBER`               | mirror | Manufacturing order |
| `PRODUCTION STATUS`       | mirror | Production          |
| `FACTORY COUNTRY`         | mirror | Manufacturing       |
| `FACTORY`                 | mirror | Manufacturing       |
| `ALLOCATION STATUS`       | mirror | Status tracking     |
| `PRODUCTION QTY`          | mirror | Production          |
| `TRIM ETA DATE`           | mirror | Material tracking   |
| `FABRIC ETA DATE`         | mirror | Material tracking   |
| `TRIM STATUS`             | mirror | Material tracking   |
| `FABRIC STATUS`           | mirror | Material tracking   |

### Formula Columns (Calculated fields)
| Monday.com Column | Type    | Notes          |
| ----------------- | ------- | -------------- |
| `Net Demand`      | formula | Planning       |
| `REVENUE (FOB)`   | formula | Financial      |
| `ORDER QTY`       | formula | Order quantity |
| `PACKED QTY`      | formula | Fulfillment    |
| `SHIPPED QTY`     | formula | Fulfillment    |

### Board Relation Columns (Internal Monday.com connections)
| Monday.com Column | Type           | Notes               |
| ----------------- | -------------- | ------------------- |
| `PLANNING BOARD`  | board_relation | Monday.com workflow |

## Monday.com Column IDs for API Implementation

*Critical reference for Monday.com GraphQL mutations - Column IDs are required for creating/updating records*

### Mappable Fields (for ETL process)

| Monday.com Column            | Column ID            | Type      | Mapping Category |
| ---------------------------- | -------------------- | --------- | ---------------- |
| `AAG ORDER NUMBER`           | `text_mkr5wya6`      | text      | exact_match      |
| `AAG SEASON`                 | `dropdown_mkr58de6`  | dropdown  | exact_match      |
| `CUSTOMER ALT PO`            | `text_mkrh94rx`      | text      | exact_match      |
| `CUSTOMER SEASON`            | `dropdown_mkr5rgs6`  | dropdown  | exact_match      |
| `ORDER DATE PO RECEIVED`     | `date_mkr5zp5`       | date      | exact_match      |
| `DROP`                       | `dropdown_mkr5w5e`   | dropdown  | exact_match      |
| `PO NUMBER`                  | `text_mkr5ej2x`      | text      | exact_match      |
| `PATTERN ID`                 | `text_mkr5cz8m`      | text      | exact_match      |
| `STYLE DESCRIPTION`          | `long_text_mkr5p0cf` | long_text | exact_match      |
| `CATEGORY`                   | `dropdown_mkr5s5n3`  | dropdown  | exact_match      |
| `UNIT OF MEASURE`            | `color_mkr5yf27`     | status    | exact_match      |
| `ORDER TYPE`                 | `dropdown_mkr518fc`  | dropdown  | exact_match      |
| `DESTINATION`                | `text_mkr5kbc6`      | text      | exact_match      |
| `DESTINATION WAREHOUSE`      | `text_mkr5ps35`      | text      | exact_match      |
| `DELIVERY TERMS`             | `dropdown_mkr5kk5`   | dropdown  | exact_match      |
| `PLANNED DELIVERY METHOD`    | `text_mkr5wcpw`      | text      | exact_match      |
| `NOTES`                      | `long_text_mkr5hass` | long_text | exact_match      |
| `CUSTOMER PRICE`             | `numeric_mkr5cact`   | numbers   | exact_match      |
| `USA ONLY LSTP 75% EX WORKS` | `numeric_mkr5yne4`   | numbers   | exact_match      |
| `EX WORKS (USD)`             | `numeric_mkr5erhv`   | numbers   | exact_match      |
| `ADMINISTRATION FEE`         | `numeric_mkr5k68`    | numbers   | exact_match      |
| `DESIGN FEE`                 | `numeric_mkr5h612`   | numbers   | exact_match      |
| `FX CHARGE`                  | `numeric_mkr5gp6a`   | numbers   | exact_match      |
| `HANDLING`                   | `text_mkr5s3tm`      | text      | exact_match      |
| `SURCHARGE FEE`              | `numeric_mkr57cem`   | numbers   | exact_match      |
| `DISCOUNT`                   | `numeric_mkr56xx8`   | numbers   | exact_match      |
| `FINAL FOB (USD)`            | `numeric_mkr5nhr7`   | numbers   | exact_match      |
| `HS CODE`                    | `dropdown_mkr5k8yn`  | dropdown  | exact_match      |
| `US DUTY RATE`               | `numeric_mkr5r6at`   | numbers   | exact_match      |
| `US DUTY`                    | `numeric_mkr5ev2q`   | numbers   | exact_match      |
| `FREIGHT`                    | `text_mkr5kyf4`      | text      | exact_match      |
| `US TARIFF RATE`             | `numeric_mkr55zg1`   | numbers   | exact_match      |
| `US TARIFF`                  | `numeric_mkr51ndy`   | numbers   | exact_match      |
| `DDP US (USD)`               | `numeric_mkr5js0x`   | numbers   | exact_match      |
| `SMS PRICE USD`              | `numeric_mkr58nvp`   | numbers   | exact_match      |
| `FINAL PRICES Y/N`           | `text_mkr5ptvg`      | text      | exact_match      |
| `NOTES FOR PRICE`            | `long_text_mkr5znxn` | long_text | exact_match      |
| `CUSTOMER`                   | `dropdown_mkr542p2`  | dropdown  | mapped_field     |
| `STYLE`                      | `dropdown_mkr5tgaa`  | dropdown  | mapped_field     |
| `ALIAS RELATED ITEM`         | `text_mkrhra2c`      | text      | mapped_field     |
| `COLOR`                      | `dropdown_mkr5677f`  | dropdown  | mapped_field     |
| `CUSTOMER REQ IN DC DATE`    | `date_mkr554yz`      | date      | mapped_field     |
| `CUSTOMER EX FACTORY DATE`   | `date_mkr57811`      | date      | mapped_field     |
| `ORDER STATUS`               | `color_mkr5j5pp`     | status    | mapped_field     |
| `ADD TO PLANNING`            | `color_mkrerxrs`     | status    | target_only      |
| `FCST CONSUMED QTY`          | `numeric_mkrbty8b`   | numbers   | target_only      |
| `FCST QTY`                   | `numeric_mkrb56rj`   | numbers   | target_only      |
| `Item ID`                    | `pulse_id_mkr5pb5q`  | item_id   | target_only      |
| `matchAlias`                 | `text_mkr61hpz`      | text      | target_only      |
| `PPS CMT DUE`                | `date_mkrvx550`      | date      | target_only      |
| `PPS CMT RCV`                | `date_mkrvpbcr`      | date      | target_only      |

---

## Monday.com API Implementation Guide

### GraphQL Mutation Template

Based on the extracted column IDs, here's how to create records via the Monday.com API:

```python
import requests
import json

# Monday.com API Configuration
API_URL = "https://api.monday.com/v2"
AUTH_KEY = "your_api_key_here"
API_VERSION = "2025-04"
BOARD_ID = "9218090006"  # Customer Master Schedule board

HEADERS = {
    "Content-Type": "application/json", 
    "API-Version": API_VERSION,
    "Authorization": f"Bearer {AUTH_KEY}"
}

def create_order_record(order_data):
    """
    Create a new order record in Monday.com Customer Master Schedule
    
    Args:
        order_data (dict): Mapped order data from ORDERS_UNIFIED
    """
    
    # Build column_values using the extracted column IDs
    column_values = json.dumps({
        # Core Order Information
        "text_mkr5wya6": order_data.get("AAG ORDER NUMBER", ""),  # AAG ORDER NUMBER
        "dropdown_mkr542p2": {"ids": [order_data.get("CUSTOMER_ID")]},  # CUSTOMER
        "dropdown_mkr58de6": {"ids": [order_data.get("AAG_SEASON_ID")]},  # AAG SEASON
        "date_mkr5zp5": {"date": order_data.get("ORDER_DATE"), "icon": ""},  # ORDER DATE PO RECEIVED
        "dropdown_mkr5rgs6": {"ids": [order_data.get("CUSTOMER_SEASON_ID")]},  # CUSTOMER SEASON
        "text_mkr5ej2x": order_data.get("PO NUMBER", ""),  # PO NUMBER
        
        # Product Information
        "dropdown_mkr5tgaa": {"ids": [order_data.get("STYLE_ID")]},  # STYLE
        "long_text_mkr5p0cf": order_data.get("STYLE DESCRIPTION", ""),  # STYLE DESCRIPTION
        "dropdown_mkr5677f": {"ids": [order_data.get("COLOR_ID")]},  # COLOR
        "dropdown_mkr5s5n3": {"ids": [order_data.get("CATEGORY_ID")]},  # CATEGORY
        "text_mkr5cz8m": order_data.get("PATTERN ID", ""),  # PATTERN ID
        
        # Logistics
        "text_mkr5kbc6": order_data.get("DESTINATION", ""),  # DESTINATION
        "text_mkr5ps35": order_data.get("DESTINATION WAREHOUSE", ""),  # DESTINATION WAREHOUSE
        "dropdown_mkr5kk5": {"ids": [order_data.get("DELIVERY_TERMS_ID")]},  # DELIVERY TERMS
        "date_mkr554yz": {"date": order_data.get("CUSTOMER_REQ_IN_DC_DATE"), "icon": ""},  # CUSTOMER REQ IN DC DATE
        "date_mkr57811": {"date": order_data.get("CUSTOMER_EX_FACTORY_DATE"), "icon": ""},  # CUSTOMER EX FACTORY DATE
        
        # Pricing
        "numeric_mkr5cact": order_data.get("CUSTOMER PRICE", 0),  # CUSTOMER PRICE
        "numeric_mkr5yne4": order_data.get("USA ONLY LSTP 75% EX WORKS", 0),  # USA ONLY LSTP 75% EX WORKS
        "numeric_mkr5erhv": order_data.get("EX WORKS (USD)", 0),  # EX WORKS (USD)
        "numeric_mkr5nhr7": order_data.get("FINAL FOB (USD)", 0),  # FINAL FOB (USD)
        
        # Status and Workflow
        "dropdown_mkr518fc": {"ids": [order_data.get("ORDER_TYPE_ID")]},  # ORDER TYPE
        "color_mkr5j5pp": {"index": order_data.get("ORDER_STATUS_INDEX"), "post_id": None},  # ORDER STATUS
        "color_mkr5yf27": {"index": order_data.get("UNIT_OF_MEASURE_INDEX"), "post_id": None},  # UNIT OF MEASURE
        
        # Notes
        "long_text_mkr5hass": order_data.get("NOTES", ""),  # NOTES
        "long_text_mkr5znxn": order_data.get("NOTES FOR PRICE", ""),  # NOTES FOR PRICE
    })
    
    # GraphQL mutation
    mutation = f'''
    mutation CreateOrderRecord {{
      create_item(
        board_id: {BOARD_ID},
        group_id: "{order_data.get('group_id', 'group_mkr7d8xj')}",
        item_name: "{order_data.get('item_name')}",
        column_values: "{column_values.replace('"', '\\"')}",
        create_labels_if_missing: true
      ) {{
        id
        name
        board {{
          id
        }}
      }}
    }}
    '''
    
    # Execute API call
    response = requests.post(API_URL, headers=HEADERS, json={'query': mutation})
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API Error: {response.status_code} - {response.text}")

# Example usage with ORDERS_UNIFIED data
example_order = {
    "AAG ORDER NUMBER": "JOO-00505",
    "CUSTOMER_ID": 19,  # Dropdown ID for JOHNNIE O
    "AAG_SEASON_ID": 1,  # Dropdown ID for 2026 SPRING
    "ORDER_DATE": "2025-05-20",
    "CUSTOMER_SEASON_ID": 4,  # Dropdown ID for SPRING SUMMER 2026
    "PO NUMBER": "8148-00",
    "STYLE_ID": 35,  # Dropdown ID for JWHD100120
    "STYLE DESCRIPTION": "NALLA",
    "COLOR_ID": 0,  # Dropdown ID for WHITE
    "CATEGORY_ID": 1,  # Dropdown ID for WOMENS
    "DESTINATION": "MISSISSIPPI",
    "CUSTOMER PRICE": 28.86,
    "ORDER_TYPE_ID": 1,  # Dropdown ID for RECEIVED
    "ORDER_STATUS_INDEX": 7,  # Status index for "00 PLANNING"
    "UNIT_OF_MEASURE_INDEX": 7,  # Status index for "PCE"
    "item_name": "JWHD100120WHITEJOO-00505",
    "group_id": "group_mkr7d8xj"
}

# Create the record
# result = create_order_record(example_order)
```

### Key Column ID Reference for ETL Development

**Critical Fields for Order Creation:**
- Item Name: Computed from `CUSTOMER STYLE` + `COLOR` + `AAG ORDER NUMBER`
- Customer: `dropdown_mkr542p2` (requires dropdown ID lookup)
- Style: `dropdown_mkr5tgaa` (requires dropdown ID lookup)
- Color: `dropdown_mkr5677f` (requires dropdown ID lookup)
- Order Status: `color_mkr5j5pp` (requires status index mapping)

**Data Type Mapping Rules:**
1. **Text fields** (`text_*`): Pass as quoted strings
2. **Dropdown fields** (`dropdown_*`): Use `{"ids": [id_number]}` format
3. **Number fields** (`numeric_*`): Pass as numeric values
4. **Date fields** (`date_*`): Use `{"date": "YYYY-MM-DD", "icon": ""}` format
5. **Status fields** (`color_*`): Use `{"index": index_number, "post_id": null}` format

**Excluded Fields (Do Not Map):**
- All `lookup_*` fields (22 mirror columns)
- All `formula_*` fields (5 calculated columns)
- `board_relation_*` fields (1 board relation column)

### Value Transformation Required

**ORDER TYPE → ORDER STATUS Mapping:**
```python
order_type_mapping = {
    "ACTIVE": "RECEIVED",
    "CANCELLED": "CANCELLED"
}

# In your ETL process:
monday_order_status = order_type_mapping.get(orders_unified_order_type, "RECEIVED")
```

**Customer Name Standardization:**
```python
customer_name_mapping = {
    "RHYTHM (AU)": "RHYTHM",
    "RHYTHM (US)": "RHYTHM", 
    "TITLE 9": "TITLE NINE"
}

# In your ETL process:
standardized_name = customer_name_mapping.get(orders_unified_customer, orders_unified_customer)
```

This comprehensive mapping enables automated ETL processes to transform ORDERS_UNIFIED data into properly formatted Monday.com records using the GraphQL API.
