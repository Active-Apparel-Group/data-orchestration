WITH AccountManagerCTE AS (
    SELECT *
    FROM (VALUES
        ('Jennifer Nyberg', '50432816', 'AESCAPE'),
        ('Viviana Garcia', '60873682', 'AIME LEON DORE'),
        ('Etienne Ong', '56977858', 'ASRV'),
        ('Nicole Guerboian', '65324767', 'BAD BIRDIE'),
        ('Viviana Garcia', '60873682', 'BANDIT'),
        ('Nicole Guerboian', '65324767', 'BORN PRIMITIVE'),
        ('Viviana Garcia', '60873682', 'FEETURES'),
        ('Natalie James', '72091244', 'GREYSON'),
        ('Etienne Ong', '56977858', 'JOHNNIE O'),
        ('Viviana Garcia', '60873682', 'LAMBS'),
        ('Natalie James', '65324767', 'MACK WELDON'),
        ('Jennifer Nyberg', '50432816', 'PELOTON'),
        ('Etienne Ong', '56977858', 'RHONE'),
        ('Viviana Garcia', '60873682', 'SOULCYCLE'),
        ('Nicole Guerboian', '65324767', 'SPIRITUAL GANGSTER'),
        ('Jennifer Nyberg', '50432816', 'SUN DAY RED'),
        ('Jennifer Nyberg', '50432816', 'TAYLORMADE'),
        ('Nicole Guerboian', '65324767', 'TITLE NINE'),
        ('Viviana Garcia', '60873682', 'TRACKSMITH')
    ) AS cte (AccountManager, AMID, Customer)
)

SELECT
    p.[Item ID] AS monday_item_id,
    cte.AMID as [Account Manager]
FROM MON_COO_Planning p
JOIN AccountManagerCTE cte ON p.CUSTOMER = cte.Customer
