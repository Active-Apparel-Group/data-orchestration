-- ======================================================================
-- Complete 5-Table Pipeline Workflow Validation
-- ======================================================================
-- Purpose: Validate all 5 tables in the ORDER_LIST delta sync workflow
-- Date: 2025-07-21
-- Context: Check readiness for Task 5.0 (Complete Pipeline Integration)

-- WORKFLOW TABLES (from End-to-End Data/Sync Sequence):
-- 1. swp_ORDER_LIST_V2 (source - should have 69 records)
-- 2. ORDER_LIST_V2 (target - should be empty until Step 1)
-- 3. ORDER_LIST_LINES (lines - should be empty until Step 2)
-- 4. ORDER_LIST_DELTA (delta tracking - should not exist until Step 1)
-- 5. ORDER_LIST_LINES_DELTA (lines delta - should not exist until Step 3)

SELECT * FROM (
    -- Table 1: Source table with NEW order detection completed
    SELECT 
        'swp_ORDER_LIST_V2' AS table_name,
        COUNT(*) AS row_count,
        'Source table - NEW order detection completed (Task 4.0)' AS status,
        'STEP 0 → STEP 1' AS pipeline_step,
        1 as sort_order
    FROM dbo.swp_ORDER_LIST_V2

    UNION ALL

    -- Table 2: Target table for headers merge (Step 1)
    SELECT 
        'ORDER_LIST_V2' AS table_name,
        CASE WHEN OBJECT_ID('dbo.ORDER_LIST_V2', 'U') IS NOT NULL 
             THEN (SELECT COUNT(*) FROM dbo.ORDER_LIST_V2)
             ELSE -1 
        END AS row_count,
        CASE WHEN OBJECT_ID('dbo.ORDER_LIST_V2', 'U') IS NOT NULL 
             THEN 'Target table exists - awaiting merge_headers.j2 (Task 5.1)'
             ELSE 'Target table does not exist - requires creation'
        END AS status,
        'STEP 1' AS pipeline_step,
        2 as sort_order

    UNION ALL

    -- Table 3: Lines table for unpivot sizes (Step 2)
    SELECT 
        'ORDER_LIST_LINES' AS table_name,
        CASE WHEN OBJECT_ID('dbo.ORDER_LIST_LINES', 'U') IS NOT NULL 
             THEN (SELECT COUNT(*) FROM dbo.ORDER_LIST_LINES)
             ELSE -1 
        END AS row_count,
        CASE WHEN OBJECT_ID('dbo.ORDER_LIST_LINES', 'U') IS NOT NULL 
             THEN 'Lines table exists - awaiting unpivot_sizes.j2 (Task 5.2)'
             ELSE 'Lines table does not exist - requires creation'
        END AS status,
        'STEP 2' AS pipeline_step,
        3 as sort_order

    UNION ALL

    -- Table 4: Delta table for Monday.com sync (Step 1 OUTPUT)
    SELECT 
        'ORDER_LIST_DELTA' AS table_name,
        CASE WHEN OBJECT_ID('dbo.ORDER_LIST_DELTA', 'U') IS NOT NULL 
             THEN (SELECT COUNT(*) FROM dbo.ORDER_LIST_DELTA)
             ELSE -1 
        END AS row_count,
        CASE WHEN OBJECT_ID('dbo.ORDER_LIST_DELTA', 'U') IS NOT NULL 
             THEN 'Delta table exists - awaiting Step 1 execution'
             ELSE 'Delta table does not exist - created by merge_headers.j2'
        END AS status,
        'STEP 1 → STEP 4A' AS pipeline_step,
        4 as sort_order

    UNION ALL

    -- Table 5: Lines delta table for Monday.com subitems (Step 3 OUTPUT)
    SELECT 
        'ORDER_LIST_LINES_DELTA' AS table_name,
        CASE WHEN OBJECT_ID('dbo.ORDER_LIST_LINES_DELTA', 'U') IS NOT NULL 
             THEN (SELECT COUNT(*) FROM dbo.ORDER_LIST_LINES_DELTA)
             ELSE -1 
        END AS row_count,
        CASE WHEN OBJECT_ID('dbo.ORDER_LIST_LINES_DELTA', 'U') IS NOT NULL 
             THEN 'Lines delta table exists - awaiting Step 3 execution'
             ELSE 'Lines delta table does not exist - created by merge_lines.j2'
        END AS status,
        'STEP 3 → STEP 4B' AS pipeline_step,
        5 as sort_order

) AS pipeline_validation
ORDER BY sort_order;
