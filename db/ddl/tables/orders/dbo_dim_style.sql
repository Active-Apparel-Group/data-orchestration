-- Table: dbo.DIM_Style
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[DIM_Style] (
    [StyleColID] INT NOT NULL,
    [Customer] NVARCHAR(255) NULL,
    [Style] NVARCHAR(100) NULL,
    [Style_Name] NVARCHAR(120) NULL,
    [Color] NVARCHAR(255) NULL,
    [Style Category] NVARCHAR(MAX) NULL,
    [ACTIVE/WOVEN/SWIM/ACC/SEAMLESS] NVARCHAR(MAX) NULL,
    [PRODUCT GROUP] NVARCHAR(MAX) NULL,
    [PRODUCT CAT] NVARCHAR(MAX) NULL,
    CONSTRAINT [PK_DIM_Style] PRIMARY KEY ([StyleColID])
);

-- Indexes
CREATE INDEX [IDX_DIM_Style_Style_Color] ON [dbo].[DIM_Style] ([Style], [Color]);
