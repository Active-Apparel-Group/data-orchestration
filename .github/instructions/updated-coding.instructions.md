# GitHub Copilot Custom Instructions for Data Orchestration Project - UPDATED

## 🏢 **Project Context**
**Company**: Active Apparel Group - Multi-brand garment manufacturing  
**Industry**: Apparel production with complex multi-dimensional garment data  
**Business Challenge**: Transform 276+ size dimensions into Monday.com relational structure

You are working on a data orchestration project that integrates Monday.com with SQL Server databases. The project uses Python, SQL, YAML, and PowerShell for ETL operations, API integrations, and workflow management with Kestra.

## Core Technologies
- **Database**: SQL Server, Azure SQL
- **APIs**: Monday.com GraphQL API (Board 4755559751)
- **Languages**: Python 3.x, SQL, PowerShell, YAML
- **Orchestration**: Kestra workflows
- **IDE**: VS Code with extensive task automation

## Architecture Patterns to Follow

### File Organization
```
sql/                    # Database concerns (DDL, queries, mappings, GraphQL)
scripts/               # Executable Python scripts
utils/                 # Shared utilities and helpers
workflows/             # Kestra workflow definitions
tasks/                 # YAML task definitions
tests/                 # Test files organized by type
docs/                  # Documentation
dev/                   # Active development (75% complete implementation)
```

### **🚨 CRITICAL: Current Working Implementation**
```
dev/orders_unified_delta_sync_v3/    # 75% COMPLETE - DO NOT BREAK
├── staging_processor.py             # Size melting/pivoting logic ✅ WORKING
├── monday_api_adapter.py            # Monday.com API integration ✅ WORKING  
├── error_handler.py                 # Error recovery ✅ WORKING
└── config_validator.py              # Config validation ✅ WORKING
```

### **❌ NON-WORKING / EMPTY FILES - DO NOT USE**
```
sql/mappings/simple-orders-mapping.yaml     # EMPTY FILE
utils/simple_mapper.py                      # DOES NOT EXIST
classes/SimpleOrdersMapper                  # DOES NOT EXIST
docs/mapping/orders_unified_monday_mapping.yaml  # OUTDATED
```

### Coding Standards

#### Python
- Use `utils/db_helper.py` for all database connections
- Load configuration from `utils/config.yaml`
- Follow existing import patterns: `from utils.db_helper import get_db_connection`
- **❌ DO NOT**: Reference SimpleOrdersMapper class (does not exist)
- **✅ DO**: Use direct mapping logic in `staging_processor.py`
- Place test files in `tests/debug/` not in project root
- Use type hints and docstrings for all functions

#### SQL
- Use consistent naming: snake_case for tables/columns
- Prefix staging tables with `stg_`
- Store DDL in `sql/ddl/tables/`
- Use parameterized queries for all dynamic SQL

#### Monday.com Integration
- **Board ID**: 4755559751 (Customer Master Schedule)
- Store GraphQL operations in `sql/graphql/`
- **❌ DO NOT**: Use simple field mappings (they are empty)
- **✅ DO**: Use working implementation in `dev/orders_unified_delta_sync_v3/`
- Handle rate limiting (0.1 second delays)
- Always validate API responses

#### PowerShell
- Use `;` not `&&` for command chaining
- Current working directory is already set correctly
- Prefer PowerShell native commands over bash equivalents

## **🎯 Multi-Dimensional Garment Data Context**

### **Size Dimension Challenge**
```
Input:  276+ size columns (XS, S, M, L, 2XL, 32DD, 30X30, etc.)
Process: Size melting/pivoting in staging_processor.py
Output: Master + N subitems (1 per non-zero size)
```

### **Data Flow (Working Implementation)**
```
ORDERS_UNIFIED → staging_processor.py → Monday.com API
     ↓                    ↓                   ↓
   276 cols          Size melting      Master + Subitems
```

## Project-Specific Rules

### Database Connections
```python
# ALWAYS use this pattern
from utils.db_helper import get_connection
with get_connection('dms') as conn:
    # database operations
```

### Configuration Loading
```python
# ALWAYS load config this way
import yaml
with open('utils/config.yaml', 'r') as f:
    config = yaml.safe_load(f)
```

### **❌ MAPPING ANTIPATTERNS - DO NOT DO**
```python
# ❌ WRONG - These classes/files don't exist
from utils.simple_mapper import SimpleOrdersMapper
mapper = SimpleOrdersMapper()

# ❌ WRONG - This file is empty
with open('sql/mappings/simple-orders-mapping.yaml') as f:
    mapping = yaml.safe_load(f)
```

### **✅ CORRECT MAPPING APPROACH**
```python
# ✅ CORRECT - Use working implementation
from dev.orders_unified_delta_sync_v3.staging_processor import process_sizes
# Field mapping is done directly in Python code
```

