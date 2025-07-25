-- Table: dbo.MON_Purchase_Contracts
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[MON_Purchase_Contracts] (
    [Contract] NVARCHAR(255) NULL,
    [UpdateDate] NVARCHAR(255) NULL,
    [Group] NVARCHAR(255) NULL,
    [Item ID] BIGINT NOT NULL,
    [Subitems] NVARCHAR(MAX) NULL,
    [REV] DECIMAL(18,2) NULL,
    [PO File] NVARCHAR(MAX) NULL,
    [Supporting Files] NVARCHAR(MAX) NULL,
    [Units] DECIMAL(18,2) NULL,
    [Currency] NVARCHAR(100) NULL,
    [PO Value] DECIMAL(18,2) NULL,
    [Bulk PO Qty] DECIMAL(18,2) NULL,
    [Partner Factory] NVARCHAR(MAX) NULL,
    [Legal Entity] NVARCHAR(MAX) NULL,
    [Factory Country] NVARCHAR(MAX) NULL,
    [Factory Location] NVARCHAR(MAX) NULL,
    [ALLOCATION STATUS] NVARCHAR(100) NULL,
    [Allocation Owner] NVARCHAR(255) NULL,
    [Allocation Due] DATE NULL,
    [Raise PO] NVARCHAR(255) NULL,
    [Approve PO] NVARCHAR(255) NULL,
    [PO Approval Status] NVARCHAR(100) NULL,
    [PO Status] NVARCHAR(100) NULL,
    [PO Approved Date] DATE NULL,
    [PO Raised Date] DATE NULL,
    [link Style COO Plan] NVARCHAR(MAX) NULL,
    [PO Value Planning Board] NVARCHAR(MAX) NULL,
    [stat] NVARCHAR(MAX) NULL,
    [CMP Partner] NVARCHAR(MAX) NULL,
    [CMP LS] NVARCHAR(MAX) NULL,
    [LS % of Partner] NVARCHAR(MAX) NULL,
    [CMP Diff (USD)] NVARCHAR(MAX) NULL,
    [CMP Per Garment] NVARCHAR(MAX) NULL,
    [CUSTOMER] NVARCHAR(100) NULL,
    [COO Planning Allocations] NVARCHAR(MAX) NULL,
    [ID] BIGINT NOT NULL,
    [Contract ID] NVARCHAR(MAX) NULL,
    [TP Issue Date] DATE NULL,
    [Prepare TP] NVARCHAR(255) NULL
);
