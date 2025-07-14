-- Table: dbo.MON_Purchase_Contracts
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[MON_Purchase_Contracts] (
    [Contract] NVARCHAR(MAX) NULL,
    [UpdateDate] DATETIME2 NULL,
    [Group] NVARCHAR(MAX) NULL,
    [REV] BIGINT NULL,
    [PO File] NVARCHAR(MAX) NULL,
    [Partner PO Units] BIGINT NULL,
    [Currency] NVARCHAR(MAX) NULL,
    [PO Value] FLOAT NULL,
    [Bulk PO Qty] BIGINT NULL,
    [Partner Factory] NVARCHAR(MAX) NULL,
    [Legal Entity] NVARCHAR(MAX) NULL,
    [Factory Country] NVARCHAR(MAX) NULL,
    [ALLOCATION STATUS] NVARCHAR(MAX) NULL,
    [Allocation Owner] NVARCHAR(MAX) NULL,
    [Allocation Due] DATE NULL,
    [Factory Location] NVARCHAR(MAX) NULL,
    [Raise PO] NVARCHAR(MAX) NULL,
    [Approve PO] NVARCHAR(MAX) NULL,
    [PO Status] NVARCHAR(MAX) NULL,
    [PO Raised Date] DATE NULL,
    [PO Approval Status] NVARCHAR(MAX) NULL,
    [PO Approved Date] DATE NULL,
    [CMP Partner] FLOAT NULL,
    [CMP LS] FLOAT NULL,
    [CMP Diff (USD)] FLOAT NULL,
    [CMP Per Garment] FLOAT NULL,
    [CUSTOMER] NVARCHAR(MAX) NULL,
    [Item ID] BIGINT NULL,
    [ID] NVARCHAR(MAX) NULL,
    [Contract ID] NVARCHAR(MAX) NULL,
    [LS % of Partner] FLOAT NULL
);
