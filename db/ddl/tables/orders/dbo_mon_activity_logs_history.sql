-- Table: dbo.MON_Activity_Logs_History
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[MON_Activity_Logs_History] (
    [ActivityLogID] NVARCHAR(MAX) NULL,
    [EventName] NVARCHAR(MAX) NULL,
    [EventData] NVARCHAR(MAX) NULL,
    [UserID] NVARCHAR(MAX) NULL,
    [CreatedAt] NVARCHAR(MAX) NULL,
    [pulse_id_b] BIGINT NULL
);

-- Indexes
CREATE INDEX [IX_MON_Activity_Logs_History_pulse_id_b] ON [dbo].[MON_Activity_Logs_History] ([pulse_id_b]);
