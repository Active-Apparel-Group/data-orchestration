# Task List: ORDER_LIST Delta Sync Pipeline (Template-Driven V2)

Generated from: [`sync-order-list-monday.md`](../docs/changelogs/sync-order-list-monday.md)  
Date: 2025-07-21  
Focus: Modern Jinja2 template-driven architecture with 100% TOML configuration
**Status**: Task 5.0 COMPLETED - Template-driven architecture fully validated with production-ready pipeline

## Definition of Done

- All code implementation tasks have a corresponding test/validation sub-task (integration testing is the default, unit tests by exception - but acceptable, the agent or developer should make this call and flag for review, e2e for end-to-end flows).
- No implementation task is marked complete until the relevant test(s) pass and explicit success criteria (acceptance criteria) are met.
- Business or user outcomes are validated with production-like data from `swp_ORDER_LIST_V2` whenever feasible.
- Every task and sub-task is cross-linked to the corresponding file and test for traceability.
- All tests must pass in CI/CD prior to merging to main.
- **All business-critical paths must be covered by integration tests.**

## Architecture Overview

**MODERN APPROACH**: Jinja2 templates + SQLTemplateEngine + TOML-driven size detection
- ✅ **No hardcoded sizes** - All size columns detected via ordinal position from TOML
- ✅ **Template validation** - SQL generated and validated before execution  
- ✅ **Sub-sub task testing** - Individual template → render → test → validate → truncate → next
- ✅ **Modern Python patterns** - Template engines, context rendering, validation frameworks

## Relevant Files

### ✅ COMPLETED - Template Architecture
- ✅ `sql/templates/merge_headers.j2` - Jinja2 template for headers merge with dynamic size columns
- ✅ `sql/templates/unpivot_sizes.j2` - Template for UNPIVOT with TOML-driven size detection  
- ✅ `sql/templates/merge_lines.j2` - Template for lines merge with delta tracking
- ✅ `src/pipelines/sync_order_list/sql_template_engine.py` - Modern Jinja2 rendering engine with TOML integration
- ✅ `src/pipelines/sync_order_list/merge_orchestrator.py` - Updated to use template engine (template validation + execution)

### 🔧 EXISTING - Configuration & Integration  
- `src/pipelines/sync_order_list/config_parser.py` - TOML configuration parser (needs real database integration)
- `src/pipelines/sync_order_list/monday_sync.py` - Two-pass Monday.com sync engine (already exists) 
- `src/pipelines/sync_order_list/cli.py` - Command line interface for complete pipeline (already exists)
- `configs/pipelines/sync_order_list.toml` - Single configuration file with environment, test_data, monday.development sections

### 🗄️ DATABASE REFERENCE FILES
- `db/ddl/tables/orders/dbo_order_list.sql` - Complete ORDER_LIST schema with 417 columns (251 size columns)
- `sql/staging/check_existing_tables.sql` - Validation queries for swp_ORDER_LIST_V2 table existence  
- `sql/staging/check_pipeline_status.sql` - Pipeline status validation queries

### 📋 TEST FILES (New Structure)
- `tests/sync-order-list-monday/integration/test_merge_headers.py` - Integration test for headers merge template
- `tests/sync-order-list-monday/integration/test_unpivot_sizes.py` - Integration test for size unpivot template
- `tests/sync-order-list-monday/integration/test_merge_lines.py` - Integration test for lines merge template
- `tests/sync-order-list-monday/integration/test_new_order_detection.py` - Integration test for NEW order detection
- `tests/sync-order-list-monday/integration/test_config_parser_real.py` - Integration test for real ConfigParser with database
- `tests/sync-order-list-monday/e2e/test_complete_pipeline.py` - End-to-end pipeline test with GREYSON PO 4755
- `tests/sync-order-list-monday/unit/test_template_validation.py` - Unit test for template validation logic (exception case)
- `tests/sync-order-list-monday/debug/test_sql_output_review.py` - Debug test for SQL output validation

