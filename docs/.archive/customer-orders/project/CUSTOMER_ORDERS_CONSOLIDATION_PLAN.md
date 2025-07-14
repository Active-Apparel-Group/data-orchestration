# Customer-Orders Documentation Consolidation Plan
**Generated**: January 2025 | **Purpose**: Eliminate fragmented/outdated documentation  
**Scope**: Complete file reorganization for customer-orders pipeline  
**Status**: ✅ Ready for Implementation

---

## 🎯 **Consolidation Objectives**

1. **Eliminate Duplication**: Remove duplicate mapping files in different locations
2. **Update Naming**: Change all "orders_unified" references to "customer-orders"
3. **Centralize Documentation**: Move related docs to logical locations
4. **Archive Legacy**: Preserve but archive outdated implementation details
5. **Simplify Structure**: Reduce complexity and improve maintainability

---

## 📂 **Current File Inventory & Analysis**
9200517329
### **🔄 FILES TO MOVE/MERGE**

#### **Mapping Files - CONSOLIDATION REQUIRED**
```
CURRENT LOCATIONS (Duplicates/Conflicts):
├── sql/mappings/
│   ├── orders-unified-comprehensive-mapping.yaml    ✅ KEEP (95% accuracy)
│   ├── orders-unified-mapping.yaml                  ❌ MERGE INTO comprehensive
│   ├── orders-unified-delta-sync-v3-mapping.yaml    ❌ MERGE INTO comprehensive  
│   ├── orders_unified_comprehensive_pipeline.yaml   ❌ MERGE INTO comprehensive
│   ├── simple-orders-mapping.yaml                   ✅ KEEP (simplified approach)
│   ├── monday-column-ids.json                       ✅ KEEP (API reference)
│   ├── orders-monday-master.json                    ❌ LEGACY - ARCHIVE
│   └── orders-monday-subitems.json                  ❌ LEGACY - ARCHIVE

├── docs/mapping/ (DUPLICATE LOCATION)
│   ├── orders_unified_monday_mapping.yaml           ❌ DUPLICATE - DELETE
│   ├── field_mapping_matrix.yaml                    ❌ FRAGMENT - MERGE
│   ├── monday_column_ids.json                       ❌ DUPLICATE - DELETE
│   ├── customer_mapping.yaml                        ❌ INCOMPLETE - ARCHIVE
│   └── mapping_fields.yaml                          ❌ FRAGMENT - MERGE

├── utils/
│   ├── data_mapping.yaml                            ❌ LEGACY - ARCHIVE
│   └── config.yaml                                  ✅ KEEP (live config)
```

**CONSOLIDATION PLAN**:
1. **Keep Primary**: `sql/mappings/orders-unified-comprehensive-mapping.yaml` → rename to `customer-orders-master-mapping.yaml`
2. **Keep Simplified**: `sql/mappings/simple-orders-mapping.yaml` → rename to `customer-orders-simple-mapping.yaml`
3. **Keep API Reference**: `sql/mappings/monday-column-ids.json` → rename to `customer-orders-monday-columns.json`
4. **Archive Legacy**: Move old files to `sql/mappings/legacy/`
5. **Delete Duplicates**: Remove all files from `docs/mapping/`

#### **Documentation Files - REORGANIZATION REQUIRED**
```
CURRENT LOCATIONS:
├── docs/
│   ├── CUSTOMER_ORDERS_PIPELINE_HANDOVER.md         ✅ NEW MASTER DOCUMENT
│   ├── MAPPING_ANALYSIS_COMPREHENSIVE_REPORT.md     ❌ ARCHIVE (superseded)
│   ├── ORDERS_UNIFIED_BACKWARD_MAPPING_COMPREHENSIVE.md  ❌ RENAME & UPDATE
│   ├── HYBRID_SNAPSHOT_ARCHITECTURE.md              ✅ KEEP (still relevant)
│   ├── SCHEMA_VALIDATION_CRITICAL_ISSUES.md         ❌ ARCHIVE (issues resolved)
│   ├── SCHEMA_VALIDATION_IMPLEMENTATION_PLAN.md     ❌ ARCHIVE (completed)
│   └── YAML_MAPPING_FORMAT_DECISION.md              ❌ ARCHIVE (decision made)

├── docs/mapping/
│   ├── orders_unified_monday_comparison.md          ❌ ARCHIVE (outdated analysis)
│   ├── subitems_monday_api_mapping.md              ❌ ARCHIVE (legacy approach)
│   └── IMPLEMENTATION_CHECKLIST.md                  ❌ ARCHIVE (completed)
```

