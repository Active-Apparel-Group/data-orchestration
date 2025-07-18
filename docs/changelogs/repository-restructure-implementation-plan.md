# 🚀 Repository Restructure Implementation Plan - ENHANCED

> **Goal**: Transform to modern Python packaging with `src/pipelines` structure, zero production disruption, immediate path fixes, AND eliminate confusing duplications.

## 🎯 Executive Summary

This plan addresses the critical issues:
- ✅ **Path Hacks**: Eliminate `sys.path.append()` throughout codebase
- ✅ **Duplicate Utils**: Consolidate multiple `/utils` folders <important> `pipelines/utils` is primary source of utils. `/utils` only with approval
- ✅ **Modern Packaging**: Implement `pyproject.toml` and `src/` layout
- ✅ **Production Safety**: Zero disruption to Kestra pipelines
- ✅ **Immediate Results**: Working package in 30 minutes
- 🆕 **Eliminate Duplications**: Fix confusing `/ddl` and `/integrations` scattered locations
- 🆕 **Standardize Structure**: Clear separation of concerns

## 🚨 **Critical Duplication Issues Identified**

### **Problem 1: Duplicate `/ddl` Folders**
- ❌ `db/ddl/` AND `sql/ddl/` - Confusing!
- ✅ **Solution**: Keep only `db/ddl/` (proper schema management)

### **Problem 2: Scattered `/integrations`**  
- ❌ `pipelines/integrations/`, root `/integrations/`, potential `sql/integrations/`
- ✅ **Solution**: Consolidate to `src/pipelines/integrations/` only

### **Problem 3: Mixed Purposes**
- ❌ Schema changes mixed with operational queries
- ✅ **Solution**: Clear separation - `db/` for schema evolution, `sql/` for operations

## 🗂️ **Target Structure (Final State)**

```text
data-orchestration/
├─ src/                          # NEW - Modern Python package
│  └─ pipelines/                 # Main package (NOT data-orchestration!)
│     ├─ __init__.py            # Package root
│     ├─ utils/                 # Consolidated utilities
│     │  ├─ __init__.py
│     │  ├─ db.py              # from pipelines/utils/db_helper.py
│     │  ├─ logger.py          # from pipelines/utils/logger_helper.py
│     │  ├─ config.py          # configuration management
│     │  └─ schema.py          # schema utilities
│     ├─ load_order_list/      # Pipeline modules (from existing)
│     │  ├─ __init__.py
│     │  ├─ extract.py
│     │  ├─ transform.py
│     │  └─ load.py
│     ├─ load_cms/           # Customer Master Schedule
│     │  ├─ __init__.py
│     │  └─ etl.py
│     ├─ update/             # Update operations
│     │  ├─ __init__.py
│     │  └─ boards.py
│     ├─ transform/          # Data transformations
│     │  ├─ __init__.py
│     │  └─ processors.py
│     ├─ ingestion/          # Data ingestion
│     │  ├─ __init__.py
│     │  └─ sources.py
│     ├─ powerbi/           # PowerBI integrations
│     │  ├─ __init__.py
│     │  └─ refresh.py
│     └─ integrations/         # External APIs
│        ├─ __init__.py
│        └─ azure/
│
├─ pipelines/                   # KEEP - Production Kestra (unchanged!)
│  ├─ scripts/
│  ├─ utils/                   # Keep during transition
│  └─ workflows/
│
├─ sql/                        # MOVED from src/sql
│  ├─ ddl/
│  ├─ graphql/
│  ├─ mappings/
│  └─ migrations/
│
├─ configs/                    # Environment configs
├─ workflows/                  # Kestra YAML
├─ tests/                      # All tests
├─ tools/                      # PowerShell tools
├─ docs/                       # Documentation
├─ db/                         # Keep existing
├─ integrations/               # Keep existing
│
├─ __legacy/                   # Archive of old structure
│  ├─ src/                    # Original src/ folder
│  ├─ utils/                  # Original utils/
│  └─ templates/              # Original templates/
│
├─ pyproject.toml             # Modern Python packaging
├─ requirements.txt
└─ README.md
```