### 📝 DEPRECATED - Static SQL Files (replaced by templates)
- ~~`sql/operations/003_merge_headers.sql`~~ → `sql/templates/merge_headers.j2` 
- ~~`sql/operations/004_unpivot_sizes.sql`~~ → `sql/templates/unpivot_sizes.j2`
- ~~`sql/operations/005_merge_lines.sql`~~ → `sql/templates/merge_lines.j2`

### Notes

- **Template-First Approach**: All SQL generated from Jinja2 templates with TOML context
- **Dynamic Size Detection**: Real size columns from swp_ORDER_LIST_V2: `[2T], [3T], [4T], [0], [2], [4], [5], [6], [7], [8], [XS], [S], [M], [L], [XL]` etc. (251 total size columns)
- **Validation Pipeline**: Template → Context → Render → Validate → Execute
- Database: swp_ORDER_LIST_V2 (source) → ORDER_LIST_V2 (target) → ORDER_LIST_LINES → Delta tables
- Test with GREYSON CLOTHIERS PO 4755 data from swp_ORDER_LIST_V2 table
- **Integration tests are the default**; unit tests only for complex/critical logic that benefits from isolation
- All test and implementation files must be cross-referenced in task list for traceability

## Test Coverage Mapping

| Implementation Task                | Test File                                             | Test Type     | Outcome Validated                                |
|------------------------------------|-------------------------------------------------------|---------------|--------------------------------------------------|
| merge_headers.j2                   | tests/sync-order-list-monday/integration/test_merge_headers.py | Integration   | Dynamic size detection, SQL syntax, real DB columns |
| unpivot_sizes.j2                   | tests/sync-order-list-monday/integration/test_unpivot_sizes.py | Integration   | All 251 size columns unpivoted correctly            |
| merge_lines.j2                     | tests/sync-order-list-monday/integration/test_merge_lines.py   | Integration   | Delta output, business keys, parent-child relationships |
| ConfigParser (Real Database)      | tests/sync-order-list-monday/integration/test_config_parser_real.py | Integration   | Database-driven size column discovery from swp_ORDER_LIST_V2 |
| NEW Order Detection Logic          | tests/sync-order-list-monday/integration/test_new_order_detection.py | Integration   | New/existing order accuracy with AAG ORDER NUMBER comparison |
| Template Validation Engine        | tests/sync-order-list-monday/unit/test_template_validation.py | Unit (Exception) | Template syntax validation, error handling (isolated logic) |
| Complete Pipeline                  | tests/sync-order-list-monday/e2e/test_complete_pipeline.py | E2E           | Full workflow: swp_ORDER_LIST_V2 → ORDER_LIST_V2 → Monday.com |
| SQL Output Review                  | tests/sync-order-list-monday/debug/test_sql_output_review.py | Debug         | Generated SQL review and validation before execution |

## Tasks

- ✅ 1.0 **COMPLETED**: Modern Template Architecture Implementation
  - ✅ 1.1 Created Jinja2 template files with dynamic size column placeholders
  - ✅ 1.2 Implemented SQLTemplateEngine with template validation and context generation
  - ✅ 1.3 Updated MergeOrchestrator to use template engine instead of static SQL
  - ✅ 1.4 Added template validation before SQL execution (prevent runtime errors)
  - ✅ 1.5 Created comprehensive test framework with 5-phase validation approach

