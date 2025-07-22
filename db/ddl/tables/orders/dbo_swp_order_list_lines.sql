-- Table: dbo.swp_ORDER_LIST_LINES
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[swp_ORDER_LIST_LINES] (
    [line_uuid] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [record_uuid] UNIQUEIDENTIFIER NOT NULL,
    [size_code] NVARCHAR(20) NOT NULL,
    [qty] INT NOT NULL,
    [row_hash] CHAR(64) NULL,
    [sync_state] VARCHAR(10) NOT NULL DEFAULT (NULL),
    [last_synced_at] DATETIME2 NULL,
    [monday_item_id] BIGINT NULL,
    [parent_item_id] BIGINT NULL,
    [created_at] DATETIME2 NULL DEFAULT (getutcdate()),
    [updated_at] DATETIME2 NULL DEFAULT (getutcdate()),
    CONSTRAINT [PK_swp_ORDER_LIST_LINES] PRIMARY KEY ([line_uuid])
);

-- Indexes
CREATE INDEX [IX_swp_ORDER_LIST_LINES_hash] ON [dbo].[swp_ORDER_LIST_LINES] ([row_hash]);
CREATE INDEX [IX_swp_ORDER_LIST_LINES_record_uuid] ON [dbo].[swp_ORDER_LIST_LINES] ([record_uuid]);
CREATE INDEX [IX_swp_ORDER_LIST_LINES_sync_state] ON [dbo].[swp_ORDER_LIST_LINES] ([sync_state]);
CREATE UNIQUE INDEX [UQ_swp_ORDER_LIST_LINES_record_size] ON [dbo].[swp_ORDER_LIST_LINES] ([record_uuid], [size_code]);
