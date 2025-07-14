# ORDER_LIST Pipeline - VS Code Tasks Reference

**Version**: 1.0  
**Date**: July 10, 2025  
**Purpose**: Quick reference for VS Code task execution

## 🎮 How to Execute Tasks

### Method 1: Command Palette (Recommended)
1. Press `Ctrl+Shift+P` (Windows) or `Cmd+Shift+P` (Mac)
2. Type "Tasks: Run Task"
3. Select from available ORDER_LIST tasks

### Method 2: Terminal Menu
1. Go to `Terminal` → `Run Task...`
2. Select desired ORDER_LIST task

### Method 3: Keyboard Shortcut
1. Press `Ctrl+Shift+P` → "Tasks: Configure Task"
2. Add custom keybindings for frequently used tasks

---

## 🚀 Production Tasks

### 📋 Primary Production Execution
```json
"ORDER_LIST: Execute Complete Pipeline"
```
- **Purpose**: Full production pipeline (Extract → Transform → Load)
- **Runtime**: ~6 minutes
- **Files**: All 45 customer files
- **Use Case**: Daily production runs
- **Command**: `python pipelines/scripts/load_order_list/order_list_pipeline.py`

### 🧪 Test Mode Execution  
```json
"ORDER_LIST: Complete Pipeline (Test Mode)"
```
- **Purpose**: Limited pipeline for testing
- **Runtime**: ~1 minute
- **Files**: 5 files maximum
- **Use Case**: Validation before production
- **Command**: `python pipelines/scripts/load_order_list/order_list_pipeline.py --limit-files 5`

---

## 🔧 Development Tasks

### ⚡ Extract Only
```json
"ORDER_LIST: Extract Only Pipeline"
```
- **Purpose**: Extract stage only (blob → raw tables)
- **Runtime**: ~3.5 minutes
- **Use Case**: Extract testing, data refresh
- **Command**: `python pipelines/scripts/load_order_list/order_list_pipeline.py --extract-only`

### 🔄 Transform Only
```json
"ORDER_LIST: Transform Only Pipeline"  
```
- **Purpose**: Transform existing raw tables
- **Runtime**: ~2 minutes
- **Use Case**: Schema testing, transformation debugging
- **Command**: `python pipelines/scripts/load_order_list/order_list_pipeline.py --transform-only`

### ✅ Validation Only
```json
"ORDER_LIST: Validation Only"
```
- **Purpose**: Data quality validation on current table
- **Runtime**: ~5 seconds
- **Use Case**: Data quality assessment
- **Command**: `python pipelines/scripts/load_order_list/order_list_pipeline.py --validation-only`

---

## 🧪 Testing Framework Tasks

### 📊 Comprehensive Testing
```json
"ORDER_LIST: Comprehensive Test Suite"
```
- **Purpose**: 5-phase validation framework
- **Runtime**: ~8 minutes
- **Use Case**: Complete pipeline validation
- **Command**: `python tests/end_to_end/test_order_list_complete_pipeline.py`

### ⚡ Limited Testing
```json
"ORDER_LIST: Test Suite (Limited)"
```
- **Purpose**: Test framework with 3-file limit
- **Runtime**: ~3 minutes
- **Use Case**: Fast validation cycle
- **Command**: `python tests/end_to_end/test_order_list_complete_pipeline.py --limit-files 3`

---

## 🎯 Task Selection Guide

### 🟢 Daily Operations
```
For regular production runs:
→ "ORDER_LIST: Execute Complete Pipeline"
```

### 🟡 Development & Testing
```
For development work:
→ "ORDER_LIST: Complete Pipeline (Test Mode)"
→ "ORDER_LIST: Transform Only Pipeline" 

For debugging specific stages:
→ "ORDER_LIST: Extract Only Pipeline"
→ "ORDER_LIST: Validation Only"
```

### 🔵 Quality Assurance
```
Before production deployment:
→ "ORDER_LIST: Comprehensive Test Suite"

For quick validation:
→ "ORDER_LIST: Test Suite (Limited)"
```

---

## 📊 Expected Output Examples

### ✅ Successful Execution
```
[*] ORDER_LIST PRODUCTION PIPELINE
============================================================
Pipeline ID: order_list_pipeline_20250710_233835
Start Time: 2025-07-10 23:38:35

[+] STAGE COMPLETED: EXTRACT
Files processed: 45
Records extracted: 101,662
Duration: 212.85 seconds

[+] STAGE COMPLETED: TRANSFORM  
Records transformed: 101,404
Duration: 119.50 seconds

[+] PIPELINE STATUS: SUCCESS
Total Duration: 334.92 seconds
```

### ⚠️ Validation Warning (Non-blocking)
```
[-] STAGE FAILED: VALIDATION
Error: Invalid column name 'CUSTOMER'
[!] Validation failed but pipeline will continue

[+] PIPELINE STATUS: SUCCESS
(Known issue: validation queries need column name updates)
```

### ❌ Critical Failure
```
[-] STAGE FAILED: EXTRACT
Error: Could not connect to Azure Blob Storage
[!] Pipeline terminated

Troubleshooting:
1. Check Azure credentials
2. Verify network connectivity
3. Review authentication settings
```

---

## 🔧 Task Customization

### Adding Custom Parameters
```json
// Example: Custom file limit
{
    "label": "ORDER_LIST: Custom File Limit",
    "type": "shell",
    "command": "python",
    "args": [
        "pipelines/scripts/load_order_list/order_list_pipeline.py",
        "--limit-files",
        "${input:fileLimit}"
    ],
    "group": "build"
}
```

### Environment Variables
```json
// Example: Custom database target
{
    "label": "ORDER_LIST: Development Environment",
    "type": "shell", 
    "command": "python",
    "args": ["pipelines/scripts/load_order_list/order_list_pipeline.py"],
    "options": {
        "env": {
            "DB_ENV": "development"
        }
    }
}
```

---

## 🚨 Common Issues & Solutions

### Task Not Found
```
Problem: Task doesn't appear in list
Solution: 
1. Check .vscode/tasks.json exists
2. Reload VS Code window (Ctrl+Shift+P → "Developer: Reload Window")
3. Verify task syntax in tasks.json
```

### Permission Denied
```
Problem: "Access denied" when running tasks
Solution:
1. Run VS Code as Administrator (Windows)
2. Check file permissions in workspace
3. Verify virtual environment activation
```

### Python Not Found
```
Problem: "python is not recognized as internal or external command"
Solution:
1. Activate virtual environment first: .\.venv\Scripts\Activate.ps1
2. Use full Python path in task configuration
3. Add Python to system PATH
```

### Long Running Tasks
```
Problem: Task seems to hang or run very long
Solution:
1. Check terminal output for progress
2. Use Ctrl+C to cancel if needed
3. Try limited file version first
4. Check Azure/database connectivity
```

---

## 📋 Task Maintenance

### Regular Updates
- Review task performance monthly
- Update file limits based on data growth
- Add new tasks for emerging requirements
- Optimize task parameters for better performance

### Best Practices
- Always test with limited files first
- Monitor task output for errors
- Use descriptive task names
- Document any custom modifications
- Keep backup of working tasks.json

---

**📋 Document Control**
- **Created**: July 10, 2025
- **Last Updated**: July 10, 2025
- **Next Review**: August 10, 2025
- **Version**: 1.0
