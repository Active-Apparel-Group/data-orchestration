-- OPUS Update Boards - Rollback Script
-- Purpose: Rollback database changes for update operations support
-- Date: 2025-06-30
-- WARNING: This will remove all update operation capabilities

-- =============================================================================
-- OPUS UPDATE BOARDS - ROLLBACK SCRIPT
-- =============================================================================

PRINT '================================================================';
PRINT 'OPUS UPDATE BOARDS - DATABASE SCHEMA ROLLBACK';
PRINT 'WARNING: This will remove all update operation capabilities';
PRINT 'Date: 2025-06-30';
PRINT '================================================================';
PRINT '';

-- Confirmation check
DECLARE @confirm_rollback VARCHAR(10) = 'NO'; -- Change to 'YES' to proceed

IF @confirm_rollback != 'YES'
BEGIN
    PRINT 'ROLLBACK CANCELLED: Set @confirm_rollback = ''YES'' to proceed';
    PRINT 'This safety check prevents accidental rollback execution.';
    RETURN;
END

-- Set rollback options
SET NOCOUNT ON;
DECLARE @rollback_start DATETIME2 = GETUTCDATE();
DECLARE @rollback_id VARCHAR(50) = 'OPUS_ROLLBACK_' + FORMAT(GETUTCDATE(), 'yyyyMMdd_HHmmss');
DECLARE @error_count INT = 0;

PRINT 'Rollback ID: ' + @rollback_id;
PRINT 'Start Time: ' + FORMAT(@rollback_start, 'yyyy-MM-dd HH:mm:ss UTC');
PRINT '';

-- =============================================================================
-- STEP 1: BACKUP AUDIT DATA (if needed)
-- =============================================================================

PRINT 'STEP 1: Backing up audit data...';

BEGIN TRY
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'MON_UpdateAudit')
    BEGIN
        -- Create backup table with timestamp
        DECLARE @backup_table VARCHAR(100) = 'MON_UpdateAudit_Backup_' + FORMAT(GETUTCDATE(), 'yyyyMMdd_HHmmss');
        DECLARE @backup_sql NVARCHAR(MAX) = 'SELECT * INTO ' + @backup_table + ' FROM MON_UpdateAudit';
        
        EXEC sp_executesql @backup_sql;
        PRINT '  ✓ Audit data backed up to: ' + @backup_table;
    END
    ELSE
        PRINT '  → No audit table found (skipping backup)';
        
END TRY
BEGIN CATCH
    SET @error_count = @error_count + 1;
    PRINT '  ✗ Backup failed: ' + ERROR_MESSAGE();
END CATCH;

PRINT '';

-- =============================================================================
-- STEP 2: DROP VIEWS
-- =============================================================================

PRINT 'STEP 2: Dropping views...';

BEGIN TRY
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.VIEWS WHERE TABLE_NAME = 'VW_UpdateOperationSummary')
    BEGIN
        DROP VIEW VW_UpdateOperationSummary;
        PRINT '  ✓ Dropped VW_UpdateOperationSummary view';
    END
    ELSE
        PRINT '  → VW_UpdateOperationSummary view not found (skipping)';
        
END TRY
BEGIN CATCH
    SET @error_count = @error_count + 1;
    PRINT '  ✗ Failed to drop view: ' + ERROR_MESSAGE();
END CATCH;

PRINT '';

-- =============================================================================
-- STEP 3: DROP STORED PROCEDURES
-- =============================================================================

PRINT 'STEP 3: Dropping stored procedures...';

BEGIN TRY
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.ROUTINES WHERE ROUTINE_NAME = 'SP_RollbackBatch')
    BEGIN
        DROP PROCEDURE SP_RollbackBatch;
        PRINT '  ✓ Dropped SP_RollbackBatch procedure';
    END
    ELSE
        PRINT '  → SP_RollbackBatch procedure not found (skipping)';
        
END TRY
BEGIN CATCH
    SET @error_count = @error_count + 1;
    PRINT '  ✗ Failed to drop procedure: ' + ERROR_MESSAGE();
END CATCH;

PRINT '';

-- =============================================================================
-- STEP 4: DROP AUDIT TABLE
-- =============================================================================

PRINT 'STEP 4: Dropping audit table...';

BEGIN TRY
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'MON_UpdateAudit')
    BEGIN
        DROP TABLE MON_UpdateAudit;
        PRINT '  ✓ Dropped MON_UpdateAudit table';
    END
    ELSE
        PRINT '  → MON_UpdateAudit table not found (skipping)';
        
END TRY
BEGIN CATCH
    SET @error_count = @error_count + 1;
    PRINT '  ✗ Failed to drop audit table: ' + ERROR_MESSAGE();
END CATCH;

PRINT '';

-- =============================================================================
-- STEP 5: REMOVE STAGING TABLE COLUMNS
-- =============================================================================

PRINT 'STEP 5: Removing staging table columns...';

