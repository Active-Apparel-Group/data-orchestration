# ORDER STAGING DEVELOPMENT - REPOSITORY STRUCTURE

This document provides a complete overview of the repository structure focused on the order staging development, with annotations explaining each component's role in the pipeline.

## 📁 Core Implementation (`src/order_staging/`)

**Purpose**: Production-ready code for staging-based order processing pipeline

```
src/order_staging/
├── __init__.py                     # Package initialization
├── batch_processor.py              # 🎯 MAIN ORCHESTRATOR (878 lines) - FUNCTIONAL ✅
│   │                               # Primary workflow coordinator
│   ├── process_customer_batch()    # Main workflow entry point  
│   ├── process_specific_po()       # Targeted PO processing (4 optional params)
│   ├── load_new_orders_to_staging() # ETL Step 1: ORDERS_UNIFIED → Staging
│   ├── create_monday_items_from_staging() # API Step 2: Staging → Monday.com
│   ├── create_group_name()         # Business logic: Customer/AAG season fallback
│   └── get_monday_column_values_for_staged_order() # YAML mapping application
│
├── staging_operations.py           # 🔧 DATABASE OPS (706 lines) - FUNCTIONAL ✅  
│   │                               # High-performance database operations
│   ├── start_batch() / update_batch_status() # Batch tracking & monitoring
│   ├── concurrent_insert_chunk()   # Ultra-fast bulk inserts (>1000 records/sec)
│   ├── StagingOperations class     # Database connection management
│   └── Performance optimization    # Pandas bulk insert with pyodbc fallback
│
├── monday_api_client.py             # 🌐 API CLIENT - FRAMEWORK ONLY ⚠️
│   │                               # Monday.com GraphQL integration (needs implementation)
│   └── [NEEDS]: create_item_with_retry(), GraphQL queries, error handling
│
├── error_handler.py                 # ❌ ERROR MANAGEMENT - FRAMEWORK ONLY ⚠️
│   │                               # Error handling & retry logic (needs implementation)  
│   └── [NEEDS]: Exponential backoff, failure logging, recovery mechanisms
│
└── staging_config.py                # ⚙️ CONFIGURATION - FRAMEWORK ONLY ⚠️
    │                               # Environment-based configuration (needs implementation)
    └── [NEEDS]: Database connections, API keys, logging config
```

## 📁 Entry Points & Scripts (`scripts/`)

**Purpose**: Kestra-compatible execution scripts and deployment utilities

```
scripts/
├── order_sync_v2.py                # 🚀 KESTRA ENTRY POINT (258 lines) - FUNCTIONAL ✅
│   │                               # Main orchestration script for production deployment
│   ├── setup_logging()             # Comprehensive logging configuration  
│   ├── get_db_connection_string()  # Environment-based database connection
│   ├── process_customer()          # Customer batch processing wrapper
│   └── Command-line interface      # [NEEDS]: Argument parsing for Kestra
│
└── order_staging/                  # 📄 Mirror of src/ for scripts execution
    │                               # Copy of core modules for script-level imports
    └── [All core modules duplicated for import resolution]
```

## 📁 Development & Testing (`dev/order_staging/`)

**Purpose**: Development tools, testing scripts, and validation utilities

```
dev/order_staging/
├── PRODUCTION_READY.md             # 📋 Ready-to-run instructions & validation results
├── QUICK_REFERENCE.md              # 🔍 Method usage guide (204 lines) - Complete API docs
├── run_greyson_po_4755.py          # 🧪 Production test script ✅ PASSING
│   │                               # Ready-to-run script for GREYSON PO 4755 validation
│   └── Validates 69 records with "GREYSON CLOTHIERS 2025 FALL" group naming
│
├── debugging/                      # 🔧 Schema analysis & data exploration (6 files)
│   ├── debug_staging_table_structure.py # Database schema validation
│   ├── explore_greyson_data.py     # Source data analysis for GREYSON
│   ├── test_group_naming_logic.py  # Business logic validation
│   └── validate_column_mappings.py # YAML mapping verification
│
├── testing/                        # ⚗️ Functional testing scripts (5 files)
│   ├── test_greyson_staging_simple.py # ✅ PASSING - Core workflow test
│   ├── test_enhanced_batch_processor.py # Enhanced method validation
│   ├── test_performance_bulk_insert.py # Performance benchmarking
│   └── test_connection_validation.py # Database & API connectivity tests
│
└── validation/                     # ✅ End-to-end verification (4 files) - ALL PASSING
    ├── test_end_to_end_flow.py     # ✅ PASSING - Complete workflow validation
    ├── run_migration.py            # ✅ COMPLETED - Database schema setup
    ├── comprehensive_validation_test.py # Full pipeline validation
    └── comprehensive_end_to_end_test.py # Business logic verification
```

