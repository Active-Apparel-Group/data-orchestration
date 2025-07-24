

Select count(*)
 FROM [dbo].[xLORNA_JANE_ORDER_LIST_RAW]
            WHERE [AAG ORDER NUMBER] IS NOT NULL 
            AND LTRIM(RTRIM([AAG ORDER NUMBER])) != ''
            -- ENHANCED DATA INTEGRITY: Comprehensive phantom record detection
            -- Delete records where AAG ORDER NUMBER exists but ALL other critical columns are NULL
            AND NOT (
                [AAG ORDER NUMBER] IS NOT NULL 
                AND [CUSTOMER STYLE] IS NULL 
                AND [PO NUMBER] IS NULL 
                AND [ORDER DATE PO RECEIVED] IS NULL
                AND [TOTAL QTY] IS NULL
            )
            -- Additional data quality filter: exclude obviously invalid records
            AND NOT (
                [AAG ORDER NUMBER] IS NOT NULL
                AND ([TOTAL QTY] IS NULL OR [TOTAL QTY] = 0)
                AND [CUSTOMER NAME] IS NULL
            )


-- compare schema ORDER_LIST with ORDERS_UNIFIED --
-- list of columns in ORDERS_UNIFIED not in ORDER_LIST --
SELECT COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'vwMasterOrderList'
AND COLUMN_NAME NOT IN (
    SELECT COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'vORDERS_UNIFIED'
);

Select top 100 * from ORDERS_UNIFIED
[PROMO GROUP / CAMPAIGN (HOT 30/GLOBAL EDIT], 
[CUSTOMER''S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS],
[ACTIVE],
[All],
[Multiple Items],
[Sum of TOTAL QTY],
[Delta],
[record_uuid]
from ORDERS_UNIFIED
where [PROMO GROUP / CAMPAIGN (HOT 30/GLOBAL EDIT] is not null


Select [CUSTOMER NAME], count(*) 
from vORDERS_UNIFIED 
where [31x30] is not null
group by [CUSTOMER NAME]




CREATE or ALTER VIEW vORDERS_UNIFIED as 
Select *,
       [PROMO GROUP / CAMPAIGN (HOT 30/GLOBAL EDIT)] as "PROMO GROUP / CAMPAIGN (HOT 30/GLOBAL EDIT",
       [CUSTOMER'S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS] as "CUSTOMER''S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS",
       null as "ACTIVE",
       null as "All",
       null as "Multiple Items",
       [TOTAL QTY] as "Sum of TOTAL QTY",
       [∆] as "Delta"
from ORDER_LIST;


Select [EX FACTORY DATE], * from ORDER_LIST where [AAG ORDER NUMBER] >= 'SPI-00707' and [AAG ORDER NUMBER] < 'SPI-00799'


WITH
-- 1) Pull in the ORDERS_UNIFIED values we care about
ou AS (
    SELECT
        [AAG ORDER NUMBER],
        [CUSTOMER STYLE],
        [ORDER DATE PO RECEIVED],
        TRY_CAST([EX FACTORY DATE] as DATE) AS [EX FACTORY DATE],
        CAST([FINAL FOB (USD)]       AS DECIMAL(18,2)) AS new_fob,
        TRY_CAST([ETA CUSTOMER WAREHOUSE DATE] AS DATE) AS new_eta
    FROM ORDER_LIST
    where CAST([FINAL FOB (USD)] AS DECIMAL(18,2)) > 0 or 
            [ETA CUSTOMER WAREHOUSE DATE] IS NOT NULL or
            [EX FACTORY DATE] IS NOT NULL
),

-- 2) Join MON_COO_Planning to ORDERS_UNIFIED, but only non-FORE orders
candidates AS (
    SELECT
        mon.[Item ID],
        mon.[AAG ORDER NUMBER],
        ou.[ORDER DATE PO RECEIVED],
        mon.[EX-FTY DATE (Original)] as old_efd,
        ou.[EX FACTORY DATE] as new_efd,
        mon.[Order Type],
        mon.[Customer FOB (USD)]            AS old_fob,
        ou.new_fob,
        mon.[ETA CUSTOMER WAREHOUSE DATE]   AS old_eta,
        ou.new_eta
    FROM MON_COO_Planning mon
    JOIN ou
      ON ou.[AAG ORDER NUMBER] = mon.[AAG ORDER NUMBER]
     AND ou.[CUSTOMER STYLE]    = mon.[STYLE CODE]
    WHERE LEFT(mon.[Order Type],4) <> 'FORE'
    AND [ORDER TYPE] <> 'CANCELLED'
) 

-- 3) Final select = only those rows where FOB or ETA differs
SELECT
    c.[Item ID] as monday_item_id,
    c.[AAG ORDER NUMBER],
    c.[ORDER DATE PO RECEIVED],

    -- Project the new values
    c.new_fob            AS [Customer FOB (USD)],
    c.new_eta            AS [ETA CUSTOMER WAREHOUSE DATE],
    c.new_efd            AS [EX-FTY DATE (Original)],

    -- For auditing you can still include the olds
    c.old_fob,
    c.old_eta,
    c.old_efd

FROM candidates c
WHERE (c.new_fob != c.old_fob and c.new_fob > 0)
    OR (c.new_eta != c.old_eta and c.new_eta IS NOT NULL)
    OR (c.new_eta != c.old_eta and year(c.new_eta) >= 2025)
    OR (c.old_efd is null and year(c.new_efd) >= 2025)


Select top 100 * from ORDER_LIST
Select top 100 * from [dbo].[xGREYSON_ORDER_LIST_RAW]

    SELECT 
    [Item ID] as monday_item_id,
    CASE 
        WHEN Factory = 'TBC' THEN 'TBC - COO'
        ELSE Factory 
    END AS Factory,
    [Factory (linked)] as 'linkRef',
    [Factory] AS [Factory (linked)]
FROM MON_COO_Planning
where [Factory (linked)] is null
order by [Item ID] asc