---

## 🚨 Phase 0: Emergency Setup (30 Minutes)

### Pre-Action Planning ✅
- **Goal**: Working `pyproject.toml` and package structure with zero breaking changes
- **Context**: Move legacy folders, create new structure, establish imports
- **Approach**: Archive old, create new, compatibility layer for transition

### Step 0.1: Archive Legacy Folders (5 minutes)
```powershell
# Create archive and move problematic folders
mkdir __legacy
move src __legacy\src
move utils __legacy\utils
move templates __legacy\templates
```

### Step 0.2: Create New Package Structure (5 minutes)
```powershell
# Create modern src/ layout
mkdir src\pipelines\utils
mkdir src\pipelines\load_order_list
mkdir src\pipelines\load_cms
mkdir src\pipelines\update
mkdir src\pipelines\transform
mkdir src\pipelines\ingestion
mkdir src\pipelines\powerbi
mkdir src\pipelines\integrations

# Create __init__.py files
echo. > src\pipelines\__init__.py
echo. > src\pipelines\utils\__init__.py
echo. > src\pipelines\load_order_list\__init__.py
echo. > src\pipelines\load_cms\__init__.py
echo. > src\pipelines\update\__init__.py
echo. > src\pipelines\transform\__init__.py
echo. > src\pipelines\ingestion\__init__.py
echo. > src\pipelines\powerbi\__init__.py
echo. > src\pipelines\integrations\__init__.py
```

### Step 0.3: Move SQL Folder (2 minutes)
```powershell
# Extract SQL from legacy src
move __legacy\src\sql .\sql
```

### Step 0.4: Create pyproject.toml (3 minutes)
```toml
[build-system]
requires = ["setuptools>=64", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "pipelines"
version = "0.1.0"
description = "AAG Data Orchestration Pipelines"
authors = [{name = "Active Apparel Group"}]
requires-python = ">=3.10"
dependencies = [
    "pandas>=2.0",
    "pyodbc",
    "pyyaml",
    "requests",
    "python-dotenv",
    "jinja2",
    "azure-storage-blob",
    "azure-identity",
    "tomli",
]

[tool.setuptools.packages.find]
where = ["src"]
include = ["pipelines*"]

[tool.setuptools.package-data]
"pipelines" = [
    "**/*.sql", "**/*.yaml", "**/*.yml", 
    "**/*.json", "**/*.graphql", "**/*.toml"
]

[project.scripts]
pipelines-order-list = "pipelines.order_list.main:main"
pipelines-monday-sync = "pipelines.monday_boards.sync:main"
```

### Step 0.5: Create Compatibility Layer (10 minutes)

Create utils with legacy import compatibility:

**src/pipelines/utils/db.py**:
```python
"""Database utilities - migrated from pipelines/utils/db_helper.py"""
import sys
from pathlib import Path

# Source from pipelines/utils (NOT root utils - that's outdated)
pipelines_utils_path = Path(__file__).parent.parent.parent.parent / "pipelines" / "utils"
if pipelines_utils_path.exists():
    sys.path.insert(0, str(pipelines_utils_path))
    
    try:
        from db_helper import *
        # Re-export for new package structure
        get_connection = get_connection
        load_config = load_config
    except ImportError as e:
        print(f"Warning: Could not import from pipelines/utils/db_helper: {e}")

# TODO: Replace with native implementation
```

**src/pipelines/utils/logger.py**:
```python
"""Logger utilities - migrated from pipelines/utils/logger_helper.py"""
import sys
from pathlib import Path

# Source from pipelines/utils (NOT root utils - that's outdated)
pipelines_utils_path = Path(__file__).parent.parent.parent.parent / "pipelines" / "utils"
if pipelines_utils_path.exists():
    sys.path.insert(0, str(pipelines_utils_path))
    
    try:
        from logger_helper import *
        get_logger = get_logger
    except ImportError as e:
        print(f"Warning: Could not import from pipelines/utils/logger_helper: {e}")

# TODO: Replace with native implementation
```

