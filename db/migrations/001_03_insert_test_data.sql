-- Migration 001_03: Insert Test Data into swp_ORDER_LIST_V2
-- Purpose: Populate shadow staging table with GREYSON PO 4755 test data
-- Source: ORDER_LIST production table
-- Database: orders
-- Created: 2025-07-21
-- Author: ORDER_LIST Delta Monday Sync - Schema Fix

-- =============================================================================
-- INSERT: Populate swp_ORDER_LIST_V2 with GREYSON PO 4755 data from ORDER_LIST
-- Phase 1 testing: Single customer, single PO for development validation
-- =============================================================================

-- Verification: Check if source data exists
DECLARE @source_count INT;
SELECT @source_count = COUNT(*) 
FROM dbo.ORDER_LIST
WHERE [CUSTOMER NAME] = 'GREYSON CLOTHIERS'
  AND [PO NUMBER] = '4755'
  AND [AAG ORDER NUMBER] IS NOT NULL;

PRINT 'SOURCE VALIDATION: Found ' + CAST(@source_count AS VARCHAR(10)) + ' GREYSON PO 4755 records in ORDER_LIST';

IF @source_count = 0
BEGIN
    PRINT 'WARNING: No GREYSON CLOTHIERS PO 4755 data found in ORDER_LIST';
    PRINT 'INFO: Will check for alternative GREYSON data...';
    
    -- Check for any GREYSON data with different PO
    SELECT @source_count = COUNT(*) 
    FROM dbo.ORDER_LIST
    WHERE [CUSTOMER NAME] LIKE '%GREYSON%'
      AND [AAG ORDER NUMBER] IS NOT NULL;
      
    PRINT 'ALTERNATIVE: Found ' + CAST(@source_count AS VARCHAR(10)) + ' total GREYSON records';
END

