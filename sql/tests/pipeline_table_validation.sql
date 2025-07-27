-- ======================================================================
-- Simple Table Validation - Row Counts Only
-- ======================================================================
-- Purpose: Quick validation of pipeline tables after Task 4.0 completion
-- Date: 2025-07-21
-- Context: Verify table states before Task 5.0 (Complete Pipeline Integration)

-- Based on sync_order_list.toml configuration:
-- source_table = "swp_ORDER_LIST_V2" (should have 69 records)
-- target_table = "ORDER_LIST_V2" (should be empty until templates run)  
-- lines_table = "ORDER_LIST_LINES" (should be empty until templates run)

SELECT * FROM (
    SELECT 
        'swp_ORDER_LIST_V2' AS table_name,
        COUNT(*) AS row_count,
        'Source table with NEW order detection completed' AS status,
        1 as sort_order
    FROM dbo.swp_ORDER_LIST_V2

    UNION ALL

    SELECT 
        'ORDER_LIST_V2' AS table_name,
        CASE WHEN OBJECT_ID('dbo.ORDER_LIST_V2', 'U') IS NOT NULL 
             THEN (SELECT COUNT(*) FROM dbo.ORDER_LIST_V2)
             ELSE -1 
        END AS row_count,
        CASE WHEN OBJECT_ID('dbo.ORDER_LIST_V2', 'U') IS NOT NULL 
             THEN 'Target table exists - awaiting template execution'
             ELSE 'Target table does not exist'
        END AS status,
        2 as sort_order

    UNION ALL

    SELECT 
        'ORDER_LIST_LINES' AS table_name,
        CASE WHEN OBJECT_ID('dbo.ORDER_LIST_LINES', 'U') IS NOT NULL 
             THEN (SELECT COUNT(*) FROM dbo.ORDER_LIST_LINES)
             ELSE -1 
        END AS row_count,
        CASE WHEN OBJECT_ID('dbo.ORDER_LIST_LINES', 'U') IS NOT NULL 
             THEN 'Lines table exists - awaiting template execution'
             ELSE 'Lines table does not exist'
        END AS status,
        3 as sort_order
) AS validation_results
ORDER BY sort_order;
