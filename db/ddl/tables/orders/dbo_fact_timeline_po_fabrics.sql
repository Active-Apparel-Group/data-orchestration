-- Table: dbo.FACT_timeline_PO_fabrics
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[FACT_timeline_PO_fabrics] (
    [Factory_Style] NVARCHAR(MAX) NULL,
    [Style] NVARCHAR(MAX) NULL,
    [PO_Number] NVARCHAR(MAX) NULL,
    [Customer] NVARCHAR(MAX) NULL,
    [Season] NVARCHAR(MAX) NULL,
    [AAG Season] NVARCHAR(MAX) NULL,
    [Style_Color] NVARCHAR(MAX) NULL,
    [MMHDPR] NVARCHAR(MAX) NULL,
    [ITCL] NVARCHAR(MAX) NULL,
    [MMITGR] NVARCHAR(MAX) NULL,
    [MMITTY] NVARCHAR(MAX) NULL,
    [MMPRGP] NVARCHAR(MAX) NULL,
    [MOITNO] NVARCHAR(MAX) NULL,
    [MMITDS] NVARCHAR(MAX) NULL,
    [MMFUDS] NVARCHAR(MAX) NULL,
    [MO_status] NVARCHAR(MAX) NULL,
    [min_material_status] NVARCHAR(MAX) NULL,
    [max_material_status] NVARCHAR(MAX) NULL,
    [qty_demand] FLOAT NULL,
    [demand_planning_date] NVARCHAR(MAX) NULL,
    [purchase_qty] FLOAT NULL,
    [manufacturing_qty] FLOAT NULL,
    [inventory_qty] FLOAT NULL,
    [purchase_planning_date] DATE NULL,
    [manufacturing_planning_date] DATE NULL,
    [inventory_planning_date] DATE NULL,
    [inventory_release_date] DATE NULL,
    [purchase_release_date] DATE NULL,
    [manufacturing_release_date] DATE NULL,
    [min_supply_planning_date] DATE NULL,
    [max_supply_planning_date] DATE NULL,
    [supply_chain_location] NVARCHAR(MAX) NULL,
    [StyleColorPOID] INT NULL
);
