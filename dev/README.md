# 🔧 Development Workspace

This folder contains active development, testing, and validation work for all workflows.

## 📁 Structure

```
dev/
├── 📁 monday-boards/           # Monday.com workflow development
│   ├── get_board_planning.py   # Dev version of main script
│   └── testing/                # Test suites and validation
├── 📁 monday-boards-dynamic/   # ✅ COMPLETED: Production-ready hybrid ETL
│   ├── get_planning_board.py   # 🚀 Production-ready script with dynamic schema
│   ├── README.md               # Complete documentation
│   └── core/                   # Original CLI tools and templates
├── 📁 customer_master_schedule/ # CMS workflow development  
├── 📁 order_staging/           # Order processing development
├── 📁 shared/                  # Shared development utilities
│   └── test_repo_root_import.py # Import pattern validation
└── 📁 checklists/              # Workflow plans & checklists
    ├── workflow_plans/         # Individual workflow status
    ├── workflow_development_checklist.md
    ├── testing_checklist.md
    └── deployment_checklist.md
```

## 🎯 Purpose

### Development Flow
1. **Develop** - Create and test scripts in appropriate dev subfolder
2. **Validate** - Run tests and verify functionality  
3. **Promote** - Copy working scripts to `/scripts` production folder
4. **Deploy** - Use deployment tools to push to Kestra

### Key Principles
- ✅ **Never edit production directly** - always develop here first
- ✅ **Test everything** - use comprehensive test suites
- ✅ **Follow import patterns** - use standardized utils imports
- ✅ **Update checklists** - track progress on workflow plans

## 🚀 Quick Start

### Working on Monday Boards
```bash
cd dev/monday-boards/
python get_board_planning.py  # Run dev version
python testing/test_*.py      # Run test suite
```

### Testing Import Patterns
```bash
python dev/shared/test_repo_root_import.py  # Validate imports work
```

### Checking Workflow Status
```bash
# Check Monday Boards status
cat dev/checklists/workflow_plans/monday_boards_plan.md
```

## 📋 Checklist Templates

Use these checklists for any new workflow development:
- `workflow_development_checklist.md` - Development phases
- `testing_checklist.md` - Testing requirements  
- `deployment_checklist.md` - Production deployment steps

## 🔄 Current Status

### ✅ **Completed Workflows**
- **Monday Boards**: 100% complete, deployed, operational

### 🔄 **In Progress**
- Customer Master Schedule: Planning phase
- Order Staging: Planning phase  

### 📋 **Planned**
- Audit Pipeline refinements
- Additional Monday.com integrations

---

**📖 For complete handover information, see `/DEVELOPER_HANDOVER.md`**