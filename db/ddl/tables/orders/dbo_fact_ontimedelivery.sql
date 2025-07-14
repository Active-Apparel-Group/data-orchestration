-- Table: dbo.FACT_OntimeDelivery
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[FACT_OntimeDelivery] (
    [ShipmentID] BIGINT NULL,
    [PO] NVARCHAR(MAX) NULL,
    [Customer] NVARCHAR(MAX) NULL,
    [Ship_Mode] NVARCHAR(MAX) NULL,
    [Country] NVARCHAR(MAX) NULL,
    [SKUBarcode] NVARCHAR(MAX) NULL,
    [Style] NVARCHAR(MAX) NULL,
    [Color] NVARCHAR(MAX) NULL,
    [Size] NVARCHAR(MAX) NULL,
    [Qty] BIGINT NULL,
    [Original_Exf_Date] DATE NULL,
    [Confirmed_Exf_Date] DATE NULL,
    [Actual_Exf_Date] DATE NULL,
    [Actual VS Original] BIGINT NULL,
    [Actual VS Confirmed] BIGINT NULL,
    [OnTimeOrigDt] BIGINT NULL,
    [OnTimeConfDt] BIGINT NULL
);