**REORGANIZATION PLAN**:
1. **Primary Reference**: `CUSTOMER_ORDERS_PIPELINE_HANDOVER.md` (already created)
2. **Archive Completed**: Move analysis/validation docs to `docs/archive/customer-orders/`
3. **Update References**: Rename "orders_unified" to "customer-orders" in remaining docs
4. **Consolidate Mapping Docs**: Merge useful info into handover document

---

## 🗂️ **NEW FILE STRUCTURE (Post-Consolidation)**

### **Production Files (Keep & Rename)**
```
sql/mappings/
├── customer-orders-master-mapping.yaml              # Renamed from orders-unified-comprehensive
├── customer-orders-simple-mapping.yaml              # Renamed from simple-orders
├── customer-orders-monday-columns.json              # Renamed from monday-column-ids
├── customer-canonical.yaml                          # Keep as-is (generic)
└── legacy/                                          # Archive folder
    ├── orders-unified-mapping.yaml                  # Moved from main folder
    ├── orders-unified-delta-sync-v3-mapping.yaml    # Moved from main folder
    ├── orders_unified_comprehensive_pipeline.yaml   # Moved from main folder
    ├── orders-monday-master.json                    # Moved from main folder
    ├── orders-monday-subitems.json                  # Moved from main folder
    ├── data_mapping.yaml                            # Moved from utils/
    ├── field_mapping_matrix.yaml                    # Moved from docs/mapping/
    ├── monday_column_ids.json                       # Moved from docs/mapping/
    ├── customer_mapping.yaml                        # Moved from docs/mapping/
    └── mapping_fields.yaml                          # Moved from docs/mapping/

docs/
├── CUSTOMER_ORDERS_PIPELINE_HANDOVER.md             # Master handover document
├── HYBRID_SNAPSHOT_ARCHITECTURE.md                  # Keep (still relevant)
└── archive/
    └── customer-orders/                             # Archive folder
        ├── MAPPING_ANALYSIS_COMPREHENSIVE_REPORT.md
        ├── ORDERS_UNIFIED_BACKWARD_MAPPING_COMPREHENSIVE.md
        ├── SCHEMA_VALIDATION_CRITICAL_ISSUES.md
        ├── SCHEMA_VALIDATION_IMPLEMENTATION_PLAN.md
        ├── YAML_MAPPING_FORMAT_DECISION.md
        ├── orders_unified_monday_comparison.md
        ├── subitems_monday_api_mapping.md
        └── IMPLEMENTATION_CHECKLIST.md

docs/mapping/                                        # DELETE ENTIRE FOLDER
```

### **Updated References**
```
scripts/
├── order_sync_v2.py                                # Update to use renamed mapping files
├── customer_master_schedule/                        # Update imports and references
└── monday-boards/                                  # Update Monday.com integration

utils/
├── mapping_helper.py                               # Update to use new file names
└── hybrid_snapshot_manager.py                      # Update references

workflows/
└── customer-orders-*.yml                           # Update file paths in workflows
```

---

## 🚀 **Implementation Steps**

### **Phase 1: Create Archive Structure**
```powershell
# Create archive directories
New-Item -ItemType Directory -Path "sql/mappings/legacy" -Force
New-Item -ItemType Directory -Path "docs/archive/customer-orders" -Force
```

### **Phase 2: Rename Primary Files**
```powershell
# Rename main mapping files to customer-orders naming
Move-Item "sql/mappings/orders-unified-comprehensive-mapping.yaml" "sql/mappings/customer-orders-master-mapping.yaml"
Move-Item "sql/mappings/simple-orders-mapping.yaml" "sql/mappings/customer-orders-simple-mapping.yaml"
Move-Item "sql/mappings/monday-column-ids.json" "sql/mappings/customer-orders-monday-columns.json"
```