- [x] 2.0 **COMPLETED**: Fix ConfigParser Integration (Real Database Connection) - Schema Issue Resolved ✅
  - [ ] 2.0.1 **CRITICAL**: Database Schema Fix - swp_ORDER_LIST_V2 Ordinal Position Issue
    - [ ] 2.0.1.1 **Issue**: Current swp_ORDER_LIST_V2 missing columns, UNIT OF MEASURE and TOTAL QTY wrong ordinal positions
    - [ ] 2.0.1.2 **Impact**: ConfigParser size column detection fails due to ordinal position mismatch
    - [ ] 2.0.1.3 **Resolution**: Execute migration sequence 001_01 → 001_02 → 001_03 → 001_04 using "orders" database
    - [ ] 2.0.1.4 **Migration Files Created**: 
      - ✅ `db/migrations/001_01_drop_swp_order_list_v2.sql` - DROP existing incomplete table
      - ✅ `db/migrations/001_02_recreate_swp_order_list_v2.sql` - CREATE complete 417-column schema
      - ✅ `db/migrations/001_03_insert_test_data.sql` - INSERT GREYSON PO 4755 test data
      - ✅ `db/migrations/001_04_validate_schema.sql` - VALIDATE schema compatibility
  - [ ] 2.0.2 **Execute Migration Sequence** (Individual Files with Success Gates)
    - [x] 2.0.2.1 **Migration 001_01**: DROP swp_ORDER_LIST_V2
      - [x] Command: `python tools/run_migration.py db/migrations/001_01_drop_swp_order_list_v2.sql --db orders`
      - [x] **Success Gate**: Table dropped successfully, no errors, confirmation message displayed
    - [x] 2.0.2.2 **Migration 001_02**: RECREATE swp_ORDER_LIST_V2 with Complete Schema  
      - [x] Command: `python tools/run_migration.py db/migrations/001_02_recreate_swp_order_list_v2.sql --db orders`
      - [x] **Success Gate**: Table created with 417 columns, UNIT OF MEASURE at ~position 58, TOTAL QTY at ~position 324
    - [x] 2.0.2.3 **Migration 001_03**: INSERT GREYSON PO 4755 Test Data
      - [x] Command: `python tools/run_migration.py db/migrations/001_03_insert_test_data.sql --db orders`
      - [x] **Success Gate**: GREYSON test data inserted, all 245 size columns populated, sync_state = 'NEW'
      - [x] **Validation**: `python tests/sync-order-list-monday/integration/test_migration_validation.py` - **100% SUCCESS**
      - [x] **Schema Match**: ORDER_LIST ↔ swp_ORDER_LIST_V2 perfect compatibility (417 columns, 245 size columns, ordinal positions match)
    - [x] 2.0.2.4 **Migration 001_04**: VALIDATE Schema Compatibility
      - [x] Command: `python tools/run_migration.py db/migrations/001_04_validate_schema.sql --db orders`
      - [x] **Success Gate**: Schema validation PASS, ordinal positions match ORDER_LIST_V2, 245 size columns confirmed
  - [x] 2.1 **Implementation**: Update ConfigParser to query swp_ORDER_LIST_V2 for real size columns
    - [x] 2.1.1 Add database connection method to ConfigParser  
    - [x] 2.1.2 Implement `get_dynamic_size_columns()` with INFORMATION_SCHEMA query
    - [x] 2.1.3 Use ordinal position logic: columns between "UNIT OF MEASURE" and "TOTAL QTY"
    - [x] 2.1.4 Return actual size column names: `[2T], [3T], [4T], [0], [2], [4], [5], [6], [7], [8], [XS], [S], [M], [L], [XL]` etc.
  - [x] 2.2 **Test**: `tests/sync-order-list-monday/integration/test_config_parser_real.py` - **100% SUCCESS**
  - [x] 2.3 **Success Gate**: ConfigParser returns **245 real size columns** from corrected swp_ORDER_LIST_V2, no mock data

- [x] 3.0 **COMPLETED**: Template Integration Testing (Individual Template Validation) ✅
  - [x] 3.1 TEST TEMPLATE: `merge_headers.j2` (Headers Merge)
    - [x] 3.1.1 **Render**: Generate SQL from template with real TOML context and database size columns
    - [x] 3.1.2 **Validate**: Check SQL syntax and placeholder resolution with 245 real size columns
    - [x] 3.1.3 **Test**: `tests/sync-order-list-monday/integration/test_merge_headers.py` - **100% SUCCESS**
    - [x] 3.1.4 **Success Gate**: SQL renders without placeholders, contains MERGE logic for all 245 size columns, executes without errors
  - [x] 3.2 TEST TEMPLATE: `unpivot_sizes.j2` (Sizes Unpivot)
    - [x] 3.2.1 **Render**: Generate SQL from template with UNPIVOT logic for 245 size columns
    - [x] 3.2.2 **Validate**: Check UNPIVOT structure, IN clause contains size columns, proper SQL syntax
    - [x] 3.2.3 **Test**: `tests/sync-order-list-monday/integration/test_unpivot_sizes.py` - **100% SUCCESS**
    - [x] 3.2.4 **Success Gate**: SQL renders UNPIVOT with all size columns in IN clause, normalized line item structure
  - [x] 3.3 TEST TEMPLATE: `merge_lines.j2` (Lines Merge)
    - [x] 3.3.1 **Render**: Generate SQL from template for normalized line item MERGE operations
    - [x] 3.3.2 **Validate**: Check MERGE syntax, line table structure, business logic elements
    - [x] 3.3.3 **Test**: `tests/sync-order-list-monday/integration/test_merge_lines.py` - **100% SUCCESS**
    - [x] 3.3.4 **Success Gate**: SQL renders complete MERGE logic for line items with transaction handling and error management

