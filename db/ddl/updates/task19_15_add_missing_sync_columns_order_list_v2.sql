-- =============================================================================
-- TASK 19.15: Add Missing Sync Columns to ORDER_LIST_V2
-- =============================================================================
-- Purpose: Add sync_pending_at column required by sync engine
-- Task: DELTA Table Elimination - Phase 5: Testing & Validation
-- Date: 2025-07-24
-- 
-- Based on sync engine requirements from Phase 3 implementation:
-- - sync_pending_at: Required by _get_pending_headers() query
--
-- SAFETY: These are non-breaking additive changes - existing data preserved
-- =============================================================================

USE [orders]
GO

-- Add missing sync tracking column to ORDER_LIST_V2
ALTER TABLE [dbo].[ORDER_LIST_V2] ADD
    [sync_pending_at] DATETIME2(7) NULL       -- Timestamp when sync was marked as pending
GO

-- Create index for efficient pending sync querying
CREATE INDEX [IX_ORDER_LIST_V2_sync_pending_at] ON [dbo].[ORDER_LIST_V2] ([sync_pending_at]) 
WHERE [sync_pending_at] IS NOT NULL
GO

PRINT 'SUCCESS: Added sync_pending_at column to ORDER_LIST_V2'
GO
