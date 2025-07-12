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
    [stg_error_message] NVARCHAR(MAX) NULL,
    [stg_retry_count] INT NOT NULL DEFAULT ((0)),
    [stg_api_payload] NVARCHAR(MAX) NULL,
    [AAG_ORDER_NUMBER] NVARCHAR(50) NULL,
    [STYLE] NVARCHAR(100) NULL,
    [COLOR] NVARCHAR(100) NULL,
    [PO_NUMBER] NVARCHAR(50) NULL,
    [CUSTOMER_ALT_PO] NVARCHAR(50) NULL,
    [CUSTOMER] NVARCHAR(100) NULL,
    [Size] NVARCHAR(10) NOT NULL,
    [ORDER_QTY] DECIMAL(18,2) NOT NULL,
    [UNIT_OF_MEASURE] NVARCHAR(20) NULL,
    [source_uuid] UNIQUEIDENTIFIER NULL,
    [stg_size_label] NVARCHAR(100) NULL,
    [stg_monday_subitem_board_id] BIGINT NULL,
    [Order Qty] NVARCHAR(MAX) NULL,
    [Shipped Qty] NVARCHAR(MAX) NULL,
    [Packed Qty] NVARCHAR(MAX) NULL,
    [Cut Qty] NVARCHAR(MAX) NULL,
    [Sew Qty] NVARCHAR(MAX) NULL,
    [Finishing Qty] NVARCHAR(MAX) NULL,
    [Received not Shipped Qty] NVARCHAR(MAX) NULL,
    [ORDER LINE STATUS] NVARCHAR(200) NULL,
    [Item ID] NVARCHAR(200) NULL,
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
