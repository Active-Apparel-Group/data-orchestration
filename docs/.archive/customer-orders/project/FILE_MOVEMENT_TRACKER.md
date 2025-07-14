# File Movement Tracker - Customer Orders Consolidation
**Generated**: January 2025 | **Purpose**: Track file reorganization progress  
**Status**: 🚧 In Progress

---

## 📋 **Movement Progress Tracker**

### **Phase 1: Legacy Mapping Files** (Priority: High)

| File Name | Current Location | Destination | Status | Validation | Notes |
|-----------|------------------|-------------|---------|------------|-------|
| `orders-unified-mapping.yaml` | `sql/mappings/` | `sql/mappings/legacy/` | ⏳ Pending | ❌ | Archive legacy mapping |
| `orders-unified-delta-sync-v3-mapping.yaml` | `sql/mappings/` | `sql/mappings/legacy/` | ⏳ Pending | ❌ | Archive legacy mapping |
| `orders_unified_comprehensive_pipeline.yaml` | `sql/mappings/` | `sql/mappings/legacy/` | ⏳ Pending | ❌ | Archive legacy mapping |
| `orders-monday-master.json` | `sql/mappings/` | `sql/mappings/legacy/` | ⏳ Pending | ❌ | Archive legacy JSON |
| `orders-monday-subitems.json` | `sql/mappings/` | `sql/mappings/legacy/` | ⏳ Pending | ❌ | Archive legacy JSON |
| `data_mapping.yaml` | `utils/` | `sql/mappings/legacy/` | ⏳ Pending | ❌ | Move config to archive |

### **Phase 2: Duplicate Documentation Files** (Priority: High)

| File Name | Current Location | Destination | Status | Validation | Notes |
|-----------|------------------|-------------|---------|------------|-------|
| `orders_unified_monday_mapping.yaml` | `docs/mapping/` | `DELETE` | ⏳ Pending | ❌ | Duplicate - remove |
| `field_mapping_matrix.yaml` | `docs/mapping/` | `sql/mappings/legacy/` | ⏳ Pending | ❌ | Archive fragment |
| `monday_column_ids.json` | `docs/mapping/` | `DELETE` | ⏳ Pending | ❌ | Duplicate - remove |
| `customer_mapping.yaml` | `docs/mapping/` | `sql/mappings/legacy/` | ⏳ Pending | ❌ | Archive incomplete |
| `mapping_fields.yaml` | `docs/mapping/` | `sql/mappings/legacy/` | ⏳ Pending | ❌ | Archive fragment |

### **Phase 3: Rename Production Files** (Priority: Medium)

| File Name | Current Location | New Name | Status | Validation | Notes |
|-----------|------------------|----------|---------|------------|-------|
| `orders-unified-comprehensive-mapping.yaml` | `sql/mappings/` | `customer-orders-master-mapping.yaml` | ⏳ Pending | ❌ | Rename primary mapping |
| `simple-orders-mapping.yaml` | `sql/mappings/` | `customer-orders-simple-mapping.yaml` | ⏳ Pending | ❌ | Rename simplified mapping |
| `monday-column-ids.json` | `sql/mappings/` | `customer-orders-monday-columns.json` | ⏳ Pending | ❌ | Rename API reference |

### **Phase 4: Documentation Archive** (Priority: Low)

| File Name | Current Location | Destination | Status | Validation | Notes |
|-----------|------------------|-------------|---------|------------|-------|
| `MAPPING_ANALYSIS_COMPREHENSIVE_REPORT.md` | `docs/` | `docs/archive/customer-orders/` | ⏳ Pending | ❌ | Archive analysis |
| `ORDERS_UNIFIED_BACKWARD_MAPPING_COMPREHENSIVE.md` | `docs/` | `docs/archive/customer-orders/` | ⏳ Pending | ❌ | Archive analysis |
| `SCHEMA_VALIDATION_CRITICAL_ISSUES.md` | `docs/` | `docs/archive/customer-orders/` | ⏳ Pending | ❌ | Archive resolved issues |
| `SCHEMA_VALIDATION_IMPLEMENTATION_PLAN.md` | `docs/` | `docs/archive/customer-orders/` | ⏳ Pending | ❌ | Archive completed plan |
| `YAML_MAPPING_FORMAT_DECISION.md` | `docs/` | `docs/archive/customer-orders/` | ⏳ Pending | ❌ | Archive decision doc |

---

## 📊 **Progress Summary**

