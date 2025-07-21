# GitHub Copilot Custom Instructions for Data Orchestration Project

## Project Context
You are working on a data orchestration project that integrates Monday.com with SQL Server databases. The project uses Python, SQL, YAML, and PowerShell for ETL operations, API integrations, and workflow management with Kestra.

## Core Technologies
- **Database**: SQL Server, Azure SQL
- **APIs**: Monday.com GraphQL API
- **Languages**: Python 3.x, SQL, PowerShell, YAML
- **Orchestration**: Kestra workflows
- **IDE**: VS Code with extensive task automation

## Architecture Patterns to Follow

## Architecture Patterns to Follow

### File Organization (Modern Structure)
```
src/                        # ✅ Modern Python package (pip install -e .)
    pipelines/              # Main package
        utils/              # Modern utilities (db.py, logger.py, config.py)
        integrations/       # API integrations (monday/, azure/, etc.)
        load_order_list/    # Existing ORDER_LIST pipeline
        sync_order_list/    # 🆕 NEW - Monday sync pipeline
sql/                        # Database operations & business logic
    operations/             # Daily operational queries
    graphql/                # 🔄 CONSOLIDATED - Monday.com GraphQL templates
    mappings/               # Field mappings and transformations
    transformations/        # ETL transformation scripts
db/                         # Schema evolution & management
    ddl/                    # CREATE TABLE statements (documentation)
    migrations/             # Version-controlled schema changes
configs/                    # Configuration management
    pipelines/              # TOML configuration files
tests/                      # Test files organized by type
docs/                       # Documentation
pipelines/                  # 🔄 LEGACY - Being phased out
    utils/                  # Legacy utilities (still used during transition)
    scripts/                # Legacy executable scripts
```

### Modern Import Patterns
```python
# ✅ NEW WAY (after pip install -e .)
from pipelines.utils import db, logger, config
from pipelines.integrations.monday import GraphQLLoader, MondayClient
from pipelines.load_order_list.extract import OrderListExtractor

# 🔄 TRANSITION SUPPORT (legacy compatibility)
import sys
from pathlib import Path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))
import db_helper as db
import logger_helper
```

### Coding Standards

#### Python
- **Modern Imports**: Use `from pipelines.utils import db` after `pip install -e .`
- **Legacy Support**: Use [`sys.path`](sys.path ) pattern during transition for legacy scripts
- **Kestra Logging**: ALWAYS use `logger_helper.get_logger(__name__)` for Kestra compatibility
- **Database Connections**: Use appropriate database from [`config.yaml`](config.yaml ) (dms, dms_item, orders, infor_132)
- **Type Hints**: Required for all new functions and methods
- **Configuration**: TOML files in [`configs/pipelines/`](configs/pipelines/ ) for new projects
- **Test Placement**: [`tests/debug/`](tests/debug/ ) for development, [`tests/end_to_end/`](tests/end_to_end/ ) for integration

#### SQL Standards
- **⚠️ CRITICAL**: Table names, column names, and definitions MUST be defined and approved before migration
- **⚠️ CRITICAL**: all sql scripts to be run during testing must use [`run_migration.py`](tools/run_migration.py)
- **Naming Convention**: snake_case for tables/columns
- **Staging Tables**: Prefix with `swp_` (staging with processing)
- **Schema Management**: DDL in [`db/ddl/`](db/ddl/ ), migrations in [`db/migrations/`](db/migrations/ )
- **Delta Tables**: Use `_DELTA` suffix for change tracking tables
- **Computed Columns**: Use PERSISTED computed columns for hash-based change detection

#### Monday.com Integration
- **GraphQL Templates**: Store in [`sql/graphql/mutations/`](sql/graphql/mutations/ ) and [`sql/graphql/queries/`](sql/graphql/queries/ )
- **Template Loading**: Use `GraphQLLoader` from [`src/pipelines/integrations/monday/`](src/pipelines/integrations/monday/ )
- **Configuration**: TOML-based board and column mappings
- **Async Processing**: Batch operations with 15-item default batch size
- **Rate Limiting**: 0.1 second delays between API calls
- **Kestra Logging**: Use standardized logger for production compatibility 