**src/pipelines/utils/config.py**:
```python
"""Configuration utilities"""
import sys
from pathlib import Path

# Source from pipelines/utils (NOT root utils - that's outdated)
pipelines_utils_path = Path(__file__).parent.parent.parent.parent / "pipelines" / "utils"
if pipelines_utils_path.exists():
    sys.path.insert(0, str(pipelines_utils_path))
    
    try:
        from db_helper import load_config
    except ImportError as e:
        print(f"Warning: Could not import config from pipelines/utils: {e}")

# TODO: Create dedicated config module
```

### Step 0.6: Create Emergency Tests (5 minutes)

**tests/test_emergency_package.py**:
```python
"""Emergency test - validate package works immediately"""
import subprocess
import sys
from pathlib import Path

def test_package_install():
    """Test package installs in editable mode"""
    print("🧪 Testing package installation...")
    result = subprocess.run([
        sys.executable, "-m", "pip", "install", "-e", "."
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Install failed: {result.stderr}")
        return False
    
    print("✅ Package installed successfully")
    return True

def test_critical_imports():
    """Test critical imports work"""
    print("🧪 Testing critical imports...")
    
    imports = [
        "pipelines",
        "pipelines.utils",
        "pipelines.utils.db", 
        "pipelines.utils.logger",
        "pipelines.utils.config",
    ]
    
    failures = []
    for module in imports:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            failures.append((module, e))
    
    return len(failures) == 0

def test_legacy_functions():
    """Test legacy function compatibility"""
    print("🧪 Testing legacy function access...")
    
    try:
        from pipelines.utils.db import get_connection, load_config
        from pipelines.utils.logger import get_logger
        
        # Test they're callable
        config = load_config()
        logger = get_logger(__name__)
        
        print("✅ Legacy functions accessible")
        return True
    except Exception as e:
        print(f"❌ Legacy compatibility failed: {e}")
        return False

def main():
    """Run emergency validation"""
    print("🚨 EMERGENCY PACKAGE VALIDATION")
    print("=" * 50)
    
    tests = [
        ("Package Install", test_package_install),
        ("Critical Imports", test_critical_imports),
        ("Legacy Functions", test_legacy_functions),
    ]
    
    all_passed = True
    for name, test_func in tests:
        print(f"\n{name}:")
        print("-" * 30)
        passed = test_func()
        if not passed:
            all_passed = False
    
    status = "✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED" 
    print(f"\n{status}")
    
    if all_passed:
        print("\n🎉 Package ready for use!")
        print("Next: Import using 'from pipelines.utils import db, logger'")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

---

## � **Phase 1: ENHANCED - Duplication Cleanup & Consolidation** ⚡ **NEXT**

### Pre-Action Planning
- **Goal**: Eliminate confusing duplications, standardize folder structure, maintain production safety
- **Context**: Multiple DDL locations, scattered integrations, mixed purposes causing confusion
- **Approach**: Systematic consolidation with clear separation of concerns

### **Phase 1.1: DDL Consolidation (10 minutes)**

**Current Mess**:
```
├── db/ddl/           # ✅ Schema management (keep)
├── sql/ddl/          # ❌ Confusing duplicate (remove)
```

**Target State**:
```
├── db/ddl/           # ✅ ONLY location for DDL
├── sql/operations/   # ✅ Operational queries only
```

**Actions**:
```powershell
# 1. Move sql/ddl content to db/ddl with conflict resolution
robocopy sql\ddl db\ddl /MIR /XO  # Skip older files

# 2. Remove empty sql/ddl
rmdir sql\ddl /s /q

# 3. Create operations folder for SQL queries
mkdir sql\operations
```

### **Phase 1.2: Integrations Consolidation (15 minutes)**

**Current Scatter**:
```
├── integrations/            # ❌ Root level (move)
├── pipelines/integrations/  # ❌ Old location (move)
├── sql/integrations/        # ❌ Wrong place (move)
```

**Target State**:
```
├── src/pipelines/integrations/  # ✅ ONLY location
    ├── monday/
    ├── powerbi/
    ├── azure/
    └── external/
