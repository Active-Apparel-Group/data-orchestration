

-- View: v_shipped_products
-- Description: All shipped cartons (LJ + Non-LJ) with ex-factory date

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
WHERE s.[Ex-factorydate] BETWEEN GETDATE() - 200 AND '2999-12-31';
