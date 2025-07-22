-- Table: dbo.ORDER_LIST_LINES_DELTA
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[ORDER_LIST_LINES_DELTA] (
    [delta_uuid] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [line_uuid] UNIQUEIDENTIFIER NOT NULL,
    [record_uuid] UNIQUEIDENTIFIER NOT NULL,
    [action_type] VARCHAR(10) NOT NULL,
    [sync_state] VARCHAR(10) NOT NULL DEFAULT ('PENDING'),
    [size_code] NVARCHAR(20) NULL,
    [qty] INT NULL,
    [row_hash] CHAR(64) NULL,
    [monday_item_id] BIGINT NULL,
    [parent_item_id] BIGINT NULL,
    [sync_attempted_at] DATETIME2 NULL,
    [sync_completed_at] DATETIME2 NULL,
    [sync_error_message] NVARCHAR(MAX) NULL,
    [retry_count] INT NULL DEFAULT ((0)),
    [created_at] DATETIME2 NULL DEFAULT (getutcdate()),
    CONSTRAINT [PK_ORDER_LIST_LINES_DELTA] PRIMARY KEY ([delta_uuid])
);

-- Indexes
CREATE INDEX [IX_ORDER_LIST_LINES_DELTA_created_at] ON [dbo].[ORDER_LIST_LINES_DELTA] ([created_at]);
CREATE INDEX [IX_ORDER_LIST_LINES_DELTA_parent_item_id] ON [dbo].[ORDER_LIST_LINES_DELTA] ([parent_item_id]);
CREATE INDEX [IX_ORDER_LIST_LINES_DELTA_record_uuid] ON [dbo].[ORDER_LIST_LINES_DELTA] ([record_uuid]);
CREATE INDEX [IX_ORDER_LIST_LINES_DELTA_sync_state] ON [dbo].[ORDER_LIST_LINES_DELTA] ([sync_state]);
