# Power BI Operations - Immediate Action Plan

**Date:** July 17, 2025 | **Priority:** IMMEDIATE  
**Context:** Replace ORDER_LIST dataflow refresh with enhanced SAS URL approach

---

## 🎯 IMMEDIATE PRIORITY: Production Script Replacement

### **Current State Analysis:**
- ✅ **Working Prototype:** `test_power_automate_sas.py` achieves HTTP 202 success
- 🔄 **Production Script:** `order_list_dataflow_refresh.py` uses same SAS URL but overly complex
- ✅ **Kestra Compatible:** Existing script already uses correct import patterns and logging
- 🎯 **Goal:** Enhance existing script with simplified, reliable approach from working prototype

### **Key Insight:** 
The existing production script actually uses the **SAME SAS URL** as our successful test, but has unnecessary complexity. We need to simplify and enhance, not completely replace.

---

## 📋 Implementation Plan

### **Phase 1: Enhanced Production Script (Next 2 Hours)**

#### **🔧 APPROACH: Enhance, Don't Replace**
The current `order_list_dataflow_refresh.py` has:
- ✅ Correct SAS URL (same as working test)
- ✅ Proper Kestra-compatible logging
- ✅ Correct import patterns (pipelines/utils)
- ✅ Database integration for audit logging
- ❌ Overly complex error handling
- ❌ Verbose logging that obscures success/failure

#### **🎯 ENHANCEMENTS NEEDED:**

**1. Simplify Core Function:**
```python
def trigger_gen1_dataflow_refresh() -> bool:
    """
    Simplified Gen1 dataflow refresh using Power Automate SAS URL
    Returns: True if successful (HTTP 200/202), False otherwise
    """
    # Use exact approach from test_power_automate_sas.py
    # Maintain existing logging structure
    # Keep database audit logging
```

**2. Streamline Success Detection:**
```python
# Current: Complex status checking
# Enhanced: Simple HTTP 200/202 = success

if response.status_code in [200, 202]:
    logger.info("✅ Gen1 dataflow refresh triggered successfully")
    return True
```

**3. Preserve Audit Features:**
- Keep database logging for audit trail
- Maintain Kestra-compatible output format
- Preserve error handling for network issues

#### **🛠️ SPECIFIC CHANGES:**

**Replace `trigger_workflow()` function:**
```python
def trigger_workflow(payload: Optional[Dict[str, Any]] = None) -> requests.Response:
    """Enhanced based on successful test_power_automate_sas.py approach"""
    
    # Same SAS URL (already correct)
    logic_app_url = "https://prod-27.australiasoutheast.logic.azure.com:443/..."
    
    # Simplified headers
    headers = {'Content-Type': 'application/json'}
    
    # Simplified payload (based on working test)
    if payload is None:
        payload = {
            "trigger_type": "Gen1_Dataflow_Refresh",
            "dataflow_name": "Master Order List", 
            "workspace": "Data Admin",
            "timestamp": datetime.now().isoformat(),
            "source": "ORDER_LIST_pipeline"
        }
    
    # Simplified request (same as working test)
    response = requests.post(logic_app_url, headers=headers, json=payload, timeout=30)
    
    # Enhanced logging (preserve Kestra compatibility)
    if response.status_code in [200, 202]:
        logger.info("✅ Gen1 dataflow refresh triggered successfully")
    else:
        logger.error(f"❌ Failed: HTTP {response.status_code}")
    
    return response
```

---

### **Phase 2: File Organization (Next 4 Hours)**

#### **🏗️ CREATE: Domain Structure**

**1. Create Folders:**
```powershell
# PowerBI domain structure
New-Item -Path "pipelines/scripts/powerbi/core" -ItemType Directory -Force
New-Item -Path "pipelines/scripts/powerbi/operations" -ItemType Directory -Force
New-Item -Path "pipelines/scripts/powerbi/utils" -ItemType Directory -Force

# Auth domain for Kestra workflows
New-Item -Path "pipelines/scripts/auth" -ItemType Directory -Force

# Test organization
New-Item -Path "tests/powerbi/debug" -ItemType Directory -Force
New-Item -Path "tests/powerbi/archive" -ItemType Directory -Force
```

**2. Move Files to Proper Locations:**

**PowerBI Core (Production):**
```powershell
# Keep and enhance core production files
Move-Item "pipelines/scripts/powerbi/powerbi_manager.py" "pipelines/scripts/powerbi/core/"
Move-Item "pipelines/scripts/powerbi/refresh_dataflow.py" "pipelines/scripts/powerbi/operations/"

# Create new Gen1-specific file based on enhanced approach
# pipelines/scripts/powerbi/core/dataflow_refresh_gen1.py
```

**Test and Debug:**
```powershell
# Move all test files to debug folder
Move-Item "pipelines/scripts/powerbi/test_*.py" "tests/powerbi/debug/"
Move-Item "pipelines/scripts/powerbi/debug_*.py" "tests/powerbi/debug/"

# Keep working prototype as reference
# tests/powerbi/debug/test_power_automate_sas.py (preserve as working reference)
```

**Auth Domain:**
```powershell
# Move token management to auth domain
Move-Item "pipelines/scripts/powerbi/load_tokens.py" "pipelines/scripts/auth/token_manager.py"

# Create Kestra-compatible auth workflows
# pipelines/scripts/auth/token_refresh.py
# pipelines/scripts/auth/service_principal_ops.py
```

