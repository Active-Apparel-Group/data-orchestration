# Global Project Instructions - Data Orchestration

## 🏢 **Company Context: Active Apparel Group**

**Industry**: Apparel Manufacturing & Distribution  
**Business Model**: Multi-brand garment production with complex size matrices  
**Key Customers**: Greyson, ACME, and other apparel brands  
**Data Challenge**: Transform multi-dimensional garment orders into relational Monday.com structure

---

## 🎯 **Project Mission**

Transform flat garment order data with 276+ size dimensions into structured Monday.com Customer Master Schedule (CMS) with master/subitem relationships for efficient production planning.

---

## 📊 **Data Dimensionality Context**

### **Multi-Dimensional Garment Data**
Active Apparel Group handles complex garment orders with multiple dimensions:

- **Style Dimension**: Product codes, SKUs, style numbers
- **Color Dimension**: Color codes, color names, seasonal variations  
- **Size Dimension**: 276+ size codes including:
  - Standard apparel: XS, S, M, L, XL, XXL, 2XL, 3XL, 4XL, 5XL
  - Specialty sizes: 32DD, 30X30, 34/34, 2/3, etc.
  - International sizes: EU/UK/Asian sizing variations
- **Customer Dimension**: Brand-specific requirements and preferences
- **Timeline Dimension**: Due dates, production schedules, delivery windows

### **Data Transformation Challenge**
```
Input:  1 Order × 276 Size Columns = Flat wide table
Output: 1 Master Record + N Size Subitems = Relational structure
```

**Example Transformation**:
```
ORDERS_UNIFIED: 
  Style "ABC", Color "Red", XS=5, S=10, M=15, L=8, XL=2

Monday.com Result:
  Master: "ABC Red" (Total: 40 units)
  ├─ Subitem 1: XS = 5 units
  ├─ Subitem 2: S = 10 units  
  ├─ Subitem 3: M = 15 units
  ├─ Subitem 4: L = 8 units
  └─ Subitem 5: XL = 2 units
```

---

## 🔧 **Technology Stack & Architecture**

### **Core Technologies**
- **Database**: SQL Server, Azure SQL Database
- **API Integration**: Monday.com GraphQL API (Board 4755559751)
- **Languages**: Python 3.x, SQL Server T-SQL, PowerShell, YAML
- **Orchestration**: Kestra workflows
- **Development**: VS Code with extensive task automation

### **Current Working Implementation**
- **Project Path**: `dev/orders_unified_delta_sync_v3/` (75% complete)
- **Key Scripts**: `staging_processor.py`, `monday_api_adapter.py`
- **Staging Tables**: UUID-based workflow with parent/child relationships
- **API Strategy**: Rate-limited (0.1s delays), batch processing, error recovery

---

## 📁 **File Organization Philosophy**

### **Working Files (Current Implementation)**
```
dev/orders_unified_delta_sync_v3/    # 75% complete working code
├── staging_processor.py             # Size melting/pivoting logic
├── monday_api_adapter.py            # Monday.com API integration  
├── error_handler.py                 # Error recovery and logging
└── config_validator.py              # Configuration validation

sql/ddl/tables/                      # Database schema (working)
├── orders/staging/                  # Staging table DDLs
└── orders/production/               # Production table DDLs

sql/graphql/                         # Monday.com API templates
├── mutations/                       # Create/update operations
└── queries/                         # Read operations
```

### **Non-Working/Empty Files (Do Not Use)**
```
sql/mappings/simple-orders-mapping.yaml    # EMPTY - not used
utils/simple_mapper.py                     # EMPTY - not used
docs/mapping/orders_unified_monday_mapping.yaml  # OUTDATED
```

---

## 🚨 **Critical Project Rules**

### **1. Mapping Implementation**
- **✅ ACTUAL**: Field mapping is done directly in Python code (`staging_processor.py`)
- **❌ MYTH**: `SimpleOrdersMapper` class does not exist and is not used
- **❌ MYTH**: Simple mapping YAML files are empty and not used

### **2. Size Data Handling**
- **Source**: 276 separate columns (XS, S, M, L, 2XL, 32DD, etc.)
- **Process**: Size melting/pivoting creates 1 subitem per non-zero size
- **Target**: Master/subitem relationship in Monday.com

### **3. API Integration**
- **Board ID**: 4755559751 (Customer Master Schedule)
- **Rate Limiting**: 0.1 second delays between API calls
- **Error Recovery**: Comprehensive retry logic with exponential backoff
- **Field Validation**: Live API schema validation against Monday.com

### **4. Zero Breaking Changes Philosophy**
- **75% Complete**: Working implementation must not be broken
- **Validation First**: Test all changes against working staging environment
- **Documentation Focus**: Consolidate fragmented docs, don't recreate working code

---

## 🎯 **Development Templates & References**

### **Dev Task Templates**
- `templates/dev-task.yml.tpl` - Development task scaffolding
- `templates/migration-task.yml.tpl` - Database migration tasks
- `templates/monday-board-deployment.yml.tpl` - Monday.com deployment

### **Operational Templates**  
- `templates/op-task.yml.tpl` - Operational task scaffolding
- `tools/deploy-all.ps1` - Production deployment script
- `tools/build.ps1` - Environment management (Kestra up/down)

### **Working Configuration**
- `utils/config.yaml` - Live credentials and API keys
- `sql/ddl/tables/` - Current working schema
- `dev/orders_unified_delta_sync_v3/` - 75% complete implementation

---

## 📋 **Current Project Priorities**

### **Phase 1: Documentation Consolidation (Current)**
1. ✅ Complete backward mapping analysis
2. ✅ Identify schema inconsistencies  
3. 🔄 Update all instruction files (in progress)
4. 🔄 Create single source of truth documentation

### **Phase 2: Schema Validation (Planned)**
1. Validate Monday.com API column IDs against live board
2. Reconcile DDL field count discrepancies  
3. Align all mapping files with working implementation
4. Test GraphQL operations against live API

### **Phase 3: Implementation Completion (Pending Approval)**
1. Complete remaining 25% of Delta Sync V3
2. Implement comprehensive error handling
3. Add monitoring and alerting
4. Production deployment and cutover

---

## 🔗 **Key Reference Documents**

- `docs/MAPPING_ANALYSIS_COMPREHENSIVE_REPORT.md` - Complete mapping file analysis
- `docs/ORDERS_UNIFIED_BACKWARD_MAPPING_COMPREHENSIVE.md` - Target-first data flow
- `docs/VSCODE_TASKS_GUIDE.md` - VS Code task automation guide
- `tools/README.md` - Development tools documentation

---

## 🚀 **Success Metrics**

- **Data Accuracy**: 100% field mapping alignment with Monday.com board
- **Performance**: <5 second processing time per order batch
- **Reliability**: 99.9% successful API integration rate
- **Scalability**: Handle 10K+ orders with 50K+ size subitems
- **Maintainability**: Single source of truth for all mapping logic

---

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
