-- Table: dbo.MON_Customers
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[MON_Customers] (
    [Customer] NVARCHAR(255) NULL,
    [UpdateDate] NVARCHAR(255) NULL,
    [Group] NVARCHAR(255) NULL,
    [Item ID] BIGINT NULL,
    [Subitems] NVARCHAR(255) NULL,
    [Account Manager] NVARCHAR(255) NULL,
    [link to Accounts] NVARCHAR(255) NULL,
    [CUSTOMER_Dropdown] NVARCHAR(255) NULL,
    [Customer_Map_LP] NVARCHAR(255) NULL,
    [Customer_Category_LP] NVARCHAR(255) NULL,
    [CUSTOMER ALLOCATION] NVARCHAR(255) NULL,
    [PLANNING BOARD] NVARCHAR(MAX) NULL,
    [Customer_Map_MOL] NVARCHAR(255) NULL,
    [CUSTOMER GROUP] NVARCHAR(255) NULL,
    [Planner] NVARCHAR(255) NULL,
    [SEASON LIBRARY] NVARCHAR(255) NULL
);
