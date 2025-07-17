# Audit Pipeline v3

**A modern, end-to-end data orchestration platform for audit and quality control, powered by Kestra and Python.**

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.8+ 
- Docker & Docker Compose
- SQL Server access

### Setup

1. **Clone and navigate to the repository**
   ```bash
   cd data-orchestration
   ```

2. **Set up the environment**
   ```bash
   make setup
   ```
   
   This will:
   - Create a Python virtual environment
   - Install all dependencies
   - Set up development tools

3. **Activate the virtual environment**
   ```bash
   venv\Scripts\activate
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

5. **Start Kestra (workflow orchestrator)**
   ```bash
   make up
   ```


## 📁 Project Structure

```
data-orchestration/
├── src/
│   ├── audit_pipeline/   # Main pipeline logic
│   │   ├── config.py     # Config/env management
│   │   ├── etl.py        # ETL & standardization
│   │   ├── matching.py   # Matching & reconciliation
│   │   ├── report.py     # Excel reporting
│   │   └── adapters/     # Integrations (e.g., Monday.com)
│   ├── jobs/             # Entrypoints (run_audit.py, build_excel_report.py)
│   └── tests/            # Unit & integration tests
├── flows/                # Kestra YAML workflows (ingestion, analytics, quality_checks, subflows)
├── sql/                  # SQL scripts (staging, warehouse, tests)
├── docs/                 # Architecture, design, runbooks, mapping, reference files
├── infra/                # Docker Compose, infra-as-code
├── outputs/              # Excel reports, logs
├── requirements.txt      # Python dependencies
├── config.yaml           # (Legacy) config, being migrated to .env
└── Makefile, setup.bat   # Dev automation
```

---


## 🛠️ Development

### Setup & Environment

1. **Clone and enter the repo**
   ```bash
   git clone <repo-url>
   cd data-orchestration
   ```
2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
4. **Copy and edit environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your DB/API credentials
   ```

### Makefile Commands

```bash
# Setup & install
make setup         # Full environment setup
make install       # Install prod dependencies
make install-dev   # Install dev dependencies

# Code quality
make test          # Run all tests
make lint          # Lint code
make format        # Format code

# Kestra orchestration
make up            # Start Kestra stack
make down          # Stop Kestra
make logs          # View Kestra logs

# Cleanup
make clean         # Remove venv, .pyc, outputs
```

### 🎯 VS Code Tasks (Recommended)

**Quick Access:** Press `Ctrl+Shift+P` → "Tasks: Run Task"

For VS Code users, we provide comprehensive task automation:
- **� Power BI Dataflow Refresh** - Automated Gen1 dataflow refresh with business hours validation
- **�📊 Data Pipeline Tasks** - Run ETL workflows and data processing
- **🧪 Testing & Validation** - Code quality and functionality testing  
- **🚀 Operations & Deployment** - Production deployment and infrastructure
- **🔧 Development Tools** - Project management and automation utilities
- **📋 Audit & Reporting** - Data quality assurance and reporting

**[📖 Complete VS Code Tasks Guide →](docs/VSCODE_TASKS_GUIDE.md)**

### Environment Variables

All secrets/configs are loaded from `.env` (see `.env.example`).

```env
# Example
DB_DISTRIBUTION_HOST=your-server.database.windows.net
DB_DISTRIBUTION_PORT=1433
DB_DISTRIBUTION_DATABASE=your-database
DB_DISTRIBUTION_USERNAME=your-username
DB_DISTRIBUTION_PASSWORD=your-password
MONDAY_API_TOKEN=your-monday-token
# ...
```


### Running Tests

```bash
# Run all tests
make test
# Or manually:
python -m pytest -v
# Run a specific test file
python -m pytest src/tests/test_matching.py -v
```

---


## 🔄 Workflows & Orchestration

All ETL, matching, and reporting is orchestrated by **Kestra** using YAML flows in `flows/`:

- `ingestion/` — Data ingestion from SQL, CSV, API
- `quality_checks/` — Data quality validation
- `analytics/` — Analytics and reporting
- `subflows/` — Reusable workflow components

**To run a workflow:**
1. Start Kestra: `make up`
2. Open Kestra UI: [http://localhost:8080](http://localhost:8080)
3. Import/trigger flows from the `flows/` directory


## 📊 Data Sources

Supported sources:
- **SQL Server** (staging, warehouse)
- **Excel** (for reporting)
- **APIs** (Monday.com, etc.)


## 🤝 Contributing

1. Fork & branch from `main`
2. Make your changes (add tests!)
3. Run `make test` and `make format`
4. Open a pull request


## 📝 Documentation

- [Architecture & Data Flow](docs/design/architecture.md)
- [ADR: Why Kestra?](docs/design/adr-0001-kestra.md)
- [Field Mappings](docs/mapping/)
- [MVP Plan & Checklists](docs/plans/plan_phase01_mvp.md)
- [Runbooks & Migration](docs/runbooks/)


## 🐛 Troubleshooting

### Common Issues

1. **Virtual environment activation fails**
   - Ensure you're in the project root
   - Run: `venv\Scripts\activate`

2. **Database connection errors**
   - Check `.env` for correct credentials
   - Verify DB server/network access

3. **Kestra not starting**
   - Try: `make down && make up && make logs`

For more, see [runbooks](docs/runbooks/) or open an issue.

---

## 🏗️ Architecture Overview

See [docs/design/architecture.md](docs/design/architecture.md) for diagrams and full details.

**Key components:**
- **Kestra**: Orchestration, scheduling, retries, secrets
- **Python (pandas, rapidfuzz)**: ETL, matching, reporting
- **Azure SQL**: Staging, warehouse, fact tables
- **Monday.com**: Notifications

**Typical flow:**
1. Extract data (SQL views, API)
2. Standardize & transform (ETL)
3. Match & reconcile (fuzzy/exact)
4. Persist to DB
5. Generate Excel report
6. Notify via Monday.com

---

## 🧪 Testing & Quality

- All code is tested with `pytest` (see `src/tests/`)
- Linting: `make lint` (uses flake8, black, mypy)
- CI: GitHub Actions (planned)

---

## 📦 Dependencies

See `requirements.txt` for all Python dependencies. Key packages:
- pandas, numpy, pyodbc, python-dotenv, PyYAML, rapidfuzz, openpyxl, xlsxwriter, requests, cerberus, matplotlib, tqdm

---

## � Recent Updates (June 2025)

## 🔄 Recent Updates (July 2025)

### **Power BI Dataflow Automation - COMPLETED** ✅

**NEW**: Intelligent Power BI Gen1 dataflow refresh automation with business hours scheduling:

**✅ Production-Ready Components**:
- **Business Hours Validation**: Automatic 9 AM-5 PM Brisbane time enforcement  
- **Power Automate Integration**: Reliable SAS URL authentication (HTTP 202 success)
- **Daily Limit Awareness**: Smart handling of Power BI's 8 refresh per 24-hour limit
- **Kestra Workflow**: Complete automation with optimized scheduling
- **Error Resilience**: Comprehensive HTTP 400, timeout, and network error handling
- **Zero Dependencies**: No database logging requirements, fully self-contained

**📋 Key Files**:
- `pipelines/scripts/load_order_list/order_list_dataflow_refresh.py` - Production script
- `workflows/order_list_dataflow_refresh_scheduled.yml` - Kestra automation
- `docs/changelogs/power-bi-dataflow-refresh-implementation-complete.md` - Full implementation guide

**🚀 Deployment Ready**: Immediate production deployment available with business hours optimization.

### **Critical Workflow Fixes - COMPLETED** ✅

Recently completed comprehensive fixes to the Customer Master Schedule → Monday.com workflow:

**✅ Restored Missing Logic** (from archive analysis):
- **Computed Fields**: Fixed missing Title field generation (`STYLE + COLOR + ORDER_NUMBER`)
- **TOTAL QTY Mapping**: Changed from calculated field to direct mapping from ORDERS_UNIFIED
- **Test Coverage**: Updated tests to use full transformation (all 81 fields, not just 2)

**✅ Database Schema Corrections**:
- Removed references to non-existent `SYNC_STATUS` column
- Fixed staging ID range logic: Use 1000-10000 for staging, not Monday.com's large IDs (e.g., 9200517596)
- Cleaned up deprecated functions in `order_queries.py`

**✅ Final Validation Results** (June 16, 2025):
```
Found 10 new orders to process
Order: MWE-00025
Title: M01Z26 TOTAL ECLIPSE/TRUE BLACK LINER MWE-00025
Monday.com fields ready: 38
Total transformed fields: 46
SUCCESS: Workflow is working!
```

**📋 Key Files Updated**:
- `src/customer_master_schedule/order_mapping.py` - Restored computed fields logic
- `docs/mapping/orders_unified_monday_mapping.yaml` - Fixed TOTAL QTY mapping
- `tests/debug/test_simple_steps.py` - Now tests full transformation
- `src/customer_master_schedule/order_queries.py` - Cleaned up dead functions

**📚 Documentation**: See `docs/plans/workflow_update_plan_v2.md` for complete details and learnings.

**Status**: 🚀 **WORKFLOW IS PRODUCTION READY**

---

## �🗂️ Additional Resources

- [Design docs](docs/design/)
- [Migration guide: YAML → .env](docs/design/migrate_config_yaml_to_env.md)
- [SQL views & tests](sql/)
- [Field mapping YAMLs](docs/mapping/)

---


# 🚀 Kestra Data Workflow Platform

## ✅ **PROJECT STATUS: PRODUCTION READY**

A complete, organized Kestra workflow development environment with deployment automation, clean project structure, and comprehensive documentation.

### 🏆 **FINAL CLEAN STRUCTURE:**

```
kestra-start/                    📁 ROOT (Clean & Organized!)
├── 🔧 tools/                   📁 Essential deployment tools (3 files)
│   ├── deploy-scripts-clean.ps1     � Deploy Python scripts to namespace  
│   ├── deploy-workflows.ps1         📋 Deploy YAML workflows
│   └── build.ps1                    � Docker container management
│
├── 📋 workflows/               📁 Kestra YAML workflows (3 files)  
│   ├── test-sql-with-variables.yml  ✅ Working database workflow
│   ├── test-enhanced-sql-script.yml 🆕 Enhanced v2.0 workflow
│   └── simple-test.yml              🧪 Basic test workflow
│
├── 🐍 scripts/                📁 Python files for Kestra (7+ files)
│   ├── test_sql_with_env.py         ✅ Working database script  
│   ├── test_sql_enhanced.py         🆕 Enhanced v2.0 script
│   └── audit_pipeline/              📁 Complete audit pipeline
│       ├── config.py, etl.py, matching.py, report.py
│       └── adapters/monday.py
│
├── 📊 queries/                📁 SQL files for Kestra (1 file)
│   └── v_master_order_list.sql      📄 Sample SQL query
│
├── 📚 docs/                   📁 Complete documentation (5+ files)
│   ├── KESTRA-SETUP-NOTES.md        📖 Comprehensive setup guide
│   ├── CLEANUP-COMPLETED.md         🧹 Organization methodology  
│   └── [Other guides and lessons]   � Deployment & structure docs
│
├── 🚀 .github/workflows/      📁 CI/CD automation
│   └── deploy-kestra.yml            🤖 GitHub Actions pipeline
│
├── 🧪 tests/                  📁 Test files and experiments
├── 📁 _backup/                📁 Historical files
│
└── 📦 Infrastructure (Root Level)
    ├── 🐳 docker-compose.yml        ✅ Container orchestration
    ├── 📦 dockerfile               ✅ Container definition
    ├── 📝 requirements.txt         ✅ Python dependencies
    ├── 🔨 makefile                ✅ Build automation  
    └── 🔐 .env*                   ✅ Environment configuration
```

## 🚀 **QUICK START COMMANDS**

### **Deploy Scripts to Kestra:**
```powershell
# Deploy all Python scripts (filtered, preserves structure)
.\tools\deploy-scripts-clean.ps1
```

### **Deploy Workflows to Kestra:**
```powershell
# Deploy all YAML workflows
.\tools\deploy-workflows.ps1 deploy-all

# Deploy specific workflow
.\tools\deploy-workflows.ps1 deploy-single test-sql-with-variables.yml

# List deployed workflows
.\tools\deploy-workflows.ps1 list
```

### **Container Management:**
```powershell
# Build and start Kestra
.\tools\build.ps1 rebuild

# Show logs
.\tools\build.ps1 logs
```

## 🎯 **KEY FEATURES**

✅ **Clean Organization** - Everything in logical folders, no root clutter
✅ **Simple Tools** - Just 3 essential scripts that work perfectly  
✅ **Filtered Uploads** - Auto-excludes `__pycache__`, `__init__.py`, `.pyc`
✅ **Structure Preservation** - Local folders match namespace structure
✅ **Working Examples** - Database connections, enhanced logging, audit pipeline
✅ **CI/CD Ready** - GitHub Actions pipeline configured
✅ **Comprehensive Docs** - Complete setup and deployment guides

## 🔧 **TOOLS EXPLANATION**

### **`deploy-scripts-clean.ps1`** 🐍
- **Purpose**: Upload Python scripts to Kestra namespace `/scripts/`
- **Features**: Filters unwanted files, preserves folder structure
- **Core**: Simple Docker command with robocopy filtering

### **`deploy-workflows.ps1`** 📋  
- **Purpose**: Deploy YAML workflows via REST API
- **Commands**: `deploy-all`, `deploy-single`, `list`, `validate`
- **Core**: PowerShell REST API calls to Kestra

### **`build.ps1`** 🐳
- **Purpose**: Docker container management
- **Commands**: `build`, `up`, `down`, `rebuild`, `logs`
- **Core**: Docker Compose automation

## 📊 **DEPLOYMENT SUCCESS METRICS**

- **🗑️  Cleaned**: Removed 9 redundant/broken tools  
- **✅ Working**: 3 essential tools, all tested and functional
- **📁 Organized**: 7+ Python scripts in proper namespace structure
- **🚀 Ready**: Complete CI/CD pipeline and documentation
- **🏆 Professional**: Production-ready project structure

## 🎉 **WHAT'S DEPLOYED & WORKING**

### **Python Scripts in Namespace `/scripts/`:**
- `test_sql_with_env.py` - Database connection with environment variables
- `test_sql_enhanced.py` - Enhanced version with improved logging  
- `audit_pipeline/` - Complete audit pipeline with multiple modules

### **Workflows in Kestra:**
- `test-sql-with-variables` - Working database workflow
- `test-enhanced-sql-script` - Enhanced v2.0 workflow with better error handling
- `simple-test` - Basic test workflow

## � **ORGANIZATIONAL PRINCIPLES**

1. **🚨 No loose files in root** - Everything organized by purpose
2. **🔧 Simple, working tools** - No over-engineered solutions
3. **📁 Logical structure** - Easy to find and maintain anything
4. **✅ Tested and documented** - Every tool works and is explained

**Ready to build amazing data workflows! 🚀**

---

*Project organized and production-ready: June 15, 2025*  
*Tools cleaned: 9 removed, 3 essential kept*  
*Structure: Professional, scalable, maintainable*
