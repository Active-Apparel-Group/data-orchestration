-- ======================================================================
-- Corrected Pipeline Data Inspection Queries
-- ======================================================================
-- Purpose: Validate ORDER_LIST pipeline data flow with correct column names
-- Date: 2025-07-21
-- Context: After NEW order detection (Task 4.0) - using validated DDL columns

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

-- Check if ORDER_LIST_V2 exists first
IF OBJECT_ID('dbo.ORDER_LIST_V2', 'U') IS NOT NULL
BEGIN
    SELECT 'ORDER_LIST_V2 - Target Headers' AS table_name,
           COUNT(*) AS total_records,
           COUNT(DISTINCT [AAG ORDER NUMBER]) AS unique_aag_orders,
           COUNT(DISTINCT [CUSTOMER NAME]) AS unique_customers,
           MIN([ORDER DATE PO RECEIVED]) AS earliest_order,
           MAX([ORDER DATE PO RECEIVED]) AS latest_order
    FROM dbo.ORDER_LIST_V2;

    -- Sample records if any exist
    IF EXISTS (SELECT 1 FROM dbo.ORDER_LIST_V2)
    BEGIN
        SELECT TOP 5 
            [AAG ORDER NUMBER],
            [CUSTOMER NAME], 
            [PO NUMBER],
            [ORDER DATE PO RECEIVED],
            [UNIT OF MEASURE],
            [TOTAL QTY]
        FROM dbo.ORDER_LIST_V2
        ORDER BY [AAG ORDER NUMBER];
    END
    ELSE
    BEGIN
        SELECT 'ORDER_LIST_V2 - EMPTY TABLE' AS status,
               'No records found' AS message;
    END
END
ELSE
BEGIN
    SELECT 'ORDER_LIST_V2 - NOT FOUND' AS table_name,
           0 AS total_records,
           'Table does not exist' AS status;
END

-- ======================================================================
-- 3. GREYSON PO 4755 VALIDATION: Our test case
-- ======================================================================

SELECT 'GREYSON PO 4755 Validation' AS validation_type,
       COUNT(*) AS greyson_records,
       COUNT(CASE WHEN [PO NUMBER] = '4755' THEN 1 END) AS po_4755_records,
       COUNT(DISTINCT [AAG ORDER NUMBER]) AS unique_aag_orders,
       AVG(CAST([TOTAL QTY] AS DECIMAL(10,2))) AS avg_total_qty,
       COUNT(CASE WHEN sync_state = 'NEW' THEN 1 END) AS new_state_records,
       COUNT(CASE WHEN sync_state IS NULL THEN 1 END) AS null_state_records
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
-- 4. SIZE COLUMNS VALIDATION: Verify dynamic size detection
-- ======================================================================

-- Get size column metadata (between UNIT OF MEASURE and TOTAL QTY)
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
SELECT 'Dynamic Size Columns Analysis' AS category,
       COUNT(*) AS total_size_columns,
       MIN(COLUMN_NAME) AS first_size_column,
       MAX(COLUMN_NAME) AS last_size_column,
       MIN(ORDINAL_POSITION) AS start_position,
       MAX(ORDINAL_POSITION) AS end_position
FROM size_columns;

-- ======================================================================
-- 5. PIPELINE SUMMARY: Overall health check
-- ======================================================================

SELECT 'Pipeline Summary' AS summary_type,
       'Source Records (swp_ORDER_LIST_V2)' AS metric,
       COUNT(*) AS value
FROM dbo.swp_ORDER_LIST_V2

UNION ALL

SELECT 'Pipeline Summary' AS summary_type,
       'Target Records (ORDER_LIST_V2)' AS metric,
       CASE WHEN OBJECT_ID('dbo.ORDER_LIST_V2', 'U') IS NOT NULL 
            THEN (SELECT COUNT(*) FROM dbo.ORDER_LIST_V2)
            ELSE 0 
       END AS value

UNION ALL

SELECT 'Pipeline Summary' AS summary_type,
       'NEW Orders Detected' AS metric,
       COUNT(*) AS value
FROM dbo.swp_ORDER_LIST_V2
WHERE sync_state = 'NEW'

UNION ALL

SELECT 'Pipeline Summary' AS summary_type,
       'NULL sync_state Records' AS metric,
       COUNT(*) AS value
FROM dbo.swp_ORDER_LIST_V2
WHERE sync_state IS NULL;
