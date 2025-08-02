
```mermaid
flowchart TD
    Start[User Executio├── 📄 merge_orchestrator.py ✅ SIMPLIFIED (4-Phase Architecture)
│   ├── 🏗️ EnhancedMergeOrchestrator class
│   ├── 👥 _execute_group_creation_workflow() (ONLY remaining transformation)
│   ├── 🔍 detect_new_orders() 
│   └── 📋 execute_enhanced_merge_sequence() (4-phase)
│
├── 📄 sync_engine.py ✅ TRUE BATCH PROCESSING
│   ├── 🚀 run_sync() with TRUE BATCH PROCESSING flow
│   ├── 🔄 _create_true_batch_groups() - batches multiple record_uuids
│   ├── 📊 _process_true_batch() - single API call for batch
│   ├── 🎛️ TOML-driven batch sizing (item_batch_size = 5)
│   └── ✅ Record_uuid → monday_item_id mapping preservationcli.py]
    
    CLI --> ENV{Environment<br/>Parameter}
    ENV -->|--environment production| PROD[Production Config]
    ENV -->|--environment development| DEV[Development Config]
    ENV -->|Default| PROD
    
    CLI --> SYNC_CMD["sync_command"]
    
    %% STEP 1: Enhanced Merge Orchestrator (4-Phase)
    SYNC_CMD --> EMO[Enhanced Merge Orchestrator]
    EMO --> EMO_EXEC[execute_enhanced_merge_sequence()]
    
    %% 4-Phase Simplified Architecture + TRUE BATCH PROCESSING
    EMO_EXEC --> PHASE1[Phase 1: detect_new_orders()]
    PHASE1 --> PHASE2[Phase 2: group_creation_workflow()]
    PHASE2 --> PHASE3[Phase 3: template_merge_headers()]
    PHASE3 --> PHASE4[Phase 4: template_unpivot_sizes_direct()]
    
    %% Note about transformations moved to stored procedure
    PHASE2 --> SP_NOTE[📋 NOTE: Group name & item name<br/>transformations moved to stored procedure<br/>Only group creation workflow remains in Python]
    
    %% STEP 2: TRUE BATCH PROCESSING Monday.com Sync Engine
    EMO --> SYNC_ENGINE[SyncEngine.run_sync()]
    SYNC_ENGINE --> BATCH_CONFIG[Load TOML batch_size=5]
    BATCH_CONFIG --> GET_PENDING[_get_pending_headers()]
    GET_PENDING --> TRUE_BATCH[_create_true_batch_groups()]
    TRUE_BATCH --> PROCESS_BATCH[_process_true_batch()]
    
    %% TRUE BATCH PROCESSING: Multiple record_uuids per API call
    PROCESS_BATCH --> BATCH_NOTE[🚀 TRUE BATCH: Process 5 record_uuids<br/>in single Monday.com API call<br/>✅ PRODUCTION VALIDATED with dropdown auto-creation]
    
    %% Monday.com API Operations
    PROCESS_BATCH --> MONDAY_API[MondayAPIClient.execute()]
    MONDAY_API --> API_OPS{Operation Type}
    API_OPS -->|create_items| CREATE_ITEMS[create_items GraphQL<br/>✅ createLabelsIfMissing properly set]
    API_OPS -->|create_subitems| CREATE_SUBITEMS[create_subitems GraphQL]
    API_OPS -->|update_items| UPDATE_ITEMS[update_items GraphQL]
    API_OPS -->|update_subitems| UPDATE_SUBITEMS[update_subitems GraphQL]
    
    %% Database Updates
    MONDAY_API --> DB_UPDATE[Database Status Updates]
    DB_UPDATE --> COMPLETE[Sync Complete]
```


```
📁 Root/src/pipelines/sync_order_list/
├── 📄 merge_orchestrator.py ✅ SIMPLIFIED (4-Phase Architecture)
│   ├── 🏗️ EnhancedMergeOrchestrator class
│   ├── � _execute_group_creation_workflow() (ONLY remaining transformation)
│   ├── 🔍 detect_new_orders() 
│   └── 📋 execute_enhanced_merge_sequence() (4-phase)
│
├── 📄 sync_engine.py ✅ OPERATIONAL
│   ├── 🚀 run_sync() with sync_state='PENDING' queries
│   ├── 🔄 _get_pending_headers() / _get_pending_lines()
│   ├── 📊 Record UUID atomic processing
│   └── ✅ Status completion (SYNCED state)
│
├── 📄 config_parser.py ✅ OPERATIONAL  
│   ├── 🎛️ DeltaSyncConfig.from_toml() 
│   ├── 📊 Dynamic table name management
│   └── 🔧 Environment awareness (dev/prod)
│
└── 📄 sql_template_engine.py ✅ OPERATIONAL
    ├── 🔧 Jinja2 template rendering
    ├── 📝 merge_headers.j2 execution  
    └── 📋 unpivot_sizes_direct.j2 execution
```

```
📁 Root/configs/pipelines/
└── 📄 sync_order_list.toml ✅ OPERATIONAL
    ├── 🎛️ [database] table mappings
    ├── � [monday.groups] auto_create settings
    └── 🔧 Environment-specific configurations
```

```
📁 Root/tests/sync-order-list-monday/e2e/
└── 📄 test_enhanced_merge_orchestrator_e2e.py ✅ WORKING
    ├── 🧪 Production-ready test validation
    ├── 🔄 Config-driven table name usage
    ├── 📊 Comprehensive data analysis patterns  
    └── ✅ Real data validation and explanations
```