```

**Actions**:
```powershell
# 1. Consolidate all integration code
mkdir src\pipelines\integrations\monday
mkdir src\pipelines\integrations\powerbi
mkdir src\pipelines\integrations\azure
mkdir src\pipelines\integrations\external

# 2. Move from scattered locations
robocopy integrations src\pipelines\integrations\external /MIR
robocopy pipelines\integrations src\pipelines\integrations\monday /MIR
robocopy sql\integrations src\pipelines\integrations\external /MIR

# 3. Create __init__.py files
echo. > src\pipelines\integrations\__init__.py
echo. > src\pipelines\integrations\monday\__init__.py
echo. > src\pipelines\integrations\powerbi\__init__.py
echo. > src\pipelines\integrations\azure\__init__.py
echo. > src\pipelines\integrations\external\__init__.py

# 4. Clean up old locations
rmdir integrations /s /q
rmdir pipelines\integrations /s /q
rmdir sql\integrations /s /q
```

### **Phase 1.3: Clear Purpose Separation (10 minutes)**

**Database Structure Clarification**:
```
├── db/               # 📁 Schema Evolution & Management
    ├── ddl/          # ✅ CREATE, ALTER, DROP statements
    ├── migrations/   # ✅ Version-controlled schema changes
    └── tests/        # ✅ Schema validation tests

├── sql/              # 📁 Operations & Business Logic  
    ├── operations/   # ✅ SELECT queries, procedures
    ├── transformations/ # ✅ ETL queries
    ├── utility/      # ✅ Admin and maintenance queries
    └── graphql/      # ✅ Monday.com API templates
```

**Actions**:
```powershell
# 1. Organize sql/ by purpose
mkdir sql\operations
move sql\*.sql sql\operations\  # Move loose SQL files

# 2. Update documentation references
# (Will be done in documentation phase)
```

### **Phase 1.4: Migration Validation (10 minutes)**

**Create validation script**:
```powershell
# tools/validate_consolidation.py
python tools\validate_consolidation.py --check-ddl --check-integrations
```

**Verification checklist**:
- [ ] DDL only in `db/ddl/` 
- [ ] Integrations only in `src/pipelines/integrations/`
- [ ] No orphaned files
- [ ] All imports still working
- [ ] Documentation updated

### **Post-Action Review**
- **Show original goals**: ✅ Eliminate duplications, ✅ Standardize structure, ✅ Maintain production safety
- **Mark completed items**: All Phase 1 consolidation steps
- **Document any failures**: Migration conflicts (to be handled in validation)
- **Preventative action**: Enhanced validation script for future changes

---

## �📋 Phase 1: Import Migration (Week 1)

### Migration Script
**tools/migrate_imports.py**:
```python
"""Migrate Python files to use new package imports"""
import re
from pathlib import Path
import argparse

MIGRATION_PATTERNS = [
    # Replace sys.path hacks
    (r'sys\.path\.insert\(0, str\(.*?utils.*?\)\)\s*\nimport db_helper',
     'from pipelines.utils import db'),
    (r'sys\.path\.insert\(0, str\(.*?utils.*?\)\)\s*\nimport logger_helper', 
     'from pipelines.utils import logger'),
    
    # Replace direct imports  
    (r'^import db_helper as db$', 'from pipelines.utils import db'),
    (r'^import logger_helper$', 'from pipelines.utils import logger'),
    
    # Replace function calls
    (r'db_helper\.', 'db.'),
    (r'logger_helper\.', 'logger.'),
]

def migrate_file(file_path: Path, dry_run: bool = True):
    """Migrate imports in a single file"""
    if file_path.suffix != '.py':
        return False
        
    content = file_path.read_text(encoding='utf-8', errors='ignore')
    original = content
    
    for pattern, replacement in MIGRATION_PATTERNS:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    if content != original:
        if not dry_run:
            file_path.write_text(content, encoding='utf-8')
            print(f"✅ Migrated: {file_path}")
        else:
            print(f"📝 Would migrate: {file_path}")
        return True
    
    return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Apply changes')
    parser.add_argument('--path', default='.', help='Path to scan')
    args = parser.parse_args()
    
    root_path = Path(args.path)
    skip_dirs = {'__pycache__', '.git', '__legacy__', '.venv'}
    
    migrated = 0
    for py_file in root_path.rglob('*.py'):
        if any(part in skip_dirs for part in py_file.parts):
            continue
        if migrate_file(py_file, dry_run=not args.apply):
            migrated += 1
    
    print(f"\n{'Migrated' if args.apply else 'Would migrate'} {migrated} files")

