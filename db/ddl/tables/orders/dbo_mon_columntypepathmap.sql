-- Table: dbo.MON_ColumnTypePathMap
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[MON_ColumnTypePathMap] (
    [column_type] NVARCHAR(100) NOT NULL,
    [new_value_path] NVARCHAR(200) NULL,
    [previous_value_path] NVARCHAR(200) NULL,
    CONSTRAINT [PK_MON_ColumnTypePathMap] PRIMARY KEY ([column_type])
);