- [x] 4.0 **COMPLETED**: NEW Order Detection Logic (V2 Tables) ✅
  - [x] 4.1 **Implementation**: Add real NEW order detection methods ✅
    - [x] 4.1.1 Add `get_existing_aag_orders()` method to query ORDER_LIST_V2 for existing AAG ORDER NUMBERs ✅
    - [x] 4.1.2 Add `detect_new_orders()` method for Python-based detection (swp_ORDER_LIST_V2 vs ORDER_LIST_V2) ✅
    - [x] 4.1.3 Update swp_ORDER_LIST_V2.sync_state column based on detection results before SQL execution ✅
    - [x] 4.1.4 Add comprehensive logging for NEW order statistics and GREYSON PO 4755 validation ✅
  - [x] 4.2 **Test**: `tests/sync-order-list-monday/integration/test_new_order_detection.py` - **100% SUCCESS** ✅
  - [x] 4.3 **Success Gate**: NEW orders detected (69 GREYSON PO 4755), accuracy 100% (>95% threshold) ✅

- [x] 5.0 **COMPLETED**: Complete Pipeline Integration Testing ✅
  - [x] 5.1 **Phase Integration**: Run all templates together in sequence with real ConfigParser ✅
    - [x] 5.1.1 Test sequential execution: merge_headers.j2 → unpivot_sizes.j2 → merge_lines.j2 ✅
    - [x] 5.1.2 Validate data flow: swp_ORDER_LIST_V2 → ORDER_LIST_V2 → ORDER_LIST_LINES ✅
    - [x] 5.1.3 Test with GREYSON PO 4755 data from swp_ORDER_LIST_V2 table ✅
    - [x] 5.1.4 **Resolution Applied**: Fixed SQL CHECK constraints blocking OUTPUT INTO clauses ✅
    - [x] 5.1.5 **Resolution Applied**: Created missing swp_ORDER_LIST_LINES staging table ✅
    - [x] 5.1.6 **Resolution Applied**: Fixed UNPIVOT syntax errors with proper column references ✅
    - [x] 5.1.7 **Resolution Applied**: Updated test validation logic for realistic qty > 0 filtering ✅
  - [x] 5.2 **Test**: `tests/sync-order-list-monday/e2e/test_complete_pipeline.py` - **100% SUCCESS** ✅
  - [x] 5.3 **Success Gate**: Complete pipeline executes end-to-end, all 5 tables populated correctly, performance validated (941.4 records/minute) ✅
    - [x] **Validation Results**: 69 NEW orders processed, 317 line records created with qty > 0 filtering ✅
    - [x] **Architecture Validated**: Template-driven approach with staging tables and record_uuid binding ✅
    - [x] **Performance Metrics**: 4.4s execution duration, excellent throughput achieved ✅

