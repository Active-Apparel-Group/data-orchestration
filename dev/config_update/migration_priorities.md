# Migration Priorities and Recommendations

**Generated:** 2025-06-17 20:45:08

## Recommended Migration Order

## AI Agent Automation Opportunities

The following tasks are well-suited for AI agent automation:

1. **Hardcoded Board ID Replacement**
   - Replace hardcoded board IDs with `mapping.get_board_config()` calls
   - Pattern: `BOARD_ID = "123456"` → `BOARD_ID = mapping.get_board_config('board_name')['board_id']`

2. **Table Name Standardization**
   - Replace hardcoded table names with mapping references
   - Pattern: `"MON_CustMasterSchedule"` → `mapping.get_board_config('customer_master_schedule')['table_name']`

3. **Type Conversion Updates**
   - Standardize type conversions using mapping helpers
   - Pattern: Manual type handling → `mapping.get_sql_type()` and `mapping.convert_field_value()`

4. **YAML File Consolidation**
   - Update references from individual YAML files to master mapping system
   - Pattern: `load_mapping_config('old_file.yaml')` → `mapping.get_board_config('board_name')`

