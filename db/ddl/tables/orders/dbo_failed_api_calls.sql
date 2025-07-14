-- Table: dbo.Failed_API_Calls
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[Failed_API_Calls] (
    [id] INT NOT NULL,
    [staging_id] NVARCHAR(50) NULL,
    [order_number] NVARCHAR(100) NULL,
    [item_name] NVARCHAR(500) NULL,
    [group_name] NVARCHAR(200) NULL,
    [api_payload] NVARCHAR(MAX) NULL,
    [error_message] NVARCHAR(MAX) NULL,
    [error_type] NVARCHAR(100) NULL,
    [created_date] DATETIME NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Failed_API_Calls] PRIMARY KEY ([id])
);
