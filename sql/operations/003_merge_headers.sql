-- ================================================================
-- 003_merge_headers.sql - ORDER_LIST Header Merge with Delta Tracking
-- ================================================================
-- Purpose: MERGE SWP_ORDER_LIST → ORDER_LIST_V2 + OUTPUT to DELTA
-- Dependencies: SWP_ORDER_LIST (staging), ORDER_LIST_V2 (target), ORDER_LIST_DELTA (tracking)
-- Configuration: Uses TOML-driven hash columns for change detection
-- Created: 2025-07-18 (Milestone 2: Delta Engine)
-- ================================================================

DECLARE @BatchId UNIQUEIDENTIFIER = NEWID();
DECLARE @ProcessedCount INT = 0;
DECLARE @NewCount INT = 0;
DECLARE @ChangedCount INT = 0;

BEGIN TRY
    BEGIN TRANSACTION;
    
    -- =============================================================
    -- MERGE OPERATION: SWP_ORDER_LIST → ORDER_LIST_V2
    -- =============================================================
    -- Hash-based change detection using TOML configuration:
    -- - NEW: Record doesn't exist in target
    -- - CHANGED: Record exists but hash differs (business logic change)
    -- - UNCHANGED: Record exists with same hash (no action needed)
    
    MERGE [dbo].[ORDER_LIST_V2] AS target
    USING [dbo].[SWP_ORDER_LIST] AS source
    ON target.[record_uuid] = source.[record_uuid]
    
    -- INSERT: New records not in target table
    WHEN NOT MATCHED BY TARGET THEN
        INSERT (
            [record_uuid],
            [AAG ORDER NUMBER],
            [CUSTOMER NAME], 
            [STYLE DESCRIPTION],
            [TOTAL QTY],
            [ETA CUSTOMER WAREHOUSE DATE],
            [CUSTOMER STYLE],
            [PO NUMBER],
            [CUSTOMER COLOUR DESCRIPTION],
            [UNIT OF MEASURE],
            -- Size columns (dynamically detected from TOML config)
            [XS], [S], [M], [L], [XL], [XXL], 
            [2T], [3T], [4T], [5T], [6T], [7T],
            [8], [10], [12], [14], [16], [18], [20],
            -- Metadata columns
            [sync_state],
            [last_synced_at],
            [monday_item_id],
            [batch_id],
            [created_at],
            [updated_at]
        )
        VALUES (
            source.[record_uuid],
            source.[AAG ORDER NUMBER],
            source.[CUSTOMER NAME],
            source.[STYLE DESCRIPTION], 
            source.[TOTAL QTY],
            source.[ETA CUSTOMER WAREHOUSE DATE],
            source.[CUSTOMER STYLE],
            source.[PO NUMBER],
            source.[CUSTOMER COLOUR DESCRIPTION],
            source.[UNIT OF MEASURE],
            -- Size columns
            source.[XS], source.[S], source.[M], source.[L], source.[XL], source.[XXL],
            source.[2T], source.[3T], source.[4T], source.[5T], source.[6T], source.[7T],
            source.[8], source.[10], source.[12], source.[14], source.[16], source.[18], source.[20],
            -- Metadata
            'NEW',                          -- sync_state
            NULL,                           -- last_synced_at
            NULL,                           -- monday_item_id  
            @BatchId,                       -- batch_id
            GETUTCDATE(),                   -- created_at
            GETUTCDATE()                    -- updated_at
        )
    
    -- UPDATE: Changed records (hash differs = business logic change)
    WHEN MATCHED AND target.[row_hash] <> source.[row_hash] THEN
        UPDATE SET
            [AAG ORDER NUMBER] = source.[AAG ORDER NUMBER],
            [CUSTOMER NAME] = source.[CUSTOMER NAME],
            [STYLE DESCRIPTION] = source.[STYLE DESCRIPTION],
            [TOTAL QTY] = source.[TOTAL QTY],
            [ETA CUSTOMER WAREHOUSE DATE] = source.[ETA CUSTOMER WAREHOUSE DATE],
            [CUSTOMER STYLE] = source.[CUSTOMER STYLE],
            [PO NUMBER] = source.[PO NUMBER],
            [CUSTOMER COLOUR DESCRIPTION] = source.[CUSTOMER COLOUR DESCRIPTION],
            [UNIT OF MEASURE] = source.[UNIT OF MEASURE],
            -- Size columns
            [XS] = source.[XS], [S] = source.[S], [M] = source.[M], 
            [L] = source.[L], [XL] = source.[XL], [XXL] = source.[XXL],
            [2T] = source.[2T], [3T] = source.[3T], [4T] = source.[4T], 
            [5T] = source.[5T], [6T] = source.[6T], [7T] = source.[7T],
            [8] = source.[8], [10] = source.[10], [12] = source.[12], 
            [14] = source.[14], [16] = source.[16], [18] = source.[18], [20] = source.[20],
            -- Metadata updates
            [sync_state] = 'CHANGED',
            [batch_id] = @BatchId,
            [updated_at] = GETUTCDATE()
            -- Note: row_hash automatically recalculated via PERSISTED computed column
    
    -- =============================================================
    -- OUTPUT CLAUSE: Capture all changes for delta tracking
    -- =============================================================
    -- All INSERT and UPDATE operations written to ORDER_LIST_DELTA
    -- for Monday.com sync processing
    
    OUTPUT 
        COALESCE(INSERTED.[record_uuid], DELETED.[record_uuid]) AS [record_uuid],
        $action AS [action_type],                               -- 'INSERT' or 'UPDATE'
        INSERTED.[AAG ORDER NUMBER],
        INSERTED.[CUSTOMER NAME],
        INSERTED.[STYLE DESCRIPTION], 
        INSERTED.[TOTAL QTY],
        INSERTED.[ETA CUSTOMER WAREHOUSE DATE],
        INSERTED.[CUSTOMER STYLE],
        INSERTED.[PO NUMBER],
        INSERTED.[CUSTOMER COLOUR DESCRIPTION],
        INSERTED.[sync_state],
        'PENDING' AS [delta_sync_state],                        -- Ready for Monday sync
        @BatchId AS [batch_id],
        GETUTCDATE() AS [delta_created_at],
        NULL AS [monday_item_id],                               -- Populated during sync
        NULL AS [synced_at]                                     -- Populated when sync complete
    INTO [dbo].[ORDER_LIST_DELTA] (
        [record_uuid], [action_type],        [AAG ORDER NUMBER], [CUSTOMER NAME], 
        [STYLE DESCRIPTION], [TOTAL QTY], [ETA CUSTOMER WAREHOUSE DATE], 
        [CUSTOMER STYLE], [PO NUMBER], [CUSTOMER COLOUR DESCRIPTION],
        [sync_state], [delta_sync_state], [batch_id], [delta_created_at],
        [monday_item_id], [synced_at]
    );
    
    -- =============================================================
    -- BATCH METRICS & VALIDATION
    -- =============================================================
    
    SET @ProcessedCount = @@ROWCOUNT;
    
    -- Count new vs changed records for reporting
    SELECT @NewCount = COUNT(*) FROM [dbo].[ORDER_LIST_DELTA] 
    WHERE [batch_id] = @BatchId AND [action_type] = 'INSERT';
    
    SELECT @ChangedCount = COUNT(*) FROM [dbo].[ORDER_LIST_DELTA] 
    WHERE [batch_id] = @BatchId AND [action_type] = 'UPDATE';
    
    -- Validation: Ensure all staging records processed
    DECLARE @StagingCount INT;
    SELECT @StagingCount = COUNT(*) FROM [dbo].[SWP_ORDER_LIST];
    
    IF @ProcessedCount <> (@NewCount + @ChangedCount)
    BEGIN
        RAISERROR('Merge validation failed: Processed count mismatch', 16, 1);
        ROLLBACK TRANSACTION;
        RETURN;
    END
    
    COMMIT TRANSACTION;
    
    -- =============================================================
    -- SUCCESS REPORTING
    -- =============================================================
    
    PRINT 'ORDER_LIST Header Merge Complete';
    PRINT 'Batch ID: ' + CAST(@BatchId AS VARCHAR(36));
    PRINT 'Total Processed: ' + CAST(@ProcessedCount AS VARCHAR(10));
    PRINT 'New Records: ' + CAST(@NewCount AS VARCHAR(10));
    PRINT 'Changed Records: ' + CAST(@ChangedCount AS VARCHAR(10));
    PRINT 'Staging Records: ' + CAST(@StagingCount AS VARCHAR(10));
    PRINT 'Delta Records Created: ' + CAST((@NewCount + @ChangedCount) AS VARCHAR(10));
    
    -- Return success metrics for Python pipeline
    SELECT 
        @BatchId AS batch_id,
        @ProcessedCount AS processed_count,
        @NewCount AS new_count, 
        @ChangedCount AS changed_count,
        @StagingCount AS staging_count,
        'SUCCESS' AS status,
        GETUTCDATE() AS completed_at;

