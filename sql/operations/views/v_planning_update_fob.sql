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
