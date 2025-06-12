# Phase-01 MVP – "run_audit.py" Successful Execution
_Target: produce a reconciled Excel report locally via `python src/jobs/run_audit.py`_

## 🎯 **CORRECTED STATUS: ~90% COMPLETE - BLOCKED BY PERFORMANCE**
**Major Components:** ✅ Config, ✅ ETL, ⚠️ Matching (performance issue), ✅ Reporting, ✅ Orchestrator, ✅ SQL Views  
**Blocking Issue:** YAML configuration loading bottleneck causing 5+ minute hangs  
**Remaining:** Performance fix, unit tests, CI pipeline, execution testing

## 1️⃣  Environment & Skeleton
- [x] Clone repo and run `create_repo.ps1` / `create_repo.bat`.
- [x] Create `.env` (copy from `.env.example`); fill SQL creds & Monday token.
- [x] `python -m venv .venv && .venv\Scripts\activate`
- [x] `pip install -r requirements.lock` *(or `poetry install`)*

## 2️⃣  Config & Secrets
- [x] Complete `src/audit_pipeline/config.py`
  - DB helpers read values from `os.getenv`.
  - `load_customer_map()` loads YAML & validates duplicates.
- [x] Add two sample YAML aliases to `docs/mapping/customer_mapping.yaml`.

## 3️⃣  ETL
- [x] Flesh out `standardize_dataset()` with all edge-case columns.
- [x] Finish `handle_master_order_list()` (wide → long melt).
- [ ] Unit-test ETL functions (`pytest src/tests/test_etl.py`). <!-- NEED: test_etl.py file -->

## 4️⃣  Matching
- [x] Implement `aggregate_quantities()`, `exact_match()`, `fuzzy_match()` in `matching.py`.
- [x] RapidFuzz vectorised scoring ≥ 75 threshold.
- [ ] **🔥 URGENT: Fix YAML Performance Bottleneck**
  - [ ] Add module-level configuration cache to prevent repeated YAML file loading
  - [ ] Implement `get_customer_config_cached()` with fallback to simple logic
  - [ ] Optimize `get_style_value_and_source()` to minimize config lookups
  - [ ] Pre-load customer configurations once per matching session
- [ ] Unit tests for:
  - `weighted_fuzzy_score()` <!-- NEED: test files -->
  - Exact merge returns 100 % for identical keys.
- [ ] **Future Refactor TODO:**
  - [ ] Split into modules (keys.py, rules.py, exact.py, fuzzy.py, analytics.py)
  - [ ] Further vectorize fuzzy matching with approximate nearest neighbor
  - [ ] Add type hints and dataclass for configs
  - [ ] Extract cross-field PO matching into dedicated function

## 5️⃣  Reporting
- [x] Implement `write_excel()`:
  - SUMMARY + ≤ 255 customer tabs.
  - [ ] Conditional formatting GOOD / ACCEPTABLE / POOR. <!-- PARTIAL: need xlsxwriter formatting -->
- [x] Guard file overwrite in `outputs/`. <!-- DONE: os.makedirs(exist_ok=True) -->

## 6️⃣  Orchestrator
- [x] Write `run_audit.py` CLI (already stubbed).
- [x] Add `--sample 5000` flag for quick dev runs. <!-- DONE: argparse added -->

## 7️⃣  Logging & QA
- [x] Replace prints with `logging` (INFO for counts, ERROR for exceptions).
- [ ] Rotate log file `audit.log` (10 MB × 3 backups). <!-- PARTIAL: basic logging setup, need rotation -->

## 8️⃣  CI Smoke
- [ ] Populate `.github/workflows/ci.yml`
  - `ruff src`
  - `pytest -q`
  - `sqlfluff lint sql/`

## ✅  Milestone exit-criteria
### Phase 1a: Performance Fix (URGENT)
1. **Performance**: `python src/jobs/run_audit.py --sample 1000` completes in < 60 seconds
2. **Stability**: No crashes, hangs, or KeyboardInterrupt during matching
3. **Caching**: Customer configs loaded once per session, not per row
4. **Fallback**: Graceful degradation when YAML configs fail

### Phase 1: MVP Completion  
1. `python src/jobs/run_audit.py --sample 1000` finishes without traceback.  
2. `outputs/global_customer_audit_fuzzy_match_by_customer.xlsx` contains:
   - SUMMARY sheet
   - ≥ 1 customer tab
   - Excel opens with no corrupt-file warning.
3. All checklist tasks above ticked in PR.

## 🚨 CRITICAL BLOCKERS TO FIX:
- ~~Missing SQL Views~~ ✅ **FIXED**: `v_packed_products.sql`, `v_shipped.sql` created
- ~~Need CLI args~~ ✅ **FIXED**: `--sample` flag implemented in `run_audit.py`  
- **URGENT: YAML Performance Bottleneck** 🔥 - `get_customer_matching_config()` loads YAML file for every row causing 5+ min hangs
- **Missing test files**: No `test_etl.py`, no unit tests for matching functions
- **CI pipeline**: `.github/workflows/ci.yml` is empty placeholder
- **Need to test actual execution**: Try running `python src/jobs/run_audit.py --sample 100`

## 🔥 **URGENT PERFORMANCE FIX (Phase 1a)**
**Priority: CRITICAL - Blocking MVP completion**

### Root Cause Analysis
- Current `matching.py` calls `get_customer_matching_config()` for every row during key generation
- This function loads & parses YAML file from disk without caching (1000+ I/O operations)
- Performance degraded from ~30 seconds to 5+ minutes with hanging/crashes
- Original working version had no such overhead

### Immediate Actions Required
1. **Add Configuration Caching** (30 mins)
   ```python
   # Module-level cache to prevent repeated YAML loading
   _CUSTOMER_CONFIG_CACHE = {}
   
   def get_customer_config_cached(customer):
       if customer not in _CUSTOMER_CONFIG_CACHE:
           try:
               _CUSTOMER_CONFIG_CACHE[customer] = get_customer_matching_config(customer)
           except Exception:
               _CUSTOMER_CONFIG_CACHE[customer] = DEFAULT_SIMPLE_CONFIG
       return _CUSTOMER_CONFIG_CACHE[customer]
   ```

2. **Simplify Style Resolution** (20 mins)
   - Reduce to simple fallback: `Style → Pattern_ID → ALIAS/RELATED ITEM`
   - Only use complex customer logic for specific edge cases
   - Avoid per-row config lookups

3. **Pre-load Customer Configs** (10 mins)
   - Load all unique customer configs once at start of matching session
   - Group processing by customer to minimize config switches

### Success Criteria
- `python src/jobs/run_audit.py --sample 1000` completes in < 60 seconds
- No hanging or crashes during matching phase
- Results accuracy maintained compared to working baseline

### Rollback Strategy
- Keep simple fallback logic that works without YAML configs
- Graceful degradation if customer-specific configs fail to load
- Error handling with clear logging for debugging

## 📋 **EXECUTION PRIORITY ORDER**
1. **🔥 Phase 1a: URGENT Performance Fix** (1 hour) - Fix YAML caching bottleneck
2. **✅ Phase 1: MVP Validation** (30 mins) - Test end-to-end execution  
3. **🧪 Phase 1b: Testing** (2 hours) - Add unit tests for stability
4. **🚀 Phase 1c: CI Pipeline** (1 hour) - Automate quality checks

**Next Sprint Focus:** Move to Phase 2 (advanced features, Kestra integration, cloud deployment)