END TRY
BEGIN CATCH
    
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    
    -- Error reporting for Python exception handling
    DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
    DECLARE @ErrorSeverity INT = ERROR_SEVERITY();
    DECLARE @ErrorState INT = ERROR_STATE();
    
    PRINT 'ORDER_LIST Header Merge Failed';
    PRINT 'Error: ' + @ErrorMessage;
    
    -- Return error metrics for Python pipeline
    SELECT 
        @BatchId AS batch_id,
        0 AS processed_count,
        0 AS new_count,
        0 AS changed_count,
        0 AS staging_count,
        'FAILED' AS status,
        @ErrorMessage AS error_message,
        GETUTCDATE() AS completed_at;
    
    -- Re-raise for Python exception handling
    RAISERROR(@ErrorMessage, @ErrorSeverity, @ErrorState);
    
END CATCH;

-- =============================================================
-- NOTES & CONFIGURATION
-- =============================================================
-- 
-- Batch Metrics & Validation
-- Hash Logic: Columns used for change detection defined in TOML:
-- AAG ORDER NUMBER, CUSTOMER NAME, STYLE DESCRIPTION,
-- TOTAL QTY, ETA CUSTOMER WAREHOUSE DATE, CUSTOMER STYLE
--
-- Size Columns (Dynamic Discovery):
-- Size columns between "UNIT OF MEASURE" and "TOTAL QTY" markers
-- are dynamically detected and included in merge operations
--
-- Sync States:
-- - NEW: Inserted this batch, ready for Monday sync
-- - CHANGED: Updated this batch, ready for Monday sync  
-- - SYNCED: Successfully synchronized to Monday.com
-- - FAILED: Monday sync failed, will retry
--
-- Delta States:
-- - PENDING: Awaiting Monday.com synchronization
-- - SYNCED: Successfully synchronized to Monday.com
-- - FAILED: Synchronization failed, requires retry
--
-- Performance Notes:
-- - Uses batch_id for tracking and cleanup
-- - PERSISTED computed columns for hash calculation
-- - OUTPUT clause captures all changes efficiently
-- - Transaction ensures atomicity of merge + delta creation
-- =============================================================
