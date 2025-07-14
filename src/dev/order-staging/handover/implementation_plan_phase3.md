# ORDER STAGING ETL - IMPLEMENTATION PLAN & TRACKING
**Date: June 18, 2025**  
**Purpose:** Methodical implementation plan for Phase 3 Batch Processing Logic  
**Goal:** Create functional ETL pipeline for Kestra orchestration with GREYSON Customer Season fix

---

## 🎯 CURRENT STATUS ASSESSMENT

### ✅ COMPLETED (Phases 1 & 2)
- **Database Schema**: All staging, error, and batch tracking tables exist
- **Infrastructure Files**: All core Python modules exist in `src/order_staging/`
- **Migration**: RANGE/COLLECTION column added successfully  
- **Group Naming Logic**: Business rule implemented (CUSTOMER SEASON → AAG SEASON fallback)
- **End-to-End Test**: Validated complete workflow with GREYSON PO 4755 ✅

### ⏳ PENDING (Phase 3 - Batch Processing Logic)
- **Main Orchestrator**: `batch_processor.py` exists but EMPTY - needs full implementation
- **ETL Integration**: Connect working `staging_operations.py` (543 lines) to full workflow
- **Monday.com API**: `monday_api_client.py` exists but EMPTY - needs full implementation  
- **Configuration**: `staging_config.py` exists but EMPTY - needs implementation
- **Error Handling**: `error_handler.py` exists but EMPTY - needs implementation
- **Entry Point**: Create `order_sync_v2.py` for Kestra execution (doesn't exist)

---

## 📊 CURRENT FILE BASELINE ASSESSMENT

### ✅ WORKING FILES (Ready to Use)
- `src/order_staging/staging_operations.py` - **543 lines, FUNCTIONAL**
  - Group naming logic implemented ✅
  - Database operations working ✅  
  - Customer SEASON → AAG SEASON fallback ✅
  - RANGE/COLLECTION handling ready ✅

### ⚠️ EMPTY FILES (Need Full Implementation)
- `src/order_staging/batch_processor.py` - **EMPTY** (main orchestrator)
- `src/order_staging/monday_api_client.py` - **EMPTY** (API integration) 
- `src/order_staging/error_handler.py` - **EMPTY** (error management)
- `src/order_staging/staging_config.py` - **EMPTY** (configuration)

### ❌ MISSING FILES (Need Creation)
- `src/order_sync_v2.py` - **DOESN'T EXIST** (Kestra entry point)

### 🧪 VALIDATED TEST FILES (Working)
- `dev/order_staging/testing/test_greyson_staging_simple.py` - ✅ PASSED
- `dev/order_staging/validation/test_end_to_end_flow.py` - ✅ PASSED  
- `dev/order_staging/validation/run_migration.py` - ✅ COMPLETED

---

## 📋 DETAILED IMPLEMENTATION PLAN

### PHASE 3: BATCH PROCESSING LOGIC IMPLEMENTATION

#### **Task 3.1: Complete batch_processor.py** 
**Status:** ⏳ PENDING  
**Dependencies:** staging_operations.py (exists), monday_api_client.py (exists)  
**Files to enhance:**
- `src/order_staging/batch_processor.py` (exists but needs implementation)

**Required Functions:**
1. `process_customer_batch(customer_name)` - Main orchestrator
2. `load_new_orders_to_staging(customer_name)` - ETL step 1  
3. `create_monday_items_from_staging(batch_id)` - API step 2
4. `create_monday_subitems_from_staging(batch_id)` - API step 3 (future)
5. `promote_successful_records(batch_id)` - Production promotion step 4
6. `cleanup_staging_for_customer(batch_id)` - Cleanup step 5

#### **Task 3.2: Enhance staging_operations.py**
**Status:** ⏳ PARTIAL (exists with good foundation)  
**Current File:** `src/order_staging/staging_operations.py` (543 lines)  
**Enhancements Needed:**
1. ✅ Group naming logic (already implemented)
2. ⏳ Integration with batch_processor workflow
3. ⏳ RANGE/COLLECTION column handling (preserve NULL as-is)

#### **Task 3.3: Complete monday_api_client.py**
**Status:** ⏳ PENDING  
**Current File:** `src/order_staging/monday_api_client.py` (exists)  
**Required Functions:**
1. `create_item_with_retry(item_data)` - Item creation with retry logic
2. `create_subitem_with_retry(parent_id, subitem_data)` - Subitem creation (future)
3. GraphQL query building and execution
4. Error handling and logging integration

#### **Task 3.4: Create order_sync_v2.py Entry Point**
**Status:** ⏳ PENDING  
**New File:** `src/order_sync_v2.py`  
**Purpose:** Kestra-compatible entry point script  
**Required Functions:**
1. Command-line argument parsing (customer filter, batch options)
2. Orchestration of batch_processor
3. Logging and monitoring setup
4. Success/failure reporting for Kestra

#### **Task 3.5: Enhanced Error Handling**
**Status:** ⏳ PARTIAL (error_handler.py exists)  
**Current File:** `src/order_staging/error_handler.py` (exists)  
**Integration Points:**
1. Monday.com API failures
2. Database operation failures  
3. Batch processing failures
4. Retry mechanisms with exponential backoff

---

## 🧪 TESTING STRATEGY

### **Our Organized Test Files:**
```
dev/order_staging/
├── debugging/     (6 files) - Schema analysis, data exploration
├── testing/       (5 files) - Functional testing scripts  
├── validation/    (4 files) - End-to-end verification
```

### **Test Progression:**
1. **Unit Tests**: Test individual functions (debugging folder)
2. **Integration Tests**: Test component interactions (testing folder)  
3. **End-to-End Tests**: Full workflow validation (validation folder)
4. **GREYSON Validation**: Specific customer test case

### **Key Test Files:**
- `dev/order_staging/testing/test_greyson_staging_simple.py` ✅ PASSED
- `dev/order_staging/validation/test_end_to_end_flow.py` ✅ PASSED  
- `dev/order_staging/validation/run_migration.py` ✅ COMPLETED

---

## 🎯 SUCCESS CRITERIA

### **Immediate Goals (Phase 3):**
1. ✅ GREYSON PO 4755 loads to staging correctly - **VALIDATED**
2. ✅ Group naming shows "GREYSON CLOTHIERS 2025 FALL" - **CORRECTED & TESTED**  
3. ✅ RANGE/COLLECTION preserved as NULL - **VALIDATED**
4. ⏳ Monday.com API creates items successfully
5. ⏳ Staging promotes to production cleanly

### **Business Validation:**
- **Before**: GREYSON orders → Blank/undefined groups in Monday.com
- **After**: GREYSON orders → "GREYSON CLOTHIERS 2025 FALL" groups in Monday.com ✅ **READY**

### **END-TO-END VALIDATION STATUS: ✅ COMPLETE**
**Date Tested:** June 18, 2025  
**Tests Passed:** 
- `dev/order_staging/testing/test_greyson_staging_simple.py` ✅
- `dev/order_staging/validation/test_end_to_end_flow.py` ✅  
**Group Format Corrected:** `CUSTOMER {SEASON}` (no hyphen) ✅

---

## 📝 IMPLEMENTATION SEQUENCE

### **Step 1: Core Orchestrator** (HIGHEST PRIORITY)
**File:** `src/order_staging/batch_processor.py`
**Focus:** Main workflow that connects all pieces
**Key Function:** `process_customer_batch('GREYSON')`

### **Step 2: Monday.com Integration** 
**File:** `src/order_staging/monday_api_client.py`  
**Focus:** API calls with proper error handling
**Key Function:** `create_item_with_retry(item_data)`

### **Step 3: Kestra Entry Point**
**File:** `src/order_sync_v2.py`
**Focus:** Command-line interface for orchestration  
**Key Function:** `main()` with argument parsing

### **Step 4: Testing & Validation**
**Files:** Use organized test files in `dev/order_staging/`
**Focus:** GREYSON PO 4755 end-to-end validation

---

## 🔄 PROGRESS TRACKING

### **Files Being Modified:**
- [ ] `src/order_staging/batch_processor.py` - NEEDS IMPLEMENTATION
- [ ] `src/order_staging/monday_api_client.py` - NEEDS COMPLETION  
- [ ] `src/order_sync_v2.py` - NEEDS CREATION
- [ ] Test files in `dev/order_staging/` - FOR VALIDATION

### **Dependencies Confirmed Working:**
- ✅ `src/order_staging/staging_operations.py` - Group naming logic working
- ✅ Database schema - All tables and columns ready
- ✅ GREYSON source data - Confirmed available and testable
- ✅ Monday.com mapping - RANGE/COLLECTION column ID ready

---

## 🎪 INTEGRATION POINTS

### **Kestra Orchestration:**
- Entry point: `src/order_sync_v2.py`
- Parameters: Customer name, batch options
- Output: Success/failure status, processing summary

### **Monday.com Integration:**
- Column mapping: `docs/mapping/orders_unified_monday_mapping.yaml` ✅
- API authentication: Environment variables or config
- Group creation: Customer + Season combinations

### **Database Flow:**
- Source: `ORDERS_UNIFIED` → Transform → `STG_MON_CustMasterSchedule` → API → `MON_CustMasterSchedule`
- Error handling: Failed records to `ERR_MON_CustMasterSchedule`
- Monitoring: Batch tracking in `MON_BatchProcessing`

---

**READY FOR IMPLEMENTATION APPROVAL** ✅  
**Next Step:** Begin with `batch_processor.py` core orchestrator implementation