| Phase | Total Files | Completed | Pending | Success Rate |
|-------|-------------|-----------|---------|--------------|
| **Phase 1: Legacy Mappings** | 6 | 0 | 6 | 0% |
| **Phase 2: Duplicate Docs** | 5 | 0 | 5 | 0% |
| **Phase 3: Rename Production** | 3 | 0 | 3 | 0% |
| **Phase 4: Doc Archive** | 5 | 0 | 5 | 0% |
| **TOTAL** | **19** | **0** | **19** | **0%** |

---

## 🛠️ **Automation Commands**

### **Quick Commands for Each Phase**

```powershell
# Phase 1: Archive Legacy Mapping Files
New-Item -ItemType Directory -Path "sql\mappings\legacy" -Force
Move-Item "sql\mappings\orders-unified-mapping.yaml" "sql\mappings\legacy\" -Force
Move-Item "sql\mappings\orders-unified-delta-sync-v3-mapping.yaml" "sql\mappings\legacy\" -Force
Move-Item "sql\mappings\orders_unified_comprehensive_pipeline.yaml" "sql\mappings\legacy\" -Force
Move-Item "sql\mappings\orders-monday-master.json" "sql\mappings\legacy\" -Force
Move-Item "sql\mappings\orders-monday-subitems.json" "sql\mappings\legacy\" -Force
Move-Item "utils\data_mapping.yaml" "sql\mappings\legacy\" -Force

# Phase 2: Remove Duplicate Documentation Files  
Remove-Item "docs\mapping\orders_unified_monday_mapping.yaml" -Force
Remove-Item "docs\mapping\monday_column_ids.json" -Force
Move-Item "docs\mapping\field_mapping_matrix.yaml" "sql\mappings\legacy\" -Force
Move-Item "docs\mapping\customer_mapping.yaml" "sql\mappings\legacy\" -Force
Move-Item "docs\mapping\mapping_fields.yaml" "sql\mappings\legacy\" -Force

# Phase 3: Rename Production Files
Rename-Item "sql\mappings\orders-unified-comprehensive-mapping.yaml" "customer-orders-master-mapping.yaml" -Force
Rename-Item "sql\mappings\simple-orders-mapping.yaml" "customer-orders-simple-mapping.yaml" -Force  
Rename-Item "sql\mappings\monday-column-ids.json" "customer-orders-monday-columns.json" -Force

# Phase 4: Archive Documentation
New-Item -ItemType Directory -Path "docs\archive\customer-orders" -Force
Move-Item "docs\MAPPING_ANALYSIS_COMPREHENSIVE_REPORT.md" "docs\archive\customer-orders\" -Force
Move-Item "docs\ORDERS_UNIFIED_BACKWARD_MAPPING_COMPREHENSIVE.md" "docs\archive\customer-orders\" -Force
Move-Item "docs\SCHEMA_VALIDATION_CRITICAL_ISSUES.md" "docs\archive\customer-orders\" -Force
Move-Item "docs\SCHEMA_VALIDATION_IMPLEMENTATION_PLAN.md" "docs\archive\customer-orders\" -Force
Move-Item "docs\YAML_MAPPING_FORMAT_DECISION.md" "docs\archive\customer-orders\" -Force
```

---

## ✅ **Validation Checklist**

### **After Each Phase:**
- [ ] **Verify files moved successfully**
- [ ] **Check no broken references in code**
- [ ] **Update any hardcoded paths**
- [ ] **Test existing scripts still work**
- [ ] **Update documentation links**
- [ ] **Mark phase complete in tracker**

### **Final Validation:**
- [ ] **Run all VS Code tasks successfully**
- [ ] **Test dev/customer-orders/ scripts**
- [ ] **Verify no import errors**
- [ ] **Check all documentation links work**
- [ ] **Update CUSTOMER_ORDERS_PIPELINE_HANDOVER.md paths**

---

## 🚨 **Rollback Plan**

If any issues occur during movement:

```powershell
# Emergency rollback for each phase
git checkout HEAD -- sql/mappings/
git checkout HEAD -- docs/mapping/
git checkout HEAD -- utils/data_mapping.yaml
git checkout HEAD -- docs/
```

---

## 📝 **Update Instructions**

**To mark a file as complete:**
1. Execute the move command
2. Verify the file moved successfully  
3. Change Status from ⏳ Pending to ✅ Complete
4. Change Validation from ❌ to ✅ 
5. Add any notes about issues encountered

**Status Legend:**
- ⏳ Pending - Not yet processed
- 🚧 In Progress - Currently being moved
- ✅ Complete - Successfully moved and validated
- ❌ Failed - Move failed, needs attention
- 🔄 Rollback - Reverted due to issues
