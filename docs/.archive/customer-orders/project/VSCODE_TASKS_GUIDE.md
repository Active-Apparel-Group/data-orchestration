# 🎯 VS Code Tasks Quick Guide

> **Access Tasks:** Press `Ctrl+Shift+P` → "Tasks: Run Task" or use Terminal → "Run Task..."

This guide provides an overview of all available VS Code tasks organized by functional groups. Tasks are designed to streamline development, testing, deployment, and maintenance workflows.

---

## **Task Categories**

Category	Count	Purpose
🧪 Testing & Validation	5 tasks	Code quality and functionality testing
🛠️ Development	4 tasks	Active development and code analysis
🚀 Operations & Deployment	4 tasks	Production deployment and infrastructure
🔧 Development Tools	6 tasks	Project management and automation
📊 Data Pipeline	3 tasks	Core ETL and data processing
📋 Audit & Reporting	2 tasks	Data quality and reporting


## 🧪 **Testing & Validation Tasks**
*Scripts and utilities for testing code quality and functionality*

### Core Test Scripts
| Task | Purpose | Location |
|------|---------|----------|
| **Test Refactored Monday Script** | Test refactored Monday.com board extraction scripts | `scripts/monday-boards/test_refactored_get_board_planning.py` |
| **Test Helper Script** | Test Monday.com helper functions and utilities | `scripts/monday-boards/test_helper.py` |
| **Test: All Validation** | Run all validation tests in parallel | *Compound task* |

### Validation & Quality Assurance
| Task | Purpose | Location |
|------|---------|----------|
| **Dev: DB Helper Refactor Validation** | Validate standardized import patterns across all scripts | `dev/db-helper-refactor/validation/test_import_patterns.py` |
| **Ops: Validate Environment** | Test Azure SQL connections and environment setup | `dev/audit-pipeline/validation/validate_env.py` |
| **Audit: Run Pipeline Audit** | Comprehensive data pipeline integrity audit | `scripts/jobs/run_audit.py` |

---

## 🛠️ **Development Tasks**
*Tools for active development and code analysis*

### Code Analysis & Refactoring
| Task | Purpose | Location |
|------|---------|----------|
| **Dev: Run Refactor Utility Analysis** | Analyze codebase for scripts needing refactoring | `dev/db-helper-refactor/refactor_utility.py` |
| **Dev: Config Codebase Scanner** | Scan codebase for configuration usage patterns | `dev/config_update/scan_codebase_config.py` |

### Monday.com Board Development
| Task | Purpose | Location |
|------|---------|----------|
| **Dev: Monday Boards Dynamic Generator** | Generate board extraction scripts dynamically | `dev/monday-boards-dynamic/universal_board_extractor.py` |
| **Run Monday ETL Script** | Execute Monday.com board planning extraction | `scripts/monday-boards/get_board_planning.py` |

---

## 🚀 **Operations & Deployment Tasks**
*Production deployment and infrastructure management*

### Deployment Operations
| Task | Purpose | Location |
|------|---------|----------|
| **Ops: Deploy All Scripts** | Deploy all scripts to production environment | `tools/deploy-all.ps1` |
| **Ops: Deploy Scripts Clean** | Clean deploy scripts to production | `tools/deploy-scripts-clean.ps1` |
| **Ops: Deploy Workflows** | Deploy Kestra workflows to production | `tools/deploy-workflows.ps1` |
| **Full: Validate & Deploy** | Complete validation and deployment sequence | *Compound task* |

---

## 🔧 **Development Tools**
*Utilities for project management and automation*

### Project Management
| Task | Purpose | Location |
|------|---------|----------|
| **Tools: Build Project** | Build entire project including Docker containers | `tools/build.ps1` |
| **Tools: Generate VS Code Tasks** | Auto-generate VS Code tasks from YAML task files | `tools/generate-vscode-tasks.py` |
| **Tools: Create New Task** | Interactive task scaffolding tool | `tools/task-scaffold.py` |
| **Tools: Generate Workflow** | Generate Kestra workflow files interactively | `tools/workflow_generator.py` |

