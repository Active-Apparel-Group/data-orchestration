-- =============================================================================
-- TASK 19.15: Fix ORDER_LIST_LINES sync_state Default Value
-- =============================================================================
-- Purpose: Fix contradictory DEFAULT NULL with NOT NULL constraint
-- Issue: ORDER_LIST_LINES.sync_state has DEFAULT (NULL) but NOT NULL constraint
-- Solution: Change default to 'NEW' to match ORDER_LIST and ORDER_LIST_V2
-- Date: 2025-07-24
-- =============================================================================

USE [orders]
GO

-- Fix the contradictory default value for sync_state
ALTER TABLE [dbo].[ORDER_LIST_LINES] 
ADD CONSTRAINT [DF_ORDER_LIST_LINES_sync_state] DEFAULT 'NEW' FOR [sync_state]
GO

PRINT 'SUCCESS: Fixed ORDER_LIST_LINES sync_state default value to NEW'
GO
