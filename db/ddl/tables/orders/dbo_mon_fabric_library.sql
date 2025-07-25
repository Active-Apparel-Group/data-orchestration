-- Table: dbo.MON_Fabric_Library
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[MON_Fabric_Library] (
    [Customer Code] NVARCHAR(255) NULL,
    [UpdateDate] NVARCHAR(255) NULL,
    [Group] NVARCHAR(255) NULL,
    [Item ID] BIGINT NOT NULL,
    [Subitems] NVARCHAR(MAX) NULL,
    [AAG CODE] NVARCHAR(MAX) NULL,
    [ND/NS] NVARCHAR(100) NULL,
    [ND/NS CODE] NVARCHAR(MAX) NULL,
    [MILL ARTICLE] NVARCHAR(MAX) NULL,
    [ACTIVE] NVARCHAR(100) NULL,
    [OLD CODE] NVARCHAR(MAX) NULL,
    [FABRIC NAME] NVARCHAR(MAX) NULL,
    [FABRIC NAME CN] NVARCHAR(MAX) NULL,
    [MATERIAL TYPE] NVARCHAR(100) NULL,
    [FABRIC GROUP] NVARCHAR(100) NULL,
    [COMPOSITION] NVARCHAR(MAX) NULL,
    [GSM] DECIMAL(18,2) NULL,
    [WIDTH (CM)] DECIMAL(18,2) NULL,
    [CUTTABLE WIDTH (CM)] DECIMAL(18,2) NULL,
    [MILL] NVARCHAR(MAX) NULL,
    [COO] NVARCHAR(MAX) NULL,
    [PRICE] DECIMAL(18,2) NULL,
    [PRICING UNIT] NVARCHAR(100) NULL,
    [CURRENCY] NVARCHAR(MAX) NULL,
    [UNIT OF MEASURE] NVARCHAR(100) NULL,
    [CURR CONV] NVARCHAR(MAX) NULL,
    [FX Rate] NVARCHAR(MAX) NULL,
    [RMB/M] DECIMAL(18,2) NULL,
    [USD/M] DECIMAL(18,2) NULL,
    [MOQ (M)] DECIMAL(18,2) NULL,
    [MCQ (M)] DECIMAL(18,2) NULL,
    [MOQ (SURCHARGE)] NVARCHAR(MAX) NULL,
    [MCQ (M) SURCHARGE] NVARCHAR(MAX) NULL,
    [LEAD TIME] DECIMAL(18,2) NULL,
    [YIELD] DECIMAL(18,2) NULL,
    [KNITTING] DECIMAL(18,2) NULL,
    [DYEING/FINISHING] DECIMAL(18,2) NULL,
    [FABRIC TRANSIT] DECIMAL(18,2) NULL,
    [TOTAL FABRIC L/T] NVARCHAR(MAX) NULL,
    [FDS - AAG] NVARCHAR(255) NULL,
    [FDS/FIS - FROM CUSTOMER] NVARCHAR(255) NULL,
    [CARE INSTRUCTIONS] NVARCHAR(MAX) NULL,
    [TEST REPORTS] NVARCHAR(255) NULL,
    [SPECIAL PROPERTY TESTING] NVARCHAR(255) NULL,
    [SPECIAL PROPERTIES] NVARCHAR(MAX) NULL,
    [NOTES] NVARCHAR(MAX) NULL,
    [CUSTOMER] NVARCHAR(100) NULL,
    [NOMINATED] NVARCHAR(100) NULL,
    [ECO] NVARCHAR(100) NULL
);