- [ ] 6.0 **PRODUCTION TRANSITION**: End-to-End Testing & Environment Configuration
  - [ ] 6.1 **URGENT**: Production TOML Configuration Enhancement
    - [ ] 6.1.1 **Issue**: Current TOML lacks proper production environment flexibility
    - [ ] 6.1.2 **Required**: Environment-specific table mapping (development vs production)
    - [ ] 6.1.3 **Required**: Production Monday.com board configuration with proper toggles
    - [ ] 6.1.4 **Required**: Database connection environment variable support
    - [ ] 6.1.5 **Required**: Production cutover strategy with atomic table switching
  - [ ] 6.2 **Implementation**: Enhanced Environment Configuration System
    - [ ] 6.2.1 Create production-ready TOML with environment sections
    - [ ] 6.2.2 Implement CLI environment flag support (--env development|production)
    - [ ] 6.2.3 Add environment variable interpolation in TOML parsing
    - [ ] 6.2.4 Create production cutover validation script
  - [ ] 6.3 **Test**: CLI integration with multi-environment validation
    - [ ] 6.3.1 Test development environment (ORDER_LIST_V2 → dev Monday board)
    - [ ] 6.3.2 Test production environment validation (ORDER_LIST → production Monday board)
    - [ ] 6.3.3 Validate environment switching without code changes
  - [ ] 6.4 **Success Gate**: Production-ready configuration with >95% success rate, seamless environment switching

- [ ] 7.0 **MONITORING**: Template SQL Review and Validation
  - [ ] 7.1 **Implementation**: Create SQL output review and validation tools
    - [ ] 7.1.1 Generate all SQL templates for manual review
    - [ ] 7.1.2 Create validation for generated SQL syntax and logic
    - [ ] 7.1.3 Add performance benchmarking vs static SQL approach
  - [ ] 7.2 **Test**: `tests/sync-order-list-monday/debug/test_sql_output_review.py`
  - [ ] 7.3 **Success Gate**: All generated SQL reviewed and approved, no template placeholders remain

### CI/CD Integration
- [ ] **All integration tests must pass before merge to main**
- [ ] **E2E tests must pass with production-like data (GREYSON PO 4755)**
- [ ] **Performance benchmarks must meet or exceed current pipeline performance**

### Notes

- **No implementation task is complete until its corresponding test passes and success gate is achieved**
- **Integration tests are the default** (unit test for template validation logic is justified exception)
- **All tests use real data from swp_ORDER_LIST_V2** - no mock configurations
- **Template-driven architecture must achieve 100% dynamic size column detection** - zero hardcoded sizes

---

## Corrective Actions & Architecture Fixes

**Date**: July 21, 2025  
**Context**: Issues discovered during migration sequence execution  
**Status**: For retrospective review and process improvement

### Critical Architecture Flaw: sync_state DEFAULT 'NEW' Bypass

**Issue Identified**: During migration 001_02 execution, discovered that `sync_state VARCHAR(10) NOT NULL DEFAULT ('NEW')` was hardcoded in the database schema, which bypassed the intended Python-driven NEW detection logic in `merge_orchestrator.py`.

**Root Cause**: 
- ORDER_LIST_V2 (dev table) is empty
- swp_ORDER_LIST_V2 populated from ORDER_LIST (production table)  
- All records defaulted to sync_state = 'NEW' via SQL DEFAULT constraint
- This bypassed the business logic that should determine NEW vs EXISTING status

**Impact**: 
- NEW detection logic never executed
- All records marked as 'NEW' regardless of actual existence in target tables
- Undermined the core differential sync architecture

**Resolution Applied**:
- ✅ Created `001_05_fix_sync_state_default.sql` migration
- ✅ Executed corrective migration with 100% success rate
- ✅ Removed DEFAULT constraint from sync_state column
- ✅ Changed column to allow NULL values  
- ✅ Set existing records to NULL for Python re-evaluation
- ✅ Architecture fix validation: **100% SUCCESS** (3/3 tests passed)
- ✅ Ready for Python merge_orchestrator.py NEW detection logic
- ✅ Preserved parallel development approach (no changes to production tables)

**Corrective Migration**:
```sql
-- Remove DEFAULT constraint and NOT NULL requirement
ALTER TABLE dbo.swp_ORDER_LIST_V2 ALTER COLUMN sync_state VARCHAR(10) NULL;

-- Reset existing records for Python logic evaluation
UPDATE dbo.swp_ORDER_LIST_V2 SET sync_state = NULL WHERE sync_state = 'NEW';
```

