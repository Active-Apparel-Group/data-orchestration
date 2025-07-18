-- View: v_packed_products
-- Description: Packed units from Distribution and WAH, excluding anything already shipped

SELECT
    UPPER(LTRIM(RTRIM(t.Customer))) AS Customer,
    LTRIM(RTRIM(t.PO)) AS Customer_PO,
    UPPER(LTRIM(RTRIM(t.Season))) AS Season,
    t.cartonid,
    t.Pack_Date,
    t.Shipping_Method,
    t.shippingCountry,
    UPPER(LTRIM(RTRIM(t.Style))) AS Style,
    UPPER(LTRIM(RTRIM(t.Color))) AS Color,
    UPPER(LTRIM(RTRIM(t.Size))) AS Size,
    UPPER(LTRIM(RTRIM(t.SKUBarcode))) AS SKUBarcode,
    CASE
        WHEN DATEDIFF(DAY, t.Pack_Date, GETDATE()) < 30 THEN '< 1 month'
        WHEN DATEDIFF(DAY, t.Pack_Date, GETDATE()) < 60 THEN '1–2 months'
        WHEN DATEDIFF(DAY, t.Pack_Date, GETDATE()) < 90 THEN '2–3 months'
        WHEN DATEDIFF(DAY, t.Pack_Date, GETDATE()) < 180 THEN '3–6 months'
        ELSE '6–12 months'
    END AS Stock_Age,
    SUM(t.qty) AS Qty
FROM (
    -- Lorna Jane packed
    SELECT
        'LORNA JANE' AS Customer,
        pd.instoreweek AS PO,
        '' AS Season,
        pd.cartonid,
        p.Pack_Date,
        '' as Shipping_Method,
        '' as shippingCountry,
        pd.style,
        pd.color,
        pd.size,
        pd.skuBarcode AS SKUBarcode,
        SUM(pd.qty) AS qty
    FROM Distribution.dbo.pack p WITH (NOLOCK)
    LEFT JOIN Distribution.dbo.pack_d pd WITH (NOLOCK) ON pd.cartonid = p.cartonid
    WHERE p.Pack_Date > GETDATE() - 180
    GROUP BY pd.instoreweek, pd.cartonid, p.Pack_Date, pd.style, pd.color, pd.size, pd.skuBarcode

    UNION

    -- Non-LJ packed
    SELECT
        ISNULL(bs.belongs_customer, pd.retailer) AS Customer,
        pd.PO,
        pd.season AS Season,
        pd.cartonid,
        p.createtime AS Pack_Date,
        pd.IsAir AS Shipping_Method,
        pd.shippingCountry,
        pd.style,
        pd.color,
        pd.size,
        pd.skuBarcode AS SKUBarcode,
        SUM(pd.qty) AS qty
    FROM wah.dbo.pack p WITH (NOLOCK)
    LEFT JOIN wah.dbo.packd pd WITH (NOLOCK) ON pd.cartonid = p.cartonid
    LEFT JOIN wah.dbo.baseshop bs WITH (NOLOCK) ON bs.shopid = pd.shopid
    WHERE p.createtime > GETDATE() - 180
    GROUP BY ISNULL(bs.belongs_customer, pd.retailer), pd.PO, pd.season, pd.cartonid, p.createtime, pd.style, 
    pd.color, pd.size, pd.skuBarcode, pd.IsAir, pd.shippingCountry
) t
LEFT JOIN (
    -- Shipped cartons
    SELECT sd.cartonid
    FROM Distribution.dbo.shipment_d sd WITH (NOLOCK)
    LEFT JOIN Distribution.dbo.shipment s WITH (NOLOCK) ON sd.shipmentID = s.shipmentid
    WHERE s.[Ex-factorydate] BETWEEN GETDATE() - 200 AND GETDATE()

    UNION

    SELECT sd.cartonid
    FROM Distribution.dbo.shipment_eur_d sd WITH (NOLOCK)
    LEFT JOIN Distribution.dbo.shipment_eur s WITH (NOLOCK) ON sd.shipmentID = s.shipmentid
    WHERE s.[Ex-factorydate] BETWEEN GETDATE() - 200 AND GETDATE()

    UNION

    SELECT sd.cartonid
    FROM wah.dbo.shipmentd sd WITH (NOLOCK)
    LEFT JOIN wah.dbo.shipment s WITH (NOLOCK) ON sd.shipmentID = s.shipmentid
    WHERE s.[Ex-factorydate] BETWEEN GETDATE() - 200 AND '2999-12-31'
) t1 ON t1.cartonid = t.cartonid
WHERE
    t1.cartonid IS NULL
    AND t.Style IS NOT NULL
GROUP BY
    t.Customer, t.PO, t.Season, t.cartonid, t.Pack_Date, t.Style, t.Color, t.Size, t.SKUBarcode, t.Shipping_Method, t.shippingCountry;
