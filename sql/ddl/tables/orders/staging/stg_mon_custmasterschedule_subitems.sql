-- Table: dbo.STG_MON_CustMasterSchedule_Subitems
-- Database: ORDERS
-- Purpose: Staging table for Monday.com Customer Master Schedule Subitems integration
-- Dependencies: Mirrors MON_CustMasterSchedule_Subitems with additional staging columns, FK to STG_MON_CustMasterSchedule

CREATE TABLE [dbo].[STG_MON_CustMasterSchedule_Subitems] (
    -- All columns from MON_CustMasterSchedule_Subitems (production table)    [parent_item_id] NVARCHAR(200) NULL,
    [subitem_id] NVARCHAR(200) NULL,
    [subitem_board_id] NVARCHAR(200) NULL,
    [Size] NVARCHAR(100) NULL,
    [Order Qty] NVARCHAR(MAX) NULL,
    [Cut Qty] NVARCHAR(MAX) NULL,
    [Sew Qty] NVARCHAR(MAX) NULL,
    [Finishing Qty] NVARCHAR(MAX) NULL,
    [Received not Shipped Qty] NVARCHAR(MAX) NULL,
    [Packed Qty] NVARCHAR(MAX) NULL,
    [Shipped Qty] NVARCHAR(MAX) NULL,    [ORDER LINE STATUS] NVARCHAR(200) NULL,
    [Item ID] NVARCHAR(200) NULL,

    -- Staging-specific columns for workflow management
    [stg_subitem_id] BIGINT IDENTITY(1,1) PRIMARY KEY,
    [stg_batch_id] UNIQUEIDENTIFIER NOT NULL,
    [stg_parent_stg_id] BIGINT NULL, -- FK to STG_MON_CustMasterSchedule.stg_id
    [stg_customer_batch] NVARCHAR(100) NULL,
    [stg_status] NVARCHAR(50) DEFAULT 'PENDING', -- PENDING, API_SUCCESS, API_FAILED, PROMOTED
    [stg_monday_subitem_id] BIGINT NULL,
    [stg_monday_subitem_board_id] BIGINT NULL,
    [stg_error_message] NVARCHAR(MAX) NULL,
    [stg_api_payload] NVARCHAR(MAX) NULL, -- Store the API payload for debugging
    [stg_retry_count] INT DEFAULT 0,
    [stg_created_date] DATETIME2 DEFAULT GETDATE(),
    [stg_processed_date] DATETIME2 NULL,

    -- Additional fields for size processing
    [stg_source_order_number] NVARCHAR(100) NULL, -- AAG ORDER NUMBER from parent
    [stg_source_style] NVARCHAR(100) NULL,
    [stg_source_color] NVARCHAR(100) NULL,
    [stg_size_label] NVARCHAR(50) NULL, -- Cleaned size label
    [stg_order_qty_numeric] BIGINT NULL -- Numeric version of Order Qty
);

-- Create indexes for performance
CREATE INDEX IX_STG_MON_CustMasterSchedule_Subitems_BatchId ON [dbo].[STG_MON_CustMasterSchedule_Subitems] ([stg_batch_id]);
CREATE INDEX IX_STG_MON_CustMasterSchedule_Subitems_Status ON [dbo].[STG_MON_CustMasterSchedule_Subitems] ([stg_status]);
CREATE INDEX IX_STG_MON_CustMasterSchedule_Subitems_ParentId ON [dbo].[STG_MON_CustMasterSchedule_Subitems] ([stg_parent_stg_id]);
CREATE INDEX IX_STG_MON_CustMasterSchedule_Subitems_CustomerBatch ON [dbo].[STG_MON_CustMasterSchedule_Subitems] ([stg_customer_batch]);

-- Add foreign key constraint to parent staging table
ALTER TABLE [dbo].[STG_MON_CustMasterSchedule_Subitems]
ADD CONSTRAINT FK_STG_Subitems_ParentStgId 
FOREIGN KEY ([stg_parent_stg_id]) 
REFERENCES [dbo].[STG_MON_CustMasterSchedule] ([stg_id]);