### **Phase 3: Archive Legacy Mapping Files**
```powershell
# Move outdated mapping files to legacy folder
Move-Item "sql/mappings/orders-unified-mapping.yaml" "sql/mappings/legacy/"
Move-Item "sql/mappings/orders-unified-delta-sync-v3-mapping.yaml" "sql/mappings/legacy/"
Move-Item "sql/mappings/orders_unified_comprehensive_pipeline.yaml" "sql/mappings/legacy/"
Move-Item "sql/mappings/orders-monday-master.json" "sql/mappings/legacy/"
Move-Item "sql/mappings/orders-monday-subitems.json" "sql/mappings/legacy/"
Move-Item "utils/data_mapping.yaml" "sql/mappings/legacy/"
```

### **Phase 4: Archive Documentation Files**
```powershell
# Move completed/outdated docs to archive
Move-Item "docs/MAPPING_ANALYSIS_COMPREHENSIVE_REPORT.md" "docs/archive/customer-orders/"
Move-Item "docs/ORDERS_UNIFIED_BACKWARD_MAPPING_COMPREHENSIVE.md" "docs/archive/customer-orders/"
Move-Item "docs/SCHEMA_VALIDATION_CRITICAL_ISSUES.md" "docs/archive/customer-orders/"
Move-Item "docs/SCHEMA_VALIDATION_IMPLEMENTATION_PLAN.md" "docs/archive/customer-orders/"
Move-Item "docs/YAML_MAPPING_FORMAT_DECISION.md" "docs/archive/customer-orders/"
```

### **Phase 5: Delete Duplicate Mapping Folder**
```powershell
# Move docs/mapping/ files to archive, then delete folder
Move-Item "docs/mapping/*" "docs/archive/customer-orders/"
Remove-Item "docs/mapping/" -Recurse -Force
```

### **Phase 6: Update Code References**
1. **Update Python imports** in all scripts to use new file names
2. **Update workflow YAML files** to reference new paths
3. **Update configuration files** with new mapping file names
4. **Update VS Code tasks** if they reference specific files

---

## 🔄 **File-by-File Action Plan**

### **✅ KEEP & RENAME**
| Current File | New Location | Action | Reason |
|-------------|-------------|---------|---------|
| `sql/mappings/orders-unified-comprehensive-mapping.yaml` | `sql/mappings/customer-orders-master-mapping.yaml` | RENAME | 95% accuracy, production ready |
| `sql/mappings/simple-orders-mapping.yaml` | `sql/mappings/customer-orders-simple-mapping.yaml` | RENAME | Current simplified approach |
| `sql/mappings/monday-column-ids.json` | `sql/mappings/customer-orders-monday-columns.json` | RENAME | API reference, actively used |
| `docs/HYBRID_SNAPSHOT_ARCHITECTURE.md` | `docs/HYBRID_SNAPSHOT_ARCHITECTURE.md` | KEEP | Still relevant architecture |
| `docs/CUSTOMER_ORDERS_PIPELINE_HANDOVER.md` | `docs/CUSTOMER_ORDERS_PIPELINE_HANDOVER.md` | KEEP | New master document |

### **📁 ARCHIVE (Move to Legacy)**
| Current File | Archive Location | Reason |
|-------------|------------------|---------|
| `sql/mappings/orders-unified-mapping.yaml` | `sql/mappings/legacy/` | Superseded by comprehensive mapping |
| `sql/mappings/orders-unified-delta-sync-v3-mapping.yaml` | `sql/mappings/legacy/` | Merged into comprehensive mapping |
| `sql/mappings/orders_unified_comprehensive_pipeline.yaml` | `sql/mappings/legacy/` | Pipeline details moved to handover doc |
| `sql/mappings/orders-monday-master.json` | `sql/mappings/legacy/` | Replaced by simplified approach |
| `sql/mappings/orders-monday-subitems.json` | `sql/mappings/legacy/` | Subitems handled differently now |
| `utils/data_mapping.yaml` | `sql/mappings/legacy/` | Legacy mapping approach |
| `docs/MAPPING_ANALYSIS_COMPREHENSIVE_REPORT.md` | `docs/archive/customer-orders/` | Analysis complete, superseded |
| `docs/ORDERS_UNIFIED_BACKWARD_MAPPING_COMPREHENSIVE.md` | `docs/archive/customer-orders/` | Backward mapping no longer needed |
| `docs/SCHEMA_VALIDATION_CRITICAL_ISSUES.md` | `docs/archive/customer-orders/` | Issues resolved |
| `docs/SCHEMA_VALIDATION_IMPLEMENTATION_PLAN.md` | `docs/archive/customer-orders/` | Implementation complete |
| `docs/YAML_MAPPING_FORMAT_DECISION.md` | `docs/archive/customer-orders/` | Decision made and implemented |

