-- Check Schema Consistency for ALL ORDER_LIST Tables in TOML Config
-- Purpose: Validate sync_state, batch_id, synced_at columns across all tables
-- Created: 2025-07-21 (Task 5.0 Schema Debugging)
-- Usage: python tools/run_migration.py sql/tests/check_order_list_schema_consistency.sql --database orders --show-results

PRINT '======================================================================';
PRINT 'SCHEMA CONSISTENCY CHECK: ORDER_LIST Tables';
PRINT '======================================================================';

-- Table 1: swp_ORDER_LIST_V2 (source_table)
PRINT '';
PRINT '1. swp_ORDER_LIST_V2 (source_table)';
PRINT '====================================';
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'swp_ORDER_LIST_V2'
AND COLUMN_NAME IN ('sync_state', 'batch_id', 'synced_at', 'sync_completed_at', 'record_uuid')
ORDER BY COLUMN_NAME;

-- Table 2: ORDER_LIST_V2 (target_table)
PRINT '';
PRINT '2. ORDER_LIST_V2 (target_table)';
PRINT '===============================';
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'ORDER_LIST_V2'
AND COLUMN_NAME IN ('sync_state', 'batch_id', 'synced_at', 'sync_completed_at', 'record_uuid')
ORDER BY COLUMN_NAME;

-- Table 3: ORDER_LIST_LINES (lines_table)
PRINT '';
PRINT '3. ORDER_LIST_LINES (lines_table)';
PRINT '=================================';
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'ORDER_LIST_LINES'
AND COLUMN_NAME IN ('sync_state', 'batch_id', 'synced_at', 'sync_completed_at', 'record_uuid', 'parent_uuid')
ORDER BY COLUMN_NAME;

-- Table 4: ORDER_LIST_DELTA (delta_table)
PRINT '';
PRINT '4. ORDER_LIST_DELTA (delta_table)';
PRINT '=================================';
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'ORDER_LIST_DELTA'
AND COLUMN_NAME IN ('sync_state', 'batch_id', 'synced_at', 'sync_completed_at', 'record_uuid', 'action_type')
ORDER BY COLUMN_NAME;

-- Table 5: ORDER_LIST_LINES_DELTA (lines_delta_table)
PRINT '';
PRINT '5. ORDER_LIST_LINES_DELTA (lines_delta_table)';
PRINT '=============================================';
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'ORDER_LIST_LINES_DELTA'
AND COLUMN_NAME IN ('sync_state', 'batch_id', 'synced_at', 'sync_completed_at', 'record_uuid', 'parent_uuid', 'action_type')
ORDER BY COLUMN_NAME;

PRINT '';
PRINT '======================================================================';
PRINT 'CONSISTENCY ANALYSIS:';
PRINT '======================================================================';

-- Count which tables have each column
PRINT '';
PRINT 'COLUMN AVAILABILITY ACROSS TABLES:';
PRINT '===================================';

SELECT 
    'sync_state' as column_name,
    COUNT(*) as tables_with_column
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME IN ('swp_ORDER_LIST_V2', 'ORDER_LIST_V2', 'ORDER_LIST_LINES', 'ORDER_LIST_DELTA', 'ORDER_LIST_LINES_DELTA')
AND COLUMN_NAME = 'sync_state'

UNION ALL

SELECT 
    'batch_id' as column_name,
    COUNT(*) as tables_with_column
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME IN ('swp_ORDER_LIST_V2', 'ORDER_LIST_V2', 'ORDER_LIST_LINES', 'ORDER_LIST_DELTA', 'ORDER_LIST_LINES_DELTA')
AND COLUMN_NAME = 'batch_id'

UNION ALL

SELECT 
    'synced_at' as column_name,
    COUNT(*) as tables_with_column
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME IN ('swp_ORDER_LIST_V2', 'ORDER_LIST_V2', 'ORDER_LIST_LINES', 'ORDER_LIST_DELTA', 'ORDER_LIST_LINES_DELTA')
AND COLUMN_NAME = 'synced_at'

UNION ALL

SELECT 
    'sync_completed_at' as column_name,
    COUNT(*) as tables_with_column
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME IN ('swp_ORDER_LIST_V2', 'ORDER_LIST_V2', 'ORDER_LIST_LINES', 'ORDER_LIST_DELTA', 'ORDER_LIST_LINES_DELTA')
AND COLUMN_NAME = 'sync_completed_at'

UNION ALL

SELECT 
    'record_uuid' as column_name,
    COUNT(*) as tables_with_column
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME IN ('swp_ORDER_LIST_V2', 'ORDER_LIST_V2', 'ORDER_LIST_LINES', 'ORDER_LIST_DELTA', 'ORDER_LIST_LINES_DELTA')
AND COLUMN_NAME = 'record_uuid';

PRINT '';
PRINT 'RECOMMENDATIONS:';
PRINT '================';
PRINT '- All 5 tables should have consistent sync tracking columns';
PRINT '- sync_state should be consistent data type and nullable across all tables';
PRINT '- If batch_id exists in some tables but not others, template needs to handle this';
PRINT '- synced_at vs sync_completed_at naming should be uniform';
PRINT '';
PRINT 'Review completed. Check for mismatched column names, types, or constraints above.';
