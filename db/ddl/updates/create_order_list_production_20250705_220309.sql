-- ORDER_LIST Production Schema
-- Generated: 2025-07-05 22:03:09
-- Issues Fixed: Duplicates removed, typos corrected, proper formatting
-- Professional garment size categorization applied

-- Drop existing table if exists
IF OBJECT_ID('dbo.ORDER_LIST', 'U') IS NOT NULL
    DROP TABLE dbo.ORDER_LIST;
GO

-- Create the unified ORDER_LIST table
CREATE TABLE dbo.ORDER_LIST (
    -- === ORDER_DETAILS (27 columns) ===
    [AAG ORDER NUMBER] NVARCHAR(100) NOT NULL,
    [CUSTOMER NAME] NVARCHAR(255) NOT NULL,
    [ORDER DATE PO RECEIVED] DATE NULL,
    [PO NUMBER] NVARCHAR(255) NULL,
    [CUSTOMER ALT PO] NVARCHAR(255) NULL,
    [AAG SEASON] NVARCHAR(255) NULL,
    [CUSTOMER SEASON] NVARCHAR(100) NULL,
    [DROP] NVARCHAR(255) NULL,
    [MONTH] NVARCHAR(255) NULL,
    [RANGE / COLLECTION] NVARCHAR(255) NULL,
    [PROMO GROUP / CAMPAIGN (HOT 30/GLOBAL EDIT)] NVARCHAR(255) NULL,
    [CATEGORY] NVARCHAR(255) NULL,
    [PATTERN ID] NVARCHAR(255) NULL,
    [PLANNER] NVARCHAR(500) NULL,
    [MAKE OR BUY] NVARCHAR(255) NULL,
    [ORIGINAL ALIAS/RELATED ITEM] NVARCHAR(255) NULL,
    [PRICING ALIAS/RELATED ITEM] NVARCHAR(255) NULL,
    [ALIAS/RELATED ITEM] NVARCHAR(255) NULL,
    [CUSTOMER STYLE] NVARCHAR(100) NULL,
    [STYLE DESCRIPTION] NVARCHAR(100) NULL,
    [CUSTOMER'S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS] NVARCHAR(255) NULL,
    [CUSTOMER COLOUR DESCRIPTION] NVARCHAR(100) NULL,
    [UNIT OF MEASURE] NVARCHAR(100) NULL,
    [COUNTRY OF ORIGIN] NVARCHAR(100) NULL,
    [DESTINATION] NVARCHAR(255) NULL,
    [LONGSON ALIAS] NVARCHAR(255) NULL,
    [VALIDATION] NVARCHAR(50) NULL,

    -- === GARMENT_SIZES (31 columns) ===
    [XS] INT NULL,
    [S] INT NULL,
    [M] INT NULL,
    [L] INT NULL,
    [XL] INT NULL,
    [XXL] INT NULL,
    [2XL] INT NULL,
    [3XL] INT NULL,
    [4XL] INT NULL,
    [5XL] INT NULL,
    [6] INT NULL,
    [8] INT NULL,
    [10] INT NULL,
    [12] INT NULL,
    [14] INT NULL,
    [16] INT NULL,
    [18] INT NULL,
    [20] INT NULL,
    [22] INT NULL,
    [24] INT NULL,
    [0-3M] INT NULL,
    [3-6M] INT NULL,
    [6-12M] INT NULL,
    [12-18M] INT NULL,
    [18-24M] INT NULL,
    [2T] INT NULL,
    [3T] INT NULL,
    [4T] INT NULL,
    [5T] INT NULL,
    [ONE SIZE] INT NULL,
    [PLUS] INT NULL,

    -- === ADDITIONAL_DETAILS (9 columns) ===
    [TOTAL QTY] INT NULL,
    [CUSTOMER PRICE] DECIMAL(18,2) NULL,
    [EX WORKS (USD)] DECIMAL(18,2) NULL,
    [FINAL FOB (USD)] DECIMAL(18,2) NULL,
    [US DUTY] DECIMAL(18,2) NULL,
    [US TARIFF] DECIMAL(18,2) NULL,
    [ETA CUSTOMER WAREHOUSE DATE] DATE NULL,
    [EX FACTORY DATE] DATE NULL,
    [LAST_UPDATED] DATETIME2 NULL
);
GO

-- Add helpful indexes for performance
CREATE NONCLUSTERED INDEX IX_ORDER_LIST_AAG_ORDER_NUMBER
    ON dbo.ORDER_LIST ([AAG ORDER NUMBER]);

CREATE NONCLUSTERED INDEX IX_ORDER_LIST_CUSTOMER_PO
    ON dbo.ORDER_LIST ([CUSTOMER NAME], [PO NUMBER]);

CREATE NONCLUSTERED INDEX IX_ORDER_LIST_ORDER_DATE
    ON dbo.ORDER_LIST ([ORDER DATE PO RECEIVED]);

-- Table creation complete
PRINT 'ORDER_LIST table created successfully';