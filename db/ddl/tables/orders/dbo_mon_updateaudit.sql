-- Table: dbo.MON_UpdateAudit
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[MON_UpdateAudit] (
    [audit_id] INT NOT NULL,
    [batch_id] VARCHAR(50) NOT NULL,
    [update_operation] VARCHAR(50) NOT NULL,
    [monday_item_id] BIGINT NULL,
    [monday_board_id] BIGINT NULL,
    [column_id] VARCHAR(100) NULL,
    [old_value] NVARCHAR(MAX) NULL,
    [new_value] NVARCHAR(MAX) NULL,
    [update_timestamp] DATETIME2 NULL DEFAULT (getutcdate()),
    [rollback_timestamp] DATETIME2 NULL,
    [rollback_reason] NVARCHAR(500) NULL,
    [user_id] VARCHAR(100) NULL,
    [source_system] VARCHAR(50) NULL DEFAULT ('OPUS_UPDATE_BOARDS'),
    [api_response_id] VARCHAR(100) NULL,
    [error_message] NVARCHAR(MAX) NULL,
    CONSTRAINT [PK_MON_UpdateAudit] PRIMARY KEY ([audit_id])
);

-- Indexes
CREATE INDEX [IX_MON_UpdateAudit_BatchId] ON [dbo].[MON_UpdateAudit] ([batch_id]);
CREATE INDEX [IX_MON_UpdateAudit_BoardId] ON [dbo].[MON_UpdateAudit] ([monday_board_id]);
CREATE INDEX [IX_MON_UpdateAudit_ItemId] ON [dbo].[MON_UpdateAudit] ([monday_item_id]);
CREATE INDEX [IX_MON_UpdateAudit_Timestamp] ON [dbo].[MON_UpdateAudit] ([update_timestamp]);
