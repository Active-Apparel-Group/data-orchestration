# Power BI Operations - File Organization Strategy

**Date:** July 17, 2025 | **Status:** Ready for Implementation  
**Context:** Post-breakthrough file consolidation and domain organization

---

## 🎯 Current State Analysis

### **Breakthrough Achievement:**
- ✅ **Gen1 Dataflow Refresh Working** via Power Automate SAS URL approach
- ✅ **HTTP 202 Success** - Flow triggering dataflow refresh successfully  
- ✅ **Production Ready** - Can be deployed immediately to fill ORDER_LIST pipeline gap

### **File Organization Challenge:**
- **powerbi folder:** 20+ files mixing production code with test/debug scripts
- **load_order_list folder:** Contains existing `order_list_dataflow_refresh.py` needing replacement
- **Scattered implementations:** Working solutions mixed with experimental code
- **Missing domain structure:** No clear separation between production vs development files

---

## 📋 File Organization Plan

### **Phase 1: Immediate Production Files (Next 2 Hours)**

#### **🚀 PRIORITY: Replace ORDER_LIST Dataflow Refresh**

**Current File:**
```
pipelines/scripts/load_order_list/order_list_dataflow_refresh.py
```

**Action:** Replace with SAS URL approach from `test_power_automate_sas.py`
- Convert successful test script to production-ready implementation
- Maintain existing logging and import patterns for Kestra compatibility
- Add comprehensive error handling and retry logic
- Include configuration support for different environments

**Implementation Steps:**
1. Copy working logic from `test_power_automate_sas.py`
2. Enhance with production logging using `logger_helper`
3. Add configuration loading using `db_helper.load_config()`
4. Include error handling and status validation
5. Test with existing Kestra workflow integration

---

### **Phase 2: Domain Organization (Next 24 Hours)**

#### **🏗️ CREATE: PowerBI Domain Structure**

**Target Structure:**
```
pipelines/scripts/powerbi/
├── 📁 core/                        # Production implementations
│   ├── powerbi_manager.py          # Enhanced universal manager
│   ├── dataflow_refresh_gen1.py    # Gen1 SAS URL operations  
│   ├── dataflow_refresh_gen2.py    # Gen2 REST API operations
│   └── resource_discovery.py       # Workspace/resource listing
├── 📁 operations/                  # Specific operation scripts
│   ├── refresh_dataflow.py         # Enhanced existing script
│   └── batch_operations.py         # Batch processing utilities
└── 📁 utils/                      # PowerBI-specific utilities
    ├── auth_helper.py              # PowerBI authentication utilities
    └── config_loader.py            # PowerBI configuration management
```

#### **🔧 CREATE: Auth Domain for Kestra**

**Target Structure:**
```
pipelines/scripts/auth/
├── token_manager.py                # Universal token operations
├── token_refresh.py                # Kestra-compatible refresh workflows
├── credential_validator.py         # Validation and diagnostics
├── service_principal_ops.py        # Service principal management
└── database_token_storage.py       # Enhanced DB token operations
```

#### **🧪 ORGANIZE: Test and Debug Files**

**Target Structure:**
```
tests/powerbi/
├── 📁 debug/                       # Debug and diagnostic scripts
│   ├── debug_power_automate_auth.py
│   ├── test_*.py                   # All test files
│   └── diagnostic_*.py             # All diagnostic files
├── 📁 archive/                     # Obsolete files for reference
│   └── [obsolete experimental files]
└── 📁 integration/                 # Integration tests
    ├── test_gen1_dataflow_refresh.py
    └── test_kestra_integration.py
```

---

### **Phase 3: File Movement Strategy**

#### **🎯 KEEP & ENHANCE (Priority Production Files)**

**Files to Keep in powerbi/core/:**
1. **`powerbi_manager.py`** → Enhanced as universal manager
   - Current: Basic implementation
   - Enhancement: Add Gen1 SAS URL support, Gen2 REST API, resource discovery
   
2. **`load_tokens.py`** → Move to auth domain as enhanced token CLI
   - Current: PowerBI-specific token loading
   - Enhancement: Universal token management across all Azure services

#### **🔄 MOVE TO DEBUG (Test/Development Files)**

**Files to Move to tests/powerbi/debug/:**
```
test_power_automate_configured.py   → tests/powerbi/debug/
test_power_automate_simple_check.py → tests/powerbi/debug/
debug_power_automate_auth.py        → tests/powerbi/debug/
test_power_automate_sas.py          → tests/powerbi/debug/ (keep working prototype)
[Additional test_*.py files]         → tests/powerbi/debug/
```

#### **🗑️ ARCHIVE (Obsolete Files)**

**Files to Move to tests/powerbi/archive/:**
```
[Experimental OAuth implementations that didn't work]
[Obsolete diagnostic scripts]
[Failed authentication approaches]
```

#### **🏗️ CREATE NEW (Production Enhancements)**

**New Files to Create:**
1. **`pipelines/scripts/powerbi/core/dataflow_refresh_gen1.py`**
   - Production-ready Gen1 dataflow refresh using SAS URL
   - Based on successful `test_power_automate_sas.py` prototype
   - Enhanced with configuration, logging, error handling

