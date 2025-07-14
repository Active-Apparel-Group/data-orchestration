-- Table: dbo.ERR_MON_CustMasterSchedule
-- Database: ORDERS
-- Purpose: Error table for failed Monday.com API calls - main items
-- Dependencies: Stores failed records from STG_MON_CustMasterSchedule for retry/review

CREATE TABLE [dbo].[ERR_MON_CustMasterSchedule] (
    [err_id] BIGINT IDENTITY(1,1) PRIMARY KEY,
    [original_stg_id] BIGINT NULL,
    [batch_id] UNIQUEIDENTIFIER NULL,
    [customer_batch] NVARCHAR(100) NULL,
    [order_number] NVARCHAR(100) NULL,
    [item_name] NVARCHAR(500) NULL,
    [group_name] NVARCHAR(200) NULL,
    [api_payload] NVARCHAR(MAX) NULL,
    [error_type] NVARCHAR(100) NULL, -- API_ERROR, NETWORK_ERROR, VALIDATION_ERROR, etc.
    [error_message] NVARCHAR(MAX) NULL,
    [http_status_code] INT NULL,
    [retry_count] INT DEFAULT 0,
    [max_retries_reached] BIT DEFAULT 0,
    [created_date] DATETIME2 DEFAULT GETDATE(),
    [last_retry_date] DATETIME2 NULL,
    [resolved_date] DATETIME2 NULL,
    [resolved_by] NVARCHAR(100) NULL,
    -- Store original order data as JSON for complete reprocessing capability
    [original_data] NVARCHAR(MAX) NULL
);

-- Create indexes for error analysis and retry processing
CREATE INDEX IX_ERR_MON_CustMasterSchedule_BatchId ON [dbo].[ERR_MON_CustMasterSchedule] ([batch_id]);
CREATE INDEX IX_ERR_MON_CustMasterSchedule_ErrorType ON [dbo].[ERR_MON_CustMasterSchedule] ([error_type]);
CREATE INDEX IX_ERR_MON_CustMasterSchedule_CustomerBatch ON [dbo].[ERR_MON_CustMasterSchedule] ([customer_batch]);
CREATE INDEX IX_ERR_MON_CustMasterSchedule_RetryEligible ON [dbo].[ERR_MON_CustMasterSchedule] ([max_retries_reached]) WHERE [max_retries_reached] = 0;