### **❌ DELETE (Duplicates)**
| Current File | Reason for Deletion |
|-------------|-------------------|
| `docs/mapping/orders_unified_monday_mapping.yaml` | Exact duplicate of sql/mappings/ version |
| `docs/mapping/monday_column_ids.json` | Exact duplicate of sql/mappings/ version |
| `docs/mapping/field_mapping_matrix.yaml` | Fragment, data merged into comprehensive |
| `docs/mapping/customer_mapping.yaml` | Incomplete, superseded by comprehensive |
| `docs/mapping/mapping_fields.yaml` | Fragment, data merged into comprehensive |
| `docs/mapping/orders_unified_monday_comparison.md` | Outdated analysis |
| `docs/mapping/subitems_monday_api_mapping.md` | Legacy approach no longer used |
| `docs/mapping/IMPLEMENTATION_CHECKLIST.md` | Checklist items completed |

---

## 🔧 **Code Update Requirements**

### **Files Requiring Import Updates**
```python
# Files that import mapping configurations
scripts/order_sync_v2.py                    # Update mapping file paths
scripts/customer_master_schedule/add_order.py
scripts/monday-boards/sync_board_groups.py
utils/mapping_helper.py                     # Update default file paths
utils/hybrid_snapshot_manager.py
```

### **Configuration Updates**
```yaml
# utils/config.yaml - Update mapping file references
mapping_files:
  master: "sql/mappings/customer-orders-master-mapping.yaml"
  simple: "sql/mappings/customer-orders-simple-mapping.yaml"
  monday_columns: "sql/mappings/customer-orders-monday-columns.json"
```

### **Workflow Updates**
```yaml
# workflows/*.yml - Update file paths
- name: "Load Mapping Configuration"
  task: "load_file"
  file: "sql/mappings/customer-orders-master-mapping.yaml"
```

---

## ✅ **Validation Checklist**

### **Pre-Implementation Validation**
- [ ] Backup current workspace before changes
- [ ] Verify all mapping files are accurately inventoried
- [ ] Confirm no critical files missed in analysis
- [ ] Test current functionality before changes

### **Post-Implementation Validation**
- [ ] All scripts run without import errors
- [ ] Mapping files load correctly in applications
- [ ] VS Code tasks execute successfully
- [ ] Kestra workflows process correctly
- [ ] No broken links in documentation
- [ ] Archive folders properly organized

### **Regression Testing**
- [ ] Run `Pipeline: Order Sync V2` task
- [ ] Execute `Test Refactored Monday Script` task
- [ ] Validate `Ops: Validate Environment` task
- [ ] Test hybrid snapshot functionality
- [ ] Confirm Monday.com API integration

---

## 📋 **Risk Assessment**

### **Low Risk**
- Moving documentation files to archive (no code impact)
- Renaming mapping files (controlled update path)
- Creating new directory structure

### **Medium Risk**
- Updating Python import statements (can cause runtime errors)
- Modifying configuration file paths (affects all scripts)
- Updating workflow YAML files (affects orchestration)

### **Mitigation Strategies**
1. **Backup Strategy**: Create full workspace backup before implementation
2. **Staged Rollout**: Implement changes in phases with validation
3. **Rollback Plan**: Keep original files until validation complete
4. **Testing**: Comprehensive testing after each phase

---

## 🚀 **Implementation Timeline**

### **Day 1: Preparation & Backup**
- Create workspace backup
- Create archive directory structure
- Validate current functionality baseline

### **Day 2: File Reorganization**
- Rename primary mapping files
- Move legacy files to archive
- Delete duplicate documentation

### **Day 3: Code Updates**
- Update Python import statements
- Modify configuration file paths
- Update workflow YAML files

### **Day 4: Testing & Validation**
- Run comprehensive test suite
- Validate all VS Code tasks
- Test Kestra workflow execution
- Confirm Monday.com API integration

### **Day 5: Documentation & Cleanup**
- Update remaining documentation references
- Clean up any missed file references
- Final validation and sign-off

---

**STATUS**: ✅ Ready for Implementation | **APPROVAL**: Required before execution  
**NEXT STEP**: Update ops YAML task to reflect new scope and deliverables
