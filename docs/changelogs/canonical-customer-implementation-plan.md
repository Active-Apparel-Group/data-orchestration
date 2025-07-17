# Canonical Customer Implementation Plan

**Version**: 1.0  
**Date**: July 17, 2025  
**Status**: 🚀 Phase 1 & 2 In Progress | Phase 3 Planned  
**Owner**: Data Engineering Team

## 📋 **Implementation Overview**

This document outlines the phased approach for implementing canonical customer references across all data pipelines, starting with ORDER_LIST and extending to ingestion workflows.

### **Core Objectives:**
- ✅ Standardize customer names using [`pipelines/utils/canonical_customers.yaml`](../pipelines/utils/canonical_customers.yaml)
- ✅ Ensure only canonical customer references reach the database
- ✅ Maintain full traceability of source customer names
- ✅ Prepare for future ingestion workflow integration

---

## 🎯 **Phase 1: Create Canonical Customer Utility** 
**Status**: ✅ **APPROVED FOR EXECUTION**  
**Target**: Universal customer name standardization utility

### **Goals:**
- Create `utils/canonical_customer_manager.py` 
- Integrate with existing `pipelines/utils/canonical_customers.yaml`
- Support all source systems (master_order_list, packed_products, shipped)
- Provide validation and mapping statistics

### **Key Features:**
- **Multi-source mapping**: Different customer names across source systems
- **Alias resolution**: Handle customer name variations
- **Status validation**: Only approved customers for production use
- **Comprehensive logging**: Track all mapping decisions

### **Deliverables:**
- ✅ `utils/canonical_customer_manager.py` - Universal customer mapper
- ✅ Factory functions for easy integration
- ✅ Validation utilities for data quality
- ✅ Testing framework integration

---

## 🔧 **Phase 2: ORDER_LIST Pipeline Integration**
**Status**: ✅ **APPROVED FOR EXECUTION**  
**Target**: Enhanced ORDER_LIST transformer with canonical customer integration

### **Goals:**
- Enhance ORDER_LIST transformer to inject canonical customer names
- Validate all customers have canonical mappings
- Preserve source customer names for audit trail
- Maintain existing ORDER_LIST functionality

### **Key Features:**
- **Canonical customer injection**: Transform during SQL generation
- **Source preservation**: Keep original customer name from table
- **Validation workflow**: Ensure all customers have mappings
- **Error handling**: Clear logging for unmapped customers

### **Database Columns (Phase 3):**
```sql
-- Three customer columns approach:
[CANONICAL_CUSTOMER] NVARCHAR(255) NOT NULL,     -- Canonical customer name
[SOURCE_CUSTOMER_NAME] NVARCHAR(255) NULL,       -- Original source customer name  
[CUSTOMER NAME] NVARCHAR(255) NULL,              -- Existing field (NOT deprecated)
```

### **Deliverables:**
- ✅ Enhanced `CanonicalOrderListTransformer` class
- ✅ Customer validation for raw tables
- ✅ Integration with existing ORDER_LIST pipeline
- ✅ Comprehensive test suite

---

## 📊 **Phase 3: Database Schema Updates**
**Status**: 🟡 **PLANNED - NOT YET EXECUTED**  
**Target**: Add canonical customer columns to ORDER_LIST table

### **Goals:**
- Add `CANONICAL_CUSTOMER` and `SOURCE_CUSTOMER_NAME` columns
- Keep existing `CUSTOMER NAME` column (NOT deprecated)
- Maintain backward compatibility
- Add performance indexes

### **Schema Changes:**
```sql
-- Add new columns to ORDER_LIST table
ALTER TABLE [dbo].[ORDER_LIST] 
ADD [CANONICAL_CUSTOMER] NVARCHAR(255) NULL,        -- Will be NOT NULL after population
    [SOURCE_CUSTOMER_NAME] NVARCHAR(255) NULL;

-- Add indexes for performance
CREATE INDEX IX_ORDER_LIST_CANONICAL_CUSTOMER ON [dbo].[ORDER_LIST] ([CANONICAL_CUSTOMER]);
CREATE INDEX IX_ORDER_LIST_SOURCE_CUSTOMER ON [dbo].[ORDER_LIST] ([SOURCE_CUSTOMER_NAME]);

-- After data population, make CANONICAL_CUSTOMER required
ALTER TABLE [dbo].[ORDER_LIST] 
ALTER COLUMN [CANONICAL_CUSTOMER] NVARCHAR(255) NOT NULL;
```

