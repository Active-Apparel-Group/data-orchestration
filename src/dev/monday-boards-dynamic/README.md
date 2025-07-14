# Dynamic Monday.com Board Extraction System 🚀

**✅ PRODUCTION-READY: Zero-Downtime Monday.com Board Extraction with Dynamic Schema Handling**

Transform any Monday.com board into a fully automated data pipeline with zero-downtime production deployments and automatic schema adaptation.

## 🎯 **PROJECT STATUS: COMPLETED & PRODUCTION-READY**

The hybrid ETL system is **production-ready** and successfully implements:
- ✅ **Repository Standards Compliance** (centralized db_helper, config, mapping)
- ✅ **Zero-Downtime Architecture** (atomic staging swap, <1s downtime)
- ✅ **Dynamic Schema Handling** (auto-adapts to Monday.com board changes)
- ✅ **Human-in-the-Loop (HITL)** (prompts for complex column approval/rejection)
- ✅ **DataFrame Filtering** (removes rejected columns before database load)
- ✅ **Kestra-Compatible Logging** (logger_helper for VS Code + Kestra environments)
- ✅ **Production Template System** (board_extractor_production.py.j2 with all features)
- ✅ **Production-Grade Performance** (retry logic, bulk operations, error handling)

**Latest Updates**: Logger helper integration, complete template system, and file consolidation completed.

## ✨ Features

- **🔍 Auto-Discovery**: Automatically discovers Monday.com board structure via GraphQL API
- **🏗️ Smart DDL**: Generates both production and staging tables with proper constraints
- **🚀 Zero-Downtime**: Staging table pattern for production deployments with atomic swaps
- **📝 Template-Driven**: Jinja2 templates for maximum flexibility and maintainability
- **🎯 Type-Based**: Centralized field type mapping, no per-column custom logic
- **💾 Name Preservation**: Database columns exactly match Monday.com (no transformation)
- **🛡️ Safe Operations**: CLI remove command only affects registry, preserves data
- **📊 Registry Management**: JSON-based tracking of deployed boards and status

## 🏗️ Architecture

```
dev/monday-boards-dynamic/
├── core/                          # Core system components
│   ├── board_schema_generator.py  # Schema discovery & DDL generation
│   ├── script_template_generator.py # Script & workflow generation
│   ├── board_registry.py          # Board configuration management
│   └── monday_board_cli.py        # Command-line interface
├── templates/                     # Jinja2 templates
│   ├── board_extractor_clean.py.j2 # Production script template
│   └── workflow_template.yml.j2   # Kestra workflow template
├── metadata/                      # Board configurations and metadata
│   ├── board_registry.json        # Master board registry
│   └── boards/                    # Individual board metadata
├── generated/                     # Generated extraction scripts
└── utils/ -> ../../utils/         # Shared utilities
```

## 🚀 Zero-Downtime Deployment Pattern

**Four-Step Process:**
1. **🏗️ Staging Preparation**: Create/truncate `stg_{table_name}`
2. **📥 Data Loading**: Load new data to staging (production remains available)
3. **✅ Data Validation**: Verify row counts and data integrity
4. **⚡ Atomic Swap**: `DROP` production, `RENAME` staging → production

**Benefits:**
- **No Data Loss**: Production table preserved during entire load process
- **Minimal Downtime**: Only during final rename operation (~seconds)
- **Automatic Rollback**: Failed validation leaves production unchanged
- **Data Integrity**: Full validation before going live

### Phase 1: Foundation ✏️ *In Progress*
- [x] Project structure setup
- [ ] `board_schema_generator.py` - Core discovery engine
- [ ] `script_template_generator.py` - Template rendering engine  
- [ ] `board_registry.py` - Board configuration management
- [ ] Field type mapping logic with comprehensive Monday.com type support
- [ ] Jinja2 template for script generation

### Phase 2: CLI & Integration
## 🚀 Quick Start

### Deploy a New Board

```bash
# Deploy new Monday.com board with automatic schema discovery
cd dev/monday-boards-dynamic
python -m core.monday_board_cli deploy --board-id 12345 --board-name "orders" --table-name "orders" --database "orders"
```

This single command will:
- 🔍 Discover board structure via Monday.com API
- 🗄️ Generate DDL for production + staging tables
- 🐍 Generate Python extraction script with zero-downtime pattern
- 🔄 Generate Kestra workflow file
- 📝 Register board in system registry

### CLI Commands