#### PowerShell
- Use `;` not `&&` for command chaining
- Current working directory is already set correctly
- Prefer PowerShell native commands over bash equivalents

## Project-Specific Rules

### Database Connections (Modern Pattern)
```python
# ✅ MODERN WAY (with new package structure)
from pipelines.utils.db import get_connection
from pipelines.utils.logger import get_logger

logger = get_logger(__name__)
# Use appropriate database from config.yaml (dms, dms_item, orders, infor_132)
with get_connection('database_name') as conn:
    # database operations

# 🔄 LEGACY TRANSITION SUPPORT
import sys
from pathlib import Path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))
import db_helper as db
import logger_helper

logger = logger_helper.get_logger(__name__)
with db.get_connection('database_name') as conn:
    # database operations
```

### Configuration Loading (Enhanced)
```python
# ✅ TOML Configuration (new projects)
import tomli
from pathlib import Path

config_path = Path("configs/pipelines/sync_order_list.toml")
with open(config_path, 'rb') as f:
    config = tomli.load(f)

# 🔄 YAML Configuration (legacy projects)
import yaml
from pathlib import Path

config_path = repo_root / "pipelines" / "utils" / "config.yaml"
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)
```
```python
# ✅ TOML Configuration (new projects)
import tomli
from pathlib import Path

config_path = Path("configs/pipelines/sync_order_list.toml")
with open(config_path, 'rb') as f:
    config = tomli.load(f)

# 🔄 YAML Configuration (legacy projects)
import yaml
from pathlib import Path

config_path = repo_root / "pipelines" / "utils" / "config.yaml"
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)
```

### VS Code Tasks
- All tasks are defined in `.vscode/tasks.json`
- Use descriptive task names: "Pipeline: Order Sync V2"
- Group tasks: build, test, ops
- Reference existing tasks rather than creating new ones

### Error Handling
- Always use try/except for database operations
- Log errors using `pipelines.utils.logger` or `logger_helper.get_logger(__name__)` for Kestra compatibility
- Provide meaningful error messages with context

## 🚫 **Unicode & Emoji Usage Policy**

**Do NOT use emoji or non-ASCII Unicode characters in:**
- Log messages
- Comments  
- Docstrings
- Output to files or terminals

**ASCII alternatives to use instead:**
- "SUCCESS" instead of ✅
- "INFO" instead of 📝  
- "ERROR" instead of ❌
- "WARNING" instead of ⚠️
- "PROCESS" instead of �

**Rationale:**
- Unicode/emoji can cause encoding errors in logs, terminals, and files
- ASCII is universally compatible and safe for all environments

**Exception:**
- **Documentation**: Unicode is allowed in markdown files (e.g., README.md) for clarity and emphasis

## What NOT to Do

❌ Don't create files without approval in milestone documentation - use established naming conventions
❌ Don't use bash syntax (`&&`) in PowerShell  
❌ Don't hardcode database connections - use config files
❌ Don't hardcode database names - use appropriate database from config (dms, dms_item, orders, infor_132)
❌ Don't bypass Kestra logging requirements - ALWAYS use `logger_helper.get_logger(__name__)`
❌ Don't create schema changes without approval - table/column definitions must be pre-approved
❌ Don't place GraphQL files in multiple locations - use centralized `sql/graphql/` only
❌ Don't break existing import patterns during transition period
❌ Don't create new dependencies without checking existing utils
❌ Don't modify `pipelines/utils/config.yaml` - it contains live credentials
❌ Don't create duplicate files like business_key_generator.py when order_key_generator.py exists
❌ Don't run python scripts in powershell - use `python` command directly (with python script, or .sql script with `run_migration.py`)

## Current Project State (July 2025)

