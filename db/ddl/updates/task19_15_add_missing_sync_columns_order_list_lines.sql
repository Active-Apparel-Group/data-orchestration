-- =============================================================================
-- TASK 19.15: Add Missing Sync Columns to ORDER_LIST_LINES
-- =============================================================================
-- Purpose: Add sync columns required by sync engine for lines processing
-- Task: DELTA Table Elimination - Phase 5: Testing & Validation  
-- Date: 2025-07-24
-- 
-- Based on sync engine requirements from Phase 3 implementation:
-- - sync_pending_at: Required by _get_pending_lines() query
-- - monday_subitem_id: Required by _update_lines_delta_with_subitem_ids()
-- - monday_parent_id: Required by sync engine lines processing
--
-- SAFETY: These are non-breaking additive changes - existing data preserved
-- =============================================================================

USE [orders]
GO

-- Add missing sync tracking columns to ORDER_LIST_LINES
ALTER TABLE [dbo].[ORDER_LIST_LINES] ADD
    [sync_pending_at] DATETIME2(7) NULL     -- Timestamp when sync was marked as pending
GO

-- Create indexes for efficient sync querying
CREATE INDEX [IX_ORDER_LIST_LINES_sync_pending_at] ON [dbo].[ORDER_LIST_LINES] ([sync_pending_at]) 
WHERE [sync_pending_at] IS NOT NULL
GO

PRINT 'SUCCESS: Added sync_pending_at column to ORDER_LIST_LINES'
GO
