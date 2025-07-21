SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ORDER_LIST_LINES](
	[line_uuid] [uniqueidentifier] NOT NULL,
	[record_uuid] [uniqueidentifier] NOT NULL,
	[size_code] [nvarchar](20) NOT NULL,
	[qty] [int] NOT NULL,
	[row_hash] [char](64) NULL,
	[sync_state] [varchar](10) NOT NULL,
	[last_synced_at] [datetime2](7) NULL,
	[monday_item_id] [bigint] NULL,
	[parent_item_id] [bigint] NULL,
	[created_at] [datetime2](7) NULL,
	[updated_at] [datetime2](7) NULL 
) ON [PRIMARY]
GO
ALTER TABLE [dbo].[ORDER_LIST_LINES] ADD PRIMARY KEY CLUSTERED 
(
	[line_uuid] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
ALTER TABLE [dbo].[ORDER_LIST_LINES] ADD  CONSTRAINT [UQ_ORDER_LIST_LINES_record_size] UNIQUE NONCLUSTERED 
(
	[record_uuid] ASC,
	[size_code] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
CREATE NONCLUSTERED INDEX [IX_ORDER_LIST_LINES_hash] ON [dbo].[ORDER_LIST_LINES]
(
	[row_hash] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
CREATE NONCLUSTERED INDEX [IX_ORDER_LIST_LINES_parent_item_id] ON [dbo].[ORDER_LIST_LINES]
(
	[parent_item_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
CREATE NONCLUSTERED INDEX [IX_ORDER_LIST_LINES_record_uuid] ON [dbo].[ORDER_LIST_LINES]
(
	[record_uuid] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
CREATE NONCLUSTERED INDEX [IX_ORDER_LIST_LINES_sync_state] ON [dbo].[ORDER_LIST_LINES]
(
	[sync_state] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
ALTER TABLE [dbo].[ORDER_LIST_LINES] ADD  DEFAULT (newid()) FOR [line_uuid]
GO
ALTER TABLE [dbo].[ORDER_LIST_LINES] ADD  DEFAULT (NULL) FOR [sync_state]
GO
ALTER TABLE [dbo].[ORDER_LIST_LINES] ADD  DEFAULT (getutcdate()) FOR [created_at]
GO
ALTER TABLE [dbo].[ORDER_LIST_LINES] ADD  DEFAULT (getutcdate()) FOR [updated_at]
GO
ALTER TABLE [dbo].[ORDER_LIST_LINES]  WITH CHECK ADD  CONSTRAINT [FK_ORDER_LIST_LINES_record_uuid] FOREIGN KEY([record_uuid])
REFERENCES [dbo].[ORDER_LIST_V2] ([record_uuid])
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[ORDER_LIST_LINES] CHECK CONSTRAINT [FK_ORDER_LIST_LINES_record_uuid]
GO
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TRIGGER [dbo].[tr_ORDER_LIST_LINES_updated_at]
ON [dbo].[ORDER_LIST_LINES]
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.ORDER_LIST_LINES
    SET updated_at = GETUTCDATE()
    FROM dbo.ORDER_LIST_LINES oll
    INNER JOIN inserted i ON oll.line_uuid = i.line_uuid;
END;

-- =============================================================================
-- Success message
-- =============================================================================

PRINT 'Migration 001: Shadow tables created successfully';
PRINT '  - ORDER_LIST_V2: Shadow table for development';
PRINT '  - ORDER_LIST_LINES: Size/quantity normalization';
PRINT '  - ORDER_LIST_DELTA: Header change tracking';
PRINT '  - ORDER_LIST_LINES_DELTA: Line change tracking';
PRINT '';
PRINT 'Next Steps:';
PRINT '  1. Deploy to development database';
PRINT '  2. Configure TOML settings for development environment';
PRINT '  3. Test shadow table population';
PRINT '  4. Validate hash generation and change detection';
GO
ALTER TABLE [dbo].[ORDER_LIST_LINES] ENABLE TRIGGER [tr_ORDER_LIST_LINES_updated_at]
GO
