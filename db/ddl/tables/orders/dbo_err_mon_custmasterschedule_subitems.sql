-- Table: dbo.ERR_MON_CustMasterSchedule_Subitems
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[ERR_MON_CustMasterSchedule_Subitems] (
    [err_id] BIGINT NOT NULL,
    [original_stg_subitem_id] BIGINT NULL,
    [parent_item_id] BIGINT NULL,
    [batch_id] UNIQUEIDENTIFIER NULL,
    [customer_batch] NVARCHAR(100) NULL,
    [order_number] NVARCHAR(100) NULL,
    [size_label] NVARCHAR(50) NULL,
    [order_qty] BIGINT NULL,
    [subitem_name] NVARCHAR(200) NULL,
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
    CONSTRAINT [PK_ERR_MON_CustMasterSchedule_Subitems] PRIMARY KEY ([err_id])
);

-- Indexes
CREATE INDEX [IX_ERR_MON_CustMasterSchedule_Subitems_BatchId] ON [dbo].[ERR_MON_CustMasterSchedule_Subitems] ([batch_id]);
CREATE INDEX [IX_ERR_MON_CustMasterSchedule_Subitems_CustomerBatch] ON [dbo].[ERR_MON_CustMasterSchedule_Subitems] ([customer_batch]);
CREATE INDEX [IX_ERR_MON_CustMasterSchedule_Subitems_ErrorType] ON [dbo].[ERR_MON_CustMasterSchedule_Subitems] ([error_type]);
CREATE INDEX [IX_ERR_MON_CustMasterSchedule_Subitems_ParentId] ON [dbo].[ERR_MON_CustMasterSchedule_Subitems] ([parent_item_id]);
CREATE INDEX [IX_ERR_MON_CustMasterSchedule_Subitems_RetryEligible] ON [dbo].[ERR_MON_CustMasterSchedule_Subitems] ([max_retries_reached]);