## 📁 Database Schema (`sql/ddl/`)

**Purpose**: Database schema definitions for staging-based architecture

```
sql/ddl/tables/orders/
├── staging/                        # 📊 Staging Tables - Temporary data processing
│   ├── stg_mon_custmasterschedule.sql      # Main staging table DDL
│   │   │                                   # Handles ORDERS_UNIFIED → staging transformation
│   │   └── Key features: RANGE/COLLECTION column, batch_id tracking
│   │
│   └── stg_mon_custmasterschedule_subitems.sql # Subitems staging DDL
│       │                                       # Future: Size breakdown processing
│       └── Supports individual size quantities → Monday.com subitems
│
├── tracking/                       # 📈 Batch Processing Monitoring
│   └── mon_batchprocessing.sql     # Batch tracking & monitoring DDL
│       │                           # Tracks batch status, timing, success/failure counts
│       └── Enables real-time processing visibility
│
├── error/                          # ❌ Error Logging & Recovery
│   ├── err_mon_custmasterschedule.sql      # Error logging DDL for main records
│   └── err_mon_custmasterschedule_subitems.sql # Error logging DDL for subitems
│       │                                       # Captures API failures for retry processing
│       └── Supports error analysis and recovery workflows
│
├── production/                     # ✅ Production Tables - Final data storage
│   ├── dbo_mon_custmasterschedule.sql      # Production table DDL
│   │   │                                   # Successfully processed orders
│   │   └── Synchronized with Monday.com via API
│   │
│   └── dbo_mon_custmasterschedule_subitems.sql # Production subitems DDL
│       │                                       # Size breakdown data
│       └── Monday.com subitems integration
│
└── views/                          # 📊 Monitoring & Reporting Views
    └── vw_mon_activebatches.sql    # Active batch monitoring view
        │                           # Real-time processing dashboard
        └── Tracks current batch status, progress, and performance
```

## 📁 Configuration & Mapping (`docs/`)

**Purpose**: Field mappings, business rules, and workflow documentation

```
docs/
├── mapping/                        # 🗺️ Data Transformation Configuration
│   └── orders_unified_monday_mapping.yaml  # 🗺️ COMPLETE Field mapping (808 lines, 51 fields)
│       │                                   # ORDERS_UNIFIED → Monday.com transformation spec
│       ├── exact_matches: 37 fields        # Direct 1:1 mappings
│       ├── mapped_fields: 7 fields         # Transformation required (customer lookup)
│       ├── computed_fields: 2 fields       # Calculated values (Title generation)
│       ├── preprocessing: Data cleaning     # US TARIFF RATE "TRUE" → "0" conversion
│       └── Business logic: Group naming    # Customer SEASON → AAG SEASON fallback
│
├── plans/                          # 📋 Project Planning & Status Tracking
│   └── implementation_plan_phase3.md       # 📋 CURRENT STATUS & ROADMAP
│       │                                   # Comprehensive implementation tracking
│       ├── Completed: Database schema, core ETL, group naming logic ✅
│       ├── Pending: Monday.com API, error handling, configuration ⏳
│       ├── File status: Working vs empty vs missing files
│       └── Test results: GREYSON PO 4755 validation ✅
│
├── diagrams/                       # 🎨 Workflow Visualization
│   └── staging_workflow_overview.md        # 🎨 UPDATED Mermaid workflow diagram
│       │                                   # Visual representation of complete pipeline
│       ├── Data flow: ORDERS_UNIFIED → Staging → Monday.com → Production
│       ├── Error handling: Failed records → Error tables → Retry logic
│       ├── Business logic: Group naming resolution
│       └── Performance: Change detection, bulk processing
│
└── handover/                       # 🚀 HANDOVER DOCUMENTATION (THIS FOLDER)
    ├── ORDER_STAGING_HANDOVER.md   # 🚀 MAIN HANDOVER DOCUMENT
    ├── implementation_plan_phase3.md # Project status & implementation plan
    ├── staging_workflow_enhanced.md # Enhanced workflow diagram & explanation
    ├── orders_unified_monday_mapping.yaml # Key mapping configuration
    ├── PRODUCTION_READY.md          # Ready-to-run instructions
    └── QUICK_REFERENCE.md           # Method usage guide
```

