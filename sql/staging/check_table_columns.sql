-- ======================================================================
-- Quick Column Inspection for Pipeline Tables
-- ======================================================================
-- Purpose: Get actual column names from our pipeline tables
-- Date: 2025-07-21

-- Check columns in swp_ORDER_LIST_V2
SELECT 'swp_ORDER_LIST_V2 Columns' AS table_info,
       COLUMN_NAME,
       DATA_TYPE,
       ORDINAL_POSITION
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'swp_ORDER_LIST_V2'
  AND ORDINAL_POSITION <= 10
ORDER BY ORDINAL_POSITION;

-- Check if ORDER_LIST_V2 exists and get its columns
IF OBJECT_ID('dbo.ORDER_LIST_V2', 'U') IS NOT NULL
BEGIN
    SELECT 'ORDER_LIST_V2 Columns' AS table_info,
           COLUMN_NAME,
           DATA_TYPE,
           ORDINAL_POSITION
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'ORDER_LIST_V2'
      AND ORDINAL_POSITION <= 10
    ORDER BY ORDINAL_POSITION;
END
ELSE
BEGIN
    SELECT 'ORDER_LIST_V2 NOT FOUND' AS table_info,
           'N/A' AS COLUMN_NAME,
           'N/A' AS DATA_TYPE,
           0 AS ORDINAL_POSITION;
END

-- Check if ORDER_LIST_LINES exists
IF OBJECT_ID('dbo.ORDER_LIST_LINES', 'U') IS NOT NULL
BEGIN
    SELECT 'ORDER_LIST_LINES Columns' AS table_info,
           COLUMN_NAME,
           DATA_TYPE,
           ORDINAL_POSITION
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'ORDER_LIST_LINES'
    ORDER BY ORDINAL_POSITION;
END
ELSE
BEGIN
    SELECT 'ORDER_LIST_LINES NOT FOUND' AS table_info,
           'N/A' AS COLUMN_NAME,
           'N/A' AS DATA_TYPE,
           0 AS ORDINAL_POSITION;
END

-- Simple record counts
SELECT 'swp_ORDER_LIST_V2' AS table_name,
       COUNT(*) AS record_count
FROM dbo.swp_ORDER_LIST_V2

UNION ALL

SELECT 'ORDER_LIST_V2' AS table_name,
       COUNT(*) AS record_count
FROM dbo.ORDER_LIST_V2;
