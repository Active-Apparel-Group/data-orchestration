-- Table: dbo.MON_Customers
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[MON_Customers] (
    [Customer] NVARCHAR(255) NULL,
    [UpdateDate] NVARCHAR(255) NULL,
    [Group] NVARCHAR(255) NULL,
    [Item ID] BIGINT NOT NULL,
    [Subitems] NVARCHAR(MAX) NULL,
    [Account Manager] NVARCHAR(255) NULL,
    [link to Accounts] NVARCHAR(MAX) NULL,
    [CUSTOMER_Dropdown] NVARCHAR(100) NULL,
    [Customer_Map_LP] NVARCHAR(100) NULL,
    [Customer_Category_LP] NVARCHAR(100) NULL,
    [CUSTOMER ALLOCATION] NVARCHAR(100) NULL,
    [PLANNING BOARD] NVARCHAR(MAX) NULL,
    [Customer_Map_MOL] NVARCHAR(100) NULL,
    [CUSTOMER GROUP] NVARCHAR(100) NULL,
    [Planner] NVARCHAR(255) NULL,
    [SEASON LIBRARY] NVARCHAR(MAX) NULL
);
