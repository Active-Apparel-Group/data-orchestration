---
applyTo: '**'
---

# Project Structure Rules - Data Orchestration

## 📁 Folder Organization Rules

### utils/ - Python Utilities (Importable Modules)
**Purpose**: All reusable Python classes and functions  
**File Types**: `.py` files only  
**Examples**: 
- `db_helper.py` - Database connections
- `logger_helper.py` - Logging utilities  
- `simple_mapper.py` - Data transformation utilities
- `config.yaml` - Configuration file

**Rules**:
- ✅ All Python modules go here
- ✅ Can be imported from anywhere
- ✅ Shared functionality only

### sql/ - Database & Configuration Files (Non-Importable)
**Purpose**: SQL files, GraphQL templates, mappings, configuration  
**File Types**: `.sql`, `.graphql`, `.yaml`, `.json`  
**Examples**:
- `ddl/` - Database schema definitions
- `graphql/` - Monday.com API templates  
- `mappings/` - Field mapping configurations
- `payload-templates/` - API payload examples

**Rules**:
- ❌ NO Python (.py) files allowed
- ✅ Configuration and template files only
- ✅ Organized by database concerns

### scripts/ - Executable Scripts
**Purpose**: Scripts that run workflows, ETL processes  
**File Types**: `.py` files that are executed directly  
**Examples**:
- `order_sync_v2.py` - Main pipeline script
- `monday-boards/` - Monday.com integration scripts

**Rules**:
- ✅ Import from utils/, never export to utils/
- ✅ Can have subfolders for organization
- ✅ Each script should be runnable

### tests/ - Test Files
**Purpose**: Unit tests, integration tests, debug scripts  
**File Types**: `.py` test files  
**Examples**:
- `test_*.py` - Unit tests
- `debug/` - Debug and example scripts

**Rules**:
- ✅ Import from utils/ and scripts/
- ✅ Follow pytest conventions
- ✅ Include debug/ for development examples

### docs/ - Documentation Only
**Purpose**: Markdown documentation, guides, plans  
**File Types**: `.md`, `.txt` files  
**Rules**:
- ❌ NO code files (.py, .sql, .yaml)
- ✅ Documentation and guides only

### workflows/ - Kestra Workflow Definitions
**Purpose**: YAML workflow definitions for Kestra  
**File Types**: `.yml` workflow files  
**Rules**:
- ✅ Kestra workflow YAML only
- ✅ Reference scripts/ for execution

## 🎯 File Placement Decision Tree

**Question**: Where should this file go?

### Is it a Python module with classes/functions?
→ **utils/** (so it can be imported)

### Is it SQL, GraphQL, or configuration?
→ **sql/** (organized by database concerns)

### Is it an executable Python script?
→ **scripts/** (organized by workflow)

### Is it a test or debug script?
→ **tests/** (with debug/ subfolder for examples)

### Is it documentation?
→ **docs/** (no code files)

### Is it a Kestra workflow?
→ **workflows/** (YAML only)

## 🚨 Common Mistakes to Avoid

### ❌ Wrong Placement Examples:
```
sql/mappings/simple_mapper.py     # Python module in sql/ - WRONG
docs/mapping/helper.py            # Code in docs/ - WRONG  
utils/create-item.graphql         # Template in utils/ - WRONG
scripts/config.yaml               # Config in scripts/ - WRONG
```

### ✅ Correct Placement:
```
utils/simple_mapper.py            # Python module - CORRECT
sql/graphql/create-item.graphql   # Template - CORRECT
sql/mappings/config.yaml          # Mapping config - CORRECT
scripts/order_sync_v2.py          # Executable script - CORRECT
```

## 🔧 Migration Guidelines

### Moving Files to Correct Locations:
1. **Identify file type** (Python module, config, script, etc.)
2. **Move to appropriate folder** based on rules above
3. **Update all import statements** in other files
4. **Test imports** to ensure they work
5. **Update documentation** to reflect new paths

### Import Updates After Moving:
```python
# Old (broken):
from utils.simple_mapper import SimpleOrdersMapper

# New (correct):
from utils.simple_mapper import SimpleOrdersMapper
```