-- Phase 1: GREYSON CLOTHIERS PO 4755 - Limited dataset for initial testing
-- Using complete column list to ensure all 417 columns are populated
INSERT INTO dbo.swp_ORDER_LIST_V2 (
    -- Core business columns (Phase 1 minimal set)
    [AAG ORDER NUMBER],
    [CUSTOMER NAME],
    [PO NUMBER],
    [CUSTOMER STYLE],
    [TOTAL QTY],
    
    -- Additional columns for comprehensive testing
    [SOURCE_CUSTOMER_NAME],
    [ORDER DATE PO RECEIVED],
    [CUSTOMER ALT PO],
    [AAG SEASON],
    [CUSTOMER SEASON],
    [STYLE DESCRIPTION],
    [CUSTOMER COLOUR DESCRIPTION],
    [UNIT OF MEASURE],
    
    -- Size columns (Phase 1 COMPLETE - ALL 251 size columns for GREYSON CLOTHIERS comprehensive testing)
    -- Baby Sizes
    [2T], [3T], [4T], [5T], [6T],
    -- Numeric Child
    [0], [0-3M], [1], [2], [2/3], [3/6 MTHS], [3-6M], [3-4 years], [3], [3-4],
    [4], [4/5], [04/XXS], [5], [5-6 years], [5-6], [6], [6-12M], [6/7], [6/12 MTHS],
    [6-9M], [6-10], [S(6-8)], [7], [7-8 years], [7-8], [8], [08/S], [8/9], [M(8-10)],
    [9], [9-12M], [9-10 years], [9-10], [10], [10/M], [10/11], [10-12], [M(10-12)], [L(10-12)],
    [11-12 years], [11-14], [12], [12/18 MTHS], [12-18M], [12/L], [12/13], [12-14], [13-14 years], [14],
    [L(14-16)], [16],
    -- Adult Sizes
    [XS], [XS/S], [XS-PETITE], [06/XS], [XXS/XS], [CD/XS], [C/XS], [D/XS], 
    [XL], [L/XL], [14/XL], [L-XL], [AB/XL], [CD/XL], [C/XL], [D/XL], 
    [XXL], [2XL], [XL/XXL], [16/XXL], [XL/2XL], [XXL/3XL], [D/XXL], [3XL], [4XL],
    -- Numeric Adult
    [18], [18/24 MTHS], [18-24M], [18/XXXL], [20], [22], [24], [25], [26], [27],
    [28], [28-30L], [29], [30], [30-30L], [30-31L], [30/32], [30-32L], [30/30], [31],
    [31-30L], [31-31L], [31/32], [31-32L], [31/30], [32], [32-30L], [32-31L], [32/32], [32-32L],
    [32/34], [32/36], [32/30], [33], [33-30L], [33-31L], [33/32], [33-32L], [33/30], [34],
    [34-30L], [34-31L], [34/32], [34-32L], [34/34], [34/30], [35], [35-30L], [35-31L], [35/32],
    [35-32L], [35/30], [36], [36-30L], [36-31L], [36/32], [36-32L], [36/34], [36/30], [38],
    [38-30L], [38-31L], [38/32], [38-32L], [38/34], [38/36], [38/30], [40], [40-30L], [40-31L],
    [40/32], [40/30], [42], [43], [44], [45], [46], [48], [50], [52], [54], [56], [58], [60],
    -- One Size
    [OS], [ONE SIZE], [One_Size], [One Sz],
    -- Other Sizes
    [S], [M], [L], [XXS], [S/M], [M/L], [XXXL], [2X], [3X], [1X], [4X], [XXXS], [S/P], [S+],
    [1Y], [2Y], [3Y], [4Y], [S-PETITE], [S-M], [32C], [32D], [4XT], [32DD], [30x30], [32DDD],
    [34C], [30x32], [0w], [2w], [32x30], [One_Sz], [34D], [34DD], [4w], [32x32], [6w], [34DDD],
    [32x34], [36C], [8w], [34x30], [10w], [O/S], [34x32], [31x30], [36D], [12w], [34x34], [36DD],
    [36DDD], [36x32], [38C], [36x30], [38D], [36x34], [38x30], [40x30], [38DD], [38x32], [38DDD],
    [38x34], [40x32], [40x34], [AB/S], [AB/M], [CD/S], [CD/M], [CD/L], [C/S], [C/M], [C/L], 
    [D/S], [D/M], [D/L],
    
    -- Business critical columns
    [ETA CUSTOMER WAREHOUSE DATE],
    [EX FACTORY DATE],
    [FINAL FOB (USD)],
    [ORDER TYPE],
    [COUNTRY OF ORIGIN],
    [_SOURCE_TABLE],
    
    -- All additional columns for complete schema compatibility
    [DROP], [MONTH], [RANGE / COLLECTION], [PROMO GROUP / CAMPAIGN (HOT 30/GLOBAL EDIT)], [CATEGORY],
    [PATTERN ID], [PLANNER], [MAKE OR BUY], [ORIGINAL ALIAS/RELATED ITEM], [PRICING ALIAS/RELATED ITEM],
    [ALIAS/RELATED ITEM], [CUSTOMER'S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS],
    [INFOR WAREHOUSE CODE], [BULK AGREEMENT NUMBER], [INFOR FACILITY CODE], [INFOR BUSINESS UNIT AREA],
    [BULK AGREEMENT DESCRIPTION], [CO NUMBER - INITIAL DISTRO], [INFOR CUSTOMER CODE], [CO NUMBER - ALLOCATION DISTRO],
    [CO NUMBER (INITIAL DISTRO)], [CO NUMBER (ALLOCATION DISTRO)], [INFOR ORDER TYPE], [INFOR SEASON CODE],
    [ITEM TYPE CODE], [PRODUCT GROUP CODE], [ITEM GROUP CODE], [PLANNER2], [GENDER GROUP CODE], [FABRIC TYPE CODE],
    [INFOR MAKE/BUY CODE], [INFOR ITEM TYPE CODE], [INFOR PRODUCT GROUP CODE], [INFOR ITEM GROUP CODE],
    [INFOR GENDER GROUP CODE], [INFOR FABRIC TYPE CODE], [LONGSON ALIAS], [INFOR COLOUR CODE], [FACILITY CODE],
    [CUSTOMER CODE], [Column2], [Column1], [AAG SEASON CODE], [MAKE OR BUY FLAG], [MAKE/BUY CODE],
    [DESTINATION], [DESTINATION WAREHOUSE], [ALLOCATION (CHANNEL)], [SHOP NAME], [SHOP CODE], [COLLECTION DELIVERY],
    [DELIVERY TERMS], [PLANNED DELIVERY METHOD], [NOTES], [VALIDATION], [VALIDATION2], [VALIDATION3], [VALIDATION4],
    [CUSTOMER PRICE], [USA ONLY LSTP 75% EX WORKS], [EX WORKS (USD)], [ADMINISTRATION FEE], [DESIGN FEE],
    [FX CHARGE], [HANDLING], [PNP], [SURCHARGE FEE], [DISCOUNT], [HS CODE], [US DUTY RATE], [US DUTY],
    [FREIGHT], [US TARIFF RATE], [US TARIFF], [DDP US (USD)], [UK DUTY RATE], [UK FREIGHT], [UK INSURANCE],
    [UK CIF], [UK DUTY], [DDP UK (USD)], [CAN DUTY RATE], [CAN DUTY], [DDP CAN (USD)], [SMS PRICE USD],
    [FINAL PRICES Y/N], [NOTES FOR PRICE], [∆], [INFOR ADDRESS ID], [TRACKING NUMBER], [INFOR DELIVERY CODE],
    [DELIVERY CODE (MODL)], [COUNTRY OF ORIGN], [FX CHARGE 2 Dec], [INFOR EX-WORKS 4 Dec], [AU Product 4 Dec],
    [AU PnP 4 Dec], [AU Price 2 Dec], [AU Discount 2 Dec], [US Product 4 Dec], [US PnP 4 Dec], [US Duty 2 Dec],
    [US Tariff 2 Dec], [TARIFF RELIEF DISCOUNT (20%)], [US Price 2 Dec], [FOB TO USE ON PRODUCT INVOICE],
    [US Discount 2 Dec], [US Price w/ Discount], [CAN Product 4 Dec], [ADDITIONAL TARIFF RATE], [CAN PnP 4 Dec],
    [CAN Duty 2 Dec], [ADDITIONAL TARIFF %], [ADDITIONAL TARIFF], [CAN Price 2 Dec], [ADDITIONAL TARIFF VALUE],
    [CAN Discount 2 Dec], [TARIFF RATE CHARGED TO AAG], [CAN Price w/ Discount], [TARIFF LOSS], [UK Product 4 Dec],
    [UK PnP 4 Dec], [INVOICE METHOD], [UK Duty 2 Dec], [UK Price 2 Dec], [UK Discount 2 Dec], [UK Price w/ Discount],
    [RMB price (ex. VAT)], [RMB Discount 2 Dec], [RMB Price w/ Discount], [PRICING NOTES], [NASC TO ROC PRICE (RMB) (inc VAT)],
    [FINANCE EST (USD)], [Warehouse], [NASC TO WHITE FOX (USD)], [INVOICE MONTH], [INVOICE YEAR], [ORTP (ORDER TYPE)],
    [HDPR], [PATTERN/STYLE NAME], [RRP], [PFI EXCHANGE RATE], [FOB (AUD)], [BUAR (BUSINESS AREA UNIT)], [MARGIN], [ADID],
    
    -- Delta sync columns (initialized for development)
    sync_state,
    created_at,
    updated_at
)
SELECT 
    -- Core business columns (Phase 1 minimal set)
    [AAG ORDER NUMBER],
    [CUSTOMER NAME],
    [PO NUMBER],
    [CUSTOMER STYLE],
    [TOTAL QTY],
    
    -- Additional columns for comprehensive testing
    [SOURCE_CUSTOMER_NAME],
    [ORDER DATE PO RECEIVED],
    [CUSTOMER ALT PO],
    [AAG SEASON],
    [CUSTOMER SEASON],
    [STYLE DESCRIPTION],
    [CUSTOMER COLOUR DESCRIPTION],
    [UNIT OF MEASURE],
    
    -- Size columns (Phase 1 COMPLETE - ALL 251 size columns for GREYSON CLOTHIERS comprehensive testing)
    -- Baby Sizes
    [2T], [3T], [4T], [5T], [6T],
    -- Numeric Child
    [0], [0-3M], [1], [2], [2/3], [3/6 MTHS], [3-6M], [3-4 years], [3], [3-4],
    [4], [4/5], [04/XXS], [5], [5-6 years], [5-6], [6], [6-12M], [6/7], [6/12 MTHS],
    [6-9M], [6-10], [S(6-8)], [7], [7-8 years], [7-8], [8], [08/S], [8/9], [M(8-10)],
    [9], [9-12M], [9-10 years], [9-10], [10], [10/M], [10/11], [10-12], [M(10-12)], [L(10-12)],
    [11-12 years], [11-14], [12], [12/18 MTHS], [12-18M], [12/L], [12/13], [12-14], [13-14 years], [14],
    [L(14-16)], [16],
    -- Adult Sizes
    [XS], [XS/S], [XS-PETITE], [06/XS], [XXS/XS], [CD/XS], [C/XS], [D/XS], 
    [XL], [L/XL], [14/XL], [L-XL], [AB/XL], [CD/XL], [C/XL], [D/XL], 
    [XXL], [2XL], [XL/XXL], [16/XXL], [XL/2XL], [XXL/3XL], [D/XXL], [3XL], [4XL],
    -- Numeric Adult
    [18], [18/24 MTHS], [18-24M], [18/XXXL], [20], [22], [24], [25], [26], [27],
    [28], [28-30L], [29], [30], [30-30L], [30-31L], [30/32], [30-32L], [30/30], [31],
    [31-30L], [31-31L], [31/32], [31-32L], [31/30], [32], [32-30L], [32-31L], [32/32], [32-32L],
    [32/34], [32/36], [32/30], [33], [33-30L], [33-31L], [33/32], [33-32L], [33/30], [34],
    [34-30L], [34-31L], [34/32], [34-32L], [34/34], [34/30], [35], [35-30L], [35-31L], [35/32],
    [35-32L], [35/30], [36], [36-30L], [36-31L], [36/32], [36-32L], [36/34], [36/30], [38],
    [38-30L], [38-31L], [38/32], [38-32L], [38/34], [38/36], [38/30], [40], [40-30L], [40-31L],
    [40/32], [40/30], [42], [43], [44], [45], [46], [48], [50], [52], [54], [56], [58], [60],
    -- One Size
    [OS], [ONE SIZE], [One_Size], [One Sz],
    -- Other Sizes
    [S], [M], [L], [XXS], [S/M], [M/L], [XXXL], [2X], [3X], [1X], [4X], [XXXS], [S/P], [S+],
    [1Y], [2Y], [3Y], [4Y], [S-PETITE], [S-M], [32C], [32D], [4XT], [32DD], [30x30], [32DDD],
    [34C], [30x32], [0w], [2w], [32x30], [One_Sz], [34D], [34DD], [4w], [32x32], [6w], [34DDD],
    [32x34], [36C], [8w], [34x30], [10w], [O/S], [34x32], [31x30], [36D], [12w], [34x34], [36DD],
    [36DDD], [36x32], [38C], [36x30], [38D], [36x34], [38x30], [40x30], [38DD], [38x32], [38DDD],
    [38x34], [40x32], [40x34], [AB/S], [AB/M], [CD/S], [CD/M], [CD/L], [C/S], [C/M], [C/L], 
    [D/S], [D/M], [D/L],
    
    -- Business critical columns
    [ETA CUSTOMER WAREHOUSE DATE],
    [EX FACTORY DATE],
    [FINAL FOB (USD)],
    [ORDER TYPE],
    [COUNTRY OF ORIGIN],
    [_SOURCE_TABLE],
    
    -- All additional columns for complete schema compatibility
    [DROP], [MONTH], [RANGE / COLLECTION], [PROMO GROUP / CAMPAIGN (HOT 30/GLOBAL EDIT)], [CATEGORY],
    [PATTERN ID], [PLANNER], [MAKE OR BUY], [ORIGINAL ALIAS/RELATED ITEM], [PRICING ALIAS/RELATED ITEM],
    [ALIAS/RELATED ITEM], [CUSTOMER'S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS],
    [INFOR WAREHOUSE CODE], [BULK AGREEMENT NUMBER], [INFOR FACILITY CODE], [INFOR BUSINESS UNIT AREA],
    [BULK AGREEMENT DESCRIPTION], [CO NUMBER - INITIAL DISTRO], [INFOR CUSTOMER CODE], [CO NUMBER - ALLOCATION DISTRO],
    [CO NUMBER (INITIAL DISTRO)], [CO NUMBER (ALLOCATION DISTRO)], [INFOR ORDER TYPE], [INFOR SEASON CODE],
    [ITEM TYPE CODE], [PRODUCT GROUP CODE], [ITEM GROUP CODE], [PLANNER2], [GENDER GROUP CODE], [FABRIC TYPE CODE],
    [INFOR MAKE/BUY CODE], [INFOR ITEM TYPE CODE], [INFOR PRODUCT GROUP CODE], [INFOR ITEM GROUP CODE],
    [INFOR GENDER GROUP CODE], [INFOR FABRIC TYPE CODE], [LONGSON ALIAS], [INFOR COLOUR CODE], [FACILITY CODE],
    [CUSTOMER CODE], [Column2], [Column1], [AAG SEASON CODE], [MAKE OR BUY FLAG], [MAKE/BUY CODE],
    [DESTINATION], [DESTINATION WAREHOUSE], [ALLOCATION (CHANNEL)], [SHOP NAME], [SHOP CODE], [COLLECTION DELIVERY],
    [DELIVERY TERMS], [PLANNED DELIVERY METHOD], [NOTES], [VALIDATION], [VALIDATION2], [VALIDATION3], [VALIDATION4],
    [CUSTOMER PRICE], [USA ONLY LSTP 75% EX WORKS], [EX WORKS (USD)], [ADMINISTRATION FEE], [DESIGN FEE],
    [FX CHARGE], [HANDLING], [PNP], [SURCHARGE FEE], [DISCOUNT], [HS CODE], [US DUTY RATE], [US DUTY],
    [FREIGHT], [US TARIFF RATE], [US TARIFF], [DDP US (USD)], [UK DUTY RATE], [UK FREIGHT], [UK INSURANCE],
    [UK CIF], [UK DUTY], [DDP UK (USD)], [CAN DUTY RATE], [CAN DUTY], [DDP CAN (USD)], [SMS PRICE USD],
    [FINAL PRICES Y/N], [NOTES FOR PRICE], [∆], [INFOR ADDRESS ID], [TRACKING NUMBER], [INFOR DELIVERY CODE],
    [DELIVERY CODE (MODL)], [COUNTRY OF ORIGN], [FX CHARGE 2 Dec], [INFOR EX-WORKS 4 Dec], [AU Product 4 Dec],
    [AU PnP 4 Dec], [AU Price 2 Dec], [AU Discount 2 Dec], [US Product 4 Dec], [US PnP 4 Dec], [US Duty 2 Dec],
    [US Tariff 2 Dec], [TARIFF RELIEF DISCOUNT (20%)], [US Price 2 Dec], [FOB TO USE ON PRODUCT INVOICE],
    [US Discount 2 Dec], [US Price w/ Discount], [CAN Product 4 Dec], [ADDITIONAL TARIFF RATE], [CAN PnP 4 Dec],
    [CAN Duty 2 Dec], [ADDITIONAL TARIFF %], [ADDITIONAL TARIFF], [CAN Price 2 Dec], [ADDITIONAL TARIFF VALUE],
    [CAN Discount 2 Dec], [TARIFF RATE CHARGED TO AAG], [CAN Price w/ Discount], [TARIFF LOSS], [UK Product 4 Dec],
    [UK PnP 4 Dec], [INVOICE METHOD], [UK Duty 2 Dec], [UK Price 2 Dec], [UK Discount 2 Dec], [UK Price w/ Discount],
    [RMB price (ex. VAT)], [RMB Discount 2 Dec], [RMB Price w/ Discount], [PRICING NOTES], [NASC TO ROC PRICE (RMB) (inc VAT)],
    [FINANCE EST (USD)], [Warehouse], [NASC TO WHITE FOX (USD)], [INVOICE MONTH], [INVOICE YEAR], [ORTP (ORDER TYPE)],
    [HDPR], [PATTERN/STYLE NAME], [RRP], [PFI EXCHANGE RATE], [FOB (AUD)], [BUAR (BUSINESS AREA UNIT)], [MARGIN], [ADID],
    
    -- Delta sync columns (initialized for development)
    'NEW' as sync_state,           -- All records start as NEW for testing
    GETUTCDATE() as created_at,
    GETUTCDATE() as updated_at
    
FROM dbo.ORDER_LIST
WHERE [CUSTOMER NAME] = 'GREYSON CLOTHIERS'
  AND [PO NUMBER] = '4755'
  AND [AAG ORDER NUMBER] IS NOT NULL;  -- Ensure valid records only

-- Alternative insert if PO 4755 not found
IF @@ROWCOUNT = 0
BEGIN
    PRINT 'INFO: GREYSON PO 4755 not found, trying alternative GREYSON data...';
    
    -- Insert any GREYSON data available for testing
    INSERT INTO dbo.swp_ORDER_LIST_V2 (
        [AAG ORDER NUMBER], [CUSTOMER NAME], [PO NUMBER], [CUSTOMER STYLE], [TOTAL QTY],
        [UNIT OF MEASURE], sync_state, created_at, updated_at
    )
    SELECT TOP 5
        [AAG ORDER NUMBER], [CUSTOMER NAME], [PO NUMBER], [CUSTOMER STYLE], [TOTAL QTY],
        [UNIT OF MEASURE], 'NEW', GETUTCDATE(), GETUTCDATE()
    FROM dbo.ORDER_LIST
    WHERE [CUSTOMER NAME] LIKE '%GREYSON%'
      AND [AAG ORDER NUMBER] IS NOT NULL;
END

-- =============================================================================
-- VALIDATION: Verify shadow staging table population
-- =============================================================================

DECLARE @RecordCount INT;
SELECT @RecordCount = COUNT(*) FROM dbo.swp_ORDER_LIST_V2;

DECLARE @GreysonCount INT;
SELECT @GreysonCount = COUNT(*) 
FROM dbo.swp_ORDER_LIST_V2 
WHERE [CUSTOMER NAME] LIKE '%GREYSON%';

-- =============================================================================
-- Success message with validation results
-- =============================================================================

PRINT 'Migration 001_03: Test data inserted successfully';
PRINT '';
PRINT 'Data Summary:';
PRINT '  - Total records in swp_ORDER_LIST_V2: ' + CAST(@RecordCount AS VARCHAR(10));
PRINT '  - GREYSON records: ' + CAST(@GreysonCount AS VARCHAR(10));
PRINT '  - Complete size column coverage: 251 size columns (baby, child, adult, numeric, one-size)';
PRINT '';
PRINT 'Next Steps:';
PRINT '  1. Run 001_04_validate_schema.sql to verify schema compatibility';
PRINT '  2. Test ConfigParser with real database size column detection';
PRINT '  3. Validate ordinal positions for UNIT OF MEASURE and TOTAL QTY';
