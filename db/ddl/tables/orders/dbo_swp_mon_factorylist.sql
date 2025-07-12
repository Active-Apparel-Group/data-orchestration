-- Table: dbo.swp_MON_FactoryList
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[swp_MON_FactoryList] (
    [Factory] NVARCHAR(MAX) NULL,
    [UpdateDate] NVARCHAR(MAX) NULL,
    [Group] NVARCHAR(MAX) NULL,
    [Item ID] NVARCHAR(MAX) NULL,
    [FACTORY LOOKUP] NVARCHAR(MAX) NULL,
    [Factory Address] NVARCHAR(MAX) NULL,
    [Factory Name (Consignee)] NVARCHAR(MAX) NULL,
    [Factory (City)] NVARCHAR(MAX) NULL,
    [Factory (Province)] NVARCHAR(MAX) NULL,
    [Country] NVARCHAR(MAX) NULL,
    [Phone] NVARCHAR(MAX) NULL,
    [Legal Entity] NVARCHAR(MAX) NULL,
    [Legal Entity Address] NVARCHAR(MAX) NULL,
    [Legal Country] NVARCHAR(MAX) NULL,
    [Map_LP] NVARCHAR(MAX) NULL,
    [OUTSOURCED] NVARCHAR(MAX) NULL,
    [PRODUCTION TYPE] NVARCHAR(MAX) NULL,
    [PAYMENT METHOD NOTES] NVARCHAR(MAX) NULL,
    [PAYMENT METHOD] NVARCHAR(MAX) NULL,
    [PAYMENT TERMS] NVARCHAR(MAX) NULL,
    [CURRENCY] NVARCHAR(MAX) NULL
);
