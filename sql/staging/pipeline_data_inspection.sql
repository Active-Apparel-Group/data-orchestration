-- ======================================================================
-- Pipeline Data Inspection Queries
-- ======================================================================
-- Purpose: Validate ORDER_LIST pipeline data flow and record counts
-- Date: 2025-07-21
-- Context: After NEW order detection (Task 4.0) - validate data presence

-- ======================================================================
-- 1. SOURCE TABLE: swp_ORDER_LIST_V2 (Input Data)
-- ======================================================================

SELECT 'swp_ORDER_LIST_V2 - Source Data' AS table_name,
       COUNT(*) AS total_records,
       COUNT(CASE WHEN sync_state = 'NEW' THEN 1 END) AS new_records,
       COUNT(CASE WHEN sync_state = 'EXISTING' THEN 1 END) AS existing_records,
       COUNT(CASE WHEN sync_state IS NULL THEN 1 END) AS null_sync_state,
       COUNT(DISTINCT [AAG ORDER NUMBER]) AS unique_aag_orders,
       COUNT(DISTINCT [CUSTOMER NAME]) AS unique_customers,
       MIN([ORDER DATE PO RECEIVED]) AS earliest_order,
       MAX([ORDER DATE PO RECEIVED]) AS latest_order
FROM dbo.swp_ORDER_LIST_V2;

-- Sample records for validation
SELECT TOP 5 
    [AAG ORDER NUMBER],
    [CUSTOMER NAME], 
    [PO NUMBER],
    [ORDER DATE PO RECEIVED],
    sync_state,
    [UNIT OF MEASURE],
    [TOTAL QTY]
FROM dbo.swp_ORDER_LIST_V2
ORDER BY [AAG ORDER NUMBER];

-- ======================================================================
-- 2. TARGET TABLE: ORDER_LIST_V2 (After Headers Merge)
-- ======================================================================

SELECT 'ORDER_LIST_V2 - Target Headers' AS table_name,
       COUNT(*) AS total_records,
       COUNT(DISTINCT [AAG ORDER NUMBER]) AS unique_aag_orders,
       COUNT(DISTINCT [CUSTOMER NAME]) AS unique_customers,
       MIN([ORDER DATE PO RECEIVED]) AS earliest_order,
       MAX([ORDER DATE PO RECEIVED]) AS latest_order
FROM dbo.ORDER_LIST_V2;

-- Sample records
SELECT TOP 5 
    [AAG ORDER NUMBER],
    [CUSTOMER NAME], 
    [PO NUMBER],
    [ORDER DATE PO RECEIVED],
    [UNIT OF MEASURE],
    [TOTAL QTY]
FROM dbo.ORDER_LIST_V2
ORDER BY [AAG ORDER NUMBER];

-- ======================================================================
-- 3. LINE ITEMS: ORDER_LIST_LINES (After Unpivot & Lines Merge)
-- ======================================================================

-- Check if ORDER_LIST_LINES table exists and has data
IF OBJECT_ID('dbo.ORDER_LIST_LINES', 'U') IS NOT NULL
BEGIN
    SELECT 'ORDER_LIST_LINES - Line Items' AS table_name,
           COUNT(*) AS total_line_records,
           COUNT(DISTINCT [AAG ORDER NUMBER]) AS unique_aag_orders,
           COUNT(DISTINCT SIZE_CODE) AS unique_sizes,
           SUM(CAST(QUANTITY AS DECIMAL(10,2))) AS total_quantity,
           COUNT(CASE WHEN QUANTITY > 0 THEN 1 END) AS non_zero_quantities
    FROM dbo.ORDER_LIST_LINES;

    -- Sample line items
    SELECT TOP 10 
        [AAG ORDER NUMBER],
        [CUSTOMER NAME],
        SIZE_CODE,
        QUANTITY,
        LINE_NUMBER
    FROM dbo.ORDER_LIST_LINES
    WHERE QUANTITY > 0
    ORDER BY [AAG ORDER NUMBER], SIZE_CODE;
END
ELSE
BEGIN
    SELECT 'ORDER_LIST_LINES - NOT FOUND' AS table_name,
           0 AS total_line_records,
           'Table does not exist' AS status;
