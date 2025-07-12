-- Table: dbo.DC_StyleColorPO
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[DC_StyleColorPO] (
    [StyleColorPOID] INT NOT NULL,
    [Customer] NVARCHAR(100) NULL,
    [Style] NVARCHAR(100) NULL,
    [Style_Longson] NVARCHAR(100) NULL,
    [Color] NVARCHAR(255) NULL,
    [PO] NVARCHAR(100) NULL,
    [Season] NVARCHAR(100) NULL,
    [Season1] NVARCHAR(100) NULL,
    [Drop] NVARCHAR(100) NULL,
    CONSTRAINT [PK_DC_StyleColorPO] PRIMARY KEY ([StyleColorPOID])
);

-- Indexes
CREATE INDEX [IDX_Color] ON [dbo].[DC_StyleColorPO] ([Color]);
CREATE INDEX [IDX_Customer] ON [dbo].[DC_StyleColorPO] ([Customer]);
CREATE INDEX [IDX_Drop] ON [dbo].[DC_StyleColorPO] ([Drop]);
CREATE INDEX [IDX_PO] ON [dbo].[DC_StyleColorPO] ([PO]);
CREATE INDEX [IDX_Season] ON [dbo].[DC_StyleColorPO] ([Season]);
CREATE INDEX [IDX_Season1] ON [dbo].[DC_StyleColorPO] ([Season1]);
CREATE INDEX [IDX_Style] ON [dbo].[DC_StyleColorPO] ([Style]);
CREATE INDEX [IDX_Style_Longson] ON [dbo].[DC_StyleColorPO] ([Style_Longson]);