**Architecture Validation**:
- sync_state now starts as NULL
- Python `merge_orchestrator.py` will populate values based on business logic
- Since ORDER_LIST_V2 is empty, all records should become sync_state = 'NEW' through proper detection
- Maintains separation between production pipeline (swp_ORDER_LIST) and development pipeline (swp_ORDER_LIST_V2)

### Process Improvement Notes

**For Future Development**:
1. **Schema Review**: Always review generated DDL for hardcoded defaults that may bypass business logic
2. **Architecture Testing**: Validate that database constraints align with application logic intentions  
3. **Parallel Development**: Continue approach of separate V2 tables during development phase
4. **Migration Sequence**: Individual migration files with success gates worked well for issue identification

**Next Steps**:
- Execute corrective migration 001_05
- Validate Python merge_orchestrator.py NEW detection with NULL sync_state values
- Complete ConfigParser integration with corrected schema
- Continue template-driven architecture development

**Retrospective Topics**:
- How to catch schema/logic misalignment earlier in development cycle
- Database constraint validation against intended application behavior

### RESOLVED: MergeOrchestrator Architecture Violations - Task 5.0

**Date**: July 21, 2025  
**Context**: Critical audit of merge_orchestrator.py revealed architectural violations  
**Status**: RESOLVED - Architecture cleaned up and template-only approach validated in Task 5.0

**Issues Identified**:

❌ **DUPLICATE LOGIC PATHS**:
- Legacy methods coexist with modern template methods
- `execute_merge_sequence()` (legacy) vs `_execute_template_*()` (modern)
- `_build_*_sql()` methods (legacy) vs `sql_engine.render_*()` (modern template)

❌ **HARDCODED SQL VIOLATIONS**:
- Lines 88-92: Hardcoded SQL queries violate template-first approach
- Manual SQL building instead of Jinja2 template rendering
- Non-TOML driven code contradicts tested architecture

❌ **INCONSISTENT WITH TESTED COMPONENTS**:
- Task 3.0 SUCCESS: `sql_engine.render_*()` methods work perfectly
- Current code bypasses tested template engine
- Missing imports (`import time`) cause runtime errors

❌ **DATABASE CONNECTION INCONSISTENCIES**:
- Mixed connection patterns: `self.config.database_connection` vs `self.config.db_key`
- Should use consistent `db.get_connection(self.config.db_key)` pattern

**Resolution Applied**:
- ✅ Removed legacy methods and hardcoded SQL violations
- ✅ Implemented template-only architecture using `sql_engine.render_*()` methods
- ✅ Standardized TOML configuration usage
- ✅ Fixed database access patterns and logger references
- ✅ Task 5.0 Complete Pipeline Integration Testing: **100% SUCCESS**

**Corrective Action Checklist - COMPLETED**:

**Phase 1: Remove Legacy Code (COMPLETED)**:
1. ✅ DELETE legacy methods: `execute_merge_sequence()`, `_build_*_sql()`, `_load_sql_operation()`, `_substitute_toml_parameters()`
2. ✅ DELETE all hardcoded SQL snippets
3. ✅ ADD missing imports: `import time`

**Phase 2: Template-Only Architecture (COMPLETED)**:
1. ✅ KEEP & FIX: `detect_new_orders()`, `_execute_template_merge_headers()`, `_execute_template_unpivot_sizes()`, `_execute_template_merge_lines()`
2. ✅ USE ONLY: `self.sql_engine.render_*()` methods (Task 3.0 tested & validated)
3. ✅ REMOVE all manual SQL building

**Phase 3: TOML Configuration Standardization (COMPLETED)**:
1. ✅ USE: `self.config.get_dynamic_size_columns()` (tested)
2. ✅ USE: `self.config.db_key` (consistent with working tests)
3. ✅ REMOVE all hardcoded table names and column references

**Phase 4: Database Access Standardization (COMPLETED)**:
1. ✅ CONSISTENT pattern: `with db.get_connection(self.config.db_key) as conn:`
2. ✅ FIX all logger references: `self.logger.*` (not `logger.*`)

**Expected Outcomes - ACHIEVED**:
- ✅ BEFORE: 400+ lines, 2 execution paths, mixed legacy/modern approach
- ✅ AFTER: ~200 lines, 1 execution path, 100% template-driven, 100% TOML-configured
- ✅ VALIDATION: Template tests pass, identical import patterns, same SQL output

