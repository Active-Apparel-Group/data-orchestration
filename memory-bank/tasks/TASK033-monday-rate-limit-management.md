# TASK033 - Monday.com Rate Limit Management & Centralized Configuration

**Status:** Completed  
**Added:** 2025-08-06  
**Updated:** 2025-08-07

## Original Request
Implement intelligent rate limiting for Monday.com API calls that:
1. Detects `FIELD_MINUTE_RATE_LIMIT_EXCEEDED` errors and respects `retry_in_seconds`
2. Creates centralized `monday_boards.toml` configuration for all Monday.com operations
3. Calculates optimal batch sizes and concurrency to prevent rate limits
4. Provides config.py module for consistent rate limit management across ingestion and update scripts

Critical error pattern to handle:
```json
{
  "message": "Rate limit exceeded for the field.",
  "extensions": {
    "field": "display_value",
    "retry_in_seconds": 18,
    "status_code": 429,
    "code": "FIELD_MINUTE_RATE_LIMIT_EXCEEDED"
  }
}
```

## Thought Process
Monday.com has multiple rate limiting tiers:
- Overall API rate limit (500 requests/minute)
- Field-specific rate limits (display_value, column_values)
- Complexity limits (25 items max for detailed queries)

Current async loader is hitting field-specific limits due to aggressive concurrency. Need:
1. Intelligent retry with Monday.com specified delays
2. Centralized configuration for rate limiting across all scripts
3. Dynamic optimization based on observed rate limits
4. Consistent error handling patterns

The `sync_order_list.toml` already has some Monday.com config structure we can build upon.

## Definition of Done
- Enhanced retry logic that respects Monday.com `retry_in_seconds` 
- Centralized `configs/pipelines/monday_boards.toml` configuration
- Config.py module for loading Monday.com settings
- Integration with `load_boards_async.py` using new config system
- Optimal rate limiting parameters calculated and documented
- All Monday.com scripts follow consistent rate limiting patterns

## Implementation Plan
- [ ] Create centralized `configs/pipelines/monday_boards.toml` configuration
- [ ] Implement `pipelines/utils/monday_config.py` configuration loader
- [ ] Enhance `load_boards_async.py` with intelligent rate limiting
- [ ] Add Monday.com error parsing for `retry_in_seconds` extraction
- [ ] Calculate and document optimal batch/concurrency settings
- [ ] Update other Monday.com scripts to use centralized config
- [ ] Test rate limiting with various board sizes

## Progress Tracking

**Overall Status:** Completed - 100% Complete

### Subtasks
| ID  | Description                                 | Status      | Updated    | Notes |
|-----|---------------------------------------------|-------------|------------|-------|
| 1.1 | Create monday_boards.toml configuration    | Complete    | 2025-08-06 | Comprehensive config with all sections |
| 1.2 | Implement monday_config.py loader          | Complete    | 2025-08-06 | Full implementation in src/pipelines/utils |
| 1.3 | Enhanced rate limiting in load_boards_async| Complete    | 2025-08-06 | MondayConfig integration successful |
| 1.4 | Monday.com error parsing and retry logic   | Complete    | 2025-08-06 | Implemented in MondayConfig.get_retry_delay |
| 1.5 | Calculate optimal parameters                | Complete    | 2025-08-06 | Board-specific and operation-specific settings |
| 1.6 | Update other scripts with centralized config| Complete    | 2025-08-07 | Both update scripts integrated |
| 1.7 | Add pipeline config generator to board_metadata_and_toml_runner.py | Complete | 2025-08-06 | ✅ Integrated as Step 3 - automatically generates board registry entries |
| 1.8 | Integrate MondayConfig with load_boards_async.py | Complete | 2025-08-06 | Configuration-driven settings with CLI override capability |
| 1.9 | Testing and validation                      | Complete    | 2025-08-07 | All integrations tested and validated |

## Relevant Files
- `src/pipelines/utils/monday_config.py` - ✅ Complete configuration manager
- `src/pipelines/utils/__init__.py` - ✅ Updated with MondayConfig exports
- `configs/pipelines/monday_boards.toml` - ✅ Comprehensive configuration file
- `pipelines/scripts/ingestion/load_boards_async.py` - ✅ MondayConfig integration complete
- `pipelines/scripts/update/update_boards_batch.py` - ✅ MondayConfig integration complete
- `pipelines/scripts/update/update_boards_async_batch.py` - ✅ MondayConfig integration complete
- `pipelines/codegen/board_metadata_and_toml_runner.py` - ✅ Pipeline config generator integrated

