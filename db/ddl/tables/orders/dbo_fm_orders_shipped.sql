-- Table: dbo.FM_orders_shipped
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[FM_orders_shipped] (
    [Customer] NVARCHAR(255) NULL,
    [CartonID] BIGINT NULL,
    [Customer_PO] NVARCHAR(255) NULL,
    [Season] NVARCHAR(255) NULL,
    [Shipped_Date] DATETIME2 NULL,
    [Style] NVARCHAR(255) NULL,
    [Color] NVARCHAR(255) NULL,
    [Size] NVARCHAR(255) NULL,
    [SKUBarcode] NVARCHAR(255) NULL,
    [Shipping_Method] NVARCHAR(255) NULL,
    [shippingCountry] NVARCHAR(255) NULL,
    [Qty] BIGINT NULL
);