### **Migration Strategy:**
1. Add columns as nullable
2. Populate existing records with canonical mappings
3. Update pipeline to populate new columns
4. Make `CANONICAL_CUSTOMER` NOT NULL
5. Update queries to use canonical customer

### **Deliverables:**
- 🟡 Database migration scripts
- 🟡 Data population scripts  
- 🟡 Performance optimization
- 🟡 Rollback procedures

---

## 🔄 **Future Phases: Ingestion Workflow Extension**

### **Phase 4: Ingestion Pipeline Integration** (Future)
- Apply canonical customer manager to all ingestion workflows
- Standardize customer names across all data sources
- Ensure consistent customer references throughout system

### **Phase 5: Reporting & Analytics Updates** (Future)
- Update dashboards to use canonical customer names
- Migrate Monday.com integrations to canonical references
- Create customer mapping audit reports

---

## 📈 **Success Metrics**

### **Phase 1 & 2 Success Criteria:**
- ✅ All 36 canonical customers loaded successfully
- ✅ 100% mapping coverage for ORDER_LIST pipeline customers  
- ✅ Zero mapping errors for approved customers
- ✅ Complete test coverage with validation framework

### **Phase 3 Success Criteria (Planned):**
- 🟡 Zero downtime schema migration
- 🟡 100% data integrity after migration
- 🟡 Performance maintained or improved
- 🟡 All existing queries continue to work

---

## 🚨 **Risk Management**

### **Identified Risks:**
1. **Customer mapping gaps**: Some ORDER_LIST customers may not have canonical mappings
2. **Performance impact**: Additional lookup operations during transformation
3. **Data consistency**: Ensuring all pipelines use same canonical mappings

### **Mitigation Strategies:**
1. **Comprehensive validation**: Pre-flight checks for all customer mappings
2. **Caching strategy**: Load canonical mappings once per pipeline run
3. **Centralized configuration**: Single source of truth in YAML file

---

## 📋 **Implementation Checklist**

### **Phase 1: Canonical Customer Utility**
- [ ] Create `utils/canonical_customer_manager.py`
- [ ] Implement YAML configuration loading
- [ ] Add multi-source system support
- [ ] Create factory functions and convenience methods
- [ ] Add comprehensive logging and validation
- [ ] Create test framework

### **Phase 2: ORDER_LIST Integration**
- [ ] Create `CanonicalOrderListTransformer` class
- [ ] Enhance SQL generation with canonical customer injection
- [ ] Add customer validation for raw tables
- [ ] Integrate with existing ORDER_LIST pipeline
- [ ] Create integration test suite
- [ ] Add VS Code tasks for testing

### **Phase 3: Database Schema (Planned)**
- [ ] Design migration scripts
- [ ] Plan data population strategy
- [ ] Create performance indexes
- [ ] Design rollback procedures
- [ ] Plan testing strategy

---

## 🔧 **Development Standards**

### **File Organization:**
- **Utilities**: `utils/canonical_customer_manager.py`
- **Transformers**: Enhanced ORDER_LIST transformer classes
- **Tests**: `tests/debug/test_canonical_customer_integration.py`
- **Configuration**: Existing `pipelines/utils/canonical_customers.yaml`

### **Import Standards:**
```python
# Standard import pattern for all scripts
import sys
from pathlib import Path

def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

from canonical_customer_manager import get_canonical_customer_manager
```

### **Error Handling:**
- Comprehensive logging for all mapping decisions
- Clear error messages for unmapped customers
- Validation before any database operations
- Graceful degradation for missing mappings

---

## 📞 **Next Steps**

### **Immediate Actions (Phase 1 & 2):**
1. ✅ **Execute Phase 1**: Create canonical customer utility
2. ✅ **Execute Phase 2**: Integrate with ORDER_LIST pipeline
3. ✅ **Create test suite**: Comprehensive validation framework
4. ✅ **Add VS Code tasks**: Easy testing and execution

### **Future Planning (Phase 3):**
1. 🟡 **Design database migration**: Schema update strategy
2. 🟡 **Plan data population**: Backfill existing records
3. 🟡 **Performance testing**: Ensure optimal query performance
4. 🟡 **Rollback procedures**: Safe migration with rollback capability

---

**Document Status**: 🚀 **Ready for Phase 1 & 2 Execution**  
**Last Updated**: July 17, 2025  
**Next Review**: After Phase 1 & 2 Completion
