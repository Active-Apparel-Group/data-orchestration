# ORDER_LIST Delta Monday Sync - Testing Documentation

## Overview
This document tracks all testing activities, outcomes, and procedures for the ORDER_LIST → Monday.com delta sync pipeline development.

**Project Phase**: Milestone 1 (Foundation) - COMPLETE  
**Next Phase**: Milestone 2 (Delta Engine) - READY TO BEGIN  
**Last Updated**: July 18, 2025

---

## Testing Philosophy

Following the **modular, iterative approach** from [test.instructions.md](../../.github/instructions/test.instructions.md):

- **Run individual test phases** when debugging specific issues
- **Build comprehensive test suites** that validate end-to-end workflows  
- **Iterate and expand tests** as new functionality is added
- **Validate against actual production data** (no test/mock data)
- **Generate detailed reports** with actionable metrics

---

## Milestone 1 Testing Results

### Foundation Validation Test
**Test File**: [tests/debug/simple_milestone_1_test.py](../../tests/debug/simple_milestone_1_test.py)  
**Execution Date**: July 18, 2025  
**Overall Result**: SUCCESS (100.0% pass rate)

#### Test Phases:
1. **TOML Configuration**: PASSED
   - Successfully loaded 11 configuration sections
   - All required sections present: environment, database, hash, sizes
   - No configuration parsing errors

2. **Config Parser**: PASSED  
   - DeltaSyncConfig class initialized successfully
   - Hash SQL generation working with CONCAT function
   - Kestra-compatible logging implemented

3. **Database Config**: PASSED
   - orders database configuration validated
   - Connection parameters accessible from config.yaml

4. **Migration DDL**: PASSED
   - Shadow table DDL syntax validated
   - No hardcoded hash logic found (configuration-driven approach)
   - Required tables present: ORDER_LIST_V2, ORDER_LIST_LINES

#### Key Success Metrics:
- **Configuration Loading**: 100% success rate
- **Schema Compatibility**: 52 size columns detected dynamically
- **Infrastructure Integration**: All components working together
- **Standards Compliance**: ASCII-only output (no Unicode/emoji violations)

### Test Execution Commands:
```bash
# Run foundation validation
python tests/debug/simple_milestone_1_test.py

# Expected output (ASCII only):
# ORDER_LIST Delta Monday Sync - Milestone 1 Foundation Test
# OVERALL SUCCESS RATE: 100.0% (4/4 tests passed)
# MILESTONE 1 FOUNDATION: READY FOR DEVELOPMENT
```

---

## Testing Infrastructure

### Core Test Files Location
All test files are stored in the consolidated test directory structure:

```
tests/
├── debug/                           # Development and debugging tests
│   ├── simple_milestone_1_test.py   # Foundation validation (COMPLETE)
│   └── [future milestone tests]     # Additional milestone validations
├── end_to_end/                      # Integration tests (future)
│   └── test_delta_sync_complete.py  # Full pipeline validation (planned)
└── unit/                            # Component-specific tests (future)
    ├── test_config_parser.py        # Configuration parser unit tests
    └── test_hash_generation.py      # Hash logic validation
```

### Test Framework Standards
Following project [test.instructions.md](../../.github/instructions/test.instructions.md) patterns:

- **Modular Testing**: Each test phase validates specific functionality
- **Database Validation**: Query actual data, not mock/test data
- **Clear Success Criteria**: Numeric thresholds for pass/fail determination
- **Comprehensive Reporting**: Detailed metrics and actionable feedback
- **ASCII Output Only**: No Unicode/emoji violations per coding standards

---

## Critical Issues Resolved During Testing

### Issue 1: Import Path Errors
**Problem**: Config parser looking for utils/ in wrong location  
**Solution**: Updated to use pipelines/utils/ path structure  
**Files Fixed**: [tests/debug/simple_milestone_1_test.py](../../tests/debug/simple_milestone_1_test.py)

### Issue 2: Hardcoded Hash Logic in SQL
**Problem**: Migration DDL contained hardcoded HASHBYTES functions  
**Solution**: Removed computed columns, made hash generation configuration-driven  
**Files Fixed**: [db/migrations/001_create_shadow_tables.sql](../../db/migrations/001_create_shadow_tables.sql)

### Issue 3: Unicode/Emoji Violations
**Problem**: Using emoji in output violated project coding standards  
**Solution**: Replaced all Unicode characters with ASCII alternatives  
**Reference**: [copilot.instructions.md](../../.github/instructions/copilot.instructions.md) Unicode Policy

