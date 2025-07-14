-- Table: dbo.swp_FM_orders_packed
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[swp_FM_orders_packed] (
    [Customer] NVARCHAR(255) NULL,
    [Customer_PO] NVARCHAR(255) NULL,
    [Season] NVARCHAR(255) NULL,
    [cartonid] BIGINT NULL,
    [Pack_Date] DATETIME2 NULL,
    [Shipping_Method] NVARCHAR(255) NULL,
    [shippingCountry] NVARCHAR(255) NULL,
    [Style] NVARCHAR(255) NULL,
    [Color] NVARCHAR(255) NULL,
    [Size] NVARCHAR(255) NULL,
    [SKUBarcode] NVARCHAR(255) NULL,
    [Stock_Age] NVARCHAR(255) NULL,
    [Qty] BIGINT NULL
);
