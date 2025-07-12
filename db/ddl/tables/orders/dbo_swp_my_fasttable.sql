-- Table: dbo.swp_my_fastTable
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[swp_my_fastTable] (
    [Factory] NVARCHAR(255) NULL,
    [UpdateDate] DATETIME NULL,
    [Group] NVARCHAR(255) NULL,
    [Item ID] BIGINT NULL,
    [FACTORY LOOKUP] NVARCHAR(255) NULL,
    [Factory Address] NVARCHAR(MAX) NULL,
    [Factory Name (Consignee)] NVARCHAR(MAX) NULL,
    [Factory (City)] NVARCHAR(255) NULL,
    [Factory (Province)] NVARCHAR(255) NULL,
    [Legal Entity] NVARCHAR(MAX) NULL,
    [Legal Entity Address] NVARCHAR(255) NULL,
    [BULK PO QTY] NVARCHAR(255) NULL,
    [PARTNER PO QTY] NVARCHAR(255) NULL,
    [Map_LP] NVARCHAR(255) NULL,
    [OUTSOURCED] NVARCHAR(255) NULL,
    [PRODUCTION TYPE] NVARCHAR(255) NULL,
    [PAYMENT METHOD NOTES] NVARCHAR(MAX) NULL,
    [PAYMENT METHOD] NVARCHAR(255) NULL,
    [PAYMENT TERMS] NVARCHAR(255) NULL
);
