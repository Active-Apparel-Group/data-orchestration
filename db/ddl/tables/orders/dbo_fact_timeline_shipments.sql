-- Table: dbo.FACT_timeline_Shipments
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[FACT_timeline_Shipments] (
    [Customer] NVARCHAR(MAX) NULL,
    [shipmentid] NVARCHAR(MAX) NULL,
    [po] NVARCHAR(MAX) NULL,
    [style] NVARCHAR(MAX) NULL,
    [color] NVARCHAR(MAX) NULL,
    [season] NVARCHAR(MAX) NULL,
    [InstoreWeek] NVARCHAR(MAX) NULL,
    [Ex-factoryDate] DATE NULL,
    [Qty] INT NULL,
    [FOB_Price] FLOAT NULL,
    [sum_price] FLOAT NULL,
    [Source] NVARCHAR(MAX) NULL,
    [StyleColorPOID] INT NULL
);
