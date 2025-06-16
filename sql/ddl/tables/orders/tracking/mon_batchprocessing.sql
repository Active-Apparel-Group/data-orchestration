-- Table: dbo.MON_BatchProcessing
-- Database: ORDERS
-- Purpose: Batch tracking table for Monday.com integration workflow monitoring
-- Dependencies: Tracks progress and status of customer batch processing

CREATE TABLE [dbo].[MON_BatchProcessing] (
    [batch_id] UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    [customer_name] NVARCHAR(100) NOT NULL,
    [batch_type] NVARCHAR(50) NOT NULL, -- 'ORDERS', 'SUBITEMS', 'FULL_BATCH'
    [status] NVARCHAR(50) DEFAULT 'STARTED', -- STARTED, STAGING_LOADED, ITEMS_CREATED, SUBITEMS_CREATED, PROMOTED, COMPLETED, FAILED
    [total_records] INT NULL,
    [successful_records] INT NULL,
    [failed_records] INT NULL,
    [start_time] DATETIME2 DEFAULT GETDATE(),
    [end_time] DATETIME2 NULL,
    [duration_seconds] AS DATEDIFF(SECOND, [start_time], [end_time]),
    [error_summary] NVARCHAR(MAX) NULL,
    [processing_notes] NVARCHAR(MAX) NULL,
    
    -- Performance metrics
    [orders_processed] INT NULL,
    [subitems_processed] INT NULL,
    [api_calls_made] INT NULL,
    [api_failures] INT NULL,
    [retries_attempted] INT NULL,
    
    -- Status tracking
    [staging_load_completed] DATETIME2 NULL,
    [items_creation_completed] DATETIME2 NULL,
    [subitems_creation_completed] DATETIME2 NULL,
    [promotion_completed] DATETIME2 NULL,
    [cleanup_completed] DATETIME2 NULL,
    
    -- User tracking
    [started_by] NVARCHAR(100) DEFAULT SYSTEM_USER,
    [completed_by] NVARCHAR(100) NULL,
    
    -- Configuration used
    [config_snapshot] NVARCHAR(MAX) NULL -- JSON snapshot of configuration used
);

-- Create indexes for monitoring and reporting
CREATE INDEX IX_MON_BatchProcessing_Customer ON [dbo].[MON_BatchProcessing] ([customer_name]);
CREATE INDEX IX_MON_BatchProcessing_Status ON [dbo].[MON_BatchProcessing] ([status]);
CREATE INDEX IX_MON_BatchProcessing_StartTime ON [dbo].[MON_BatchProcessing] ([start_time]);
CREATE INDEX IX_MON_BatchProcessing_BatchType ON [dbo].[MON_BatchProcessing] ([batch_type]);