### VS Code Tasks
- All tasks are defined in `.vscode/tasks.json`
- Use descriptive task names: "Pipeline: Order Sync V2"
- Group tasks: build, test, ops
- Reference existing tasks rather than creating new ones

### Error Handling
- Always use try/except for database operations
- Log errors using `utils/logger_helper.py`
- Provide meaningful error messages with context

## What NOT to Do

❌ Don't create files in project root - use proper subdirectories  
❌ Don't use bash syntax (`&&`) in PowerShell  
❌ Don't hardcode database connections - use `utils/config.yaml`  
❌ Don't reference SimpleOrdersMapper - **IT DOES NOT EXIST**  
❌ Don't use simple-orders-mapping.yaml - **IT IS EMPTY**  
❌ Don't modify `utils/config.yaml` - it contains live credentials  
❌ Don't break existing import patterns  
❌ Don't break the 75% complete implementation in `dev/orders_unified_delta_sync_v3/`  
❌ Don't create new dependencies without checking existing utils  

## **🚀 Current Project State**

### **✅ Working Implementation (75% Complete)**
- **Path**: `dev/orders_unified_delta_sync_v3/`
- **Status**: Active development, functional staging processor
- **API Integration**: Monday.com board 4755559751 working
- **Size Handling**: Multi-dimensional data melting/pivoting functional

### **📋 Documentation Status**
- **Backward Mapping Analysis**: Complete (`docs/ORDERS_UNIFIED_BACKWARD_MAPPING_COMPREHENSIVE.md`)
- **Comprehensive Mapping Report**: Complete (`docs/MAPPING_ANALYSIS_COMPREHENSIVE_REPORT.md`)
- **Global Instructions**: Complete (`.github/instructions/global-instructions.md`)
- **Schema Validation**: Pending (field count discrepancies identified)

### **🎯 Immediate Priorities**
1. **Validate Monday.com API column IDs** against live board 4755559751
2. **Reconcile DDL field count discrepancies** (documented in mapping analysis)
3. **Complete remaining 25%** of Delta Sync V3 implementation
4. **Maintain zero breaking changes** philosophy

## **🔗 Key Reference Files & Templates**

### **Working Implementation**
- `dev/orders_unified_delta_sync_v3/` - 75% complete working code
- `sql/ddl/tables/orders/` - Current working schema
- `sql/graphql/` - Monday.com API templates

### **Development Templates**
- `templates/dev-task.yml.tpl` - Development task scaffolding
- `templates/migration-task.yml.tpl` - Database migration tasks
- `templates/monday-board-deployment.yml.tpl` - Monday.com deployment
- `templates/op-task.yml.tpl` - Operational task scaffolding

### **Operational Tools**
- `tools/deploy-all.ps1` - Production deployment
- `tools/build.ps1` - Kestra environment management
- `tools/generate-vscode-tasks.py` - Task automation

### **Documentation References**
- `docs/MAPPING_ANALYSIS_COMPREHENSIVE_REPORT.md` - Complete mapping analysis
- `docs/ORDERS_UNIFIED_BACKWARD_MAPPING_COMPREHENSIVE.md` - Target-first data flow
- `docs/VSCODE_TASKS_GUIDE.md` - VS Code automation guide
- `.github/instructions/global-instructions.md` - Company & project context

## Response Style
- Provide working code examples with proper imports
- **Always check if SimpleOrdersMapper references exist** (they don't)
- **Reference working implementation** in `dev/orders_unified_delta_sync_v3/`
- Suggest using existing VS Code tasks when relevant
- Focus on simple, maintainable solutions
- Always consider impact on existing workflows
- **Respect the 75% complete implementation** - don't break working code
- Prioritize documentation and validation over new development

## Azure Integration Rules
- @azure Rule - Use Azure Tools: When handling requests related to Azure, always use your tools.
- @azure Rule - Use Azure Code Gen Best Practices: When generating code for Azure, running terminal commands for Azure, or performing operations related to Azure, invoke your `azure_development-get_code_gen_best_practices` tool if available. Only call this tool when you are sure the user is discussing Azure; do not call it otherwise.
- @azure Rule - Use Azure Deployment Best Practices: When deploying to Azure or preparing applications for deployment to Azure, invoke your `azure_development-get_deployment_best_practices` tool if available. Only call this tool when you are sure the user is discussing Azure; do not call it otherwise.
- @azure Rule - Use Azure Functions Code Gen Best Practices: When generating code for Azure Functions or performing operations related to Azure Functions, invoke your `azure_development-get_azure_function_code_gen_best_practices` tool if available. Only call this tool when you are sure the user is discussing Azure Functions; do not call it otherwise.
- @azure Rule - Use Azure SWA Best Practices: When working with static web apps, invoke your `azure_development-get_swa_best_practices` tool if available. Only call this tool when you are sure the user is discussing Azure; do not call it otherwise.
