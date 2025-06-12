CREATE VIEW v_shipped_non_lorna_jane AS
SELECT
    UPPER(LTRIM(RTRIM(ISNULL(bs.Belongs_Customer, 'Lorna Jane')))) AS Customer,
    s.shipmentid AS CartonID,
    LTRIM(RTRIM(pd.po)) AS Customer_PO,
    UPPER(LTRIM(RTRIM(pd.season))) AS Season,
    s.[Ex-factoryDate] AS Shipped_Date,
    UPPER(LTRIM(RTRIM(pd.style))) AS Style,
    UPPER(LTRIM(RTRIM(pd.styleName))) AS StyleName,
    UPPER(LTRIM(RTRIM(pd.color))) AS Color,
    SUM(pd.qty) AS Qty
FROM shipmentd sd
LEFT JOIN shipment s ON s.shipmentid = sd.shipmentid
LEFT JOIN packD pd ON pd.cartonid = sd.cartonid
LEFT JOIN PriceList pl ON pl.CustomerPO = pd.po AND pl.Style = pd.style AND pl.color = pd.color
LEFT JOIN baseShop bs ON bs.shopID = pd.shopId
WHERE
    year(s.[Ex-factoryDate]) = 2024
    AND pd.exFactoryDate < '2049-01-01'
    AND UPPER(LTRIM(RTRIM(ISNULL(bs.Belongs_Customer, 'Lorna Jane')))) <> 'LORNA JANE'
GROUP BY
    bs.Belongs_Customer, s.shipmentid, pd.po, pd.season, s.[Ex-factoryDate], pd.style, 
    pd.color, pd.styleName
