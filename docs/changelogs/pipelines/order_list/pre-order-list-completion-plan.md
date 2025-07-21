# 🎯 Pre-Order-List Project Completion Plan

> **Goal**: Complete repository restructure foundation before starting sync-order-list-monday project

## 📋 **Required Completion Checklist**

### **Phase 1: Enhanced Repository Consolidation** ⚡ **DO FIRST**

**Duration**: 45 minutes  
**Risk**: Low (file moves only)  
**Impact**: Critical foundation for order-list project

#### **1.1 DDL Consolidation** (10 minutes)
- [x] ✅ Move `sql/ddl/*` content to `db/ddl/`
- [x] ✅ Remove `sql/ddl/` folder (eliminate duplication)
- [x] ✅ Create `sql/operations/` for operational queries
- [x] ✅ Validate no orphaned DDL files

**Commands to Execute**:
```powershell
# Move DDL content and clean up
robocopy sql\ddl db\ddl /MIR /XO
rmdir sql\ddl /s /q
mkdir sql\operations
```

#### **1.2 Integrations Consolidation** (15 minutes)
- [ ] Create `src/pipelines/integrations/monday/` 
- [ ] Move Monday.com code from scattered locations
- [ ] Create `src/pipelines/integrations/powerbi/`
- [ ] Clean up old integration folders

**Commands to Execute**:
```powershell
# Create consolidated integrations
mkdir src\pipelines\integrations\monday
mkdir src\pipelines\integrations\powerbi
mkdir src\pipelines\integrations\azure
mkdir src\pipelines\integrations\external

# Move from scattered locations
robocopy integrations src\pipelines\integrations\external /MIR
robocopy pipelines\integrations src\pipelines\integrations\monday /MIR

# Clean up duplicates
rmdir integrations /s /q
rmdir pipelines\integrations /s /q
```

#### **1.3 Structure Validation** (10 minutes)
- [ ] Test package imports still work: `from pipelines.utils import db`
- [ ] Validate folder structure matches plan
- [ ] Run emergency tests to ensure no breakage
- [ ] Update documentation references

#### **1.4 Order-List Specific Prep** (10 minutes)
- [ ] Create `src/pipelines/sync_order_list/` module
- [ ] Create `configs/pipelines/` for TOML configs
- [ ] Prepare `sql/operations/` for 003-006.sql files
- [ ] Set up `db/migrations/` for schema changes

### **Phase 2: Order-List Project Structure** ⚡ **THEN**

**Duration**: 15 minutes  
**Risk**: Zero (documentation only)  
**Impact**: Clear development guidance

#### **2.1 Documentation Updates**
- [x] ✅ Updated execution tree in sync-order-list-monday.md
- [x] ✅ Added integration section showing existing infrastructure leverage
- [x] ✅ File placement guidelines created
- [ ] Create order-list project folder structure

#### **2.2 Folder Preparation**
```powershell
# Create order-list specific structure
mkdir src\pipelines\sync_order_list
mkdir configs\pipelines
mkdir docs\implementation\sync_order_list

# Prepare for SQL files
# 001-002 will go in db/migrations/
# 003-006 will go in sql/operations/
```

## 🎯 **Why This Sequence Matters**

### **For Order-List Project Success**:

1. **Clean DDL Management**: 
   - Schema changes (001-002.sql) in `db/migrations/`
   - Operations (003-006.sql) in `sql/operations/`
   - No confusion about where files belong

2. **Leveraged Infrastructure**:
   - Existing `src/pipelines/load_order_list/` for Excel ingestion
   - Consolidated `src/pipelines/integrations/monday/` for API calls
   - Modern `src/pipelines/utils/` for database connections

3. **Modern Development**:
   - No `sys.path.append()` hacks
   - Clean imports: `from pipelines.utils import db`
   - Package-based architecture

### **Dependencies Eliminated**:
- ❌ No more hunting for DDL files in multiple locations
- ❌ No more scattered integration code
- ❌ No more import path confusion
- ❌ No more duplicate folder management

## 🚀 **Execution Plan**

### **Immediate (Next 1 Hour)**:
1. **Execute Enhanced Phase 1** (45 min)
   - Run DDL consolidation commands
   - Execute integrations consolidation
   - Validate structure
   - Test package functionality

2. **Prepare Order-List Structure** (15 min)
   - Create project folders
   - Set up initial files
   - Validate development environment

### **Then Start Order-List Project** with:
- ✅ Clean, consolidated repository structure
- ✅ Modern Python package architecture  
- ✅ Clear file placement guidelines
- ✅ Existing infrastructure ready to leverage
- ✅ Zero duplicate/confusing locations

## 📊 **Risk Assessment**

| Component | Risk Level | Mitigation |
|-----------|------------|------------|
| DDL Consolidation | 🟡 Low | File moves with backup |
| Integrations Cleanup | 🟡 Low | Consolidation, not deletion |
| Package Structure | 🟢 Zero | Already working from Phase 0 |
| Order-List Start | 🟢 Zero | Clean foundation established |

**Overall Risk**: 🟡 **Low** - Mainly file organization with rollback capability

## ✅ **Success Criteria**

Before starting order-list project, validate:

- [ ] **DDL**: Only in `db/ddl/`, no `sql/ddl/`
- [ ] **Integrations**: Only in `src/pipelines/integrations/`
- [ ] **Structure**: Clear separation of schema vs operations
- [ ] **Imports**: Package imports work: `from pipelines.utils import db`
- [ ] **Foundation**: Folders ready for order-list SQL files
- [ ] **Documentation**: Updated and aligned with structure

**When all checked**: Ready to start sync-order-list-monday development! 🚀