```
src/pipelines/sync_order_list/
├── cli.py                           # ✅ KEEP - Entry point, calls merge_orchestrator
│   └── sync_command()               # ✅ KEEP - Triggers STEP 1 & 2
│       ├── EnhancedMergeOrchestrator.execute_enhanced_merge_sequence() # ✅ SIMPLIFIED - Now 4-phase
│       └── sync_engine.run_sync()   # ✅ KEEP - Monday.com API sync
│
├── merge_orchestrator.py            # ✅ SIMPLIFIED - 4-Phase Architecture
│   ├── execute_enhanced_merge_sequence() # ✅ SIMPLIFIED - 4 phases instead of 6
│   │   ├── Phase 1: detect_new_orders() # ✅ KEEP - AAG ORDER NUMBER detection
│   │   ├── Phase 2: _execute_group_creation_workflow() # ✅ KEEP - Monday.com group API
│   │   ├── Phase 3: _execute_template_merge_headers() # ✅ KEEP - Jinja2 template execution
│   │   └── Phase 4: _execute_template_unpivot_sizes_direct() # ✅ KEEP - Jinja2 template execution
│   │
│   ├── 🔴 GROUP CREATION WORKFLOW (ONLY REMAINING TRANSFORMATION)
│   │   ├── _execute_group_creation_workflow()         # ✅ KEEP - Monday.com group management
│   │   ├── _detect_missing_groups()                   # ✅ KEEP - Group detection logic
│   │   ├── _filter_existing_groups()                  # ✅ KEEP - Group filtering logic
│   │   ├── _create_groups_batch()                     # ✅ KEEP - Monday.com API batch creation
│   │   └── _update_single_group()                     # ✅ KEEP - Database group updates
│   │
│   ├── ✅ CORE METHODS (UNCHANGED)
│   │   ├── detect_new_orders()                        # ✅ KEEP - Core business logic
│   │   ├── get_existing_aag_orders()                  # ✅ KEEP - Supporting method
│   │   ├── execute_template_sequence()                # ✅ KEEP - Template execution
│   │   ├── _execute_template_merge_headers()          # ✅ KEEP - Jinja2 templates
│   │   ├── _execute_template_unpivot_sizes_direct()   # ✅ KEEP - Jinja2 templates  
│   │   ├── _execute_template_merge_lines()            # ✅ KEEP - Jinja2 templates
│   │   └── validate_cancelled_order_handling()       # ✅ KEEP - Validation logic
│   │
│   ├── ❌ REMOVED METHODS
│   │   ├── _execute_group_name_transformation()       # ❌ REMOVED - Moved to stored procedure
│   │   ├── _execute_item_name_transformation()        # ❌ REMOVED - Moved to stored procedure
│   │   ├── _is_group_transformation_enabled()         # ❌ REMOVED - No longer needed
│   │   └── _is_item_transformation_enabled()          # ❌ REMOVED - No longer needed
│   │
│   └── 🔧 HELPER METHODS (UNCHANGED)
│       └── _format_error_result()                     # ✅ KEEP - Error handling
│
└── sql/operations/order_list_transform/              # ✅ SQL FILES PRESERVED (User Request)
    ├── 01_delete_null_rows.sql                       # ✅ KEEP - File preserved
    ├── 02_filldown_customer_name.sql                 # ✅ KEEP - File preserved  
    ├── 03_check_customer_name_blanks.sql             # ✅ KEEP - File preserved
    ├── 04_copy_customer_to_source_customer.sql       # ✅ KEEP - File preserved (User edited)
    ├── 05_update_canonical_customer_name.sql         # ✅ KEEP - File preserved
    ├── 06_validate_canonical_mapping.sql             # ✅ KEEP - File preserved
    └── 12_update_order_type.sql                      # ✅ KEEP - File preserved
```



## SYNC STATE

```
-- When copying from ORDER_LIST to swp_ORDER_LIST_SYNC:
sync_state = NULL                    -- No default constraint (Python controls this)
action_type = NULL                   -- No default constraint (Python controls this)
```

```
STEP 0: Table Creation
   swp_ORDER_LIST_SYNC → sync_state: NULL, action_type: NULL
   ↓

STEP 1: detect_new_orders() [Python Logic]
   NEW Orders → sync_state: 'NEW', action_type: (unchanged/NULL)
   EXISTING Orders → sync_state: 'EXISTING', action_type: (unchanged/NULL)
   ↓

STEP 2: Group Creation Workflow [Python Logic] 
   Records remain → sync_state: 'NEW'/'EXISTING', action_type: (unchanged/NULL)
   ↓

STEP 3: merge_headers.j2 Template [Target Table Updates]
   INSERT Operations → target_table sync_state: 'PENDING', action_type: 'INSERT'
   UPDATE Operations → target_table sync_state: 'PENDING', action_type: 'UPDATE' 
   ↓

STEP 4: unpivot_sizes_direct.j2 Template [Lines Table Updates]
   INSERT Operations → lines_table sync_state: 'PENDING', action_type: 'INSERT'
   UPDATE Operations → lines_table sync_state: 'PENDING', action_type: 'UPDATE'
   ↓

STEP 5: Monday.com Sync [sync_engine.run_sync()]
   SUCCESS → sync_state: 'SYNCED', action_type: (unchanged)
   ERROR → sync_state: 'ERROR', action_type: (unchanged)
```