```bash
# List all registered boards
python -m core.monday_board_cli list

# Show detailed status for specific board
python -m core.monday_board_cli status orders

# Remove board from registry (preserves files & database tables)
python -m core.monday_board_cli remove orders

# Show system summary
python -m core.monday_board_cli summary

# Deploy with custom options
python -m core.monday_board_cli deploy \
  --board-id 8709134353 \
  --board-name "planning" \
  --table-name "planning" \
  --database "orders" \
  --batch-size 1000 \
  --max-workers 4 \
  --dry-run
```

## 🛠️ Configuration

### Type Mapping
Centralized Monday.com field type mappings in `utils/data_mapping.yaml`:
```yaml
monday_types:
  text: 
    sql_type: "NVARCHAR(MAX)"
    extraction_field: "text"
    nullable: true
  numbers:
    sql_type: "DECIMAL(18,2)"
    extraction_field: "text"
    nullable: true
  # ... 28+ more types
```

### Environment Variables
```bash
export MONDAY_API_TOKEN="your_monday_api_token"
export TARGET_DATABASE="orders"  # Default database
```

## 📊 Generated Outputs

### DDL Example
```sql
-- Production Table
CREATE TABLE [dbo].[orders] (
    [Item ID] NVARCHAR(100) NOT NULL,
    [Name] NVARCHAR(MAX),
    [Customer] NVARCHAR(MAX),
    CONSTRAINT [PK_orders] PRIMARY KEY CLUSTERED ([Item ID] ASC)
);

-- Staging Table (for zero-downtime deployments)
CREATE TABLE [dbo].[stg_orders] (
    [Item ID] NVARCHAR(100) NOT NULL,
    [Name] NVARCHAR(MAX),
    [Customer] NVARCHAR(MAX),
    CONSTRAINT [PK_stg_orders] PRIMARY KEY CLUSTERED ([Item ID] ASC)
);
```

### Generated Script Features
- ✅ Zero-downtime staging table pattern
- ✅ Type-based field extraction
- ✅ Automatic data validation
- ✅ Batch processing with configurable sizes
- ✅ Comprehensive error handling and logging
- ✅ Production-ready code quality

# List all boards
python monday_board_cli.py list

# Update existing board
python monday_board_cli.py update --board-id 12345
```

## Current Reference Implementation

The existing production script `scripts/monday-boards/get_board_planning.py` serves as the reference implementation for:
- ✅ **Robust Error Handling**: Comprehensive exception handling and recovery
- ✅ **Performance Optimized**: Concurrent processing with configurable batch sizes
- ✅ **Pagination Support**: Cursor-based pagination for large datasets
- ✅ **Type Safety**: Careful data type conversion and validation
- ✅ **Database Integration**: Seamless integration with existing `db_helper.py`
- ✅ **Configuration Management**: Centralized config via `utils/config.yaml`

## Development Notes

- All generated scripts will preserve the proven optimization patterns from the reference implementation
- The system integrates with existing infrastructure (`db_helper.py`, `config.yaml`, `mapping_helper.py`)
- Error handling and validation follow established patterns
- Once validated, components will be moved to production `scripts/` directory

## Testing

Run tests from the project root:
```bash
python -m pytest dev/monday-boards-dynamic/tests/ -v
```

## Documentation

See `docs/design/` for detailed design specifications:
- `dynamic_monday_board_implementation_plan.md`
- `dynamic_monday_board_template_system.md`
- `dynamic_monday_board_template_system_diagrams.md`

## 📝 **Template System & Integration**

### **Production Template: `board_extractor_production.py.j2`**
The latest template includes ALL production features:
- **🤖 Kestra-Compatible Logging**: Automatic detection via `logger_helper`
- **🔍 HITL Schema Approval**: Interactive prompts for complex columns
- **📊 DataFrame Filtering**: Automatic removal of rejected columns
- **⚙️ Auto-Rejection Config**: `AUTO_REJECT_BOARD_RELATIONS = True`
- **🚀 Zero-Downtime Operations**: Complete staging and atomic swap logic
- **📝 YAML Decision Recording**: Schema decisions saved to `data_mapping.yaml`

### **Template Variables**
```python
{{ board_name }}        # Human-readable board name
{{ board_id }}          # Monday.com board ID
{{ table_name }}        # Target SQL table name
{{ database }}          # Target database name
{{ board_key }}         # Key for YAML schema decisions
{{ generation_timestamp }} # When template was generated
```

### **Logger Helper Integration**
Automatic environment detection:
```python
# Kestra environment: Uses Kestra.logger()
# VS Code/local: Uses standard Python logging
logger = logger_helper.get_logger("board_name_etl")
```
