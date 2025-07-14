-- OPUS Update Boards - Simplified DDL Deployment Script
-- Purpose: Orchestrate all database changes for update operations support
-- Date: 2025-06-30 (Fixed Version)
-- Reference: OPUS_dev_update_boards.yaml - Task IMM.1

-- =============================================================================
-- MASTER DEPLOYMENT SCRIPT FOR OPUS UPDATE BOARDS (SIMPLIFIED)
-- =============================================================================

PRINT '================================================================';
PRINT 'OPUS UPDATE BOARDS - DATABASE SCHEMA DEPLOYMENT (SIMPLIFIED)';
PRINT 'Phase 0: Foundation Extension for Monday.com Bidirectional Sync';
PRINT 'Date: 2025-06-30';
PRINT '================================================================';
PRINT '';

-- Set deployment options
SET NOCOUNT ON;
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;

-- =============================================================================
-- STEP 1: EXTEND STAGING TABLES
-- =============================================================================

PRINT 'STEP 1: Extending staging tables for update operations...';
PRINT '';

-- Extend STG_MON_CustMasterSchedule
PRINT '  1.1 Extending STG_MON_CustMasterSchedule...';

IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule' 
    AND COLUMN_NAME = 'update_operation'
)
BEGIN
    ALTER TABLE STG_MON_CustMasterSchedule ADD
        update_operation VARCHAR(50) DEFAULT 'CREATE',
        update_fields NVARCHAR(MAX),
        source_table VARCHAR(100),
        source_query NVARCHAR(MAX),
        update_batch_id VARCHAR(50),
        validation_status VARCHAR(20) DEFAULT 'PENDING',
        validation_errors NVARCHAR(MAX);
    
    PRINT '      ✓ Successfully extended STG_MON_CustMasterSchedule';
END
ELSE
BEGIN
    PRINT '      → STG_MON_CustMasterSchedule already extended (skipping)';
END

-- Extend STG_MON_CustMasterSchedule_Subitems
PRINT '  1.2 Extending STG_MON_CustMasterSchedule_Subitems...';

IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule_Subitems' 
    AND COLUMN_NAME = 'update_operation'
)
BEGIN
    ALTER TABLE STG_MON_CustMasterSchedule_Subitems ADD
        update_operation VARCHAR(50) DEFAULT 'CREATE',
        update_fields NVARCHAR(MAX),
        source_table VARCHAR(100),
        source_query NVARCHAR(MAX),
        update_batch_id VARCHAR(50),
        validation_status VARCHAR(20) DEFAULT 'PENDING',
        validation_errors NVARCHAR(MAX);
    
    PRINT '      ✓ Successfully extended STG_MON_CustMasterSchedule_Subitems';
END
ELSE
BEGIN
    PRINT '      → STG_MON_CustMasterSchedule_Subitems already extended (skipping)';
END

PRINT '  ✓ STEP 1 COMPLETED: Staging tables extended successfully';
PRINT '';
GO

-- =============================================================================
-- STEP 2: CREATE AUDIT TABLE
-- =============================================================================

PRINT 'STEP 2: Creating audit table and infrastructure...';
PRINT '';

-- Create MON_UpdateAudit table
PRINT '  2.1 Creating MON_UpdateAudit table...';

IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'MON_UpdateAudit')
BEGIN
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
        
        -- Additional metadata
        user_id VARCHAR(100),
        source_system VARCHAR(50) DEFAULT 'OPUS_UPDATE_BOARDS',
        api_response_id VARCHAR(100),
        error_message NVARCHAR(MAX),
        
        -- Performance indexes
        INDEX IX_MON_UpdateAudit_BatchId (batch_id),
        INDEX IX_MON_UpdateAudit_ItemId (monday_item_id),
        INDEX IX_MON_UpdateAudit_BoardId (monday_board_id),
        INDEX IX_MON_UpdateAudit_Timestamp (update_timestamp)
    );
    
    PRINT '      ✓ Successfully created MON_UpdateAudit table';
END
ELSE
BEGIN
    PRINT '      → MON_UpdateAudit table already exists (skipping)';
END

PRINT '  ✓ STEP 2 COMPLETED: Audit infrastructure created successfully';
PRINT '';
GO

-- =============================================================================
-- STEP 3: CREATE STORED PROCEDURES
-- =============================================================================

PRINT 'STEP 3: Creating stored procedures...';
PRINT '';

-- Create SP_RollbackBatch procedure
PRINT '  3.1 Creating SP_RollbackBatch procedure...';

IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.ROUTINES WHERE ROUTINE_NAME = 'SP_RollbackBatch')
BEGIN
    EXEC('
CREATE PROCEDURE SP_RollbackBatch
    @batch_id VARCHAR(50),
    @rollback_reason NVARCHAR(500)
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @rollback_count INT = 0;
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
        UPDATE MON_UpdateAudit 
        SET 
            rollback_timestamp = GETUTCDATE(),
            rollback_reason = @rollback_reason
        WHERE 
            batch_id = @batch_id 
            AND rollback_timestamp IS NULL;
        
        SET @rollback_count = @@ROWCOUNT;
        
        COMMIT TRANSACTION;
        
        PRINT ''Marked '' + CAST(@rollback_count AS VARCHAR) + '' records for rollback in batch '' + @batch_id;
        
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
    ');
    
    PRINT '      ✓ Successfully created SP_RollbackBatch procedure';
END
ELSE
BEGIN
    PRINT '      → SP_RollbackBatch procedure already exists (skipping)';
END

PRINT '  ✓ STEP 3 COMPLETED: Stored procedures created successfully';
PRINT '';
GO

-- =============================================================================
-- STEP 4: CREATE VIEWS
-- =============================================================================

PRINT 'STEP 4: Creating views...';
PRINT '';

-- Create VW_UpdateOperationSummary view
PRINT '  4.1 Creating VW_UpdateOperationSummary view...';

IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.VIEWS WHERE TABLE_NAME = 'VW_UpdateOperationSummary')
BEGIN
    EXEC('
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
    ');
    
    PRINT '      ✓ Successfully created VW_UpdateOperationSummary view';
END
ELSE
BEGIN
    PRINT '      → VW_UpdateOperationSummary view already exists (skipping)';
END

PRINT '  ✓ STEP 4 COMPLETED: Views created successfully';
PRINT '';
GO

-- =============================================================================
-- STEP 5: DEPLOYMENT VALIDATION & SUMMARY
-- =============================================================================

PRINT 'STEP 5: Validating deployment...';
PRINT '';

DECLARE @validation_errors INT = 0;

-- Validate staging table extensions
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule' 
    AND COLUMN_NAME = 'update_operation'
)
BEGIN
    PRINT '  ✗ STG_MON_CustMasterSchedule missing update_operation column';
    SET @validation_errors = @validation_errors + 1;
END
ELSE
    PRINT '  ✓ STG_MON_CustMasterSchedule properly extended';

-- Validate subitem table extensions
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule_Subitems' 
    AND COLUMN_NAME = 'update_operation'
)
BEGIN
    PRINT '  ✗ STG_MON_CustMasterSchedule_Subitems missing update_operation column';
    SET @validation_errors = @validation_errors + 1;
END
ELSE
    PRINT '  ✓ STG_MON_CustMasterSchedule_Subitems properly extended';

-- Validate audit table
IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'MON_UpdateAudit')
BEGIN
    PRINT '  ✗ MON_UpdateAudit table missing';
    SET @validation_errors = @validation_errors + 1;
END
ELSE
    PRINT '  ✓ MON_UpdateAudit table created';

-- Validate stored procedure
IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.ROUTINES WHERE ROUTINE_NAME = 'SP_RollbackBatch')
BEGIN
    PRINT '  ✗ SP_RollbackBatch procedure missing';
    SET @validation_errors = @validation_errors + 1;
END
ELSE
    PRINT '  ✓ SP_RollbackBatch procedure created';

-- Validate view
IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.VIEWS WHERE TABLE_NAME = 'VW_UpdateOperationSummary')
BEGIN
    PRINT '  ✗ VW_UpdateOperationSummary view missing';
    SET @validation_errors = @validation_errors + 1;
END
ELSE
    PRINT '  ✓ VW_UpdateOperationSummary view created';

-- =============================================================================
-- DEPLOYMENT SUMMARY
-- =============================================================================

PRINT '';
PRINT '================================================================';
PRINT 'DEPLOYMENT SUMMARY';
PRINT '================================================================';
PRINT 'Deployment Time: ' + FORMAT(GETUTCDATE(), 'yyyy-MM-dd HH:mm:ss UTC');
PRINT 'Validation Errors: ' + CAST(@validation_errors AS VARCHAR);
PRINT '';

IF @validation_errors = 0
BEGIN
    PRINT 'STATUS: ✓ DEPLOYMENT SUCCESSFUL';
    PRINT '';
    PRINT 'Database schema is now ready for OPUS Update Boards!';
    PRINT '';
    PRINT 'NEXT STEPS:';
    PRINT '  1. Test UpdateOperations module (pipelines/utils/update_operations.py)';
    PRINT '  2. Run single update workflow in dry-run mode';
    PRINT '  3. Proceed to Phase 1: GraphQL Operations';
    PRINT '  4. Begin Monday.com API integration';
END
ELSE
BEGIN
    PRINT 'STATUS: ✗ DEPLOYMENT FAILED';
    PRINT '';
    PRINT 'Please review validation errors above and troubleshoot.';
    PRINT 'Contact development team if issues persist.';
END

PRINT '';
PRINT '================================================================';

-- Log deployment to audit table if it exists
IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'MON_UpdateAudit')
BEGIN
    DECLARE @deployment_id VARCHAR(50) = 'OPUS_DDL_' + FORMAT(GETUTCDATE(), 'yyyyMMdd_HHmmss');
    
    INSERT INTO MON_UpdateAudit (
        batch_id, update_operation, old_value, new_value, user_id, source_system
    ) VALUES (
        @deployment_id, 
        'schema_deployment',
        'pre_opus_update_boards',
        'opus_update_boards_ready',
        SYSTEM_USER,
        'DDL_DEPLOYMENT'
    );
    
    PRINT 'Deployment logged to MON_UpdateAudit table.';
END

PRINT 'OPUS Update Boards deployment complete.';
