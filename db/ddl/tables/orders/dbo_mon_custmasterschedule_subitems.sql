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
    [Item ID] NVARCHAR(MAX) NULL
);
