-- Table: dbo.DIM_Style_Season
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[DIM_Style_Season] (
    [StyleColID] INT NULL,
    [StyleColorPOID] INT NULL,
    [Customer] NVARCHAR(255) NULL,
    [Style] NVARCHAR(100) NULL,
    [Color] NVARCHAR(255) NULL,
    [Style_Longson] NVARCHAR(MAX) NULL,
    [Season_Customer] NVARCHAR(MAX) NULL,
    [Season] NVARCHAR(MAX) NULL,
    [Drop] NVARCHAR(MAX) NULL,
    [AAG Season] NVARCHAR(MAX) NULL,
    [Essential/Core/ACC] NVARCHAR(MAX) NULL,
    [PO] NVARCHAR(MAX) NULL,
    [PO QTY] BIGINT NULL,
    [Customer request exfty date] DATE NULL,
    [Revised Ex-fty Date] DATE NULL,
    [Fabric ETA Date] DATE NULL,
    [Fabric Status] NVARCHAR(MAX) NULL,
    [Trims ETA Date] DATE NULL,
    [Trims Status] NVARCHAR(MAX) NULL,
    [PPS Sign off Date] DATE NULL,
    [PPS Status] NVARCHAR(MAX) NULL
);

-- Indexes
CREATE INDEX [IDX_DIM_Style_Season_Style_Color] ON [dbo].[DIM_Style_Season] ([Style], [Color]);
CREATE INDEX [IDX_DIM_Style_Season_StyleColID] ON [dbo].[DIM_Style_Season] ([StyleColID]);
CREATE INDEX [Index_DIM_Style_Season_StyleColorPOID] ON [dbo].[DIM_Style_Season] ([StyleColorPOID]);
