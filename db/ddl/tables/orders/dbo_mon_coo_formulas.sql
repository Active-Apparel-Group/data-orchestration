-- Table: dbo.MON_COO_Formulas
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[MON_COO_Formulas] (
    [Item ID] BIGINT NULL,
    [ORDER TYPE] NVARCHAR(MAX) NULL,
    [CUSTOMER] NVARCHAR(MAX) NULL,
    [STYLE CODE] NVARCHAR(MAX) NULL,
    [STYLE DESCRIPTION] NVARCHAR(MAX) NULL,
    [Color] NVARCHAR(MAX) NULL,
    [BULK PO QTY] BIGINT NULL,
    [CMP LS] FLOAT NULL,
    [CMP Partner] FLOAT NULL,
    [PO Base (Partner)] FLOAT NULL,
    [PO Other (Partner)] FLOAT NULL,
    [PO MOQ% (Partner)] NVARCHAR(MAX) NULL,
    [PO Unit Total (Partner)] FLOAT NULL,
    [PO Total Value (Partner)] FLOAT NULL,
    [Longson RM EX-FTY] NVARCHAR(MAX) NULL,
    [EX-FTY (Partner PO)] NVARCHAR(MAX) NULL
);
