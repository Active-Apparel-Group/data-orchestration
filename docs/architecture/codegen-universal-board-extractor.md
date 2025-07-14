# Monday.com Board Configuration & Column Control Guide

## Overview

This guide explains the complete column control system for Monday.com board extraction, including how to exclude columns, change datatypes, and apply conversion logic.

## Architecture

Our system uses two configuration layers:

1. **Metadata JSON** (`board_{id}_metadata.json`) - Raw board discovery data
2. **Config JSON** (`board_{id}.json`) - User-customizable extraction rules

## Column Control Methods

### 1. 🚫 Exclude Columns from Target Table

#### Method A: By Column ID (Monday.com Internal ID)
```json
{
  "exclusions": {
    "column_ids": ["dropdown_mks82bg4", "long_text_mkpbqfkn"]
  }
}
```

#### Method B: By Column Title (Human-Readable Name)
```json
{
  "exclusions": {
    "column_titles": [
      "Internal Notes",
      "Private Comments", 
      "Debug Field"
    ]
  }
}
```

**Logic:** If a column is found in either exclusion list, it returns `None` and is skipped entirely.

### 2. 🔄 Change Datatype in Target Table

Three levels of datatype control (in priority order):

#### A. Column-Specific Override (HIGHEST PRIORITY)
```json
{
  "column_mappings": {
    "column_overrides": {
      "dropdown_mks82bg4": {
        "sql": "VARCHAR(50)",
        "field": "label"
      },
      "Factory Name": {
        "sql": "NVARCHAR(500)",
        "nullable": false
      }
    }
  }
}
```

#### B. Type-Based Override (MEDIUM PRIORITY)
```json
{
  "column_mappings": {
    "type_overrides": {
      "date": {"sql": "DATE"},
      "numbers": {"sql": "DECIMAL(18,2)"},
      "dropdown": {"sql": "NVARCHAR(100)", "field": "text"}
    }
  }
}
```

#### C. Default Rule (LOWEST PRIORITY)
```json
{
  "column_mappings": {
    "default_rule": {
      "sql": "NVARCHAR(255)",
      "include": true
    }
  }
}
```

**Logic Flow:**
1. Start with `default_rule`
2. Apply `type_overrides` if column type matches
3. Apply `column_overrides` if column ID/title matches

### 3. 🔧 Conversion Logic & Helper Functions

#### In Metadata JSON
Each column can specify conversion logic:
```json
{
  "monday_id": "date_mks32x8d",
  "monday_title": "Due Date",
  "monday_type": "date",
  "sql_type": "DATE",
  "conversion_logic": "safe_date_convert(extract_value(cv))"
}
```

#### Available Conversion Functions
- `safe_date_convert(extract_value(cv))` - For date columns
- `safe_numeric_convert(extract_value(cv))` - For numeric columns
- Custom functions can be added as needed

#### Extraction Field Control
Control which GraphQL field to extract:
```json
{
  "column_overrides": {
    "Status Field": {
      "field": "label"  // Extract 'label' instead of 'text'
    },
    "Dropdown Field": {
      "field": "text"   // Extract 'text' (default for dropdowns)
    }
  }
}
```

## Practical Examples

### Example 1: Factory List Board Configuration
```json
{
  "meta": {
    "board_id": 8685586257,
    "board_name": "Factory List",
    "table_name": "MON_FactoryList"
  },
  "exclusions": {
    "column_titles": [
      "Internal Notes",
      "link COO Planning",
      "link to POs"
    ]
  },
  "column_mappings": {
    "default_rule": {
      "sql": "NVARCHAR(255)",
      "include": true
    },
    "type_overrides": {
      "phone": {"sql": "VARCHAR(50)"},
      "country": {"sql": "VARCHAR(100)"},
      "item_id": {"sql": "BIGINT NOT NULL"}
    },
    "column_overrides": {
      "Factory Name (Consignee)": {
        "sql": "NVARCHAR(500)",
        "nullable": false
      },
      "Factory Address": {
        "sql": "NVARCHAR(1000)"
      }
    }
  }
}
```

### Example 2: Complex Date Processing
```json
{
  "column_mappings": {
    "type_overrides": {
      "date": {
        "sql": "DATETIME2",
        "field": "text"
      }
    },
    "column_overrides": {
      "Due Date": {
        "sql": "DATE",
        "conversion_logic": "safe_date_convert(extract_value(cv))",
        "nullable": false
      }
    }
  }
}
```

## Processing Logic Flow

### In `get_column_rule()` function:
1. **Check Exclusions** - Return `None` if excluded
2. **Start with Default Rule** - Base configuration
3. **Apply Type Override** - Update based on Monday.com column type
4. **Apply Column Override** - Final customization by ID or title
5. **Return Final Rule** - Or `None` if `include: false`

### In `extract_column_value()` function:
1. **Get Field Type** - From column metadata
2. **Apply Type-Specific Logic** - Date/numeric/text handling
3. **Extract Value** - Using specified field (`text`, `label`, `display_value`, etc.)
4. **Apply Conversion** - If conversion_logic specified

## Configuration Files Structure

### board_{id}.json (User Configuration)
```
configs/boards/board_8685586257.json
├── meta (board info)
├── column_mappings
│   ├── default_rule
│   ├── type_overrides
│   └── column_overrides
└── exclusions
    ├── column_ids
    └── column_titles
```

### board_{id}_metadata.json (Raw Discovery)
```
configs/boards/board_8685586257_metadata.json
├── board_id, board_name, etc.
├── columns[] (all discovered columns)
│   ├── monday_id, monday_title
│   ├── monday_type, sql_type
│   ├── extraction_field
│   └── conversion_logic
└── metadata (discovery info)
```

## Best Practices

### 1. Column Exclusions
- Use `column_titles` for human-readable exclusions
- Use `column_ids` for permanent exclusions (IDs don't change)
- Exclude large/complex fields like `board_relation` for better performance

### 2. Datatype Mapping
- Use `type_overrides` for consistent type mapping across all boards
- Use `column_overrides` for specific field requirements
- Consider nullable constraints based on business rules

### 3. Conversion Logic
- Always use `safe_*` functions for robust error handling
- Test conversion logic with sample data first
- Document custom conversion functions

### 4. Performance Considerations
- Exclude unnecessary columns to reduce payload size
- Use appropriate SQL datatypes (VARCHAR vs NVARCHAR, sizes)
- Consider indexing strategy when choosing datatypes

## Troubleshooting

### Column Not Appearing in Target Table
1. Check if column is in `exclusions`
2. Verify `include: true` in applicable rule
3. Check if column exists in metadata.json

### Wrong Datatype in Target Table
1. Check `column_overrides` first (highest priority)
2. Then check `type_overrides` 
3. Finally check `default_rule`

### Conversion Errors
1. Verify conversion_logic syntax
2. Check sample data matches expected format
3. Add error handling in conversion functions

## Related Files

- `pipelines/scripts/load_boards.py` - Main processing logic
- `pipelines/codegen/universal_board_extractor.py` - Metadata discovery
- `configs/registry.json` - Board registry
- `workflows/extract_board_{id}.yaml` - Kestra workflows