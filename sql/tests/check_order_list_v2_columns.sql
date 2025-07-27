-- Check ORDER_LIST_V2 Table Schema for Task 5.0 Template Fix

-- Get all column names and check for critical ones
WITH cte as (
    SELECT 
        COLUMN_NAME,
        DATA_TYPE,
        CASE 
            WHEN COLUMN_NAME IN ('record_uuid', 'sync_state') THEN 'CRITICAL'
            ELSE 'OTHER'
        END as importance
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'ORDER_LIST_V2' 
      AND TABLE_SCHEMA = 'dbo'
)

SELECT 
    * from cte where importance = 'CRITICAL'