END

-- ======================================================================
-- 4. DELTA TABLES: Check for delta tracking tables
-- ======================================================================

-- Check for common delta table patterns
DECLARE @sql NVARCHAR(MAX);
DECLARE @tables TABLE (table_name NVARCHAR(128));

-- Find tables with DELTA or similar patterns
INSERT INTO @tables
SELECT TABLE_NAME 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_TYPE = 'BASE TABLE' 
  AND (TABLE_NAME LIKE '%DELTA%' 
       OR TABLE_NAME LIKE '%_NEW%' 
       OR TABLE_NAME LIKE '%_CHANGES%'
       OR TABLE_NAME LIKE '%ORDER_LIST%STAGING%');

-- Display delta tables found
SELECT 'Delta Tables Found' AS category,
       table_name,
       'Exists' AS status
FROM @tables;

-- ======================================================================
-- 5. SIZE COLUMNS VALIDATION: Verify dynamic size detection
-- ======================================================================

-- Count non-zero size columns in source
SELECT 'Size Columns Analysis' AS category,
       COUNT(*) AS total_records;

-- Get column names for size columns (between UNIT OF MEASURE and TOTAL QTY)
WITH size_columns AS (
    SELECT COLUMN_NAME, ORDINAL_POSITION
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'swp_ORDER_LIST_V2'
      AND ORDINAL_POSITION > (
          SELECT ORDINAL_POSITION 
          FROM INFORMATION_SCHEMA.COLUMNS 
          WHERE TABLE_NAME = 'swp_ORDER_LIST_V2' 
            AND COLUMN_NAME = 'UNIT OF MEASURE'
      )
      AND ORDINAL_POSITION < (
          SELECT ORDINAL_POSITION 
          FROM INFORMATION_SCHEMA.COLUMNS 
          WHERE TABLE_NAME = 'swp_ORDER_LIST_V2' 
            AND COLUMN_NAME = 'TOTAL QTY'
      )
)
SELECT 'Dynamic Size Columns' AS category,
       COUNT(*) AS total_size_columns,
       MIN(COLUMN_NAME) AS first_size_column,
       MAX(COLUMN_NAME) AS last_size_column
FROM size_columns;

-- ======================================================================
-- 6. GREYSON PO 4755 VALIDATION: Our test case
-- ======================================================================

SELECT 'GREYSON PO 4755 Validation' AS validation_type,
       COUNT(*) AS greyson_records,
       COUNT(CASE WHEN [PO NUMBER] = '4755' THEN 1 END) AS po_4755_records,
       COUNT(DISTINCT [AAG ORDER NUMBER]) AS unique_aag_orders,
       AVG(CAST([TOTAL QTY] AS DECIMAL(10,2))) AS avg_total_qty
FROM dbo.swp_ORDER_LIST_V2
WHERE [CUSTOMER NAME] LIKE '%GREYSON%';

-- Sample GREYSON records
SELECT TOP 10 
    [AAG ORDER NUMBER],
    [CUSTOMER NAME], 
    [PO NUMBER],
    [ORDER DATE PO RECEIVED],
    sync_state,
    [TOTAL QTY]
FROM dbo.swp_ORDER_LIST_V2
WHERE [CUSTOMER NAME] LIKE '%GREYSON%'
ORDER BY [AAG ORDER NUMBER];

-- ======================================================================
-- 7. PIPELINE SUMMARY: Overall health check
-- ======================================================================

SELECT 'Pipeline Summary' AS summary_type,
       'Source Records' AS metric,
       COUNT(*) AS value
FROM dbo.swp_ORDER_LIST_V2

UNION ALL

SELECT 'Pipeline Summary' AS summary_type,
       'Target Records' AS metric,
       COUNT(*) AS value
FROM dbo.ORDER_LIST_V2

UNION ALL

SELECT 'Pipeline Summary' AS summary_type,
       'NEW Orders Detected' AS metric,
       COUNT(*) AS value
FROM dbo.swp_ORDER_LIST_V2
WHERE sync_state = 'NEW';
