-- Table: dbo.MON_CustMasterSchedule_Subitems
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[MON_CustMasterSchedule_Subitems] (
    [parent_item_id] NVARCHAR(MAX) NULL,
    [subitem_id] NVARCHAR(MAX) NULL,
    [subitem_board_id] NVARCHAR(MAX) NULL,
    [Size] NVARCHAR(MAX) NULL,
    [Order Qty] NVARCHAR(MAX) NULL,
    [Cut Qty] NVARCHAR(MAX) NULL,
    [Sew Qty] NVARCHAR(MAX) NULL,
    [Finishing Qty] NVARCHAR(MAX) NULL,
    [Received not Shipped Qty] NVARCHAR(MAX) NULL,
    [Packed Qty] NVARCHAR(MAX) NULL,
    [Shipped Qty] NVARCHAR(MAX) NULL,
    [ORDER LINE STATUS] NVARCHAR(MAX) NULL,
    [Item ID] NVARCHAR(MAX) NULL,
    [validation_status] NVARCHAR(255) NULL,
    [update_operation] NVARCHAR(255) NULL,
    [validation_errors] NVARCHAR(255) NULL,
    [update_batch_id] NVARCHAR(50) NULL,
    [board_id] NVARCHAR(50) NULL,
    [source_query] NVARCHAR(255) NULL,
    [source_table] NVARCHAR(255) NULL,
    [update_fields] NVARCHAR(255) NULL,
    [ORDER_QTY] NVARCHAR(50) NULL,
    [AAG_ORDER_NUMBER] NVARCHAR(50) NULL,
    [UNIT_OF_MEASURE] NVARCHAR(50) NULL,
    [COLOR] NVARCHAR(50) NULL,
    [STYLE] NVARCHAR(50) NULL,
    [CUSTOMER] NVARCHAR(50) NULL,
    [PO_NUMBER] NVARCHAR(50) NULL,
    [CUSTOMER_ALT_PO] NVARCHAR(50) NULL
);
