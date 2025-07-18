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
        order_delta_sync/   # 🆕 NEW - Delta sync pipeline
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

config_path = Path("configs/pipelines/order_list_delta_sync.toml")
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

config_path = Path("configs/pipelines/order_list_delta_sync.toml")
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
- Log errors using `utils/logger_helper.py`
- Provide meaningful error messages with context

## 🚫 **Unicode & Emoji Usage Policy**

**Do NOT use emoji or non-ASCII Unicode characters in:**
- Log messages
- Comments
- Docstrings
- Output to files or terminals

**Problematic Unicode/Emoji examples (to avoid):**
- ✅ (U+2705) - "White Heavy Check Mark"
- 📝 (U+1F4DD) - "Memo"
- 💡 (U+1F4A1) - "Light Bulb"
- 🔍 (U+1F50D) - "Magnifying Glass"
- 📋 (U+1F4CB) - "Clipboard"
- 📊 (U+1F4CA) - "Bar Chart"
- 📥 (U+1F4E5) - "Inbox Tray"
- 🔄 (U+1F504) - "Anticlockwise Arrows Button"
- 🗄️ (U+1F5C4) - "File Cabinet"
- 💾 (U+1F4BE) - "Floppy Disk"
- ⏱️ (U+23F1) - "Stopwatch"
- 🎉 (U+1F389) - "Party Popper"
- 🚀 (U+1F680) - "Rocket"

**ASCII alternatives to use instead:**
- "SUCCESS" instead of ✅
- "INFO" instead of 📝
- "TIP" instead of 💡
- "SEARCH" instead of 🔍
- "SCHEMA" instead of 📋
- "DATA" instead of 📊
- "FETCH" instead of 📥
- "PROCESS" instead of 🔄
- "STAGING" instead of 🗄️
- "SAVE" instead of 💾
- "TIME" instead of ⏱️
- "COMPLETE" instead of 🎉
- "START" instead of 🚀

**Rationale:**
- Unicode/emoji can cause encoding errors in logs, terminals, and files.
- ASCII is universally compatible and safe for all environments.

## What NOT to Do

❌ Don't create files in project root - use proper subdirectories
❌ Don't use bash syntax (`&&`) in PowerShell  
❌ Don't hardcode database connections - use config files
❌ Don't hardcode database names - use appropriate database from config (dms, dms_item, orders, infor_132)
❌ Don't bypass Kestra logging requirements - ALWAYS use `logger_helper.get_logger(__name__)`
❌ Don't create schema changes without approval - table/column definitions must be pre-approved
❌ Don't place GraphQL files in multiple locations - use centralized `sql/graphql/` only
❌ Don't break existing import patterns during transition period
❌ Don't create new dependencies without checking existing utils
❌ Don't modify `pipelines/utils/config.yaml` - it contains live credentials

## Current Project State

### Repository Restructure (Recently Completed)
- ✅ **Modern Package Structure**: `src/pipelines/` with `pip install -e .` support
- ✅ **GraphQL Consolidation**: All templates in `sql/graphql/` with `GraphQLLoader` utility
- ✅ **Kestra-Compatible Logging**: Standardized `logger_helper.py` for production
- 🔄 **Transition Period**: Legacy `pipelines/utils/` still supported during migration

### Enhanced Pipeline Development
- **New Project**: Order List → Monday.com delta sync pipeline
- **Shadow Table Strategy**: `ORDER_LIST_V2` for zero-downtime development
- **TOML Configuration**: Environment-specific settings in `configs/pipelines/`
- **Async GraphQL Processing**: Batch operations with standardized templates

### Development Standards
- **Schema Approval Required**: All table/column changes must be pre-approved
- **Production Safety**: Shadow tables during development, atomic cutover for production
- **Configuration-Driven**: TOML files define business logic, mappings, and environment settings
- **Kestra Integration**: All new code must use compatible logging patterns

### Active Development: Order List Delta Sync
**Current Focus**: Building ORDER_LIST → Monday.com incremental sync pipeline

**Key Components**:
- **Hash-based Change Detection**: PERSISTED computed columns for efficient delta identification
- **Dual Table Strategy**: `ORDER_LIST` (headers) + `ORDER_LIST_LINES` (unpivoted sizes)
- **State Management**: `sync_state` tracking (NEW, CHANGED, SYNCED, FAILED)
- **Shadow Development**: `ORDER_LIST_V2` for zero production impact
- **TOML Configuration**: Environment-specific board mappings and business rules

**Implementation Approach**:
1. **Milestone 1**: Shadow tables + TOML config + `ORDER_LIST_LINES` structure
2. **Milestone 2**: Delta merge operations + GraphQL integration  
3. **Milestone 3**: Monday.com two-pass sync (headers → lines)
4. **Milestone 4**: Production cutover + operational handoff

## Response Style
- Provide working code examples with proper imports
- Reference existing project files and patterns
- Suggest using existing VS Code tasks when relevant
- Focus on simple, maintainable solutions
- Always consider impact on existing workflows