### Issue 4: Config Class Initialization
**Problem**: DeltaSyncConfig required config_data parameter  
**Solution**: Load TOML data before initializing config parser  
**Pattern**: Load config → Pass to constructor → Validate functionality

---

## Testing Standards & Patterns

### Database Testing Pattern
```python
# Always use actual database connections to 'orders' database
with db.get_connection('orders') as conn:
    sql = "SELECT COUNT(*) FROM ORDER_LIST_V2 WHERE [criteria]"
    result = pd.read_sql(sql, conn)
    
# Validate against expected criteria
success_rate = (successful_records / total_records * 100)
validation = {
    'success': success_rate >= 95,  # Clear numeric criteria
    'success_rate': success_rate,
    'total_records': total_records
}
```

### Configuration Testing Pattern
```python
# Load and validate TOML configuration
import tomli
config_path = Path("configs/pipelines/sync_order_list_dev.toml")
with open(config_path, 'rb') as f:
    config = tomli.load(f)

# Validate required sections
required_sections = ['environment', 'database', 'hash', 'sizes']
missing_sections = [s for s in required_sections if s not in config]
```

### Success Criteria Definitions
- **Excellent**: >95% success rate, <5% errors
- **Good**: >90% success rate, <10% errors  
- **Needs Attention**: <90% success rate, >10% errors

---

## Milestone 2 Testing Plan (READY TO IMPLEMENT)

### Planned Test Components:
1. **Hash-based Change Detection**
   - Test file: `tests/debug/test_hash_change_detection.py`
   - Validation: Hash calculation accuracy, change identification

2. **Size Column Discovery**  
   - Test file: `tests/debug/test_size_column_discovery.py`
   - Validation: Dynamic detection between UNIT OF MEASURE and TOTAL QTY

3. **Delta Merge Operations**
   - Test file: `tests/debug/test_delta_merge_operations.py`
   - Validation: SQL merge logic for headers and lines

4. **GraphQL Integration**
   - Test file: `tests/debug/test_graphql_integration.py`
   - Validation: Template loading, async batch processing

### Integration Testing:
- **End-to-End Validation**: `tests/end_to_end/test_milestone_2_complete.py`
- **Database State Verification**: Actual ORDER_LIST_V2 and ORDER_LIST_LINES validation
- **Monday.com Mock Integration**: Validate API calls without live Monday updates

---

## VS Code Testing Tasks

### Current Tasks Available:
```json
{
    "label": "Test: Milestone 1 Foundation",
    "command": "python",
    "args": ["tests/debug/simple_milestone_1_test.py"],
    "detail": "Validate Milestone 1 foundation components (100% success rate achieved)"
}
```

### Planned Tasks for Milestone 2:
- **Test: Hash Change Detection**
- **Test: Size Column Discovery** 
- **Test: Delta Merge Operations**
- **Test: GraphQL Integration**
- **Test: Milestone 2 Complete**

---

## Quality Assurance Checklist

### Before Each Milestone:
- [ ] All test files follow ASCII-only output standards
- [ ] Database connections use 'orders' database (contains ORDER_LIST tables)
- [ ] Configuration loading uses correct TOML patterns
- [ ] Import paths follow modern src/pipelines/ structure
- [ ] Success criteria clearly defined with numeric thresholds
- [ ] Error handling includes actionable remediation steps

### After Each Test Run:
- [ ] Document test outcomes in this file
- [ ] Update success/failure metrics
- [ ] Identify and document lessons learned
- [ ] Create follow-up issues for any failures
- [ ] Validate against production data patterns

---

## Future Testing Roadmap

### Milestone 3 Testing (Monday Integration):
- **Two-pass sync validation**: Headers → Lines dependency chain
- **Retry logic testing**: Failed sync recovery scenarios
- **State management validation**: Sync status tracking across tables
- **Production integration**: Real Monday.com board validation

### Milestone 4 Testing (Production Cutover):
- **Migration validation**: Shadow → Production table cutover
- **Performance testing**: Large-scale data processing
- **Operational testing**: Scheduled sync functionality
- **Rollback testing**: Emergency recovery procedures

---

## Contact & Support

**Test Framework Reference**: [.github/instructions/test.instructions.md](../../.github/instructions/test.instructions.md)  
**Development Standards**: [.github/instructions/copilot.instructions.md](../../.github/instructions/copilot.instructions.md)  
**Project Overview**: [docs/changelogs/sync-order-list-monday.md](../changelogs/sync-order-list-monday.md)

**Testing Philosophy**: Validate early, validate often, validate with actual data.