## Test Coverage Mapping
| Implementation Task                | Test File                                             | Outcome Validated                                |
|------------------------------------|-------------------------------------------------------|--------------------------------------------------|
| MondayConfig class                 | src/pipelines/utils/monday_config.py (main block)    | ✅ Config loading, board settings, retry logic |
| TOML configuration loading         | Verified with test imports                            | ✅ Configuration parsing and path resolution |
| Package structure integration      | Verified with convenience imports                     | ✅ Proper Python package structure |
| Rate limit error detection        | Mock error testing in main block                     | ✅ FIELD_MINUTE_RATE_LIMIT_EXCEEDED detection |

## Progress Log

### 2025-08-07 (COMPLETION)
**✅ TASK033 COMPLETED - UPDATE SCRIPTS INTEGRATION COMPLETE**
- ✅ Final integration complete: Both update scripts now use MondayConfig system
- ✅ `update_boards_batch.py`: Integrated with board-specific optimization and intelligent rate limiting
- ✅ `update_boards_async_batch.py`: Enhanced with async-compatible MondayConfig retry logic
- ✅ Centralized configuration: All Monday.com operations now use unified `monday_boards.toml` settings
- ✅ Production ready: Board complexity analysis, optimal batch sizes, and rate limit compliance

**Complete Integration Coverage:**
- ✅ Ingestion scripts: `load_boards_async.py` integrated (2025-08-06)
- ✅ Update scripts: Both batch processors integrated (2025-08-07)
- ✅ Pipeline generators: `board_metadata_and_toml_runner.py` integrated (2025-08-06)
- ✅ Configuration system: Comprehensive `monday_boards.toml` with board registry
- ✅ Utility framework: `MondayConfig` class with intelligent retry and optimization logic

**Update Scripts Integration Details:**
1. **update_boards_batch.py Enhancements:**
   - Added `self.monday_config = MondayConfig()` initialization
   - Dynamic API configuration: `get_api_url()`, `get_api_version()`
   - Intelligent retry logic with Monday.com rate limit error detection
   - Board-specific batch sizing: `get_optimal_batch_size(board_id, operation="updates")`
   - Configurable delays: `get_rate_limits().delay_between_batches`

2. **update_boards_async_batch.py Enhancements:**
   - MondayConfig integration with async-compatible retry logic
   - Smart concurrency detection using board complexity analysis
   - Enhanced `execute_graphql_async()` with rate limit compliance
   - Dynamic batch size optimization per board characteristics
   - Centralized delay management between async batch groups

**Configuration Integration Benefits:**
- Centralized Monday.com settings in single `monday_boards.toml` file
- Board-specific optimization (Planning: 20/6, Factory List: 25/12)
- Intelligent rate limiting respecting `retry_in_seconds` directives
- Consistent error handling across all update operations
- Performance tuning based on board complexity categories

### 2025-08-06
- ✅ Integration complete (subtask 1.8) - MondayConfig successfully integrated with load_boards_async.py
- ✅ Configuration-driven settings: Batch size and concurrency automatically loaded from monday_boards.toml
- ✅ Intelligent rate limiting: Enhanced gql_request() function respects Monday.com retry_in_seconds
- ✅ CLI transparency: Shows optimal settings from config while allowing manual overrides
- ✅ Production validation: Tested with multiple boards (8446553051, 8709134353) with correct optimal settings
- � Next: Extend configuration system to update scripts for complete rate limiting coverage

### 2025-08-06 (Earlier)
- ✅ Pipeline config generator (subtask 1.7) complete - Auto-generates board registry entries from metadata JSON
- ✅ Enhanced monday_boards.toml with comprehensive board registry and optimal settings
- ✅ Board complexity analysis algorithm implemented (analyzes columns, formulas, lookups, item counts)
- ✅ Integration ready for board_metadata_and_toml_runner.py workflow as Step 3
- 🔄 Starting integration with load_boards_async.py to use MondayConfig system
- 📋 Next: Replace manual rate limiting with configuration-driven optimization
