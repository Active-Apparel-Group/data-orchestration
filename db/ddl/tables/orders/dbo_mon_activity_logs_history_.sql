-- Table: dbo.MON_Activity_Logs_History_
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[MON_Activity_Logs_History_] (
    [ActivityLogID] NVARCHAR(36) NOT NULL,
    [EventName] NVARCHAR(100) NULL,
    [EventData] NVARCHAR(MAX) NULL,
    [UserID] NVARCHAR(50) NULL,
    [CreatedAt] NVARCHAR(50) NULL,
    CONSTRAINT [PK_MON_Activity_Logs_History_] PRIMARY KEY ([ActivityLogID])
);