## 📁 Pain Points & Solutions Documentation

**Purpose**: Lessons learned and resolution tracking

### **🚀 Performance Issues Resolved**
- **Location**: `src/order_staging/staging_operations.py` lines 85-180
- **Problem**: Concurrent processing was extremely slow (12-14 records/sec)
- **Solution**: Pandas bulk insert with pyodbc fallback
- **Result**: >1000 records/second performance improvement

### **🎯 Business Logic Issues Resolved**  
- **Location**: `src/order_staging/batch_processor.py` lines 112-132
- **Problem**: GREYSON orders created blank/undefined groups in Monday.com
- **Root Cause**: CUSTOMER SEASON field was NULL for GREYSON records
- **Solution**: Customer SEASON → AAG SEASON fallback logic
- **Validation**: GREYSON PO 4755 now shows "GREYSON CLOTHIERS 2025 FALL" ✅

### **📊 Architecture Decisions**
- **Location**: Complete `sql/ddl/` schema structure
- **Decision**: Staging-first architecture vs direct API processing
- **Benefits**: Error resilience, rollback capability, better monitoring
- **Implementation**: Separate staging, error, and production table layers

### **🔧 Development Workflow Improvements**
- **Location**: `dev/order_staging/` complete structure
- **Problem**: Testing was difficult with rigid customer processing
- **Solution**: `process_specific_po()` with 4 optional parameters
- **Safety**: At least one parameter required to prevent accidental bulk processing
- **Flexibility**: Any combination of customer_name, po_number, aag_season, customer_season

## 🔗 Integration Points & Dependencies

### **Kestra Orchestration**
- **Entry Point**: `scripts/order_sync_v2.py`
- **Status**: Framework ready, needs command-line interface enhancement
- **Integration**: Environment variables, logging, success/failure reporting

### **Monday.com API Integration**
- **Current**: Framework exists in `src/order_staging/monday_api_client.py`
- **Needs**: GraphQL client implementation, retry logic, authentication
- **Mapping**: Complete YAML configuration ready for implementation

### **Database Dependencies**
- **Source**: `ORDERS_UNIFIED` table (existing production data)
- **Staging**: Complete schema deployed and tested ✅
- **Connection**: Environment-based connection string resolution

---

**📍 REPOSITORY NAVIGATION SUMMARY**

- **Start Here**: `docs/handover/ORDER_STAGING_HANDOVER.md` (this document)
- **Run Tests**: `dev/order_staging/run_greyson_po_4755.py`
- **Core Code**: `src/order_staging/batch_processor.py` (878 lines, main orchestrator)
- **Performance**: `src/order_staging/staging_operations.py` (706 lines, database ops)
- **Configuration**: `docs/mapping/orders_unified_monday_mapping.yaml` (808 lines)
- **Current Status**: `docs/plans/implementation_plan_phase3.md`
- **Database Schema**: `sql/ddl/tables/orders/` (complete schema structure)

**🎯 QUICK START**: Run `cd dev/order_staging && python run_greyson_po_4755.py` to validate current implementation
