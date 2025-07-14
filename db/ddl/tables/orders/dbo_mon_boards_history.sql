-- Table: dbo.MON_Boards_History
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[MON_Boards_History] (
    [data.boards.id] NVARCHAR(MAX) NULL,
    [data.boards.name] NVARCHAR(MAX) NULL,
    [data.boards.state] NVARCHAR(MAX) NULL,
    [data.boards.board_kind] NVARCHAR(MAX) NULL,
    [data.boards.workspace_id] NVARCHAR(MAX) NULL,
    [retrieved_at] DATETIME2 NOT NULL
);
