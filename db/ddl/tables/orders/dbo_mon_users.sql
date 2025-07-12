-- Table: dbo.MON_Users
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[MON_Users] (
    [data.users.id] NVARCHAR(MAX) NULL,
    [data.users.name] NVARCHAR(MAX) NULL,
    [data.users.email] NVARCHAR(MAX) NULL,
    [data.users.created_at] NVARCHAR(MAX) NULL,
    [data.users.is_guest] BIT NULL,
    [data.users.is_admin] BIT NULL,
    [data.users.teams.id] NVARCHAR(MAX) NULL,
    [data.users.teams.name] NVARCHAR(MAX) NULL
);