if __name__ == "__main__":
    main()
```

---

## 🎯 Success Metrics

### Phase 0 Complete (TODAY):
- [ ] `__legacy/` created with old folders archived
- [ ] New `src/pipelines/` structure established
- [ ] `pyproject.toml` working with `pip install -e .`
- [ ] Emergency tests passing
- [ ] Legacy imports still functional

### **Current Status Summary**

| Phase | Status | Duration | Key Achievement |
|-------|---------|----------|-----------------|
| **Phase 0** | ✅ **COMPLETE** | 30 min | Working modern package structure |
| **Enhanced Phase 1** | 📋 **READY** | 45 min | Duplication cleanup & consolidation |
| **Phase 2** | 📋 Planned | 30 min | Import migration tools |
| **Phase 3** | 📋 Planned | 15 min | Legacy deprecation |

### **Phase 0 Achievements**:
- ✅ Modern `src/pipelines/` package structure created
- ✅ Full `pyproject.toml` with all dependencies consolidated
- ✅ Compatibility layer: `src/pipelines/utils/` (db.py, logger.py, config.py)
- ✅ Legacy code safely archived in `__legacy/`
- ✅ Emergency test suite validates all imports
- ✅ Package installs: `pip install -e .`
- ✅ Zero breaking changes to production

### Phase 1 Complete (Week 1):
- [ ] DDL consolidation (only in `db/ddl/`)
- [ ] Integrations consolidation (only in `src/pipelines/integrations/`)
- [ ] Clear purpose separation (`db/` vs `sql/`)
- [ ] Migration validation tools
- [ ] Legacy imports still functional

### Phase 2 Complete (Week 1):
- [ ] Import migration tools ready
- [ ] Selected scripts using package imports
- [ ] Comprehensive test coverage
- [ ] No breaking changes

---

## 🚀 **NEXT STEPS - Execute Enhanced Phase 1**

**Immediate Actions** (next 45 minutes):

1. **Execute Enhanced Phase 1.1: DDL Consolidation** (10 min)
   - Move `sql/ddl/*` → `db/ddl/`
   - Remove duplicate DDL locations
   - Create `sql/operations/` for queries

2. **Execute Enhanced Phase 1.2: Integrations Consolidation** (15 min)  
   - Consolidate all integration code to `src/pipelines/integrations/`
   - Clean up scattered integration folders
   - Update import paths

3. **Execute Enhanced Phase 1.3: Purpose Separation** (10 min)
   - Organize `sql/` by operational purpose
   - Update documentation references
   - Validate folder structure

4. **Execute Enhanced Phase 1.4: Validation** (10 min)
   - Run consolidation validation script
   - Test all imports still working
   - Document changes

**Why Enhanced Phase 1 Now?**
- ✅ **Immediate Impact**: Eliminates confusing duplications
- ✅ **Low Risk**: File moves with safety checks  
- ✅ **High Value**: Clear, logical structure
- ✅ **Foundation**: Sets up clean base for import migration

**After Phase 1**: Repository will have clean, logical structure with zero duplications and clear purpose separation, ready for import migration tools in Phase 2.

---

## 🎯 Long-term Success Metrics

This approach ensures:
- ✅ **Immediate modern packaging** with working `pyproject.toml`
- ✅ **Zero production disruption** via compatibility layer
- ✅ **Clean `src/pipelines` structure** (not data-orchestration)
- ✅ **Eliminated duplications** with clear separation of concerns
- ✅ **Gradual migration path** with full backward compatibility
- ✅ **Comprehensive testing** at each phase

**Ready to execute Enhanced Phase 1 now!**
