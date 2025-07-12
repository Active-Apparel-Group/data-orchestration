-- Table: dbo.Workspace_Lookup
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[Workspace_Lookup] (
    [Id] INT NOT NULL,
    [Workspace_Id] BIGINT NOT NULL,
    [Workspace_Name] NVARCHAR(255) NULL,
    [IsActive] BIT NOT NULL DEFAULT ((1)),
    [DateCreated] DATETIME2 NOT NULL DEFAULT (getdate()),
    CONSTRAINT [PK_Workspace_Lookup] PRIMARY KEY ([Id])
);

-- Indexes
CREATE UNIQUE INDEX [UQ__Workspac__A15825DB5F343B9E] ON [dbo].[Workspace_Lookup] ([Workspace_Id]);