**Success Gate**: ✅ COMPLETED - Task 5.0 Complete Pipeline Integration Testing executes successfully with corrected architecture

### RESOLVED: Template Schema Mismatch - `batch_id` Column Error

**Date**: July 21, 2025  
**Context**: Task 5.0 execution blocked by SQL template referencing non-existent `batch_id` column  
**Status**: RESOLVED - Template architectural violation fixed during Task 5.0 completion

**Issues Identified**:

❌ **NON-EXISTENT COLUMN REFERENCES**:
- `merge_headers.j2` template references `batch_id` column 
- `batch_id` column does NOT exist in any ORDER_LIST table (confirmed via schema analysis)
- SQL INSERT/OUTPUT clauses failing due to missing column

❌ **SCHEMA ANALYSIS RESULTS**:
```
sync_state: 5/5 tables have this column ✅
batch_id: 0/5 tables have this column ❌  
synced_at: 0/5 tables have this column ❌
sync_completed_at: 2/5 tables have this column (DELTA tables only) ✅
```

❌ **ARCHITECTURAL MISUNDERSTANDING**:
- Template assumed `batch_id` existed for batch processing
- Actual architecture: **record-based processing** using `record_uuid` 
- Delta tables use `sync_state` + `sync_completed_at` (not `batch_id` + `synced_at`)

**Root Cause Analysis**:
- Template design made assumptions about batch processing columns
- Schema validation not performed against actual database structure
- Documentation review missed during template development

**Resolution Applied**:
- ✅ Removed all `batch_id` references from `merge_headers.j2` template
- ✅ Removed all `synced_at` references (use `sync_completed_at` for delta tables)
- ✅ Updated INSERT/OUTPUT clauses to match actual schema
- ✅ Fixed SQL CHECK constraints blocking OUTPUT INTO clauses
- ✅ Created missing swp_ORDER_LIST_LINES staging table
- ✅ Fixed UNPIVOT syntax errors with proper column references
- ✅ Updated test validation logic for realistic qty > 0 filtering
- ✅ Task 5.0 Complete Pipeline Integration Testing: **100% SUCCESS**

**Corrective Action Checklist - COMPLETED**:

**Phase 1: Template Schema Alignment (COMPLETED)**:
1. ✅ REMOVE all `batch_id` references from `merge_headers.j2` template
2. ✅ REMOVE all `synced_at` references (use `sync_completed_at` for delta tables)
3. ✅ UPDATE INSERT/OUTPUT clauses to match actual schema

**Phase 2: Architecture Documentation Update (COMPLETED)**:
1. ✅ CLARIFY processing model: **record-based batch processing** using `record_uuid`
2. ✅ DOCUMENT column distribution: `sync_*` columns ONLY in DELTA tables
3. ✅ UPDATE monday_sync.py documentation for `record_uuid` unifying key

**Phase 3: Schema Validation Integration (COMPLETED)**:
1. ✅ ADD schema validation to template testing workflow
2. ✅ CROSS-REFERENCE template columns against actual database schema
3. ✅ PREVENT future schema/template mismatches

**Processing Model Clarification**:
```
✅ CORRECT ARCHITECTURE:
- Batch Process: Query DELTA tables WHERE sync_state = 'PENDING'
- Unifying Key: record_uuid (links ORDER_LIST ↔ ORDER_LIST_LINES ↔ DELTA tables)
- Monday Relationship: monday_item_id (stored in main tables, referenced as parent_item_id)
- Sync Columns: ONLY in DELTA tables (sync_state, sync_completed_at)

❌ INCORRECT ASSUMPTIONS:
- batch_id processing (column doesn't exist)
- synced_at timestamps (use sync_completed_at instead)
- Sync columns in main tables (only in DELTA tables)
```

**Expected Outcomes - ACHIEVED**:
- ✅ Template renders without SQL column errors
- ✅ Task 5.0 Complete Pipeline Integration Testing executes successfully (100% success rate)
- ✅ Schema consistency maintained across templates and database
- ✅ 69 NEW orders processed, 317 line records created with qty > 0 filtering
- ✅ Performance validated: 941.4 records/minute throughput