2. **`pipelines/scripts/auth/token_manager.py`**
   - Universal token management for all Azure services
   - Kestra-compatible workflows
   - Database integration for credential storage

3. **`pipelines/scripts/auth/service_principal_validator.py`**
   - Validate service principal setup and permissions
   - Diagnostic utilities for authentication troubleshooting

---

## 🔧 Implementation Sequence

### **Step 1: Critical Production Replacement (Immediate)**
```powershell
# 1. Backup existing file
Copy-Item "pipelines/scripts/load_order_list/order_list_dataflow_refresh.py" "pipelines/scripts/load_order_list/order_list_dataflow_refresh.py.backup"

# 2. Create enhanced production version from working prototype
# (Convert test_power_automate_sas.py to production script)

# 3. Test with existing Kestra workflow
# 4. Deploy and validate first production run
```

### **Step 2: Domain Creation (Next 4 Hours)**
```powershell
# 1. Create domain folders
New-Item -Path "pipelines/scripts/powerbi/core" -ItemType Directory -Force
New-Item -Path "pipelines/scripts/powerbi/operations" -ItemType Directory -Force  
New-Item -Path "pipelines/scripts/powerbi/utils" -ItemType Directory -Force
New-Item -Path "pipelines/scripts/auth" -ItemType Directory -Force

# 2. Create test organization folders
New-Item -Path "tests/powerbi/debug" -ItemType Directory -Force
New-Item -Path "tests/powerbi/archive" -ItemType Directory -Force
New-Item -Path "tests/powerbi/integration" -ItemType Directory -Force
```

### **Step 3: File Movement and Enhancement (Next 8 Hours)**
```powershell
# 1. Move debug/test files to appropriate test folders
# 2. Enhance core production files
# 3. Create new auth domain utilities
# 4. Update all import statements
# 5. Test all moved and enhanced files
```

### **Step 4: Integration and Validation (Next 12 Hours)**
```powershell
# 1. Update Kestra workflows with new file paths
# 2. Test ORDER_LIST pipeline with new dataflow refresh
# 3. Validate all production operations
# 4. Update documentation and runbooks
```

---

## 📊 Before/After Comparison

### **Before: Disorganized State**
```
pipelines/scripts/powerbi/
├── powerbi_manager.py              # Production + many test files mixed
├── test_power_automate_sas.py      # WORKING PROTOTYPE (success!)
├── test_power_automate_*.py        # Multiple test variations
├── debug_power_automate_auth.py    # Debug files
├── load_tokens.py                  # Token management
└── [15+ other mixed files]

pipelines/scripts/load_order_list/
└── order_list_dataflow_refresh.py  # NEEDS REPLACEMENT (old approach)
```

### **After: Clean Domain Organization**
```
pipelines/scripts/powerbi/core/
├── powerbi_manager.py              # Enhanced universal manager
├── dataflow_refresh_gen1.py        # NEW: Production Gen1 refresh
└── dataflow_refresh_gen2.py        # Enhanced Gen2 operations

pipelines/scripts/auth/
├── token_manager.py                # Universal token operations
├── token_refresh.py                # Kestra workflows
└── service_principal_ops.py        # Service principal management

pipelines/scripts/load_order_list/
└── order_list_dataflow_refresh.py  # REPLACED: SAS URL approach

tests/powerbi/debug/
├── test_power_automate_sas.py      # Working prototype preserved
└── [All test and debug files]
```

---

## 🎯 Success Criteria

### **Phase 1 Success (Production Ready):**
- ✅ ORDER_LIST dataflow refresh working with new SAS URL approach
- ✅ Kestra workflow integration maintained and functional
- ✅ Production logging and error handling implemented
- ✅ First successful production run validated

### **Phase 2 Success (Domain Organization):**
- ✅ Clean separation between production and development code
- ✅ PowerBI domain properly structured for future expansion
- ✅ Auth domain created for Kestra-compatible token workflows
- ✅ All test files organized and accessible for debugging

### **Phase 3 Success (Platform Foundation):**
- ✅ Enhanced production scripts supporting both Gen1 and Gen2 operations
- ✅ Universal token management system operational
- ✅ Configuration-driven resource management implemented
- ✅ Documentation updated and team trained on new structure

---

## 🚨 Risk Mitigation

### **Production Continuity:**
- **Backup Strategy:** All existing files backed up before replacement
- **Rollback Plan:** Preserve working `test_power_automate_sas.py` as reference
- **Testing Protocol:** Validate each file movement and enhancement
- **Kestra Integration:** Maintain existing logging and import patterns

### **File Organization Risks:**
- **Import Dependencies:** Update all import statements systematically
- **Path References:** Check all script references and VS Code tasks
- **Configuration Files:** Update any hardcoded file paths
- **Documentation:** Update all references to moved files

---

*This organization strategy transforms our breakthrough achievement into a production-ready, scalable platform while maintaining operational continuity.*
