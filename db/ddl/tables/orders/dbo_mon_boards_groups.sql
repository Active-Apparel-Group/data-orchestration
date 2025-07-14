-- Table: dbo.MON_Boards_Groups
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[MON_Boards_Groups] (
    [board_id] NVARCHAR(20) NOT NULL,
    [board_name] NVARCHAR(255) NOT NULL,
    [group_id] NVARCHAR(50) NOT NULL,
    [group_title] NVARCHAR(255) NOT NULL,
    [created_date] DATETIME2 NOT NULL DEFAULT (getdate()),
    [updated_date] DATETIME2 NOT NULL DEFAULT (getdate()),
    [is_active] BIT NOT NULL DEFAULT ((1)),
    CONSTRAINT [PK_MON_Boards_Groups] PRIMARY KEY ([board_id], [group_id])
);

-- Indexes
CREATE INDEX [IX_MON_Boards_Groups_BoardId] ON [dbo].[MON_Boards_Groups] ([board_name], [group_title], [is_active], [board_id]);
CREATE INDEX [IX_MON_Boards_Groups_GroupTitle] ON [dbo].[MON_Boards_Groups] ([board_id], [group_id], [is_active], [group_title]);
