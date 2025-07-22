-- Table: dbo.STG_MON_CustMasterSchedule_Subitems
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[STG_MON_CustMasterSchedule_Subitems] (
    [stg_id] BIGINT NOT NULL,
    [stg_batch_id] NVARCHAR(36) NOT NULL,
    [stg_parent_stg_id] BIGINT NULL,
    [stg_status] NVARCHAR(20) NOT NULL DEFAULT ('PENDING'),
    [stg_created_date] DATETIME2 NOT NULL DEFAULT (getdate()),
    [stg_processed_date] DATETIME2 NULL,
    [stg_monday_subitem_id] BIGINT NULL,
    [stg_monday_parent_item_id] BIGINT NULL,
    [stg_monday_subitem_board_id] BIGINT NULL,
    [stg_error_message] NVARCHAR(MAX) NULL,
    [stg_retry_count] INT NOT NULL DEFAULT ((0)),
    [stg_api_payload] NVARCHAR(MAX) NULL,
    [source_uuid] UNIQUEIDENTIFIER NULL,
    [AAG_ORDER_NUMBER] NVARCHAR(50) NULL,
    [STYLE] NVARCHAR(100) NULL,
    [COLOR] NVARCHAR(100) NULL,
    [PO_NUMBER] NVARCHAR(50) NULL,
    [CUSTOMER_ALT_PO] NVARCHAR(50) NULL,
    [CUSTOMER] NVARCHAR(100) NULL,
    [ORDER_QTY] INT NOT NULL,
    [UNIT_OF_MEASURE] NVARCHAR(20) NULL,
    [Size] NVARCHAR(20) NOT NULL,
    [stg_size_label] NVARCHAR(100) NULL,
    [Order Qty] INT NULL,
    [Shipped Qty] INT NULL,
    [Packed Qty] INT NULL,
    [Cut Qty] INT NULL,
    [Sew Qty] INT NULL,
    [Finishing Qty] INT NULL,
    [Received not Shipped Qty] INT NULL,
    [ORDER LINE STATUS] NVARCHAR(100) NULL,
    [Item ID] BIGINT NULL,
    [update_operation] VARCHAR(50) NULL DEFAULT ('CREATE'),
    [update_fields] NVARCHAR(MAX) NULL,
    [source_table] VARCHAR(100) NULL,
    [source_query] NVARCHAR(MAX) NULL,
    [update_batch_id] VARCHAR(50) NULL,
    [validation_status] VARCHAR(20) NULL DEFAULT ('PENDING'),
    [validation_errors] NVARCHAR(MAX) NULL,
    [board_id] BIGINT NULL,
    CONSTRAINT [PK_STG_MON_CustMasterSchedule_Subitems] PRIMARY KEY ([stg_id])
);

-- Indexes
CREATE INDEX [IX_STG_MON_CustMasterSchedule_Subitems_AAGOrder] ON [dbo].[STG_MON_CustMasterSchedule_Subitems] ([AAG_ORDER_NUMBER]);
CREATE INDEX [IX_STG_MON_CustMasterSchedule_Subitems_BatchId] ON [dbo].[STG_MON_CustMasterSchedule_Subitems] ([stg_batch_id]);
CREATE INDEX [IX_STG_MON_CustMasterSchedule_Subitems_board_id] ON [dbo].[STG_MON_CustMasterSchedule_Subitems] ([stg_monday_subitem_board_id]);
CREATE INDEX [IX_STG_MON_CustMasterSchedule_Subitems_ParentId] ON [dbo].[STG_MON_CustMasterSchedule_Subitems] ([stg_monday_parent_item_id]);
CREATE INDEX [IX_STG_MON_CustMasterSchedule_Subitems_ParentStgId] ON [dbo].[STG_MON_CustMasterSchedule_Subitems] ([stg_parent_stg_id]);
CREATE INDEX [IX_STG_MON_CustMasterSchedule_Subitems_source_uuid] ON [dbo].[STG_MON_CustMasterSchedule_Subitems] ([source_uuid]);
CREATE INDEX [IX_STG_MON_CustMasterSchedule_Subitems_Status] ON [dbo].[STG_MON_CustMasterSchedule_Subitems] ([stg_status]);
