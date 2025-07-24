-- =============================================================================
-- TASK 19.2: Add Sync Tracking Columns to ORDER_LIST_LINES  
-- =============================================================================
-- Purpose: Add additional Monday.com sync tracking columns to ORDER_LIST_LINES table
-- Task: DELTA Table Elimination - Phase 1: Schema Updates
-- Date: 2025-07-23
-- 
-- This script adds missing sync tracking columns to ORDER_LIST_LINES to enable
-- direct sync without requiring ORDER_LIST_LINES_DELTA table.
--
-- NOTE: ORDER_LIST_LINES already has some sync columns, this adds the missing ones
-- SAFETY: These are non-breaking additive changes - existing data preserved
-- =============================================================================

USE [orders]
GO

-- Check existing columns first
PRINT 'Current ORDER_LIST_LINES columns:'
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'ORDER_LIST_LINES'
ORDER BY ORDINAL_POSITION
GO

-- alter sync_state DEFAULT = 'NEW'
ALTER TABLE [dbo].[ORDER_LIST_LINES] 
    ADD CONSTRAINT [DF_ORDER_LIST_LINES_sync_state] DEFAULT 'NEW' FOR [sync_state]

-- Add missing sync tracking columns to ORDER_LIST_LINES
-- (Note: Some columns like sync_state, monday_item_id already exist)
ALTER TABLE [dbo].[ORDER_LIST_LINES] ADD
    [row_hash] CHAR(64) NULL,                    -- Row hash for change detection
    [sync_state] VARCHAR(10) NULL,               -- 'NEW', 'PENDING', 'SYNCED', 'ERROR'  
    [action_type] VARCHAR(10) NULL,              -- 'INSERT', 'UPDATE', 'DELETE' 
    [monday_item_id] BIGINT NULL,                -- Monday.com item ID for subitem
    [monday_parent_id] BIGINT NULL,              -- Monday.com parent item ID reference
    [sync_attempted_at] DATETIME2(7) NULL,       -- Last sync attempt timestamp
    [sync_completed_at] DATETIME2(7) NULL,       -- Last successful sync timestamp
    [sync_error_message] NVARCHAR(1000) NULL,   -- Error message if sync failed
    [retry_count] INT NULL DEFAULT 0,             -- Number of retry attempts
    [sync_pending_at] DATETIME2(7) NULL     -- Timestamp when sync was marked as pending
GO

-- Create indexes for efficient sync querying
CREATE INDEX [IX_ORDER_LIST_LINES_action_type] ON [dbo].[ORDER_LIST_LINES] ([action_type])
WHERE [action_type] IS NOT NULL
GO

CREATE INDEX [IX_ORDER_LIST_LINES_monday_subitem_id] ON [dbo].[ORDER_LIST_LINES] ([monday_subitem_id])
WHERE [monday_subitem_id] IS NOT NULL  
GO

CREATE INDEX [IX_ORDER_LIST_LINES_monday_parent_id] ON [dbo].[ORDER_LIST_LINES] ([monday_parent_id])
WHERE [monday_parent_id] IS NOT NULL
GO

CREATE INDEX [IX_ORDER_LIST_LINES_sync_timestamps] ON [dbo].[ORDER_LIST_LINES] ([sync_attempted_at], [sync_completed_at])
WHERE [sync_attempted_at] IS NOT NULL
GO

-- Add constraints for data integrity
ALTER TABLE [dbo].[ORDER_LIST_LINES] 
ADD CONSTRAINT [CK_ORDER_LIST_LINES_action_type] 
CHECK ([action_type] IN ('INSERT', 'UPDATE', 'DELETE'))
GO

-- Note: sync_state constraint may already exist, check first
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'CK_ORDER_LIST_LINES_sync_state')
BEGIN
    ALTER TABLE [dbo].[ORDER_LIST_LINES] 
    ADD CONSTRAINT [CK_ORDER_LIST_LINES_sync_state] 
    CHECK ([sync_state] IN ('NEW', 'PENDING', 'SYNCED', 'ERROR'))
    
    ALTER TABLE [dbo].[ORDER_LIST_LINES]
    ADD CONSTRAINT [DF_ORDER_LIST_LINES_sync_state] DEFAULT 'NEW' FOR [sync_state]
END
GO

-- Add trigger to automatically update updated_at timestamp (if updated_at exists)
CREATE OR ALTER TRIGGER [TR_ORDER_LIST_LINES_UpdateTimestamp] 
ON [dbo].[ORDER_LIST_LINES]
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Only update if updated_at column exists
    IF COL_LENGTH('[dbo].[ORDER_LIST_LINES]', 'updated_at') IS NOT NULL
    BEGIN
        UPDATE [dbo].[ORDER_LIST_LINES] 
        SET [updated_at] = GETUTCDATE()
        FROM [dbo].[ORDER_LIST_LINES] o
        INNER JOIN inserted i ON o.[line_uuid] = i.[line_uuid]
    END
END
GO

-- Validation: Confirm new columns were added
PRINT ''
PRINT 'ORDER_LIST_LINES columns after update:'
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'ORDER_LIST_LINES' 
AND COLUMN_NAME IN (
    'action_type', 'sync_state', 'monday_item_id', 'monday_subitem_id', 'monday_parent_id',
    'sync_attempted_at', 'sync_completed_at', 'sync_error_message', 
    'retry_count', 'created_at', 'updated_at', 'row_hash', 'line_uuid', 'record_uuid'
)
ORDER BY COLUMN_NAME
GO

-- Final validation query
SELECT COUNT(*) as total_columns 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'ORDER_LIST_LINES'
GO

PRINT '✅ TASK 19.2 COMPLETED: Additional sync tracking columns added to ORDER_LIST_LINES'
PRINT 'Added columns: action_type, monday_subitem_id, monday_parent_id, sync_attempted_at, sync_completed_at, sync_error_message, retry_count'
PRINT 'Added indexes: action_type, monday_subitem_id, monday_parent_id, sync_timestamps'
PRINT 'Added constraints: action_type check, sync_state check (if not exists)'
PRINT 'Added trigger: UpdateTimestamp trigger for updated_at (if column exists)'
