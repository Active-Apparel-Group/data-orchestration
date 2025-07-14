# Workflow Development & Deployment Process

**Purpose**: Standardized process for developing, testing, and deploying data workflows from dev → scripts → Kestra

## 📁 **Directory Structure & Workflow**

```
dev/                              # Development environment
├── {workflow-name}/              # Individual workflow development
│   ├── {main_script}.py         # Main production-ready script
│   ├── backup/                  # Archived/backup files
│   ├── testing/                 # Test files and samples
│   └── validation/              # Validation scripts
└── {workflow-name}-dynamic/     # Template-driven workflows (optional)
    ├── get_{workflow}.py        # Master template script
    ├── templates/               # Jinja2 templates
    ├── generated/               # Generated scripts
    └── core/                    # Template generation logic

scripts/                         # Production deployment location
├── {workflow-name}/             # Production scripts
│   ├── {main_script}.py        # Deployed production script
│   └── [supporting files]      # Config, helper files
└── [other workflows...]

workflows/                       # Kestra workflow definitions
├── {workflow-name}.yml         # Kestra workflow configuration
└── [other workflows...]
```

## 🔄 **Development to Production Process**

### **Phase 1: Development** (`dev/` folder)
1. **Create Development Environment**
   ```bash
   mkdir dev/{workflow-name}
   mkdir dev/{workflow-name}/testing
   mkdir dev/{workflow-name}/validation
   ```

2. **Develop Script**
   - Use `utils/logger_helper.py` for Kestra-compatible logging
   - Follow standardized patterns (db_helper, config, mapping)
   - Implement production features (retry logic, error handling, etc.)

3. **Test in Development**
   - Unit tests in `testing/` folder
   - Validation scripts in `validation/` folder
   - Use `TEST_MODE=true` for limited data testing

### **Phase 2: Generated Scripts** (for template-driven workflows)
1. **Template Generation** (`dev/{workflow-name}-dynamic/generated/`)
   ```python
   # Generate script from template
   python dev/{workflow-name}-dynamic/core/script_template_generator.py
   ```

2. **Generated Script Testing**
   - Generated scripts appear in `generated/` folder
   - Test generated script functionality
   - Validate template variables and configuration

### **Phase 3: Production Deployment** 

#### **Step 1: Move to Scripts Folder**
```bash
# Copy production-ready script
cp dev/{workflow-name}/{main_script}.py scripts/{workflow-name}/

# Or for generated scripts:
cp dev/{workflow-name}-dynamic/generated/{script}.py scripts/{workflow-name}/
```

#### **Step 2: Production Testing**
```bash
cd scripts/{workflow-name}
python {main_script}.py  # Final production test
```

#### **Step 3: Deploy to Kestra**

**Option A: Manual Deployment**
1. Upload script to Kestra environment
2. Create/update workflow YAML in `workflows/` folder
3. Deploy workflow configuration

**Option B: Automated Deployment** (if available)
```bash
# Deploy using automation tools
./tools/deploy-scripts.ps1 {workflow-name}
```

## 📋 **Checklist Integration**

### **Update Workflow Plan**
For each workflow, update the corresponding plan in `dev/checklists/workflow_plans/`:
- `{workflow_name}_plan.md`

### **Track Progress**
Update `dev/checklists/workflow_development_checklist.md` with:
- Development status
- Testing results  
- Production deployment status
- Performance metrics

## 🔧 **Template-Driven Workflows (Advanced)**

### **When to Use Templates**
- Multiple similar boards/APIs to process
- Dynamic schema requirements
- Standardized patterns across multiple data sources

### **Template Development Process**
1. **Create Master Template** (`dev/{workflow}-dynamic/`)
2. **Generate Specific Scripts** (to `generated/` folder)
3. **Test Generated Scripts** 
4. **Deploy Best Script** (move to `scripts/` folder)

### **Template Variables**
Common template variables for Monday.com workflows:
```python
{
    "board_name": "Planning Board",
    "board_id": 8709134353,
    "table_name": "MON_COO_Planning", 
    "database": "orders",
    "board_key": "coo_planning",
    "generation_timestamp": "2025-06-18 14:30:00"
}
```

## 🚀 **Deployment Standards**

### **Production Requirements**
- ✅ Logger helper integration (Kestra-compatible)
- ✅ Error handling and retry logic
- ✅ Configuration management (centralized config)
- ✅ Database operations via db_helper
- ✅ Test mode support (`TEST_MODE` environment variable)
- ✅ Production validation testing

### **Kestra Workflow Requirements**
- YAML configuration in `workflows/` folder
- Environment variable configuration
- Scheduling and trigger setup
- Error notification configuration
- Monitoring and logging setup

## 📊 **Tracking & Monitoring**

### **Development Tracking**
- Individual workflow plans in `dev/checklists/workflow_plans/`
- General checklist in `workflow_development_checklist.md`
- Documentation status in `docs/DOCUMENTATION_STATUS.md`

### **Production Monitoring**
- Kestra workflow dashboards
- Performance metrics tracking
- Error rate monitoring  
- Data quality validation

## 🔄 **Example: Monday Boards Workflow**

```bash
# Development (completed)
dev/monday-boards/get_planning_board.py    ✅ Production-ready

# Template System (completed)  
dev/monday-boards-dynamic/                 ✅ Template system
├── get_planning_board.py                  ✅ Master template
├── templates/board_extractor_production.py.j2  ✅ Jinja2 template
└── generated/                             📁 Generated scripts go here

# Production Deployment (next step)
scripts/monday-boards/get_planning_board.py    📋 Ready to deploy

# Kestra Configuration (next step)
workflows/monday-boards.yml                    📋 Deploy to Kestra
```

---

**Process Version**: 1.0  
**Created**: 2025-06-18  
**Last Updated**: 2025-06-18  
**Next Review**: 2025-07-18
