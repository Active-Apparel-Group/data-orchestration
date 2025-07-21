-- Migration 001_04: Validate Schema Compatibility between swp_ORDER_LIST_V2 and ORDER_LIST_V2
-- Purpose: Ensure complete schema match for ConfigParser ordinal position detection
-- Database: orders
-- Created: 2025-07-21
-- Author: ORDER_LIST Delta Monday Sync - Schema Fix

-- =============================================================================
-- SCHEMA VALIDATION: Compare column structure and ordinal positions
-- =============================================================================

-- Compare table schemas
PRINT 'SCHEMA VALIDATION: Comparing swp_ORDER_LIST_V2 and ORDER_LIST_V2';
PRINT '=================================================================';

-- Get column counts
DECLARE @swp_count INT, @main_count INT;

SELECT @swp_count = COUNT(*) 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'swp_ORDER_LIST_V2' 
  AND TABLE_SCHEMA = 'dbo';

SELECT @main_count = COUNT(*) 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'ORDER_LIST_V2' 
  AND TABLE_SCHEMA = 'dbo';

PRINT 'Column Count Comparison:';
PRINT '  swp_ORDER_LIST_V2: ' + CAST(@swp_count AS VARCHAR(10)) + ' columns';
PRINT '  ORDER_LIST_V2: ' + CAST(@main_count AS VARCHAR(10)) + ' columns';

IF @swp_count = @main_count
    PRINT '✅ Column counts match';
ELSE
    PRINT '❌ Column count mismatch - Schema compatibility issue detected';

-- =============================================================================
-- ORDINAL POSITION VALIDATION: Critical for ConfigParser size column detection
-- =============================================================================

PRINT '';
PRINT 'ORDINAL POSITION VALIDATION:';
PRINT '=============================';

-- Check critical columns for ConfigParser
WITH swp_positions AS (
    SELECT 
        COLUMN_NAME,
        ORDINAL_POSITION,
        DATA_TYPE,
        IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'swp_ORDER_LIST_V2' 
      AND TABLE_SCHEMA = 'dbo'
      AND COLUMN_NAME IN ('UNIT OF MEASURE', 'TOTAL QTY')
),
main_positions AS (
    SELECT 
        COLUMN_NAME,
        ORDINAL_POSITION,
        DATA_TYPE,
        IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'ORDER_LIST_V2' 
      AND TABLE_SCHEMA = 'dbo'
      AND COLUMN_NAME IN ('UNIT OF MEASURE', 'TOTAL QTY')
)
SELECT 
    COALESCE(s.COLUMN_NAME, m.COLUMN_NAME) as COLUMN_NAME,
    s.ORDINAL_POSITION as swp_position,
    m.ORDINAL_POSITION as main_position,
    CASE 
        WHEN s.ORDINAL_POSITION = m.ORDINAL_POSITION THEN '✅ Match'
        WHEN s.ORDINAL_POSITION IS NULL THEN '❌ Missing in swp'
        WHEN m.ORDINAL_POSITION IS NULL THEN '❌ Missing in main'
        ELSE '❌ Position mismatch'
    END as status
FROM swp_positions s
FULL OUTER JOIN main_positions m ON s.COLUMN_NAME = m.COLUMN_NAME
ORDER BY COALESCE(s.ORDINAL_POSITION, m.ORDINAL_POSITION);

-- =============================================================================
-- SIZE COLUMNS VALIDATION: Ensure 251 size columns match between tables
-- =============================================================================

PRINT '';
PRINT 'SIZE COLUMNS VALIDATION:';
PRINT '========================';

-- Count size columns in both tables (columns between UNIT OF MEASURE and TOTAL QTY)
DECLARE @swp_size_count INT, @main_size_count INT;
DECLARE @unit_pos_swp INT, @total_pos_swp INT;
DECLARE @unit_pos_main INT, @total_pos_main INT;

-- Get positions for swp table
SELECT @unit_pos_swp = ORDINAL_POSITION 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'swp_ORDER_LIST_V2' AND COLUMN_NAME = 'UNIT OF MEASURE';

SELECT @total_pos_swp = ORDINAL_POSITION 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'swp_ORDER_LIST_V2' AND COLUMN_NAME = 'TOTAL QTY';

-- Get positions for main table
SELECT @unit_pos_main = ORDINAL_POSITION 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'ORDER_LIST_V2' AND COLUMN_NAME = 'UNIT OF MEASURE';

SELECT @total_pos_main = ORDINAL_POSITION 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'ORDER_LIST_V2' AND COLUMN_NAME = 'TOTAL QTY';

-- Count size columns (between UNIT OF MEASURE and TOTAL QTY)
SELECT @swp_size_count = COUNT(*) 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'swp_ORDER_LIST_V2' 
  AND ORDINAL_POSITION > @unit_pos_swp 
  AND ORDINAL_POSITION < @total_pos_swp;

SELECT @main_size_count = COUNT(*) 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'ORDER_LIST_V2' 
  AND ORDINAL_POSITION > @unit_pos_main 
  AND ORDINAL_POSITION < @total_pos_main;

