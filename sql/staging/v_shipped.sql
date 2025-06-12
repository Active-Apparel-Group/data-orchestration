SELECT
    UPPER(LTRIM(RTRIM(ISNULL(bs.Belongs_Customer, 'Lorna Jane')))) AS Customer,
    s.shipmentid AS CartonID,
    LTRIM(RTRIM(pd.po)) AS Customer_PO,
    UPPER(LTRIM(RTRIM(pd.season))) AS Season,
    s.[Ex-factoryDate] AS Shipped_Date,
    UPPER(LTRIM(RTRIM(pd.style))) AS Style,
    UPPER(LTRIM(RTRIM(pd.color))) AS Color,
    UPPER(LTRIM(RTRIM(pd.size))) AS Size,
    UPPER(LTRIM(RTRIM(pd.skuBarcode))) AS SKUBarcode,
    pd.IsAir AS Shipping_Method,
    pd.shippingCountry,
    SUM(pd.qty) AS Qty
FROM shipmentd sd
LEFT JOIN shipment s ON s.shipmentid = sd.shipmentid
LEFT JOIN packD pd ON pd.cartonid = sd.cartonid
LEFT JOIN PriceList pl ON pl.CustomerPO = pd.po AND pl.Style = pd.style AND pl.color = pd.color
LEFT JOIN baseShop bs ON bs.shopID = pd.shopId
WHERE
    s.[Ex-factoryDate] BETWEEN '2025-01-01' AND '2049-01-01'
    AND pd.exFactoryDate < '2049-01-01'
GROUP BY
    bs.Belongs_Customer, s.shipmentid, pd.po, pd.season, s.[Ex-factoryDate], pd.style, pd.color, pd.size, pd.skuBarcode, pd.IsAir, pd.shippingCountry

UNION ALL

SELECT
    'LORNA JANE' AS Customer,
    s.shipmentid AS CartonID,
    LTRIM(RTRIM(pd_2.Style)) AS Customer_PO,
    '' AS Season,
    s.[Ex-factoryDate] AS Shipped_Date,
    UPPER(LTRIM(RTRIM(pd_2.Style))) AS Style,
    UPPER(LTRIM(RTRIM(pd_2.Color))) AS Color,
    UPPER(LTRIM(RTRIM(pd_2.Size))) AS Size,
    UPPER(LTRIM(RTRIM(pd_2.skuBarcode))) AS SKUBarcode,
    '' AS Shipping_Method,
    sp.Country AS shippingCountry,
    SUM(pd_2.Qty) AS Qty
FROM Distribution.dbo.Shipment AS s
LEFT JOIN Distribution.dbo.Shipment_d AS sd ON sd.shipmentid = s.shipmentid
LEFT JOIN Distribution.dbo.Pack_D AS pd_2 ON pd_2.CartonID = sd.cartonid
LEFT JOIN Distribution.dbo.Shop AS sp ON sp.ShopID = pd_2.ShopID
WHERE (s.[Ex-factoryDate] > GETDATE() - 62)
GROUP BY s.shipmentid, pd_2.Style, pd_2.Color, pd_2.Size, s.[Ex-factoryDate], pd_2.skuBarcode, sp.Country

UNION ALL

SELECT
    'LORNA JANE' AS Customer,
    se.shipmentid AS CartonID,
    LTRIM(RTRIM(pd_1.Style)) AS Customer_PO,
    '' AS Season,
    se.[Ex-factoryDate] AS Shipped_Date,
    UPPER(LTRIM(RTRIM(pd_1.Style))) AS Style,
    UPPER(LTRIM(RTRIM(pd_1.Color))) AS Color,
    UPPER(LTRIM(RTRIM(pd_1.Size))) AS Size,
    UPPER(LTRIM(RTRIM(pd_1.skuBarcode))) AS SKUBarcode,
    '' AS Shipping_Method,
    sp.Country AS shippingCountry,
    SUM(pd_1.Qty) AS Qty
FROM Distribution.dbo.Shipment_EUR AS se
LEFT JOIN Distribution.dbo.Shipment_EUR_d AS sed ON sed.shipmentid = se.shipmentid
LEFT JOIN Distribution.dbo.Pack_D AS pd_1 ON pd_1.CartonID = sed.cartonid
LEFT JOIN Distribution.dbo.Shop AS sp ON sp.ShopID = pd_1.ShopID
WHERE (se.[Ex-factoryDate] > GETDATE() - 62)
  AND (sp.ShopID NOT IN ('1W/SALE', 'GWS', 'GWS-UK'))
GROUP BY se.shipmentid, pd_1.Style, pd_1.Color, pd_1.Size, se.[Ex-factoryDate], pd_1.skuBarcode, sp.Country



