-- Table: dbo.MON_COO_DailySnapshot
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[MON_COO_DailySnapshot] (
    [SnapshotDate] DATE NOT NULL DEFAULT (CONVERT([date],getutcdate())),
    [ItemID] BIGINT NULL,
    [StyleKey] NVARCHAR(MAX) NULL,
    [FieldName] NVARCHAR(255) NULL,
    [FieldValue] NVARCHAR(MAX) NULL
);
