# Database Helper Refactoring Plan

## Overview
Refactor all data orchestration scripts to use the standardized `db_helper.py` module, eliminating custom database connection code and improving maintainability across the codebase.

## Current State Analysis

### ✅ Proven Working Structure
```
data-orchestration/
├── utils/
│   ├── db_helper.py          # ✅ Working database utilities
│   ├── config.yaml           # ✅ Working database configurations  
│   └── test_helper.py        # ✅ Validated test patterns
└── scripts/
    └── monday-boards/
        ├── get_board_planning.py  # ❌ Needs refactoring
        └── test_helper.py         # ✅ Working with simple import
```

### Import Pattern That Works
```python
import sys
from pathlib import Path

# Add utils directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "utils"))
import db_helper as db
```

## Phase 1: Core Script Refactoring

### 1.1 Priority Scripts (High Impact)

#### `scripts/monday-boards/get_board_planning.py` ⭐ **FIRST**
- **Status**: Custom database connection functions
- **Impact**: Production ETL script with 580 lines
- **Functions to Replace**:
  - `get_database_connection()` → `db.get_connection()`
  - `truncate_table()` → Use `db.run_query()` and `db.execute()`
  - `concurrent_insert_chunk()` → Use `db.get_connection()`
  - `production_concurrent_insert()` → Use `db.run_query()` for schema queries

#### `scripts/customer_master_schedule/add_bulk_orders.py`
- **Status**: Likely has custom database code
- **Impact**: Customer data management
- **Effort**: Medium - Similar patterns to monday-boards

#### `scripts/order_staging/*.py`
- **Status**: Multiple staging scripts
- **Impact**: Core data pipeline components
- **Effort**: Medium per script

### 1.2 Secondary Scripts (Medium Impact)

#### `scripts/audit_pipeline/*.py`
- **Status**: May have existing db functions to harmonize
- **Impact**: Data quality and auditing
- **Effort**: Low - Review and align with db_helper

#### `scripts/jobs/*.py`
- **Status**: Various job scripts
- **Impact**: Scheduled operations
- **Effort**: Low-Medium per script

### 1.3 Test Scripts
- **Create test files** for each refactored script following `test_helper.py` pattern
- **Validate** VS Code and Kestra compatibility

## Phase 2: Template and Tooling Updates

### 2.1 Workflow Templates in `tools/`

#### `tools/workflow_generator.py`
- **Update** to include db_helper import pattern
- **Add** standardized error handling
- **Include** configuration validation

#### YAML Workflow Templates
- **Review** current templates in `workflows/`
- **Update** with standardized file copying pattern
- **Add** db_helper and config.yaml to input files

### 2.2 Development Tools

#### `tools/deploy-scripts-clean.ps1`
- **Ensure** db_helper.py and config.yaml are included in deployments
- **Add** validation checks

#### `tools/build.ps1`
- **Add** import validation
- **Include** db_helper dependency checks

## Phase 3: Documentation and Standards

### 3.1 Developer Guidelines
- **Create** coding standards document
- **Document** import patterns and best practices
- **Add** troubleshooting guide for common issues

### 3.2 Testing Framework
- **Standardize** test patterns across all scripts
- **Create** common test utilities
- **Document** VS Code vs Kestra testing approaches

## Implementation Timeline

### Week 1: Foundation
- [x] ✅ Test and validate utils structure with `test_helper.py`
- [ ] 🎯 Refactor `get_board_planning.py` (Priority 1)
- [ ] Create comprehensive test for refactored script
- [ ] Validate in VS Code and Kestra

### Week 2: Core Scripts
- [ ] Refactor `customer_master_schedule/add_bulk_orders.py`
- [ ] Refactor 2-3 `order_staging/*.py` scripts
- [ ] Update corresponding test files
- [ ] Document any edge cases or issues

### Week 3: Templates and Tooling
- [ ] Update `tools/workflow_generator.py`
- [ ] Review and update YAML workflow templates
- [ ] Update deployment scripts
- [ ] Test template generation with new patterns

### Week 4: Validation and Documentation
- [ ] Test all refactored scripts in both environments
- [ ] Complete documentation updates
- [ ] Create developer guidelines
- [ ] Final validation and cleanup

## Success Criteria

### ✅ Technical Success
- [ ] All scripts use `db_helper.py` consistently
- [ ] No custom database connection code remains
- [ ] All scripts work in both VS Code and Kestra
- [ ] Performance maintained or improved
- [ ] Error handling standardized

### ✅ Operational Success
- [ ] Reduced maintenance overhead
- [ ] Consistent configuration management
- [ ] Easier onboarding for new developers
- [ ] Clear testing procedures

### ✅ Deployment Success
- [ ] Templates generate correct import patterns
- [ ] Kestra workflows deploy without modification
- [ ] Configuration changes centralized
- [ ] Rollback procedures documented

## Risk Mitigation

### 🔒 Low Risk Items
- **Import path changes**: Proven pattern already working
- **Configuration**: Using existing config.yaml structure
- **Testing**: Existing test validates approach

### ⚠️ Medium Risk Items
- **Complex scripts**: Some may have intricate database logic
- **Performance**: Bulk operations need careful handling
- **Dependencies**: Some scripts may have unique requirements

### 🚨 High Risk Items
- **Production scripts**: Require thorough testing before deployment
- **Concurrent operations**: Need to maintain performance characteristics
- **Error scenarios**: Must handle edge cases properly

## Mitigation Strategies

1. **Incremental Approach**: Refactor one script at a time
2. **Test First**: Validate each change in isolation
3. **Backup Plans**: Keep original code commented until validation
4. **Gradual Rollout**: Deploy to test environments first
5. **Monitoring**: Add logging to track any issues

## File Structure After Refactoring

```
data-orchestration/
├── utils/
│   ├── db_helper.py          # ✅ Centralized database utilities
│   ├── config.yaml           # ✅ Database configurations
│   └── test_helper.py        # ✅ Reference implementation
├── scripts/
│   ├── monday-boards/
│   │   ├── get_board_planning.py     # ✅ Refactored
│   │   └── test_get_board_planning.py # ✅ New test file
│   ├── customer_master_schedule/
│   │   ├── add_bulk_orders.py        # ✅ Refactored
│   │   └── test_add_bulk_orders.py   # ✅ New test file
│   └── order_staging/
│       ├── *.py                      # ✅ All refactored
│       └── test_*.py                 # ✅ Comprehensive tests
├── tools/
│   ├── workflow_generator.py         # ✅ Updated templates
│   └── *.ps1                         # ✅ Updated deployment scripts
└── workflows/
    └── *.yml                         # ✅ Updated templates
```

## Next Steps

1. **Review and Approve** this plan
2. **Begin with `get_board_planning.py`** refactoring
3. **Create comprehensive test** for the refactored script
4. **Validate in both environments** before proceeding
5. **Update templates** based on lessons learned
6. **Continue with remaining scripts** following proven pattern

---

**Status**: 📋 Ready for Review and Approval  
**Priority**: 🎯 High - Foundation for improved maintainability  
**Timeline**: 4 weeks for complete implementation
