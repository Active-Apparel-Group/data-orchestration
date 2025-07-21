-- Migration 001_01: Drop swp_ORDER_LIST_V2 Table
-- Purpose: Remove existing incomplete shadow staging table
-- Reason: Schema mismatch with complete ORDER_LIST schema causing ordinal position errors
-- Database: orders
-- Created: 2025-07-21
-- Author: ORDER_LIST Delta Monday Sync - Schema Fix

-- =============================================================================
-- DROP: swp_ORDER_LIST_V2 Shadow Staging Table
-- This table has incomplete schema compared to complete ORDER_LIST schema
-- Causing UNIT OF MEASURE and TOTAL QTY to be in wrong ordinal positions
-- =============================================================================

-- Drop table if it exists (safe operation)
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'swp_ORDER_LIST_V2' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    PRINT 'Dropping existing swp_ORDER_LIST_V2 table with incomplete schema...';
    DROP TABLE dbo.swp_ORDER_LIST_V2;
    PRINT 'SUCCESS: swp_ORDER_LIST_V2 table dropped.';
END
ELSE
BEGIN
    PRINT 'INFO: swp_ORDER_LIST_V2 table does not exist - no action needed.';
END

-- Verification: Ensure table is dropped
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'swp_ORDER_LIST_V2' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    PRINT 'VERIFICATION SUCCESS: swp_ORDER_LIST_V2 table confirmed dropped.';
END
ELSE
BEGIN
    PRINT 'ERROR: swp_ORDER_LIST_V2 table still exists after drop attempt.';
    RAISERROR('Failed to drop swp_ORDER_LIST_V2 table', 16, 1);
END

-- =============================================================================
-- Success message
-- =============================================================================

PRINT 'Migration 001_01: Drop swp_ORDER_LIST_V2 completed successfully';
PRINT '';
PRINT 'Next Steps:';
PRINT '  1. Run 001_02_recreate_swp_order_list_v2.sql to create table with complete schema';
PRINT '  2. Run 001_03_insert_test_data.sql to populate with GREYSON PO 4755 data';
PRINT '  3. Validate ordinal positions match ORDER_LIST_V2 for ConfigParser compatibility';
