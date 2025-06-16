# Audit Pipeline v3

**A modern, end-to-end data orchestration platform for audit and quality control, powered by Kestra and Python.**

---

## 🚀 Quick Start

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

## 🔄 Recent Updates (June 2025)

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
