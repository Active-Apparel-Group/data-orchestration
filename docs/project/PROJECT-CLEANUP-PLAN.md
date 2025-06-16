# 🧹 PROJECT ORGANIZATION & CLEANUP RULES

## 🎯 **GROUND RULES FOR CLEAN PROJECT STRUCTURE**

### 📁 **FOLDER STRUCTURE RULES:**

```
kestra-start/
├── 📋 workflows/           # All Kestra workflow YAML files  
├── 🐍 scripts/            # Python files for Kestra namespace
├── 📊 queries/            # SQL files for Kestra namespace
├── 🔧 tools/              # Helper PowerShell scripts & utilities
├── 🧪 tests/              # Test files and experimental code
├── 📚 docs/               # Documentation files
├── 🚀 .github/            # CI/CD workflows
├── 📁 _backup/            # Old/deprecated files
│
├── 🐳 docker-compose.yml  # Infrastructure (root level OK)
├── 📦 dockerfile          # Infrastructure (root level OK)  
├── 📝 requirements.txt    # Dependencies (root level OK)
├── 🔨 makefile           # Build automation (root level OK)
├── 🔐 .env*              # Environment (root level OK)
└── 📖 README.md          # Project info (root level OK)
```

### 🚨 **RULE #1: NO LOOSE FILES IN ROOT**
- ❌ **No `.ps1` scripts in root** (move to `tools/`)
- ❌ **No `.yml` workflows in root** (move to `workflows/`)  
- ❌ **No `.py` files in root** (move to `scripts/` or `tests/`)
- ❌ **No test/temp files in root** (move to `tests/` or delete)

### 🚨 **RULE #2: CLEAR NAMING CONVENTIONS**
- 🔧 **Tools**: `tools/deploy-workflows.ps1`, `tools/kestra-helper.ps1`
- 📋 **Workflows**: `workflows/database-connection.yml`, `workflows/data-processing.yml`
- 🐍 **Scripts**: `scripts/database_utils.py`, `scripts/data_processor.py`
- 🧪 **Tests**: `tests/test-deployment.ps1`, `tests/experiment-*.yml`

### 🚨 **RULE #3: ONE PURPOSE PER FOLDER**
- `scripts/` = Python files for Kestra execution only
- `tools/` = Development/deployment helper scripts only  
- `workflows/` = Production Kestra workflows only
- `tests/` = Experimental/test code only

## 🗑️ **IMMEDIATE CLEANUP NEEDED:**

### **Files to Move:**

#### 🔧 **PowerShell Scripts → `tools/`**
- `build.ps1` → `tools/build.ps1`
- `deployment-methods-summary.ps1` → `tools/deployment-methods-summary.ps1` 
- `simple-deployment-test.ps1` → `tools/simple-deployment-test.ps1`
- `test-deploy.ps1` → `tools/test-deploy.ps1`
- `test-deployment-methods.ps1` → `tools/test-deployment-methods.ps1`
- `test-kestra-deploy.ps1` → `tools/test-kestra-deploy.ps1`
- `working-deployment-methods.ps1` → `tools/working-deployment-methods.ps1`

#### 📋 **YAML Workflows → `workflows/`**
- `simple-test.yml` → `workflows/simple-test.yml`

#### 🐍 **Python Files → `scripts/`**
- `test_sql_with_env.py` → `scripts/test_sql_with_env.py` (move duplicate)

### **Files to Delete/Review:**
- Multiple similar deployment test scripts (consolidate)
- Duplicate Python files
- Experimental files that are no longer needed

## ✅ **CLEANUP EXECUTION PLAN:**

### **Phase 1: Move Files**
```powershell
# Move PowerShell tools
Move-Item "*.ps1" "tools/"

# Move workflows  
Move-Item "*.yml" "workflows/"

# Move Python files
Move-Item "*.py" "scripts/"
```

### **Phase 2: Consolidate**
- Keep only the working deployment scripts
- Remove duplicate/experimental files
- Update any references to moved files

### **Phase 3: Update Documentation**
- Update all documentation with new file paths
- Update CI/CD workflows with new paths
- Create clear README with new structure

## 🎯 **TARGET CLEAN STRUCTURE:**

```
kestra-start/
├── workflows/
│   ├── database-connection.yml
│   ├── data-processing.yml  
│   └── simple-test.yml
├── scripts/
│   ├── test_sql_with_env.py
│   └── test_sql_enhanced.py
├── tools/
│   ├── deploy-workflows.ps1      # Main deployment tool
│   ├── kestra-helper.ps1         # CLI helper
│   └── cleanup-namespace.ps1     # Utilities
├── tests/
│   └── experimental/             # Test workflows
├── docs/
│   ├── KESTRA-SETUP-NOTES.md
│   └── PROJECT-ORGANIZATION.md
└── [infrastructure files in root]
```

## 🎉 **BENEFITS OF CLEAN STRUCTURE:**

✅ **Easy to find files** - everything has a logical place
✅ **Clear separation** - production vs development vs testing  
✅ **Better CI/CD** - workflows know exactly what to deploy
✅ **Team collaboration** - new team members understand structure immediately
✅ **Maintenance** - easier to update and refactor

## 🚨 **ENFORCEMENT RULES:**

1. **Before committing**: Run cleanup check
2. **No exceptions**: All new files go in proper folders
3. **Regular reviews**: Weekly cleanup of root folder
4. **Documentation**: Update docs when structure changes

**Time to clean up! 🧹**
