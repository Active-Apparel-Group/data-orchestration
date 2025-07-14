# Hash Pipeline Process - Customer Orders

## Overview
The hash-based change detection system creates SHA256 hashes on-the-fly to identify changes between ORDERS_UNIFIED source data and existing Monday.com records.

## Hash Generation Workflow

### 1. Source Data Processing
- **Location**: `change_detector.py` → `_generate_row_hash()`
- **Input**: Row from ORDERS_UNIFIED table
- **Process**: 
  - Exclude system fields (record_uuid, snapshot_date, customer_filter, row_hash)
  - Sort remaining columns for consistency
  - Concatenate values with '|' separator
  - Generate SHA256 hash

### 2. Change Detection Process
```
ORDERS_UNIFIED → Hash Generation → Compare with Snapshot → Classify Changes
                                                           ↓
                                            NEW | UNCHANGED | CHANGED | DELETED
```

### 3. Hash Storage
- **Runtime**: Generated on-the-fly during processing
- **Persistence**: Stored in `ORDERS_UNIFIED_SNAPSHOT` table as `row_hash`
- **Comparison**: Current hash vs stored hash determines change status

## Key Implementation Details

### Hash Exclusions
- `record_uuid` - System generated identifier
- `snapshot_date` - System timestamp
- `customer_filter` - System metadata  
- `row_hash` - The hash field itself

### Change Classification
- **NEW**: Record exists in source but not in snapshot
- **UNCHANGED**: Hash matches between source and snapshot
- **CHANGED**: Hash differs between source and snapshot
- **DELETED**: Record exists in snapshot but not in source

## Technical Notes
- Hash algorithm: SHA256
- Encoding: UTF-8
- Field separator: '|' (pipe character)
- Field ordering: Alphabetical (sorted) for consistency
