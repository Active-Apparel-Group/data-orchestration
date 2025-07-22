-- Table: dbo.MON_Factory_List
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[MON_Factory_List] (
    [Factory] NVARCHAR(255) NULL,
    [UpdateDate] NVARCHAR(255) NULL,
    [Group] NVARCHAR(255) NULL,
    [Item ID] DECIMAL(18,2) NOT NULL,
    [FACTORY LOOKUP] NVARCHAR(100) NULL,
    [Factory Address] NVARCHAR(MAX) NULL,
    [Factory Name (Consignee)] NVARCHAR(MAX) NULL,
    [Factory (City)] NVARCHAR(100) NULL,
    [Factory (Province)] NVARCHAR(100) NULL,
    [Country] NVARCHAR(255) NULL,
    [Phone] NVARCHAR(255) NULL,
    [Legal Entity] NVARCHAR(MAX) NULL,
    [Legal Entity Address] NVARCHAR(MAX) NULL,
    [Legal Country] NVARCHAR(255) NULL,
    [Map_LP] NVARCHAR(100) NULL,
    [OUTSOURCED] NVARCHAR(100) NULL,
    [PRODUCTION TYPE] NVARCHAR(100) NULL,
    [PAYMENT METHOD NOTES] NVARCHAR(MAX) NULL,
    [PAYMENT METHOD] NVARCHAR(100) NULL,
    [PAYMENT TERMS] NVARCHAR(100) NULL,
    [CURRENCY] NVARCHAR(MAX) NULL
);
