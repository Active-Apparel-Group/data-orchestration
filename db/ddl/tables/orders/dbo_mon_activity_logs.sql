-- Table: dbo.MON_Activity_Logs
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[MON_Activity_Logs] (
    [id] NVARCHAR(36) NOT NULL,
    [event] NVARCHAR(100) NULL,
    [data] NVARCHAR(MAX) NULL,
    [user_id] NVARCHAR(50) NULL,
    [created_at] NVARCHAR(50) NULL,
    CONSTRAINT [PK_MON_Activity_Logs] PRIMARY KEY ([id])
);