---

### **Phase 3: Integration and Testing (Next 8 Hours)**

#### **🧪 TESTING SEQUENCE:**

**1. Validate Enhanced Script:**
```bash
# Test enhanced ORDER_LIST dataflow refresh
python pipelines/scripts/load_order_list/order_list_dataflow_refresh.py

# Expected: HTTP 202, successful trigger, audit log entry
```

**2. Test Kestra Integration:**
```bash
# Run ORDER_LIST pipeline with new dataflow refresh
# Validate Kestra workflow compatibility
# Check logging output in Kestra format
```

**3. Validate Domain Organization:**
```bash
# Test all moved files have correct imports
# Validate VS Code tasks still work
# Check no broken dependencies
```

#### **🔍 VALIDATION CRITERIA:**

**Enhanced Script Success:**
- ✅ HTTP 202 response from Power Automate
- ✅ Simplified, clear logging output
- ✅ Database audit log entry created
- ✅ Kestra-compatible execution

**File Organization Success:**
- ✅ All production files in correct domain folders
- ✅ Test files organized in tests/powerbi/debug/
- ✅ Auth domain created with token management
- ✅ No broken import statements

**Integration Success:**
- ✅ ORDER_LIST pipeline works with enhanced script
- ✅ Kestra workflow execution successful
- ✅ VS Code tasks updated and functional
- ✅ Documentation reflects new structure

---

## 🎯 Detailed Implementation Steps

### **Step 1: Backup and Enhance (Immediate)**

```powershell
# 1. Backup current production script
Copy-Item "pipelines/scripts/load_order_list/order_list_dataflow_refresh.py" `
         "pipelines/scripts/load_order_list/order_list_dataflow_refresh.py.backup"

# 2. Enhance the script with simplified approach (keep same file)
# 3. Test the enhanced script
# 4. Validate with ORDER_LIST pipeline
```

### **Step 2: Create Domain Structure (Next 2 Hours)**

```powershell
# Create all domain folders
# Move files to appropriate locations  
# Update import statements
# Test all moved files
```

### **Step 3: Create New Production Files (Next 4 Hours)**

**Create:** `pipelines/scripts/powerbi/core/dataflow_refresh_gen1.py`
```python
"""
Gen1 Dataflow Refresh Operations
Purpose: Production-ready Gen1 dataflow refresh using Power Automate
"""
# Based on successful test_power_automate_sas.py approach
# Enhanced with configuration, logging, error handling
# Kestra-compatible execution
```

**Create:** `pipelines/scripts/auth/token_manager.py`
```python
"""
Universal Token Management for Azure Services
Purpose: Centralized token operations for Kestra workflows
"""
# Enhanced version of load_tokens.py
# Support for multiple Azure services
# Kestra-compatible token refresh workflows
```

### **Step 4: Update VS Code Tasks (Next 1 Hour)**

```json
// Update .vscode/tasks.json with new file locations
{
    "label": "ORDER_LIST: Test Enhanced Dataflow Refresh",
    "type": "shell",
    "command": "python",
    "args": ["pipelines/scripts/load_order_list/order_list_dataflow_refresh.py"],
    "detail": "Test enhanced Gen1 dataflow refresh with SAS URL approach"
}
```

---

## 🚨 Risk Mitigation

### **Production Continuity:**
- **Backup Strategy:** Original script backed up before enhancement
- **Rollback Plan:** Simple revert to backup if issues occur
- **Testing Protocol:** Validate each enhancement before deployment
- **Monitoring:** Check ORDER_LIST pipeline execution post-enhancement

### **File Movement Risks:**
- **Import Dependencies:** Test all import statements after moves
- **Path References:** Update VS Code tasks and documentation
- **Kestra Workflows:** Validate no path changes affect Kestra execution

### **Integration Risks:**
- **Database Dependencies:** Preserve audit logging functionality
- **Configuration:** Maintain compatibility with existing config.yaml
- **Error Handling:** Preserve Kestra-compatible error reporting

---

## 📊 Success Metrics

### **Phase 1 Success (Enhanced Script):**
- ✅ HTTP 202 response from enhanced script
- ✅ Simplified, clear execution output
- ✅ Successful ORDER_LIST pipeline integration
- ✅ Database audit logging functional

### **Phase 2 Success (File Organization):**
- ✅ Clean domain-based folder structure
- ✅ Production vs test code clearly separated
- ✅ Auth domain created for Kestra workflows
- ✅ All import statements working correctly

### **Phase 3 Success (Integration):**
- ✅ All VS Code tasks updated and functional
- ✅ Kestra workflows using enhanced approach
- ✅ Documentation updated with new structure
- ✅ Team confident with organized codebase

---

## 🔄 Next Steps After Completion

### **Immediate Value (Today):**
- Gen1 dataflow refresh working reliably in ORDER_LIST pipeline
- Clean, organized codebase ready for expansion
- Foundation for additional Power BI operations

### **Short Term (Next Week):**
- Gen2 dataflow operations via REST API
- Enhanced batch processing capabilities
- Additional Power BI resource management

### **Medium Term (Next Month):**
- Full Power Platform operations support
- Advanced monitoring and alerting
- Comprehensive automation workflows

---

*This action plan transforms our breakthrough success into a production-ready, scalable foundation while maintaining operational continuity and following project standards.*
