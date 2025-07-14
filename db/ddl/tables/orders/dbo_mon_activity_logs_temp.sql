-- Table: dbo.MON_Activity_Logs_Temp
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[MON_Activity_Logs_Temp] (
    [id] NVARCHAR(36) NULL,
    [event] NVARCHAR(100) NULL,
    [data] NVARCHAR(MAX) NULL,
    [user_id] NVARCHAR(50) NULL,
    [created_at] NVARCHAR(50) NULL
);