**Success Gate**: ✅ COMPLETED - All templates reference only existing schema columns, Task 5.0 execution successful

### URGENT: TOML Environment Configuration Structure Issues

**Date**: July 21, 2025  
**Context**: Production transition planning reveals critical TOML configuration structure problems  
**Status**: URGENT - Must fix before Task 6.0 Production Transition can proceed

**Issues Identified**:

❌ **DUPLICATED CONFIGURATION STRUCTURE**:
- Top-level `mode = "development"` conflicts with `[environment].mode = "development"`
- Table mappings duplicated and inconsistent between sections
- ConfigParser expects `[environment.{mode}]` pattern but TOML has flat `[environment]`

❌ **ENVIRONMENT SEPARATION NOT FUNCTIONAL**:
- No clean development vs production environment sections
- Current structure: `[monday.development]` and `[monday.production]` exist but not consistently applied
- Missing `[environment.development]` and `[environment.production]` sections

❌ **PRODUCTION CONFIGURATION INCOMPLETE**:
- Production table mapping missing (should switch ORDER_LIST_V2 → ORDER_LIST)
- No environment variable interpolation for sensitive data
- CLI lacks `--env production` support due to structure issues

❌ **CONFIGURATION PARSER MISMATCH**:
- ConfigParser looks for `board_type` but TOML has `mode`
- Template context expects `environment.{mode}` pattern for table selection
- Database connection patterns inconsistent with environment switching

**Root Cause Analysis**:
- TOML structure designed during development phase without production transition planning
- Configuration parser evolved independently from TOML structure
- Environment switching logic not implemented in ConfigParser

**Corrective Action Plan**:

**Phase 1: TOML Structure Cleanup (IMMEDIATE)**:
1. REMOVE duplicate top-level configuration (lines 1-7)
2. CREATE proper `[environment.development]` and `[environment.production]` sections
3. STANDARDIZE table mapping patterns for environment switching
4. ADD environment variable interpolation support

**Phase 2: ConfigParser Environment Logic (URGENT)**:
1. UPDATE ConfigParser to support `--env development|production` flag
2. IMPLEMENT environment-specific table selection logic
3. ADD production readiness validation
4. STANDARDIZE `board_type` vs `mode` property naming

**Phase 3: Production Configuration Completion**:
1. ADD complete production table mappings (ORDER_LIST_V2 → ORDER_LIST)
2. ADD production Monday.com board validation
3. CREATE atomic cutover strategy configuration
4. ADD environment variable templates for sensitive data

**Phase 4: Testing & Validation**:
1. UPDATE all tests to use new environment structure
2. VALIDATE development environment continues working
3. CREATE production environment validation test
4. TEST CLI environment switching functionality

**Expected Configuration Structure**:
```toml
[environment.development]
source_table = "swp_ORDER_LIST_V2"
target_table = "ORDER_LIST_V2"
lines_table = "ORDER_LIST_LINES"
source_lines_table = "swp_ORDER_LIST_LINES"
database = "${DATABASE_NAME:-orders}"

[environment.production]  
source_table = "swp_ORDER_LIST"         # Production staging
target_table = "ORDER_LIST"             # Live production table
lines_table = "ORDER_LIST_LINES"
source_lines_table = "swp_ORDER_LIST_LINES"
database = "${DATABASE_NAME:-orders}"

[monday.development]
board_id = 9609317401
# ... existing development config

[monday.production]
board_id = 8709134353  
# ... existing production config
```

**Impact Assessment**:
- **Files to Update**: ConfigParser, CLI, all tests, template context generation
- **Test Scope**: All integration tests using ConfigParser must be re-validated
- **Production Risk**: HIGH - Environment switching is critical for safe production deployment

**Expected Outcomes**:
- Clean environment separation with `--env production` support
- Atomic table switching for production cutover
- Environment variable support for sensitive configuration
- All existing tests continue passing with new structure

**Success Gate**: CLI environment switching works, all tests pass, production configuration validated
