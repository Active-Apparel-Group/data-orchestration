-- OPUS Update Boards - Extend Staging Tables for Update Operations
-- Purpose: Add update tracking capabilities to existing staging tables
-- Date: 2025-06-30
-- Reference: OPUS_dev_update_boards.yaml - Task 0.1.1, 0.1.2

-- =============================================================================
-- EXTEND STG_MON_CustMasterSchedule - Task 0.1.1
-- =============================================================================

-- Add update operation tracking columns to master staging table
ALTER TABLE STG_MON_CustMasterSchedule ADD
    board_id BIGINT,
    update_operation VARCHAR(50) DEFAULT 'CREATE',
    update_fields NVARCHAR(MAX),
    source_table VARCHAR(100),
    source_query NVARCHAR(MAX),
    update_batch_id VARCHAR(50),
    validation_status VARCHAR(20) DEFAULT 'PENDING',
    validation_errors NVARCHAR(MAX);

PRINT 'SUCCESS: Extended STG_MON_CustMasterSchedule with update tracking columns';

-- =============================================================================
-- EXTEND STG_MON_CustMasterSchedule_Subitems - Task 0.1.2
-- =============================================================================

-- Add update operation tracking columns to subitems staging table
ALTER TABLE STG_MON_CustMasterSchedule_Subitems ADD
    board_id BIGINT,
    update_operation VARCHAR(50) DEFAULT 'CREATE',
    update_fields NVARCHAR(MAX),
    source_table VARCHAR(100),
    source_query NVARCHAR(MAX),
    update_batch_id VARCHAR(50),
    validation_status VARCHAR(20) DEFAULT 'PENDING',
    validation_errors NVARCHAR(MAX);

PRINT 'SUCCESS: Extended STG_MON_CustMasterSchedule_Subitems with update tracking columns';

-- =============================================================================
-- VALIDATION QUERIES
-- =============================================================================

-- Verify new columns exist in master table
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    COLUMN_DEFAULT,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule'
AND COLUMN_NAME IN (
    'board_id',
    'update_operation',
    'update_fields', 
    'source_table',
    'source_query',
    'update_batch_id',
    'validation_status',
    'validation_errors'
)
ORDER BY COLUMN_NAME;

-- Verify new columns exist in subitems table
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    COLUMN_DEFAULT,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule_Subitems'
AND COLUMN_NAME IN (
    'board_id',
    'update_operation',
    'update_fields',
    'source_table', 
    'source_query',
    'update_batch_id',
    'validation_status',
    'validation_errors'
)
ORDER BY COLUMN_NAME;

PRINT 'COMPLETE: Staging table extensions ready for update operations';
