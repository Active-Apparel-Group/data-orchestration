-- View: v_orders_shipped
-- Description: Packed cartons that have been shipped (joined with ex-factory date)

SELECT
    UPPER(LTRIM(RTRIM(t.Customer))) AS Customer,
    LTRIM(RTRIM(t.PO)) AS Customer_PO,
    UPPER(LTRIM(RTRIM(t.Season))) AS Season,
    t.cartonid,
    t.Pack_Date,
    t.Shipping_Method,
    UPPER(LTRIM(RTRIM(t.Style))) AS Style,
    UPPER(LTRIM(RTRIM(t.Color))) AS Color,
    UPPER(LTRIM(RTRIM(t.Size))) AS Size,
    UPPER(LTRIM(RTRIM(t.SKUBarcode))) AS SKUBarcode,
    t1.[Ex-factorydate] AS Shipped_Date,
    SUM(t.qty) AS Qty
FROM (
    -- Packed Cartons (Lorna Jane)
    SELECT
        'LORNA JANE' AS Customer,
        pd.instoreweek AS PO,
        '' AS Season,
        pd.cartonid,
        p.Pack_Date,
        '' AS Shipping_Method,
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

    -- Packed Cartons (Non-Lorna Jane)
    SELECT
        ISNULL(bs.belongs_customer, pd.retailer) AS Customer,
        pd.PO,
        pd.season AS Season,
        pd.cartonid,
        p.createtime AS Pack_Date,
        pd.IsAir AS Shipping_Method,
        pd.style,
        pd.color,
        pd.size,
        pd.skuBarcode AS SKUBarcode,
        SUM(pd.qty) AS qty
    FROM wah.dbo.pack p WITH (NOLOCK)
    LEFT JOIN wah.dbo.packd pd WITH (NOLOCK) ON pd.cartonid = p.cartonid
    LEFT JOIN wah.dbo.baseshop bs WITH (NOLOCK) ON bs.shopid = pd.shopid
    WHERE p.createtime > GETDATE() - 180
    GROUP BY ISNULL(bs.belongs_customer, pd.retailer), pd.PO, pd.season, pd.cartonid, p.createtime, pd.style, pd.color, pd.size, pd.skuBarcode
) t
INNER JOIN (
    -- Shipped Cartons (LJ AU, LJ EUR, Non-LJ)
    SELECT sd.cartonid, s.[Ex-factorydate]
    FROM Distribution.dbo.shipment_d sd WITH (NOLOCK)
    LEFT JOIN Distribution.dbo.shipment s WITH (NOLOCK) ON sd.shipmentID = s.shipmentid
    WHERE s.[Ex-factorydate] BETWEEN GETDATE() - 200 AND GETDATE()

    UNION

    SELECT sd.cartonid, s.[Ex-factorydate]
    FROM Distribution.dbo.shipment_eur_d sd WITH (NOLOCK)
    LEFT JOIN Distribution.dbo.shipment_eur s WITH (NOLOCK) ON sd.shipmentID = s.shipmentid
    WHERE s.[Ex-factorydate] BETWEEN GETDATE() - 200 AND GETDATE()

    UNION

    SELECT sd.cartonid, s.[Ex-factorydate]
    FROM wah.dbo.shipmentd sd WITH (NOLOCK)
    LEFT JOIN wah.dbo.shipment s WITH (NOLOCK) ON sd.shipmentID = s.shipmentid
    WHERE s.[Ex-factorydate] BETWEEN GETDATE() - 200 AND '2999-12-31'
) t1 ON t1.cartonid = t.cartonid
WHERE t.Style IS NOT NULL
GROUP BY
    t.Customer, t.PO, t.Season, t.cartonid, t.Pack_Date, t.Shipping_Method, t.Style, t.Color, t.Size, t.SKUBarcode, t1.[Ex-factorydate];
