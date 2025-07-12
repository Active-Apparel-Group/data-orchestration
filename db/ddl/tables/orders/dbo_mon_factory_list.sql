-- Table: dbo.MON_Factory_List
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[MON_Factory_List] (
    [Factory] NVARCHAR(255) NULL,
    [UpdateDate] NVARCHAR(255) NULL,
    [Group] NVARCHAR(255) NULL,
    [Item ID] BIGINT NULL,
    [FACTORY LOOKUP] NVARCHAR(255) NULL,
    [Factory Address] NVARCHAR(255) NULL,
    [Factory Name (Consignee)] NVARCHAR(255) NULL,
    [Factory (City)] NVARCHAR(255) NULL,
    [Factory (Province)] NVARCHAR(255) NULL,
    [Country] NVARCHAR(255) NULL,
    [Phone] NVARCHAR(255) NULL,
    [Legal Entity] NVARCHAR(255) NULL,
    [Legal Entity Address] NVARCHAR(255) NULL,
    [Legal Country] NVARCHAR(255) NULL,
    [Map_LP] NVARCHAR(255) NULL,
    [OUTSOURCED] NVARCHAR(255) NULL,
    [PRODUCTION TYPE] NVARCHAR(255) NULL,
    [PAYMENT METHOD NOTES] NVARCHAR(727) NULL,
    [PAYMENT METHOD] NVARCHAR(255) NULL,
    [PAYMENT TERMS] NVARCHAR(255) NULL,
    [CURRENCY] NVARCHAR(255) NULL
);
