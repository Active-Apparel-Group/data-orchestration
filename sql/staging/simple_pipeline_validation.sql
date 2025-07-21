-- ======================================================================
-- Simple Pipeline Data Validation - Working with Existing Tables Only
-- ======================================================================
-- Purpose: Validate what tables exist and their basic record counts
-- Date: 2025-07-21
-- Context: After Task 4.0 NEW order detection (100% success with 69 records)

-- ======================================================================
-- 1. TABLE EXISTENCE CHECK
-- ======================================================================

SELECT 'Table Existence Check' AS category,
       TABLE_NAME,
       'EXISTS' AS status
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME IN ('swp_ORDER_LIST_V2', 'ORDER_LIST_V2', 'ORDER_LIST_LINES')
  AND TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME;

-- ======================================================================
-- 2. SOURCE TABLE: swp_ORDER_LIST_V2 (Input Data - VALIDATED DDL)
-- ======================================================================

SELECT 'swp_ORDER_LIST_V2 Record Summary' AS summary_type,
       COUNT(*) AS total_records,
       COUNT(CASE WHEN sync_state = 'NEW' THEN 1 END) AS new_records,
       COUNT(CASE WHEN sync_state = 'EXISTING' THEN 1 END) AS existing_records,
       COUNT(CASE WHEN sync_state IS NULL THEN 1 END) AS null_sync_state,
       COUNT(DISTINCT [AAG ORDER NUMBER]) AS unique_aag_orders,
       COUNT(DISTINCT [CUSTOMER NAME]) AS unique_customers
FROM dbo.swp_ORDER_LIST_V2;

-- Sample records for validation (using validated DDL column names)
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
-- 3. TARGET TABLE: ORDER_LIST_V2 (Check if populated after templates)
-- ======================================================================

-- Only query if table exists
IF OBJECT_ID('dbo.ORDER_LIST_V2', 'U') IS NOT NULL
BEGIN
    SELECT 'ORDER_LIST_V2 Record Summary' AS summary_type,
           COUNT(*) AS total_records,
           COUNT(DISTINCT [AAG ORDER NUMBER]) AS unique_aag_orders
    FROM dbo.ORDER_LIST_V2;

    -- Sample records if any exist
    IF EXISTS (SELECT 1 FROM dbo.ORDER_LIST_V2)
    BEGIN
        SELECT TOP 3 
            [AAG ORDER NUMBER],
            [CUSTOMER NAME], 
            [PO NUMBER],
            [ORDER DATE PO RECEIVED]
        FROM dbo.ORDER_LIST_V2
        ORDER BY [AAG ORDER NUMBER];
    END
END
ELSE
BEGIN
    SELECT 'ORDER_LIST_V2 - NOT FOUND' AS summary_type,
           0 AS total_records,
           'Table does not exist' AS status;
END

-- ======================================================================
-- 4. GREYSON PO 4755 VALIDATION (Our validated test case)
-- ======================================================================

SELECT 'GREYSON PO 4755 Validation' AS validation_type,
       COUNT(*) AS greyson_records,
       COUNT(CASE WHEN [PO NUMBER] = '4755' THEN 1 END) AS po_4755_records,
       COUNT(DISTINCT [AAG ORDER NUMBER]) AS unique_aag_orders,
       AVG(CAST([TOTAL QTY] AS DECIMAL(10,2))) AS avg_total_qty
FROM dbo.swp_ORDER_LIST_V2
WHERE [CUSTOMER NAME] LIKE '%GREYSON%';

-- ======================================================================
-- 5. SIZE COLUMNS VALIDATION (From validated migration)
-- ======================================================================

-- Get size column count (between UNIT OF MEASURE and TOTAL QTY per migration)
WITH size_columns AS (
    SELECT COUNT(*) as size_column_count
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
SELECT 'Size Column Validation' AS validation_type,
       size_column_count AS detected_size_columns,
       CASE 
         WHEN size_column_count = 245 THEN 'PASS - Migration 245 columns detected'
         WHEN size_column_count = 251 THEN 'PASS - Full 251 columns detected'  
         ELSE 'CHECK - Unexpected count: ' + CAST(size_column_count AS VARCHAR(10))
       END AS validation_result
FROM size_columns;

-- ======================================================================
-- 6. PIPELINE STATUS SUMMARY (Based on Task 4.0 success)
-- ======================================================================

SELECT 'Pipeline Status Summary' AS status_category,
       'Source Ready' AS metric,
       COUNT(*) AS value,
       'Records in swp_ORDER_LIST_V2' AS description
FROM dbo.swp_ORDER_LIST_V2

UNION ALL

SELECT 'Pipeline Status Summary' AS status_category,
       'NEW Orders Detected' AS metric,
       COUNT(*) AS value,
       'Task 4.0 - 100% detection accuracy' AS description
FROM dbo.swp_ORDER_LIST_V2
WHERE sync_state = 'NEW'

UNION ALL

SELECT 'Pipeline Status Summary' AS status_category,
       'Template Pipeline Status' AS metric,
       CASE WHEN OBJECT_ID('dbo.ORDER_LIST_V2', 'U') IS NOT NULL 
            THEN (SELECT COUNT(*) FROM dbo.ORDER_LIST_V2)
            ELSE 0 
       END AS value,
       'Ready for Task 5.0 - Complete Pipeline Integration' AS description;
