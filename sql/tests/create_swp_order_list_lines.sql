-- Create swp_ORDER_LIST_LINES staging table based on ORDER_LIST_LINES schema
-- Purpose: Staging table for unpivoted size/quantity data before merging to ORDER_LIST_LINES
-- Source: dbo_order_list_lines.sql schema
-- Date: July 21, 2025

-- Drop table if exists
IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'swp_ORDER_LIST_LINES' AND TABLE_SCHEMA = 'dbo')
BEGIN
    PRINT 'Dropping existing swp_ORDER_LIST_LINES table...';
    DROP TABLE [dbo].[swp_ORDER_LIST_LINES];
END

-- Create swp_ORDER_LIST_LINES with identical schema to ORDER_LIST_LINES
PRINT 'Creating swp_ORDER_LIST_LINES staging table...';

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[swp_ORDER_LIST_LINES](
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

-- Primary key
ALTER TABLE [dbo].[swp_ORDER_LIST_LINES] ADD PRIMARY KEY CLUSTERED 
(
	[line_uuid] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

-- Unique constraint on record_uuid + size_code
SET ANSI_PADDING ON
GO
ALTER TABLE [dbo].[swp_ORDER_LIST_LINES] ADD  CONSTRAINT [UQ_swp_ORDER_LIST_LINES_record_size] UNIQUE NONCLUSTERED 
(
	[record_uuid] ASC,
	[size_code] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

-- Indexes
SET ANSI_PADDING ON
GO
CREATE NONCLUSTERED INDEX [IX_swp_ORDER_LIST_LINES_hash] ON [dbo].[swp_ORDER_LIST_LINES]
(
	[row_hash] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

CREATE NONCLUSTERED INDEX [IX_swp_ORDER_LIST_LINES_record_uuid] ON [dbo].[swp_ORDER_LIST_LINES]
(
	[record_uuid] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

SET ANSI_PADDING ON
GO
CREATE NONCLUSTERED INDEX [IX_swp_ORDER_LIST_LINES_sync_state] ON [dbo].[swp_ORDER_LIST_LINES]
(
	[sync_state] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

-- Default constraints
ALTER TABLE [dbo].[swp_ORDER_LIST_LINES] ADD  DEFAULT (newid()) FOR [line_uuid]
GO
ALTER TABLE [dbo].[swp_ORDER_LIST_LINES] ADD  DEFAULT (NULL) FOR [sync_state]
GO
ALTER TABLE [dbo].[swp_ORDER_LIST_LINES] ADD  DEFAULT (getutcdate()) FOR [created_at]
GO
ALTER TABLE [dbo].[swp_ORDER_LIST_LINES] ADD  DEFAULT (getutcdate()) FOR [updated_at]
GO

-- Foreign key to ORDER_LIST_V2 (not swp_ORDER_LIST_V2 since we're in staging)
ALTER TABLE [dbo].[swp_ORDER_LIST_LINES]  WITH CHECK ADD  CONSTRAINT [FK_swp_ORDER_LIST_LINES_record_uuid] FOREIGN KEY([record_uuid])
REFERENCES [dbo].[ORDER_LIST_V2] ([record_uuid])
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[swp_ORDER_LIST_LINES] CHECK CONSTRAINT [FK_swp_ORDER_LIST_LINES_record_uuid]
GO

-- Updated_at trigger
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TRIGGER [dbo].[tr_swp_ORDER_LIST_LINES_updated_at]
ON [dbo].[swp_ORDER_LIST_LINES]
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.swp_ORDER_LIST_LINES
    SET updated_at = GETUTCDATE()
    FROM dbo.swp_ORDER_LIST_LINES oll
    INNER JOIN inserted i ON oll.line_uuid = i.line_uuid;
END;
GO
ALTER TABLE [dbo].[swp_ORDER_LIST_LINES] ENABLE TRIGGER [tr_swp_ORDER_LIST_LINES_updated_at]
GO

-- Success message
PRINT 'SUCCESS: swp_ORDER_LIST_LINES staging table created';
PRINT 'Schema matches ORDER_LIST_LINES with swp_ prefix';
PRINT 'Foreign key links to ORDER_LIST_V2 for development pipeline';
PRINT 'Ready for unpivot_sizes.j2 template Step 2 integration';

-- Validation
SELECT 
    'swp_ORDER_LIST_LINES' as table_name,
    COUNT(*) as column_count
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'swp_ORDER_LIST_LINES' 
  AND TABLE_SCHEMA = 'dbo';