### Maintenance & Utilities
| Task | Purpose | Location |
|------|---------|----------|
| **Tools: Update Requirements** | Update Python requirements.txt automatically | `tools/update-requirements.py` |
| **Tools: Extract DDL** | Extract database DDL statements | `tools/extract_ddl.py` |

---

## 📊 **Data Pipeline Tasks**
*Core ETL and data processing workflows*

### Main Data Pipelines
| Task | Purpose | Location |
|------|---------|----------|
| **Pipeline: Order Sync V2** | Main order synchronization pipeline | `scripts/order_sync_v2.py` |
| **Pipeline: Customer Master Schedule** | Add orders to customer master schedule | `scripts/customer_master_schedule/add_order.py` |
| **Pipeline: Sync Board Groups** | Synchronize Monday.com board groups | `scripts/monday-boards/sync_board_groups.py` |

---

## 📋 **Audit & Reporting Tasks**
*Data quality assurance and reporting*

### Reporting & Analysis
| Task | Purpose | Location |
|------|---------|----------|
| **Audit: Run Pipeline Audit** | Comprehensive pipeline audit with quality checks | `scripts/jobs/run_audit.py` |
| **Audit: Build Excel Report** | Generate Excel audit reports | `scripts/jobs/build_excel_report.py` |

---

## ⚙️ **Kestra Workflow Management**
*Dedicated tasks for Kestra orchestration platform integration*

### Workflow Deployment
| Task | Purpose | Location |
|------|---------|----------|
| **Ops: Deploy Workflows** | Deploy Kestra workflow YAML files to production | `tools/deploy-workflows.ps1` |
| **Ops: Deploy All Scripts** | Deploy Python scripts and workflows to Kestra environment | `tools/deploy-all.ps1` |
| **Ops: Deploy Scripts Clean** | Clean deployment of scripts to Kestra (removes old versions) | `tools/deploy-scripts-clean.ps1` |

### Workflow Development
| Task | Purpose | Location |
|------|---------|----------|
| **Tools: Generate Workflow** | Interactive Kestra workflow generator with database integration | `tools/workflow_generator.py` |
| **Tools: Build Project** | Build Docker containers for Kestra environment | `tools/build.ps1` |

### Available Kestra Workflows
The following workflows are available in the `/workflows/` directory and can be deployed to Kestra:

| Workflow File | Purpose | Namespace |
|---------------|---------|-----------|
| `monday-boards.yml` | Sync Monday.com boards with Azure SQL | `company.team` |
| `monday-board-customer_master_schedule.yml` | Customer master schedule board processing | `company.team` |
| `ayoun-flow.yml` | Custom Ayoun workflow process | `company.team` |
| `hello-import-test.yml` | Test workflow for import validation | `company.team` |
| `test-sql.yml` | SQL testing and validation workflow | `company.team` |
| `simple-test.yml` | Basic Kestra functionality test | `company.team` |
| `test-this-out.yml` | Experimental workflow testing | `company.team` |
| `last-one.yml` | Final validation workflow | `company.team` |
| `wolf_750702.yml` | Specialized Wolf process workflow | `company.team` |

### Kestra Environment Management
| Task | Purpose | Docker Commands |
|------|---------|-----------------|
| **Kestra: Start Environment** | Start Kestra stack with Docker Compose | `docker-compose up -d` |
| **Kestra: Stop Environment** | Stop Kestra environment | `docker-compose down` |
| **Kestra: View Logs** | View Kestra container logs | `docker-compose logs -f` |
| **Kestra: Rebuild Environment** | Rebuild and restart Kestra | `docker-compose down && up --build -d` |
| **Kestra: Open UI** | Open Kestra web interface in browser | Opens `http://localhost:8080` |

