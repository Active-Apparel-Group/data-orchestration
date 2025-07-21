-- ======================================================================
-- Simple Pipeline Data Inspection
-- ======================================================================
-- Purpose: Basic data validation with correct column names
-- Date: 2025-07-21

-- 1. Source table summary
SELECT 
    'swp_ORDER_LIST_V2' AS table_name,
    COUNT(*) AS total_records,
    COUNT(CASE WHEN sync_state = 'NEW' THEN 1 END) AS new_records,
    COUNT(CASE WHEN sync_state = 'EXISTING' THEN 1 END) AS existing_records,
    COUNT(CASE WHEN sync_state IS NULL THEN 1 END) AS null_sync_state
FROM dbo.swp_ORDER_LIST_V2;
