-- Table: dbo.ERR_MON_CustMasterSchedule
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[ERR_MON_CustMasterSchedule] (
    [err_id] BIGINT NOT NULL,
    [original_stg_id] BIGINT NULL,
    [batch_id] UNIQUEIDENTIFIER NULL,
    [customer_batch] NVARCHAR(100) NULL,
    [order_number] NVARCHAR(100) NULL,
    [item_name] NVARCHAR(500) NULL,
    [group_name] NVARCHAR(200) NULL,
    [api_payload] NVARCHAR(MAX) NULL,
    [error_type] NVARCHAR(100) NULL,
    [error_message] NVARCHAR(MAX) NULL,
    [http_status_code] INT NULL,
    [retry_count] INT NULL DEFAULT ((0)),
    [max_retries_reached] BIT NULL DEFAULT ((0)),
    [created_date] DATETIME2 NULL DEFAULT (getdate()),
    [last_retry_date] DATETIME2 NULL,
    [resolved_date] DATETIME2 NULL,
    [resolved_by] NVARCHAR(100) NULL,
    [original_data] NVARCHAR(MAX) NULL,
    CONSTRAINT [PK_ERR_MON_CustMasterSchedule] PRIMARY KEY ([err_id])
);

-- Indexes
CREATE INDEX [IX_ERR_MON_CustMasterSchedule_BatchId] ON [dbo].[ERR_MON_CustMasterSchedule] ([batch_id]);
CREATE INDEX [IX_ERR_MON_CustMasterSchedule_CustomerBatch] ON [dbo].[ERR_MON_CustMasterSchedule] ([customer_batch]);
CREATE INDEX [IX_ERR_MON_CustMasterSchedule_ErrorType] ON [dbo].[ERR_MON_CustMasterSchedule] ([error_type]);
CREATE INDEX [IX_ERR_MON_CustMasterSchedule_RetryEligible] ON [dbo].[ERR_MON_CustMasterSchedule] ([max_retries_reached]);