-- Remove columns from STG_MON_CustMasterSchedule
BEGIN TRY
    PRINT '  5.1 Removing columns from STG_MON_CustMasterSchedule...';
    
    DECLARE @columns_to_drop TABLE (column_name VARCHAR(100));
    INSERT INTO @columns_to_drop VALUES 
        ('update_operation'), ('update_fields'), ('source_table'),
        ('source_query'), ('update_batch_id'), ('validation_status'), ('validation_errors');
    
    DECLARE @column_name VARCHAR(100);
    DECLARE drop_cursor CURSOR FOR 
        SELECT column_name FROM @columns_to_drop 
        WHERE EXISTS (
            SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule' 
            AND COLUMN_NAME = column_name
        );
    
    OPEN drop_cursor;
    FETCH NEXT FROM drop_cursor INTO @column_name;
    
    WHILE @@FETCH_STATUS = 0
    BEGIN
        DECLARE @drop_sql NVARCHAR(MAX) = 'ALTER TABLE STG_MON_CustMasterSchedule DROP COLUMN ' + @column_name;
        EXEC sp_executesql @drop_sql;
        PRINT '      ✓ Dropped column: ' + @column_name;
        
        FETCH NEXT FROM drop_cursor INTO @column_name;
    END
    
    CLOSE drop_cursor;
    DEALLOCATE drop_cursor;
    
END TRY
BEGIN CATCH
    SET @error_count = @error_count + 1;
    PRINT '  ✗ Failed to remove master table columns: ' + ERROR_MESSAGE();
END CATCH;

-- Remove columns from STG_MON_CustMasterSchedule_Subitems
BEGIN TRY
    PRINT '  5.2 Removing columns from STG_MON_CustMasterSchedule_Subitems...';
    
    DECLARE drop_cursor2 CURSOR FOR 
        SELECT column_name FROM @columns_to_drop 
        WHERE EXISTS (
            SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule_Subitems' 
            AND COLUMN_NAME = column_name
        );
    
    OPEN drop_cursor2;
    FETCH NEXT FROM drop_cursor2 INTO @column_name;
    
    WHILE @@FETCH_STATUS = 0
    BEGIN
        DECLARE @drop_sql2 NVARCHAR(MAX) = 'ALTER TABLE STG_MON_CustMasterSchedule_Subitems DROP COLUMN ' + @column_name;
        EXEC sp_executesql @drop_sql2;
        PRINT '      ✓ Dropped column: ' + @column_name;
        
        FETCH NEXT FROM drop_cursor2 INTO @column_name;
    END
    
    CLOSE drop_cursor2;
    DEALLOCATE drop_cursor2;
    
END TRY
BEGIN CATCH
    SET @error_count = @error_count + 1;
    PRINT '  ✗ Failed to remove subitems table columns: ' + ERROR_MESSAGE();
END CATCH;

PRINT '';

-- =============================================================================
-- ROLLBACK VALIDATION
-- =============================================================================

PRINT 'STEP 6: Validating rollback...';

DECLARE @validation_errors INT = 0;

-- Check that update columns are removed
IF EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule' 
    AND COLUMN_NAME = 'update_operation'
)
BEGIN
    PRINT '  ✗ update_operation column still exists in master table';
    SET @validation_errors = @validation_errors + 1;
END
ELSE
    PRINT '  ✓ Update columns removed from master table';

-- Check that audit table is removed
IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'MON_UpdateAudit')
BEGIN
    PRINT '  ✗ MON_UpdateAudit table still exists';
    SET @validation_errors = @validation_errors + 1;
END
ELSE
    PRINT '  ✓ Audit table removed';

-- Check that procedures are removed
IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.ROUTINES WHERE ROUTINE_NAME = 'SP_RollbackBatch')
BEGIN
    PRINT '  ✗ SP_RollbackBatch procedure still exists';
    SET @validation_errors = @validation_errors + 1;
END
ELSE
    PRINT '  ✓ Stored procedures removed';

-- =============================================================================
-- ROLLBACK SUMMARY
-- =============================================================================

DECLARE @rollback_end DATETIME2 = GETUTCDATE();
DECLARE @rollback_duration_seconds INT = DATEDIFF(SECOND, @rollback_start, @rollback_end);

PRINT '';
PRINT '================================================================';
PRINT 'ROLLBACK SUMMARY';
PRINT '================================================================';
PRINT 'Rollback ID: ' + @rollback_id;
PRINT 'Start Time: ' + FORMAT(@rollback_start, 'yyyy-MM-dd HH:mm:ss UTC');
PRINT 'End Time: ' + FORMAT(@rollback_end, 'yyyy-MM-dd HH:mm:ss UTC');
PRINT 'Duration: ' + CAST(@rollback_duration_seconds AS VARCHAR) + ' seconds';
PRINT 'Rollback Errors: ' + CAST(@error_count AS VARCHAR);
PRINT 'Validation Errors: ' + CAST(@validation_errors AS VARCHAR);
PRINT '';

IF @error_count = 0 AND @validation_errors = 0
BEGIN
    PRINT 'STATUS: ✓ ROLLBACK SUCCESSFUL';
    PRINT '';
    PRINT 'Database schema has been restored to pre-OPUS state.';
    PRINT 'All update operation capabilities have been removed.';
END
ELSE
BEGIN
    PRINT 'STATUS: ✗ ROLLBACK INCOMPLETE';
    PRINT '';
    PRINT 'Some components may not have been removed successfully.';
    PRINT 'Manual cleanup may be required.';
END

PRINT '';
PRINT '================================================================';