### Repository Structure: Stabilized
- ✅ **Modern Package Structure**: `src/pipelines/` with `pip install -e .` support
- ✅ **Business Key Architecture**: Customer canonicalization and Excel-compatible matching
- ✅ **OrderKeyGenerator & CanonicalCustomerManager**: Core utilities implemented
- ✅ **Testing Framework**: Structured phases with measurable success criteria (95%+ thresholds)
- ✅ **Import Standards**: Modern/legacy split documented and working

### Enhanced Pipeline Development
- **Active Development**: Milestone 2 complete - ORDER_LIST delta sync with business keys
- **OrderKeyGenerator**: Excel-compatible business key generation using customer canonicalization
- **CanonicalCustomerManager**: YAML-driven customer name resolution with unique key definitions
- **Testing Framework**: Structured phases with 95%+ success thresholds for production validation
- **Modern Architecture**: Clean package structure with modern/legacy import pattern support

### Development Standards
- **Schema Approval Required**: All table/column changes must be pre-approved
- **Modern Import Patterns**: Use `from pipelines.utils import module` with pip install -e .
- **Legacy Support**: Transition patterns with sys.path for legacy scripts
- **Configuration-Driven**: TOML files define business logic, mappings, and environment settings
- **Kestra Integration**: All new code must use compatible logging patterns
- **Error Prevention**: Follow established naming conventions to prevent file conflicts

## 🚨 Critical Error Prevention

### Naming & File Organization Rules
- **NEVER** create files without checking project structure documentation
- **ALWAYS** use established import patterns (modern vs legacy transition support)
- **VERIFY** file placement against existing successful implementations
- **PREVENT** duplicate file creation (like business_key_generator.py vs order_key_generator.py)

### Business Key & Customer Resolution Standards
- **USE** CanonicalCustomerManager for all customer name resolution
- **APPLY** customer-specific unique keys from canonical_customers.yaml configuration
- **IMPLEMENT** Excel-compatible NEW detection using AAG ORDER NUMBER existence checks
- **ENSURE** OrderKeyGenerator is single source of truth for business key generation

### Task Execution Methodology
For EVERY action you take, follow this structured approach:

#### 1. Pre-Action Planning
- **Summarize task goals** (high-level bullet points)
- **Reference current documentation** and existing implementations
- **Check instructions, docs, and reference files** before proceeding
- **Ask yourself**: Am I approaching this correctly? Have I reviewed existing patterns?

#### 2. Execute Actions  
- Perform the planned action using established patterns
- Document what was done and why

#### 3. Post-Action Review
- **Show original goals** and mark completed items with ✅
- **If any failures**: Document corrective action and preventative measures
- **Self-assess**: Is this the right approach? Does it follow project standards?

#### 4. Iterate Until Complete
- Continue until all goals achieved with proper validation

### Active Development: Order List Delta Sync
**Current Focus**: ORDER_LIST → Monday.com incremental sync with business keys (Milestone 2 Complete)

**Key Components**:
- **Business Key Architecture**: OrderKeyGenerator with customer canonicalization
- **Customer Resolution**: CanonicalCustomerManager using YAML configuration  
- **Excel Compatibility**: NEW detection via AAG ORDER NUMBER existence checks
- **Structured Testing**: Framework with 95%+ success rate validation criteria
- **Modern Package Structure**: Clean src/pipelines/utils/ organization

**Implementation Status**:
- ✅ **Milestone 1**: Modern package structure and utilities implemented
- ✅ **Milestone 2**: Business key generation and customer canonicalization complete  
- 🔄 **Milestone 3**: SQL merge operations with business keys (next phase)
- 🔄 **Milestone 4**: Monday.com integration testing and production deployment

## Response Style
- Provide working code examples with proper imports
- Reference existing project files and patterns
- Suggest using existing VS Code tasks when relevant
- Focus on simple, maintainable solutions
- Always consider impact on existing workflows