### Advanced Kestra Management
| Task | Purpose | Alternative Commands |
|------|---------|---------------------|
| **Tools: Build Project** → `up` | Alternative way to start Kestra | Same as "Kestra: Start Environment" |
| **Tools: Build Project** → `down` | Alternative way to stop Kestra | Same as "Kestra: Stop Environment" |
| **Tools: Build Project** → `logs` | Alternative way to view logs | Same as "Kestra: View Logs" |
| **Tools: Build Project** → `rebuild` | Alternative way to rebuild | Same as "Kestra: Rebuild Environment" |

### Kestra Workflow Patterns
Our Kestra workflows follow standardized patterns:

**Standard Workflow Structure:**
```yaml
id: workflow-name
namespace: company.team
description: "Workflow description"

tasks:
  - id: setup_and_log
    type: io.kestra.plugin.core.log.Log
    message: "Starting workflow with metadata"
    
  - id: execute_main_workflow
    type: io.kestra.plugin.core.flow.WorkingDirectory
    description: "Execute main script with environment"
    namespaceFiles:
      enabled: true
    tasks:
      - id: run_script
        type: io.kestra.plugin.scripts.python.Script
        script: python scripts/workflow-name/main.py
```

**Environment Integration:**
- All workflows use `namespaceFiles: enabled: true` for script access
- Python scripts are located in matching `scripts/workflow-name/` directories
- Database connections handled through environment variables
- Logging standardized with workflow metadata

### Kestra Quick Start Workflows

#### 🔄 **Kestra Development Cycle**
1. `Kestra: Start Environment` - Start Kestra Docker environment
2. `Tools: Generate Workflow` - Create new Kestra workflow interactively
3. `Ops: Deploy Scripts Clean` - Deploy supporting Python scripts
4. `Ops: Deploy Workflows` - Deploy workflow YAML to Kestra
5. `Kestra: Open UI` - Open Kestra dashboard for testing

#### 🚀 **Kestra Production Deployment**
1. `Kestra: Rebuild Environment` - Ensure clean Kestra environment
2. `Full: Validate & Deploy` - Complete validation and deployment
3. `Kestra: Open UI` - Monitor execution status and logs
4. `Audit: Run Pipeline Audit` - Validate data pipeline integrity

#### 🔧 **Kestra Troubleshooting**
1. `Kestra: View Logs` - Check Kestra container logs
2. `Ops: Validate Environment` - Test database connections
3. `Kestra: Rebuild Environment` - Clean restart if needed
4. `Ops: Deploy Scripts Clean` - Redeploy scripts if needed
5. `Kestra: Open UI` - Use Kestra's built-in debugging tools

### Kestra Integration Benefits
- **Unified Orchestration:** All data pipelines managed through Kestra
- **Version Control:** Workflows stored as YAML in Git repository
- **Environment Consistency:** Docker-based deployment ensures reproducibility
- **Monitoring & Alerting:** Built-in Kestra monitoring and notification system
- **Scalability:** Kestra handles parallel execution and resource management

---

## 🔄 **Compound Tasks**
*Multi-step workflows that combine multiple operations*

### Complete Workflows
| Task | Components | Purpose |
|------|------------|---------|
| **Full: Validate & Deploy** | Validation → Environment Check → Deploy All | Complete production deployment with validation |
| **Test: All Validation** | All validation tasks in parallel | Comprehensive testing before deployment |

---

## 🚦 **Task Groups by Repository Structure**

### `/scripts/` - Production Scripts
- **Pipeline: Order Sync V2** - Main data pipeline
- **Pipeline: Customer Master Schedule** - Order management
- **Pipeline: Sync Board Groups** - Monday.com synchronization
- **Audit: Run Pipeline Audit** - Quality assurance
- **Audit: Build Excel Report** - Reporting