PRINT 'Size Column Analysis:';
PRINT '  UNIT OF MEASURE position - swp: ' + CAST(ISNULL(@unit_pos_swp, 0) AS VARCHAR(10)) + ', main: ' + CAST(ISNULL(@unit_pos_main, 0) AS VARCHAR(10));
PRINT '  TOTAL QTY position - swp: ' + CAST(ISNULL(@total_pos_swp, 0) AS VARCHAR(10)) + ', main: ' + CAST(ISNULL(@total_pos_main, 0) AS VARCHAR(10));
PRINT '  Size columns count - swp: ' + CAST(@swp_size_count AS VARCHAR(10)) + ', main: ' + CAST(@main_size_count AS VARCHAR(10));

IF @swp_size_count = @main_size_count AND @swp_size_count = 251
    PRINT '✅ Size column count matches expected 251 columns';
ELSE
    PRINT '❌ Size column count mismatch - ConfigParser may fail';

-- =============================================================================
-- MISSING COLUMNS ANALYSIS: Identify any schema differences
-- =============================================================================

PRINT '';
PRINT 'MISSING COLUMNS ANALYSIS:';
PRINT '==========================';

-- Columns in ORDER_LIST_V2 but missing from swp_ORDER_LIST_V2
PRINT 'Columns missing from swp_ORDER_LIST_V2:';
SELECT COUNT(*) as missing_count
FROM INFORMATION_SCHEMA.COLUMNS m
WHERE m.TABLE_NAME = 'ORDER_LIST_V2' 
  AND m.TABLE_SCHEMA = 'dbo'
  AND NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS s 
    WHERE s.TABLE_NAME = 'swp_ORDER_LIST_V2' 
      AND s.TABLE_SCHEMA = 'dbo'
      AND s.COLUMN_NAME = m.COLUMN_NAME
  );

-- Columns in swp_ORDER_LIST_V2 but missing from ORDER_LIST_V2  
PRINT 'Columns missing from ORDER_LIST_V2:';
SELECT COUNT(*) as extra_count
FROM INFORMATION_SCHEMA.COLUMNS s
WHERE s.TABLE_NAME = 'swp_ORDER_LIST_V2' 
  AND s.TABLE_SCHEMA = 'dbo'
  AND NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS m 
    WHERE m.TABLE_NAME = 'ORDER_LIST_V2' 
      AND m.TABLE_SCHEMA = 'dbo'
      AND m.COLUMN_NAME = s.COLUMN_NAME
  );

-- =============================================================================
-- DATA VALIDATION: Ensure test data populated correctly
-- =============================================================================

PRINT '';
PRINT 'DATA VALIDATION:';
PRINT '================';

DECLARE @data_count INT;
SELECT @data_count = COUNT(*) FROM dbo.swp_ORDER_LIST_V2;

DECLARE @greyson_count INT;
SELECT @greyson_count = COUNT(*) FROM dbo.swp_ORDER_LIST_V2 WHERE [CUSTOMER NAME] LIKE '%GREYSON%';

PRINT 'Test Data Summary:';
PRINT '  Total records: ' + CAST(@data_count AS VARCHAR(10));
PRINT '  GREYSON records: ' + CAST(@greyson_count AS VARCHAR(10));

-- Sample data validation
SELECT TOP 3
    [AAG ORDER NUMBER],
    [CUSTOMER NAME], 
    [PO NUMBER],
    [UNIT OF MEASURE],
    [TOTAL QTY],
    sync_state,
    created_at
FROM dbo.swp_ORDER_LIST_V2;

-- =============================================================================
-- FINAL VALIDATION SUMMARY
-- =============================================================================

PRINT '';
PRINT 'VALIDATION SUMMARY:';
PRINT '===================';

DECLARE @validation_status VARCHAR(10) = '✅ PASS';

-- Check all critical conditions
IF @swp_count != @main_count 
    SET @validation_status = '❌ FAIL';
    
IF @swp_size_count != 251 
    SET @validation_status = '❌ FAIL';
    
IF @unit_pos_swp != @unit_pos_main OR @total_pos_swp != @total_pos_main
    SET @validation_status = '❌ FAIL';
    
IF @data_count = 0
    SET @validation_status = '❌ FAIL';

PRINT 'Overall Status: ' + @validation_status;
PRINT '';

IF @validation_status = '✅ PASS'
BEGIN
    PRINT 'SUCCESS: Schema validation complete - Ready for ConfigParser testing';
    PRINT '';
    PRINT 'Next Steps:';
    PRINT '  1. Test ConfigParser with real database connection';
    PRINT '  2. Validate size column detection with swp_ORDER_LIST_V2';
    PRINT '  3. Execute delta sync testing with GREYSON PO 4755 data';
END
ELSE
BEGIN
    PRINT 'FAILED: Schema validation issues detected';
    PRINT '';
    PRINT 'Required Actions:';
    PRINT '  1. Review schema differences above';
    PRINT '  2. Fix ordinal position mismatches';
    PRINT '  3. Re-run migration sequence if needed';
END
