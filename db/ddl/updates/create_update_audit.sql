-- OPUS Update Boards - Create Update Audit Table
-- Purpose: Create MON_UpdateAudit table for rollback capability and audit trail
-- Date: 2025-06-30
-- Reference: OPUS_dev_update_boards.yaml - Task 0.1.3

-- =============================================================================
-- CREATE MON_UpdateAudit TABLE - Task 0.1.3
-- =============================================================================

-- Create comprehensive audit table for all Monday.com update operations
CREATE TABLE MON_UpdateAudit (
    audit_id INT IDENTITY(1,1) PRIMARY KEY,
    batch_id VARCHAR(50) NOT NULL,
    update_operation VARCHAR(50) NOT NULL,
    monday_item_id BIGINT,
    monday_board_id BIGINT,
    column_id VARCHAR(100),
    old_value NVARCHAR(MAX),
    new_value NVARCHAR(MAX),
    update_timestamp DATETIME2 DEFAULT GETUTCDATE(),
    rollback_timestamp DATETIME2 NULL,
    rollback_reason NVARCHAR(500) NULL,
    
    -- Additional metadata for enhanced tracking
    user_id VARCHAR(100),
    source_system VARCHAR(50) DEFAULT 'OPUS_UPDATE_BOARDS',
    api_response_id VARCHAR(100),
    error_message NVARCHAR(MAX),
    
    -- Indexing for performance
    INDEX IX_MON_UpdateAudit_BatchId (batch_id),
    INDEX IX_MON_UpdateAudit_ItemId (monday_item_id),
    INDEX IX_MON_UpdateAudit_BoardId (monday_board_id),
    INDEX IX_MON_UpdateAudit_Timestamp (update_timestamp)
);

PRINT 'SUCCESS: Created MON_UpdateAudit table with comprehensive audit capabilities';
GO

-- =============================================================================
-- CREATE ROLLBACK PROCEDURES
-- =============================================================================

-- Create stored procedure for batch rollback capability
CREATE PROCEDURE SP_RollbackBatch
    @batch_id VARCHAR(50),
    @rollback_reason NVARCHAR(500)
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @rollback_count INT = 0;
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
        -- Update audit records to mark as rolled back
        UPDATE MON_UpdateAudit 
        SET 
            rollback_timestamp = GETUTCDATE(),
            rollback_reason = @rollback_reason
        WHERE 
            batch_id = @batch_id 
            AND rollback_timestamp IS NULL;
        
        SET @rollback_count = @@ROWCOUNT;
        
        COMMIT TRANSACTION;
        
        PRINT 'SUCCESS: Marked ' + CAST(@rollback_count AS VARCHAR) + ' records for rollback in batch ' + @batch_id;
        
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;

PRINT 'SUCCESS: Created SP_RollbackBatch stored procedure';
GO

-- =============================================================================
-- CREATE AUDIT REPORTING VIEWS
-- =============================================================================

-- Create view for update operation summary
CREATE VIEW VW_UpdateOperationSummary AS
SELECT 
    batch_id,
    update_operation,
    monday_board_id,
    COUNT(*) as total_updates,
    COUNT(CASE WHEN rollback_timestamp IS NULL THEN 1 END) as active_updates,
    COUNT(CASE WHEN rollback_timestamp IS NOT NULL THEN 1 END) as rolled_back_updates,
    MIN(update_timestamp) as batch_start_time,
    MAX(update_timestamp) as batch_end_time,
    COUNT(CASE WHEN error_message IS NOT NULL THEN 1 END) as error_count
FROM MON_UpdateAudit
GROUP BY batch_id, update_operation, monday_board_id;
GO

PRINT 'SUCCESS: Created VW_UpdateOperationSummary view';

-- =============================================================================
-- VALIDATION QUERIES
-- =============================================================================

-- Verify table structure
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'MON_UpdateAudit'
ORDER BY ORDINAL_POSITION;

-- Verify indexes exist
SELECT 
    i.name AS index_name,
    i.type_desc,
    c.name AS column_name
FROM sys.indexes i
INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
WHERE i.object_id = OBJECT_ID('MON_UpdateAudit')
ORDER BY i.name, ic.key_ordinal;

-- Test insert capability
INSERT INTO MON_UpdateAudit (
    batch_id,
    update_operation,
    monday_item_id,
    monday_board_id,
    column_id,
    old_value,
    new_value,
    user_id
) VALUES (
    'TEST_BATCH_001',
    'update_items',
    1234567890,
    8709134353,
    'status_mkp44k3t',
    'In Progress',
    'Shipped',
    'SYSTEM_TEST'
);

PRINT 'SUCCESS: Test record inserted successfully';

-- Clean up test record
DELETE FROM MON_UpdateAudit WHERE batch_id = 'TEST_BATCH_001';

PRINT 'COMPLETE: MON_UpdateAudit table ready for production use';
