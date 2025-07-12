-- Table: dbo.MON_BatchProcessing
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[MON_BatchProcessing] (
    [batch_id] UNIQUEIDENTIFIER NOT NULL DEFAULT (newid()),
    [customer_name] NVARCHAR(100) NOT NULL,
    [batch_type] NVARCHAR(50) NOT NULL,
    [status] NVARCHAR(50) NULL DEFAULT ('STARTED'),
    [total_records] INT NULL,
    [successful_records] INT NULL,
    [failed_records] INT NULL,
    [start_time] DATETIME2 NULL DEFAULT (getdate()),
    [end_time] DATETIME2 NULL,
    [duration_seconds] INT NULL,
    [error_summary] NVARCHAR(MAX) NULL,
    [processing_notes] NVARCHAR(MAX) NULL,
    [orders_processed] INT NULL,
    [subitems_processed] INT NULL,
    [api_calls_made] INT NULL,
    [api_failures] INT NULL,
    [retries_attempted] INT NULL,
    [staging_load_completed] DATETIME2 NULL,
    [items_creation_completed] DATETIME2 NULL,
    [subitems_creation_completed] DATETIME2 NULL,
    [promotion_completed] DATETIME2 NULL,
    [cleanup_completed] DATETIME2 NULL,
    [started_by] NVARCHAR(100) NULL DEFAULT (suser_sname()),
    [completed_by] NVARCHAR(100) NULL,
    [config_snapshot] NVARCHAR(MAX) NULL,
    CONSTRAINT [PK_MON_BatchProcessing] PRIMARY KEY ([batch_id])
);

-- Indexes
CREATE INDEX [IX_MON_BatchProcessing_BatchType] ON [dbo].[MON_BatchProcessing] ([batch_type]);
CREATE INDEX [IX_MON_BatchProcessing_Customer] ON [dbo].[MON_BatchProcessing] ([customer_name]);
CREATE INDEX [IX_MON_BatchProcessing_StartTime] ON [dbo].[MON_BatchProcessing] ([start_time]);
CREATE INDEX [IX_MON_BatchProcessing_Status] ON [dbo].[MON_BatchProcessing] ([status]);