### `/dev/` - Development & Testing
- **Dev: DB Helper Refactor Validation** - Code quality
- **Dev: Run Refactor Utility Analysis** - Code analysis
- **Dev: Monday Boards Dynamic Generator** - Dynamic generation
- **Dev: Config Codebase Scanner** - Configuration audit
- **Ops: Validate Environment** - Environment testing

### `/tools/` - Automation Tools
- **Tools: Build Project** - Project build
- **Tools: Deploy All Scripts** - Script deployment
- **Tools: Deploy Scripts Clean** - Clean deployment
- **Tools: Deploy Workflows** - Workflow deployment
- **Tools: Generate VS Code Tasks** - Task generation
- **Tools: Create New Task** - Task creation
- **Tools: Generate Workflow** - Workflow creation
- **Tools: Update Requirements** - Dependency management
- **Tools: Extract DDL** - Database utilities

### `/tests/` - Legacy Testing
- **Test Refactored Monday Script** - Refactoring validation
- **Test Helper Script** - Helper function testing

---

## 🎯 **Quick Start Workflows**

### 🔥 **Daily Development**
1. `Dev: DB Helper Refactor Validation` - Validate code quality
2. `Test: All Validation` - Run comprehensive tests
3. `Pipeline: [Choose specific pipeline]` - Test your changes

### 🚀 **Deployment Day**
1. `Test: All Validation` - Pre-deployment validation
2. `Full: Validate & Deploy` - Complete deployment workflow
3. `Audit: Run Pipeline Audit` - Post-deployment verification

### 🆕 **New Feature Development**
1. `Tools: Create New Task` - Plan your work
2. `Dev: Monday Boards Dynamic Generator` - Generate boilerplate
3. `Tools: Generate Workflow` - Create Kestra workflows
4. `Dev: Config Codebase Scanner` - Validate configuration

### ⚙️ **Kestra Workflow Development**
1. `Tools: Generate Workflow` - Create new Kestra workflow interactively
2. `Ops: Deploy Scripts Clean` - Deploy supporting Python scripts to Kestra
3. `Ops: Deploy Workflows` - Deploy workflow YAML files to Kestra
4. **Test in Kestra UI** - Execute and monitor workflows in Kestra dashboard

### 🔧 **Maintenance & Troubleshooting**
1. `Ops: Validate Environment` - Check system health
2. `Audit: Run Pipeline Audit` - Identify issues
3. `Tools: Update Requirements` - Update dependencies
4. `Audit: Build Excel Report` - Generate reports

---

## 💡 **Pro Tips**

**Keyboard Shortcuts:**
- Bind frequently used tasks to custom keyboard shortcuts via VS Code settings
- Use `Ctrl+Shift+P` → "Tasks: Rerun Last Task" to repeat tasks quickly

**Task Chaining:**
- Compound tasks automatically run dependent tasks in sequence or parallel
- Monitor task output in the VS Code terminal panel

**Kestra Integration:**
- Use `Tools: Generate Workflow` to create standardized Kestra workflows
- Always deploy scripts before workflows: `Ops: Deploy Scripts Clean` → `Ops: Deploy Workflows`
- Monitor Kestra workflows at `http://localhost:8080` (default) after starting with `Tools: Build Project`
- Kestra workflows automatically reload when deployed - no restart needed

**Customization:**
- Use `Tools: Generate VS Code Tasks` to regenerate tasks after adding new YAML task files
- Edit `.vscode/tasks.json` to customize presentation and behavior

**Troubleshooting:**
- Check task output in the VS Code terminal panel for detailed error messages
- For Kestra issues, use `Tools: Build Project` → `logs` to check container logs
- Ensure all prerequisites (Python, PowerShell, Docker) are properly installed
- Verify file paths and permissions if tasks fail
- Use Kestra UI debugging tools for workflow-specific issues

---

**Last Updated:** June 19, 2025  
**Generated by:** Data Orchestration Tools  
**Repository:** [data-orchestration](../)
