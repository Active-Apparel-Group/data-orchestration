-- Table: dbo.etl_ORDER_LIST_stats
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[etl_ORDER_LIST_stats] (
    [run_id] INT NOT NULL,
    [table_name] NVARCHAR(128) NULL,
    [rows_loaded] INT NULL,
    [load_time] DATETIME2 NULL,
    [error_msg] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_etl_ORDER_LIST_stats] PRIMARY KEY ([run_id])
);
