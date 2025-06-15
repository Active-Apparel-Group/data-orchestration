-- Monday.com Board Groups Table
-- Stores board groups information from Monday.com Customer Master Schedule board
-- Created: June 15, 2025

CREATE TABLE [dbo].[mon_boards_groups] (
    [board_id] NVARCHAR(20) NOT NULL,
    [board_name] NVARCHAR(255) NOT NULL,
    [group_id] NVARCHAR(50) NOT NULL,
    [group_title] NVARCHAR(255) NOT NULL,
    [created_date] DATETIME2 NOT NULL DEFAULT GETDATE(),
    [updated_date] DATETIME2 NOT NULL DEFAULT GETDATE(),
    [is_active] BIT NOT NULL DEFAULT 1,
    
    -- Primary key on board_id and group_id combination
    CONSTRAINT [PK_mon_boards_groups] PRIMARY KEY CLUSTERED ([board_id], [group_id])
);

-- Index for efficient querying by board
CREATE NONCLUSTERED INDEX [IX_mon_boards_groups_BoardId] 
ON [dbo].[mon_boards_groups] ([board_id]) 
INCLUDE ([board_name], [group_title], [is_active]);

-- Index for querying by group title
CREATE NONCLUSTERED INDEX [IX_mon_boards_groups_GroupTitle] 
ON [dbo].[mon_boards_groups] ([group_title]) 
INCLUDE ([board_id], [group_id], [is_active]);

-- Index for active records
CREATE NONCLUSTERED INDEX [IX_mon_boards_groups_Active] 
ON [dbo].[mon_boards_groups] ([is_active]) 
WHERE [is_active] = 1
INCLUDE ([board_id], [group_id], [group_title]);
