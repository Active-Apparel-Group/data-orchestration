-- Table: dbo.xGREYSON_ORDER_LIST_RAW
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[xGREYSON_ORDER_LIST_RAW] (
    [AAG ORDER NUMBER] NVARCHAR(100) NULL,
    [CUSTOMER NAME] NVARCHAR(100) NULL,
    [ORDER DATE PO RECEIVED] NVARCHAR(100) NULL,
    [PO NUMBER] NVARCHAR(100) NULL,
    [CUSTOMER ALT PO] NVARCHAR(100) NULL,
    [AAG SEASON] NVARCHAR(100) NULL,
    [CUSTOMER SEASON] NVARCHAR(100) NULL,
    [DROP] NVARCHAR(100) NULL,
    [MONTH] NVARCHAR(100) NULL,
    [RANGE / COLLECTION] NVARCHAR(100) NULL,
    [PROMO GROUP / CAMPAIGN (HOT 30/GLOBAL EDIT] NVARCHAR(100) NULL,
    [CATEGORY] NVARCHAR(100) NULL,
    [PATTERN ID] NVARCHAR(100) NULL,
    [PLANNER] NVARCHAR(100) NULL,
    [MAKE OR BUY] NVARCHAR(100) NULL,
    [ITEM TYPE CODE] NVARCHAR(100) NULL,
    [PRODUCT GROUP CODE] NVARCHAR(100) NULL,
    [ITEM GROUP CODE] NVARCHAR(100) NULL,
    [GENDER GROUP CODE] NVARCHAR(100) NULL,
    [FABRIC TYPE CODE] NVARCHAR(100) NULL,
    [ORIGINAL ALIAS/RELATED ITEM] NVARCHAR(100) NULL,
    [PRICING ALIAS/RELATED ITEM] NVARCHAR(100) NULL,
    [ALIAS/RELATED ITEM] NVARCHAR(100) NULL,
    [CUSTOMER STYLE] NVARCHAR(100) NULL,
    [STYLE DESCRIPTION] NVARCHAR(100) NULL,
    [CUSTOMER'S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS] NVARCHAR(100) NULL,
    [CUSTOMER COLOUR DESCRIPTION] NVARCHAR(100) NULL,
    [UNIT OF MEASURE] NVARCHAR(100) NULL,
    [XS] NVARCHAR(100) NULL,
    [S] NVARCHAR(100) NULL,
    [M] NVARCHAR(100) NULL,
    [L] NVARCHAR(100) NULL,
    [XL] NVARCHAR(100) NULL,
    [2XL] NVARCHAR(100) NULL,
    [3XL] NVARCHAR(100) NULL,
    [4XL] NVARCHAR(100) NULL,
    [S/M] NVARCHAR(100) NULL,
    [L/XL] NVARCHAR(100) NULL,
    [0w] NVARCHAR(100) NULL,
    [2w] NVARCHAR(100) NULL,
    [4w] NVARCHAR(100) NULL,
    [6w] NVARCHAR(100) NULL,
    [8w] NVARCHAR(100) NULL,
    [10w] NVARCHAR(100) NULL,
    [12w] NVARCHAR(100) NULL,
    [28] NVARCHAR(100) NULL,
    [30] NVARCHAR(100) NULL,
    [31] NVARCHAR(100) NULL,
    [32] NVARCHAR(100) NULL,
    [33] NVARCHAR(100) NULL,
    [34] NVARCHAR(100) NULL,
    [35] NVARCHAR(100) NULL,
    [36] NVARCHAR(100) NULL,
    [38] NVARCHAR(100) NULL,
    [40] NVARCHAR(100) NULL,
    [42] NVARCHAR(100) NULL,
    [44] NVARCHAR(100) NULL,
    [46] NVARCHAR(100) NULL,
    [48] NVARCHAR(100) NULL,
    [30/32] NVARCHAR(100) NULL,
    [31/32] NVARCHAR(100) NULL,
    [32/32] NVARCHAR(100) NULL,
    [33/32] NVARCHAR(100) NULL,
    [34/32] NVARCHAR(100) NULL,
    [35/32] NVARCHAR(100) NULL,
    [36/32] NVARCHAR(100) NULL,
    [38/32] NVARCHAR(100) NULL,
    [40/32] NVARCHAR(100) NULL,
    [32/34] NVARCHAR(100) NULL,
    [34/34] NVARCHAR(100) NULL,
    [36/34] NVARCHAR(100) NULL,
    [32/36] NVARCHAR(100) NULL,
    [38/34] NVARCHAR(100) NULL,
    [38/36] NVARCHAR(100) NULL,
    [4] NVARCHAR(100) NULL,
    [5] NVARCHAR(100) NULL,
    [6] NVARCHAR(100) NULL,
    [7] NVARCHAR(100) NULL,
    [8] NVARCHAR(100) NULL,
    [9] NVARCHAR(100) NULL,
    [10] NVARCHAR(100) NULL,
    [12] NVARCHAR(100) NULL,
    [30/30] NVARCHAR(100) NULL,
    [31/30] NVARCHAR(100) NULL,
    [32/30] NVARCHAR(100) NULL,
    [33/30] NVARCHAR(100) NULL,
    [34/30] NVARCHAR(100) NULL,
    [35/30] NVARCHAR(100) NULL,
    [36/30] NVARCHAR(100) NULL,
    [38/30] NVARCHAR(100) NULL,
    [40/30] NVARCHAR(100) NULL,
    [ONE SIZE] NVARCHAR(100) NULL,
    [TOTAL QTY] NVARCHAR(100) NULL,
    [DESTINATION] NVARCHAR(100) NULL,
    [DESTINATION WAREHOUSE] NVARCHAR(100) NULL,
    [ALLOCATION (CHANNEL)] NVARCHAR(100) NULL,
    [TRACKING NUMBER] NVARCHAR(100) NULL,
    [SHOP NAME] NVARCHAR(100) NULL,
    [SHOP CODE] NVARCHAR(100) NULL,
    [COLLECTION DELIVERY] NVARCHAR(100) NULL,
    [ETA CUSTOMER WAREHOUSE DATE] NVARCHAR(100) NULL,
    [EX FACTORY DATE] NVARCHAR(100) NULL,
    [DELIVERY TERMS] NVARCHAR(100) NULL,
    [PLANNED DELIVERY METHOD] NVARCHAR(100) NULL,
    [COUNTRY OF ORIGN] NVARCHAR(100) NULL,
    [NOTES] NVARCHAR(500) NULL,
    [ORDER TYPE] NVARCHAR(100) NULL,
    [VALIDATION] NVARCHAR(100) NULL,
    [VALIDATION2] NVARCHAR(100) NULL,
    [VALIDATION3] NVARCHAR(100) NULL,
    [VALIDATION4] NVARCHAR(100) NULL,
    [CUSTOMER PRICE] NVARCHAR(100) NULL,
    [USA ONLY LSTP 75% EX WORKS] NVARCHAR(100) NULL,
    [EX WORKS (USD)] NVARCHAR(100) NULL,
    [ADMINISTRATION FEE] NVARCHAR(100) NULL,
    [DESIGN FEE] NVARCHAR(100) NULL,
    [FX CHARGE] NVARCHAR(100) NULL,
    [HANDLING] NVARCHAR(100) NULL,
    [PNP] NVARCHAR(100) NULL,
    [SURCHARGE FEE] NVARCHAR(100) NULL,
    [DISCOUNT] NVARCHAR(100) NULL,
    [FINAL FOB (USD)] NVARCHAR(100) NULL,
    [HS CODE] NVARCHAR(100) NULL,
    [US DUTY RATE] NVARCHAR(100) NULL,
    [US DUTY] NVARCHAR(100) NULL,
    [FREIGHT] NVARCHAR(100) NULL,
    [US TARIFF RATE] NVARCHAR(100) NULL,
    [US TARIFF] NVARCHAR(100) NULL,
    [DDP US (USD)] NVARCHAR(100) NULL,
    [UK DUTY RATE] NVARCHAR(100) NULL,
    [UK FREIGHT] NVARCHAR(100) NULL,
    [UK INSURANCE] NVARCHAR(100) NULL,
    [UK CIF] NVARCHAR(100) NULL,
    [UK DUTY] NVARCHAR(100) NULL,
    [DDP UK (USD)] NVARCHAR(100) NULL,
    [CAN DUTY RATE] NVARCHAR(100) NULL,
    [CAN DUTY] NVARCHAR(100) NULL,
    [DDP CAN (USD)] NVARCHAR(100) NULL,
    [SMS PRICE USD] NVARCHAR(100) NULL,
    [FINAL PRICES Y/N] NVARCHAR(100) NULL,
    [NOTES FOR PRICE] NVARCHAR(255) NULL,
    [∆] NVARCHAR(100) NULL,
    [_SOURCE_FILE] NVARCHAR(100) NULL,
    [_EXTRACTED_AT] DATETIME2 NULL
);
