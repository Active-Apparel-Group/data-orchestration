-- Table: dbo.ORDER_LIST_DELTA
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[ORDER_LIST_DELTA] (
    [delta_uuid] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [record_uuid] UNIQUEIDENTIFIER NOT NULL,
    [action_type] VARCHAR(10) NOT NULL,
    [sync_state] VARCHAR(10) NOT NULL DEFAULT ('PENDING'),
    [AAG ORDER NUMBER] NVARCHAR(100) NULL,
    [CUSTOMER NAME] NVARCHAR(100) NULL,
    [SOURCE_CUSTOMER_NAME] NVARCHAR(100) NULL,
    [STYLE DESCRIPTION] NVARCHAR(100) NULL,
    [TOTAL QTY] SMALLINT NULL,
    [ETA CUSTOMER WAREHOUSE DATE] DATETIME2 NULL,
    [PO NUMBER] NVARCHAR(255) NULL,
    [CUSTOMER STYLE] NVARCHAR(100) NULL,
    [CUSTOMER COLOUR DESCRIPTION] NVARCHAR(100) NULL,
    [FINAL FOB (USD)] DECIMAL(17,4) NULL,
    [ORDER TYPE] NVARCHAR(100) NULL,
    [row_hash] CHAR(64) NULL,
    [monday_item_id] BIGINT NULL,
    [sync_attempted_at] DATETIME2 NULL,
    [sync_completed_at] DATETIME2 NULL,
    [sync_error_message] NVARCHAR(MAX) NULL,
    [retry_count] INT NULL DEFAULT ((0)),
    [created_at] DATETIME2 NULL DEFAULT (getutcdate()),
    CONSTRAINT [PK_ORDER_LIST_DELTA] PRIMARY KEY ([delta_uuid])
);

-- Indexes
CREATE INDEX [IX_ORDER_LIST_DELTA_created_at] ON [dbo].[ORDER_LIST_DELTA] ([created_at]);
CREATE INDEX [IX_ORDER_LIST_DELTA_record_uuid] ON [dbo].[ORDER_LIST_DELTA] ([record_uuid]);
CREATE INDEX [IX_ORDER_LIST_DELTA_sync_state] ON [dbo].[ORDER_LIST_DELTA] ([sync_state]);
