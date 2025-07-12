# Phase 1 Quick Start Guide
**Get GREYSON PO 4755 Subitems Working in 3 Hours**

---

## 🚀 Quick Start (TL;DR)

**Problem:** Subitems not created - 0 records in staging table  
**Root Cause:** Triple change detection blocking NEW orders  
**Solution:** Simplify to direct comparison, fix batch sequence  
**Target:** 264 subitems in Monday.com board 4755559751  

---

## ⚡ 3-Hour Implementation

### Hour 1: Code Simplification
```powershell
# 1. Backup current state
git checkout -b phase_1_fix

# 2. Edit CustomerBatchProcessor
code dev/customer-orders/customer_batch_processor.py
```

**Replace `get_customer_changes()` method with:**
```python
def get_customer_changes(self, customer_name: str, limit: Optional[int] = None, po_number_filter: Optional[str] = None) -> pd.DataFrame:
    """Direct query for NEW orders - Phase 1 fix"""
    
    query = f"""
    SELECT TOP {limit or 10000} *
    FROM [dbo].[ORDERS_UNIFIED] ou
    LEFT JOIN [dbo].[MON_CustMasterSchedule] mc
        ON ou.[AAG ORDER NUMBER] = mc.[AAG ORDER NUMBER]
    WHERE ou.[CUSTOMER NAME] LIKE ?
        AND ou.[PO NUMBER] = ?
        AND mc.[AAG ORDER NUMBER] IS NULL  -- NEW orders only
    ORDER BY ou.[ORDER DATE PO RECEIVED] DESC
    """
    
    with db.get_connection('orders') as conn:
        return pd.read_sql(query, conn, params=[f'%{customer_name}%', po_number_filter])
```

### Hour 2: Test & Validate
```powershell
# 1. Run direct test
python main_customer_orders.py --customer GREYSON --po-number 4755 --mode TEST --limit 5

# 2. Check staging table
# Expected: >0 records in STG_MON_CustMasterSchedule_Subitems
```

**SQL to check results:**
```sql
SELECT COUNT(*) as subitem_count 
FROM STG_MON_CustMasterSchedule_Subitems 
WHERE stg_batch_id = 'latest_batch_id'
```

### Hour 3: Full Production Test
```powershell
# 1. Full end-to-end test
python tests/end_to_end/test_greyson_po_4755_complete_workflow.py

# 2. Expected results:
# - 69 source records found
# - 264 subitems in staging
# - 264 subitems in Monday.com
```

---

## 🎯 Success Checkpoints

### ✅ Checkpoint 1: Code Changed (30 min)
- [ ] CustomerBatchProcessor simplified
- [ ] Direct SQL comparison implemented
- [ ] No more SNAPSHOT table dependency

### ✅ Checkpoint 2: Staging Works (1 hour)
- [ ] STG_MON_CustMasterSchedule_Subitems has records
- [ ] Size melting creates correct count
- [ ] UUID relationships maintained

### ✅ Checkpoint 3: API Works (2 hours)
- [ ] Monday.com API calls successful
- [ ] Subitems visible in board interface
- [ ] Correct field values (Size, Order Qty)

### ✅ Checkpoint 4: Production Ready (3 hours)
- [ ] End-to-end test passes
- [ ] All 264 subitems created
- [ ] Performance acceptable

---

## 🔧 Troubleshooting

### Issue: Still 0 subitems in staging
**Cause:** Batch completion logic still wrong  
**Fix:** Check `_process_subitems()` is actually called

### Issue: API calls fail
**Cause:** Rate limiting or authentication  
**Fix:** Check Monday.com token in config.yaml

### Issue: Wrong subitem count
**Cause:** Size melting logic issue  
**Fix:** Verify 162 size columns detected

---

## 📊 Expected Results

**Before Fix:**
```
Subitems completed: None
STG_MON_CustMasterSchedule_Subitems: 0 records
Monday.com board: No subitems
```

**After Fix:**
```
Subitems completed: 264
STG_MON_CustMasterSchedule_Subitems: 264 records
Monday.com board: 264 subitems with size data
```

---

## 🎉 Success!

Once working, you'll see:
- ✅ Staging table populated with 264 subitem records
- ✅ Monday.com board 4755559751 shows subitems
- ✅ End-to-end test passes all phases
- ✅ Production ready for NEW orders

**Next:** Plan Phase 2 for MODIFIED/DELETED orders

---

**Quick Reference:**
- **Board:** 4755559751 (Customer Master Schedule)
- **Test Data:** GREYSON PO 4755 (69 orders → 264 subitems)
- **Key Files:** CustomerBatchProcessor, StagingProcessor
- **Success Metric:** 264 subitems created successfully
