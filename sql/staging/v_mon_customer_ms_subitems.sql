
SELECT 
    ms.[CUSTOMER],
    ms.[Style],
    ms.[COLOR],
    ms.[PO NUMBER],
    si.[parent_item_id],
    si.[subitem_id],
    si.[subitem_board_id],
    si.[Size],
    si.[Order Qty],
    si.[Cut Qty],
    si.[Sew Qty],
    si.[Finishing Qty],
    si.[Received not Shipped Qty],
    si.[Packed Qty],
    si.[Shipped Qty],
    si.[ORDER LINE STATUS],
    ms.[Item ID]
FROM dbo.MON_CustMasterSchedule_Subitems si
JOIN dbo.MON_CustMasterSchedule ms
    ON ms.[Item ID] = si.[parent_item_id]
where CUSTOMER = 'UNE PIECE' and ms.[PO NUMBER] = 'F1SS2501'