-- View: v_packed_barcode
-- Description: Total packed quantity by SKUBarcode from Distribution and WAH systems (last 60 days), normalized format

SELECT
    UPPER(LTRIM(RTRIM(pd.skuBarcode))) AS SKUBarcode,
    SUM(pd.qty) AS Qty
FROM
    Distribution.dbo.pack p WITH (NOLOCK)
LEFT JOIN
    Distribution.dbo.pack_d pd WITH (NOLOCK) ON pd.cartonid = p.cartonid
WHERE
    p.Pack_Date > GETDATE() - 60
GROUP BY
    UPPER(LTRIM(RTRIM(pd.skuBarcode)))

UNION

SELECT
    UPPER(LTRIM(RTRIM(pd.skuBarcode))) AS SKUBarcode,
    SUM(pd.qty) AS Qty
FROM
    wah.dbo.pack p WITH (NOLOCK)
LEFT JOIN
    wah.dbo.packd pd WITH (NOLOCK) ON pd.cartonid = p.cartonid
WHERE
    p.createtime > GETDATE() - 60
GROUP BY
    UPPER(LTRIM(RTRIM(pd.skuBarcode)));
