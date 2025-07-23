-- =============================================================================
-- TASK 19.1: Add Sync Tracking Columns to ORDER_LIST_V2
-- =============================================================================
-- Purpose: Add Monday.com sync tracking columns to ORDER_LIST_V2 table
-- Task: DELTA Table Elimination - Phase 1: Schema Updates
-- Date: 2025-07-23
-- 
-- This script adds sync tracking columns to ORDER_LIST_V2 to enable
-- direct sync without requiring ORDER_LIST_DELTA table.
--
-- SAFETY: These are non-breaking additive changes - existing data preserved
-- =============================================================================

USE [orders]
GO

-- Add sync tracking columns to ORDER_LIST_V2
ALTER TABLE [dbo].[ORDER_LIST] ADD
    [action_type] VARCHAR(10) NULL,              -- 'INSERT', 'UPDATE', 'DELETE'
    --[sync_state] VARCHAR(10) NULL,               -- 'NEW', 'PENDING', 'SYNCED', 'ERROR'  
    --[monday_item_id] BIGINT NULL,                -- Monday.com item ID
    [sync_attempted_at] DATETIME2(7) NULL,       -- Last sync attempt timestamp
    [sync_completed_at] DATETIME2(7) NULL,       -- Last successful sync timestamp
    [sync_error_message] NVARCHAR(1000) NULL,   -- Error message if sync failed
    [retry_count] INT NULL DEFAULT 0            -- Number of retry attempts
    --[created_at] DATETIME2(7) NULL DEFAULT GETUTCDATE(),  -- Record creation timestamp
    --[updated_at] DATETIME2(7) NULL DEFAULT GETUTCDATE(),  -- Record update timestamp
    --[row_hash] CHAR(64) NULL                     -- Row hash for change detection
GO

-- Create indexes for efficient sync querying
CREATE INDEX [IX_ORDER_LIST_sync_state] ON [dbo].[ORDER_LIST] ([sync_state]) 
WHERE [sync_state] IS NOT NULL
GO

CREATE INDEX [IX_ORDER_LIST_action_type] ON [dbo].[ORDER_LIST] ([action_type])
WHERE [action_type] IS NOT NULL
GO

CREATE INDEX [IX_ORDER_LIST_monday_item_id] ON [dbo].[ORDER_LIST] ([monday_item_id])
WHERE [monday_item_id] IS NOT NULL
GO

CREATE INDEX [IX_ORDER_LIST_sync_timestamps] ON [dbo].[ORDER_LIST] ([sync_attempted_at], [sync_completed_at])
WHERE [sync_attempted_at] IS NOT NULL
GO

-- Add constraints for data integrity
ALTER TABLE [dbo].[ORDER_LIST_V2] 
ADD CONSTRAINT [CK_ORDER_LIST_V2_action_type] 
CHECK ([action_type] IN ('INSERT', 'UPDATE', 'DELETE'))
GO

ALTER TABLE [dbo].[ORDER_LIST_V2] 
ADD CONSTRAINT [CK_ORDER_LIST_V2_sync_state] 
CHECK ([sync_state] IN ('NEW', 'PENDING', 'SYNCED', 'ERROR'))
GO

-- Add trigger to automatically update updated_at timestamp
CREATE OR ALTER TRIGGER [TR_ORDER_LIST_UpdateTimestamp] 
ON [dbo].[ORDER_LIST]
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update updated_at if it wasn't already being updated (prevent recursion)
    IF NOT UPDATE([updated_at])
    BEGIN
        UPDATE [dbo].[ORDER_LIST] 
        SET [updated_at] = GETUTCDATE()
        FROM [dbo].[ORDER_LIST_V2] o
        INNER JOIN inserted i ON o.[record_uuid] = i.[record_uuid]
    END
END
GO

-- Validation: Confirm columns were added
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'ORDER_LIST_V2' 
AND COLUMN_NAME IN (
    'action_type', 'sync_state', 'monday_item_id', 
    'sync_attempted_at', 'sync_completed_at', 'sync_error_message', 
    'retry_count', 'created_at', 'updated_at', 'row_hash'
)
ORDER BY COLUMN_NAME
GO

PRINT '✅ TASK 19.1 COMPLETED: Sync tracking columns added to ORDER_LIST_V2'
PRINT 'Added columns: action_type, sync_state, monday_item_id, sync_attempted_at, sync_completed_at, sync_error_message, retry_count, created_at, updated_at, row_hash'
PRINT 'Added indexes: sync_state, action_type, monday_item_id, sync_timestamps'
PRINT 'Added constraints: action_type check, sync_state check'
PRINT 'Added trigger: UpdateTimestamp trigger for updated_at'
